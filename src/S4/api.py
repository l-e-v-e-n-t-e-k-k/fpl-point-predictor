import json
import joblib
import os
import pandas as pd
import threading
import time

from pathlib import Path
from fastapi import FastAPI
from fastapi import HTTPException
from shared.http.json_client import fetch_url

app = FastAPI()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = Path(os.getenv("MODEL_BASE_DIR", str(PROJECT_ROOT / "models")))
LATEST_METADATA_PATH = MODEL_DIR / "latest.json"
MODEL_POLL_SECONDS = float(os.getenv("MODEL_POLL_SECONDS", "10"))
S1_BASE_URL = os.getenv("S1_BASE_URL", "").strip()
S2_BASE_URL = os.getenv("S2_BASE_URL", "").strip()

TOP_K = 20

model = None
scaler = None
feature_cols = []
player_meta = {}
current_version = None
model_lock = threading.Lock()


# ---- helper functions ----
def normalize_name(name: str):
    if not name:
        return ""
    return " ".join(name.lower().strip().split())


def pos_name(element_type: int):
    return {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}.get(element_type, str(element_type))


def load_player_meta():
    if not S1_BASE_URL:
        raise RuntimeError("S1_BASE_URL is required for API player metadata loading")

    payload = fetch_url(S1_BASE_URL, "player-meta")
    data = payload.get("data", [])
    meta_df = pd.DataFrame(data)

    meta = {}

    for row in meta_df.itertuples(index=False):
        full_name = f"{row.first_name} {row.second_name}".strip()
        key = normalize_name(full_name)

        meta[key] = {
            "name": full_name,
            "web_name": row.web_name,
            "team": row.team_name or "Unknown",
            "pos": pos_name(int(row.element_type)),
            "price": float(row.now_cost or 0) / 10.0,
        }

    return meta


def resolve_path(path_str: str):
    path = Path(path_str)
    if path.is_absolute():
        return path

    candidates = [
        PROJECT_ROOT / path,
        MODEL_DIR.parent / path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def load_latest_paths():
    with LATEST_METADATA_PATH.open("r", encoding="utf-8") as f:
        latest = json.load(f)

    model_path = resolve_path(latest["model_path"])
    scaler_path = resolve_path(latest["scaler_path"])
    metadata_path = resolve_path(latest["metadata_path"])
    return model_path, scaler_path, metadata_path, latest


def load_model_artifacts():
    global model, scaler, feature_cols, player_meta, current_version

    model_path, scaler_path, metadata_path, latest = load_latest_paths()

    if latest["version"] == current_version:
        return False

    loaded_model = joblib.load(model_path)
    loaded_scaler = joblib.load(scaler_path)
    with metadata_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    loaded_feature_cols = metadata["feature_cols"]
    loaded_player_meta = load_player_meta()

    with model_lock:
        model = loaded_model
        scaler = loaded_scaler
        feature_cols = loaded_feature_cols
        player_meta = loaded_player_meta
        current_version = latest["version"]

    print(f"Model loaded: {latest['version']} ({latest['model_type']})")
    return True


def model_watcher():
    while True:
        try:
            load_model_artifacts()
        except Exception as exc:
            print(f"Model reload error: {exc}")
        time.sleep(MODEL_POLL_SECONDS)


# ---- startup ----
@app.on_event("startup")
def load_model():
    load_model_artifacts()

    if MODEL_POLL_SECONDS > 0:
        watcher = threading.Thread(target=model_watcher, daemon=True)
        watcher.start()


@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "s4-prediction-api"}


@app.get("/readyz")
def readyz():
    if not S1_BASE_URL:
        raise HTTPException(status_code=503, detail="S1_BASE_URL is not configured")

    if not S2_BASE_URL:
        raise HTTPException(status_code=503, detail="S2_BASE_URL is not configured")

    with model_lock:
        model_loaded = model is not None
        current_model_version = current_version

    if not model_loaded:
        raise HTTPException(status_code=503, detail="model is not loaded")

    try:
        fetch_url(S1_BASE_URL, "/healthz")
        fetch_url(S2_BASE_URL, "/healthz")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"dependency not ready: {exc}") from exc

    return {
        "status": "ready",
        "service": "s4-prediction-api",
        "model_version": current_model_version,
    }


# ---- prediction endpoint ----
@app.get("/predict")
def predict():
    with model_lock:
        loaded_model = model
        loaded_scaler = scaler
        loaded_feature_cols = list(feature_cols)
        loaded_player_meta = dict(player_meta)

    if loaded_model is None:
        raise RuntimeError("Model is not loaded")

    if not S2_BASE_URL:
        raise RuntimeError("S2_BASE_URL is required for API prediction loading")

    payload = fetch_url(S2_BASE_URL, "/player-data/latest")
    data = payload.get("data", [])
    df = pd.DataFrame(data)

    latest_season = df["season"].max()
    latest_gw = df[df["season"] == latest_season]["GW"].max()

    next_gw_df = df[
        (df["season"] == latest_season) &
        (df["GW"] == latest_gw)
    ].copy()

    X_next = next_gw_df[loaded_feature_cols]

    if "LinearRegression" in str(type(loaded_model)):
        X_next = loaded_scaler.transform(X_next)

    preds = loaded_model.predict(X_next)

    next_gw_df["predicted_points"] = preds

    top_players = next_gw_df.sort_values(
        "predicted_points", ascending=False
    ).head(TOP_K)

    next_gw = latest_gw + 1

    # ---- top players ----
    top_results = []

    for i, row in enumerate(top_players.itertuples(), start=1):

        player_name = getattr(row, "name")

        meta = loaded_player_meta.get(
            normalize_name(player_name),
            {"team": "Unknown", "pos": "", "price": 0, "web_name": player_name}
        )

        top_results.append({
            "rank": i,
            "player": meta["web_name"],
            "team": meta["team"],
            "position": meta["pos"],
            "price": meta["price"],
            "predicted_points": float(row.predicted_points)
        })

    # ---- position results ----
    positions = ["GKP", "DEF", "MID", "FWD"]

    position_results = {}

    for pos in positions:

        pos_df = next_gw_df[next_gw_df["position"] == pos]

        top_pos = pos_df.sort_values(
            "predicted_points", ascending=False
        ).head(3)

        pos_list = []

        for i, row in enumerate(top_pos.itertuples(), start=1):

            player_name = getattr(row, "name")

            meta = loaded_player_meta.get(
                normalize_name(player_name),
                {"team": "Unknown", "pos": "", "price": 0, "web_name": player_name}
            )

            pos_list.append({
                "rank": i,
                "player": meta["web_name"],
                "team": meta["team"],
                "position": meta["pos"],
                "price": meta["price"],
                "predicted_points": float(row.predicted_points)
            })

        position_results[pos] = pos_list

    return {
        "gw": int(next_gw),
        "top_players": top_results,
        "top_by_position": position_results
    }

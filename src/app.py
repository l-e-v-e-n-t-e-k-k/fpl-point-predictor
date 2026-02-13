
import json
from pathlib import Path

from data_utils import load_rows
from features import build_supervised, build_nextgw_features
from model import fit_linear_regression, predict_row

BOOTSTRAP_PATH = Path("data/raw/bootstrap-static.json")
MATCH_HISTORY_PATH = Path("data/processed/match_history.csv")

TOP_K = 20

# Helper

def pos_name(element_type: int) -> str:
    # FPL: 1=GKP, 2=DEF, 3=MID, 4=FWD
    return {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}.get(element_type, str(element_type))


def main():

    if not BOOTSTRAP_PATH.exists():
        raise FileNotFoundError("Futtasd előbb: python3 src/fpl_api.py")

    if not MATCH_HISTORY_PATH.exists():
        raise FileNotFoundError("Futtasd előbb: python3 src/build_dataset.py")

    # ---- Load metadata ----
    bootstrap = json.loads(BOOTSTRAP_PATH.read_text(encoding="utf-8"))
    elements = bootstrap.get("elements", [])
    teams = {t["id"]: t["name"] for t in bootstrap.get("teams", [])}

    player_meta = {}
    for e in elements:
        pid = int(e["id"])
        player_meta[pid] = {
            "name": e.get("web_name") or "",
            "team": teams.get(int(e.get("team", 0)), "Unknown"),
            "pos": pos_name(int(e.get("element_type", 0))),
            "price": float(e.get("now_cost", 0)) / 10.0,
        }

    # ---- Load match history ----
    rows = load_rows(MATCH_HISTORY_PATH)

    # ---- Train model ----
    X, y = build_supervised(rows)

    if len(y) < 50:
        print("Túl kevés adat a tanításhoz.")
        return

    w = fit_linear_regression(X, y)

    # ---- Build next GW features ----
    next_feats = build_nextgw_features(rows)

    preds = []

    for pid, x in next_feats.items():
        if pid not in player_meta:
            continue

        pred_pts = predict_row(x, w)
        meta = player_meta[pid]

        preds.append((pred_pts, meta))

    preds.sort(reverse=True, key=lambda t: t[0])

    max_gw = max(r["gw"] for r in rows if r["gw"] is not None)
    next_gw = max_gw + 1

    print(f"\nPredicting GW {next_gw}")
    print("-" * 90)
    print(f"{'Rank':>4}  {'Player':<18}  {'Team':<18}  {'Pos':<3}  {'Price':>5}  {'PredPts':>7}")
    print("-" * 90)

    for i, (pred_pts, meta) in enumerate(preds[:TOP_K], start=1):
        print(
            f"{i:>4}  "
            f"{meta['name']:<18.18}  "
            f"{meta['team']:<18.18}  "
            f"{meta['pos']:<3}  "
            f"{meta['price']:>5.1f}  "
            f"{pred_pts:>7.2f}"
        )

    print("-" * 90)


if __name__ == "__main__":
    main()
 
#from pathlib import Path
from statistics import mean
import pandas as pd

MIN_MATCHES_REQUIRED = 5
MIN_AVG_MIN_LAST5 = 0.0

# ---------- Feature epites (last3/last5) + target shift ----------
def build_supervised(rows):
    """
    Kimenet: X, y listak
    X: [1, avg_pts_last3, avg_min_last3, avg_pts_last5, avg_min_last5]
    y: next_gw_total_points
    """
    # csoportositas
    by_player = {}
    for row in rows:
        by_player.setdefault(row["name"], []).append(row)

    X = []
    y = []

    for pid, games in by_player.items():
        # gw szerint rendezes
        games.sort(key=lambda r: r["GW"])

        # csak a minutes es points sorozat kell
        pts = [g["total_points"] for g in games]
        mins = [g["minutes"] for g in games]

        # supervised peldak: t -> (featureek t-1..), target = pts[t]
        for t in range(len(games)):
            # target: aktualis gw pontja (t)
            target = pts[t]

            # feature ablakok az elozo meccsekbol
            prev_pts = pts[:t]
            prev_mins = mins[:t]

            if len(prev_pts) < MIN_MATCHES_REQUIRED:
                # baseline-hoz legalabb 5 multbeli meccs
                continue
            if mean(prev_mins[-5:]) < MIN_AVG_MIN_LAST5:
                continue

            avg_pts_last3 = mean(prev_pts[-3:])
            avg_min_last3 = mean(prev_mins[-3:])
            avg_pts_last5 = mean(prev_pts[-5:])
            avg_min_last5 = mean(prev_mins[-5:])

            # X sor: bias + 4 feature
            X.append([1.0, avg_pts_last3, avg_min_last3, avg_pts_last5, avg_min_last5])
            y.append(target)

    return X, y

# ---------- Next GW feature sorok ----------

def build_nextgw_features(rows):
    """
    visszaad:
        dict[player_id] = feature_row
    """

    by_player = {}

    for row in rows:
        by_player.setdefault(row["player_id"], []).append(row)

    features = {}

    for pid, games in by_player.items():
        games.sort(key=lambda r: r["gw"])

        pts = [g["total_points"] for g in games]
        mins = [g["minutes"] for g in games]

        if len(pts) < MIN_MATCHES_REQUIRED:
            continue

        if mean(mins[-5:]) < MIN_AVG_MIN_LAST5:
            continue

        avg_pts_last3 = mean(pts[-3:])
        avg_min_last3 = mean(mins[-3:])
        avg_pts_last5 = mean(pts[-5:])
        avg_min_last5 = mean(mins[-5:])

        features[pid] = [
            1.0,
            avg_pts_last3,
            avg_min_last3,
            avg_pts_last5,
            avg_min_last5,
        ]

    return features

def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Season-aware rolling feature engineering.

    Feltetelezi:
        df tartalmazza:
            season, name, GW, total_points, minutes

    Visszaad:
        df uj rolling feature oszlopokkal.
    """

    df = df.sort_values(["season", "name", "GW"]).copy()

    # --- Rolling last3 ---
    df["avg_pts_last3"] = (
        df.groupby(["season", "name"])["total_points"]
          .transform(lambda x: x.shift(1).rolling(3).mean())
    )

    df["avg_min_last3"] = (
        df.groupby(["season", "name"])["minutes"]
          .transform(lambda x: x.shift(1).rolling(3).mean())
    )

    # --- Rolling last5 ---
    df["avg_pts_last5"] = (
        df.groupby(["season", "name"])["total_points"]
          .transform(lambda x: x.shift(1).rolling(5).mean())
    )

    df["avg_min_last5"] = (
        df.groupby(["season", "name"])["minutes"]
          .transform(lambda x: x.shift(1).rolling(5).mean())
    )

    # --- Szűrés ---
   # df = df[df["avg_pts_last5"].notna()]
    df = df[df["avg_min_last5"] >= MIN_AVG_MIN_LAST5]

    return df

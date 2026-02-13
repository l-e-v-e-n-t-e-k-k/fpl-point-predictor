# src/data_utils.py

import csv
from pathlib import Path


def load_rows(path: Path):
    """
    match_history.csv betoltese eegysegesen
    """

    rows = []

    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)

        for row in r:
            rows.append({
                "player_id": int(row["player_id"]),
                "gw": int(row["gw"]) if row["gw"] not in (None, "", "None") else None,
                "minutes": float(row["minutes"]) if row["minutes"] not in (None, "", "None") else 0.0,
                "total_points": float(row["total_points"]) if row["total_points"] not in (None, "", "None") else 0.0,
            })

    return rows

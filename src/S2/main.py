from S2.add_target import add_target, save_supervised
from S2.build_dataset_multiseason import build_multiseason, save_multiseason, save_multiseason_db
from S2.build_dataset_pandas import build_current_season, save_current_season
from S2.merge_difficulty import merge_difficulty, save_with_difficulty


def run_pipeline():
    current_raw_df = build_current_season()
    save_current_season(current_raw_df)

    current_with_difficulty_df = merge_difficulty(current_raw_df)
    save_with_difficulty(current_with_difficulty_df)

    current_supervised_df = add_target(current_with_difficulty_df)
    save_supervised(current_supervised_df)

    multiseason_df = build_multiseason(current_supervised_df)
    save_multiseason(multiseason_df)
    save_multiseason_db(multiseason_df)

    return {
        "status": "ok",
        "current_rows": len(current_raw_df),
        "current_with_difficulty_rows": len(current_with_difficulty_df),
        "current_supervised_rows": len(current_supervised_df),
        "multiseason_rows": len(multiseason_df),
    }


if __name__ == "__main__":
    run_pipeline()

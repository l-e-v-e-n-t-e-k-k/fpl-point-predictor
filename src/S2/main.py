from S2.build_dataset_pandas import main as build_dataset_main
from S2.add_target import main as add_target_main
from S2.merge_difficulty import main as merge_difficulty_main
from S2.build_dataset_multiseason import main as build_multiseason_main

if __name__ == "__main__":
    build_dataset_main()
    merge_difficulty_main()
    add_target_main()
    build_multiseason_main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI script for running the FIS-based Comparator.

This script compares frequent itemsets between yes/no cases using theta sketches,
inspired by classification-based association rules.

Usage:
    python fis_comparator.py --config my_comparator_config.json

The configuration file determines which mode to run:
1. Two-file mode: Separate CSV files for yes and no cases
2. Single-file with one target: Split data using intersection and A-not-B
3. Single-file with two targets: Split data using two intersections
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from FIS_comparator.comparator_config import (
    load_comparator_config,
    TwoFileComparatorConfig,
    SingleFileComparatorConfig,
)
from FIS_comparator.comparator_core import (
    run_two_file_comparison,
    run_single_file_comparison_one_target,
    run_single_file_comparison_two_targets,
)


def main():
    """Main entry point for the CLI script."""
    parser = argparse.ArgumentParser(
        description="FIS-based Comparator for Yes/No Classification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration Modes:

1. Two-File Mode (separate yes/no CSV files):
{
    "input_csv_path_for_yes_case": "yes_sketches.csv",
    "input_csv_path_for_no_case": "no_sketches.csv",
    "min_support_for_yes_case": 0.05,
    "min_support_for_no_case": 0.05,
    "max_levels": 5,
    "include_all_level1": true,
    "output_itemsets_path_yes_case": "yes_itemsets.csv",
    "output_itemsets_path_no_case": "no_itemsets.csv",
    "output_itemsets_joined": "joined.csv",
    "item_separator": " && ",
    "sketch_lg_k_yes_case": 12,
    "sketch_lg_k_no_case": 12
}

2. Single-File Mode with One Target (intersection vs A-not-B):
{
    "input_csv_path": "sketches.csv",
    "min_support_for_yes_case": 0.05,
    "min_support_for_no_case": 0.05,
    "max_levels": 5,
    "include_all_level1": true,
    "output_itemsets_path": "joined.csv",
    "item_separator": " && ",
    "sketch_lg_k": 12,
    "target_item_1": "dimension=value"
}

3. Single-File Mode with Two Targets (two intersections):
{
    "input_csv_path": "sketches.csv",
    "min_support_for_yes_case": 0.05,
    "min_support_for_no_case": 0.05,
    "max_levels": 5,
    "include_all_level1": true,
    "output_itemsets_path": "joined.csv",
    "item_separator": " && ",
    "sketch_lg_k": 12,
    "target_item_1": "dimension=yes",
    "target_item_0": "dimension=no"
}

Input CSV Format:
  First row: "total" or "" followed by base64-encoded total count sketch
  Remaining rows: "dimension=value/item,<base64_encoded_sketch>"

Output CSV Format:
  Columns: Level, Frequent_itemset, Frequent_item_set_seen_in,
           Yes_case_count, No_case_count, Total, Yes_percentage

Reference:
  Inspired by: Liu et al. "Integrating Classification and Association Rule Mining"
  KDD 1998 (https://rsrikant.com/papers/kdd97_class.pdf)
        """,
    )

    parser.add_argument(
        "--config", type=str, required=True, help="Path to the JSON configuration file"
    )

    parser.add_argument(
        "-v",
        "--verbosity",
        type=int,
        default=0,
        choices=[0, 1, 2],
        help="Verbosity level (0=quiet, 1=normal, 2=verbose)",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_comparator_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Dispatch based on configuration type
    try:
        if isinstance(config, TwoFileComparatorConfig):
            # Two-file mode
            run_two_file_comparison(config, verbosity=args.verbosity)

        elif isinstance(config, SingleFileComparatorConfig):
            if config.target_item_0 is None:
                # Single-file with one target (intersection and A-not-B)
                run_single_file_comparison_one_target(config, verbosity=args.verbosity)
            else:
                # Single-file with two targets (two intersections)
                run_single_file_comparison_two_targets(
                    config, verbosity=args.verbosity
                )
        else:
            print(f"Unknown configuration type: {type(config)}")
            sys.exit(1)

    except Exception as e:
        print(f"Error running comparator: {e}")
        if args.verbosity > 1:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

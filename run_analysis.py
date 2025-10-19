#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick helper script to run the complete Apriori analysis pipeline.

This script automates the three-step process:
1. Convert transactions to theta sketches
2. Create configuration file
3. Run Apriori algorithm

Usage:
    python run_analysis.py my_transactions.csv --min-support 0.3 --min-confidence 0.5
"""

import argparse
import json
import sys
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run complete Apriori analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with defaults
  python run_analysis.py my_transactions.csv

  # Custom support and confidence
  python run_analysis.py my_transactions.csv --min-support 0.3 --min-confidence 0.6

  # With custom sketch size and max levels
  python run_analysis.py my_transactions.csv --sketch-lg-k 14 --max-levels 4

  # Don't include all level 1 items
  python run_analysis.py my_transactions.csv --no-include-all-level1
        """
    )

    parser.add_argument(
        'input_file',
        type=str,
        help='Path to the input transaction CSV file'
    )

    parser.add_argument(
        '--min-support',
        type=float,
        default=0.3,
        help='Minimum support threshold (default: 0.3)'
    )

    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.5,
        help='Minimum confidence threshold (default: 0.5)'
    )

    parser.add_argument(
        '--max-levels',
        type=int,
        default=5,
        help='Maximum itemset size (default: 5)'
    )

    parser.add_argument(
        '--sketch-lg-k',
        type=int,
        default=12,
        help='Sketch size parameter (default: 12, size=4096)'
    )

    parser.add_argument(
        '--item-separator',
        type=str,
        default='&&',
        help='Separator for items in output (default: "&&")'
    )

    parser.add_argument(
        '--no-include-all-level1',
        action='store_true',
        help='Do not include all level 1 items in output'
    )

    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        default=1,
        choices=[0, 1, 2],
        help='Verbosity level (default: 1)'
    )

    args = parser.parse_args()

    # Validate input file exists
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)

    # Generate output file names
    basename = input_path.stem
    sketch_file = f"data/{basename}_sketches.csv"
    config_file = f"{basename}_config.json"
    itemsets_output = f"output/{basename}_frequent_itemsets.csv"
    rules_output = f"output/{basename}_association_rules.csv"

    print("=" * 60)
    print("Apriori Analysis Pipeline")
    print("=" * 60)
    print(f"Input file: {args.input_file}")
    print(f"Min support: {args.min_support}")
    print(f"Min confidence: {args.min_confidence}")
    print(f"Max levels: {args.max_levels}")
    print(f"Sketch lg_k: {args.sketch_lg_k} (size={2**args.sketch_lg_k})")
    print()

    # Step 1: Convert to sketches
    print("Step 1/3: Converting transactions to theta sketches...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                'convert_to_sketches.py',
                '--input', args.input_file,
                '--output', sketch_file,
                '--sketch-lg-k', str(args.sketch_lg_k),
                '-v', str(args.verbosity)
            ],
            check=True,
            capture_output=(args.verbosity == 0)
        )
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to convert transactions to sketches")
        sys.exit(1)

    # Step 2: Create config file
    print()
    print("Step 2/3: Creating configuration file...")
    config = {
        "input_csv_path": sketch_file,
        "min_support": args.min_support,
        "max_levels": args.max_levels,
        "include_all_level1": not args.no_include_all_level1,
        "output_itemsets_path": itemsets_output,
        "output_rules_path": rules_output,
        "item_separator": args.item_separator,
        "min_confidence": args.min_confidence,
        "sketch_lg_k": args.sketch_lg_k,
    }

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"Created: {config_file}")

    # Step 3: Run Apriori
    print()
    print("Step 3/3: Running Apriori algorithm...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                'apriori_sketch.py',
                '--config', config_file,
                '-v', str(args.verbosity)
            ],
            check=True,
            capture_output=(args.verbosity == 0)
        )
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to run Apriori algorithm")
        sys.exit(1)

    # Summary
    print()
    print("=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    print("Outputs:")
    print(f"  - Frequent itemsets: {itemsets_output}")
    print(f"  - Association rules: {rules_output}")
    print(f"  - Configuration: {config_file}")
    print()
    print("View results:")
    print(f"  cat {itemsets_output}")
    print(f"  cat {rules_output}")


if __name__ == "__main__":
    main()

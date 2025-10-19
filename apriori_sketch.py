#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI script for running Apriori algorithm with theta sketches.

This script reads configuration from a JSON file and runs the Apriori algorithm
using pre-computed theta sketches from Apache DataSketches. The results are
written to CSV files.

Usage:
    python apriori_sketch.py --config config.json

Configuration file format (JSON):
{
    "input_csv_path": "data/sketches.csv",
    "min_support": 0.3,
    "max_levels": 5,
    "include_all_level1": true,
    "output_itemsets_path": "output/frequent_itemsets.csv",
    "output_rules_path": "output/association_rules.csv",
    "item_separator": "&&",
    "min_confidence": 0.5
}
"""

import argparse
import sys
from pathlib import Path

# Add the parent directory to the path to import efficient_apriori
sys.path.insert(0, str(Path(__file__).parent))

from efficient_apriori.config import load_config, SketchConfig
from efficient_apriori.sketch_support import ThetaSketchManager
from efficient_apriori.itemsets_sketch import itemsets_from_sketches
from efficient_apriori.rules import generate_rules_apriori
from efficient_apriori.rules_sketch import write_itemsets_to_csv, write_rules_to_csv


def run_apriori_with_sketches(config: SketchConfig, verbosity: int = 0):
    """
    Run the Apriori algorithm with theta sketches.

    Parameters
    ----------
    config : SketchConfig
        Configuration object with all parameters.
    verbosity : int
        Verbosity level (0, 1, or 2).
    """
    print(f"Loading theta sketches from: {config.input_csv_path}")

    # Load sketches
    try:
        sketch_manager = ThetaSketchManager(config.input_csv_path)
    except Exception as e:
        print(f"Error loading sketches: {e}")
        sys.exit(1)

    print(f"Loaded {len(sketch_manager.items)} items")
    print(f"Total count estimate: {sketch_manager.total_count:.2f}")

    # Run Apriori algorithm
    print(f"\nRunning Apriori algorithm...")
    print(f"  Min support: {config.min_support}")
    print(f"  Max levels: {config.max_levels}")
    print(f"  Include all level 1: {config.include_all_level1}")

    try:
        itemsets, total_count = itemsets_from_sketches(
            sketch_manager=sketch_manager,
            min_support=config.min_support,
            max_length=config.max_levels,
            verbosity=verbosity,
            include_all_level1=config.include_all_level1,
        )
    except Exception as e:
        print(f"Error computing itemsets: {e}")
        sys.exit(1)

    # Print summary
    print(f"\nFrequent itemsets found:")
    for level in sorted(itemsets.keys()):
        print(f"  Level {level}: {len(itemsets[level])} itemsets")

    # Write itemsets to CSV
    print(f"\nWriting frequent itemsets to: {config.output_itemsets_path}")
    try:
        write_itemsets_to_csv(
            itemsets=itemsets,
            total_count=total_count,
            output_path=config.output_itemsets_path,
            item_separator=config.item_separator,
        )
    except Exception as e:
        print(f"Error writing itemsets: {e}")
        sys.exit(1)

    # Generate association rules
    print(f"\nGenerating association rules...")
    print(f"  Min confidence: {config.min_confidence}")

    try:
        rules = list(generate_rules_apriori(
            itemsets=itemsets,
            min_confidence=config.min_confidence,
            num_transactions=int(total_count),
            verbosity=verbosity,
        ))
    except Exception as e:
        print(f"Error generating rules: {e}")
        sys.exit(1)

    print(f"Generated {len(rules)} association rules")

    # Write rules to CSV
    print(f"\nWriting association rules to: {config.output_rules_path}")
    try:
        write_rules_to_csv(
            rules=rules,
            output_path=config.output_rules_path,
            item_separator=config.item_separator,
        )
    except Exception as e:
        print(f"Error writing rules: {e}")
        sys.exit(1)

    print("\nDone!")


def main():
    """Main entry point for the CLI script."""
    parser = argparse.ArgumentParser(
        description="Run Apriori algorithm with theta sketches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example configuration file (config.json):
{
    "input_csv_path": "data/sketches.csv",
    "min_support": 0.3,
    "max_levels": 5,
    "include_all_level1": true,
    "output_itemsets_path": "output/frequent_itemsets.csv",
    "output_rules_path": "output/association_rules.csv",
    "item_separator": "&&",
    "min_confidence": 0.5
}

Input CSV format (no header):
  First row: "total" or "" followed by base64-encoded total count sketch
  Remaining rows: "<item/dimension=value>,<base64_encoded_sketch>"

Output CSV formats:
  Frequent itemsets: level,frequent_itemset,count,support
  Association rules: level,frequent_itemset,count,support,confidence,lift,conviction
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to the JSON configuration file'
    )

    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        default=0,
        choices=[0, 1, 2],
        help='Verbosity level (0=quiet, 1=normal, 2=verbose)'
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Run the algorithm
    run_apriori_with_sketches(config, verbosity=args.verbosity)


if __name__ == "__main__":
    main()

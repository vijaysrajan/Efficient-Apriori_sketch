#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper script to convert transaction data to theta sketches CSV format.

This script reads transaction data and converts it to theta sketches that can
be used with the apriori_sketch.py script.

Usage:
    python convert_to_sketches.py --input transactions.csv --output sketches.csv

Input format (CSV):
    Each row is a transaction with items separated by commas or a custom delimiter.
    Example:
        eggs,bacon,soup
        eggs,bacon,apple
        soup,bacon,banana

Output format (CSV):
    <item>,<base64_encoded_sketch>
    First row: total,<base64_total_sketch>
    Subsequent rows: item_name,<base64_sketch>
"""

import argparse
import csv
import sys
from pathlib import Path
from collections import defaultdict

# Increase CSV field size limit to handle large base64-encoded sketches
csv.field_size_limit(sys.maxsize)

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from efficient_apriori import (
    create_sketch_from_transaction_ids,
    serialize_sketch_to_base64,
)


def read_transactions_from_csv(
    input_path: str,
    delimiter: str = ',',
    skip_header: bool = False,
) -> list:
    """
    Read transactions from a CSV file.

    Parameters
    ----------
    input_path : str
        Path to the input CSV file.
    delimiter : str
        Delimiter used in the CSV file.
    skip_header : bool
        Whether to skip the first row.

    Returns
    -------
    list
        List of transactions, where each transaction is a list of items.
    """
    transactions = []

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter)

        if skip_header:
            next(reader, None)

        for row in reader:
            # Filter out empty items
            transaction = [item.strip() for item in row if item.strip()]
            if transaction:
                transactions.append(transaction)

    return transactions


def convert_transactions_to_sketches(
    transactions: list,
    output_path: str,
    verbosity: int = 0,
    lg_k: int = 12,
):
    """
    Convert transactions to theta sketches and write to CSV.

    Parameters
    ----------
    transactions : list
        List of transactions.
    output_path : str
        Path to the output CSV file.
    verbosity : int
        Verbosity level.
    lg_k : int
        Log base 2 of sketch size. Default 12 (size = 4096).
        Higher values = more accurate but more memory.
    """
    if verbosity > 0:
        print(f"Processing {len(transactions)} transactions...")

    # Build transaction indices for each item
    indices_by_item = defaultdict(set)
    for i, transaction in enumerate(transactions):
        for item in transaction:
            indices_by_item[item].add(i)

    if verbosity > 0:
        print(f"Found {len(indices_by_item)} unique items")

    # Create output directory if needed
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Write sketches to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Write total sketch
        if verbosity > 0:
            print("Creating total sketch...")

        total_sketch = create_sketch_from_transaction_ids(
            set(range(len(transactions))), lg_k=lg_k
        )
        writer.writerow(['total', serialize_sketch_to_base64(total_sketch)])

        if verbosity > 0:
            print(f"Total count: {total_sketch.get_estimate():.0f}")
            print(f"Sketch size (lg_k): {lg_k} (k = {2**lg_k})")

        # Write item sketches
        if verbosity > 0:
            print("Creating item sketches...")

        for item, indices in sorted(indices_by_item.items()):
            sketch = create_sketch_from_transaction_ids(indices, lg_k=lg_k)
            writer.writerow([item, serialize_sketch_to_base64(sketch)])

            if verbosity > 1:
                count = sketch.get_estimate()
                support = count / len(transactions)
                print(f"  {item}: count={count:.0f}, support={support:.3f}")

    if verbosity > 0:
        print(f"\nSketches written to: {output_path}")


def read_transactions_from_list(
    input_path: str,
    skip_header: bool = False,
) -> list:
    """
    Read transactions where each line is a transaction with items separated by spaces.

    Parameters
    ----------
    input_path : str
        Path to the input file.
    skip_header : bool
        Whether to skip the first line.

    Returns
    -------
    list
        List of transactions.
    """
    transactions = []

    with open(input_path, 'r', encoding='utf-8') as f:
        if skip_header:
            next(f, None)

        for line in f:
            items = line.strip().split()
            if items:
                transactions.append(items)

    return transactions


def main():
    """Main entry point for the conversion script."""
    parser = argparse.ArgumentParser(
        description="Convert transaction data to theta sketches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert CSV file with comma delimiter
  python convert_to_sketches.py --input transactions.csv --output sketches.csv

  # Convert CSV with custom delimiter
  python convert_to_sketches.py --input data.csv --output sketches.csv --delimiter ';'

  # Convert space-separated file
  python convert_to_sketches.py --input data.txt --output sketches.csv --format list

  # With header row
  python convert_to_sketches.py --input data.csv --output sketches.csv --skip-header

Input formats:
  CSV (default):
    eggs,bacon,soup
    eggs,bacon,apple
    soup,bacon,banana

  List (--format list):
    eggs bacon soup
    eggs bacon apple
    soup bacon banana
        """
    )

    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to the input transaction file'
    )

    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to the output sketches CSV file'
    )

    parser.add_argument(
        '--format',
        type=str,
        default='csv',
        choices=['csv', 'list'],
        help='Input file format (csv or list)'
    )

    parser.add_argument(
        '--delimiter',
        type=str,
        default=',',
        help='Delimiter for CSV format (default: comma)'
    )

    parser.add_argument(
        '--skip-header',
        action='store_true',
        help='Skip the first row/line of the input file'
    )

    parser.add_argument(
        '--sketch-lg-k',
        type=int,
        default=12,
        help='Log base 2 of sketch size (default: 12, size=4096). Range: 4-26'
    )

    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        default=1,
        choices=[0, 1, 2],
        help='Verbosity level (0=quiet, 1=normal, 2=verbose)'
    )

    args = parser.parse_args()

    # Read transactions
    try:
        if args.format == 'csv':
            transactions = read_transactions_from_csv(
                args.input,
                delimiter=args.delimiter,
                skip_header=args.skip_header,
            )
        else:  # list format
            transactions = read_transactions_from_list(
                args.input,
                skip_header=args.skip_header,
            )
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    if not transactions:
        print("Error: No transactions found in input file")
        sys.exit(1)

    # Validate sketch_lg_k
    if not 4 <= args.sketch_lg_k <= 26:
        print(f"Error: sketch_lg_k must be between 4 and 26, got {args.sketch_lg_k}")
        sys.exit(1)

    # Convert to sketches
    try:
        convert_transactions_to_sketches(
            transactions,
            args.output,
            verbosity=args.verbosity,
            lg_k=args.sketch_lg_k,
        )
    except Exception as e:
        print(f"Error converting to sketches: {e}")
        sys.exit(1)

    if args.verbosity > 0:
        print("\nConversion complete!")
        print(f"You can now run: python apriori_sketch.py --config config.json")


if __name__ == "__main__":
    main()

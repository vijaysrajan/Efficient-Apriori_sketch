#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full outer join implementation for frequent itemsets.

This module implements the logic to join frequent itemsets from yes and no
cases, computing comparison metrics.
"""

import csv
from pathlib import Path
from typing import Dict, Set, Tuple


def full_outer_join_itemsets(
    yes_itemsets: Dict[int, Dict[tuple, float]],
    no_itemsets: Dict[int, Dict[tuple, float]],
    yes_total: float,
    no_total: float,
    min_support_yes: float,
    min_support_no: float,
    output_path: str,
    item_separator: str = " && ",
    use_equi_join: bool = False,
):
    """
    Perform a full outer join on two sets of frequent itemsets.

    This function joins frequent itemsets from yes and no cases, computing
    counts and percentages for comparison.

    Parameters
    ----------
    yes_itemsets : dict
        Dictionary of {level: {itemset: count}} for yes case.
    no_itemsets : dict
        Dictionary of {level: {itemset: count}} for no case.
    yes_total : float
        Total count for yes case.
    no_total : float
        Total count for no case.
    min_support_yes : float
        Minimum support threshold used for yes case (0-1).
    min_support_no : float
        Minimum support threshold used for no case (0-1).
    output_path : str
        Path to output CSV file.
    item_separator : str
        Separator for items in itemset strings (default: " && ").
    use_equi_join : bool
        If True, only output itemsets in both yes and no cases (default: False).

    Output Format
    -------------
    CSV with columns:
    - Level: The level (size) of the itemset
    - Frequent_itemset: String representation of the itemset
    - Yes_case_count: Count in yes case (or empty string if not present in full outer join)
    - No_case_count: Count in no case (or empty string if not present in full outer join)
    - Total: Sum of yes and no counts
    - Yes_percentage: Percentage of yes in total (rounded to 3 decimals)

    When use_equi_join=True, only itemsets appearing in both cases are included.
    When use_equi_join=False, all itemsets are included with empty strings for missing counts.

    Examples
    --------
    >>> yes_items = {1: {('A',): 100.0, ('B',): 80.0}, 2: {('A', 'B'): 60.0}}
    >>> no_items = {1: {('A',): 50.0, ('C',): 40.0}, 2: {('A', 'C'): 30.0}}
    >>> full_outer_join_itemsets(  # doctest: +SKIP
    ...     yes_items, no_items, 200.0, 100.0, 0.3, 0.3,
    ...     "output.csv", " && "
    ... )
    """
    # Create parent directory if needed
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Collect all unique (level, itemset) pairs
    all_pairs: Set[Tuple[int, tuple]] = set()

    for level, itemsets_dict in yes_itemsets.items():
        for itemset in itemsets_dict.keys():
            all_pairs.add((level, itemset))

    for level, itemsets_dict in no_itemsets.items():
        for itemset in itemsets_dict.keys():
            all_pairs.add((level, itemset))

    # Build output rows
    rows = []

    for level, itemset in all_pairs:
        # Determine where the itemset is seen
        in_yes = level in yes_itemsets and itemset in yes_itemsets[level]
        in_no = level in no_itemsets and itemset in no_itemsets[level]

        # For equi-join, skip if not in both
        if use_equi_join and not (in_yes and in_no):
            continue

        # Get yes count
        if in_yes:
            yes_count = yes_itemsets[level][itemset]
            yes_count_present = True
        else:
            # Use empty string for missing in full outer join
            yes_count = 0.0  # For calculation purposes
            yes_count_present = False

        # Get no count
        if in_no:
            no_count = no_itemsets[level][itemset]
            no_count_present = True
        else:
            # Use empty string for missing in full outer join
            no_count = 0.0  # For calculation purposes
            no_count_present = False

        # Compute totals and percentage
        total = yes_count + no_count
        yes_percentage = round((yes_count * 100.0 / total), 3) if total > 0 else 0.0

        # Format itemset string
        if level == 1:
            itemset_str = itemset[0]
        else:
            itemset_str = item_separator.join(sorted(itemset))

        rows.append(
            {
                "level": level,
                "itemset": itemset,
                "itemset_str": itemset_str,
                "yes_count": yes_count,
                "yes_count_present": yes_count_present,
                "no_count": no_count,
                "no_count_present": no_count_present,
                "total": total,
                "yes_percentage": yes_percentage,
            }
        )

    # Sort rows: by level, then by yes_percentage (descending), then by itemset
    rows.sort(key=lambda r: (r["level"], -r["yes_percentage"], r["itemset"]))

    # Write to CSV
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(
            [
                "Level",
                "Frequent_itemset",
                "Yes_case_count",
                "No_case_count",
                "Total",
                "Yes_percentage",
            ]
        )

        # Write data rows
        for row in rows:
            # Format counts: use empty string if not present, otherwise format as integer
            yes_count_str = f"{row['yes_count']:.0f}" if row["yes_count_present"] else ""
            no_count_str = f"{row['no_count']:.0f}" if row["no_count_present"] else ""

            writer.writerow(
                [
                    row["level"],
                    row["itemset_str"],
                    yes_count_str,
                    no_count_str,
                    f"{row['total']:.0f}",
                    f"{row['yes_percentage']:.3f}",
                ]
            )


def read_joined_itemsets(csv_path: str) -> list:
    """
    Read joined itemsets from a CSV file.

    Utility function for loading previously saved joined itemsets.

    Parameters
    ----------
    csv_path : str
        Path to the joined itemsets CSV file.

    Returns
    -------
    list
        List of dictionaries, each containing the joined itemset data.

    Examples
    --------
    >>> rows = read_joined_itemsets("output.csv")  # doctest: +SKIP
    >>> len(rows)  # doctest: +SKIP
    15
    >>> rows[0]["Level"]  # doctest: +SKIP
    1
    """
    rows = []

    with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # Handle empty strings for counts
            yes_count = float(row["Yes_case_count"]) if row["Yes_case_count"] else 0.0
            no_count = float(row["No_case_count"]) if row["No_case_count"] else 0.0

            rows.append(
                {
                    "Level": int(row["Level"]),
                    "Frequent_itemset": row["Frequent_itemset"],
                    "Yes_case_count": yes_count,
                    "No_case_count": no_count,
                    "Total": float(row["Total"]),
                    "Yes_percentage": float(row["Yes_percentage"]),
                }
            )

    return rows


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v"])

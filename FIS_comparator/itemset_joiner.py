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

    Output Format
    -------------
    CSV with columns:
    - Level: The level (size) of the itemset
    - Frequent_itemset: String representation of the itemset
    - Frequent_item_set_seen_in: "both", "yes", or "no"
    - Yes_case_count: Count in yes case (or min_support * total if not present)
    - No_case_count: Count in no case (or min_support * total if not present)
    - Total: Sum of yes and no counts
    - Yes_percentage: Percentage of yes in total (rounded to 3 decimals)

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

        if in_yes and in_no:
            seen_in = "both"
        elif in_yes:
            seen_in = "yes"
        else:
            seen_in = "no"

        # Get yes count
        if in_yes:
            yes_count = yes_itemsets[level][itemset]
        else:
            # Use min_support * total as default
            yes_count = min_support_yes * yes_total

        # Get no count
        if in_no:
            no_count = no_itemsets[level][itemset]
        else:
            # Use min_support * total as default
            no_count = min_support_no * no_total

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
                "seen_in": seen_in,
                "yes_count": yes_count,
                "no_count": no_count,
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
                "Frequent_item_set_seen_in",
                "Yes_case_count",
                "No_case_count",
                "Total",
                "Yes_percentage",
            ]
        )

        # Write data rows
        for row in rows:
            writer.writerow(
                [
                    row["level"],
                    row["itemset_str"],
                    row["seen_in"],
                    f"{row['yes_count']:.1f}",
                    f"{row['no_count']:.1f}",
                    f"{row['total']:.1f}",
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
            rows.append(
                {
                    "Level": int(row["Level"]),
                    "Frequent_itemset": row["Frequent_itemset"],
                    "Frequent_item_set_seen_in": row["Frequent_item_set_seen_in"],
                    "Yes_case_count": float(row["Yes_case_count"]),
                    "No_case_count": float(row["No_case_count"]),
                    "Total": float(row["Total"]),
                    "Yes_percentage": float(row["Yes_percentage"]),
                }
            )

    return rows


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v"])

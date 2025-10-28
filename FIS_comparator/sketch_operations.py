#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sketch manipulation operations for FIS comparator.

This module provides functions to manipulate theta sketches for the
comparator, including intersection and A-not-B operations.
"""

import csv
import sys
import base64
from typing import Dict, Optional, List, Tuple
from datasketches import (
    compact_theta_sketch,
    theta_intersection,
    theta_a_not_b,
    theta_union,
)

# Increase CSV field size limit to handle large base64-encoded sketches
csv.field_size_limit(sys.maxsize)


def intersect_sketches(
    sketches_dict: Dict[str, compact_theta_sketch],
    target_sketch: compact_theta_sketch,
) -> Dict[str, compact_theta_sketch]:
    """
    Intersect all sketches in the dictionary with a target sketch.

    Parameters
    ----------
    sketches_dict : dict
        Dictionary mapping item names to their theta sketches.
    target_sketch : compact_theta_sketch
        The sketch to intersect with each sketch in the dictionary.

    Returns
    -------
    dict
        New dictionary with intersected sketches.

    Examples
    --------
    >>> from datasketches import update_theta_sketch
    >>> sketch1 = update_theta_sketch()
    >>> sketch1.update(1)
    >>> sketch1.update(2)
    >>> sketch1.update(3)
    >>> sketch2 = update_theta_sketch()
    >>> sketch2.update(2)
    >>> sketch2.update(3)
    >>> sketch2.update(4)
    >>> target = update_theta_sketch()
    >>> target.update(1)
    >>> target.update(2)
    >>> result = intersect_sketches(
    ...     {"item1": sketch1.compact(), "item2": sketch2.compact()},
    ...     target.compact()
    ... )
    >>> result["item1"].get_estimate()
    1.0
    >>> result["item2"].get_estimate()
    1.0
    """
    intersected = {}

    for item_name, item_sketch in sketches_dict.items():
        # Create intersection object
        intersection = theta_intersection()

        # Add both sketches to the intersection
        intersection.update(item_sketch)
        intersection.update(target_sketch)

        # Get the result
        result_sketch = intersection.get_result()
        intersected[item_name] = result_sketch

    return intersected


def a_not_b_sketches(
    sketches_dict: Dict[str, compact_theta_sketch],
    subtract_sketch: compact_theta_sketch,
) -> Dict[str, compact_theta_sketch]:
    """
    Perform A-not-B operation on all sketches (subtract_sketch subtracted from each).

    For each sketch A in the dictionary, computes A - B where B is subtract_sketch.

    Parameters
    ----------
    sketches_dict : dict
        Dictionary mapping item names to their theta sketches (the A sketches).
    subtract_sketch : compact_theta_sketch
        The sketch to subtract from each sketch (the B sketch).

    Returns
    -------
    dict
        New dictionary with A-not-B results.

    Examples
    --------
    >>> from datasketches import update_theta_sketch
    >>> sketch1 = update_theta_sketch()
    >>> sketch1.update(1)
    >>> sketch1.update(2)
    >>> sketch1.update(3)
    >>> sketch2 = update_theta_sketch()
    >>> sketch2.update(2)
    >>> sketch2.update(3)
    >>> sketch2.update(4)
    >>> subtract = update_theta_sketch()
    >>> subtract.update(2)
    >>> result = a_not_b_sketches(
    ...     {"item1": sketch1.compact(), "item2": sketch2.compact()},
    ...     subtract.compact()
    ... )
    >>> result["item1"].get_estimate()
    2.0
    >>> result["item2"].get_estimate()
    2.0
    """
    result_dict = {}

    for item_name, item_sketch in sketches_dict.items():
        # Create A-not-B object
        anotb = theta_a_not_b()

        # Compute A - B
        result_sketch = anotb.compute(item_sketch, subtract_sketch)
        result_dict[item_name] = result_sketch

    return result_dict


def compute_total_sketch(
    sketches_dict: Dict[str, compact_theta_sketch]
) -> compact_theta_sketch:
    """
    Compute the union of all sketches to get total count.

    Parameters
    ----------
    sketches_dict : dict
        Dictionary mapping item names to their theta sketches.

    Returns
    -------
    compact_theta_sketch
        Union sketch representing the total.

    Examples
    --------
    >>> from datasketches import update_theta_sketch
    >>> sketch1 = update_theta_sketch()
    >>> sketch1.update(1)
    >>> sketch1.update(2)
    >>> sketch2 = update_theta_sketch()
    >>> sketch2.update(2)
    >>> sketch2.update(3)
    >>> total = compute_total_sketch(
    ...     {"item1": sketch1.compact(), "item2": sketch2.compact()}
    ... )
    >>> total.get_estimate()
    3.0
    """
    union = theta_union()

    for sketch in sketches_dict.values():
        union.update(sketch)

    return union.get_result()


def save_sketches_to_csv(
    sketches_dict: Dict[str, compact_theta_sketch],
    total_sketch: compact_theta_sketch,
    csv_path: str,
):
    """
    Save sketches to a CSV file in the standard format.

    Parameters
    ----------
    sketches_dict : dict
        Dictionary mapping item names to their theta sketches.
    total_sketch : compact_theta_sketch
        The total count sketch.
    csv_path : str
        Path to the output CSV file.

    Examples
    --------
    >>> from datasketches import update_theta_sketch
    >>> sketch1 = update_theta_sketch()
    >>> sketch1.update(1)
    >>> total = update_theta_sketch()
    >>> total.update(1)
    >>> total.update(2)
    >>> save_sketches_to_csv(  # doctest: +SKIP
    ...     {"item1": sketch1.compact()},
    ...     total.compact(),
    ...     "output.csv"
    ... )
    """
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Write total sketch first
        total_b64 = base64.b64encode(total_sketch.serialize()).decode("utf-8")
        writer.writerow(["total", total_b64])

        # Write item sketches
        for item_name, sketch in sorted(sketches_dict.items()):
            sketch_b64 = base64.b64encode(sketch.serialize()).decode("utf-8")
            writer.writerow([item_name, sketch_b64])


def load_sketches_from_csv(
    csv_path: str,
) -> tuple[Dict[str, compact_theta_sketch], compact_theta_sketch, float]:
    """
    Load sketches from a CSV file.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file.

    Returns
    -------
    tuple
        (sketches_dict, total_sketch, total_count) where:
        - sketches_dict: Dictionary mapping item names to sketches
        - total_sketch: The total count sketch
        - total_count: The total count estimate

    Examples
    --------
    >>> sketches, total_sketch, total_count = load_sketches_from_csv(  # doctest: +SKIP
    ...     "input.csv"
    ... )
    >>> len(sketches)  # doctest: +SKIP
    10
    """
    sketches_dict: Dict[str, compact_theta_sketch] = {}
    total_sketch: Optional[compact_theta_sketch] = None
    total_count = 0.0

    with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)

        for row_idx, row in enumerate(reader):
            if len(row) != 2:
                raise ValueError(
                    f"Invalid CSV format at row {row_idx + 1}. "
                    f"Expected 2 columns, got {len(row)}"
                )

            item_name, sketch_b64 = row

            # Decode the sketch
            try:
                sketch_bytes = base64.b64decode(sketch_b64)
                sketch = compact_theta_sketch.deserialize(sketch_bytes)
            except Exception as e:
                raise ValueError(f"Failed to decode sketch at row {row_idx + 1}: {e}")

            # First row is the total
            if row_idx == 0:
                if item_name.lower() == "total" or item_name == "":
                    total_sketch = sketch
                    total_count = sketch.get_estimate()
                    continue
                else:
                    # If first row is not total, treat it as regular item
                    pass

            # Store item sketch
            sketches_dict[item_name] = sketch

    # If no total was provided, compute it
    if total_sketch is None:
        if sketches_dict:
            total_sketch = compute_total_sketch(sketches_dict)
            total_count = total_sketch.get_estimate()
        else:
            raise ValueError("No sketches found in CSV file")

    return sketches_dict, total_sketch, total_count


def filter_excluded_items(
    sketches_dict: Dict[str, compact_theta_sketch],
    excluded_items: List[str],
) -> Dict[str, compact_theta_sketch]:
    """
    Remove excluded items from sketch dictionary.

    Parameters
    ----------
    sketches_dict : dict
        Dictionary mapping item names to their theta sketches.
    excluded_items : list of str
        List of item names to exclude.

    Returns
    -------
    dict
        New dictionary with excluded items removed.

    Examples
    --------
    >>> from datasketches import update_theta_sketch
    >>> sketch1 = update_theta_sketch()
    >>> sketch1.update(1)
    >>> sketch2 = update_theta_sketch()
    >>> sketch2.update(2)
    >>> sketches = {"item1": sketch1.compact(), "item2": sketch2.compact()}
    >>> filtered = filter_excluded_items(sketches, ["item1"])
    >>> "item1" in filtered
    False
    >>> "item2" in filtered
    True
    """
    return {k: v for k, v in sketches_dict.items() if k not in excluded_items}


def apply_filter_item(
    sketches_dict: Dict[str, compact_theta_sketch],
    filter_item: str,
) -> Tuple[Dict[str, compact_theta_sketch], compact_theta_sketch]:
    """
    Intersect all sketches with a filter item sketch.

    This function extracts the filter_item sketch from the dictionary,
    then intersects all other sketches with it. The filter_item itself
    is removed from the output dictionary.

    Parameters
    ----------
    sketches_dict : dict
        Dictionary mapping item names to their theta sketches.
    filter_item : str
        Name of the filter item (must exist in sketches_dict).

    Returns
    -------
    tuple
        (filtered_sketches_dict, new_total_sketch) where:
        - filtered_sketches_dict: Dictionary with all sketches intersected with filter
        - new_total_sketch: The filter item's sketch (new total)

    Raises
    ------
    ValueError
        If filter_item is not found in sketches_dict.

    Examples
    --------
    >>> from datasketches import update_theta_sketch
    >>> sketch1 = update_theta_sketch()
    >>> for i in [1, 2, 3]:
    ...     sketch1.update(i)
    >>> sketch2 = update_theta_sketch()
    >>> for i in [2, 3, 4]:
    ...     sketch2.update(i)
    >>> filter_sk = update_theta_sketch()
    >>> for i in [2, 3]:
    ...     filter_sk.update(i)
    >>> sketches = {
    ...     "item1": sketch1.compact(),
    ...     "item2": sketch2.compact(),
    ...     "filter": filter_sk.compact()
    ... }
    >>> filtered, total = apply_filter_item(sketches, "filter")
    >>> "filter" in filtered
    False
    >>> filtered["item1"].get_estimate()
    2.0
    """
    if filter_item not in sketches_dict:
        raise ValueError(
            f"Filter item '{filter_item}' not found in sketches dictionary"
        )

    # Extract the filter sketch
    filter_sketch = sketches_dict[filter_item]

    # Create new dictionary without the filter item
    sketches_without_filter = {
        k: v for k, v in sketches_dict.items() if k != filter_item
    }

    # Intersect all sketches with the filter
    filtered_sketches = intersect_sketches(sketches_without_filter, filter_sketch)

    # The new total is the filter sketch itself
    new_total_sketch = filter_sketch

    return filtered_sketches, new_total_sketch


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v"])

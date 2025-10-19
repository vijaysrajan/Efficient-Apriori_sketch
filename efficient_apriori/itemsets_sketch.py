#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Theta sketch-based implementation of the Apriori algorithm.
"""

import typing
import numbers
from efficient_apriori.itemsets import join_step, prune_step, apriori_gen
from efficient_apriori.sketch_support import (
    ThetaSketchManager,
    ItemsetCountSketch,
)


def itemsets_from_sketches(
    sketch_manager: ThetaSketchManager,
    min_support: float,
    max_length: int = 8,
    verbosity: int = 0,
    include_all_level1: bool = False,
) -> typing.Tuple[typing.Dict[int, typing.Dict[tuple, float]], float]:
    """
    Compute itemsets from theta sketches using the Apriori algorithm.

    This function is analogous to itemsets_from_transactions but works with
    theta sketches instead of raw transactions. It computes frequent itemsets
    by using sketch intersections for counting.

    Parameters
    ----------
    sketch_manager : ThetaSketchManager
        Manager containing theta sketches for each item.
    min_support : float
        The minimum support of the itemsets, i.e. the minimum frequency as a
        percentage (between 0 and 1).
    max_length : int
        The maximum length of the itemsets.
    verbosity : int
        The level of detail printing when the algorithm runs. Either 0, 1 or 2.
    include_all_level1 : bool
        If True, include all level 1 items in the output regardless of
        min_support. Items below min_support will not be used for generating
        higher level itemsets.

    Returns
    -------
    tuple
        (large_itemsets, total_count) where:
        - large_itemsets is a dict of {level: {itemset: count}}
        - total_count is the total count estimate

    Examples
    --------
    >>> # Assuming we have a sketch manager
    >>> manager = ThetaSketchManager("sketches.csv")  # doctest: +SKIP
    >>> itemsets, total = itemsets_from_sketches(  # doctest: +SKIP
    ...     manager, min_support=0.3, max_length=3
    ... )
    >>> print(itemsets[1])  # doctest: +SKIP
    {('item1',): 150.0, ('item2',): 200.0}
    """

    # STEP 0 - Validate inputs
    # -------------------------
    if not (isinstance(min_support, numbers.Number) and (0 <= min_support <= 1)):
        raise ValueError("`min_support` must be a number between 0 and 1.")

    # Get total count
    total_count = sketch_manager.total_count
    if total_count == 0:
        return dict(), 0.0

    # STEP 1 - Generate all large itemsets of size 1
    # -----------------------------------------------
    if verbosity > 0:
        print("Generating itemsets from theta sketches.")
        print(" Counting itemsets of length 1.")

    # Get counts for all single items
    candidates: typing.Dict[tuple, float] = {}
    all_level1_items: typing.Dict[tuple, float] = {}

    for item in sketch_manager.items:
        count = sketch_manager.get_count(item)
        itemset = (item,)
        all_level1_items[itemset] = count

        # Check if it meets min_support
        support = count / total_count
        if support >= min_support:
            candidates[itemset] = count

    # Determine what to include in level 1 output
    if include_all_level1:
        # Include all level 1 items in output
        large_itemsets: typing.Dict[int, typing.Dict[tuple, float]] = {
            1: all_level1_items.copy()
        }
        # But only use items meeting min_support for further processing
        level1_for_processing = candidates
    else:
        # Only include items meeting min_support
        large_itemsets = {1: candidates.copy()}
        level1_for_processing = candidates

    if verbosity > 0:
        print(f"  Found {len(sketch_manager.items)} candidate itemsets of length 1.")
        print(f"  Found {len(level1_for_processing)} large itemsets of length 1 (above min_support).")
        if include_all_level1:
            print(f"  Output includes all {len(all_level1_items)} level 1 items.")
    if verbosity > 1:
        print(f"    {list(level1_for_processing.keys())}")

    # If no large itemsets meeting min_support, return
    if not level1_for_processing:
        return large_itemsets, total_count

    # STEP 2 - Build up the size of the itemsets
    # -------------------------------------------
    k = 2
    # Use level1_for_processing (items meeting min_support) for generating higher levels
    processing_itemsets = {1: level1_for_processing}

    while processing_itemsets.get(k - 1) and (max_length != 1):
        if verbosity > 0:
            print(f" Counting itemsets of length {k}.")

        # STEP 2a) - Build candidate itemsets of size k
        itemsets_list = sorted(item for item in processing_itemsets[k - 1].keys())

        # Generate candidates of length k
        C_k: typing.List[tuple] = list(apriori_gen(itemsets_list))

        if verbosity > 0:
            print(f"  Found {len(C_k)} candidate itemsets of length {k}.")
        if verbosity > 1:
            print(f"   {C_k}")

        if not C_k:
            break

        # STEP 2b) - Count support for candidates using sketch intersections
        if verbosity > 1:
            print("    Computing sketch intersections.")

        found_itemsets: typing.Dict[tuple, float] = {}
        for candidate in C_k:
            count = sketch_manager.get_itemset_count(candidate)
            support = count / total_count

            if support >= min_support:
                found_itemsets[candidate] = count

        if not found_itemsets:
            break

        # Add to both output and processing dicts
        large_itemsets[k] = found_itemsets.copy()
        processing_itemsets[k] = found_itemsets.copy()

        if verbosity > 0:
            num_found = len(large_itemsets[k])
            print(f"  Found {num_found} large itemsets of length {k}.")
        if verbosity > 1:
            print(f"   {list(large_itemsets[k].keys())}")

        k += 1

        # Break if we've reached max_length
        if k > max_length:
            break

    if verbosity > 0:
        print("Itemset generation terminated.\n")

    return large_itemsets, total_count


def itemsets_from_sketches_with_details(
    sketch_manager: ThetaSketchManager,
    min_support: float,
    max_length: int = 8,
    verbosity: int = 0,
    include_all_level1: bool = False,
) -> typing.Tuple[typing.Dict[int, typing.Dict[tuple, ItemsetCountSketch]], float]:
    """
    Compute itemsets from theta sketches with detailed sketch information.

    Similar to itemsets_from_sketches but returns ItemsetCountSketch objects
    containing both counts and sketch objects.

    Parameters
    ----------
    sketch_manager : ThetaSketchManager
        Manager containing theta sketches for each item.
    min_support : float
        The minimum support of the itemsets (between 0 and 1).
    max_length : int
        The maximum length of the itemsets.
    verbosity : int
        The level of detail printing when the algorithm runs.
    include_all_level1 : bool
        If True, include all level 1 items regardless of min_support.

    Returns
    -------
    tuple
        (itemsets_with_sketches, total_count) where:
        - itemsets_with_sketches is a dict of {level: {itemset: ItemsetCountSketch}}
        - total_count is the total count estimate

    Examples
    --------
    >>> manager = ThetaSketchManager("sketches.csv")  # doctest: +SKIP
    >>> itemsets, total = itemsets_from_sketches_with_details(  # doctest: +SKIP
    ...     manager, min_support=0.3
    ... )
    >>> itemsets[1][('item1',)].itemset_count  # doctest: +SKIP
    150.0
    """
    # STEP 0 - Validate inputs
    if not (isinstance(min_support, numbers.Number) and (0 <= min_support <= 1)):
        raise ValueError("`min_support` must be a number between 0 and 1.")

    total_count = sketch_manager.total_count
    if total_count == 0:
        return dict(), 0.0

    # STEP 1 - Generate level 1 itemsets
    if verbosity > 0:
        print("Generating itemsets from theta sketches (with details).")
        print(" Counting itemsets of length 1.")

    candidates: typing.Dict[tuple, ItemsetCountSketch] = {}
    all_level1_items: typing.Dict[tuple, ItemsetCountSketch] = {}

    for item in sketch_manager.items:
        sketch = sketch_manager.get_sketch(item)
        count = sketch.get_estimate() if sketch else 0.0
        itemset = (item,)

        itemset_obj = ItemsetCountSketch(
            itemset_count=count,
            sketch=sketch,
        )
        all_level1_items[itemset] = itemset_obj

        support = count / total_count
        if support >= min_support:
            candidates[itemset] = itemset_obj

    # Determine output based on include_all_level1
    if include_all_level1:
        large_itemsets: typing.Dict[int, typing.Dict[tuple, ItemsetCountSketch]] = {
            1: all_level1_items.copy()
        }
        level1_for_processing = candidates
    else:
        large_itemsets = {1: candidates.copy()}
        level1_for_processing = candidates

    if verbosity > 0:
        print(f"  Found {len(sketch_manager.items)} candidate itemsets of length 1.")
        print(f"  Found {len(level1_for_processing)} large itemsets of length 1 (above min_support).")

    if not level1_for_processing:
        return large_itemsets, total_count

    # STEP 2 - Build higher level itemsets
    k = 2
    processing_itemsets = {1: level1_for_processing}

    while processing_itemsets.get(k - 1) and (max_length != 1):
        if verbosity > 0:
            print(f" Counting itemsets of length {k}.")

        itemsets_list = sorted(item for item in processing_itemsets[k - 1].keys())
        C_k: typing.List[tuple] = list(apriori_gen(itemsets_list))

        if verbosity > 0:
            print(f"  Found {len(C_k)} candidate itemsets of length {k}.")

        if not C_k:
            break

        found_itemsets: typing.Dict[tuple, ItemsetCountSketch] = {}
        for candidate in C_k:
            sketch = sketch_manager.get_itemset_sketch(candidate)
            if sketch is None:
                continue

            count = sketch.get_estimate()
            support = count / total_count

            if support >= min_support:
                itemset_obj = ItemsetCountSketch(
                    itemset_count=count,
                    sketch=sketch,
                )
                found_itemsets[candidate] = itemset_obj

        if not found_itemsets:
            break

        large_itemsets[k] = found_itemsets.copy()
        processing_itemsets[k] = found_itemsets.copy()

        if verbosity > 0:
            print(f"  Found {len(large_itemsets[k])} large itemsets of length {k}.")

        k += 1
        if k > max_length:
            break

    if verbosity > 0:
        print("Itemset generation terminated.\n")

    return large_itemsets, total_count


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v"])

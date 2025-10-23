#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core comparison logic for FIS-based Comparator.

This module implements the three main workflows:
1. Two-file comparison
2. Single-file with one target (intersection and A-not-B)
3. Single-file with two targets (two intersections)
"""

import sys
from pathlib import Path
from typing import Dict, Tuple

# Add parent directory to path to import efficient_apriori
sys.path.insert(0, str(Path(__file__).parent.parent))

from efficient_apriori.sketch_support import ThetaSketchManager
from efficient_apriori.itemsets_sketch import itemsets_from_sketches
from efficient_apriori.rules_sketch import write_itemsets_to_csv

from .comparator_config import TwoFileComparatorConfig, SingleFileComparatorConfig
from .sketch_operations import (
    intersect_sketches,
    a_not_b_sketches,
    compute_total_sketch,
    load_sketches_from_csv,
    save_sketches_to_csv,
)
from .itemset_joiner import full_outer_join_itemsets


def run_two_file_comparison(
    config: TwoFileComparatorConfig, verbosity: int = 0
) -> Tuple[
    Dict[int, Dict[tuple, float]],
    Dict[int, Dict[tuple, float]],
    float,
    float,
]:
    """
    Run comparison with two separate CSV files (yes and no cases).

    Parameters
    ----------
    config : TwoFileComparatorConfig
        Configuration for two-file mode.
    verbosity : int
        Verbosity level (0, 1, or 2).

    Returns
    -------
    tuple
        (yes_itemsets, no_itemsets, yes_total, no_total)

    Examples
    --------
    >>> config = TwoFileComparatorConfig(...)  # doctest: +SKIP
    >>> yes_items, no_items, yes_total, no_total = run_two_file_comparison(  # doctest: +SKIP
    ...     config, verbosity=1
    ... )
    """
    if verbosity > 0:
        print("=" * 70)
        print("FIS-based Comparator: Two-File Mode")
        print("=" * 70)

    # Load yes case sketches
    if verbosity > 0:
        print(f"\nLoading YES case sketches from: {config.input_csv_path_for_yes_case}")

    yes_manager = ThetaSketchManager(config.input_csv_path_for_yes_case)

    if verbosity > 0:
        print(f"  Loaded {len(yes_manager.items)} items")
        print(f"  Total count estimate: {yes_manager.total_count:.2f}")

    # Load no case sketches
    if verbosity > 0:
        print(f"\nLoading NO case sketches from: {config.input_csv_path_for_no_case}")

    no_manager = ThetaSketchManager(config.input_csv_path_for_no_case)

    if verbosity > 0:
        print(f"  Loaded {len(no_manager.items)} items")
        print(f"  Total count estimate: {no_manager.total_count:.2f}")

    # Run Apriori on yes case
    if verbosity > 0:
        print(f"\nRunning Apriori on YES case...")
        print(f"  Min support: {config.min_support_for_yes_case}")
        print(f"  Max levels: {config.max_levels}")

    yes_itemsets, yes_total = itemsets_from_sketches(
        sketch_manager=yes_manager,
        min_support=config.min_support_for_yes_case,
        max_length=config.max_levels,
        verbosity=verbosity,
        include_all_level1=config.include_all_level1,
    )

    if verbosity > 0:
        print(f"\nFrequent itemsets found in YES case:")
        for level in sorted(yes_itemsets.keys()):
            print(f"  Level {level}: {len(yes_itemsets[level])} itemsets")

    # Write yes itemsets
    if verbosity > 0:
        print(f"\nWriting YES itemsets to: {config.output_itemsets_path_yes_case}")

    write_itemsets_to_csv(
        itemsets=yes_itemsets,
        total_count=yes_total,
        output_path=config.output_itemsets_path_yes_case,
        item_separator=config.item_separator,
    )

    # Run Apriori on no case
    if verbosity > 0:
        print(f"\nRunning Apriori on NO case...")
        print(f"  Min support: {config.min_support_for_no_case}")
        print(f"  Max levels: {config.max_levels}")

    no_itemsets, no_total = itemsets_from_sketches(
        sketch_manager=no_manager,
        min_support=config.min_support_for_no_case,
        max_length=config.max_levels,
        verbosity=verbosity,
        include_all_level1=config.include_all_level1,
    )

    if verbosity > 0:
        print(f"\nFrequent itemsets found in NO case:")
        for level in sorted(no_itemsets.keys()):
            print(f"  Level {level}: {len(no_itemsets[level])} itemsets")

    # Write no itemsets
    if verbosity > 0:
        print(f"\nWriting NO itemsets to: {config.output_itemsets_path_no_case}")

    write_itemsets_to_csv(
        itemsets=no_itemsets,
        total_count=no_total,
        output_path=config.output_itemsets_path_no_case,
        item_separator=config.item_separator,
    )

    # Perform full outer join
    if verbosity > 0:
        print(f"\nPerforming full outer join...")
        print(f"Writing joined itemsets to: {config.output_itemsets_joined}")

    full_outer_join_itemsets(
        yes_itemsets=yes_itemsets,
        no_itemsets=no_itemsets,
        yes_total=yes_total,
        no_total=no_total,
        min_support_yes=config.min_support_for_yes_case,
        min_support_no=config.min_support_for_no_case,
        output_path=config.output_itemsets_joined,
        item_separator=config.item_separator,
    )

    if verbosity > 0:
        print("\nTwo-file comparison completed successfully!")

    return yes_itemsets, no_itemsets, yes_total, no_total


def run_single_file_comparison_one_target(
    config: SingleFileComparatorConfig, verbosity: int = 0
) -> Tuple[
    Dict[int, Dict[tuple, float]],
    Dict[int, Dict[tuple, float]],
    float,
    float,
]:
    """
    Run comparison with single file and one target (intersection vs A-not-B).

    YES case: Sketches intersected with target_item_1
    NO case: Sketches with A-not-B (subtract target_item_1)

    Parameters
    ----------
    config : SingleFileComparatorConfig
        Configuration for single-file mode with target_item_0 = None.
    verbosity : int
        Verbosity level (0, 1, or 2).

    Returns
    -------
    tuple
        (yes_itemsets, no_itemsets, yes_total, no_total)

    Examples
    --------
    >>> config = SingleFileComparatorConfig(...)  # doctest: +SKIP
    >>> yes_items, no_items, yes_total, no_total = run_single_file_comparison_one_target(  # doctest: +SKIP
    ...     config, verbosity=1
    ... )
    """
    if verbosity > 0:
        print("=" * 70)
        print("FIS-based Comparator: Single-File Mode (One Target)")
        print("=" * 70)
        print(f"Target item (YES): {config.target_item_1}")
        print(f"NO case: A-not-B with target item")

    # Load sketches
    if verbosity > 0:
        print(f"\nLoading sketches from: {config.input_csv_path}")

    sketches_dict, total_sketch, original_total = load_sketches_from_csv(
        config.input_csv_path
    )

    if verbosity > 0:
        print(f"  Loaded {len(sketches_dict)} items")
        print(f"  Total count estimate: {original_total:.2f}")

    # Extract target item sketch
    if config.target_item_1 not in sketches_dict:
        raise ValueError(
            f"Target item '{config.target_item_1}' not found in input CSV"
        )

    target_sketch = sketches_dict[config.target_item_1]

    if verbosity > 0:
        print(f"\nTarget item count: {target_sketch.get_estimate():.2f}")

    # Create copies without target item
    sketches_without_target = {
        k: v for k, v in sketches_dict.items() if k != config.target_item_1
    }

    # Create YES case: Intersection with target
    if verbosity > 0:
        print(f"\nCreating YES case (intersection with target)...")

    yes_sketches = intersect_sketches(sketches_without_target, target_sketch)
    yes_total_sketch = target_sketch  # Total is the target sketch itself
    yes_total = yes_total_sketch.get_estimate()

    if verbosity > 0:
        print(f"  YES case total count: {yes_total:.2f}")

    # Create NO case: A-not-B with target
    if verbosity > 0:
        print(f"\nCreating NO case (A-not-B with target)...")

    no_sketches = a_not_b_sketches(sketches_without_target, target_sketch)
    no_total_sketch = compute_total_sketch(no_sketches)
    no_total = no_total_sketch.get_estimate()

    if verbosity > 0:
        print(f"  NO case total count: {no_total:.2f}")

    # Create temporary sketch managers for Apriori
    # We'll save to temp files and load them
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as yes_temp_file:
        yes_temp_path = yes_temp_file.name

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as no_temp_file:
        no_temp_path = no_temp_file.name

    try:
        # Save temporary files
        save_sketches_to_csv(yes_sketches, yes_total_sketch, yes_temp_path)
        save_sketches_to_csv(no_sketches, no_total_sketch, no_temp_path)

        # Load as ThetaSketchManagers
        yes_manager = ThetaSketchManager(yes_temp_path)
        no_manager = ThetaSketchManager(no_temp_path)

        # Run Apriori on YES case
        if verbosity > 0:
            print(f"\nRunning Apriori on YES case...")
            print(f"  Min support: {config.min_support_for_yes_case}")

        yes_itemsets, yes_total = itemsets_from_sketches(
            sketch_manager=yes_manager,
            min_support=config.min_support_for_yes_case,
            max_length=config.max_levels,
            verbosity=verbosity,
            include_all_level1=config.include_all_level1,
        )

        if verbosity > 0:
            print(f"\nFrequent itemsets found in YES case:")
            for level in sorted(yes_itemsets.keys()):
                print(f"  Level {level}: {len(yes_itemsets[level])} itemsets")

        # Run Apriori on NO case
        if verbosity > 0:
            print(f"\nRunning Apriori on NO case...")
            print(f"  Min support: {config.min_support_for_no_case}")

        no_itemsets, no_total = itemsets_from_sketches(
            sketch_manager=no_manager,
            min_support=config.min_support_for_no_case,
            max_length=config.max_levels,
            verbosity=verbosity,
            include_all_level1=config.include_all_level1,
        )

        if verbosity > 0:
            print(f"\nFrequent itemsets found in NO case:")
            for level in sorted(no_itemsets.keys()):
                print(f"  Level {level}: {len(no_itemsets[level])} itemsets")

    finally:
        # Clean up temp files
        Path(yes_temp_path).unlink(missing_ok=True)
        Path(no_temp_path).unlink(missing_ok=True)

    # Perform full outer join
    if verbosity > 0:
        print(f"\nPerforming full outer join...")
        print(f"Writing joined itemsets to: {config.output_itemsets_path}")

    full_outer_join_itemsets(
        yes_itemsets=yes_itemsets,
        no_itemsets=no_itemsets,
        yes_total=yes_total,
        no_total=no_total,
        min_support_yes=config.min_support_for_yes_case,
        min_support_no=config.min_support_for_no_case,
        output_path=config.output_itemsets_path,
        item_separator=config.item_separator,
    )

    if verbosity > 0:
        print("\nSingle-file comparison (one target) completed successfully!")

    return yes_itemsets, no_itemsets, yes_total, no_total


def run_single_file_comparison_two_targets(
    config: SingleFileComparatorConfig, verbosity: int = 0
) -> Tuple[
    Dict[int, Dict[tuple, float]],
    Dict[int, Dict[tuple, float]],
    float,
    float,
]:
    """
    Run comparison with single file and two targets (two intersections).

    YES case: Sketches intersected with target_item_1
    NO case: Sketches intersected with target_item_0

    Parameters
    ----------
    config : SingleFileComparatorConfig
        Configuration for single-file mode with both targets specified.
    verbosity : int
        Verbosity level (0, 1, or 2).

    Returns
    -------
    tuple
        (yes_itemsets, no_itemsets, yes_total, no_total)

    Examples
    --------
    >>> config = SingleFileComparatorConfig(...)  # doctest: +SKIP
    >>> yes_items, no_items, yes_total, no_total = run_single_file_comparison_two_targets(  # doctest: +SKIP
    ...     config, verbosity=1
    ... )
    """
    if verbosity > 0:
        print("=" * 70)
        print("FIS-based Comparator: Single-File Mode (Two Targets)")
        print("=" * 70)
        print(f"Target item 1 (YES): {config.target_item_1}")
        print(f"Target item 0 (NO): {config.target_item_0}")

    # Load sketches
    if verbosity > 0:
        print(f"\nLoading sketches from: {config.input_csv_path}")

    sketches_dict, total_sketch, original_total = load_sketches_from_csv(
        config.input_csv_path
    )

    if verbosity > 0:
        print(f"  Loaded {len(sketches_dict)} items")
        print(f"  Total count estimate: {original_total:.2f}")

    # Extract both target sketches
    if config.target_item_1 not in sketches_dict:
        raise ValueError(
            f"Target item 1 '{config.target_item_1}' not found in input CSV"
        )

    if config.target_item_0 not in sketches_dict:
        raise ValueError(
            f"Target item 0 '{config.target_item_0}' not found in input CSV"
        )

    target_1_sketch = sketches_dict[config.target_item_1]
    target_0_sketch = sketches_dict[config.target_item_0]

    if verbosity > 0:
        print(f"\nTarget item 1 count: {target_1_sketch.get_estimate():.2f}")
        print(f"Target item 0 count: {target_0_sketch.get_estimate():.2f}")

    # Create copies without target items
    sketches_without_targets = {
        k: v
        for k, v in sketches_dict.items()
        if k != config.target_item_1 and k != config.target_item_0
    }

    # Create YES case: Intersection with target_1
    if verbosity > 0:
        print(f"\nCreating YES case (intersection with target_item_1)...")

    yes_sketches = intersect_sketches(sketches_without_targets, target_1_sketch)
    yes_total_sketch = target_1_sketch
    yes_total = yes_total_sketch.get_estimate()

    if verbosity > 0:
        print(f"  YES case total count: {yes_total:.2f}")

    # Create NO case: Intersection with target_0
    if verbosity > 0:
        print(f"\nCreating NO case (intersection with target_item_0)...")

    no_sketches = intersect_sketches(sketches_without_targets, target_0_sketch)
    no_total_sketch = target_0_sketch
    no_total = no_total_sketch.get_estimate()

    if verbosity > 0:
        print(f"  NO case total count: {no_total:.2f}")

    # Create temporary sketch managers
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as yes_temp_file:
        yes_temp_path = yes_temp_file.name

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as no_temp_file:
        no_temp_path = no_temp_file.name

    try:
        # Save temporary files
        save_sketches_to_csv(yes_sketches, yes_total_sketch, yes_temp_path)
        save_sketches_to_csv(no_sketches, no_total_sketch, no_temp_path)

        # Load as ThetaSketchManagers
        yes_manager = ThetaSketchManager(yes_temp_path)
        no_manager = ThetaSketchManager(no_temp_path)

        # Run Apriori on YES case
        if verbosity > 0:
            print(f"\nRunning Apriori on YES case...")
            print(f"  Min support: {config.min_support_for_yes_case}")

        yes_itemsets, yes_total = itemsets_from_sketches(
            sketch_manager=yes_manager,
            min_support=config.min_support_for_yes_case,
            max_length=config.max_levels,
            verbosity=verbosity,
            include_all_level1=config.include_all_level1,
        )

        if verbosity > 0:
            print(f"\nFrequent itemsets found in YES case:")
            for level in sorted(yes_itemsets.keys()):
                print(f"  Level {level}: {len(yes_itemsets[level])} itemsets")

        # Run Apriori on NO case
        if verbosity > 0:
            print(f"\nRunning Apriori on NO case...")
            print(f"  Min support: {config.min_support_for_no_case}")

        no_itemsets, no_total = itemsets_from_sketches(
            sketch_manager=no_manager,
            min_support=config.min_support_for_no_case,
            max_length=config.max_levels,
            verbosity=verbosity,
            include_all_level1=config.include_all_level1,
        )

        if verbosity > 0:
            print(f"\nFrequent itemsets found in NO case:")
            for level in sorted(no_itemsets.keys()):
                print(f"  Level {level}: {len(no_itemsets[level])} itemsets")

    finally:
        # Clean up temp files
        Path(yes_temp_path).unlink(missing_ok=True)
        Path(no_temp_path).unlink(missing_ok=True)

    # Perform full outer join
    if verbosity > 0:
        print(f"\nPerforming full outer join...")
        print(f"Writing joined itemsets to: {config.output_itemsets_path}")

    full_outer_join_itemsets(
        yes_itemsets=yes_itemsets,
        no_itemsets=no_itemsets,
        yes_total=yes_total,
        no_total=no_total,
        min_support_yes=config.min_support_for_yes_case,
        min_support_no=config.min_support_for_no_case,
        output_path=config.output_itemsets_path,
        item_separator=config.item_separator,
    )

    if verbosity > 0:
        print("\nSingle-file comparison (two targets) completed successfully!")

    return yes_itemsets, no_itemsets, yes_total, no_total


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v"])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration management for FIS-based Comparator.

This module defines configuration classes for running the FIS comparator
in two different modes:
1. Two-file mode: Separate CSV files for yes and no cases
2. Single-file mode: One CSV file with target item(s) to split the data
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union, List


@dataclass
class TwoFileComparatorConfig:
    """
    Configuration for two-file comparison mode.

    In this mode, two separate CSV files are provided - one for the "yes" case
    and one for the "no" case. Frequent itemsets are computed separately for
    each, then joined.

    Attributes
    ----------
    input_csv_path_for_yes_case : str
        Path to CSV file for yes case (format: "item,<theta sketch>")
    input_csv_path_for_no_case : str
        Path to CSV file for no case (format: "item,<theta sketch>")
    min_support_for_yes_case : float
        Minimum support threshold for yes case (0-1)
    min_support_for_no_case : float
        Minimum support threshold for no case (0-1)
    max_levels : int
        Maximum depth of frequent itemsets
    include_all_level1 : bool
        If True, include all level 1 items regardless of min_support
    output_itemsets_path_yes_case : str
        Path to output frequent itemsets for yes case
    output_itemsets_path_no_case : str
        Path to output frequent itemsets for no case
    output_itemsets_joined : str
        Path to output joined itemsets
    item_separator : str
        Separator for items in itemsets (default: " && ")
    sketch_lg_k_yes_case : int
        Sketch size parameter for yes case (log base 2)
    sketch_lg_k_no_case : int
        Sketch size parameter for no case (log base 2)
    excluded_items : Optional[List[str]]
        List of items to exclude from analysis (removed from input sketches)
    use_equi_join : bool
        If True, only output itemsets that appear in both yes and no cases (default: False)
    filter_item : Optional[str]
        Optional pre-filter item - intersect all sketches with this before splitting
    """

    input_csv_path_for_yes_case: str
    input_csv_path_for_no_case: str
    min_support_for_yes_case: float
    min_support_for_no_case: float
    max_levels: int
    include_all_level1: bool
    output_itemsets_path_yes_case: str
    output_itemsets_path_no_case: str
    output_itemsets_joined: str
    item_separator: str = " && "
    sketch_lg_k_yes_case: int = 12
    sketch_lg_k_no_case: int = 12
    excluded_items: Optional[List[str]] = None
    use_equi_join: bool = False
    filter_item: Optional[str] = None

    def __post_init__(self):
        """Validate configuration parameters."""
        if not 0 <= self.min_support_for_yes_case <= 1:
            raise ValueError(
                f"min_support_for_yes_case must be between 0 and 1, "
                f"got {self.min_support_for_yes_case}"
            )

        if not 0 <= self.min_support_for_no_case <= 1:
            raise ValueError(
                f"min_support_for_no_case must be between 0 and 1, "
                f"got {self.min_support_for_no_case}"
            )

        if self.max_levels < 1:
            raise ValueError(f"max_levels must be at least 1, got {self.max_levels}")

        if not 4 <= self.sketch_lg_k_yes_case <= 26:
            raise ValueError(
                f"sketch_lg_k_yes_case must be between 4 and 26, "
                f"got {self.sketch_lg_k_yes_case}"
            )

        if not 4 <= self.sketch_lg_k_no_case <= 26:
            raise ValueError(
                f"sketch_lg_k_no_case must be between 4 and 26, "
                f"got {self.sketch_lg_k_no_case}"
            )

        if not Path(self.input_csv_path_for_yes_case).exists():
            raise FileNotFoundError(
                f"Yes case CSV file not found: {self.input_csv_path_for_yes_case}"
            )

        if not Path(self.input_csv_path_for_no_case).exists():
            raise FileNotFoundError(
                f"No case CSV file not found: {self.input_csv_path_for_no_case}"
            )


@dataclass
class SingleFileComparatorConfig:
    """
    Configuration for single-file comparison mode.

    In this mode, one CSV file is provided along with target item(s) that
    define the split between yes and no cases.

    Two sub-modes:
    1. One target (target_item_1 only): Yes = intersect with target_item_1,
       No = A-not-B with target_item_1
    2. Two targets (both specified): Yes = intersect with target_item_1,
       No = intersect with target_item_0

    Attributes
    ----------
    input_csv_path : str
        Path to CSV file (format: "item,<theta sketch>")
    min_support_for_yes_case : float
        Minimum support threshold for yes case (0-1)
    min_support_for_no_case : float
        Minimum support threshold for no case (0-1)
    max_levels : int
        Maximum depth of frequent itemsets
    include_all_level1 : bool
        If True, include all level 1 items regardless of min_support
    output_itemsets_path : str
        Path to output joined itemsets
    item_separator : str
        Separator for items in itemsets (default: " && ")
    sketch_lg_k : int
        Sketch size parameter (log base 2)
    target_item_1 : str
        Target item for yes case (mandatory)
    target_item_0 : Optional[str]
        Target item for no case (optional, mutually exclusive with target_item_1)
    excluded_items : Optional[List[str]]
        List of items to exclude from analysis (removed from input sketches)
    use_equi_join : bool
        If True, only output itemsets that appear in both yes and no cases (default: False)
    filter_item : Optional[str]
        Optional pre-filter item - intersect all sketches with this before splitting
    """

    input_csv_path: str
    min_support_for_yes_case: float
    min_support_for_no_case: float
    max_levels: int
    include_all_level1: bool
    output_itemsets_path: str
    item_separator: str = " && "
    sketch_lg_k: int = 12
    target_item_1: str = ""
    target_item_0: Optional[str] = None
    excluded_items: Optional[List[str]] = None
    use_equi_join: bool = False
    filter_item: Optional[str] = None

    def __post_init__(self):
        """Validate configuration parameters."""
        if not self.target_item_1:
            raise ValueError("target_item_1 is mandatory in single-file mode")

        if not 0 <= self.min_support_for_yes_case <= 1:
            raise ValueError(
                f"min_support_for_yes_case must be between 0 and 1, "
                f"got {self.min_support_for_yes_case}"
            )

        if not 0 <= self.min_support_for_no_case <= 1:
            raise ValueError(
                f"min_support_for_no_case must be between 0 and 1, "
                f"got {self.min_support_for_no_case}"
            )

        if self.max_levels < 1:
            raise ValueError(f"max_levels must be at least 1, got {self.max_levels}")

        if not 4 <= self.sketch_lg_k <= 26:
            raise ValueError(
                f"sketch_lg_k must be between 4 and 26, got {self.sketch_lg_k}"
            )

        if not Path(self.input_csv_path).exists():
            raise FileNotFoundError(
                f"Input CSV file not found: {self.input_csv_path}"
            )

        # Validate that target items are mutually exclusive if both provided
        if self.target_item_0 is not None:
            if self.target_item_1 == self.target_item_0:
                raise ValueError(
                    "target_item_1 and target_item_0 must be different items"
                )


def load_comparator_config(
    config_path: str,
) -> Union[TwoFileComparatorConfig, SingleFileComparatorConfig]:
    """
    Load comparator configuration from a JSON file.

    The function auto-detects which configuration mode to use based on
    the fields present in the JSON file.

    Parameters
    ----------
    config_path : str
        Path to the JSON configuration file.

    Returns
    -------
    Union[TwoFileComparatorConfig, SingleFileComparatorConfig]
        Configuration object based on the detected mode.

    Raises
    ------
    FileNotFoundError
        If the configuration file doesn't exist.
    ValueError
        If the configuration is invalid or ambiguous.

    Examples
    --------
    >>> config = load_comparator_config("my_comparator_config.json")  # doctest: +SKIP
    >>> isinstance(config, (TwoFileComparatorConfig, SingleFileComparatorConfig))  # doctest: +SKIP
    True
    """
    config_path_obj = Path(config_path)

    if not config_path_obj.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path_obj, "r") as f:
        config_dict = json.load(f)

    # Remove comment fields (keys starting with "//")
    config_dict = {k: v for k, v in config_dict.items() if not k.startswith("//")}

    # Auto-detect configuration mode
    has_two_file_fields = (
        "input_csv_path_for_yes_case" in config_dict
        and "input_csv_path_for_no_case" in config_dict
    )
    has_single_file_fields = "input_csv_path" in config_dict

    if has_two_file_fields and has_single_file_fields:
        raise ValueError(
            "Ambiguous configuration: cannot have both two-file and single-file fields"
        )

    if not has_two_file_fields and not has_single_file_fields:
        raise ValueError(
            "Invalid configuration: must specify either "
            "(input_csv_path_for_yes_case, input_csv_path_for_no_case) or "
            "(input_csv_path)"
        )

    # Set defaults for optional parameters
    config_dict.setdefault("item_separator", " && ")
    config_dict.setdefault("excluded_items", None)
    config_dict.setdefault("use_equi_join", False)
    config_dict.setdefault("filter_item", None)

    if has_two_file_fields:
        # Two-file mode
        config_dict.setdefault("sketch_lg_k_yes_case", 12)
        config_dict.setdefault("sketch_lg_k_no_case", 12)
        return TwoFileComparatorConfig(**config_dict)
    else:
        # Single-file mode
        config_dict.setdefault("sketch_lg_k", 12)
        config_dict.setdefault("target_item_0", None)
        return SingleFileComparatorConfig(**config_dict)


def save_comparator_config(
    config: Union[TwoFileComparatorConfig, SingleFileComparatorConfig],
    config_path: str,
):
    """
    Save comparator configuration to a JSON file.

    Parameters
    ----------
    config : Union[TwoFileComparatorConfig, SingleFileComparatorConfig]
        Configuration object to save.
    config_path : str
        Path where the JSON configuration file will be saved.

    Examples
    --------
    >>> config = TwoFileComparatorConfig(...)  # doctest: +SKIP
    >>> save_comparator_config(config, "config.json")  # doctest: +SKIP
    """
    if isinstance(config, TwoFileComparatorConfig):
        config_dict = {
            "input_csv_path_for_yes_case": config.input_csv_path_for_yes_case,
            "input_csv_path_for_no_case": config.input_csv_path_for_no_case,
            "min_support_for_yes_case": config.min_support_for_yes_case,
            "min_support_for_no_case": config.min_support_for_no_case,
            "max_levels": config.max_levels,
            "include_all_level1": config.include_all_level1,
            "output_itemsets_path_yes_case": config.output_itemsets_path_yes_case,
            "output_itemsets_path_no_case": config.output_itemsets_path_no_case,
            "output_itemsets_joined": config.output_itemsets_joined,
            "item_separator": config.item_separator,
            "sketch_lg_k_yes_case": config.sketch_lg_k_yes_case,
            "sketch_lg_k_no_case": config.sketch_lg_k_no_case,
            "use_equi_join": config.use_equi_join,
        }
        if config.excluded_items is not None:
            config_dict["excluded_items"] = config.excluded_items
        if config.filter_item is not None:
            config_dict["filter_item"] = config.filter_item
    elif isinstance(config, SingleFileComparatorConfig):
        config_dict = {
            "input_csv_path": config.input_csv_path,
            "min_support_for_yes_case": config.min_support_for_yes_case,
            "min_support_for_no_case": config.min_support_for_no_case,
            "max_levels": config.max_levels,
            "include_all_level1": config.include_all_level1,
            "output_itemsets_path": config.output_itemsets_path,
            "item_separator": config.item_separator,
            "sketch_lg_k": config.sketch_lg_k,
            "target_item_1": config.target_item_1,
            "use_equi_join": config.use_equi_join,
        }
        if config.target_item_0 is not None:
            config_dict["target_item_0"] = config.target_item_0
        if config.excluded_items is not None:
            config_dict["excluded_items"] = config.excluded_items
        if config.filter_item is not None:
            config_dict["filter_item"] = config.filter_item
    else:
        raise TypeError(f"Unknown config type: {type(config)}")

    with open(config_path, "w") as f:
        json.dump(config_dict, f, indent=2)


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v"])

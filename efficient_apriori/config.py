#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration management for theta sketch-based Apriori algorithm.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SketchConfig:
    """
    Configuration for running Apriori algorithm with theta sketches.

    Attributes
    ----------
    input_csv_path : str
        Path to the CSV file containing base64-encoded theta sketches.
        Format: "<item/dimension=value>,<base64_encoded_sketch>"
        First row: "total" or "" followed by the total count sketch.
    min_support : float
        Minimum support threshold (between 0 and 1).
    max_levels : int
        Maximum number of levels for computing frequent itemsets.
    include_all_level1 : bool
        If True, include all level 1 items in output regardless of min_support.
        Items below min_support won't be used for generating higher levels.
    output_itemsets_path : str
        Path for the output CSV file containing frequent itemsets.
        Format: "level,frequent_itemset,support"
    output_rules_path : str
        Path for the output CSV file containing association rules.
        Format: "level,frequent_itemset,support,confidence,lift,conviction"
    item_separator : str
        Separator between items in frequent itemsets (default: "&&").
    min_confidence : float
        Minimum confidence threshold for association rules (default: 0.5).
    sketch_lg_k : int
        Log base 2 of sketch size (lg_k parameter). Determines sketch accuracy.
        Default: 12 (sketch size = 2^12 = 4096).
        Higher values = more accurate but more memory.
        Range: typically 4-26 (sketch size 16 to 67M).
    """

    input_csv_path: str
    min_support: float
    max_levels: int
    include_all_level1: bool
    output_itemsets_path: str
    output_rules_path: str
    item_separator: str = "&&"
    min_confidence: float = 0.5
    sketch_lg_k: int = 12

    def __post_init__(self):
        """Validate configuration parameters."""
        if not 0 <= self.min_support <= 1:
            raise ValueError(f"min_support must be between 0 and 1, got {self.min_support}")

        if not 0 <= self.min_confidence <= 1:
            raise ValueError(f"min_confidence must be between 0 and 1, got {self.min_confidence}")

        if self.max_levels < 1:
            raise ValueError(f"max_levels must be at least 1, got {self.max_levels}")

        if not 4 <= self.sketch_lg_k <= 26:
            raise ValueError(f"sketch_lg_k must be between 4 and 26, got {self.sketch_lg_k}")

        if not Path(self.input_csv_path).exists():
            raise FileNotFoundError(f"Input CSV file not found: {self.input_csv_path}")


def load_config(config_path: str) -> SketchConfig:
    """
    Load configuration from a JSON file.

    Parameters
    ----------
    config_path : str
        Path to the JSON configuration file.

    Returns
    -------
    SketchConfig
        Configuration object with validated parameters.

    Examples
    --------
    >>> config = load_config("config.json")  # doctest: +SKIP
    >>> print(config.min_support)  # doctest: +SKIP
    0.3

    Example JSON structure:
    {
        "input_csv_path": "data/sketches.csv",
        "min_support": 0.3,
        "max_levels": 5,
        "include_all_level1": true,
        "output_itemsets_path": "output/frequent_itemsets.csv",
        "output_rules_path": "output/association_rules.csv",
        "item_separator": "&&",
        "min_confidence": 0.5,
        "sketch_lg_k": 12
    }
    """
    config_path_obj = Path(config_path)

    if not config_path_obj.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path_obj, 'r') as f:
        config_dict = json.load(f)

    # Provide default values for optional parameters
    config_dict.setdefault('item_separator', '&&')
    config_dict.setdefault('min_confidence', 0.5)
    config_dict.setdefault('sketch_lg_k', 12)

    return SketchConfig(**config_dict)


def save_config(config: SketchConfig, config_path: str):
    """
    Save configuration to a JSON file.

    Parameters
    ----------
    config : SketchConfig
        Configuration object to save.
    config_path : str
        Path where the JSON configuration file will be saved.

    Examples
    --------
    >>> config = SketchConfig(  # doctest: +SKIP
    ...     input_csv_path="data/sketches.csv",
    ...     min_support=0.3,
    ...     max_levels=5,
    ...     include_all_level1=True,
    ...     output_itemsets_path="output/itemsets.csv",
    ...     output_rules_path="output/rules.csv"
    ... )
    >>> save_config(config, "config.json")  # doctest: +SKIP
    """
    config_dict = {
        'input_csv_path': config.input_csv_path,
        'min_support': config.min_support,
        'max_levels': config.max_levels,
        'include_all_level1': config.include_all_level1,
        'output_itemsets_path': config.output_itemsets_path,
        'output_rules_path': config.output_rules_path,
        'item_separator': config.item_separator,
        'min_confidence': config.min_confidence,
        'sketch_lg_k': config.sketch_lg_k,
    }

    with open(config_path, 'w') as f:
        json.dump(config_dict, f, indent=2)


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v"])

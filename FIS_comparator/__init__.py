#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIS_based_Comparator: Frequent Itemset Comparator for Yes/No Classification

This package provides tools for comparing frequent itemsets between two classes
(yes/no) using theta sketches, inspired by classification-based association rules.
"""

__version__ = "1.0.0"

from .comparator_config import (
    TwoFileComparatorConfig,
    SingleFileComparatorConfig,
    load_comparator_config,
)
from .comparator_core import (
    run_two_file_comparison,
    run_single_file_comparison_one_target,
    run_single_file_comparison_two_targets,
)

__all__ = [
    "TwoFileComparatorConfig",
    "SingleFileComparatorConfig",
    "load_comparator_config",
    "run_two_file_comparison",
    "run_single_file_comparison_one_target",
    "run_single_file_comparison_two_targets",
]

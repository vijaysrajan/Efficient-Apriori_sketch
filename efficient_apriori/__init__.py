#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the Apriori algorithm.
"""

import importlib.metadata
from efficient_apriori.apriori import apriori
from efficient_apriori.itemsets import itemsets_from_transactions
from efficient_apriori.rules import Rule, generate_rules_apriori

# Theta sketch support (optional imports)
try:
    from efficient_apriori.sketch_support import (
        ThetaSketchManager,
        ItemsetCountSketch,
        create_sketch_from_transaction_ids,
        serialize_sketch_to_base64,
        deserialize_sketch_from_base64,
    )
    from efficient_apriori.itemsets_sketch import (
        itemsets_from_sketches,
        itemsets_from_sketches_with_details,
    )
    from efficient_apriori.config import SketchConfig, load_config, save_config
    from efficient_apriori.rules_sketch import (
        write_itemsets_to_csv,
        write_rules_to_csv,
        read_itemsets_from_csv,
        read_rules_from_csv,
    )

    _SKETCH_SUPPORT_AVAILABLE = True
    __all__ = [
        "apriori",
        "itemsets_from_transactions",
        "Rule",
        "generate_rules_apriori",
        # Theta sketch support
        "ThetaSketchManager",
        "ItemsetCountSketch",
        "itemsets_from_sketches",
        "itemsets_from_sketches_with_details",
        "SketchConfig",
        "load_config",
        "save_config",
        "write_itemsets_to_csv",
        "write_rules_to_csv",
        "read_itemsets_from_csv",
        "read_rules_from_csv",
        "create_sketch_from_transaction_ids",
        "serialize_sketch_to_base64",
        "deserialize_sketch_from_base64",
    ]
except ImportError:
    # Theta sketch support not available (datasketches not installed)
    _SKETCH_SUPPORT_AVAILABLE = False
    __all__ = ["apriori", "itemsets_from_transactions", "Rule", "generate_rules_apriori"]

# We use semantic versioning
# See https://semver.org/
__version__ = importlib.metadata.version("efficient_apriori")


def run_tests():
    """
    Run all tests.
    """
    import pytest
    import os

    base, _ = os.path.split(__file__)
    pytest.main(args=[base, "--doctest-modules"])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for theta sketch-based Apriori implementation.
"""

import pytest
import tempfile
import csv
import json
from pathlib import Path

from efficient_apriori.sketch_support import (
    ThetaSketchManager,
    create_sketch_from_transaction_ids,
    serialize_sketch_to_base64,
    deserialize_sketch_from_base64,
)
from efficient_apriori.itemsets_sketch import itemsets_from_sketches
from efficient_apriori.config import SketchConfig, load_config, save_config
from efficient_apriori.rules_sketch import (
    write_itemsets_to_csv,
    write_rules_to_csv,
    read_itemsets_from_csv,
    format_itemset,
)
from efficient_apriori.rules import generate_rules_apriori


class TestSketchSerialization:
    """Test sketch serialization and deserialization."""

    def test_create_sketch(self):
        """Test creating a sketch from transaction IDs."""
        sketch = create_sketch_from_transaction_ids({1, 2, 3, 4, 5})
        assert sketch.get_estimate() == 5.0

    def test_serialize_deserialize(self):
        """Test serializing and deserializing a sketch."""
        sketch = create_sketch_from_transaction_ids({1, 2, 3})
        b64_str = serialize_sketch_to_base64(sketch)
        sketch2 = deserialize_sketch_from_base64(b64_str)
        assert sketch2.get_estimate() == 3.0

    def test_empty_sketch(self):
        """Test creating an empty sketch."""
        sketch = create_sketch_from_transaction_ids(set())
        assert sketch.get_estimate() == 0.0


class TestThetaSketchManager:
    """Test ThetaSketchManager class."""

    @pytest.fixture
    def sample_csv(self):
        """Create a sample CSV file with theta sketches."""
        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')

        # Create sketches for testing
        # Total: 10 transactions
        total_sketch = create_sketch_from_transaction_ids(set(range(10)))

        # Item A: appears in transactions 0-6 (7 times)
        sketch_a = create_sketch_from_transaction_ids({0, 1, 2, 3, 4, 5, 6})

        # Item B: appears in transactions 0-4 (5 times)
        sketch_b = create_sketch_from_transaction_ids({0, 1, 2, 3, 4})

        # Item C: appears in transactions 0-2 (3 times)
        sketch_c = create_sketch_from_transaction_ids({0, 1, 2})

        # Write to CSV
        writer = csv.writer(temp_file)
        writer.writerow(['total', serialize_sketch_to_base64(total_sketch)])
        writer.writerow(['item_a', serialize_sketch_to_base64(sketch_a)])
        writer.writerow(['item_b', serialize_sketch_to_base64(sketch_b)])
        writer.writerow(['item_c', serialize_sketch_to_base64(sketch_c)])

        temp_file.close()
        yield temp_file.name

        # Cleanup
        Path(temp_file.name).unlink()

    def test_load_from_csv(self, sample_csv):
        """Test loading sketches from CSV."""
        manager = ThetaSketchManager(sample_csv)

        assert len(manager.items) == 3
        assert 'item_a' in manager.items
        assert 'item_b' in manager.items
        assert 'item_c' in manager.items

    def test_total_count(self, sample_csv):
        """Test total count retrieval."""
        manager = ThetaSketchManager(sample_csv)
        assert manager.total_count == 10.0

    def test_get_count(self, sample_csv):
        """Test getting count for individual items."""
        manager = ThetaSketchManager(sample_csv)

        assert manager.get_count('item_a') == 7.0
        assert manager.get_count('item_b') == 5.0
        assert manager.get_count('item_c') == 3.0

    def test_get_itemset_count(self, sample_csv):
        """Test getting count for itemsets (intersections)."""
        manager = ThetaSketchManager(sample_csv)

        # A ∩ B should be {0, 1, 2, 3, 4} (5 items)
        count_ab = manager.get_itemset_count(('item_a', 'item_b'))
        assert count_ab == 5.0

        # A ∩ B ∩ C should be {0, 1, 2} (3 items)
        count_abc = manager.get_itemset_count(('item_a', 'item_b', 'item_c'))
        assert count_abc == 3.0

    def test_get_support(self, sample_csv):
        """Test getting support for itemsets."""
        manager = ThetaSketchManager(sample_csv)

        support_a = manager.get_support(('item_a',))
        assert support_a == 0.7  # 7/10

        support_ab = manager.get_support(('item_a', 'item_b'))
        assert support_ab == 0.5  # 5/10


class TestItemsetsFromSketches:
    """Test itemsets_from_sketches function."""

    @pytest.fixture
    def sample_csv(self):
        """Create a sample CSV for testing."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')

        total_sketch = create_sketch_from_transaction_ids(set(range(10)))
        sketch_a = create_sketch_from_transaction_ids({0, 1, 2, 3, 4, 5, 6})
        sketch_b = create_sketch_from_transaction_ids({0, 1, 2, 3, 4})
        sketch_c = create_sketch_from_transaction_ids({0, 1, 2})

        writer = csv.writer(temp_file)
        writer.writerow(['total', serialize_sketch_to_base64(total_sketch)])
        writer.writerow(['item_a', serialize_sketch_to_base64(sketch_a)])
        writer.writerow(['item_b', serialize_sketch_to_base64(sketch_b)])
        writer.writerow(['item_c', serialize_sketch_to_base64(sketch_c)])

        temp_file.close()
        yield temp_file.name
        Path(temp_file.name).unlink()

    def test_itemsets_basic(self, sample_csv):
        """Test basic itemset generation."""
        manager = ThetaSketchManager(sample_csv)
        itemsets, total = itemsets_from_sketches(manager, min_support=0.5, max_length=3)

        # Should find item_a and item_b at level 1 (support >= 0.5)
        assert 1 in itemsets
        assert ('item_a',) in itemsets[1]
        assert ('item_b',) in itemsets[1]
        assert ('item_c',) not in itemsets[1]  # support = 0.3 < 0.5

        # Should find (item_a, item_b) at level 2
        assert 2 in itemsets
        assert ('item_a', 'item_b') in itemsets[2]

    def test_include_all_level1(self, sample_csv):
        """Test include_all_level1 parameter."""
        manager = ThetaSketchManager(sample_csv)
        itemsets, total = itemsets_from_sketches(
            manager, min_support=0.5, max_length=3, include_all_level1=True
        )

        # Should include all level 1 items
        assert ('item_a',) in itemsets[1]
        assert ('item_b',) in itemsets[1]
        assert ('item_c',) in itemsets[1]  # Included even though support < 0.5

        # But item_c should not be used for higher levels
        if 2 in itemsets:
            assert ('item_b', 'item_c') not in itemsets[2]


class TestConfig:
    """Test configuration management."""

    def test_sketch_config_creation(self):
        """Test creating a SketchConfig object."""
        # Create a temporary input file
        temp_input = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_input.close()

        try:
            config = SketchConfig(
                input_csv_path=temp_input.name,
                min_support=0.3,
                max_levels=5,
                include_all_level1=True,
                output_itemsets_path="output/itemsets.csv",
                output_rules_path="output/rules.csv",
            )

            assert config.min_support == 0.3
            assert config.max_levels == 5
            assert config.include_all_level1 is True
            assert config.item_separator == "&&"  # Default value
        finally:
            Path(temp_input.name).unlink()

    def test_config_validation(self):
        """Test configuration validation."""
        temp_input = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_input.close()

        try:
            # Invalid min_support
            with pytest.raises(ValueError):
                SketchConfig(
                    input_csv_path=temp_input.name,
                    min_support=1.5,
                    max_levels=5,
                    include_all_level1=True,
                    output_itemsets_path="output/itemsets.csv",
                    output_rules_path="output/rules.csv",
                )
        finally:
            Path(temp_input.name).unlink()

    def test_save_load_config(self):
        """Test saving and loading configuration."""
        temp_input = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_input.close()

        temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_config.close()

        try:
            # Create and save config
            config = SketchConfig(
                input_csv_path=temp_input.name,
                min_support=0.3,
                max_levels=5,
                include_all_level1=True,
                output_itemsets_path="output/itemsets.csv",
                output_rules_path="output/rules.csv",
            )
            save_config(config, temp_config.name)

            # Load config
            loaded_config = load_config(temp_config.name)

            assert loaded_config.min_support == 0.3
            assert loaded_config.max_levels == 5
            assert loaded_config.include_all_level1 is True
        finally:
            Path(temp_input.name).unlink()
            Path(temp_config.name).unlink()


class TestCSVFormatting:
    """Test CSV formatting functions."""

    def test_format_itemset(self):
        """Test itemset formatting."""
        assert format_itemset(('a',), separator='&&') == 'a'
        assert format_itemset(('a', 'b'), separator='&&') == 'a&&b'
        assert format_itemset(('a', 'b', 'c'), separator='||') == 'a||b||c'

    def test_write_read_itemsets(self):
        """Test writing and reading itemsets to CSV."""
        itemsets = {
            1: {('item_a',): 70.0, ('item_b',): 50.0},
            2: {('item_a', 'item_b'): 30.0}
        }
        total_count = 100.0

        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        temp_file.close()

        try:
            # Write
            write_itemsets_to_csv(itemsets, total_count, temp_file.name)

            # Read
            loaded_itemsets, max_sup = read_itemsets_from_csv(temp_file.name)

            assert 1 in loaded_itemsets
            assert ('item_a',) in loaded_itemsets[1]
            assert loaded_itemsets[1][('item_a',)] == 0.7
        finally:
            Path(temp_file.name).unlink()


if __name__ == "__main__":
    pytest.main(args=[__file__, "-v"])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for sketch_operations module.
"""

import pytest
import tempfile
import os
from datasketches import update_theta_sketch

from FIS_comparator.sketch_operations import (
    intersect_sketches,
    a_not_b_sketches,
    compute_total_sketch,
    save_sketches_to_csv,
    load_sketches_from_csv,
)


def create_test_sketch(values):
    """Helper to create a sketch from values."""
    sketch = update_theta_sketch()
    for val in values:
        sketch.update(val)
    return sketch.compact()


class TestIntersectSketches:
    """Tests for intersect_sketches function."""

    def test_simple_intersection(self):
        """Test basic intersection operation."""
        # Create test sketches
        sketch1 = create_test_sketch([1, 2, 3])
        sketch2 = create_test_sketch([2, 3, 4])
        target = create_test_sketch([1, 2])

        sketches_dict = {"item1": sketch1, "item2": sketch2}
        result = intersect_sketches(sketches_dict, target)

        # item1 ∩ target = {1, 2}
        assert result["item1"].get_estimate() == pytest.approx(2.0, abs=0.1)
        # item2 ∩ target = {2}
        assert result["item2"].get_estimate() == pytest.approx(1.0, abs=0.1)

    def test_empty_intersection(self):
        """Test intersection with no overlap."""
        sketch1 = create_test_sketch([1, 2, 3])
        target = create_test_sketch([4, 5, 6])

        result = intersect_sketches({"item1": sketch1}, target)

        assert result["item1"].get_estimate() == pytest.approx(0.0, abs=0.1)


class TestANotBSketches:
    """Tests for a_not_b_sketches function."""

    def test_simple_a_not_b(self):
        """Test basic A-not-B operation."""
        sketch1 = create_test_sketch([1, 2, 3])
        sketch2 = create_test_sketch([2, 3, 4])
        subtract = create_test_sketch([2])

        sketches_dict = {"item1": sketch1, "item2": sketch2}
        result = a_not_b_sketches(sketches_dict, subtract)

        # item1 - {2} = {1, 3}
        assert result["item1"].get_estimate() == pytest.approx(2.0, abs=0.1)
        # item2 - {2} = {3, 4}
        assert result["item2"].get_estimate() == pytest.approx(2.0, abs=0.1)

    def test_a_not_b_removes_all(self):
        """Test A-not-B when B contains all of A."""
        sketch1 = create_test_sketch([1, 2])
        subtract = create_test_sketch([1, 2, 3, 4])

        result = a_not_b_sketches({"item1": sketch1}, subtract)

        assert result["item1"].get_estimate() == pytest.approx(0.0, abs=0.1)


class TestComputeTotalSketch:
    """Tests for compute_total_sketch function."""

    def test_union_of_sketches(self):
        """Test computing total from multiple sketches."""
        sketch1 = create_test_sketch([1, 2])
        sketch2 = create_test_sketch([2, 3])
        sketch3 = create_test_sketch([3, 4])

        sketches_dict = {"item1": sketch1, "item2": sketch2, "item3": sketch3}
        total = compute_total_sketch(sketches_dict)

        # Union should be {1, 2, 3, 4}
        assert total.get_estimate() == pytest.approx(4.0, abs=0.1)


class TestSaveAndLoadSketches:
    """Tests for save and load functions."""

    def test_save_and_load_roundtrip(self):
        """Test saving and loading sketches."""
        # Create test sketches
        sketch1 = create_test_sketch([1, 2, 3])
        sketch2 = create_test_sketch([2, 3, 4])
        total = create_test_sketch([1, 2, 3, 4])

        sketches_dict = {"item1": sketch1, "item2": sketch2}

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            save_sketches_to_csv(sketches_dict, total, temp_path)

            # Load back
            loaded_sketches, loaded_total, loaded_count = load_sketches_from_csv(
                temp_path
            )

            # Verify
            assert len(loaded_sketches) == 2
            assert "item1" in loaded_sketches
            assert "item2" in loaded_sketches
            assert loaded_sketches["item1"].get_estimate() == pytest.approx(
                3.0, abs=0.1
            )
            assert loaded_sketches["item2"].get_estimate() == pytest.approx(
                3.0, abs=0.1
            )
            assert loaded_count == pytest.approx(4.0, abs=0.1)

        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for itemset_joiner module.
"""

import pytest
import tempfile
import os
import csv

from FIS_comparator.itemset_joiner import (
    full_outer_join_itemsets,
    read_joined_itemsets,
)


class TestFullOuterJoinItemsets:
    """Tests for full_outer_join_itemsets function."""

    def test_overlapping_itemsets(self):
        """Test join with overlapping itemsets."""
        yes_itemsets = {
            1: {("A",): 100.0, ("B",): 80.0},
            2: {("A", "B"): 60.0},
        }
        no_itemsets = {
            1: {("A",): 50.0, ("C",): 40.0},
            2: {("A", "C"): 30.0},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            full_outer_join_itemsets(
                yes_itemsets=yes_itemsets,
                no_itemsets=no_itemsets,
                yes_total=200.0,
                no_total=100.0,
                min_support_yes=0.3,
                min_support_no=0.3,
                output_path=temp_path,
                item_separator=" && ",
            )

            # Read and verify results
            rows = read_joined_itemsets(temp_path)

            # Should have 5 rows: A, B, C, A&&B, A&&C
            assert len(rows) == 5

            # Find row for item A (should be in both)
            a_row = next(r for r in rows if r["Frequent_itemset"] == "A")
            # Note: "Frequent_item_set_seen_in" column was removed in new version
            assert a_row["Yes_case_count"] == pytest.approx(100.0, abs=0.1)
            assert a_row["No_case_count"] == pytest.approx(50.0, abs=0.1)
            assert a_row["Total"] == pytest.approx(150.0, abs=0.1)
            assert a_row["Yes_percentage"] == pytest.approx(66.667, abs=0.01)

            # Find row for item B (only in yes)
            b_row = next(r for r in rows if r["Frequent_itemset"] == "B")
            assert b_row["Yes_case_count"] == pytest.approx(80.0, abs=0.1)
            # No case should be empty string in CSV, which reads as 0.0
            assert b_row["No_case_count"] == pytest.approx(0.0, abs=0.1)

            # Find row for item C (only in no)
            c_row = next(r for r in rows if r["Frequent_itemset"] == "C")
            # Yes case should be empty string in CSV, which reads as 0.0
            assert c_row["Yes_case_count"] == pytest.approx(0.0, abs=0.1)
            assert c_row["No_case_count"] == pytest.approx(40.0, abs=0.1)

        finally:
            os.unlink(temp_path)

    def test_disjoint_itemsets(self):
        """Test join with completely disjoint itemsets."""
        yes_itemsets = {1: {("A",): 100.0}}
        no_itemsets = {1: {("B",): 50.0}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            full_outer_join_itemsets(
                yes_itemsets=yes_itemsets,
                no_itemsets=no_itemsets,
                yes_total=200.0,
                no_total=100.0,
                min_support_yes=0.3,
                min_support_no=0.3,
                output_path=temp_path,
            )

            rows = read_joined_itemsets(temp_path)

            # Should have 2 rows
            assert len(rows) == 2

            # Verify counts (Note: "Frequent_item_set_seen_in" column removed)
            a_row = next(r for r in rows if r["Frequent_itemset"] == "A")
            assert a_row["Yes_case_count"] == pytest.approx(100.0, abs=0.1)
            # Missing no count should be 0.0 (empty string in CSV)
            assert a_row["No_case_count"] == pytest.approx(0.0, abs=0.1)

            b_row = next(r for r in rows if r["Frequent_itemset"] == "B")
            # Missing yes count should be 0.0 (empty string in CSV)
            assert b_row["Yes_case_count"] == pytest.approx(0.0, abs=0.1)
            assert b_row["No_case_count"] == pytest.approx(50.0, abs=0.1)

        finally:
            os.unlink(temp_path)

    def test_empty_itemsets(self):
        """Test join with empty itemsets."""
        yes_itemsets = {}
        no_itemsets = {}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            full_outer_join_itemsets(
                yes_itemsets=yes_itemsets,
                no_itemsets=no_itemsets,
                yes_total=100.0,
                no_total=50.0,
                min_support_yes=0.3,
                min_support_no=0.3,
                output_path=temp_path,
            )

            # Should create file with just header
            with open(temp_path, "r") as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) == 1  # Just header
                assert rows[0][0] == "Level"

        finally:
            os.unlink(temp_path)

    def test_custom_separator(self):
        """Test join with custom item separator."""
        yes_itemsets = {2: {("A", "B"): 100.0}}
        no_itemsets = {2: {("A", "B"): 50.0}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            full_outer_join_itemsets(
                yes_itemsets=yes_itemsets,
                no_itemsets=no_itemsets,
                yes_total=200.0,
                no_total=100.0,
                min_support_yes=0.3,
                min_support_no=0.3,
                output_path=temp_path,
                item_separator=" | ",
            )

            rows = read_joined_itemsets(temp_path)

            # Itemset should be joined with custom separator
            assert " | " in rows[0]["Frequent_itemset"]

        finally:
            os.unlink(temp_path)


class TestReadJoinedItemsets:
    """Tests for read_joined_itemsets function."""

    def test_read_valid_file(self):
        """Test reading a valid joined itemsets file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name
            writer = csv.writer(f)
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
            writer.writerow([1, "A", "both", "100.0", "50.0", "150.0", "66.667"])
            writer.writerow([1, "B", "yes", "80.0", "30.0", "110.0", "72.727"])

        try:
            rows = read_joined_itemsets(temp_path)

            assert len(rows) == 2
            assert rows[0]["Level"] == 1
            assert rows[0]["Frequent_itemset"] == "A"
            assert rows[0]["Yes_case_count"] == 100.0
            assert rows[0]["Yes_percentage"] == 66.667

        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

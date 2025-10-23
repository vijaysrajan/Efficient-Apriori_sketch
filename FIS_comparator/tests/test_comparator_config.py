#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for comparator_config module.
"""

import pytest
import tempfile
import json
import os

from FIS_comparator.comparator_config import (
    TwoFileComparatorConfig,
    SingleFileComparatorConfig,
    load_comparator_config,
    save_comparator_config,
)


class TestTwoFileComparatorConfig:
    """Tests for TwoFileComparatorConfig."""

    def test_valid_config(self):
        """Test creating a valid config."""
        # Create temporary CSV files
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f1:
            yes_path = f1.name
            f1.write("item,sketch\n")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f2:
            no_path = f2.name
            f2.write("item,sketch\n")

        try:
            config = TwoFileComparatorConfig(
                input_csv_path_for_yes_case=yes_path,
                input_csv_path_for_no_case=no_path,
                min_support_for_yes_case=0.3,
                min_support_for_no_case=0.4,
                max_levels=5,
                include_all_level1=True,
                output_itemsets_path_yes_case="yes.csv",
                output_itemsets_path_no_case="no.csv",
                output_itemsets_joined="joined.csv",
            )

            assert config.min_support_for_yes_case == 0.3
            assert config.min_support_for_no_case == 0.4
            assert config.max_levels == 5

        finally:
            os.unlink(yes_path)
            os.unlink(no_path)

    def test_invalid_min_support(self):
        """Test that invalid min_support raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f1:
            yes_path = f1.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f2:
            no_path = f2.name

        try:
            with pytest.raises(ValueError, match="min_support_for_yes_case"):
                TwoFileComparatorConfig(
                    input_csv_path_for_yes_case=yes_path,
                    input_csv_path_for_no_case=no_path,
                    min_support_for_yes_case=1.5,  # Invalid
                    min_support_for_no_case=0.3,
                    max_levels=5,
                    include_all_level1=True,
                    output_itemsets_path_yes_case="yes.csv",
                    output_itemsets_path_no_case="no.csv",
                    output_itemsets_joined="joined.csv",
                )
        finally:
            os.unlink(yes_path)
            os.unlink(no_path)

    def test_missing_file(self):
        """Test that missing input file raises error."""
        with pytest.raises(FileNotFoundError):
            TwoFileComparatorConfig(
                input_csv_path_for_yes_case="/nonexistent/yes.csv",
                input_csv_path_for_no_case="/nonexistent/no.csv",
                min_support_for_yes_case=0.3,
                min_support_for_no_case=0.3,
                max_levels=5,
                include_all_level1=True,
                output_itemsets_path_yes_case="yes.csv",
                output_itemsets_path_no_case="no.csv",
                output_itemsets_joined="joined.csv",
            )


class TestSingleFileComparatorConfig:
    """Tests for SingleFileComparatorConfig."""

    def test_valid_one_target(self):
        """Test creating config with one target."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            config = SingleFileComparatorConfig(
                input_csv_path=csv_path,
                min_support_for_yes_case=0.3,
                min_support_for_no_case=0.3,
                max_levels=5,
                include_all_level1=True,
                output_itemsets_path="output.csv",
                target_item_1="outcome=positive",
            )

            assert config.target_item_1 == "outcome=positive"
            assert config.target_item_0 is None

        finally:
            os.unlink(csv_path)

    def test_valid_two_targets(self):
        """Test creating config with two targets."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            config = SingleFileComparatorConfig(
                input_csv_path=csv_path,
                min_support_for_yes_case=0.3,
                min_support_for_no_case=0.3,
                max_levels=5,
                include_all_level1=True,
                output_itemsets_path="output.csv",
                target_item_1="outcome=positive",
                target_item_0="outcome=negative",
            )

            assert config.target_item_1 == "outcome=positive"
            assert config.target_item_0 == "outcome=negative"

        finally:
            os.unlink(csv_path)

    def test_missing_target_item_1(self):
        """Test that missing target_item_1 raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            with pytest.raises(ValueError, match="target_item_1 is mandatory"):
                SingleFileComparatorConfig(
                    input_csv_path=csv_path,
                    min_support_for_yes_case=0.3,
                    min_support_for_no_case=0.3,
                    max_levels=5,
                    include_all_level1=True,
                    output_itemsets_path="output.csv",
                    target_item_1="",  # Empty
                )
        finally:
            os.unlink(csv_path)

    def test_identical_targets(self):
        """Test that identical targets raise error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            with pytest.raises(ValueError, match="must be different"):
                SingleFileComparatorConfig(
                    input_csv_path=csv_path,
                    min_support_for_yes_case=0.3,
                    min_support_for_no_case=0.3,
                    max_levels=5,
                    include_all_level1=True,
                    output_itemsets_path="output.csv",
                    target_item_1="same",
                    target_item_0="same",  # Same as target_item_1
                )
        finally:
            os.unlink(csv_path)


class TestLoadComparatorConfig:
    """Tests for load_comparator_config function."""

    def test_load_two_file_config(self):
        """Test loading a two-file configuration."""
        # Create temp CSV files
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f1:
            yes_path = f1.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f2:
            no_path = f2.name

        # Create config file
        config_dict = {
            "input_csv_path_for_yes_case": yes_path,
            "input_csv_path_for_no_case": no_path,
            "min_support_for_yes_case": 0.3,
            "min_support_for_no_case": 0.3,
            "max_levels": 5,
            "include_all_level1": True,
            "output_itemsets_path_yes_case": "yes.csv",
            "output_itemsets_path_no_case": "no.csv",
            "output_itemsets_joined": "joined.csv",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f_config:
            config_path = f_config.name
            json.dump(config_dict, f_config)

        try:
            config = load_comparator_config(config_path)

            assert isinstance(config, TwoFileComparatorConfig)
            assert config.min_support_for_yes_case == 0.3

        finally:
            os.unlink(yes_path)
            os.unlink(no_path)
            os.unlink(config_path)

    def test_load_single_file_config(self):
        """Test loading a single-file configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        config_dict = {
            "input_csv_path": csv_path,
            "min_support_for_yes_case": 0.3,
            "min_support_for_no_case": 0.3,
            "max_levels": 5,
            "include_all_level1": True,
            "output_itemsets_path": "output.csv",
            "target_item_1": "outcome=positive",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f_config:
            config_path = f_config.name
            json.dump(config_dict, f_config)

        try:
            config = load_comparator_config(config_path)

            assert isinstance(config, SingleFileComparatorConfig)
            assert config.target_item_1 == "outcome=positive"

        finally:
            os.unlink(csv_path)
            os.unlink(config_path)

    def test_ambiguous_config(self):
        """Test that ambiguous config raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        # Config with both two-file and single-file fields
        config_dict = {
            "input_csv_path_for_yes_case": csv_path,
            "input_csv_path_for_no_case": csv_path,
            "input_csv_path": csv_path,  # Ambiguous!
            "min_support_for_yes_case": 0.3,
            "min_support_for_no_case": 0.3,
            "max_levels": 5,
            "include_all_level1": True,
            "output_itemsets_path": "output.csv",
            "output_itemsets_path_yes_case": "yes.csv",
            "output_itemsets_path_no_case": "no.csv",
            "output_itemsets_joined": "joined.csv",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f_config:
            config_path = f_config.name
            json.dump(config_dict, f_config)

        try:
            with pytest.raises(ValueError, match="Ambiguous"):
                load_comparator_config(config_path)

        finally:
            os.unlink(csv_path)
            os.unlink(config_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

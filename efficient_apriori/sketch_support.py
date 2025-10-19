#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Support for Apache DataSketches theta sketches in Apriori algorithm.
"""

import base64
import csv
from dataclasses import dataclass
from typing import Dict, Set, Optional
from datasketches import compact_theta_sketch, update_theta_sketch


@dataclass
class ItemsetCountSketch:
    """
    ItemsetCount for theta sketch-based counting.

    Attributes
    ----------
    itemset_count : float
        Estimated count from theta sketch.
    sketch : theta_sketch
        The theta sketch object for this itemset.
    """

    itemset_count: float = 0.0
    sketch: Optional[compact_theta_sketch] = None


class ThetaSketchManager:
    """
    Manager for theta sketch-based transaction counting.

    This class provides an interface similar to TransactionManager but works
    with theta sketches instead of raw transactions. It loads sketches from
    a CSV file and provides methods for computing intersections and counts.

    Attributes
    ----------
    sketches_by_item : dict
        Dictionary mapping item names to their theta sketches.
    total_count : float
        Total count estimate from the "total" sketch.
    """

    def __init__(self, csv_path: str):
        """
        Initialize ThetaSketchManager from a CSV file.

        Parameters
        ----------
        csv_path : str
            Path to CSV file (no header) with format: "<item>,<base64_encoded_sketch>"
            First row should be "total" or "" followed by the total count sketch.

        Examples
        --------
        >>> # Assuming sketches.csv exists
        >>> manager = ThetaSketchManager("sketches.csv")  # doctest: +SKIP
        >>> len(manager.items)  # doctest: +SKIP
        10
        """
        self.sketches_by_item: Dict[str, compact_theta_sketch] = {}
        self.total_count: float = 0.0
        self._load_from_csv(csv_path)

    def _load_from_csv(self, csv_path: str):
        """
        Load theta sketches from CSV file.

        Parameters
        ----------
        csv_path : str
            Path to the CSV file.
        """
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)

            for row_idx, row in enumerate(reader):
                if len(row) != 2:
                    raise ValueError(
                        f"Invalid CSV format at row {row_idx + 1}. "
                        f"Expected 2 columns, got {len(row)}"
                    )

                item_name, sketch_b64 = row

                # Decode the base64 sketch
                try:
                    sketch_bytes = base64.b64decode(sketch_b64)
                    sketch = compact_theta_sketch.deserialize(sketch_bytes)
                except Exception as e:
                    raise ValueError(
                        f"Failed to decode sketch at row {row_idx + 1}: {e}"
                    )

                # First row is the total count
                if row_idx == 0:
                    if item_name.lower() == "total" or item_name == "":
                        self.total_count = sketch.get_estimate()
                        continue
                    else:
                        # If first row is not total, treat it as a regular item
                        # and use a default total count
                        pass

                # Store the sketch for this item
                self.sketches_by_item[item_name] = sketch

        if self.total_count == 0.0:
            # If no total was provided, compute it from the union of all sketches
            if self.sketches_by_item:
                from datasketches import theta_union
                union = theta_union()
                for sketch in self.sketches_by_item.values():
                    union.update(sketch)
                self.total_count = union.get_result().get_estimate()
            else:
                raise ValueError("No sketches found in CSV file")

    @property
    def items(self) -> Set[str]:
        """
        Return the set of all item names.

        Returns
        -------
        set
            Set of item names.
        """
        return set(self.sketches_by_item.keys())

    def __len__(self) -> float:
        """
        Return the total count estimate.

        Returns
        -------
        float
            Total count estimate from the total sketch.
        """
        return self.total_count

    def get_sketch(self, item: str) -> Optional[compact_theta_sketch]:
        """
        Get the theta sketch for a specific item.

        Parameters
        ----------
        item : str
            The item name.

        Returns
        -------
        compact_theta_sketch or None
            The sketch for the item, or None if not found.
        """
        return self.sketches_by_item.get(item)

    def get_count(self, item: str) -> float:
        """
        Get the count estimate for a specific item.

        Parameters
        ----------
        item : str
            The item name.

        Returns
        -------
        float
            Count estimate for the item.
        """
        sketch = self.sketches_by_item.get(item)
        if sketch is None:
            return 0.0
        return sketch.get_estimate()

    def get_itemset_sketch(self, itemset: tuple) -> Optional[compact_theta_sketch]:
        """
        Compute the intersection sketch for an itemset.

        Parameters
        ----------
        itemset : tuple
            Tuple of item names.

        Returns
        -------
        compact_theta_sketch or None
            The intersection sketch, or None if any item is not found.

        Examples
        --------
        >>> # Create a simple example
        >>> manager = ThetaSketchManager("sketches.csv")  # doctest: +SKIP
        >>> sketch = manager.get_itemset_sketch(("item1", "item2"))  # doctest: +SKIP
        >>> count = sketch.get_estimate()  # doctest: +SKIP
        """
        if not itemset:
            return None

        # Start with all items in an intersection
        from datasketches import theta_intersection

        intersection = theta_intersection()
        for item in itemset:
            sketch = self.sketches_by_item.get(item)
            if sketch is None:
                return None
            intersection.update(sketch)

        return intersection.get_result()

    def get_itemset_count(self, itemset: tuple) -> float:
        """
        Get the count estimate for an itemset (intersection of items).

        Parameters
        ----------
        itemset : tuple
            Tuple of item names.

        Returns
        -------
        float
            Count estimate for the itemset intersection.

        Examples
        --------
        >>> manager = ThetaSketchManager("sketches.csv")  # doctest: +SKIP
        >>> count = manager.get_itemset_count(("item1", "item2"))  # doctest: +SKIP
        """
        sketch = self.get_itemset_sketch(itemset)
        if sketch is None:
            return 0.0
        return sketch.get_estimate()

    def get_support(self, itemset: tuple) -> float:
        """
        Get the support (relative frequency) for an itemset.

        Parameters
        ----------
        itemset : tuple
            Tuple of item names.

        Returns
        -------
        float
            Support value between 0 and 1.

        Examples
        --------
        >>> manager = ThetaSketchManager("sketches.csv")  # doctest: +SKIP
        >>> support = manager.get_support(("item1", "item2"))  # doctest: +SKIP
        """
        if self.total_count == 0:
            return 0.0
        count = self.get_itemset_count(itemset)
        return count / self.total_count


def create_sketch_from_transaction_ids(
    transaction_ids: Set[int], lg_k: int = 12
) -> compact_theta_sketch:
    """
    Create a theta sketch from a set of transaction IDs.

    Utility function for testing and conversion from transaction-based format.

    Parameters
    ----------
    transaction_ids : set of int
        Set of transaction IDs.
    lg_k : int
        Log base 2 of sketch size. Default 12 (size = 4096).
        Higher values = more accurate but more memory.

    Returns
    -------
    compact_theta_sketch
        A theta sketch containing the transaction IDs.

    Examples
    --------
    >>> sketch = create_sketch_from_transaction_ids({1, 2, 3, 4, 5})
    >>> sketch.get_estimate()
    5.0
    >>> sketch_large = create_sketch_from_transaction_ids({1, 2, 3}, lg_k=16)
    >>> sketch_large.get_estimate()
    3.0
    """
    sketch = update_theta_sketch(lg_k=lg_k)
    for tid in transaction_ids:
        sketch.update(tid)
    return sketch.compact()


def serialize_sketch_to_base64(sketch: compact_theta_sketch) -> str:
    """
    Serialize a theta sketch to a base64-encoded string.

    Parameters
    ----------
    sketch : theta_sketch
        The sketch to serialize.

    Returns
    -------
    str
        Base64-encoded string representation of the sketch.

    Examples
    --------
    >>> sketch = create_sketch_from_transaction_ids({1, 2, 3})
    >>> b64_str = serialize_sketch_to_base64(sketch)
    >>> len(b64_str) > 0
    True
    """
    sketch_bytes = sketch.serialize()
    return base64.b64encode(sketch_bytes).decode('utf-8')


def deserialize_sketch_from_base64(b64_str: str) -> compact_theta_sketch:
    """
    Deserialize a theta sketch from a base64-encoded string.

    Parameters
    ----------
    b64_str : str
        Base64-encoded string representation of the sketch.

    Returns
    -------
    compact_theta_sketch
        The deserialized sketch.

    Examples
    --------
    >>> sketch = create_sketch_from_transaction_ids({1, 2, 3})
    >>> b64_str = serialize_sketch_to_base64(sketch)
    >>> sketch2 = deserialize_sketch_from_base64(b64_str)
    >>> sketch2.get_estimate()
    3.0
    """
    sketch_bytes = base64.b64decode(b64_str)
    return compact_theta_sketch.deserialize(sketch_bytes)


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v"])

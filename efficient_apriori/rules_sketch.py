#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV output formatting for theta sketch-based Apriori results.
"""

import csv
import typing
from pathlib import Path
from efficient_apriori.rules import Rule


def write_itemsets_to_csv(
    itemsets: typing.Dict[int, typing.Dict[tuple, float]],
    total_count: float,
    output_path: str,
    item_separator: str = "&&",
):
    """
    Write frequent itemsets to a CSV file.

    Parameters
    ----------
    itemsets : dict
        Dictionary of {level: {itemset: count}}.
    total_count : float
        Total count for computing support.
    output_path : str
        Path to the output CSV file.
    item_separator : str
        Separator between items in itemsets (default: "&&").

    Output Format
    -------------
    CSV columns: level,frequent_itemset,count,support

    Examples
    --------
    >>> itemsets = {  # doctest: +SKIP
    ...     1: {('item1',): 100.0, ('item2',): 150.0},
    ...     2: {('item1', 'item2'): 80.0}
    ... }
    >>> write_itemsets_to_csv(itemsets, 200.0, "output.csv")  # doctest: +SKIP
    """
    # Create parent directory if it doesn't exist
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(['level', 'frequent_itemset', 'count', 'support'])

        # Write itemsets level by level
        for level in sorted(itemsets.keys()):
            for itemset, count in sorted(itemsets[level].items()):
                # Format the itemset
                if level == 1:
                    itemset_str = itemset[0]
                else:
                    itemset_str = item_separator.join(sorted(itemset))

                # Compute support
                support = count / total_count if total_count > 0 else 0.0

                # Write row
                writer.writerow([level, itemset_str, f"{count:.1f}", f"{support:.6f}"])


def write_rules_to_csv(
    rules: typing.List[Rule],
    output_path: str,
    item_separator: str = "&&",
):
    """
    Write association rules to a CSV file.

    Parameters
    ----------
    rules : list of Rule
        List of association rules.
    output_path : str
        Path to the output CSV file.
    item_separator : str
        Separator between items in itemsets (default: "&&").

    Output Format
    -------------
    CSV columns: level,frequent_itemset,count,support,confidence,lift,conviction

    where:
    - level is the total size of the rule (len(lhs) + len(rhs))
    - frequent_itemset is the full itemset (lhs + rhs)

    Examples
    --------
    >>> from efficient_apriori import Rule  # doctest: +SKIP
    >>> rules = [  # doctest: +SKIP
    ...     Rule(('item1',), ('item2',), 80, 100, 150, 200)
    ... ]
    >>> write_rules_to_csv(rules, "rules.csv")  # doctest: +SKIP
    """
    # Create parent directory if it doesn't exist
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow([
            'level',
            'frequent_itemset',
            'count',
            'support',
            'confidence',
            'lift',
            'conviction'
        ])

        # Write rules
        for rule in rules:
            # Compute level (total size of rule)
            level = len(rule.lhs) + len(rule.rhs)

            # Combine lhs and rhs for the frequent itemset
            full_itemset = tuple(sorted(rule.lhs + rule.rhs))
            itemset_str = item_separator.join(full_itemset)

            # Get metrics
            count_full = rule.count_full if hasattr(rule, 'count_full') else 0.0
            support = rule.support if rule.support is not None else 0.0
            confidence = rule.confidence if rule.confidence is not None else 0.0
            lift = rule.lift if rule.lift is not None else 0.0
            conviction = rule.conviction if rule.conviction is not None else 0.0

            # Write row
            writer.writerow([
                level,
                itemset_str,
                f"{count_full:.1f}",
                f"{support:.6f}",
                f"{confidence:.6f}",
                f"{lift:.6f}",
                f"{conviction:.6f}"
            ])


def format_itemset(itemset: tuple, separator: str = "&&") -> str:
    """
    Format an itemset as a string with a custom separator.

    Parameters
    ----------
    itemset : tuple
        Tuple of items.
    separator : str
        Separator between items.

    Returns
    -------
    str
        Formatted itemset string.

    Examples
    --------
    >>> format_itemset(('item1', 'item2'), separator='&&')
    'item1&&item2'
    >>> format_itemset(('a',), separator='&&')
    'a'
    """
    return separator.join(itemset)


def read_itemsets_from_csv(
    csv_path: str,
    item_separator: str = "&&",
) -> typing.Tuple[typing.Dict[int, typing.Dict[tuple, float]], float]:
    """
    Read frequent itemsets from a CSV file.

    Utility function for loading previously saved itemsets.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file.
    item_separator : str
        Separator between items in itemsets.

    Returns
    -------
    tuple
        (itemsets, max_support) where:
        - itemsets is a dict of {level: {itemset: support}}
        - max_support is the maximum support value found

    Examples
    --------
    >>> # Assuming output.csv exists
    >>> itemsets, max_sup = read_itemsets_from_csv("output.csv")  # doctest: +SKIP
    >>> print(itemsets[1])  # doctest: +SKIP
    {('item1',): 0.5, ('item2',): 0.75}
    """
    itemsets: typing.Dict[int, typing.Dict[tuple, float]] = {}
    max_support = 0.0

    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            level = int(row['level'])
            itemset_str = row['frequent_itemset']
            support = float(row['support'])

            # Parse itemset
            if level == 1:
                itemset = (itemset_str,)
            else:
                itemset = tuple(itemset_str.split(item_separator))

            # Add to dictionary
            if level not in itemsets:
                itemsets[level] = {}
            itemsets[level][itemset] = support

            # Track max support
            max_support = max(max_support, support)

    return itemsets, max_support


def read_rules_from_csv(
    csv_path: str,
    item_separator: str = "&&",
) -> typing.List[typing.Dict[str, typing.Any]]:
    """
    Read association rules from a CSV file.

    Utility function for loading previously saved rules.

    Parameters
    ----------
    csv_path : str
        Path to the CSV file.
    item_separator : str
        Separator between items in itemsets.

    Returns
    -------
    list of dict
        List of rule dictionaries with keys:
        ['level', 'frequent_itemset', 'support', 'confidence', 'lift', 'conviction']

    Examples
    --------
    >>> # Assuming rules.csv exists
    >>> rules = read_rules_from_csv("rules.csv")  # doctest: +SKIP
    >>> print(rules[0])  # doctest: +SKIP
    {'level': 2, 'frequent_itemset': 'item1&&item2', ...}
    """
    rules = []

    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            rule_dict = {
                'level': int(row['level']),
                'frequent_itemset': row['frequent_itemset'],
                'support': float(row['support']),
                'confidence': float(row['confidence']),
                'lift': float(row['lift']),
                'conviction': float(row['conviction']),
            }
            rules.append(rule_dict)

    return rules


if __name__ == "__main__":
    import pytest

    pytest.main(args=[".", "--doctest-modules", "-v"])

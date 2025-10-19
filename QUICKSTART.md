# Quick Start Guide - Theta Sketch Extension

This guide will walk you through using the theta sketch extension for the Efficient-Apriori library.

## Step 1: Install Dependencies

Make sure you have the package installed with its dependencies:

```bash
pip install -e .
```

This will install the `datasketches` library which is required for theta sketch support.

## Step 2: Convert Your Transaction Data to Sketches

If you have existing transaction data, use the `convert_to_sketches.py` script:

```bash
python convert_to_sketches.py \
  --input example_transactions.csv \
  --output data/sketches.csv \
  -v 2
```

This will:
- Read your transaction data from `example_transactions.csv`
- Create theta sketches for each item
- Save the sketches to `data/sketches.csv`

Example output:
```
Processing 10 transactions...
Found 5 unique items
Creating total sketch...
Total count: 10
Creating item sketches...
  apple: count=5, support=0.500
  bacon: count=8, support=0.800
  banana: count=4, support=0.400
  eggs: count=7, support=0.700
  soup: count=6, support=0.600

Sketches written to: data/sketches.csv
```

## Step 3: Configure the Apriori Algorithm

Edit `example_config.json` to set your parameters:

```json
{
  "input_csv_path": "data/sketches.csv",
  "min_support": 0.3,
  "max_levels": 5,
  "include_all_level1": true,
  "output_itemsets_path": "output/frequent_itemsets.csv",
  "output_rules_path": "output/association_rules.csv",
  "item_separator": "&&",
  "min_confidence": 0.5
}
```

**Key parameters:**
- `min_support`: 0.3 means items must appear in at least 30% of transactions
- `max_levels`: Maximum itemset size to consider
- `include_all_level1`: If true, show all items in output (even below min_support)
- `min_confidence`: Minimum confidence for association rules (0.5 = 50%)

## Step 4: Run the Apriori Algorithm

```bash
python apriori_sketch.py --config example_config.json -v 1
```

Example output:
```
Loading theta sketches from: data/sketches.csv
Loaded 5 items
Total count estimate: 10.00

Running Apriori algorithm...
  Min support: 0.3
  Max levels: 5
  Include all level 1: True

Frequent itemsets found:
  Level 1: 5 itemsets
  Level 2: 8 itemsets
  Level 3: 4 itemsets

Writing frequent itemsets to: output/frequent_itemsets.csv

Generating association rules...
  Min confidence: 0.5
Generated 12 association rules

Writing association rules to: output/association_rules.csv

Done!
```

## Step 5: Examine the Results

### Frequent Itemsets (output/frequent_itemsets.csv)

```csv
level,frequent_itemset,support
1,apple,0.500000
1,bacon,0.800000
1,banana,0.400000
1,eggs,0.700000
1,soup,0.600000
2,bacon&&eggs,0.600000
2,bacon&&soup,0.400000
...
```

This shows:
- Level 1: Individual items and their support
- Level 2+: Combinations of items that frequently appear together

### Association Rules (output/association_rules.csv)

```csv
level,frequent_itemset,support,confidence,lift,conviction
2,bacon&&eggs,0.600000,0.750000,1.071429,1.600000
2,eggs&&soup,0.400000,0.571429,0.952381,0.800000
...
```

This shows rules like:
- If someone buys `eggs`, there's a 75% chance they also buy `bacon`
- The `lift` value shows how much more likely the combination is vs. random

## Advanced Usage

### Using the Python API

```python
from efficient_apriori import (
    ThetaSketchManager,
    itemsets_from_sketches,
    generate_rules_apriori,
)

# Load sketches
manager = ThetaSketchManager("data/sketches.csv")

# Run Apriori
itemsets, total = itemsets_from_sketches(
    manager,
    min_support=0.3,
    max_length=5,
    verbosity=1,
)

# Examine results
for level, items in itemsets.items():
    print(f"\nLevel {level}:")
    for itemset, count in items.items():
        support = count / total
        print(f"  {itemset}: count={count:.0f}, support={support:.3f}")
```

### Custom Item Separator

Want to use a different separator in the output?

```json
{
  "item_separator": " | "
}
```

Output will look like:
```csv
2,bacon | eggs,0.600000
```

### Only Items Above Threshold

Set `include_all_level1` to `false` to only show items meeting `min_support`:

```json
{
  "include_all_level1": false
}
```

## Understanding the Output Metrics

### Support
The fraction of transactions containing the itemset.
- `support = count / total_transactions`
- Example: If eggs appear in 7 out of 10 transactions, support = 0.7

### Confidence
For a rule X → Y, the probability of Y given X.
- `confidence = P(Y|X) = count(X∪Y) / count(X)`
- Example: If 6 transactions have both eggs and bacon, and 7 have eggs:
  - confidence(eggs → bacon) = 6/7 ≈ 0.857

### Lift
How much more likely X and Y appear together vs. independently.
- `lift = support(X∪Y) / (support(X) × support(Y))`
- Lift > 1: Positive correlation
- Lift < 1: Negative correlation
- Lift ≈ 1: Independent

### Conviction
How much more often Y does NOT appear without X.
- High conviction means the rule rarely makes mistakes
- conviction(X → Y) = ∞ means Y always appears with X

## Troubleshooting

### Error: "datasketches not installed"

Install the dependency:
```bash
pip install datasketches
```

### Error: "Input CSV file not found"

Make sure your paths in `config.json` are correct. Use relative or absolute paths.

### No itemsets found

Try lowering `min_support` in your config file. Start with 0.1 (10%) and adjust.

### Memory issues

Theta sketches are already memory-efficient. If you still have issues:
1. Reduce `max_levels` (try 3-4 instead of 8)
2. Increase `min_support` to filter out rare items

## Next Steps

- Read [THETA_SKETCH_EXTENSION.md](THETA_SKETCH_EXTENSION.md) for detailed documentation
- Explore the test files in `efficient_apriori/tests/test_sketch.py` for more examples
- Check out the original Apriori algorithm in the main README

## Example Workflow

Complete example from start to finish:

```bash
# 1. Convert transactions to sketches
python convert_to_sketches.py \
  --input example_transactions.csv \
  --output data/sketches.csv

# 2. Edit example_config.json to set your parameters

# 3. Run the algorithm
python apriori_sketch.py --config example_config.json -v 1

# 4. Check the results
cat output/frequent_itemsets.csv
cat output/association_rules.csv
```

Happy mining! 🎯

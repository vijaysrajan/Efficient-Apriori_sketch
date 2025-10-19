# Theta Sketch Extension for Efficient-Apriori

This extension adds support for running the Apriori algorithm using [Apache DataSketches](https://datasketches.apache.org/) theta sketches instead of raw transactions. This is useful for:

- Privacy-preserving analysis (only sketches are shared, not raw data)
- Working with pre-aggregated data
- Distributed computation scenarios
- Memory-efficient processing of large datasets

## Features

- ✅ Support for Apache DataSketches theta sketches
- ✅ CSV-based input/output format
- ✅ Configurable via JSON configuration files
- ✅ Optional inclusion of all level 1 items regardless of min_support
- ✅ Customizable item separator for output
- ✅ Command-line interface
- ✅ Python API for programmatic use
- ✅ Full backward compatibility with existing Apriori implementation

## Installation

The extension is included in the package. Make sure you have the `datasketches` dependency installed:

```bash
pip install efficient-apriori
```

## Usage

### Command Line Interface

1. **Prepare your input CSV file** with theta sketches in the following format (no header):

```csv
total,<base64_encoded_total_sketch>
item1,<base64_encoded_sketch_for_item1>
item2,<base64_encoded_sketch_for_item2>
...
```

The first row should contain either "total" or an empty string, followed by a base64-encoded theta sketch representing the total count. The CSV file should NOT have a header row.

2. **Create a configuration file** (e.g., `config.json`):

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

3. **Run the algorithm**:

```bash
python apriori_sketch.py --config config.json
```

Or with verbosity:

```bash
python apriori_sketch.py --config config.json -v 2
```

### Python API

```python
from efficient_apriori import (
    ThetaSketchManager,
    itemsets_from_sketches,
    generate_rules_apriori,
    write_itemsets_to_csv,
    write_rules_to_csv,
)

# Load sketches from CSV
manager = ThetaSketchManager("data/sketches.csv")

# Run Apriori algorithm
itemsets, total_count = itemsets_from_sketches(
    manager,
    min_support=0.3,
    max_length=5,
    include_all_level1=True,
    verbosity=1,
)

# Generate association rules
rules = list(generate_rules_apriori(
    itemsets,
    min_confidence=0.5,
    num_transactions=int(total_count),
))

# Write results to CSV
write_itemsets_to_csv(itemsets, total_count, "output/itemsets.csv")
write_rules_to_csv(rules, "output/rules.csv")
```

## Configuration Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `input_csv_path` | string | Path to the CSV file containing theta sketches |
| `min_support` | float (0-1) | Minimum support threshold for frequent itemsets |
| `max_levels` | int | Maximum number of levels for itemset generation |
| `include_all_level1` | bool | If true, include all level 1 items in output regardless of min_support (they won't be used for higher levels) |
| `output_itemsets_path` | string | Path for the output frequent itemsets CSV |
| `output_rules_path` | string | Path for the output association rules CSV |
| `item_separator` | string | Separator between items in itemsets (default: "&&") |
| `min_confidence` | float (0-1) | Minimum confidence threshold for association rules (default: 0.5) |
| `sketch_lg_k` | int (4-26) | Log base 2 of sketch size for creating sketches (default: 12, size=4096). Higher = more accurate but more memory |

## Output Format

### Frequent Itemsets CSV

Format: `level,frequent_itemset,count,support`

Example:
```csv
level,frequent_itemset,count,support
1,item1,75.0,0.750000
1,item2,60.0,0.600000
2,item1&&item2,50.0,0.500000
3,item1&&item2&&item3,35.0,0.350000
```

### Association Rules CSV

Format: `level,frequent_itemset,count,support,confidence,lift,conviction`

Example:
```csv
level,frequent_itemset,count,support,confidence,lift,conviction
2,item1&&item2,50.0,0.500000,0.667000,1.112000,1.500000
3,item1&&item2&&item3,35.0,0.350000,0.700000,1.167000,1.667000
```

## Creating Theta Sketches

### Sketch Size Parameter (lg_k)

The `sketch_lg_k` parameter controls the accuracy and memory usage of theta sketches:

- **lg_k = 12** (default): Sketch size = 2^12 = 4,096 entries (~99% accuracy)
- **lg_k = 14**: Sketch size = 2^14 = 16,384 entries (~99.5% accuracy)
- **lg_k = 16**: Sketch size = 2^16 = 65,536 entries (~99.9% accuracy)

**Choosing lg_k:**
- Use lg_k=12 for most cases (good balance)
- Increase for very large datasets or when high precision is critical
- Decrease for memory-constrained environments

### From Transaction IDs

```python
from efficient_apriori import (
    create_sketch_from_transaction_ids,
    serialize_sketch_to_base64,
)

# Create a sketch from transaction IDs with default size
transaction_ids = {0, 1, 2, 3, 4}
sketch = create_sketch_from_transaction_ids(transaction_ids)

# Create a sketch with custom size for higher accuracy
sketch_large = create_sketch_from_transaction_ids(transaction_ids, lg_k=16)

# Serialize to base64 for CSV storage
b64_string = serialize_sketch_to_base64(sketch)
```

### From Raw Transactions (Converting Existing Data)

```python
import csv
from collections import defaultdict
from efficient_apriori import (
    create_sketch_from_transaction_ids,
    serialize_sketch_to_base64,
)

# Example transactions
transactions = [
    ['eggs', 'bacon', 'soup'],
    ['eggs', 'bacon', 'apple'],
    ['soup', 'bacon', 'banana'],
]

# Build transaction indices for each item
indices_by_item = defaultdict(set)
for i, transaction in enumerate(transactions):
    for item in transaction:
        indices_by_item[item].add(i)

# Create sketches and write to CSV
with open('sketches.csv', 'w', newline='') as f:
    writer = csv.writer(f)

    # Write total sketch
    total_sketch = create_sketch_from_transaction_ids(set(range(len(transactions))))
    writer.writerow(['total', serialize_sketch_to_base64(total_sketch)])

    # Write item sketches
    for item, indices in indices_by_item.items():
        sketch = create_sketch_from_transaction_ids(indices)
        writer.writerow([item, serialize_sketch_to_base64(sketch)])
```

## Special Features

### Include All Level 1 Items

When `include_all_level1` is set to `true`, all level 1 items are included in the output CSV, even if their support is below `min_support`. However, items below the threshold will NOT be used to generate higher-level itemsets.

This is useful for:
- Getting a complete view of all items in the dataset
- Analysis that requires knowing all individual item frequencies
- Debugging and data exploration

Example:
```python
# With include_all_level1=True and min_support=0.5
# Item A: support 0.7 → Included in output, used for level 2+
# Item B: support 0.6 → Included in output, used for level 2+
# Item C: support 0.3 → Included in output, NOT used for level 2+
```

### Custom Item Separator

The `item_separator` parameter allows you to customize how items are joined in the output CSV:

```json
{
  "item_separator": " | "
}
```

Output:
```csv
2,item1 | item2,0.500000
```

## Architecture

The extension follows a modular design:

```
efficient_apriori/
├── config.py              # Configuration management
├── sketch_support.py      # ThetaSketchManager and sketch utilities
├── itemsets_sketch.py     # Sketch-based itemset generation
├── rules_sketch.py        # CSV formatting for output
└── tests/
    └── test_sketch.py     # Comprehensive test suite

apriori_sketch.py          # CLI script
```

All existing code remains unchanged, ensuring full backward compatibility.

## Testing

Run the test suite:

```bash
pytest efficient_apriori/tests/test_sketch.py -v
```

## Examples

See `example_config.json` for a sample configuration file.

## Performance Notes

- Theta sketches provide approximate counts with high accuracy
- Memory usage is significantly lower than storing full transaction data
- Intersection operations are efficient even for large sketches
- Ideal for distributed or privacy-preserving scenarios

## Limitations

- Counts are estimates (though typically very accurate)
- Cannot retrieve original transaction IDs from sketches
- Requires pre-computation of sketches from raw data

## Contributing

Contributions are welcome! Please ensure:
- All tests pass
- Code follows PEP8 style guidelines
- New features include appropriate tests

## References

- [Apache DataSketches](https://datasketches.apache.org/)
- [Theta Sketch Documentation](https://datasketches.apache.org/docs/Theta/ThetaSketchFramework.html)
- [Original Apriori Paper](https://www.macs.hw.ac.uk/~dwcorne/Teaching/agrawal94fast.pdf)

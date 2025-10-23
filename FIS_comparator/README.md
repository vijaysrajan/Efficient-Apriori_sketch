# FIS-based Comparator

A tool for comparing frequent itemsets between two classes (yes/no) using theta sketches, inspired by classification-based association rules.

## Overview

The FIS-based Comparator implements a comparison methodology inspired by the paper ["Integrating Classification and Association Rule Mining"](https://rsrikant.com/papers/kdd97_class.pdf) by Liu et al. (KDD 1998). It uses Apache DataSketches theta sketches to efficiently compute and compare frequent itemsets between two classes.

Unlike traditional association rule mining that finds patterns across all data, this tool focuses on finding patterns that distinguish between two classes (e.g., yes/no, positive/negative, success/failure).

## Features

- **Three Operation Modes**:
  1. Two-file mode: Separate CSV files for yes and no cases
  2. Single-file with one target: Split using intersection and A-not-B operations
  3. Single-file with two targets: Split using two intersection operations

- **Efficient Sketch-based Computation**: Uses theta sketches for approximate counting with bounded error
- **Full Outer Join**: Compares itemsets from both classes with detailed metrics
- **Configurable Parameters**: Flexible min support, max levels, and output options

## Installation

The FIS_comparator is part of the Efficient-Apriori_sketch project. Ensure you have the required dependencies:

```bash
pip install datasketches
```

## Usage

### Command Line Interface

```bash
python FIS_comparator/fis_comparator.py --config my_comparator_config.json -v 1
```

Options:
- `--config`: Path to JSON configuration file (required)
- `-v, --verbosity`: Verbosity level (0=quiet, 1=normal, 2=verbose)

### Configuration Modes

#### Mode 1: Two-File Comparison

Use this when you have separate CSV files for yes and no cases.

**Configuration Example:**

```json
{
  "input_csv_path_for_yes_case": "./input/yes_sketches.csv",
  "input_csv_path_for_no_case": "./input/no_sketches.csv",
  "min_support_for_yes_case": 0.05,
  "min_support_for_no_case": 0.05,
  "max_levels": 5,
  "include_all_level1": true,
  "output_itemsets_path_yes_case": "./output/yes_itemsets.csv",
  "output_itemsets_path_no_case": "./output/no_itemsets.csv",
  "output_itemsets_joined": "./output/joined.csv",
  "item_separator": " && ",
  "sketch_lg_k_yes_case": 12,
  "sketch_lg_k_no_case": 12
}
```

**Workflow:**
1. Load yes and no CSV files separately
2. Run Apriori algorithm on each with respective min_support
3. Write separate itemset files
4. Perform full outer join and write joined results

#### Mode 2a: Single-File with One Target

Use this when you want to split one CSV file using a target item. The yes case is computed by intersecting all sketches with the target, and the no case uses A-not-B (sketches minus target).

**Configuration Example:**

```json
{
  "input_csv_path": "./input/sketches.csv",
  "min_support_for_yes_case": 0.05,
  "min_support_for_no_case": 0.05,
  "max_levels": 5,
  "include_all_level1": true,
  "output_itemsets_path": "./output/joined.csv",
  "item_separator": " && ",
  "sketch_lg_k": 12,
  "target_item_1": "outcome=positive"
}
```

**Workflow:**
1. Load CSV file
2. Extract target_item_1 sketch
3. Create YES case: Intersect all other sketches with target_item_1
4. Create NO case: A-not-B all other sketches with target_item_1
5. Run Apriori on both cases
6. Perform full outer join and write results

#### Mode 2b: Single-File with Two Targets

Use this when you have mutually exclusive target items (e.g., positive/negative outcomes).

**Configuration Example:**

```json
{
  "input_csv_path": "./input/sketches.csv",
  "min_support_for_yes_case": 0.05,
  "min_support_for_no_case": 0.05,
  "max_levels": 5,
  "include_all_level1": true,
  "output_itemsets_path": "./output/joined.csv",
  "item_separator": " && ",
  "sketch_lg_k": 12,
  "target_item_1": "outcome=positive",
  "target_item_0": "outcome=negative"
}
```

**Workflow:**
1. Load CSV file
2. Extract both target_item_1 and target_item_0 sketches
3. Create YES case: Intersect all other sketches with target_item_1
4. Create NO case: Intersect all other sketches with target_item_0
5. Run Apriori on both cases
6. Perform full outer join and write results

### Input Format

CSV files should have the format:
```
total,<base64_encoded_total_sketch>
dimension=value/item,<base64_encoded_sketch>
dimension=value/item,<base64_encoded_sketch>
...
```

The first row contains the total count sketch (item name can be "total" or empty).

### Output Format

The joined output CSV contains the following columns:

| Column | Description |
|--------|-------------|
| `Level` | Size of the itemset (1, 2, 3, ...) |
| `Frequent_itemset` | String representation of the itemset |
| `Frequent_item_set_seen_in` | "both", "yes", or "no" |
| `Yes_case_count` | Count in yes case (or min_support × total if not frequent) |
| `No_case_count` | Count in no case (or min_support × total if not frequent) |
| `Total` | Sum of yes and no counts |
| `Yes_percentage` | Percentage of yes in total (rounded to 3 decimals) |

**Example Output:**

```csv
Level,Frequent_itemset,Frequent_item_set_seen_in,Yes_case_count,No_case_count,Total,Yes_percentage
1,symptom=fever,both,850.0,420.0,1270.0,66.929
1,symptom=cough,both,720.0,380.0,1100.0,65.455
2,symptom=fever && symptom=cough,yes,580.0,50.0,630.0,92.063
1,treatment=medicine_A,no,100.0,450.0,550.0,18.182
```

## Configuration Parameters

### Common Parameters

- `min_support_for_yes_case` (float): Minimum support threshold for yes case (0.0-1.0)
- `min_support_for_no_case` (float): Minimum support threshold for no case (0.0-1.0)
- `max_levels` (int): Maximum itemset depth/level
- `include_all_level1` (bool): Include all level 1 items regardless of min_support
- `item_separator` (str): Separator for items in itemsets (default: " && ")

### Two-File Mode Parameters

- `input_csv_path_for_yes_case` (str): Path to yes case CSV
- `input_csv_path_for_no_case` (str): Path to no case CSV
- `output_itemsets_path_yes_case` (str): Output path for yes itemsets
- `output_itemsets_path_no_case` (str): Output path for no itemsets
- `output_itemsets_joined` (str): Output path for joined results
- `sketch_lg_k_yes_case` (int): Sketch size parameter for yes case (4-26, default: 12)
- `sketch_lg_k_no_case` (int): Sketch size parameter for no case (4-26, default: 12)

### Single-File Mode Parameters

- `input_csv_path` (str): Path to input CSV
- `output_itemsets_path` (str): Output path for joined results
- `sketch_lg_k` (int): Sketch size parameter (4-26, default: 12)
- `target_item_1` (str): Target item for yes case (mandatory)
- `target_item_0` (str): Target item for no case (optional)

## Use Cases

### Medical Diagnosis

Compare symptom patterns between patients with positive vs. negative test results:

```json
{
  "input_csv_path": "patient_symptoms.csv",
  "target_item_1": "test_result=positive",
  "target_item_0": "test_result=negative",
  ...
}
```

### Customer Segmentation

Find feature patterns that distinguish customers who purchased vs. didn't purchase:

```json
{
  "input_csv_path": "customer_features.csv",
  "target_item_1": "purchase=yes",
  "target_item_0": "purchase=no",
  ...
}
```

### Fraud Detection

Identify transaction patterns associated with fraudulent vs. legitimate transactions:

```json
{
  "input_csv_path_for_yes_case": "fraudulent_transactions.csv",
  "input_csv_path_for_no_case": "legitimate_transactions.csv",
  ...
}
```

## Technical Details

### Sketch Operations

The tool uses three main sketch operations from Apache DataSketches:

1. **Intersection**: Computes the overlap between two sketches
   ```python
   intersection = theta_intersection()
   intersection.update(sketch_a)
   intersection.update(sketch_b)
   result = intersection.get_result()
   ```

2. **A-not-B**: Subtracts one sketch from another
   ```python
   anotb = theta_a_not_b()
   result = anotb.compute(sketch_a, sketch_b)  # A - B
   ```

3. **Union**: Combines sketches for total count
   ```python
   union = theta_union()
   union.update(sketch_a)
   union.update(sketch_b)
   result = union.get_result()
   ```

### Full Outer Join Algorithm

1. Collect all unique (level, itemset) pairs from both yes and no cases
2. For each pair:
   - Determine presence: "both", "yes", or "no"
   - Get yes_count (or min_support × yes_total if not present)
   - Get no_count (or min_support × no_total if not present)
   - Calculate total and yes_percentage
3. Sort by level, then by yes_percentage (descending), then by itemset
4. Write to CSV

### Default Count Estimation

When an itemset appears in only one case, the count for the other case is estimated as:
```
estimated_count = min_support × total_count
```

This conservative estimate represents the threshold below which the itemset is not considered frequent.

## Module Structure

```
FIS_comparator/
├── __init__.py                  # Package exports
├── comparator_config.py         # Configuration dataclasses and loader
├── sketch_operations.py         # Sketch manipulation functions
├── itemset_joiner.py           # Full outer join implementation
├── comparator_core.py          # Main comparison workflows
├── fis_comparator.py           # CLI entry point
└── tests/
    ├── test_comparator_config.py
    ├── test_sketch_operations.py
    └── test_itemset_joiner.py
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest FIS_comparator/tests/ -v

# Run specific test module
pytest FIS_comparator/tests/test_sketch_operations.py -v

# Run with coverage
pytest FIS_comparator/tests/ --cov=FIS_comparator --cov-report=html
```

## References

1. Liu, B., Hsu, W., & Ma, Y. (1998). Integrating Classification and Association Rule Mining.
   In Proceedings of the Fourth International Conference on Knowledge Discovery and Data Mining (KDD-98).
   https://rsrikant.com/papers/kdd97_class.pdf

2. Apache DataSketches: https://datasketches.apache.org/

3. Efficient-Apriori: The underlying Apriori implementation used for frequent itemset mining

## License

This module is part of the Efficient-Apriori_sketch project and follows the same license.

## Contributing

Contributions are welcome! Please ensure that:
- All tests pass
- New features include corresponding tests
- Code follows the existing style conventions
- Documentation is updated accordingly

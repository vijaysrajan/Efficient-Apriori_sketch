#!/bin/bash
# Quick script to run the complete analysis pipeline

# Check if input file is provided
if [ $# -eq 0 ]; then
    echo "Usage: ./run_analysis.sh <input_csv_file> [min_support] [min_confidence]"
    echo ""
    echo "Example: ./run_analysis.sh my_transactions.csv 0.3 0.5"
    echo ""
    exit 1
fi

INPUT_FILE=$1
MIN_SUPPORT=${2:-0.3}
MIN_CONFIDENCE=${3:-0.5}

# Extract base name for outputs
BASENAME=$(basename "$INPUT_FILE" .csv)
SKETCH_FILE="data/${BASENAME}_sketches.csv"
CONFIG_FILE="${BASENAME}_config.json"
ITEMSETS_OUTPUT="output/${BASENAME}_frequent_itemsets.csv"
RULES_OUTPUT="output/${BASENAME}_association_rules.csv"

echo "=========================================="
echo "Apriori Analysis Pipeline"
echo "=========================================="
echo "Input file: $INPUT_FILE"
echo "Min support: $MIN_SUPPORT"
echo "Min confidence: $MIN_CONFIDENCE"
echo ""

# Step 1: Convert to sketches
echo "Step 1/3: Converting transactions to theta sketches..."
python convert_to_sketches.py \
  --input "$INPUT_FILE" \
  --output "$SKETCH_FILE" \
  -v 1

if [ $? -ne 0 ]; then
    echo "Error: Failed to convert transactions to sketches"
    exit 1
fi

# Step 2: Create config file
echo ""
echo "Step 2/3: Creating configuration file..."
cat > "$CONFIG_FILE" << EOF
{
  "input_csv_path": "$SKETCH_FILE",
  "min_support": $MIN_SUPPORT,
  "max_levels": 5,
  "include_all_level1": true,
  "output_itemsets_path": "$ITEMSETS_OUTPUT",
  "output_rules_path": "$RULES_OUTPUT",
  "item_separator": "&&",
  "min_confidence": $MIN_CONFIDENCE,
  "sketch_lg_k": 12
}
EOF

echo "Created: $CONFIG_FILE"

# Step 3: Run Apriori
echo ""
echo "Step 3/3: Running Apriori algorithm..."
python apriori_sketch.py --config "$CONFIG_FILE" -v 1

if [ $? -ne 0 ]; then
    echo "Error: Failed to run Apriori algorithm"
    exit 1
fi

# Summary
echo ""
echo "=========================================="
echo "Analysis Complete!"
echo "=========================================="
echo "Outputs:"
echo "  - Frequent itemsets: $ITEMSETS_OUTPUT"
echo "  - Association rules: $RULES_OUTPUT"
echo ""
echo "View results:"
echo "  cat $ITEMSETS_OUTPUT"
echo "  cat $RULES_OUTPUT"

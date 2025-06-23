#!/bin/bash
"""
Process H3K27Ac CUT&Tag peak data - Shell script version

This script provides the shell-based implementation for processing H3K27Ac peak data,
following the exact commands from the original workflow.
"""

set -e  # Exit on any error

# Function to print usage
usage() {
    echo "Usage: $0 [OPTIONS] -o OUTPUT_PREFIX FILE1 FILE2 [FILE3 ...]"
    echo ""
    echo "Process H3K27Ac CUT&Tag BED files into standardized format"
    echo ""
    echo "Options:"
    echo "  -o PREFIX    Output file prefix (required)"
    echo "  -n           Skip overlapping peak merge"
    echo "  -s           Skip sorting"
    echo "  -v           Verbose output"
    echo "  -h           Show this help"
    echo ""
    echo "Example:"
    echo "  $0 -o E145_E E145_E_H3K27ac_CUTTAG_1.bed E145_E_H3K27ac_CUTTAG_2.bed"
    exit 1
}

# Default parameters
MERGE_OVERLAPPING=true
SORT_PEAKS=true
VERBOSE=false
OUTPUT_PREFIX=""

# Parse command line options
while getopts "o:nsvh" opt; do
    case $opt in
        o)
            OUTPUT_PREFIX="$OPTARG"
            ;;
        n)
            MERGE_OVERLAPPING=false
            ;;
        s)
            SORT_PEAKS=false
            ;;
        v)
            VERBOSE=true
            ;;
        h)
            usage
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
    esac
done

shift $((OPTIND-1))

# Check if output prefix is provided
if [ -z "$OUTPUT_PREFIX" ]; then
    echo "Error: Output prefix is required (-o option)" >&2
    usage
fi

# Check if input files are provided
if [ $# -eq 0 ]; then
    echo "Error: At least one input file is required" >&2
    usage
fi

# Validate input files
for file in "$@"; do
    if [ ! -f "$file" ]; then
        echo "Error: File not found: $file" >&2
        exit 1
    fi
done

# Check if bedtools is available when needed
if [ "$MERGE_OVERLAPPING" = true ] || [ "$SORT_PEAKS" = true ]; then
    if ! command -v bedtools &> /dev/null; then
        echo "Error: bedtools is required but not found in PATH" >&2
        echo "Please install bedtools or use -n and -s options to skip bedtools operations" >&2
        exit 1
    fi
fi

OUTPUT_FILE="${OUTPUT_PREFIX}_H3K27ac_CUTTAG_union.bed"

# Log function
log() {
    if [ "$VERBOSE" = true ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
    fi
}

log "Processing ${#} H3K27Ac peak files..."
log "Output file: $OUTPUT_FILE"

# AWK script to extract first 3 columns (chr, start, end)
# This matches the exact logic from command_log.txt
AWK_SCRIPT='BEGIN{OFS="\t"}{print $1,$2,$3}'

log "Running peak processing..."

# Build and execute the command based on options
if [ "$MERGE_OVERLAPPING" = true ] && [ "$SORT_PEAKS" = true ]; then
    # Full processing: cat + awk + bedtools sort + bedtools merge (original command)
    log "Processing with sorting and overlapping peak merge..."
    cat "$@" | \
    awk "$AWK_SCRIPT" | \
    bedtools sort -i - | \
    bedtools merge -i - > "$OUTPUT_FILE"
elif [ "$SORT_PEAKS" = true ]; then
    # cat + awk + bedtools sort only
    log "Processing with sorting only..."
    cat "$@" | \
    awk "$AWK_SCRIPT" | \
    bedtools sort -i - > "$OUTPUT_FILE"
else
    # cat + awk only
    log "Processing without sorting or merging..."
    cat "$@" | \
    awk "$AWK_SCRIPT" > "$OUTPUT_FILE"
fi

# Verify output
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "Error: Output file was not created" >&2
    exit 1
fi

# Count lines for verification
LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
log "Successfully created: $OUTPUT_FILE"
log "Output contains $(printf "%'d" $LINE_COUNT) peaks"

# Basic format validation
log "Validating output format..."
SAMPLE_LINES=10
if head -n $SAMPLE_LINES "$OUTPUT_FILE" | awk '
{
    if (NF < 3) {
        print "Error: Line " NR " has fewer than 3 fields: " $0 > "/dev/stderr"
        exit 1
    }
    # Check if coordinates are numeric
    if ($2 !~ /^[0-9]+$/ || $3 !~ /^[0-9]+$/) {
        print "Error: Line " NR " has non-numeric coordinates: " $0 > "/dev/stderr"
        exit 1
    }
    # Check if start < end
    if ($2 >= $3) {
        print "Error: Line " NR " has start >= end: " $0 > "/dev/stderr"
        exit 1
    }
}
END {
    if (NR > 0) print "Format validation passed for " NR " sample lines" > "/dev/stderr"
}'; then
    log "Output validation successful"
else
    echo "Error: Output validation failed" >&2
    exit 1
fi

echo "Processing completed successfully: $OUTPUT_FILE" 
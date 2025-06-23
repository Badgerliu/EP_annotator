#!/bin/bash
"""
Process HiCUT interaction data - Shell script version

This script provides the shell-based implementation for processing HiCUT data,
following the exact commands from the original workflow.
"""

set -e  # Exit on any error

# Function to print usage
usage() {
    echo "Usage: $0 [OPTIONS] -o OUTPUT_PREFIX FILE1 FILE2 [FILE3 ...]"
    echo ""
    echo "Process HiCUT allValidPairs files into standardized BEDPE format"
    echo ""
    echo "Options:"
    echo "  -o PREFIX    Output file prefix (required)"
    echo "  -n           Skip duplicate removal"
    echo "  -s           Skip sorting"
    echo "  -v           Verbose output"
    echo "  -h           Show this help"
    echo ""
    echo "Example:"
    echo "  $0 -o E145_E E145_E_1.allValidPairs E145_E_2.allValidPairs"
    exit 1
}

# Default parameters
REMOVE_DUPLICATES=true
SORT_OUTPUT=true
VERBOSE=false
OUTPUT_PREFIX=""

# Parse command line options
while getopts "o:nsvh" opt; do
    case $opt in
        o)
            OUTPUT_PREFIX="$OPTARG"
            ;;
        n)
            REMOVE_DUPLICATES=false
            ;;
        s)
            SORT_OUTPUT=false
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

OUTPUT_FILE="${OUTPUT_PREFIX}_HiCUT_union.bedpe"

# Log function
log() {
    if [ "$VERBOSE" = true ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
    fi
}

log "Processing ${#} HiCUT files..."
log "Output file: $OUTPUT_FILE"

# AWK script to process HiCUT data
# This matches the exact logic from command_log.txt
AWK_SCRIPT='
# Convert each line to chrA posA chrB posB (ensuring A < B order)
{
    chr1=$2; pos1=$3; chr2=$5; pos2=$6
    # Compare chromosome first, then coordinates to ensure unique order
    if (chr1 < chr2 || (chr1==chr2 && pos1 < pos2)) {
        print chr1"\t"pos1"\t"chr2"\t"pos2
    } else {
        print chr2"\t"pos2"\t"chr1"\t"pos1
    }
}'

log "Running AWK processing..."

# Build and execute the command based on options
if [ "$REMOVE_DUPLICATES" = true ] && [ "$SORT_OUTPUT" = true ]; then
    # Full processing: AWK + sort + uniq (original command from log)
    log "Processing with sorting and duplicate removal..."
    awk "$AWK_SCRIPT" "$@" | \
    sort -k1,1 -k2,2n -k3,3 -k4,4n | \
    uniq > "$OUTPUT_FILE"
elif [ "$SORT_OUTPUT" = true ]; then
    # AWK + sort only
    log "Processing with sorting only..."
    awk "$AWK_SCRIPT" "$@" | \
    sort -k1,1 -k2,2n -k3,3 -k4,4n > "$OUTPUT_FILE"
else
    # AWK only
    log "Processing without sorting..."
    awk "$AWK_SCRIPT" "$@" > "$OUTPUT_FILE"
fi

# Verify output
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "Error: Output file was not created" >&2
    exit 1
fi

# Count lines for verification
LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
log "Successfully created: $OUTPUT_FILE"
log "Output contains $(printf "%'d" $LINE_COUNT) interactions"

# Basic format validation
log "Validating output format..."
SAMPLE_LINES=10
if head -n $SAMPLE_LINES "$OUTPUT_FILE" | awk '
{
    if (NF < 4) {
        print "Error: Line " NR " has fewer than 4 fields: " $0 > "/dev/stderr"
        exit 1
    }
    # Check if coordinates are numeric
    if ($2 !~ /^[0-9]+$/ || $4 !~ /^[0-9]+$/) {
        print "Error: Line " NR " has non-numeric coordinates: " $0 > "/dev/stderr"
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
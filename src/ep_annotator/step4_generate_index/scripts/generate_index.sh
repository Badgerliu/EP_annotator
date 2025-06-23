#!/bin/bash

# Step 4: Generate E-P Interaction Index
# This script combines promoter generation and E-P annotation
# Usage: ./generate_index.sh -i interactions.bedpe -r refseq.bed -o output.bedpe.gz [options]

set -euo pipefail

# Default parameters
REFSEQ_FILE=""
BEDPE_FILE=""
OUTPUT_FILE=""
PROMOTER_FILE=""
UPSTREAM=1000
DOWNSTREAM=1001
VERBOSE=false
KEEP_TEMP=false
USE_INTERVAL_TREE=true

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STEP4_DIR="$(dirname "$SCRIPT_DIR")"

# Temporary directory for intermediate files
TEMP_DIR=""

# Function to show usage
usage() {
    cat << EOF
Step 4: Generate E-P Interaction Index

This script generates promoter regions from RefSeq annotations and creates 
an E-P interaction index by labeling each interaction endpoint as either 
Promoter (P) or Enhancer (E).

Usage: $0 -i <bedpe_file> -r <refseq_file> -o <output_file> [options]

Required arguments:
  -i, --input     Input BEDPE file with interaction data (from step 3)
  -r, --refseq    RefSeq gene annotation BED file
  -o, --output    Output file for annotated interactions

Optional arguments:
  -p, --promoter  Pre-generated promoter regions file (skip generation)
  --upstream      Distance upstream of TSS for promoters (default: 1000)
  --downstream    Distance downstream of TSS for promoters (default: 1001)
  --no-interval-tree  Use simple lookup instead of IntervalTree
  -k, --keep      Keep temporary files
  -v, --verbose   Enable verbose output
  -h, --help      Show this help message

Examples:
  # Basic usage
  $0 -i interactions.bedpe -r mm10_refseq.bed -o interactions_index.bedpe.gz
  
  # Use pre-generated promoter file
  $0 -i interactions.bedpe -p mm10_promoters1kb.bed -o interactions_index.bedpe.gz
  
  # Custom promoter regions and verbose output
  $0 -i interactions.bedpe -r mm10_refseq.bed -o output.bedpe.gz \\
     --upstream 500 --downstream 2000 -v

Output:
  The output file contains the original 12 columns from the input BEDPE file
  plus 3 additional columns:
  - Column 13: Left endpoint label (gene name or "enhancer")
  - Column 14: Right endpoint label (gene name or "enhancer")  
  - Column 15: Interaction category (PP/PE/EP/EE)

EOF
}

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

# Function to log error and exit
error_exit() {
    log "ERROR: $1"
    cleanup
    exit 1
}

# Function to cleanup temporary files
cleanup() {
    if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" && "$KEEP_TEMP" == "false" ]]; then
        log "Cleaning up temporary files in $TEMP_DIR"
        rm -rf "$TEMP_DIR"
    fi
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Function to validate input files
validate_inputs() {
    if [[ ! -f "$BEDPE_FILE" ]]; then
        error_exit "BEDPE file not found: $BEDPE_FILE"
    fi
    
    if [[ -n "$REFSEQ_FILE" && ! -f "$REFSEQ_FILE" ]]; then
        error_exit "RefSeq file not found: $REFSEQ_FILE"
    fi
    
    if [[ -n "$PROMOTER_FILE" && ! -f "$PROMOTER_FILE" ]]; then
        error_exit "Promoter file not found: $PROMOTER_FILE"
    fi
    
    if [[ -z "$PROMOTER_FILE" && -z "$REFSEQ_FILE" ]]; then
        error_exit "Either --refseq or --promoter must be provided"
    fi
    
    # Validate BEDPE file format
    if ! head -1 "$BEDPE_FILE" | awk '{if(NF<12) exit 1}'; then
        error_exit "BEDPE file should have at least 12 columns"
    fi
}

# Function to generate promoter regions
generate_promoters() {
    local refseq_file="$1"
    local promoter_file="$2"
    local upstream="$3"
    local downstream="$4"
    
    log "Generating promoter regions from RefSeq annotations..."
    log "Input: $refseq_file"
    log "Output: $promoter_file" 
    log "Region: TSS -$upstream to +$downstream"
    
    local verbose_flag=""
    if [[ "$VERBOSE" == "true" ]]; then
        verbose_flag="-v"
    fi
    
    python3 "$STEP4_DIR/generate_promoters.py" \
        -i "$refseq_file" \
        -o "$promoter_file" \
        --upstream "$upstream" \
        --downstream "$downstream" \
        $verbose_flag \
    || error_exit "Failed to generate promoter regions"
    
    if [[ ! -f "$promoter_file" ]]; then
        error_exit "Promoter file was not created: $promoter_file"
    fi
    
    local promoter_count=$(wc -l < "$promoter_file")
    log "Generated $promoter_count promoter regions"
}

# Function to annotate E-P interactions
annotate_interactions() {
    local bedpe_file="$1"
    local promoter_file="$2"
    local output_file="$3"
    
    log "Annotating E-P interactions..."
    log "BEDPE file: $bedpe_file"
    log "Promoter file: $promoter_file"
    log "Output file: $output_file"
    
    local verbose_flag=""
    local interval_tree_flag=""
    
    if [[ "$VERBOSE" == "true" ]]; then
        verbose_flag="-v"
    fi
    
    if [[ "$USE_INTERVAL_TREE" == "false" ]]; then
        interval_tree_flag="--no-interval-tree"
    fi
    
    python3 "$STEP4_DIR/annotate_ep.py" \
        --bedpe "$bedpe_file" \
        --prom "$promoter_file" \
        -o "$output_file" \
        $verbose_flag \
        $interval_tree_flag \
    || error_exit "Failed to annotate interactions"
    
    if [[ ! -f "$output_file" ]]; then
        error_exit "Output file was not created: $output_file"
    fi
    
    log "E-P annotation completed successfully"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input)
            BEDPE_FILE="$2"
            shift 2
            ;;
        -r|--refseq)
            REFSEQ_FILE="$2"
            shift 2
            ;;
        -p|--promoter)
            PROMOTER_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --upstream)
            UPSTREAM="$2"
            shift 2
            ;;
        --downstream)
            DOWNSTREAM="$2"
            shift 2
            ;;
        --no-interval-tree)
            USE_INTERVAL_TREE=false
            shift
            ;;
        -k|--keep)
            KEEP_TEMP=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            error_exit "Unknown option: $1"
            ;;
    esac
done

# Validate required arguments
if [[ -z "$BEDPE_FILE" ]]; then
    error_exit "Input BEDPE file (-i/--input) is required"
fi

if [[ -z "$OUTPUT_FILE" ]]; then
    error_exit "Output file (-o/--output) is required"
fi

# Validate inputs
validate_inputs

# Create temporary directory
TEMP_DIR=$(mktemp -d)
log "Using temporary directory: $TEMP_DIR"

# Determine promoter file to use
FINAL_PROMOTER_FILE=""
if [[ -n "$PROMOTER_FILE" ]]; then
    # Use provided promoter file
    FINAL_PROMOTER_FILE="$PROMOTER_FILE"
    log "Using provided promoter file: $FINAL_PROMOTER_FILE"
else
    # Generate promoter file from RefSeq
    FINAL_PROMOTER_FILE="$TEMP_DIR/promoters.bed"
    generate_promoters "$REFSEQ_FILE" "$FINAL_PROMOTER_FILE" "$UPSTREAM" "$DOWNSTREAM"
fi

# Annotate interactions
annotate_interactions "$BEDPE_FILE" "$FINAL_PROMOTER_FILE" "$OUTPUT_FILE"

# Final validation
if [[ -f "$OUTPUT_FILE" ]]; then
    output_size=$(du -h "$OUTPUT_FILE" | cut -f1)
    line_count=$(if [[ "$OUTPUT_FILE" =~ \.gz$ ]]; then gunzip -c "$OUTPUT_FILE" | wc -l; else wc -l < "$OUTPUT_FILE"; fi)
    log "✅ Successfully created index: $OUTPUT_FILE"
    log "   File size: $output_size"
    log "   Interactions: $line_count"
else
    error_exit "Output file was not created"
fi

log "Step 4 completed successfully!" 
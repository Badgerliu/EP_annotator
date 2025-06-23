#!/usr/bin/env bash
set -euo pipefail

# ===================================================================
# Associate HiCUT Interactions with H3K27Ac CUT&Tag Peaks
# ===================================================================
# This script finds the closest H3K27Ac peak for each endpoint of 
# chromatin interactions and calculates distances.
#
# Based on the original annotate_hicut_w_cuttag.sh script
# ===================================================================

# Default parameters
DISTANCE_THRESHOLD=""
VERBOSE=false
KEEP_TEMP=false
TEMP_DIR=""

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS] -i <interaction_file> -p <peak_file> -o <output_file>

Associate HiCUT chromatin interactions with H3K27Ac CUT&Tag peaks.

OPTIONS:
    -i, --interaction FILE    Input HiCUT interaction file (4-column BEDPE format)
    -p, --peaks FILE         Input H3K27Ac peak file (3-column BED format)  
    -o, --output FILE        Output file path
    -d, --distance INT       Maximum distance threshold for filtering (optional)
    -v, --verbose            Enable verbose output
    -k, --keep-temp          Keep temporary files for debugging
    -h, --help              Show this help message

EXAMPLES:
    # Basic association
    $0 -i interactions.bedpe -p peaks.bed -o output.bedpe
    
    # With distance filtering (2kb threshold)
    $0 -i interactions.bedpe -p peaks.bed -o output.bedpe -d 2000
    
    # Verbose mode
    $0 -i interactions.bedpe -p peaks.bed -o output.bedpe -v

INPUT FORMATS:
    Interaction file: 4-column BEDPE format (chrA posA chrB posB)
    Peak file: 3-column BED format (chr start end)

OUTPUT FORMAT:
    12-column format: chrA posA chrB posB l_chr l_start l_end l_dist r_chr r_start r_end r_dist
    
    Where:
    - l_chr, l_start, l_end, l_dist: closest peak info for left endpoint
    - r_chr, r_start, r_end, r_dist: closest peak info for right endpoint

DEPENDENCIES:
    - bedtools
    - awk
    - sort
    - cut
    - paste

EOF
}

# Function for logging
log() {
    if [[ "$VERBOSE" == true ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
    fi
}

# Function to log errors
error() {
    echo "[ERROR] $*" >&2
    exit 1
}

# Function to check dependencies
check_dependencies() {
    local missing=()
    
    for tool in bedtools awk sort cut paste; do
        if ! command -v "$tool" &> /dev/null; then
            missing+=("$tool")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        error "Missing required dependencies: ${missing[*]}"
    fi
    
    # Check bedtools version
    if ! bedtools --version &> /dev/null; then
        error "bedtools is not working properly"
    fi
}

# Function to validate input files
validate_files() {
    local interaction_file=$1
    local peak_file=$2
    
    # Check if files exist
    [[ -f "$interaction_file" ]] || error "Interaction file not found: $interaction_file"
    [[ -f "$peak_file" ]] || error "Peak file not found: $peak_file"
    
    # Check if files are readable
    [[ -r "$interaction_file" ]] || error "Cannot read interaction file: $interaction_file"
    [[ -r "$peak_file" ]] || error "Cannot read peak file: $peak_file"
    
    # Validate interaction file format (4 columns)
    log "Validating interaction file format..."
    local line_count=0
    while IFS= read -r line && [[ $line_count -lt 5 ]]; do
        if [[ -n "$line" ]]; then
            local cols
            IFS=$'\t' read -ra cols <<< "$line"
            if [[ ${#cols[@]} -lt 4 ]]; then
                error "Interaction file should have at least 4 columns, found ${#cols[@]} in line $((line_count+1))"
            fi
            # Check if coordinates are numeric
            if ! [[ "${cols[1]}" =~ ^[0-9]+$ ]] || ! [[ "${cols[3]}" =~ ^[0-9]+$ ]]; then
                error "Invalid coordinates in interaction file line $((line_count+1))"
            fi
        fi
        ((line_count++))
    done < "$interaction_file"
    
    # Validate peak file format (3 columns)
    log "Validating peak file format..."
    line_count=0
    while IFS= read -r line && [[ $line_count -lt 5 ]]; do
        if [[ -n "$line" ]]; then
            local cols
            IFS=$'\t' read -ra cols <<< "$line"
            if [[ ${#cols[@]} -lt 3 ]]; then
                error "Peak file should have at least 3 columns, found ${#cols[@]} in line $((line_count+1))"
            fi
            # Check if coordinates are numeric  
            if ! [[ "${cols[1]}" =~ ^[0-9]+$ ]] || ! [[ "${cols[2]}" =~ ^[0-9]+$ ]]; then
                error "Invalid coordinates in peak file line $((line_count+1))"
            fi
        fi
        ((line_count++))
    done < "$peak_file"
}

# Function to associate interactions with peaks
associate_peaks() {
    local interaction_file=$1
    local peak_file=$2
    local output_file=$3
    local temp_dir=$4
    
    log "Starting peak association..."
    log "Interaction file: $interaction_file"
    log "Peak file: $peak_file"
    log "Output file: $output_file"
    
    # Create temporary files
    local left_temp="$temp_dir/_L.tmp"
    local right_temp="$temp_dir/_R.tmp"
    
    # Step 1: Process left endpoints and find closest peaks
    log "Processing left endpoints..."
    awk 'BEGIN{OFS="\t"}{print $1,$2,$2+1,NR}' "$interaction_file" | \
    bedtools sort -i - | \
    bedtools closest -a - -b <(bedtools sort -i "$peak_file") -d -t first | \
    awk 'BEGIN{OFS="\t"}{print $4,$1,$6,$7,$8}' | \
    sort -k1,1n > "$left_temp"
    
    if [[ $? -ne 0 ]]; then
        error "Failed to process left endpoints"
    fi
    
    # Step 2: Process right endpoints and find closest peaks
    log "Processing right endpoints..."
    awk 'BEGIN{OFS="\t"}{print $3,$4,$4+1,NR}' "$interaction_file" | \
    bedtools sort -i - | \
    bedtools closest -a - -b <(bedtools sort -i "$peak_file") -d -t first | \
    awk 'BEGIN{OFS="\t"}{print $4,$1,$6,$7,$8}' | \
    sort -k1,1n > "$right_temp"
    
    if [[ $? -ne 0 ]]; then
        error "Failed to process right endpoints"  
    fi
    
    # Step 3: Combine results using paste
    log "Combining results..."
    paste <(cat "$interaction_file") \
          <(cut -f2- "$left_temp") \
          <(cut -f2- "$right_temp") \
    > "$output_file"
    
    if [[ $? -ne 0 ]]; then
        error "Failed to combine results"
    fi
    
    # Count results
    local line_count
    line_count=$(wc -l < "$output_file")
    echo "✅ Associated $line_count interactions with peaks"
    log "Association completed successfully"
}

# Function to filter by distance
filter_by_distance() {
    local input_file=$1
    local output_file=$2  
    local max_distance=$3
    
    log "Filtering by distance threshold: $max_distance"
    
    # Filter interactions where both endpoints are within distance threshold
    awk -v max_dist="$max_distance" 'BEGIN{OFS="\t"} 
        {
            if (NF >= 12 && $8 < max_dist && $12 < max_dist) {
                print $0
            }
        }' "$input_file" > "$output_file"
    
    if [[ $? -ne 0 ]]; then
        error "Failed to filter by distance"
    fi
    
    local total_count filtered_count
    total_count=$(wc -l < "$input_file")
    filtered_count=$(wc -l < "$output_file")
    
    local percentage
    if [[ $total_count -gt 0 ]]; then
        percentage=$(awk "BEGIN {printf \"%.1f\", $filtered_count/$total_count*100}")
    else
        percentage="0.0"
    fi
    
    echo "✅ Filtered $filtered_count / $total_count interactions ($percentage%)"
    log "Distance filtering completed"
}

# Main function
main() {
    local interaction_file=""
    local peak_file=""
    local output_file=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--interaction)
                interaction_file="$2"
                shift 2
                ;;
            -p|--peaks)
                peak_file="$2"
                shift 2
                ;;
            -o|--output)
                output_file="$2"
                shift 2
                ;;
            -d|--distance)
                DISTANCE_THRESHOLD="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -k|--keep-temp)
                KEEP_TEMP=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1. Use -h for help."
                ;;
        esac
    done
    
    # Check required arguments
    [[ -n "$interaction_file" ]] || error "Interaction file is required (-i)"
    [[ -n "$peak_file" ]] || error "Peak file is required (-p)"
    [[ -n "$output_file" ]] || error "Output file is required (-o)"
    
    # Validate distance threshold if provided
    if [[ -n "$DISTANCE_THRESHOLD" ]]; then
        if ! [[ "$DISTANCE_THRESHOLD" =~ ^[0-9]+$ ]]; then
            error "Distance threshold must be a positive integer"
        fi
        log "Distance threshold: $DISTANCE_THRESHOLD"
    fi
    
    log "Starting association process..."
    
    # Check dependencies
    check_dependencies
    
    # Validate input files
    validate_files "$interaction_file" "$peak_file"
    
    # Create output directory if needed
    local output_dir
    output_dir=$(dirname "$output_file")
    if [[ "$output_dir" != "." ]]; then
        mkdir -p "$output_dir"
    fi
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    
    # Cleanup function
    cleanup() {
        if [[ "$KEEP_TEMP" != true ]]; then
            log "Cleaning up temporary files..."
            rm -rf "$TEMP_DIR"
        else
            log "Keeping temporary files in: $TEMP_DIR"
        fi
    }
    trap cleanup EXIT
    
    # Associate interactions with peaks
    if [[ -n "$DISTANCE_THRESHOLD" ]]; then
        # Use temporary file for intermediate result
        local temp_output="$TEMP_DIR/associated.bedpe"
        associate_peaks "$interaction_file" "$peak_file" "$temp_output" "$TEMP_DIR"
        filter_by_distance "$temp_output" "$output_file" "$DISTANCE_THRESHOLD"
    else
        associate_peaks "$interaction_file" "$peak_file" "$output_file" "$TEMP_DIR"
    fi
    
    echo "✅ Peak association completed: $output_file"
    log "Process finished successfully"
}

# Run main function with all arguments
main "$@" 
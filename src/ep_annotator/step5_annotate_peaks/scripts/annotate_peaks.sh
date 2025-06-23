#!/bin/bash
# annotate_peaks.sh
# Shell script for annotating ChIP-seq peaks with E-P interaction information
# Based on the command_log.txt workflow

set -euo pipefail

# Default parameters
PEAKS=""
BEDPE=""
PROMOTERS=""
OUTPUT=""
EXTEND=1000
VERBOSE=false

# Function to display usage
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Annotate ChIP-seq peaks with enhancer-promoter interaction information.

OPTIONS:
    --peaks PEAKS_FILE     Path to query peaks BED file (required)
    --bedpe BEDPE_FILE     Path to labeled E-P interaction BEDPE file (required)
    --prom PROM_FILE       Path to promoter regions BED file (required)
    -o, --output OUTPUT    Output TSV file (auto-generated if not provided)
    --extend BP            Base pairs to extend endpoints for intersection (default: 1000)
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

EXAMPLE:
    $(basename "$0") --peaks ARID3A_peak.bed \\
                     --bedpe E145_E_HiCUT_with_peaks_near2k.promLabel.bedpe.gz \\
                     --prom mm10_promoters1kb.bed \\
                     -o ARID3A_peak_EP_annotation_detail.tsv

EOF
}

# Function for logging
log() {
    if [[ "$VERBOSE" == true ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
    fi
}

info() {
    echo "[INFO] $1" >&2
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --peaks)
            PEAKS="$2"
            shift 2
            ;;
        --bedpe)
            BEDPE="$2"
            shift 2
            ;;
        --prom)
            PROMOTERS="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        --extend)
            EXTEND="$2"
            shift 2
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
            error "Unknown option: $1"
            ;;
    esac
done

# Validate required parameters
if [[ -z "$PEAKS" ]]; then
    error "Missing required parameter: --peaks"
fi

if [[ -z "$BEDPE" ]]; then
    error "Missing required parameter: --bedpe"
fi

if [[ -z "$PROMOTERS" ]]; then
    error "Missing required parameter: --prom"
fi

# Auto-generate output filename if not provided
if [[ -z "$OUTPUT" ]]; then
    PEAKS_BASENAME=$(basename "$PEAKS" .bed)
    OUTPUT="${PEAKS_BASENAME}_EP_annotation_detail.tsv"
fi

# Validate input files
for file in "$PEAKS" "$BEDPE" "$PROMOTERS"; do
    if [[ ! -f "$file" ]]; then
        error "Input file not found: $file"
    fi
    if [[ ! -r "$file" ]]; then
        error "Cannot read input file: $file"
    fi
done

info "Starting peak annotation..."
log "Peaks file: $PEAKS"
log "BEDPE file: $BEDPE"
log "Promoter file: $PROMOTERS"
log "Output file: $OUTPUT"
log "Extension: ±${EXTEND} bp"

# Check for required tools
for tool in bedtools awk sort; do
    if ! command -v "$tool" &> /dev/null; then
        error "Required tool not found: $tool"
    fi
done

# Create temporary directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

log "Created temporary directory: $TEMP_DIR"

# Step 1: Process peaks file (ensure 4 columns)
info "Processing peaks file..."
PEAKS_PROCESSED="$TEMP_DIR/peaks_processed.bed"

awk 'BEGIN{OFS="\t"} {
    if (NF >= 4) {
        print $1, $2, $3, $4
    } else if (NF >= 3) {
        print $1, $2, $3, "peak_" NR
    }
}' "$PEAKS" > "$PEAKS_PROCESSED"

PEAK_COUNT=$(wc -l < "$PEAKS_PROCESSED")
log "Processed $PEAK_COUNT peaks"

# Step 2: Extract and extend endpoints from BEDPE
info "Extracting E-P interaction endpoints..."
ENDPOINTS="$TEMP_DIR/endpoints.bed"

# Function to handle both gzipped and regular files
if [[ "$BEDPE" == *.gz ]]; then
    CAT_CMD="gzip -dc"
else
    CAT_CMD="cat"
fi

# Extract endpoints with extended coordinates
$CAT_CMD "$BEDPE" | awk -v extend="$EXTEND" 'BEGIN{OFS="\t"} {
    if (NF >= 15) {
        # Left endpoint (H3K27Ac peak)
        l_chr = $5; l_start = $6; l_end = $7
        l_label = $13; r_label = $14; category = $15
        r_chr = $9; r_start = $10; r_end = $11
        
        # Extend coordinates
        l_ext_start = (l_start - extend > 0) ? l_start - extend : 0
        l_ext_end = l_end + extend
        r_ext_start = (r_start - extend > 0) ? r_start - extend : 0
        r_ext_end = r_end + extend
        
        # Output left endpoint
        print l_chr, l_ext_start, l_ext_end, "L", l_label, r_label, category, r_chr, r_start, r_end
        
        # Output right endpoint  
        print r_chr, r_ext_start, r_ext_end, "R", r_label, l_label, category, l_chr, l_start, l_end
    }
}' > "$ENDPOINTS"

ENDPOINT_COUNT=$(wc -l < "$ENDPOINTS")
log "Generated $ENDPOINT_COUNT endpoint entries"

# Step 3: Create promoter overlap mapping
info "Creating promoter overlap mapping..."
PROMOTER_OVERLAP="$TEMP_DIR/promoter_overlap.txt"

bedtools intersect -a "$PEAKS_PROCESSED" -b "$PROMOTERS" -wa -wb | \
awk 'BEGIN{OFS="\t"} {print $4, $8}' | \
sort -k1,1 | \
awk '{
    if ($1 == prev_peak) {
        genes = genes ";" $2
    } else {
        if (prev_peak != "") print prev_peak, genes
        prev_peak = $1
        genes = $2
    }
} END {
    if (prev_peak != "") print prev_peak, genes
}' > "$PROMOTER_OVERLAP"

log "Created promoter overlap mapping"

# Step 4: Find intersections between peaks and endpoints
info "Finding peak-endpoint intersections..."
INTERSECTIONS="$TEMP_DIR/intersections.txt"

bedtools intersect -a "$PEAKS_PROCESSED" -b "$ENDPOINTS" -wa -wb > "$INTERSECTIONS"

INTERSECTION_COUNT=$(wc -l < "$INTERSECTIONS")
log "Found $INTERSECTION_COUNT peak-endpoint intersections"

# Step 5: Process results and create final annotation
info "Processing annotation results..."

# Create header for output file
echo -e "chr\tstart\tend\tname\tis_promoter\tis_enhancer\toverlapping_promoter_genes\tenhancer_target_genes\tregulating_enhancers\tenhancer_partners\tpromoter_partners" > "$OUTPUT"

# Process each peak
awk 'BEGIN{OFS="\t"}
# Read promoter overlap mapping
FILENAME == ARGV[1] {
    prom_genes[$1] = $2
    next
}

# Read intersection results
FILENAME == ARGV[2] {
    peak_name = $4
    my_label = $8
    partner_label = $9
    category = $10
    partner_loc = $11 ":" $12 "-" $13
    
    # Classify interactions
    if (category == "EP" && my_label == "enhancer" && partner_label != "enhancer") {
        enhancer_targets[peak_name] = enhancer_targets[peak_name] ? enhancer_targets[peak_name] ";" partner_label : partner_label
    }
    else if (category == "PE" && my_label != "enhancer" && partner_label == "enhancer") {
        regulating_enh[peak_name] = regulating_enh[peak_name] ? regulating_enh[peak_name] ";" partner_loc : partner_loc
    }
    else if (category == "EE" && my_label == "enhancer" && partner_label == "enhancer") {
        enh_partners[peak_name] = enh_partners[peak_name] ? enh_partners[peak_name] ";" partner_loc : partner_loc
    }
    else if (category == "PP" && my_label != "enhancer" && partner_label != "enhancer") {
        prom_partners[peak_name] = prom_partners[peak_name] ? prom_partners[peak_name] ";" partner_label : partner_label
    }
    next
}

# Read peaks file and generate output
FILENAME == ARGV[3] {
    chr = $1; start = $2; end = $3; name = $4
    
    # Determine if promoter
    is_promoter = (name in prom_genes) ? "True" : "False"
    
    # Determine if enhancer (not promoter and has enhancer interactions)
    is_enhancer = (is_promoter == "False" && ((name in enhancer_targets) || (name in enh_partners))) ? "True" : "False"
    
    # Get gene list
    genes = (name in prom_genes) ? prom_genes[name] : ""
    
    # Get interaction lists
    enh_targ = (name in enhancer_targets) ? enhancer_targets[name] : ""
    reg_enh = (name in regulating_enh) ? regulating_enh[name] : ""
    enh_part = (name in enh_partners) ? enh_partners[name] : ""
    prom_part = (name in prom_partners) ? prom_partners[name] : ""
    
    print chr, start, end, name, is_promoter, is_enhancer, genes, enh_targ, reg_enh, enh_part, prom_part
}' "$PROMOTER_OVERLAP" "$INTERSECTIONS" "$PEAKS_PROCESSED" >> "$OUTPUT"

# Generate summary statistics
info "Generating summary statistics..."
TOTAL_PEAKS=$(tail -n +2 "$OUTPUT" | wc -l)
PROMOTER_PEAKS=$(tail -n +2 "$OUTPUT" | awk -F'\t' '$5=="True"' | wc -l)
ENHANCER_PEAKS=$(tail -n +2 "$OUTPUT" | awk -F'\t' '$6=="True"' | wc -l)
NEITHER_PEAKS=$((TOTAL_PEAKS - PROMOTER_PEAKS - ENHANCER_PEAKS))

info "=== Annotation Summary ==="
info "Total peaks: $TOTAL_PEAKS"
info "Promoter peaks: $PROMOTER_PEAKS ($(echo "scale=1; $PROMOTER_PEAKS * 100 / $TOTAL_PEAKS" | bc -l)%)"
info "Enhancer peaks: $ENHANCER_PEAKS ($(echo "scale=1; $ENHANCER_PEAKS * 100 / $TOTAL_PEAKS" | bc -l)%)"
info "Neither: $NEITHER_PEAKS ($(echo "scale=1; $NEITHER_PEAKS * 100 / $TOTAL_PEAKS" | bc -l)%)"

info "✅ Detailed annotation complete → $OUTPUT"

# Cleanup is handled by trap
exit 0 
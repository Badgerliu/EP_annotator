#!/bin/bash

# analyze_results.sh
# Shell script for Step 6: Analyze Results
# 
# This script provides a convenient interface for running comprehensive
# analysis and visualization of EP interaction results.
#
# Based on the command_log.txt workflow for step 6

set -euo pipefail

# Script information
SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STEP6_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
INPUT_FILE=""
OUTPUT_PREFIX=""
ANNOTATION_MODE=false
CREATE_PLOTS=true
VERBOSE=false
PYTHON_CMD="python3"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Function to show usage
usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS] INPUT_FILE

Step 6: Comprehensive Analysis and Visualization of EP Interaction Results

This script performs comprehensive analysis including:
  • Statistical analysis of interaction types, distances, and chromosomes
  • Generation of detailed reports
  • Creation of publication-ready visualizations
  • Pie chart with specific colors (EP: #7DC69B, PE: #9BD7F3, EE: #D5EAD9, PP: #D8EEFB)

ARGUMENTS:
    INPUT_FILE              Path to labeled BEDPE file (.bedpe or .bedpe.gz)
                           OR annotation TSV file (with --annotation)

OPTIONS:
    -o, --output PREFIX     Output prefix for generated files
                           (default: auto-generated from input filename)
    -a, --annotation        Treat input as annotation TSV file from step5
    -n, --no-plots          Skip creating visualization plots
    -p, --python CMD        Python command to use (default: python3)
    -v, --verbose           Enable verbose logging
    -h, --help              Show this help message

EXAMPLES:
    # Analyze BEDPE file with interaction labels
    $SCRIPT_NAME E145_E_HiCUT_with_peaks_near2k.promLabel.bedpe.gz -o results

    # Analyze step5 annotation output
    $SCRIPT_NAME --annotation ARID3A_peak_EP_annotation_detail.tsv -o ARID3A_analysis

    # Create only statistical report (no plots)
    $SCRIPT_NAME data.bedpe.gz --no-plots -o analysis

OUTPUT FILES:
    PREFIX_comprehensive_statistics.txt     - Detailed statistical report
    PREFIX_interaction_pie.png              - Interaction type pie chart
    PREFIX_distance_analysis.png            - Distance distribution plots
    PREFIX_chromosome_distribution.png      - Chromosome distribution plot
    PREFIX_comprehensive_summary.png        - Multi-panel summary plot

REQUIREMENTS:
    • Python 3.6+
    • pandas, numpy, matplotlib, seaborn, scipy
    • Input BEDPE file with interaction labels OR step5 annotation TSV

EOF
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        print_error "Python command '$PYTHON_CMD' not found"
        print_error "Please install Python 3.6+ or specify correct command with -p"
        exit 1
    fi
    
    # Check Python packages
    local required_packages=("pandas" "numpy" "matplotlib" "seaborn" "scipy")
    local missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if ! $PYTHON_CMD -c "import $package" &> /dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        print_error "Missing required Python packages: ${missing_packages[*]}"
        print_error "Please install them using: pip install ${missing_packages[*]}"
        exit 1
    fi
    
    print_status "All dependencies satisfied"
}

# Function to validate input file
validate_input() {
    if [ -z "$INPUT_FILE" ]; then
        print_error "Input file is required"
        usage
        exit 1
    fi
    
    if [ ! -f "$INPUT_FILE" ]; then
        print_error "Input file not found: $INPUT_FILE"
        exit 1
    fi
    
    # Check file format
    if [ "$ANNOTATION_MODE" = true ]; then
        # For annotation mode, expect TSV file
        if [[ ! "$INPUT_FILE" =~ \.(tsv|txt)$ ]]; then
            print_warning "Expected TSV file for annotation mode, got: $INPUT_FILE"
        fi
    else
        # For BEDPE mode, expect .bedpe or .bedpe.gz
        if [[ ! "$INPUT_FILE" =~ \.(bedpe|bedpe\.gz)$ ]]; then
            print_warning "Expected BEDPE file (.bedpe or .bedpe.gz), got: $INPUT_FILE"
        fi
    fi
    
    print_status "Input file validated: $INPUT_FILE"
}

# Function to generate output prefix
generate_output_prefix() {
    if [ -z "$OUTPUT_PREFIX" ]; then
        local basename=$(basename "$INPUT_FILE")
        local stem="${basename%.*}"
        
        # Remove additional extensions
        if [[ "$stem" =~ \.bedpe$ ]]; then
            stem="${stem%.bedpe}"
        fi
        if [[ "$stem" =~ \.promLabel$ ]]; then
            stem="${stem%.promLabel}"
        fi
        
        OUTPUT_PREFIX="${stem}_step6_analysis"
        print_status "Auto-generated output prefix: $OUTPUT_PREFIX"
    fi
}

# Function to run the analysis
run_analysis() {
    print_header "="*60
    print_header "EP_annotator - Step 6: Comprehensive Results Analysis"
    print_header "="*60
    
    print_status "Input file: $INPUT_FILE"
    print_status "Output prefix: $OUTPUT_PREFIX"
    print_status "Annotation mode: $ANNOTATION_MODE"
    print_status "Create plots: $CREATE_PLOTS"
    print_status "Verbose: $VERBOSE"
    
    # Build Python command
    local python_script="$STEP6_DIR/analyze_results.py"
    local cmd_args=()
    
    if [ "$ANNOTATION_MODE" = true ]; then
        cmd_args+=("--annotation" "$INPUT_FILE")
    else
        cmd_args+=("$INPUT_FILE")
    fi
    
    cmd_args+=("-o" "$OUTPUT_PREFIX")
    
    if [ "$CREATE_PLOTS" = false ]; then
        cmd_args+=("--no-plots")
    fi
    
    if [ "$VERBOSE" = true ]; then
        cmd_args+=("--verbose")
    fi
    
    # Run the analysis
    print_status "Starting analysis..."
    print_status "Command: $PYTHON_CMD $python_script ${cmd_args[*]}"
    
    if $PYTHON_CMD "$python_script" "${cmd_args[@]}"; then
        print_status "Analysis completed successfully!"
        
        # List output files
        print_header "Generated files:"
        local output_files=(
            "${OUTPUT_PREFIX}_comprehensive_statistics.txt"
            "${OUTPUT_PREFIX}_interaction_pie.png"
            "${OUTPUT_PREFIX}_distance_analysis.png"
            "${OUTPUT_PREFIX}_chromosome_distribution.png"
            "${OUTPUT_PREFIX}_comprehensive_summary.png"
        )
        
        for file in "${output_files[@]}"; do
            if [ -f "$file" ]; then
                local size=$(du -h "$file" | cut -f1)
                print_status "  ✓ $file ($size)"
            fi
        done
        
        return 0
    else
        print_error "Analysis failed!"
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -o|--output)
            OUTPUT_PREFIX="$2"
            shift 2
            ;;
        -a|--annotation)
            ANNOTATION_MODE=true
            shift
            ;;
        -n|--no-plots)
            CREATE_PLOTS=false
            shift
            ;;
        -p|--python)
            PYTHON_CMD="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -*)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            if [ -z "$INPUT_FILE" ]; then
                INPUT_FILE="$1"
            else
                print_error "Multiple input files specified"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Main execution
main() {
    print_header "EP_annotator Step 6: Analyze Results"
    
    # Validate inputs
    validate_input
    
    # Generate output prefix if not provided
    generate_output_prefix
    
    # Check dependencies
    check_dependencies
    
    # Run analysis
    if run_analysis; then
        print_header "Step 6 completed successfully!"
        exit 0
    else
        print_error "Step 6 failed!"
        exit 1
    fi
}

# Run main function
main 
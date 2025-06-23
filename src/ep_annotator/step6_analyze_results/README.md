# Step 6: Analyze Results

This module performs comprehensive statistical analysis and visualization of enhancer-promoter (EP) interaction results. It provides advanced analytics and publication-ready visualizations for the complete EP_annotator pipeline.

## Overview

Step 6 builds upon the outputs from previous steps to provide:

- **Statistical Analysis**: Comprehensive statistics on interaction types, distances, and chromosomal distributions
- **Advanced Visualizations**: Publication-ready plots with specific color schemes as defined in the original workflow
- **Quality Assessment**: Data quality metrics and completeness analysis
- **Reporting**: Detailed text reports with all analysis results

## Features

### 📊 Statistical Analysis
- **Interaction Type Analysis**: Count and percentage of EP, PE, EE, PP interactions
- **Distance Distribution**: Analysis of genomic and peak distances
- **Chromosome Distribution**: Per-chromosome interaction counts and patterns
- **Quality Metrics**: Data completeness and validation statistics

### 🎨 Visualizations
- **Interaction Type Pie Chart**: With specific colors from command_log.txt
  - EP (Enhancer → Promoter): `#7DC69B` (green)
  - PE (Promoter ← Enhancer): `#9BD7F3` (blue)
  - EE (Enhancer → Enhancer): `#D5EAD9` (light green)
  - PP (Promoter → Promoter): `#D8EEFB` (light blue)
- **Distance Distribution Plots**: Multi-panel analysis of interaction distances
- **Chromosome Distribution**: Bar plots of interactions per chromosome
- **Comprehensive Summary**: Multi-panel overview of all analyses

### 📋 Reporting
- **Comprehensive Statistics Report**: Detailed text report with all metrics
- **File Listings**: Automatic cataloging of generated output files
- **Analysis Summaries**: Key findings and statistics logging

## Input Files

### Primary Input: Labeled BEDPE File
```
# Expected format (15+ columns):
chr1  start1  end1  chr2  start2  end2  peak1_chr  peak1_dist  peak2_chr  peak2_dist  peak1_closest  peak2_closest  label1  label2  interaction_type
```

### Alternative Input: Step5 Annotation TSV
```
# Detailed annotation file from step5_annotate_peaks
# Contains peak-level annotations with interaction information
```

## Usage

### Command Line Interface

#### Basic Usage
```bash
# Analyze BEDPE file with interaction labels
python analyze_results.py E145_E_HiCUT_with_peaks_near2k.promLabel.bedpe.gz -o results

# Analyze step5 annotation output  
python analyze_results.py --annotation ARID3A_peak_EP_annotation_detail.tsv -o ARID3A_analysis

# Create only statistical report (no plots)
python analyze_results.py data.bedpe.gz --no-plots -o analysis
```

#### Shell Script Interface
```bash
# Using the convenient shell script
./scripts/analyze_results.sh E145_E_HiCUT_with_peaks_near2k.promLabel.bedpe.gz -o results

# With annotation mode
./scripts/analyze_results.sh --annotation ARID3A_peak_EP_annotation_detail.tsv -o ARID3A_analysis

# Skip plots for faster analysis
./scripts/analyze_results.sh data.bedpe.gz --no-plots -o analysis
```

### Python API

#### Direct Function Calls
```python
from ep_annotator.step6_analyze_results import analyze_results

# Analyze BEDPE file
output_files = analyze_results(
    bedpe_file="E145_E_HiCUT_with_peaks_near2k.promLabel.bedpe.gz",
    output_prefix="results",
    create_plots=True,
    verbose=True
)

# Access generated files
print(f"Statistics report: {output_files['statistics_report']}")
print(f"Pie chart: {output_files['pie_chart']}")
```

#### Individual Analysis Components
```python
from ep_annotator.step6_analyze_results import (
    load_bedpe_data,
    calculate_interaction_statistics,
    create_interaction_pie_chart
)

# Load data
df = load_bedpe_data("data.bedpe.gz", logger)

# Calculate statistics
stats = calculate_interaction_statistics(df, logger)

# Create specific visualizations
create_interaction_pie_chart(stats['interaction_types'], "pie.png", logger)
```

## Output Files

### Statistical Reports
- `PREFIX_comprehensive_statistics.txt`: Detailed statistical analysis report

### Visualization Plots
- `PREFIX_interaction_pie.png`: Interaction type pie chart with specified colors
- `PREFIX_distance_analysis.png`: Multi-panel distance distribution analysis
- `PREFIX_chromosome_distribution.png`: Chromosome interaction distribution
- `PREFIX_comprehensive_summary.png`: Multi-panel summary of all analyses

## Implementation Details

### Module Structure
```
step6_analyze_results/
├── __init__.py                 # Module initialization and exports
├── analyze_results.py          # Main analysis coordination
├── statistical_analysis.py    # Statistical computation functions
├── visualization.py           # Plotting and visualization functions
├── scripts/
│   └── analyze_results.sh     # Shell script interface
└── README.md                  # This documentation
```

### Key Functions

#### `analyze_results()`
Main coordination function that:
1. Loads and validates BEDPE data
2. Calculates comprehensive statistics
3. Generates detailed reports
4. Creates all visualizations
5. Returns dictionary of output file paths

#### `calculate_interaction_statistics()`
Comprehensive statistical analysis including:
- Basic interaction counts and unique loci
- Distance distribution analysis (genomic and peak distances)
- Interaction type classification and counting
- Chromosome distribution analysis
- Data quality metrics

#### `create_all_visualizations()`
Creates all publication-ready plots:
- Interaction type pie chart with specified colors
- Distance distribution multi-panel plots
- Chromosome distribution bar plots
- Comprehensive multi-panel summary

## Dependencies

### Required Python Packages
```
pandas>=1.3.0      # Data manipulation and analysis
numpy>=1.20.0      # Numerical computing
matplotlib>=3.3.0  # Basic plotting
seaborn>=0.11.0    # Statistical plotting
scipy>=1.7.0       # Statistical functions
```

### System Requirements
- Python 3.6+
- Memory: Recommended 4GB+ for large datasets
- Storage: ~100MB per analysis (including plots)

## Integration with Pipeline

### Input from Previous Steps
- **Step 4**: Generates labeled BEDPE files with interaction types
- **Step 5**: Provides detailed peak annotations for alternative analysis

### Workflow Position
```
Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6
                                     ↓        ↓
                               BEDPE files  Annotation TSV
                                     ↓        ↓
                                  Step 6 Analysis
                                     ↓
                            Reports + Visualizations
```

## Examples

### Example 1: Full Analysis Pipeline
```bash
# Complete analysis with all visualizations
./scripts/analyze_results.sh \
    E145_E_HiCUT_with_peaks_near2k.promLabel.bedpe.gz \
    -o E145_comprehensive_analysis \
    --verbose
```

### Example 2: Quick Statistics Only
```bash
# Fast analysis without plots
python analyze_results.py \
    data.bedpe.gz \
    --no-plots \
    -o quick_stats
```

### Example 3: Peak-Level Analysis
```bash
# Analyze step5 annotation results
python analyze_results.py \
    --annotation ARID3A_peak_EP_annotation_detail.tsv \
    -o ARID3A_peak_analysis
```

## Troubleshooting

### Common Issues

#### Missing Dependencies
```bash
# Install required packages
pip install pandas numpy matplotlib seaborn scipy
```

#### File Format Issues
- Ensure BEDPE files have at least 15 columns
- Check that interaction labels are in the expected columns
- Verify file is readable (check permissions)

#### Memory Issues
- For large datasets (>1M interactions), consider using `--no-plots`
- Monitor memory usage during analysis
- Consider processing subsets for very large datasets

### Performance Optimization
- Use gzipped input files to save disk space
- Skip plotting for initial data exploration
- Use verbose mode to monitor progress

## Command Log Integration

This implementation directly addresses the requirements from `command_log.txt`:

1. **Pie Chart Visualization**: Implements the exact color scheme specified
   - EP: #7DC69B, PE: #9BD7F3, EE: #D5EAD9, PP: #D8EEFB

2. **Statistical Analysis**: Provides comprehensive interaction type statistics
   - Matches the format: "EP : 50,032", "PE : 50,751", etc.

3. **Classification and Reporting**: Generates detailed analysis reports
   - Follows the workflow: annotation → classification → visualization

4. **Integration**: Works with outputs from previous pipeline steps
   - Accepts both BEDPE files and step5 annotation outputs

## Future Enhancements

- **Functional Enrichment**: Gene ontology analysis for target genes
- **Interactive Plots**: HTML-based interactive visualizations
- **Comparative Analysis**: Multi-sample comparison capabilities
- **Export Formats**: Additional output formats (SVG, PDF, etc.) 
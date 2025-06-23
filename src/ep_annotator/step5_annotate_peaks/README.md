# Step 5: Annotate ChIP-seq Peaks

This step annotates user-provided ChIP-seq peaks with detailed enhancer-promoter (E-P) interaction information using the E-P interaction index generated in step 4.

## Overview

The peak annotation process involves:

1. **Load query peaks**: Read user-provided ChIP-seq peak BED file
2. **Map to promoters**: Identify peaks overlapping with promoter regions  
3. **Parse E-P interactions**: Extract endpoint information from labeled BEDPE file
4. **Find intersections**: Map peaks to E-P interaction endpoints
5. **Classify interactions**: Categorize peaks as promoters, enhancers, or neither
6. **Generate annotations**: Output detailed interaction information for each peak

## Input Files

### Required Inputs
- **Query peaks BED file**: ChIP-seq peaks to annotate (≥3 columns: chr, start, end, [name])
- **Labeled BEDPE file**: E-P interaction index from step 4 (15 columns with promoter/enhancer labels)
- **Promoter regions BED file**: Promoter regions (4 columns: chr, start, end, gene)

### Input Formats

**Query peaks (BED)**:
```
chr1    1000    2000    peak_1
chr1    5000    6000    peak_2
chr2    3000    4000    peak_3
```

**Labeled BEDPE (from step 4)**:
```
chr1    1000    2000    chr2    5000    6000    chr1    1500    1600    400    chr2    5500    5600    300    gene_A    enhancer    EP
```

**Promoter regions**:
```
chr1    1000    3000    Gene1
chr2    5000    7000    Gene2
```

## Output Files

### Main Output
- **Detailed annotation TSV**: Complete annotation results with interaction information

### Analysis Outputs (optional)
- **Classified BED files**: Separate files for promoter, enhancer, and neither peaks
- **Summary report**: Text report with statistics
- **Visualization plots**: Charts showing peak classification and interaction types

## Output Format

The main output is a TSV file with the following columns:

| Column | Description |
|--------|-------------|
| chr | Chromosome |
| start | Peak start coordinate |
| end | Peak end coordinate |
| name | Peak name |
| is_promoter | Whether peak overlaps with promoter regions (True/False) |
| is_enhancer | Whether peak functions as enhancer based on interactions (True/False) |
| overlapping_promoter_genes | Genes whose promoters overlap with this peak (semicolon-separated) |
| enhancer_target_genes | Target genes when this peak acts as enhancer (semicolon-separated) |
| regulating_enhancers | Enhancer locations regulating this promoter peak (semicolon-separated) |
| enhancer_partners | Other enhancers in EE interactions (semicolon-separated) |
| promoter_partners | Other promoters in PP interactions (semicolon-separated) |

## Usage

### Python API

```python
from ep_annotator.step5_annotate_peaks import annotate_peaks_detailed, analyze_annotation_results

# Annotate peaks
output_file = annotate_peaks_detailed(
    peaks_file="query_peaks.bed",
    bedpe_file="ep_interactions.promLabel.bedpe.gz",
    promoter_file="promoters.bed",
    output_file="detailed_annotation.tsv",
    extend_bp=1000,
    verbose=True
)

# Analyze results
analysis_files = analyze_annotation_results(
    annotation_file="detailed_annotation.tsv",
    output_prefix="analysis",
    create_plots=True,
    verbose=True
)
```

### Command Line

**Python script**:
```bash
python -m ep_annotator.step5_annotate_peaks.annotate_peaks_detail \
    --peaks query_peaks.bed \
    --bedpe ep_interactions.promLabel.bedpe.gz \
    --prom promoters.bed \
    -o detailed_annotation.tsv \
    --extend 1000 \
    -v
```

**Shell script**:
```bash
./src/ep_annotator/step5_annotate_peaks/scripts/annotate_peaks.sh \
    --peaks query_peaks.bed \
    --bedpe ep_interactions.promLabel.bedpe.gz \
    --prom promoters.bed \
    -o detailed_annotation.tsv \
    --extend 1000 \
    -v
```

**Analysis**:
```bash
python -m ep_annotator.step5_annotate_peaks.analyze_annotations \
    detailed_annotation.tsv \
    -o analysis \
    -v
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--peaks` | Path to query peaks BED file | Required |
| `--bedpe` | Path to labeled E-P interaction BEDPE file | Required |
| `--prom` | Path to promoter regions BED file | Required |
| `-o, --output` | Output file path | Auto-generated |
| `--extend` | Base pairs to extend endpoints for intersection | 1000 |
| `-v, --verbose` | Enable verbose logging | False |

## Algorithm Details

### Peak Classification Logic

1. **Promoter identification**: Peak overlaps with promoter regions
2. **Enhancer identification**: Peak is involved in EP or EE interactions (and not a promoter)
3. **Neither**: Peak doesn't meet promoter or enhancer criteria

### Interaction Type Processing

- **EP interactions**: Enhancer → Promoter (peak as enhancer targets genes)
- **PE interactions**: Promoter ← Enhancer (peak as promoter regulated by enhancers)  
- **EE interactions**: Enhancer ← → Enhancer (enhancer-enhancer partnerships)
- **PP interactions**: Promoter ← → Promoter (promoter-promoter partnerships)

### Coordinate Extension

E-P interaction endpoints are extended by ±1000 bp (configurable) to account for:
- Peak calling variations
- Chromatin accessibility regions
- Regulatory element boundaries

## Example Workflow

Based on the original command_log.txt:

```bash
# Step 1: Annotate ARID3A peaks
python -m ep_annotator.step5_annotate_peaks.annotate_peaks_detail \
    --peaks ARID3A_peak.bed \
    --bedpe E145_E_HiCUT_with_peaks_near2k.promLabel.bedpe.gz \
    --prom mm10_promoters1kb.bed \
    -o ARID3A_peak_EP_annotation_detail.tsv

# Step 2: Analyze results
python -m ep_annotator.step5_annotate_peaks.analyze_annotations \
    ARID3A_peak_EP_annotation_detail.tsv \
    -o ARID3A_analysis

# Step 3: Results available in:
# - ARID3A_peak_EP_annotation_detail.tsv (main annotation)
# - ARID3A_analysis_promoter.bed (promoter peaks)
# - ARID3A_analysis_enhancer.bed (enhancer peaks)  
# - ARID3A_analysis_neither.bed (neither peaks)
# - ARID3A_analysis_report.txt (summary statistics)
# - ARID3A_analysis_summary.png (visualization)
```

## Dependencies

- **Python packages**: pandas, pybedtools, matplotlib, seaborn
- **System tools**: bedtools, awk, sort
- **Optional**: bc (for shell script percentage calculations)

## Performance Notes

- Processing time scales with number of peaks and E-P interactions
- Memory usage depends on interaction data size
- Shell script version may be faster for very large datasets
- Consider using `--extend` parameter to balance sensitivity vs specificity 
# Step 4: Generate E-P Interaction Index

This step creates an E-P (Enhancer-Promoter) interaction index by:
1. Generating promoter regions from RefSeq gene annotations
2. Annotating each interaction endpoint as Promoter (P) or Enhancer (E)
3. Categorizing interactions as PP, PE, EP, or EE

## Overview

Step 4 takes the peak-associated HiCUT interactions from Step 3 and adds biological context by determining whether each interaction endpoint overlaps with promoter regions. This creates a comprehensive index that categorizes all interactions by their regulatory potential.

## Input Requirements

### Required Files
- **BEDPE file** (from Step 3): 12-column BEDPE format with peak association data
- **RefSeq annotations** OR **Pre-generated promoter regions**

### RefSeq File Format
```
chr1    134199214    134235457    NM_001039510    0    -    ...
chr1    134199214    134235457    NM_001282945    0    -    ...
```
Columns: chr, start, end, transcript_id, score, strand, ...

### Promoter File Format (if pre-generated)
```
chr1    134234456    134236457    NM_001039510
chr1    134234456    134236457    NM_001282945
```
Columns: chr, start, end, gene_id

## Output Format

The output is a gzipped BEDPE file with 15 columns:
- Columns 1-12: Original interaction data from Step 3
- Column 13: Left endpoint label (gene name or "enhancer")
- Column 14: Right endpoint label (gene name or "enhancer")
- Column 15: Interaction category (PP/PE/EP/EE)

Example:
```
chr1    4827882    chr1    4892095    ...    NM_008651    enhancer    EP
chr1    4827882    chr1    5018538    ...    NM_008651    NM_021374    PP
```

## Usage Examples

### 1. Python API (Recommended)

```python
from ep_annotator.step4_generate_index import generate_interaction_index

# Basic usage with RefSeq file
result = generate_interaction_index(
    bedpe_file="step3_output.bedpe",
    refseq_file="mm10_NCBIRefSeq_refGene.bed",
    output_file="interactions_index.bedpe.gz",
    verbose=True
)

# Using pre-generated promoter file
result = generate_interaction_index(
    bedpe_file="step3_output.bedpe",
    promoter_file="mm10_promoters1kb.bed",
    output_file="interactions_index.bedpe.gz"
)

# Custom promoter regions (TSS ±2kb)
result = generate_interaction_index(
    bedpe_file="step3_output.bedpe",
    refseq_file="mm10_NCBIRefSeq_refGene.bed",
    upstream=2000,
    downstream=2001,
    verbose=True
)
```

### 2. Command Line Interface

```bash
# Generate promoter regions first
python src/ep_annotator/step4_generate_index/generate_promoters.py \
    -i mm10_NCBIRefSeq_refGene.bed \
    -o mm10_promoters1kb.bed \
    --upstream 1000 --downstream 1001

# Annotate interactions
python src/ep_annotator/step4_generate_index/annotate_ep.py \
    --bedpe step3_output.bedpe \
    --prom mm10_promoters1kb.bed \
    -o interactions_index.bedpe.gz
```

### 3. Shell Script (Complete Workflow)

```bash
# Basic usage
./src/ep_annotator/step4_generate_index/scripts/generate_index.sh \
    -i step3_output.bedpe \
    -r mm10_NCBIRefSeq_refGene.bed \
    -o interactions_index.bedpe.gz

# With custom parameters
./src/ep_annotator/step4_generate_index/scripts/generate_index.sh \
    -i step3_output.bedpe \
    -r mm10_NCBIRefSeq_refGene.bed \
    -o interactions_index.bedpe.gz \
    --upstream 2000 --downstream 2001 \
    --verbose

# Using pre-generated promoter file
./src/ep_annotator/step4_generate_index/scripts/generate_index.sh \
    -i step3_output.bedpe \
    -p mm10_promoters1kb.bed \
    -o interactions_index.bedpe.gz
```

### 4. Integration with Pipeline

```python
# Pipeline integration
from ep_annotator.step3_associate_peaks import associate_interactions_with_peaks
from ep_annotator.step4_generate_index import generate_interaction_index

# Step 3: Associate peaks
interactions_with_peaks = associate_interactions_with_peaks(
    interactions_file="step2_output.bedpe",
    peaks_file="h3k27ac_peaks.bed",
    output_file="step3_output.bedpe",
    distance_threshold=2000
)

# Step 4: Generate index
interaction_index = generate_interaction_index(
    bedpe_file=interactions_with_peaks,
    refseq_file="mm10_NCBIRefSeq_refGene.bed",
    output_file="step4_output.bedpe.gz"
)
```

## Algorithm Details

### Promoter Region Generation
1. **Parse RefSeq annotations** to extract gene coordinates and strand information
2. **Calculate TSS position**:
   - Forward strand (+): TSS = gene_start
   - Reverse strand (-): TSS = gene_end - 1
3. **Define promoter region**: TSS ± specified distance (default: ±1kb)
4. **Handle edge cases**: Ensure no negative coordinates

### E-P Annotation Process
1. **Load promoter regions** into efficient data structure (IntervalTree or sorted lists)
2. **For each interaction endpoint**:
   - Extract chromosome and position
   - Query promoter regions for overlaps
   - Label as promoter (gene name) or enhancer
3. **Categorize interaction**:
   - PP: Both endpoints are promoters
   - PE: Left=promoter, Right=enhancer
   - EP: Left=enhancer, Right=promoter  
   - EE: Both endpoints are enhancers

### Performance Optimization
- **IntervalTree**: O(log n) lookup time for promoter queries
- **Fallback method**: Linear search if IntervalTree unavailable
- **Memory efficient**: Stream processing for large files
- **Progress tracking**: tqdm progress bars for long-running operations

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `upstream` | 1000 | Distance upstream of TSS for promoter regions |
| `downstream` | 1001 | Distance downstream of TSS for promoter regions |
| `use_interval_tree` | True | Use IntervalTree for faster lookup |
| `verbose` | False | Enable detailed logging |
| `keep_temp` | False | Keep temporary files for debugging |

## Output Statistics

The tool reports interaction category counts:
```
✅ 写入 interactions_index.bedpe.gz
PE: 50,032
EP: 50,751  
PP: 22,104
EE: 439,023
```

**Interpretation**:
- **EP/PE**: Enhancer-promoter interactions (most biologically relevant)
- **PP**: Promoter-promoter interactions (regulatory networks)
- **EE**: Enhancer-enhancer interactions (enhancer hubs)

## Dependencies

### Required
- Python 3.6+
- Standard library modules

### Optional (for performance)
- `intervaltree`: Fast interval queries
- `tqdm`: Progress bars
- `pandas`: Data manipulation (for downstream analysis)

### Installation
```bash
# Basic functionality
pip install intervaltree tqdm

# For advanced analysis
pip install pandas matplotlib seaborn
```

## Performance Benchmarks

| Dataset Size | Interactions | Promoters | Time | Memory |
|--------------|-------------|-----------|------|--------|
| Small | 10K | 20K | ~5s | <100MB |
| Medium | 100K | 50K | ~30s | <500MB |
| Large | 500K | 50K | ~2min | <1GB |
| Very Large | 3M+ | 50K | ~10min | <2GB |

*Benchmarks on standard desktop (16GB RAM, SSD)*

## Troubleshooting

### Common Issues

1. **Memory errors with large files**
   ```bash
   # Use simple lookup method
   python annotate_ep.py --bedpe large.bedpe --prom promoters.bed --no-interval-tree
   ```

2. **IntervalTree import error**
   ```bash
   pip install intervaltree
   # Or use --no-interval-tree flag
   ```

3. **Invalid file formats**
   - Ensure BEDPE has 12+ columns
   - Check RefSeq file has 6+ columns with valid coordinates
   - Verify chromosome naming consistency

4. **Empty output or no promoter overlaps**
   - Check chromosome naming (chr1 vs 1)
   - Verify coordinate systems match
   - Try larger promoter windows

### Debug Mode
```python
# Enable detailed logging
result = generate_interaction_index(
    bedpe_file="input.bedpe",
    refseq_file="refseq.bed",
    verbose=True,
    keep_temp=True  # Keep intermediate files
)
```

## Integration Notes

### With Step 3
- Requires 12-column BEDPE output from peak association
- Maintains all original annotation data

### With Step 5
- Provides categorized interactions for peak annotation
- Creates foundation for regulatory network analysis

### Data Flow
```
Step 3 Output (12-col BEDPE) + RefSeq → Step 4 → Index (15-col BEDPE.gz)
                                ↓
                           Promoter regions (4-col BED)
```

## Quality Control

### Validation Checks
1. **Input validation**: File existence, format correctness
2. **Coordinate validation**: Non-negative coordinates, valid ranges
3. **Output validation**: Expected column count, category distributions
4. **Sanity checks**: Reasonable promoter/enhancer ratios

### Expected Results
- **Promoter coverage**: 5-15% of interaction endpoints typically overlap promoters
- **Category distribution**: EE > EP/PE > PP (varies by cell type)
- **File size**: Output typically 1.5-2x larger than input due to annotations

This step is crucial for downstream regulatory analysis and provides the foundation for understanding the functional significance of chromatin interactions. 
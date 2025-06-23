# Associate Peaks - Usage Examples

## Overview

`associate_peaks.py` is the simplified implementation of step 3, directly translating the original shell script logic with complete distance filtering functionality.

## Basic Usage

### 1. Basic Association (no filtering)

```bash
python src/ep_annotator/step3_associate_peaks/associate_peaks.py \
    input_interactions.bedpe \
    input_peaks.bed \
    output_with_peaks.bedpe
```

**Input formats:**
- `input_interactions.bedpe`: 4-column format (chrA posA chrB posB)
- `input_peaks.bed`: 3-column format (chr start end)

**Output format:**
- `output_with_peaks.bedpe`: 12-column format (chrA posA chrB posB l_chr l_start l_end l_dist r_chr r_start r_end r_dist)

### 2. With Distance Filtering (recommended)

```bash
python src/ep_annotator/step3_associate_peaks/associate_peaks.py \
    input_interactions.bedpe \
    input_peaks.bed \
    output_near_peaks.bedpe \
    2000
```

This is equivalent to the two-step operation in the original workflow:
1. `./annotate_hicut_w_cuttag.sh`
2. `awk '$8 < 2000 && $12 < 2000' input.bedpe > output.bedpe`

## Real-world Examples

### Reproducing Original Workflow

```bash
# Original workflow (2 steps):
./annotate_hicut_w_cuttag.sh
awk '$8 < 2000 && $12 < 2000' E145_E_HiCUT_with_peaks.bedpe > E145_E_HiCUT_with_peaks_near2k.bedpe

# Simplified version (1 step):
python associate_peaks.py \
    E145_E_H3K27ac_HiCUT_union.bedpe \
    E145_E_H3K27ac_CUTTAG_union.bed \
    E145_E_HiCUT_with_peaks_near2k.bedpe \
    2000
```

### Integration into Python Pipeline

```python
from step3_associate_peaks.associate_peaks import associate_peaks_simple

# Call within Python code
result_file = associate_peaks_simple(
    interaction_file="data/interactions.bedpe",
    peak_file="data/peaks.bed", 
    output_file="output/associated.bedpe",
    distance_threshold=2000  # optional
)
```

## Performance Features

- **Speed**: Near original shell script performance
- **Memory**: Low memory footprint
- **Simplicity**: ~120 lines of code vs original 37 lines shell + 427 lines complex Python
- **Compatibility**: Fully compatible with original data formats and output

## Output Examples

**Input interactions.bedpe:**
```
chr1    1000000    chr1    2000000
chr2    500000     chr2    1500000
```

**Input peaks.bed:**
```
chr1    999900    1000100
chr1    2000050   2000150
chr2    500200    500400
```

**Output (no filtering):**
```
chr1    1000000    chr1    2000000    chr1    999900    1000100    100    chr1    2000050    2000150    50
chr2    500000     chr2    1500000    chr2    500200    500400     200    chr2    500200    500400     1000000
```

**Output (2000bp filtering):**
```
chr1    1000000    chr1    2000000    chr1    999900    1000100    100    chr1    2000050    2000150    50
# Second line filtered out because right endpoint distance is 1000000 > 2000
```

## Error Handling

The script includes basic error handling:
- File existence checks
- bedtools dependency verification
- Command execution error capture
- Clear error messages

## Dependencies

- `bedtools` (required)
- `awk` (required)
- `sort` (required)
- Python 3.6+ (required)

No additional Python package dependencies required! 
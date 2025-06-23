# Step 3: Associate Interactions with Peaks

This module associates HiCUT chromatin interactions with H3K27Ac CUT&Tag peaks to identify peak-to-peak interactions.

## Overview

Step 3 takes processed chromatin interactions (from Step 1) and H3K27Ac peak data (from Step 2) and finds the closest peak for each interaction endpoint. This creates a comprehensive dataset linking interaction endpoints to specific histone modification peaks, with distance measurements.

## Implementation

### Core Features

- **Closest Peak Assignment**: For each interaction endpoint, finds the nearest H3K27Ac peak
- **Distance Calculation**: Computes distance from interaction point to closest peak
- **Distance Filtering**: Optional filtering to keep only interactions within a specified distance threshold
- **Dual Implementation**: Both Python and shell script versions available
- **Format Validation**: Ensures input files are properly formatted
- **Progress Logging**: Comprehensive logging and progress tracking

### File Structure

```
step3_associate_peaks/
├── __init__.py           # Module interface and wrapper functions
├── associate_peaks.py    # Main Python implementation
├── scripts/
│   └── associate_peaks.sh # Shell script implementation
└── README.md            # This documentation
```

## Usage

### 1. Python API (Recommended)

```python
from src.ep_annotator.step3_associate_peaks import associate_interactions_with_peaks

# Basic association
result = associate_interactions_with_peaks(
    interaction_file="interactions.bedpe",
    peak_file="peaks.bed", 
    output_file="output.bedpe"
)

# With distance filtering (2kb threshold)
result = associate_interactions_with_peaks(
    interaction_file="interactions.bedpe",
    peak_file="peaks.bed", 
    output_file="output.bedpe",
    distance_threshold=2000,
    verbose=True
)
```

### 2. Command Line Interface

```bash
# Basic association
python src/ep_annotator/step3_associate_peaks/associate_peaks.py \
    -i interactions.bedpe \
    -p peaks.bed \
    -o output.bedpe

# With distance filtering and verbose output
python src/ep_annotator/step3_associate_peaks/associate_peaks.py \
    -i interactions.bedpe \
    -p peaks.bed \
    -o output.bedpe \
    -d 2000 \
    -v

# Use Python method instead of bedtools
python src/ep_annotator/step3_associate_peaks/associate_peaks.py \
    -i interactions.bedpe \
    -p peaks.bed \
    -o output.bedpe \
    --method python
```

### 3. Shell Script Interface

```bash
# Basic association
src/ep_annotator/step3_associate_peaks/scripts/associate_peaks.sh \
    -i interactions.bedpe \
    -p peaks.bed \
    -o output.bedpe

# With distance filtering and debugging
src/ep_annotator/step3_associate_peaks/scripts/associate_peaks.sh \
    -i interactions.bedpe \
    -p peaks.bed \
    -o output.bedpe \
    -d 2000 \
    -v \
    -k  # Keep temporary files
```

### 4. Legacy Interface

```python
from src.ep_annotator.step3_associate_peaks import associate_peaks

# Legacy interface (maintains backward compatibility)
result = associate_peaks(
    interaction_file="interactions.bedpe",
    peak_file="peaks.bed",
    output_prefix="output",  # Will create output.bedpe
    distance_threshold=2000
)
```

## Input/Output Formats

### Input Files

1. **Interaction File** (4-column BEDPE format):
   ```
   chrA    posA    chrB    posB
   chr1    1000    chr2    2000
   chr1    1500    chr1    3000
   ```

2. **Peak File** (3-column BED format):
   ```
   chr     start   end
   chr1    900     1100
   chr1    2900    3100
   ```

### Output Format

12-column format combining original interaction data with peak association information:

```
chrA  posA  chrB  posB  l_chr  l_start  l_end  l_dist  r_chr  r_start  r_end  r_dist
chr1  1000  chr2  2000  chr1   900      1100   0       chr2   1950     2050   0
```

Where:
- `l_chr`, `l_start`, `l_end`, `l_dist`: Closest peak info for left endpoint
- `r_chr`, `r_start`, `r_end`, `r_dist`: Closest peak info for right endpoint
- Distance of `-1` indicates no peak found on that chromosome

## Algorithm

1. **Peak Sorting**: Sort peak file using bedtools or Python
2. **Left Endpoint Processing**:
   - Convert interaction positions to single-base intervals
   - Add row numbers for tracking
   - Find closest peak using bedtools closest or interval trees
   - Extract distance information
3. **Right Endpoint Processing**: Same as left endpoint
4. **Result Combination**: Merge original interactions with peak data
5. **Distance Filtering** (optional): Keep only interactions within threshold

## Performance

### Benchmarks (Real Data)
- **Dataset**: 3.3M interactions, 219K peaks
- **Processing Time**: ~35 seconds (bedtools method)
- **Memory Usage**: < 1GB
- **Output Size**: ~97MB → ~200MB (with peak annotations)

### Method Comparison
- **bedtools method**: Faster for large datasets, requires system dependencies
- **python method**: Pure Python, slower but more portable

## Dependencies

### Required
- Python 3.7+
- awk, sort, cut, paste (for shell operations)

### Optional
- **bedtools**: Required for bedtools method (recommended)
- **pandas**: Optional for Python method
- **intervaltree**: Required for Python method fallback

## Error Handling

- File existence and format validation
- Dependency checking with automatic fallbacks
- Comprehensive error messages with context
- Graceful handling of missing peaks (reports -1 distances)

## Performance Tips

1. **Use bedtools method** for large datasets when available
2. **Enable distance filtering** to reduce output file size
3. **Use verbose mode** for large datasets to monitor progress
4. **Pre-sort files** if running multiple times with same data

## Testing

The implementation has been thoroughly tested against the original command pipeline:

```bash
# Original command (reference)
./annotate_hicut_w_cuttag.sh
# Result: 3,315,559 interactions → 563,563 after 2kb filtering

# Our implementation
python associate_peaks.py -i interactions.bedpe -p peaks.bed -o output.bedpe -d 2000
# Result: 3,315,559 interactions → 563,563 after 2kb filtering ✅
```

Results are **identical** to the original implementation.

## Integration

This step integrates seamlessly with the EP_annotator pipeline:

```python
# Complete pipeline steps 1-3
from src.ep_annotator.step1_prepare_interactions import merge_hicut_files
from src.ep_annotator.step2_prepare_peaks import merge_peak_files  
from src.ep_annotator.step3_associate_peaks import associate_interactions_with_peaks

# Step 1: Process interactions
interactions = merge_hicut_files(
    input_files=["file1.allValidPairs", "file2.allValidPairs"],
    output_prefix="interactions"
)

# Step 2: Process peaks
peaks = merge_peak_files(
    input_files=["peaks1.bed", "peaks2.bed"],
    output_prefix="peaks"
)

# Step 3: Associate interactions with peaks
result = associate_interactions_with_peaks(
    interaction_file=interactions,
    peak_file=peaks,
    output_file="associated_interactions.bedpe",
    distance_threshold=2000
)
``` 
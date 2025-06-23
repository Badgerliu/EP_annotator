# Step 3: Associate Peaks with Interactions

This module is responsible for finding the nearest H3K27Ac peak for each endpoint of chromatin interactions, based on the logic of the original `annotate_hicut_w_cuttag.sh` script.

## Implementation

We use a **simplified implementation** that directly translates the original shell script logic:

- **`associate_peaks.py`** (~120 lines) - Main implementation
- Direct translation of original shell script using bedtools
- Includes integrated distance filtering functionality
- High performance with minimal complexity

## Quick Start

### Command Line Usage

```bash
# Basic association
python src/ep_annotator/step3_associate_peaks/associate_peaks.py \
    input_interactions.bedpe \
    input_peaks.bed \
    output_with_peaks.bedpe

# With distance filtering (recommended)
python src/ep_annotator/step3_associate_peaks/associate_peaks.py \
    input_interactions.bedpe \
    input_peaks.bed \
    output_near_peaks.bedpe \
    2000
```

### Python API

```python
from src.ep_annotator.step3_associate_peaks import associate_interactions_with_peaks

# Basic usage
result = associate_interactions_with_peaks(
    interaction_file="interactions.bedpe",
    peak_file="peaks.bed", 
    output_file="output.bedpe"
)

# With distance filtering
result = associate_interactions_with_peaks(
    interaction_file="interactions.bedpe",
    peak_file="peaks.bed", 
    output_file="output.bedpe",
    distance_threshold=2000,
    verbose=True
)
```

## Input/Output Formats

### Input Files

1. **Interaction File** (4-column BEDPE):
   ```
   chrA    posA    chrB    posB
   chr1    1000    chr2    2000
   ```

2. **Peak File** (3-column BED):
   ```
   chr     start   end
   chr1    900     1100
   ```

### Output Format

12-column BEDPE with peak association data:

```
chrA  posA  chrB  posB  l_chr  l_start  l_end  l_dist  r_chr  r_start  r_end  r_dist
chr1  1000  chr2  2000  chr1   900      1100   100     chr2   1950     2050   50
```

Where:
- `l_*`: Left endpoint peak information
- `r_*`: Right endpoint peak information  
- `*_dist`: Distance to nearest peak

## Algorithm

This implementation follows the exact same logic as the original shell script:

1. **Left Endpoint Processing**: Find closest peak for each left endpoint using `bedtools closest`
2. **Right Endpoint Processing**: Find closest peak for each right endpoint using `bedtools closest`
3. **Combine Results**: Use `paste` to merge original interactions with peak data
4. **Distance Filtering**: Optional filtering using `awk` (same as original: `$8 < threshold && $12 < threshold`)

## Performance

- **Speed**: Near original shell script performance
- **Memory**: Low memory footprint
- **Simplicity**: ~120 lines vs 427 lines complex version
- **Compatibility**: 100% compatible with original data formats

### Benchmarks
- **Dataset**: 3.3M interactions, 219K peaks
- **Processing Time**: ~35 seconds
- **Results**: Identical to original implementation

## Dependencies

- `bedtools` (required)
- `awk`, `sort`, `cut`, `paste` (required)
- Python 3.6+ (required)

**No additional Python packages required!**

## Distance Filtering

The distance filtering feature replicates the original workflow's two-step process in a single command:

### Original Workflow (2 steps):
```bash
./annotate_hicut_w_cuttag.sh
awk '$8 < 2000 && $12 < 2000' input.bedpe > output.bedpe
```

### Simplified Version (1 step):
```bash
python associate_peaks.py input.bedpe peaks.bed output.bedpe 2000
```

## Testing

Tested against original implementation with identical results:

```bash
# Original: 3,315,559 → 563,563 after 2kb filtering (17.0%)
# Our implementation: 3,315,559 → 563,563 after 2kb filtering (17.0%) ✅
```

## Error Handling

- File existence validation
- Basic command execution error capture
- Clear error messages
- Graceful dependency checking

## Integration

Seamlessly integrates with the EP_annotator pipeline and maintains full backward compatibility with the original workflow. 
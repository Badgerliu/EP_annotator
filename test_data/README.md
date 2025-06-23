# EP_annotator Test Data

This directory contains sample data for testing and validating the EP_annotator pipeline. The data is derived from real Hi-C and CUT&Tag experiments but has been processed and formatted for demonstration purposes.

## 📁 Data Files

### Input Data Files

| File | Description | Size | Records |
|------|-------------|------|---------|
| `test_experiment_HiCUT_union.bedpe` | Hi-C interaction data (BEDPE format) | ~93MB | 3,315,559 interactions |
| `test_experiment_H3K27ac_CUTTAG_union.bed` | H3K27Ac CUT&Tag peaks (BED format) | ~5MB | 219,072 peaks |
| `sample_query_peaks.bed` | Subset of H3K27Ac peaks for annotation | ~22KB | 1,000 peaks |

### Configuration File

| File | Description |
|------|-------------|
| `test_config.yaml` | Complete pipeline configuration using test data |

## 🚀 Quick Start

### 1. Test Individual Steps

```bash
# Test Step 1: Prepare HiCUT interactions
python scripts/run_pipeline.py -c test_data/test_config.yaml -s 1 -v

# Test Step 2: Prepare H3K27Ac peaks  
python scripts/run_pipeline.py -c test_data/test_config.yaml -s 2 -v

# Test Step 3: Associate peaks with interactions
python scripts/run_pipeline.py -c test_data/test_config.yaml -s 3 -v

# Continue with steps 4-6...
```

### 2. Run Complete Pipeline

```bash
# Run all 6 steps in sequence
python scripts/run_pipeline.py -c test_data/test_config.yaml -v
```

### 3. Expected Output

The pipeline will create a `test_output/` directory with:

#### Core Data Files
- `test_result_interactions.bedpe` - Processed Hi-C data (Step 1)
- `test_result_peaks.bed` - Processed H3K27Ac peaks (Step 2)  
- `test_result_associated.bedpe` - Peak-interaction associations (Step 3)
- `test_result_index.bedpe.gz` - Labeled E-P interactions (Step 4)
- `test_result_peak_annotation.tsv` - Detailed peak annotations (Step 5)

#### Analysis Results  
- `test_result_comprehensive_statistics.txt` - Statistical summary
- `test_result_*_enhancer.bed` - Classified enhancer peaks
- `test_result_*_promoter.bed` - Classified promoter peaks

#### Visualizations
- `test_result_interaction_pie.png` - Interaction type distribution
- `test_result_distance_analysis.png` - Distance distribution plots
- `test_result_chromosome_distribution.png` - Chromosome analysis
- `test_result_comprehensive_summary.png` - Multi-panel summary

## 📊 Expected Results Summary

Based on the test data, you should expect approximately:

### Interaction Processing
- **Input**: 3,315,559 Hi-C interactions
- **After filtering (2kb)**: ~563,563 interactions (17.0%)
- **Processing time**: ~35 seconds for Step 3

### E-P Classification (Step 4)
- **EE (Enhancer-Enhancer)**: ~440,573 (78.2%)
- **EP (Enhancer-Promoter)**: ~50,854 (9.0%)  
- **PE (Promoter-Enhancer)**: ~50,032 (8.9%)
- **PP (Promoter-Promoter)**: ~22,104 (3.9%)

### Peak Annotation (Step 5, 1000 peaks)
- **Promoter peaks**: ~56 (5.6%)
- **Enhancer peaks**: ~896 (89.6%)
- **Neither**: ~48 (4.8%)

## 🔧 Performance Expectations

### System Requirements
- **Memory**: 4GB+ recommended
- **Storage**: ~500MB for output files
- **Time**: 2-5 minutes for complete pipeline

### Processing Times
- **Step 1**: <10 seconds
- **Step 2**: <10 seconds  
- **Step 3**: ~35 seconds (largest step)
- **Step 4**: ~10 seconds
- **Step 5**: ~30 seconds (depends on query size)
- **Step 6**: ~15 seconds

## 🧪 Validation

To verify your installation and results:

```bash
# 1. Check output file sizes match expectations
ls -lh test_output/

# 2. Verify interaction counts
wc -l test_output/test_result_interactions.bedpe

# 3. Check final statistics
cat test_output/test_result_comprehensive_statistics.txt

# 4. Validate visualizations were created
ls test_output/*.png
```

## 📝 Data Format Details

### BEDPE Format (Hi-C interactions)
```
chr1    3268337    3268746    chr1    4256399    4258826
chrA    startA     endA       chrB    startB     endB
```

### BED Format (H3K27Ac peaks)
```
chr1    3268337    3268746
chr     start      end
```

### Extended BEDPE (Step 3 output)
```
chrA  startA  endA  chrB  startB  endB  l_chr  l_start  l_end  l_dist  r_chr  r_start  r_end  r_dist
```

## 🔍 Troubleshooting

### Common Issues

1. **File not found errors**
   - Ensure you're running from the EP_annotator root directory
   - Check that `refGenome/mm10/mm10_NCBIRefSeq_refGene.bed` exists

2. **Memory errors**
   - Reduce the dataset size or increase available memory
   - Use the smaller `sample_query_peaks.bed` for Step 5

3. **Long processing times**
   - Step 3 processes 3M+ interactions - expect ~35 seconds
   - Use verbose mode (`-v`) to monitor progress

### Getting Help

If you encounter issues:
1. Check the main README.md for installation instructions
2. Review the VERIFICATION_REPORT.md for expected behavior
3. Run with `-v` flag for detailed logging
4. Ensure all dependencies are installed correctly

## 📚 Next Steps

After successfully running the test data:

1. **Explore outputs**: Examine the generated files and visualizations
2. **Understand parameters**: Modify `test_config.yaml` to test different settings
3. **Use your data**: Create a new configuration file pointing to your own Hi-C and CUT&Tag data
4. **Scale up**: Process larger datasets using the same pipeline

---

*This test dataset is designed to validate EP_annotator installation and demonstrate all pipeline features with realistic biological data.* 
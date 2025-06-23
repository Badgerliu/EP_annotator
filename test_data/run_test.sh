#!/bin/bash

# EP_annotator Complete Pipeline Test Script
# This script runs the complete EP_annotator pipeline (Steps 1-6) using sample data

echo "🧪 EP_annotator Complete Pipeline Test"
echo "======================================="
echo ""

# Check if we're in the right directory
if [ ! -f "scripts/run_pipeline.py" ]; then
    echo "❌ Error: Please run this script from the EP_annotator root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: scripts/run_pipeline.py"
    exit 1
fi

# Check if test data exists
if [ ! -f "test_data/test_config.yaml" ]; then
    echo "❌ Error: Test data not found. Please ensure test_data/ directory exists."
    exit 1
fi

# Check if output directory exists, create if not
if [ ! -d "test_output" ]; then
    echo "📁 Creating test_output directory..."
    mkdir -p test_output
fi

echo "📋 Test Configuration:"
echo "   Config: test_data/test_config.yaml"
echo "   HiCUT data: $(wc -l < test_data/test_experiment_HiCUT_union.bedpe) interactions"
echo "   H3K27Ac data: $(wc -l < test_data/test_experiment_H3K27ac_CUTTAG_union.bed) peaks"
echo "   Query peaks: $(wc -l < test_data/sample_query_peaks.bed) peaks"
echo "   Pipeline: Step 1 → Step 6 (Complete)"
echo ""

# Clean previous test output
echo "🧹 Cleaning previous test output..."
rm -rf test_output/*
echo ""

echo "🚀 Starting complete EP_annotator pipeline (Steps 1-6)..."
echo "   This will process the data through all 6 steps sequentially"
echo ""

# Run the complete pipeline
start_time=$(date +%s)

if python scripts/run_pipeline.py -c test_data/test_config.yaml -v; then
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    echo ""
    echo "✅ Complete pipeline finished successfully!"
    echo "⏱️  Total time: ${duration} seconds"
    echo ""
    
    # Check outputs
    echo "📁 Generated output files:"
    if [ -d "test_output" ]; then
        file_count=$(ls -1 test_output/ 2>/dev/null | wc -l)
        echo "   Total files: $file_count"
        echo ""
        ls -lh test_output/ | grep -v '^total' | while read line; do
            echo "   $line"
        done
    else
        echo "   ❌ No test_output directory found"
    fi
    echo ""
    
    # Show summary statistics if available
    if [ -f "test_output/test_result_comprehensive_statistics.txt" ]; then
        echo "📊 Pipeline Summary Statistics:"
        head -20 test_output/test_result_comprehensive_statistics.txt | sed 's/^/   /'
        echo ""
    fi
    
    # Comprehensive validation
    echo "🔍 Pipeline Validation:"
    
    # Check Step 1 output
    if [ -f "test_output/test_result_interactions.bedpe" ]; then
        interactions=$(wc -l < test_output/test_result_interactions.bedpe)
        echo "   ✅ Step 1: Processed interactions ($interactions lines)"
    else
        echo "   ❌ Step 1: Missing interactions file"
    fi
    
    # Check Step 2 output
    if [ -f "test_output/test_result_peaks.bed" ]; then
        peaks=$(wc -l < test_output/test_result_peaks.bed)
        echo "   ✅ Step 2: Merged peaks ($peaks lines)"
    else
        echo "   ❌ Step 2: Missing peaks file"
    fi
    
    # Check Step 3 output
    if [ -f "test_output/test_result_associated.bedpe" ]; then
        associated=$(wc -l < test_output/test_result_associated.bedpe)
        echo "   ✅ Step 3: Associated interactions ($associated lines)"
    else
        echo "   ❌ Step 3: Missing associated file"
    fi
    
    # Check Step 4 output
    if [ -f "test_output/test_result_index.bedpe.gz" ]; then
        echo "   ✅ Step 4: E-P index generated (compressed)"
    else
        echo "   ❌ Step 4: Missing E-P index file"
    fi
    
    # Check Step 5 output
    if [ -f "test_output/test_result_peak_annotation.tsv" ]; then
        annotated=$(tail -n +2 test_output/test_result_peak_annotation.tsv | wc -l)
        echo "   ✅ Step 5: Peak annotations ($annotated peaks)"
    else
        echo "   ❌ Step 5: Missing annotation file"
    fi
    
    # Check Step 6 output
    viz_count=$(ls test_output/*.png 2>/dev/null | wc -l)
    if [ -f "test_output/test_result_comprehensive_statistics.txt" ]; then
        echo "   ✅ Step 6: Statistical analysis ($viz_count plots)"
    else
        echo "   ❌ Step 6: Missing statistics file"
    fi
    
    echo ""
    echo "🎉 Complete pipeline test finished!"
    echo ""
    echo "📚 Results Summary:"
    echo "   📁 Output directory: test_output/"
    echo "   🗂️  Total files generated: $(ls -1 test_output/ 2>/dev/null | wc -l)"
    echo "   📊 Visualization plots: $viz_count"
    echo "   ⏱️  Processing time: ${duration} seconds"
    echo ""
    echo "📖 Next steps:"
    echo "   1. Explore results in test_output/"
    echo "   2. View statistical plots (*.png files)"
    echo "   3. Read comprehensive_statistics.txt for detailed analysis"
    echo "   4. Check peak_annotation.tsv for individual peak details"
    echo "   5. Examine the E-P index (test_result_index.bedpe.gz)"
    
else
    echo ""
    echo "❌ Pipeline failed. Check the error messages above."
    echo ""
    echo "🔍 Troubleshooting tips:"
    echo "   1. Ensure all dependencies are installed: pip install -r requirements.txt"
    echo "   2. Check that bedtools is available: bedtools --version"
    echo "   3. Verify the reference genome file exists: ls refGenome/mm10/"
    echo "   4. Check individual steps:"
    echo "      python scripts/run_pipeline.py -c test_data/test_config.yaml -s 1 -v"
    echo "      python scripts/run_pipeline.py -c test_data/test_config.yaml -s 2 -v"
    echo "      (continue for each step)"
    exit 1
fi 
#!/usr/bin/env python3
"""
Test script for Step 6: Analyze Results

This script demonstrates the functionality of step6 with sample data
and validates that all components work correctly.
"""

import os
import sys
import tempfile
import logging
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ep_annotator.step6_analyze_results import (
    analyze_results,
    create_interaction_pie_chart,
    calculate_interaction_statistics,
    load_bedpe_data
)


def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def create_sample_bedpe_data(output_file: str, logger: logging.Logger):
    """
    Create sample BEDPE data for testing.
    
    Args:
        output_file: Path to output BEDPE file
        logger: Logger instance
    """
    logger.info(f"Creating sample BEDPE data: {output_file}")
    
    # Sample data with different interaction types
    sample_data = [
        # chr1, start1, end1, chr2, start2, end2, peak1_chr, peak1_dist, peak2_chr, peak2_dist, peak1_closest, peak2_closest, label1, label2, interaction_type
        "chr1\t1000000\t1000001\tchr1\t1500000\t1500001\tchr1\t500\tchr1\t800\tpeak1\tpeak2\tE\tP\tEP",
        "chr1\t2000000\t2000001\tchr1\t2500000\t2500001\tchr1\t300\tchr1\t1200\tpeak3\tpeak4\tP\tE\tPE",
        "chr2\t1000000\t1000001\tchr2\t1500000\t1500001\tchr2\t700\tchr2\t900\tpeak5\tpeak6\tE\tE\tEE",
        "chr2\t2000000\t2000001\tchr2\t2500000\t2500001\tchr2\t400\tchr2\t600\tpeak7\tpeak8\tP\tP\tPP",
        "chr3\t1000000\t1000001\tchr3\t1500000\t1500001\tchr3\t1500\tchr3\t1800\tpeak9\tpeak10\tE\tP\tEP",
        "chr3\t2000000\t2000001\tchr4\t1000000\t1000001\tchr3\t200\tchr4\t300\tpeak11\tpeak12\tE\tE\tEE",
        "chr4\t1000000\t1000001\tchr4\t1500000\t1500001\tchr4\t800\tchr4\t1000\tpeak13\tpeak14\tP\tE\tPE",
        "chr5\t1000000\t1000001\tchr5\t1500000\t1500001\tchr5\t600\tchr5\t750\tpeak15\tpeak16\tP\tP\tPP",
    ]
    
    with open(output_file, 'w') as f:
        for line in sample_data:
            f.write(line + '\n')
    
    logger.info(f"Created sample BEDPE file with {len(sample_data)} interactions")


def test_pie_chart_creation(logger: logging.Logger):
    """Test the pie chart creation functionality."""
    logger.info("Testing pie chart creation...")
    
    # Sample interaction counts from command_log.txt
    interaction_counts = {
        'EP': 1238,
        'PE': 781,
        'EE': 3408,
        'PP': 723
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = os.path.join(temp_dir, "test_pie_chart.png")
        
        # Create pie chart
        result_file = create_interaction_pie_chart(interaction_counts, output_file, logger)
        
        # Verify file was created
        if os.path.exists(result_file):
            logger.info(f"✅ Pie chart created successfully: {result_file}")
            file_size = os.path.getsize(result_file)
            logger.info(f"   File size: {file_size} bytes")
        else:
            logger.error("❌ Pie chart was not created")
            return False
    
    return True


def test_bedpe_analysis(logger: logging.Logger):
    """Test the complete BEDPE analysis workflow."""
    logger.info("Testing complete BEDPE analysis workflow...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample BEDPE file
        bedpe_file = os.path.join(temp_dir, "sample_data.bedpe")
        create_sample_bedpe_data(bedpe_file, logger)
        
        # Run analysis
        output_prefix = os.path.join(temp_dir, "test_analysis")
        
        try:
            output_files = analyze_results(
                bedpe_file=bedpe_file,
                output_prefix=output_prefix,
                create_plots=True,
                verbose=True
            )
            
            logger.info("✅ Analysis completed successfully")
            logger.info("Generated files:")
            for file_type, file_path in output_files.items():
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    logger.info(f"  ✓ {file_type}: {file_path} ({file_size} bytes)")
                else:
                    logger.warning(f"  ⚠ {file_type}: {file_path} (not found)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            return False


def test_statistics_calculation(logger: logging.Logger):
    """Test the statistics calculation functionality."""
    logger.info("Testing statistics calculation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample BEDPE file
        bedpe_file = os.path.join(temp_dir, "sample_data.bedpe")
        create_sample_bedpe_data(bedpe_file, logger)
        
        try:
            # Load data
            df = load_bedpe_data(bedpe_file, logger)
            
            # Calculate statistics
            stats = calculate_interaction_statistics(df, logger)
            
            # Verify statistics structure
            expected_keys = ['basic_stats', 'distance_stats', 'interaction_types', 
                           'chromosome_distribution', 'quality_metrics']
            
            for key in expected_keys:
                if key in stats:
                    logger.info(f"  ✓ {key}: present")
                else:
                    logger.error(f"  ❌ {key}: missing")
                    return False
            
            # Check interaction types
            interaction_types = stats['interaction_types']
            logger.info(f"Interaction type counts: {interaction_types}")
            
            # Verify we have the expected types
            expected_types = ['EP', 'PE', 'EE', 'PP']
            for int_type in expected_types:
                if int_type in interaction_types:
                    logger.info(f"  ✓ {int_type}: {interaction_types[int_type]} interactions")
                else:
                    logger.warning(f"  ⚠ {int_type}: not found")
            
            logger.info("✅ Statistics calculation successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Statistics calculation failed: {e}")
            return False


def main():
    """Run all tests."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("EP_annotator Step 6: Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Pie Chart Creation", test_pie_chart_creation),
        ("Statistics Calculation", test_statistics_calculation),
        ("Complete BEDPE Analysis", test_bedpe_analysis),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running test: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = test_func(logger)
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        icon = "✅" if result else "❌"
        logger.info(f"{icon} {test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Step 6 is working correctly.")
        return 0
    else:
        logger.error("💥 Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit(main()) 
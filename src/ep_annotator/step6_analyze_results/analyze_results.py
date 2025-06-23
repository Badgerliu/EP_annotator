#!/usr/bin/env python3
"""
Main Analysis Module for Step 6: Analyze Results

This module integrates statistical analysis and visualization for 
comprehensive EP interaction results analysis.
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from .statistical_analysis import (
    load_bedpe_data, 
    calculate_interaction_statistics,
    export_statistics_report
)
from .visualization import create_all_visualizations


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def analyze_results(bedpe_file: str, output_prefix: str, 
                   create_plots: bool = True, verbose: bool = False) -> Dict[str, str]:
    """
    Main function to analyze and visualize EP interaction results.
    
    This function performs comprehensive analysis including:
    - Loading and validating BEDPE interaction data
    - Calculating comprehensive statistics (distances, types, chromosomes)
    - Generating detailed statistical reports
    - Creating multiple visualization plots
    
    Args:
        bedpe_file: Path to labeled BEDPE file (can be gzipped)
        output_prefix: Prefix for output files
        create_plots: Whether to create visualization plots
        verbose: Enable verbose logging
        
    Returns:
        Dictionary with paths to generated analysis files
    """
    logger = setup_logging(verbose)
    
    logger.info("=" * 60)
    logger.info("EP_annotator - Step 6: Comprehensive Results Analysis")
    logger.info("=" * 60)
    logger.info(f"Input BEDPE file: {bedpe_file}")
    logger.info(f"Output prefix: {output_prefix}")
    logger.info(f"Create plots: {create_plots}")
    
    output_files = {}
    
    try:
        # Step 1: Load BEDPE data
        logger.info("\n📊 Loading interaction data...")
        df = load_bedpe_data(bedpe_file, logger)
        
        # Step 2: Calculate comprehensive statistics
        logger.info("\n📈 Calculating comprehensive statistics...")
        stats = calculate_interaction_statistics(df, logger)
        
        # Step 3: Export statistical report
        logger.info("\n📝 Generating statistical report...")
        stats_report = f"{output_prefix}_comprehensive_statistics.txt"
        output_files['statistics_report'] = export_statistics_report(
            stats, stats_report, logger)
        
        # Step 4: Create visualizations (if requested)
        if create_plots:
            logger.info("\n🎨 Creating visualization plots...")
            try:
                plot_files = create_all_visualizations(stats, output_prefix, logger)
                output_files.update(plot_files)
            except Exception as e:
                logger.warning(f"Failed to create some visualizations: {e}")
                logger.warning("Continuing with statistical analysis...")
        
        # Step 5: Generate summary
        logger.info("\n📋 Analysis Summary:")
        logger.info(f"  Total interactions analyzed: {stats['basic_stats']['total_interactions']:,}")
        logger.info(f"  Unique genomic loci: {stats['basic_stats']['unique_loci']:,}")
        logger.info("  Interaction types:")
        for int_type, count in stats['interaction_types'].items():
            logger.info(f"    {int_type}: {count:,}")
        logger.info(f"  Intra-chromosomal: {stats['distance_stats']['intra_chromosomal']:,}")
        logger.info(f"  Inter-chromosomal: {stats['distance_stats']['inter_chromosomal']:,}")
        
        logger.info("\n📁 Output files generated:")
        for file_type, file_path in output_files.items():
            logger.info(f"  {file_type}: {file_path}")
        
        logger.info("\n✅ Step 6 analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise
    
    return output_files


def analyze_from_step5_output(annotation_file: str, output_prefix: str,
                            create_plots: bool = True, verbose: bool = False) -> Dict[str, str]:
    """
    Analyze results from step5 annotation output.
    
    This function takes the detailed annotation TSV file from step5 and
    performs additional analysis focused on peak-level statistics.
    
    Args:
        annotation_file: Path to detailed annotation TSV file from step5
        output_prefix: Prefix for output files
        create_plots: Whether to create visualization plots
        verbose: Enable verbose logging
        
    Returns:
        Dictionary with paths to generated analysis files
    """
    logger = setup_logging(verbose)
    
    logger.info("=" * 60)
    logger.info("EP_annotator - Step 6: Analysis from Step 5 Output")
    logger.info("=" * 60)
    logger.info(f"Input annotation file: {annotation_file}")
    logger.info(f"Output prefix: {output_prefix}")
    
    # Import step5 analysis functions
    try:
        from ..step5_annotate_peaks.analyze_annotations import analyze_annotation_results
        
        # Run step5 analysis
        logger.info("Running step5 annotation analysis...")
        step5_outputs = analyze_annotation_results(
            annotation_file=annotation_file,
            output_prefix=f"{output_prefix}_step5",
            create_plots=create_plots,
            verbose=verbose
        )
        
        logger.info("✅ Step 6 analysis from step5 output completed!")
        return step5_outputs
        
    except ImportError as e:
        logger.error(f"Failed to import step5 analysis functions: {e}")
        logger.error("Please ensure step5 is properly implemented")
        raise


def main():
    """CLI entry point for step 6 analysis."""
    parser = argparse.ArgumentParser(
        description="Comprehensive analysis and visualization of EP interaction results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze BEDPE file with interaction labels
  python analyze_results.py E145_E_HiCUT_with_peaks_near2k.promLabel.bedpe.gz -o results

  # Analyze step5 annotation output
  python analyze_results.py --annotation ARID3A_peak_EP_annotation_detail.tsv -o ARID3A_analysis

  # Create only statistical report (no plots)
  python analyze_results.py data.bedpe.gz --no-plots -o analysis
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("bedpe_file", nargs='?',
                           help="Path to labeled BEDPE file (with interaction types)")
    input_group.add_argument("--annotation", 
                           help="Path to detailed annotation TSV file from step5")
    
    # Output options
    parser.add_argument("-o", "--output-prefix", default=None,
                       help="Prefix for output files (auto-generated if not provided)")
    parser.add_argument("--no-plots", action="store_true",
                       help="Skip creating visualization plots")
    
    # General options
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Validate inputs
    if args.bedpe_file and not os.path.exists(args.bedpe_file):
        parser.error(f"BEDPE file not found: {args.bedpe_file}")
    if args.annotation and not os.path.exists(args.annotation):
        parser.error(f"Annotation file not found: {args.annotation}")
    
    # Auto-generate output prefix if not provided
    if args.output_prefix is None:
        if args.bedpe_file:
            input_stem = Path(args.bedpe_file).stem
            if input_stem.endswith('.promLabel.bedpe'):
                input_stem = input_stem.replace('.promLabel.bedpe', '')
            args.output_prefix = f"{input_stem}_step6_analysis"
        elif args.annotation:
            input_stem = Path(args.annotation).stem
            args.output_prefix = f"{input_stem}_step6_analysis"
    
    # Run analysis
    try:
        if args.bedpe_file:
            # Analyze BEDPE file
            analyze_results(
                bedpe_file=args.bedpe_file,
                output_prefix=args.output_prefix,
                create_plots=not args.no_plots,
                verbose=args.verbose
            )
        elif args.annotation:
            # Analyze step5 annotation output
            analyze_from_step5_output(
                annotation_file=args.annotation,
                output_prefix=args.output_prefix,
                create_plots=not args.no_plots,
                verbose=args.verbose
            )
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 
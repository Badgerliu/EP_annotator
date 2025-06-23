#!/usr/bin/env python3
"""
Analyze annotation results from detailed peak annotation.

This module provides functions to:
- Classify peaks into promoter, enhancer, and neither categories
- Generate summary statistics
- Create visualizations of annotation results
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def load_annotation_results(annotation_file: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Load detailed annotation results.
    
    Args:
        annotation_file: Path to TSV file with annotation results
        logger: Logger instance
        
    Returns:
        DataFrame with annotation data
    """
    logger.info(f"Loading annotation results from: {annotation_file}")
    
    if not os.path.exists(annotation_file):
        raise FileNotFoundError(f"Annotation file not found: {annotation_file}")
    
    df = pd.read_csv(annotation_file, sep='\t')
    logger.info(f"✅ Loaded {len(df):,} annotated peaks")
    
    return df


def classify_peaks(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, pd.DataFrame]:
    """
    Classify peaks into promoter, enhancer, and neither categories.
    
    Args:
        df: DataFrame with annotation results
        logger: Logger instance
        
    Returns:
        Dictionary with DataFrames for each category
    """
    logger.info("Classifying peaks by category...")
    
    # Basic classification
    promoter_peaks = df[df['is_promoter'] == True].copy()
    enhancer_peaks = df[df['is_enhancer'] == True].copy()
    neither_peaks = df[(df['is_promoter'] == False) & (df['is_enhancer'] == False)].copy()
    
    categories = {
        'promoter': promoter_peaks,
        'enhancer': enhancer_peaks,
        'neither': neither_peaks
    }
    
    # Log counts
    logger.info("=== Peak Classification ===")
    for category, peaks in categories.items():
        count = len(peaks)
        percentage = count / len(df) * 100
        logger.info(f"{category.capitalize()}: {count:,} peaks ({percentage:.1f}%)")
    
    return categories


def analyze_interaction_types(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, int]:
    """
    Analyze interaction types for peaks with interactions.
    
    Args:
        df: DataFrame with annotation results
        logger: Logger instance
        
    Returns:
        Dictionary with interaction type counts
    """
    logger.info("Analyzing interaction types...")
    
    # Count peaks by interaction type
    interaction_counts = {
        'EP': 0,  # Enhancer -> Promoter
        'PE': 0,  # Promoter <- Enhancer
        'EE': 0,  # Enhancer -> Enhancer
        'PP': 0   # Promoter -> Promoter
    }
    
    for _, row in df.iterrows():
        # Check each type of interaction
        if row['enhancer_target_genes']:
            interaction_counts['EP'] += 1
        if row['regulating_enhancers']:
            interaction_counts['PE'] += 1
        if row['enhancer_partners']:
            interaction_counts['EE'] += 1
        if row['promoter_partners']:
            interaction_counts['PP'] += 1
    
    logger.info("=== Interaction Type Statistics ===")
    for int_type, count in interaction_counts.items():
        logger.info(f"{int_type}: {count:,} peaks")
    
    return interaction_counts


def save_classified_peaks(categories: Dict[str, pd.DataFrame], output_prefix: str,
                         logger: logging.Logger) -> Dict[str, str]:
    """
    Save classified peaks to separate BED files.
    
    Args:
        categories: Dictionary with classified peak DataFrames
        output_prefix: Prefix for output files
        logger: Logger instance
        
    Returns:
        Dictionary mapping category names to output file paths
    """
    logger.info("Saving classified peaks to BED files...")
    
    output_files = {}
    
    for category, peaks_df in categories.items():
        if len(peaks_df) > 0:
            # Create BED format output
            bed_df = peaks_df[['chr', 'start', 'end', 'name']].copy()
            
            output_file = f"{output_prefix}_{category}.bed"
            bed_df.to_csv(output_file, sep='\t', header=False, index=False)
            
            output_files[category] = output_file
            logger.info(f"✅ Saved {len(peaks_df):,} {category} peaks → {output_file}")
    
    return output_files


def create_summary_plot(categories: Dict[str, pd.DataFrame], interaction_counts: Dict[str, int],
                       output_file: str, logger: logging.Logger) -> str:
    """
    Create summary plots for annotation results.
    
    Args:
        categories: Dictionary with classified peak DataFrames
        interaction_counts: Dictionary with interaction type counts
        output_file: Path for output plot file
        logger: Logger instance
        
    Returns:
        Path to output plot file
    """
    logger.info("Creating summary plots...")
    
    # Set up the plot style
    plt.style.use('default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: Peak classification pie chart
    category_counts = [len(df) for df in categories.values()]
    category_labels = list(categories.keys())
    colors_category = ['#D8EEFB', '#7DC69B', '#FFB6C1']  # Light blue, green, pink
    
    wedges, texts, autotexts = ax1.pie(category_counts, labels=category_labels, 
                                      autopct='%1.1f%%', colors=colors_category,
                                      startangle=90)
    ax1.set_title('Peak Classification')
    
    # Plot 2: Interaction type bar chart
    int_types = list(interaction_counts.keys())
    int_counts = list(interaction_counts.values())
    colors_interaction = ['#7DC69B', '#9BD7F3', '#D5EAD9', '#D8EEFB']
    
    bars = ax2.bar(int_types, int_counts, color=colors_interaction)
    ax2.set_title('Interaction Type Statistics')
    ax2.set_ylabel('Number of Peaks')
    ax2.set_xlabel('Interaction Type')
    
    # Add value labels on bars
    for bar, count in zip(bars, int_counts):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(int_counts)*0.01,
                f'{count:,}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✅ Summary plots saved → {output_file}")
    return output_file


def generate_detailed_report(df: pd.DataFrame, categories: Dict[str, pd.DataFrame],
                           interaction_counts: Dict[str, int], output_file: str,
                           logger: logging.Logger) -> str:
    """
    Generate a detailed text report of annotation results.
    
    Args:
        df: Full annotation DataFrame
        categories: Dictionary with classified peaks
        interaction_counts: Dictionary with interaction type counts
        output_file: Path for output report file
        logger: Logger instance
        
    Returns:
        Path to output report file
    """
    logger.info("Generating detailed report...")
    
    total_peaks = len(df)
    
    with open(output_file, 'w') as f:
        f.write("EP_annotator - Peak Annotation Report\n")
        f.write("=" * 50 + "\n\n")
        
        # Basic statistics
        f.write("BASIC STATISTICS\n")
        f.write("-" * 20 + "\n")
        f.write(f"Total peaks analyzed: {total_peaks:,}\n\n")
        
        # Peak classification
        f.write("PEAK CLASSIFICATION\n")
        f.write("-" * 20 + "\n")
        for category, peaks_df in categories.items():
            count = len(peaks_df)
            percentage = count / total_peaks * 100
            f.write(f"{category.capitalize()} peaks: {count:,} ({percentage:.1f}%)\n")
        f.write("\n")
        
        # Interaction types
        f.write("INTERACTION TYPES\n")
        f.write("-" * 20 + "\n")
        for int_type, count in interaction_counts.items():
            percentage = count / total_peaks * 100
            f.write(f"{int_type} interactions: {count:,} ({percentage:.1f}%)\n")
        f.write("\n")
        
        # Detailed breakdown
        f.write("DETAILED BREAKDOWN\n")
        f.write("-" * 20 + "\n")
        
        # Promoter peaks with enhancer regulation
        prom_with_enh = df[(df['is_promoter'] == True) & 
                          (df['regulating_enhancers'] != "")]['regulating_enhancers'].count()
        f.write(f"Promoter peaks with enhancer regulation: {prom_with_enh:,}\n")
        
        # Enhancer peaks with targets
        enh_with_targets = df[(df['is_enhancer'] == True) & 
                             (df['enhancer_target_genes'] != "")]['enhancer_target_genes'].count()
        f.write(f"Enhancer peaks with target genes: {enh_with_targets:,}\n")
        
        # Peaks with multiple interaction types
        multi_interaction = df[
            (df['enhancer_target_genes'] != "") & 
            (df['regulating_enhancers'] != "")
        ]
        f.write(f"Peaks with multiple interaction types: {len(multi_interaction):,}\n")
        
        f.write(f"\nReport generated by EP_annotator step 5\n")
    
    logger.info(f"✅ Detailed report saved → {output_file}")
    return output_file


def analyze_annotation_results(annotation_file: str, output_prefix: str,
                             create_plots: bool = True, verbose: bool = False) -> Dict[str, str]:
    """
    Main function to analyze detailed annotation results.
    
    Args:
        annotation_file: Path to annotation TSV file
        output_prefix: Prefix for output files
        create_plots: Whether to create visualization plots
        verbose: Enable verbose logging
        
    Returns:
        Dictionary with output file paths
    """
    logger = setup_logging(verbose)
    
    logger.info("Starting annotation results analysis...")
    logger.info(f"Input file: {annotation_file}")
    logger.info(f"Output prefix: {output_prefix}")
    
    # Load data
    df = load_annotation_results(annotation_file, logger)
    
    # Classify peaks
    categories = classify_peaks(df, logger)
    
    # Analyze interactions
    interaction_counts = analyze_interaction_types(df, logger)
    
    # Save classified peaks
    output_files = save_classified_peaks(categories, output_prefix, logger)
    
    # Generate report
    report_file = f"{output_prefix}_report.txt"
    output_files['report'] = generate_detailed_report(
        df, categories, interaction_counts, report_file, logger)
    
    # Create plots if requested
    if create_plots:
        try:
            plot_file = f"{output_prefix}_summary.png"
            output_files['plot'] = create_summary_plot(
                categories, interaction_counts, plot_file, logger)
        except Exception as e:
            logger.warning(f"Failed to create plots: {e}")
    
    logger.info("✅ Analysis complete!")
    return output_files


def main():
    """CLI entry point for annotation analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze detailed peak annotation results"
    )
    parser.add_argument("annotation_file",
                       help="Path to detailed annotation TSV file")
    parser.add_argument("-o", "--output-prefix", default=None,
                       help="Prefix for output files (auto-generated if not provided)")
    parser.add_argument("--no-plots", action="store_true",
                       help="Skip creating visualization plots")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Auto-generate output prefix if not provided
    if args.output_prefix is None:
        input_stem = Path(args.annotation_file).stem
        args.output_prefix = f"{input_stem}_analysis"
    
    # Run analysis
    analyze_annotation_results(
        annotation_file=args.annotation_file,
        output_prefix=args.output_prefix,
        create_plots=not args.no_plots,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main() 
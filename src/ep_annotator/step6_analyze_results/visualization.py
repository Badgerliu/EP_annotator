#!/usr/bin/env python3
"""
Advanced Visualization Module for EP Interaction Results

This module provides comprehensive visualization functions for 
enhancer-promoter interaction data, including:
- Interaction type pie charts (with specific colors from command_log.txt)
- Distance distribution plots
- Chromosome distribution plots
- Quality metrics visualization
- Multi-panel summary plots
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import gzip

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Wedge
import matplotlib.patches as mpatches

# Set matplotlib backend for headless environments
import matplotlib
matplotlib.use('Agg')


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def create_interaction_pie_chart(interaction_counts: Dict[str, int], output_file: str, 
                                logger: logging.Logger) -> str:
    """
    Create pie chart for interaction types with specific colors from command_log.txt.
    
    Colors specified in command_log.txt:
    - EP: #7DC69B (green)
    - PE: #9BD7F3 (blue)  
    - EE: #D5EAD9 (light green)
    - PP: #D8EEFB (light blue)
    
    Args:
        interaction_counts: Dictionary with interaction type counts
        output_file: Path for output plot file
        logger: Logger instance
        
    Returns:
        Path to output plot file
    """
    logger.info("Creating interaction type pie chart...")
    
    # Define colors as specified in command_log.txt
    colors = {
        'EP': '#7DC69B',  # green
        'PE': '#9BD7F3',  # blue
        'EE': '#D5EAD9',  # light green
        'PP': '#D8EEFB'   # light blue
    }
    
    # Prepare data
    labels = []
    sizes = []
    plot_colors = []
    
    for interaction_type in ['EP', 'PE', 'EE', 'PP']:
        if interaction_type in interaction_counts and interaction_counts[interaction_type] > 0:
            labels.append(f'{interaction_type}: {interaction_counts[interaction_type]:,} peaks')
            sizes.append(interaction_counts[interaction_type])
            plot_colors.append(colors[interaction_type])
    
    if not sizes:
        logger.warning("No interaction data to plot")
        return output_file
    
    # Create the plot
    plt.figure(figsize=(10, 8))
    
    # Create pie chart
    wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=plot_colors,
                                      autopct='%1.1f%%', startangle=90,
                                      textprops={'fontsize': 12})
    
    # Customize the plot
    plt.title('Interaction Type Statistics', fontsize=16, fontweight='bold', pad=20)
    
    # Add legend with interaction type descriptions
    legend_labels = [
        'EP: Enhancer → Promoter',
        'PE: Promoter ← Enhancer', 
        'EE: Enhancer → Enhancer',
        'PP: Promoter → Promoter'
    ]
    legend_colors = [colors[t] for t in ['EP', 'PE', 'EE', 'PP']]
    legend_patches = [mpatches.Patch(color=color, label=label) 
                     for color, label in zip(legend_colors, legend_labels)]
    
    plt.legend(handles=legend_patches, loc='center left', bbox_to_anchor=(1, 0.5),
              fontsize=11)
    
    # Equal aspect ratio ensures that pie is drawn as a circle
    plt.axis('equal')
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✅ Interaction pie chart saved → {output_file}")
    return output_file


def create_distance_distribution_plots(stats: Dict[str, any], output_file: str,
                                     logger: logging.Logger) -> str:
    """
    Create distance distribution plots.
    
    Args:
        stats: Dictionary with distance statistics
        output_file: Path for output plot file
        logger: Logger instance
        
    Returns:
        Path to output plot file
    """
    logger.info("Creating distance distribution plots...")
    
    # Create subplot layout
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Intra vs Inter-chromosomal interactions
    intra_count = stats['distance_stats']['intra_chromosomal']
    inter_count = stats['distance_stats']['inter_chromosomal']
    
    ax1.pie([intra_count, inter_count], 
           labels=[f'Intra-chromosomal\n{intra_count:,}', f'Inter-chromosomal\n{inter_count:,}'],
           autopct='%1.1f%%', colors=['#FFB6C1', '#87CEEB'])
    ax1.set_title('Chromosomal Interaction Distribution', fontweight='bold')
    
    # Plot 2: Peak distance histogram (if we had the raw data)
    # For now, show summary statistics
    peak1_stats = stats['distance_stats']['peak1_distance_stats']
    peak2_stats = stats['distance_stats']['peak2_distance_stats']
    
    categories = ['Mean', 'Median', 'Under 2kb']
    peak1_values = [peak1_stats['mean'], peak1_stats['median'], peak1_stats['under_2kb']]
    peak2_values = [peak2_stats['mean'], peak2_stats['median'], peak2_stats['under_2kb']]
    
    x = np.arange(len(categories))
    width = 0.35
    
    ax2.bar(x - width/2, peak1_values, width, label='Peak 1', color='#7DC69B')
    ax2.bar(x + width/2, peak2_values, width, label='Peak 2', color='#9BD7F3')
    ax2.set_xlabel('Distance Metrics')
    ax2.set_ylabel('Distance (bp) / Count')
    ax2.set_title('Peak Distance Statistics', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories)
    ax2.legend()
    
    # Add value labels on bars
    for i, (v1, v2) in enumerate(zip(peak1_values, peak2_values)):
        ax2.text(i - width/2, v1 + max(peak1_values + peak2_values) * 0.01, 
                f'{v1:.0f}', ha='center', va='bottom')
        ax2.text(i + width/2, v2 + max(peak1_values + peak2_values) * 0.01, 
                f'{v2:.0f}', ha='center', va='bottom')
    
    # Plot 3: Genomic distance statistics (if available)
    if stats['distance_stats']['genomic_distance_stats']['mean'] > 0:
        gd_stats = stats['distance_stats']['genomic_distance_stats']
        gd_categories = ['Mean', 'Median', 'Min', 'Max']
        gd_values = [gd_stats['mean'], gd_stats['median'], gd_stats['min'], gd_stats['max']]
        
        ax3.bar(gd_categories, gd_values, color='#D5EAD9')
        ax3.set_ylabel('Distance (bp)')
        ax3.set_title('Genomic Distance Statistics (Intra-chromosomal)', fontweight='bold')
        ax3.tick_params(axis='x', rotation=45)
        
        # Add value labels
        for i, v in enumerate(gd_values):
            ax3.text(i, v + max(gd_values) * 0.01, f'{v:,.0f}', ha='center', va='bottom')
    else:
        ax3.text(0.5, 0.5, 'No intra-chromosomal\ninteractions found', 
                ha='center', va='center', transform=ax3.transAxes, fontsize=12)
        ax3.set_title('Genomic Distance Statistics', fontweight='bold')
    
    # Plot 4: Quality metrics
    quality = stats['quality_metrics']
    completeness_data = [
        quality['peak1_distance_completeness'],
        quality['peak2_distance_completeness']
    ]
    
    ax4.bar(['Peak 1 Distance', 'Peak 2 Distance'], completeness_data, 
           color=['#FFB6C1', '#87CEEB'])
    ax4.set_ylabel('Completeness (%)')
    ax4.set_title('Data Quality Metrics', fontweight='bold')
    ax4.set_ylim(0, 100)
    
    # Add value labels
    for i, v in enumerate(completeness_data):
        ax4.text(i, v + 2, f'{v:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✅ Distance distribution plots saved → {output_file}")
    return output_file


def create_chromosome_distribution_plot(chr_stats: Dict[str, any], output_file: str,
                                      logger: logging.Logger) -> str:
    """
    Create chromosome distribution plot.
    
    Args:
        chr_stats: Dictionary with chromosome statistics
        output_file: Path for output plot file
        logger: Logger instance
        
    Returns:
        Path to output plot file
    """
    logger.info("Creating chromosome distribution plot...")
    
    # Get top chromosomes
    top_chrs = chr_stats['top_chromosomes']
    
    if not top_chrs:
        logger.warning("No chromosome data to plot")
        return output_file
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Prepare data (limit to top 20 for readability)
    chr_names = list(top_chrs.keys())[:20]
    chr_counts = [top_chrs[name] for name in chr_names]
    
    # Create bar plot
    bars = plt.bar(range(len(chr_names)), chr_counts, color='#7DC69B')
    
    # Customize the plot
    plt.xlabel('Chromosome', fontsize=12)
    plt.ylabel('Number of Interactions', fontsize=12)
    plt.title('Chromosome Distribution of Interactions (Top 20)', fontsize=14, fontweight='bold')
    plt.xticks(range(len(chr_names)), chr_names, rotation=45, ha='right')
    
    # Add value labels on bars
    for bar, count in zip(bars, chr_counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(chr_counts)*0.01,
                f'{count:,}', ha='center', va='bottom', fontsize=10)
    
    # Add grid for better readability
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✅ Chromosome distribution plot saved → {output_file}")
    return output_file


def create_comprehensive_summary_plot(stats: Dict[str, any], output_file: str,
                                    logger: logging.Logger) -> str:
    """
    Create a comprehensive multi-panel summary plot.
    
    Args:
        stats: Dictionary with comprehensive statistics
        output_file: Path for output plot file
        logger: Logger instance
        
    Returns:
        Path to output plot file
    """
    logger.info("Creating comprehensive summary plot...")
    
    # Create subplot layout
    fig = plt.figure(figsize=(16, 12))
    
    # Define grid layout
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Plot 1: Interaction type pie chart (top left)
    ax1 = fig.add_subplot(gs[0, 0])
    interaction_counts = stats['interaction_types']
    colors = {'EP': '#7DC69B', 'PE': '#9BD7F3', 'EE': '#D5EAD9', 'PP': '#D8EEFB'}
    
    labels = [f'{k}: {v:,}' for k, v in interaction_counts.items() if v > 0]
    sizes = [v for v in interaction_counts.values() if v > 0]
    plot_colors = [colors[k] for k, v in interaction_counts.items() if v > 0]
    
    if sizes:
        ax1.pie(sizes, labels=labels, colors=plot_colors, autopct='%1.1f%%', startangle=90)
    ax1.set_title('Interaction Types', fontweight='bold')
    
    # Plot 2: Chromosomal distribution (top middle)
    ax2 = fig.add_subplot(gs[0, 1])
    intra_count = stats['distance_stats']['intra_chromosomal']
    inter_count = stats['distance_stats']['inter_chromosomal']
    
    ax2.pie([intra_count, inter_count], 
           labels=[f'Intra: {intra_count:,}', f'Inter: {inter_count:,}'],
           autopct='%1.1f%%', colors=['#FFB6C1', '#87CEEB'])
    ax2.set_title('Chromosomal Distribution', fontweight='bold')
    
    # Plot 3: Quality metrics (top right)
    ax3 = fig.add_subplot(gs[0, 2])
    quality = stats['quality_metrics']
    completeness_data = [
        quality['peak1_distance_completeness'],
        quality['peak2_distance_completeness']
    ]
    
    bars3 = ax3.bar(['Peak 1', 'Peak 2'], completeness_data, color=['#7DC69B', '#9BD7F3'])
    ax3.set_ylabel('Completeness (%)')
    ax3.set_title('Data Quality', fontweight='bold')
    ax3.set_ylim(0, 100)
    
    for bar, value in zip(bars3, completeness_data):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{value:.1f}%', ha='center', va='bottom')
    
    # Plot 4: Top chromosomes (middle row)
    ax4 = fig.add_subplot(gs[1, :])
    top_chrs = stats['chromosome_distribution']['top_chromosomes']
    chr_names = list(top_chrs.keys())[:15]  # Top 15 chromosomes
    chr_counts = [top_chrs[name] for name in chr_names]
    
    bars4 = ax4.bar(range(len(chr_names)), chr_counts, color='#D5EAD9')
    ax4.set_xlabel('Chromosome')
    ax4.set_ylabel('Interactions')
    ax4.set_title('Top Chromosomes by Interaction Count', fontweight='bold')
    ax4.set_xticks(range(len(chr_names)))
    ax4.set_xticklabels(chr_names, rotation=45, ha='right')
    
    # Add value labels on top chromosomes
    for i, (bar, count) in enumerate(zip(bars4, chr_counts)):
        if i < 5:  # Only label top 5 to avoid clutter
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(chr_counts)*0.01,
                    f'{count:,}', ha='center', va='bottom', fontsize=9)
    
    # Plot 5: Distance statistics (bottom left)
    ax5 = fig.add_subplot(gs[2, 0])
    peak1_stats = stats['distance_stats']['peak1_distance_stats']
    peak2_stats = stats['distance_stats']['peak2_distance_stats']
    
    categories = ['Mean', 'Median']
    peak1_values = [peak1_stats['mean'], peak1_stats['median']]
    peak2_values = [peak2_stats['mean'], peak2_stats['median']]
    
    x = np.arange(len(categories))
    width = 0.35
    
    ax5.bar(x - width/2, peak1_values, width, label='Peak 1', color='#7DC69B')
    ax5.bar(x + width/2, peak2_values, width, label='Peak 2', color='#9BD7F3')
    ax5.set_xlabel('Distance Metrics')
    ax5.set_ylabel('Distance (bp)')
    ax5.set_title('Peak Distance Statistics', fontweight='bold')
    ax5.set_xticks(x)
    ax5.set_xticklabels(categories)
    ax5.legend()
    
    # Plot 6: Basic statistics (bottom middle)
    ax6 = fig.add_subplot(gs[2, 1])
    basic = stats['basic_stats']
    basic_labels = ['Total\nInteractions', 'Unique\nLoci']
    basic_values = [basic['total_interactions'], basic['unique_loci']]
    
    bars6 = ax6.bar(basic_labels, basic_values, color=['#FFB6C1', '#87CEEB'])
    ax6.set_ylabel('Count')
    ax6.set_title('Basic Statistics', fontweight='bold')
    
    for bar, value in zip(bars6, basic_values):
        ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(basic_values)*0.01,
                f'{value:,}', ha='center', va='bottom')
    
    # Plot 7: Distance filtering results (bottom right)
    ax7 = fig.add_subplot(gs[2, 2])
    under_2kb_p1 = stats['distance_stats']['peak1_distance_stats']['under_2kb']
    under_2kb_p2 = stats['distance_stats']['peak2_distance_stats']['under_2kb']
    total_p1 = stats['distance_stats']['peak1_distance_stats']['total_valid']
    total_p2 = stats['distance_stats']['peak2_distance_stats']['total_valid']
    
    over_2kb_p1 = total_p1 - under_2kb_p1
    over_2kb_p2 = total_p2 - under_2kb_p2
    
    categories = ['Peak 1', 'Peak 2']
    under_2kb = [under_2kb_p1, under_2kb_p2]
    over_2kb = [over_2kb_p1, over_2kb_p2]
    
    ax7.bar(categories, under_2kb, label='< 2kb', color='#7DC69B')
    ax7.bar(categories, over_2kb, bottom=under_2kb, label='≥ 2kb', color='#D5EAD9')
    ax7.set_ylabel('Count')
    ax7.set_title('Distance Filtering (2kb)', fontweight='bold')
    ax7.legend()
    
    # Add main title
    fig.suptitle('EP_annotator - Comprehensive Analysis Summary', 
                fontsize=16, fontweight='bold', y=0.98)
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✅ Comprehensive summary plot saved → {output_file}")
    return output_file


def create_all_visualizations(stats: Dict[str, any], output_prefix: str, 
                            logger: logging.Logger) -> Dict[str, str]:
    """
    Create all visualization plots.
    
    Args:
        stats: Dictionary with comprehensive statistics
        output_prefix: Prefix for output files
        logger: Logger instance
        
    Returns:
        Dictionary with output file paths
    """
    logger.info("Creating all visualization plots...")
    
    output_files = {}
    
    try:
        # 1. Interaction type pie chart (as specified in command_log.txt)
        pie_file = f"{output_prefix}_interaction_pie.png"
        output_files['pie_chart'] = create_interaction_pie_chart(
            stats['interaction_types'], pie_file, logger)
        
        # 2. Distance distribution plots
        distance_file = f"{output_prefix}_distance_analysis.png"
        output_files['distance_plots'] = create_distance_distribution_plots(
            stats, distance_file, logger)
        
        # 3. Chromosome distribution plot
        chr_file = f"{output_prefix}_chromosome_distribution.png"
        output_files['chromosome_plot'] = create_chromosome_distribution_plot(
            stats['chromosome_distribution'], chr_file, logger)
        
        # 4. Comprehensive summary plot
        summary_file = f"{output_prefix}_comprehensive_summary.png"
        output_files['summary_plot'] = create_comprehensive_summary_plot(
            stats, summary_file, logger)
        
        logger.info("✅ All visualizations created successfully")
        
    except Exception as e:
        logger.error(f"Error creating visualizations: {e}")
        raise
    
    return output_files


def main():
    """CLI entry point for creating interaction pie chart."""
    parser = argparse.ArgumentParser(
        description="Create interaction type pie chart visualization"
    )
    parser.add_argument("--ep", type=int, default=0, help="Number of EP interactions")
    parser.add_argument("--pe", type=int, default=0, help="Number of PE interactions")
    parser.add_argument("--ee", type=int, default=0, help="Number of EE interactions")
    parser.add_argument("--pp", type=int, default=0, help="Number of PP interactions")
    parser.add_argument("-o", "--output", default="interaction_pie.png",
                       help="Output file path")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    # Create interaction counts dictionary
    interaction_counts = {
        'EP': args.ep,
        'PE': args.pe,
        'EE': args.ee,
        'PP': args.pp
    }
    
    # Create pie chart
    create_interaction_pie_chart(interaction_counts, args.output, logger)
    
    logger.info("✅ Pie chart creation complete!")


if __name__ == "__main__":
    main() 
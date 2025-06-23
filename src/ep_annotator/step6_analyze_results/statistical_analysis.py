#!/usr/bin/env python3
"""
Statistical Analysis Module for EP Interaction Results

This module provides advanced statistical analysis functions for 
enhancer-promoter interaction data, including:
- Distance distribution analysis
- Interaction strength statistics
- Gene set enrichment analysis
- Comparative analysis between different peak sets
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

# Optional scipy import
try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def load_bedpe_data(bedpe_file: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Load BEDPE data with interaction labels.
    
    Args:
        bedpe_file: Path to labeled BEDPE file (can be gzipped)
        logger: Logger instance
        
    Returns:
        DataFrame with interaction data
    """
    logger.info(f"Loading BEDPE data from {bedpe_file}")
    
    try:
        if bedpe_file.endswith('.gz'):
            with gzip.open(bedpe_file, 'rt') as f:
                df = pd.read_csv(f, sep='\t', header=None)
        else:
            df = pd.read_csv(bedpe_file, sep='\t', header=None)
        
        # Standard BEDPE columns + additional annotation columns
        expected_cols = [
            'chr1', 'start1', 'end1', 'chr2', 'start2', 'end2',
            'peak1_chr', 'peak1_dist', 'peak2_chr', 'peak2_dist',
            'peak1_closest', 'peak2_closest', 'label1', 'label2', 'interaction_type'
        ]
        
        if len(df.columns) >= 15:
            df.columns = expected_cols[:len(df.columns)]
        else:
            logger.warning(f"Expected at least 15 columns, got {len(df.columns)}")
            
        logger.info(f"Loaded {len(df):,} interactions")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load BEDPE data: {e}")
        raise


def analyze_distance_distribution(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, any]:
    """
    Analyze distance distribution of interactions.
    
    Args:
        df: DataFrame with interaction data
        logger: Logger instance
        
    Returns:
        Dictionary with distance statistics
    """
    logger.info("Analyzing distance distributions...")
    
    # Calculate genomic distances for intra-chromosomal interactions
    intra_chr = df[df['chr1'] == df['chr2']].copy()
    intra_chr['genomic_distance'] = abs(intra_chr['start2'] - intra_chr['start1'])
    
    # Calculate peak distances
    peak1_dists = pd.to_numeric(df['peak1_dist'], errors='coerce').dropna()
    peak2_dists = pd.to_numeric(df['peak2_dist'], errors='coerce').dropna()
    
    stats_dict = {
        'total_interactions': len(df),
        'intra_chromosomal': len(intra_chr),
        'inter_chromosomal': len(df) - len(intra_chr),
        'genomic_distance_stats': {
            'mean': intra_chr['genomic_distance'].mean() if len(intra_chr) > 0 else 0,
            'median': intra_chr['genomic_distance'].median() if len(intra_chr) > 0 else 0,
            'std': intra_chr['genomic_distance'].std() if len(intra_chr) > 0 else 0,
            'min': intra_chr['genomic_distance'].min() if len(intra_chr) > 0 else 0,
            'max': intra_chr['genomic_distance'].max() if len(intra_chr) > 0 else 0
        },
        'peak1_distance_stats': {
            'mean': peak1_dists.mean(),
            'median': peak1_dists.median(),
            'std': peak1_dists.std(),
            'under_2kb': (peak1_dists < 2000).sum(),
            'total_valid': len(peak1_dists)
        },
        'peak2_distance_stats': {
            'mean': peak2_dists.mean(),
            'median': peak2_dists.median(),
            'std': peak2_dists.std(),
            'under_2kb': (peak2_dists < 2000).sum(),
            'total_valid': len(peak2_dists)
        }
    }
    
    logger.info("=== Distance Distribution Analysis ===")
    logger.info(f"Total interactions: {stats_dict['total_interactions']:,}")
    logger.info(f"Intra-chromosomal: {stats_dict['intra_chromosomal']:,}")
    logger.info(f"Inter-chromosomal: {stats_dict['inter_chromosomal']:,}")
    
    if len(intra_chr) > 0:
        logger.info(f"Genomic distance - Mean: {stats_dict['genomic_distance_stats']['mean']:.0f} bp")
        logger.info(f"Genomic distance - Median: {stats_dict['genomic_distance_stats']['median']:.0f} bp")
    
    logger.info(f"Peak1 distances under 2kb: {stats_dict['peak1_distance_stats']['under_2kb']:,}")
    logger.info(f"Peak2 distances under 2kb: {stats_dict['peak2_distance_stats']['under_2kb']:,}")
    
    return stats_dict


def analyze_interaction_types(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, int]:
    """
    Analyze interaction types (EP, PE, EE, PP).
    
    Args:
        df: DataFrame with interaction data
        logger: Logger instance
        
    Returns:
        Dictionary with interaction type counts
    """
    logger.info("Analyzing interaction types...")
    
    # Count interaction types
    if 'interaction_type' in df.columns:
        type_counts = df['interaction_type'].value_counts().to_dict()
    else:
        # Fallback: infer from label columns
        type_counts = {'EP': 0, 'PE': 0, 'EE': 0, 'PP': 0}
        
        for _, row in df.iterrows():
            label1 = str(row.get('label1', ''))
            label2 = str(row.get('label2', ''))
            
            if 'E' in label1 and 'P' in label2:
                type_counts['EP'] += 1
            elif 'P' in label1 and 'E' in label2:
                type_counts['PE'] += 1
            elif 'E' in label1 and 'E' in label2:
                type_counts['EE'] += 1
            elif 'P' in label1 and 'P' in label2:
                type_counts['PP'] += 1
    
    logger.info("=== Interaction Type Statistics ===")
    for int_type, count in type_counts.items():
        logger.info(f"{int_type}: {count:,} interactions")
    
    return type_counts


def analyze_chromosome_distribution(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, any]:
    """
    Analyze chromosome distribution of interactions.
    
    Args:
        df: DataFrame with interaction data
        logger: Logger instance
        
    Returns:
        Dictionary with chromosome statistics
    """
    logger.info("Analyzing chromosome distribution...")
    
    # Count interactions per chromosome
    chr1_counts = df['chr1'].value_counts()
    chr2_counts = df['chr2'].value_counts()
    
    # Combine counts
    all_chrs = set(chr1_counts.index) | set(chr2_counts.index)
    chr_total_counts = {}
    
    for chr_name in all_chrs:
        count1 = chr1_counts.get(chr_name, 0)
        count2 = chr2_counts.get(chr_name, 0)
        chr_total_counts[chr_name] = count1 + count2
    
    # Sort by chromosome name (natural sort)
    def chr_sort_key(chr_name):
        # Convert to string if it's not already
        chr_name_str = str(chr_name)
        if chr_name_str.startswith('chr'):
            chr_name_str = chr_name_str[3:]
        if chr_name_str.isdigit():
            return (0, int(chr_name_str))
        elif chr_name_str in ['X', 'Y']:
            return (1, ord(chr_name_str))
        else:
            return (2, chr_name_str)
    
    sorted_chrs = sorted(chr_total_counts.keys(), key=chr_sort_key)
    
    chr_stats = {
        'chromosome_counts': {chr_name: chr_total_counts[chr_name] for chr_name in sorted_chrs},
        'top_chromosomes': dict(sorted(chr_total_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        'total_chromosomes': len(all_chrs)
    }
    
    logger.info(f"Total chromosomes involved: {chr_stats['total_chromosomes']}")
    logger.info("Top 5 chromosomes by interaction count:")
    for i, (chr_name, count) in enumerate(list(chr_stats['top_chromosomes'].items())[:5]):
        logger.info(f"  {i+1}. {chr_name}: {count:,} interactions")
    
    return chr_stats


def calculate_interaction_statistics(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, any]:
    """
    Calculate comprehensive interaction statistics.
    
    Args:
        df: DataFrame with interaction data
        logger: Logger instance
        
    Returns:
        Dictionary with comprehensive statistics
    """
    logger.info("Calculating comprehensive interaction statistics...")
    
    # Basic statistics
    total_interactions = len(df)
    
    # Distance analysis
    distance_stats = analyze_distance_distribution(df, logger)
    
    # Interaction type analysis
    type_stats = analyze_interaction_types(df, logger)
    
    # Chromosome distribution
    chr_stats = analyze_chromosome_distribution(df, logger)
    
    # Quality metrics
    valid_peak1_dist = pd.to_numeric(df['peak1_dist'], errors='coerce').notna().sum()
    valid_peak2_dist = pd.to_numeric(df['peak2_dist'], errors='coerce').notna().sum()
    
    quality_stats = {
        'valid_peak1_distances': valid_peak1_dist,
        'valid_peak2_distances': valid_peak2_dist,
        'peak1_distance_completeness': valid_peak1_dist / total_interactions * 100,
        'peak2_distance_completeness': valid_peak2_dist / total_interactions * 100
    }
    
    # Combine all statistics
    comprehensive_stats = {
        'basic_stats': {
            'total_interactions': total_interactions,
            'unique_loci': len(set(zip(df['chr1'], df['start1'])) | set(zip(df['chr2'], df['start2'])))
        },
        'distance_stats': distance_stats,
        'interaction_types': type_stats,
        'chromosome_distribution': chr_stats,
        'quality_metrics': quality_stats
    }
    
    logger.info("✅ Comprehensive statistics calculated")
    return comprehensive_stats


def export_statistics_report(stats: Dict[str, any], output_file: str, logger: logging.Logger) -> str:
    """
    Export comprehensive statistics to a detailed report.
    
    Args:
        stats: Dictionary with comprehensive statistics
        output_file: Path for output report file
        logger: Logger instance
        
    Returns:
        Path to output report file
    """
    logger.info("Generating comprehensive statistics report...")
    
    with open(output_file, 'w') as f:
        f.write("EP_annotator - Comprehensive Interaction Statistics Report\n")
        f.write("=" * 60 + "\n\n")
        
        # Basic statistics
        f.write("BASIC STATISTICS\n")
        f.write("-" * 30 + "\n")
        basic = stats['basic_stats']
        f.write(f"Total interactions: {basic['total_interactions']:,}\n")
        f.write(f"Unique genomic loci: {basic['unique_loci']:,}\n\n")
        
        # Distance statistics
        f.write("DISTANCE ANALYSIS\n")
        f.write("-" * 30 + "\n")
        dist = stats['distance_stats']
        f.write(f"Intra-chromosomal interactions: {dist['intra_chromosomal']:,}\n")
        f.write(f"Inter-chromosomal interactions: {dist['inter_chromosomal']:,}\n")
        
        if dist['genomic_distance_stats']['mean'] > 0:
            gd = dist['genomic_distance_stats']
            f.write(f"Genomic distance (intra-chr):\n")
            f.write(f"  Mean: {gd['mean']:,.0f} bp\n")
            f.write(f"  Median: {gd['median']:,.0f} bp\n")
            f.write(f"  Std: {gd['std']:,.0f} bp\n")
            f.write(f"  Range: {gd['min']:,.0f} - {gd['max']:,.0f} bp\n")
        
        p1 = dist['peak1_distance_stats']
        p2 = dist['peak2_distance_stats']
        f.write(f"Peak distances:\n")
        f.write(f"  Peak1 - Mean: {p1['mean']:.0f} bp, Under 2kb: {p1['under_2kb']:,}\n")
        f.write(f"  Peak2 - Mean: {p2['mean']:.0f} bp, Under 2kb: {p2['under_2kb']:,}\n\n")
        
        # Interaction types
        f.write("INTERACTION TYPES\n")
        f.write("-" * 30 + "\n")
        total = sum(stats['interaction_types'].values())
        for int_type, count in stats['interaction_types'].items():
            percentage = count / total * 100 if total > 0 else 0
            f.write(f"{int_type}: {count:,} ({percentage:.1f}%)\n")
        f.write("\n")
        
        # Chromosome distribution
        f.write("CHROMOSOME DISTRIBUTION\n")
        f.write("-" * 30 + "\n")
        chr_dist = stats['chromosome_distribution']
        f.write(f"Total chromosomes involved: {chr_dist['total_chromosomes']}\n")
        f.write("Top 10 chromosomes by interaction count:\n")
        for i, (chr_name, count) in enumerate(list(chr_dist['top_chromosomes'].items())[:10]):
            f.write(f"  {i+1:2d}. {chr_name}: {count:,}\n")
        f.write("\n")
        
        # Quality metrics
        f.write("QUALITY METRICS\n")
        f.write("-" * 30 + "\n")
        quality = stats['quality_metrics']
        f.write(f"Valid peak1 distances: {quality['valid_peak1_distances']:,} ({quality['peak1_distance_completeness']:.1f}%)\n")
        f.write(f"Valid peak2 distances: {quality['valid_peak2_distances']:,} ({quality['peak2_distance_completeness']:.1f}%)\n")
        
        f.write(f"\nReport generated by EP_annotator step 6\n")
    
    logger.info(f"✅ Comprehensive report saved → {output_file}")
    return output_file


def main():
    """CLI entry point for statistical analysis."""
    parser = argparse.ArgumentParser(
        description="Perform comprehensive statistical analysis of EP interactions"
    )
    parser.add_argument("bedpe_file",
                       help="Path to labeled BEDPE file")
    parser.add_argument("-o", "--output-prefix", default=None,
                       help="Prefix for output files (auto-generated if not provided)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    # Auto-generate output prefix if not provided
    if args.output_prefix is None:
        input_stem = Path(args.bedpe_file).stem
        if input_stem.endswith('.promLabel.bedpe'):
            input_stem = input_stem.replace('.promLabel.bedpe', '')
        args.output_prefix = f"{input_stem}_statistics"
    
    # Load data
    df = load_bedpe_data(args.bedpe_file, logger)
    
    # Calculate statistics
    stats = calculate_interaction_statistics(df, logger)
    
    # Export report
    report_file = f"{args.output_prefix}_comprehensive_report.txt"
    export_statistics_report(stats, report_file, logger)
    
    logger.info("✅ Statistical analysis complete!")


if __name__ == "__main__":
    main() 
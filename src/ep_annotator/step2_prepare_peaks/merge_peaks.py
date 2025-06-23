#!/usr/bin/env python3
"""
Merge and process H3K27Ac CUT&Tag peak data.

This module handles the merging of multiple H3K27Ac CUT&Tag BED files,
standardizes the format, sorts peaks, and merges overlapping regions.
"""

import os
import subprocess
import tempfile
from pathlib import Path
import logging

# Import pandas only when needed
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def merge_peak_files(peak_files, output_prefix, merge_overlapping=True, sort_peaks=True):
    """
    Merge multiple H3K27Ac CUT&Tag BED files into a single standardized BED file.
    
    Args:
        peak_files (list): List of paths to H3K27Ac CUT&Tag BED files
        output_prefix (str): Prefix for output files
        merge_overlapping (bool): Whether to merge overlapping peaks
        sort_peaks (bool): Whether to sort the peaks
        
    Returns:
        str: Path to the merged output file
    """
    logger.info(f"Processing {len(peak_files)} H3K27Ac peak files")
    
    # Validate input files
    for file_path in peak_files:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Peak file not found: {file_path}")
    
    output_file = f"{output_prefix}_H3K27ac_CUTTAG_union.bed"
    
    try:
        # Build the command following the original workflow
        file_list = " ".join(peak_files)
        
        if merge_overlapping and sort_peaks:
            # Full processing: cat + awk + bedtools sort + bedtools merge
            cmd = f"""
            cat {file_list} | \
            awk 'BEGIN{{OFS="\\t"}}{{print $1,$2,$3}}' | \
            bedtools sort -i - | \
            bedtools merge -i - > {output_file}
            """
        elif sort_peaks:
            # Sort only, no merge
            cmd = f"""
            cat {file_list} | \
            awk 'BEGIN{{OFS="\\t"}}{{print $1,$2,$3}}' | \
            bedtools sort -i - > {output_file}
            """
        else:
            # Just concatenate and format
            cmd = f"""
            cat {file_list} | \
            awk 'BEGIN{{OFS="\\t"}}{{print $1,$2,$3}}' > {output_file}
            """
        
        logger.info("Running H3K27Ac peak processing command...")
        logger.debug(f"Command: {cmd}")
        
        # Execute the command
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully created: {output_file}")
            
            # Count lines for verification
            line_count = count_lines(output_file)
            logger.info(f"Output contains {line_count:,} peaks")
            
            return output_file
        else:
            raise RuntimeError(f"Command failed with error: {result.stderr}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to process peak files: {e}")
        logger.error(f"Command output: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


def merge_peak_files_python(peak_files, output_prefix, merge_overlapping=True, sort_peaks=True):
    """
    Pure Python implementation for merging peak files (alternative to bedtools).
    
    Args:
        peak_files (list): List of paths to H3K27Ac CUT&Tag BED files
        output_prefix (str): Prefix for output files
        merge_overlapping (bool): Whether to merge overlapping peaks
        sort_peaks (bool): Whether to sort the peaks
        
    Returns:
        str: Path to the merged output file
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for Python implementation. Install with: pip install pandas")
        
    logger.info(f"Processing {len(peak_files)} H3K27Ac peak files (Python implementation)")
    
    # Validate input files
    for file_path in peak_files:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Peak file not found: {file_path}")
    
    output_file = f"{output_prefix}_H3K27ac_CUTTAG_union.bed"
    
    try:
        # Read and concatenate all peak files
        all_peaks = []
        for file_path in peak_files:
            logger.debug(f"Reading {file_path}")
            df = pd.read_csv(file_path, sep='\t', header=None, 
                           usecols=[0, 1, 2], names=['chr', 'start', 'end'])
            all_peaks.append(df)
        
        # Concatenate all dataframes
        combined_df = pd.concat(all_peaks, ignore_index=True)
        logger.info(f"Combined {len(combined_df):,} peaks from {len(peak_files)} files")
        
        # Sort if requested
        if sort_peaks:
            logger.info("Sorting peaks...")
            combined_df = combined_df.sort_values(['chr', 'start', 'end'])
        
        # Merge overlapping peaks if requested
        if merge_overlapping:
            logger.info("Merging overlapping peaks...")
            combined_df = merge_overlapping_intervals(combined_df)
            logger.info(f"After merging: {len(combined_df):,} peaks")
        
        # Write output
        combined_df.to_csv(output_file, sep='\t', header=False, index=False)
        logger.info(f"Successfully created: {output_file}")
        
        return output_file
        
    except Exception as e:
        logger.error(f"Failed to process peak files: {e}")
        raise


def merge_overlapping_intervals(df):
    """
    Merge overlapping intervals in a pandas DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with columns ['chr', 'start', 'end']
        
    Returns:
        pd.DataFrame: DataFrame with merged intervals
    """
    merged_intervals = []
    
    # Group by chromosome
    for chr_name, chr_group in df.groupby('chr'):
        # Sort by start position
        chr_group = chr_group.sort_values(['start', 'end'])
        
        intervals = []
        current_start = None
        current_end = None
        
        for _, row in chr_group.iterrows():
            start, end = row['start'], row['end']
            
            if current_start is None:
                # First interval
                current_start, current_end = start, end
            elif start <= current_end:
                # Overlapping interval, extend the current one
                current_end = max(current_end, end)
            else:
                # Non-overlapping interval, save the current one and start a new one
                intervals.append([chr_name, current_start, current_end])
                current_start, current_end = start, end
        
        # Add the last interval
        if current_start is not None:
            intervals.append([chr_name, current_start, current_end])
        
        merged_intervals.extend(intervals)
    
    return pd.DataFrame(merged_intervals, columns=['chr', 'start', 'end'])


def count_lines(file_path):
    """Count lines in a file efficiently."""
    try:
        result = subprocess.run(['wc', '-l', file_path], 
                              capture_output=True, text=True, check=True)
        return int(result.stdout.split()[0])
    except:
        # Fallback method
        with open(file_path, 'r') as f:
            return sum(1 for _ in f)


def validate_bed_format(file_path, sample_lines=10):
    """
    Validate that the output file has correct BED format.
    
    Args:
        file_path (str): Path to BED file to validate
        sample_lines (int): Number of lines to check
        
    Returns:
        bool: True if format is valid
    """
    try:
        with open(file_path, 'r') as f:
            for i, line in enumerate(f):
                if i >= sample_lines:
                    break
                
                fields = line.strip().split('\t')
                if len(fields) < 3:
                    logger.warning(f"Line {i+1} has fewer than 3 fields: {line.strip()}")
                    return False
                
                # Check if coordinates are numeric
                try:
                    int(fields[1])  # start
                    int(fields[2])  # end
                except ValueError:
                    logger.warning(f"Line {i+1} has non-numeric coordinates: {line.strip()}")
                    return False
                
                # Check if start < end
                if int(fields[1]) >= int(fields[2]):
                    logger.warning(f"Line {i+1} has start >= end: {line.strip()}")
                    return False
        
        logger.info("BED format validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Failed to validate BED format: {e}")
        return False


def process_peak_data(peak_files, output_prefix, use_bedtools=True, **kwargs):
    """
    Main function to process H3K27Ac peak data.
    
    This is a wrapper function that calls the appropriate merge function.
    
    Args:
        peak_files (list): List of H3K27Ac CUT&Tag BED files
        output_prefix (str): Prefix for output files
        use_bedtools (bool): Whether to use bedtools (True) or pure Python (False)
        **kwargs: Additional parameters (merge_overlapping, sort_peaks, etc.)
        
    Returns:
        str: Path to processed peak file
    """
    logger.info("Starting H3K27Ac peak data processing...")
    
    # Set default parameters
    params = {
        'merge_overlapping': kwargs.get('merge_overlapping', True),
        'sort_peaks': kwargs.get('sort_peaks', True)
    }
    
    # Choose implementation
    if use_bedtools:
        output_file = merge_peak_files(peak_files, output_prefix, **params)
    else:
        output_file = merge_peak_files_python(peak_files, output_prefix, **params)
    
    # Validate output
    if validate_bed_format(output_file):
        logger.info("H3K27Ac peak data processing completed successfully")
        return output_file
    else:
        raise RuntimeError("Output file failed validation")


if __name__ == "__main__":
    # Example usage for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Merge H3K27Ac peak files")
    parser.add_argument("--input", nargs="+", required=True,
                       help="Input H3K27Ac CUT&Tag BED files")
    parser.add_argument("--output-prefix", required=True,
                       help="Output file prefix")
    parser.add_argument("--no-merge", action="store_false", dest="merge_overlapping",
                       help="Skip overlapping peak merge")
    parser.add_argument("--no-sort", action="store_false", dest="sort_peaks",
                       help="Skip sorting")
    parser.add_argument("--python-only", action="store_false", dest="use_bedtools",
                       help="Use pure Python implementation (no bedtools)")
    
    args = parser.parse_args()
    
    try:
        output_file = process_peak_data(
            args.input, 
            args.output_prefix,
            use_bedtools=args.use_bedtools,
            merge_overlapping=args.merge_overlapping,
            sort_peaks=args.sort_peaks
        )
        print(f"Successfully created: {output_file}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1) 
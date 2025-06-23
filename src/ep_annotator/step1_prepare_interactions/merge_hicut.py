#!/usr/bin/env python3
"""
Merge and process HiCUT interaction data.

This module handles the merging of multiple HiCUT allValidPairs files,
standardizes the format, removes duplicates, and sorts the output.
"""

import os
import subprocess
import tempfile
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def merge_hicut_files(hicut_files, output_prefix, remove_duplicates=True, sort_output=True):
    """
    Merge multiple HiCUT allValidPairs files into a single standardized BEDPE file.
    
    Args:
        hicut_files (list): List of paths to HiCUT allValidPairs files
        output_prefix (str): Prefix for output files
        remove_duplicates (bool): Whether to remove duplicate interactions
        sort_output (bool): Whether to sort the output
        
    Returns:
        str: Path to the merged output file
    """
    logger.info(f"Processing {len(hicut_files)} HiCUT files")
    
    # Validate input files
    for file_path in hicut_files:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"HiCUT file not found: {file_path}")
    
    output_file = f"{output_prefix}_HiCUT_union.bedpe"
    
    # Create AWK script for processing HiCUT data
    awk_script = """
    # Convert each line to chrA posA chrB posB (ensuring A < B order)
    {
        chr1=$2; pos1=$3; chr2=$5; pos2=$6
        # Compare chromosome first, then coordinates to ensure unique order
        if (chr1 < chr2 || (chr1==chr2 && pos1 < pos2)) {
            print chr1"\\t"pos1"\\t"chr2"\\t"pos2
        } else {
            print chr2"\\t"pos2"\\t"chr1"\\t"pos1
        }
    }
    """
    
    try:
        # Build the command
        file_list = " ".join(hicut_files)
        
        if remove_duplicates and sort_output:
            # Original command from log: process, sort, and remove duplicates
            cmd = f"""
            awk '{awk_script}' {file_list} | \
            sort -k1,1 -k2,2n -k3,3 -k4,4n | \
            uniq > {output_file}
            """
        elif sort_output:
            # Sort only
            cmd = f"""
            awk '{awk_script}' {file_list} | \
            sort -k1,1 -k2,2n -k3,3 -k4,4n > {output_file}
            """
        else:
            # Process only
            cmd = f"""
            awk '{awk_script}' {file_list} > {output_file}
            """
        
        logger.info("Running HiCUT processing command...")
        logger.debug(f"Command: {cmd}")
        
        # Execute the command
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully created: {output_file}")
            
            # Count lines for verification
            line_count = count_lines(output_file)
            logger.info(f"Output contains {line_count:,} interactions")
            
            return output_file
        else:
            raise RuntimeError(f"Command failed with error: {result.stderr}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to process HiCUT files: {e}")
        logger.error(f"Command output: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


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


def validate_bedpe_format(file_path, sample_lines=10):
    """
    Validate that the output file has correct BEDPE format.
    
    Args:
        file_path (str): Path to BEDPE file to validate
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
                if len(fields) < 4:
                    logger.warning(f"Line {i+1} has fewer than 4 fields: {line.strip()}")
                    return False
                
                # Check if coordinates are numeric
                try:
                    int(fields[1])  # pos1
                    int(fields[3])  # pos2
                except ValueError:
                    logger.warning(f"Line {i+1} has non-numeric coordinates: {line.strip()}")
                    return False
        
        logger.info("BEDPE format validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Failed to validate BEDPE format: {e}")
        return False


def process_hicut_data(hicut_files, output_prefix, **kwargs):
    """
    Main function to process HiCUT interaction data.
    
    This is a wrapper function that calls merge_hicut_files with validation.
    
    Args:
        hicut_files (list): List of HiCUT allValidPairs files
        output_prefix (str): Prefix for output files
        **kwargs: Additional parameters (remove_duplicates, sort_output, etc.)
        
    Returns:
        str: Path to processed interaction file
    """
    logger.info("Starting HiCUT data processing...")
    
    # Set default parameters
    params = {
        'remove_duplicates': kwargs.get('remove_duplicates', True),
        'sort_output': kwargs.get('sort_output', True)
    }
    
    # Process the files
    output_file = merge_hicut_files(hicut_files, output_prefix, **params)
    
    # Validate output
    if validate_bedpe_format(output_file):
        logger.info("HiCUT data processing completed successfully")
        return output_file
    else:
        raise RuntimeError("Output file failed validation")


if __name__ == "__main__":
    # Example usage for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Merge HiCUT interaction files")
    parser.add_argument("--input", nargs="+", required=True,
                       help="Input HiCUT allValidPairs files")
    parser.add_argument("--output-prefix", required=True,
                       help="Output file prefix")
    parser.add_argument("--no-duplicates", action="store_false", dest="remove_duplicates",
                       help="Skip duplicate removal")
    parser.add_argument("--no-sort", action="store_false", dest="sort_output",
                       help="Skip sorting")
    
    args = parser.parse_args()
    
    try:
        output_file = process_hicut_data(
            args.input, 
            args.output_prefix,
            remove_duplicates=args.remove_duplicates,
            sort_output=args.sort_output
        )
        print(f"Successfully created: {output_file}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1) 
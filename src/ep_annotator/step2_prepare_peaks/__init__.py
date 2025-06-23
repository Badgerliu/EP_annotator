"""
Step 2: Prepare H3K27Ac Peak Data

This module handles the preparation and processing of H3K27Ac CUT&Tag peak data.
Functions include merging multiple samples, sorting peaks, and merging overlapping regions.
"""

from .merge_peaks import merge_peak_files, merge_peak_files_python, process_peak_data, validate_bed_format
import subprocess
import os
from pathlib import Path

__all__ = [
    'merge_peak_files',
    'merge_peak_files_python',
    'process_peak_data',
    'validate_bed_format',
    'prepare_peaks',
    'run_peak_shell_script'
]

def prepare_peaks(peak_files, output_prefix, **kwargs):
    """
    Main function to prepare H3K27Ac peak data.
    
    Args:
        peak_files (list): List of H3K27Ac CUT&Tag BED files
        output_prefix (str): Prefix for output files
        **kwargs: Additional parameters
        
    Returns:
        str: Path to processed peak file
    """
    return process_peak_data(peak_files, output_prefix, **kwargs)

def run_peak_shell_script(peak_files, output_prefix, **kwargs):
    """
    Run the shell script version for processing H3K27Ac peak data.
    
    Args:
        peak_files (list): List of H3K27Ac CUT&Tag BED files
        output_prefix (str): Prefix for output files
        **kwargs: Additional parameters (merge_overlapping, sort_peaks, verbose)
        
    Returns:
        str: Path to processed peak file
    """
    # Get the script path
    script_dir = Path(__file__).parent / "scripts"
    script_path = script_dir / "process_peaks.sh"
    
    if not script_path.exists():
        raise FileNotFoundError(f"Shell script not found: {script_path}")
    
    # Make script executable
    os.chmod(script_path, 0o755)
    
    # Build command arguments
    cmd = [str(script_path), "-o", output_prefix]
    
    # Add optional flags
    if not kwargs.get('merge_overlapping', True):
        cmd.append("-n")
    if not kwargs.get('sort_peaks', True):
        cmd.append("-s")
    if kwargs.get('verbose', False):
        cmd.append("-v")
    
    # Add input files
    cmd.extend(peak_files)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # The output file name is predictable
        output_file = f"{output_prefix}_H3K27ac_CUTTAG_union.bed"
        
        if os.path.exists(output_file):
            return output_file
        else:
            raise RuntimeError("Output file was not created")
            
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Shell script failed: {e.stderr}") 
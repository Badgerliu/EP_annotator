"""
Step 1: Prepare Interaction Data

This module handles the preparation and processing of HiCUT chromatin interaction data.
Functions include merging multiple HiCUT files, removing duplicates, and formatting data.
"""

from .merge_hicut import merge_hicut_files, process_hicut_data, validate_bedpe_format
import subprocess
import os
from pathlib import Path

__all__ = [
    'merge_hicut_files',
    'process_hicut_data', 
    'validate_bedpe_format',
    'prepare_interactions',
    'run_hicut_shell_script'
]

def prepare_interactions(hicut_files, output_prefix, **kwargs):
    """
    Main function to prepare HiCUT interaction data.
    
    Args:
        hicut_files (list): List of HiCUT allValidPairs files
        output_prefix (str): Prefix for output files
        **kwargs: Additional parameters
        
    Returns:
        str: Path to processed interaction file
    """
    return process_hicut_data(hicut_files, output_prefix, **kwargs)

def run_hicut_shell_script(hicut_files, output_prefix, **kwargs):
    """
    Run the shell script version for processing HiCUT data.
    
    Args:
        hicut_files (list): List of HiCUT allValidPairs files
        output_prefix (str): Prefix for output files
        **kwargs: Additional parameters (remove_duplicates, sort_output, verbose)
        
    Returns:
        str: Path to processed interaction file
    """
    # Get the script path
    script_dir = Path(__file__).parent / "scripts"
    script_path = script_dir / "process_hicut.sh"
    
    if not script_path.exists():
        raise FileNotFoundError(f"Shell script not found: {script_path}")
    
    # Make script executable
    os.chmod(script_path, 0o755)
    
    # Build command arguments
    cmd = [str(script_path), "-o", output_prefix]
    
    # Add optional flags
    if not kwargs.get('remove_duplicates', True):
        cmd.append("-n")
    if not kwargs.get('sort_output', True):
        cmd.append("-s")
    if kwargs.get('verbose', False):
        cmd.append("-v")
    
    # Add input files
    cmd.extend(hicut_files)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # The output file name is predictable
        output_file = f"{output_prefix}_HiCUT_union.bedpe"
        
        if os.path.exists(output_file):
            return output_file
        else:
            raise RuntimeError("Output file was not created")
            
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Shell script failed: {e.stderr}") 
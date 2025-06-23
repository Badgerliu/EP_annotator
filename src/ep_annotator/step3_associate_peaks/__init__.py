"""
Step 3: Associate Interactions with Peaks

This module maps chromatin interaction endpoints to H3K27Ac peaks and filters
by distance threshold to generate peak-to-peak interactions.
"""

import os
import subprocess
from typing import Optional

from .associate_peaks import associate_peaks_main


__all__ = [
    'associate_interactions_with_peaks',
    'run_association_script',
    'associate_peaks_main'
]


def associate_interactions_with_peaks(
    interaction_file: str,
    peak_file: str,
    output_file: str,
    distance_threshold: Optional[int] = None,
    method: str = "bedtools",
    verbose: bool = False
) -> str:
    """
    Associate HiCUT chromatin interactions with H3K27Ac peaks.
    
    This function finds the closest H3K27Ac peak for each endpoint of chromatin
    interactions and calculates distances. Optionally filters by distance threshold.
    
    Args:
        interaction_file (str): Path to HiCUT interaction file (4-column BEDPE format)
        peak_file (str): Path to H3K27Ac peak file (3-column BED format)
        output_file (str): Path for output file
        distance_threshold (int, optional): Maximum distance for filtering (e.g., 2000)
        method (str): Method to use - "bedtools" (default) or "python"
        verbose (bool): Enable verbose logging
        
    Returns:
        str: Path to output file
        
    Examples:
        >>> # Basic association
        >>> result = associate_interactions_with_peaks(
        ...     "interactions.bedpe", 
        ...     "peaks.bed", 
        ...     "output.bedpe"
        ... )
        
        >>> # With distance filtering
        >>> result = associate_interactions_with_peaks(
        ...     "interactions.bedpe", 
        ...     "peaks.bed", 
        ...     "output.bedpe",
        ...     distance_threshold=2000
        ... )
    """
    return associate_peaks_main(
        interaction_file=interaction_file,
        peak_file=peak_file,
        output_file=output_file,
        distance_threshold=distance_threshold,
        method=method,
        verbose=verbose
    )


def run_association_script(
    interaction_file: str,
    peak_file: str,
    output_file: str,
    distance_threshold: Optional[int] = None,
    verbose: bool = False,
    keep_temp: bool = False
) -> str:
    """
    Run the association using the shell script version.
    
    This function calls the shell script to associate interactions with peaks
    using bedtools. Provides an alternative to the Python implementation.
    
    Args:
        interaction_file (str): Path to HiCUT interaction file (4-column BEDPE format)
        peak_file (str): Path to H3K27Ac peak file (3-column BED format)
        output_file (str): Path for output file
        distance_threshold (int, optional): Maximum distance for filtering
        verbose (bool): Enable verbose logging
        keep_temp (bool): Keep temporary files for debugging
        
    Returns:
        str: Path to output file
        
    Raises:
        RuntimeError: If the shell script fails
        FileNotFoundError: If required dependencies are missing
        
    Examples:
        >>> # Basic association using shell script
        >>> result = run_association_script(
        ...     "interactions.bedpe", 
        ...     "peaks.bed", 
        ...     "output.bedpe"
        ... )
        
        >>> # With distance filtering and verbose output
        >>> result = run_association_script(
        ...     "interactions.bedpe", 
        ...     "peaks.bed", 
        ...     "output.bedpe",
        ...     distance_threshold=2000,
        ...     verbose=True
        ... )
    """
    # Get path to shell script
    script_dir = os.path.dirname(__file__)
    script_path = os.path.join(script_dir, "scripts", "associate_peaks.sh")
    
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Shell script not found: {script_path}")
    
    # Build command arguments
    cmd = [script_path, "-i", interaction_file, "-p", peak_file, "-o", output_file]
    
    if distance_threshold is not None:
        cmd.extend(["-d", str(distance_threshold)])
    
    if verbose:
        cmd.append("-v")
    
    if keep_temp:
        cmd.append("-k")
    
    # Execute the script
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return output_file
    except subprocess.CalledProcessError as e:
        error_msg = f"Shell script failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f"\nError output: {e.stderr}"
        if e.stdout:
            error_msg += f"\nStandard output: {e.stdout}"
        raise RuntimeError(error_msg)


def associate_peaks(
    interaction_file: str, 
    peak_file: str, 
    output_prefix: str, 
    distance_threshold: Optional[int] = None, 
    **kwargs
) -> str:
    """
    Main function to associate interactions with H3K27Ac peaks.
    
    This is the legacy interface maintained for backward compatibility.
    
    Args:
        interaction_file (str): Path to processed HiCUT interaction file
        peak_file (str): Path to processed H3K27Ac peak file
        output_prefix (str): Prefix for output files (will add .bedpe extension)
        distance_threshold (int, optional): Maximum distance for association
        **kwargs: Additional parameters (method, verbose, etc.)
        
    Returns:
        str: Path to annotated interaction file
        
    Examples:
        >>> # Basic usage
        >>> result = associate_peaks(
        ...     "interactions.bedpe",
        ...     "peaks.bed", 
        ...     "output_prefix"
        ... )
        # Creates output_prefix.bedpe
        
        >>> # With distance filtering
        >>> result = associate_peaks(
        ...     "interactions.bedpe",
        ...     "peaks.bed", 
        ...     "output_prefix",
        ...     distance_threshold=2000
        ... )
        # Creates output_prefix.bedpe with filtered results
    """
    # Add .bedpe extension if not present
    if not output_prefix.endswith('.bedpe'):
        output_file = f"{output_prefix}.bedpe"
    else:
        output_file = output_prefix
    
    # Extract method preference from kwargs
    method = kwargs.get('method', 'bedtools')
    verbose = kwargs.get('verbose', False)
    
    return associate_interactions_with_peaks(
        interaction_file=interaction_file,
        peak_file=peak_file,
        output_file=output_file,
        distance_threshold=distance_threshold,
        method=method,
        verbose=verbose
    ) 
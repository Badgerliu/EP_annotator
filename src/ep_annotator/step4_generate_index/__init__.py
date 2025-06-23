"""
Step 4: Generate E-P Interaction Index

This module provides functionality to generate E-P interaction index by:
1. Creating promoter regions from RefSeq gene annotations
2. Annotating each interaction endpoint as Promoter (P) or Enhancer (E)
3. Categorizing interactions as PP, PE, EP, or EE

The module provides multiple interfaces:
- Modern Python API for direct integration
- Shell script wrapper for command-line usage
- Legacy compatibility interfaces
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union

# Import from submodules
from .generate_promoters import generate_promoters_main
from .annotate_ep import annotate_ep_main


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def generate_interaction_index(
    bedpe_file: str,
    refseq_file: Optional[str] = None,
    promoter_file: Optional[str] = None,
    output_file: Optional[str] = None,
    upstream: int = 1000,
    downstream: int = 1001,
    use_interval_tree: bool = True,
    keep_temp: bool = False,
    verbose: bool = False
) -> str:
    """
    Generate E-P interaction index from HiCUT interactions and gene annotations.
    
    This function combines promoter generation and E-P annotation to create
    a comprehensive interaction index with promoter/enhancer labels.
    
    Args:
        bedpe_file: Path to BEDPE file with interaction data (from step 3)
        refseq_file: Path to RefSeq gene annotation file (required if no promoter_file)
        promoter_file: Path to pre-generated promoter regions file
        output_file: Path for output file (auto-generated if not provided)
        upstream: Distance upstream of TSS for promoter regions (default: 1000)
        downstream: Distance downstream of TSS for promoter regions (default: 1001)
        use_interval_tree: Use IntervalTree for faster lookup (default: True)
        keep_temp: Keep temporary files for debugging (default: False)
        verbose: Enable verbose logging (default: False)
        
    Returns:
        Path to output file
        
    Raises:
        ValueError: If input parameters are invalid
        FileNotFoundError: If required input files don't exist
        RuntimeError: If processing fails
        
    Example:
        >>> # Basic usage with RefSeq file
        >>> result = generate_interaction_index(
        ...     bedpe_file="interactions.bedpe",
        ...     refseq_file="mm10_refseq.bed",
        ...     output_file="interactions_index.bedpe.gz"
        ... )
        
        >>> # Using pre-generated promoter file
        >>> result = generate_interaction_index(
        ...     bedpe_file="interactions.bedpe",
        ...     promoter_file="mm10_promoters1kb.bed",
        ...     output_file="interactions_index.bedpe.gz"
        ... )
    """
    logger = setup_logging(verbose)
    
    logger.info("Starting E-P interaction index generation...")
    logger.info(f"Input BEDPE: {bedpe_file}")
    
    # Validate inputs
    if not os.path.exists(bedpe_file):
        raise FileNotFoundError(f"BEDPE file not found: {bedpe_file}")
    
    if promoter_file is None and refseq_file is None:
        raise ValueError("Either refseq_file or promoter_file must be provided")
    
    if promoter_file and not os.path.exists(promoter_file):
        raise FileNotFoundError(f"Promoter file not found: {promoter_file}")
    
    if refseq_file and not os.path.exists(refseq_file):
        raise FileNotFoundError(f"RefSeq file not found: {refseq_file}")
    
    # Auto-generate output filename if not provided
    if output_file is None:
        base_name = bedpe_file.rsplit(".", 1)[0] if "." in bedpe_file else bedpe_file
        output_file = f"{base_name}.promLabel.bedpe.gz"
    
    # Determine promoter file to use
    temp_promoter_file = None
    final_promoter_file = promoter_file
    
    if promoter_file is None:
        # Generate promoter regions from RefSeq
        logger.info("Generating promoter regions from RefSeq...")
        temp_promoter_file = f"{bedpe_file}.temp_promoters.bed"
        final_promoter_file = generate_promoters_main(
            refseq_file=refseq_file,
            output_file=temp_promoter_file,
            upstream=upstream,
            downstream=downstream,
            verbose=verbose
        )
        logger.info(f"Generated promoter file: {final_promoter_file}")
    else:
        logger.info(f"Using provided promoter file: {final_promoter_file}")
    
    try:
        # Annotate E-P interactions
        logger.info("Annotating E-P interactions...")
        result = annotate_ep_main(
            bedpe_file=bedpe_file,
            promoter_file=final_promoter_file,
            output_file=output_file,
            use_interval_tree=use_interval_tree,
            verbose=verbose
        )
        
        logger.info(f"✅ Successfully generated interaction index: {result}")
        return result
        
    finally:
        # Clean up temporary files if requested
        if temp_promoter_file and not keep_temp:
            try:
                if os.path.exists(temp_promoter_file):
                    os.remove(temp_promoter_file)
                    logger.debug(f"Removed temporary promoter file: {temp_promoter_file}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_promoter_file}: {e}")


def run_generate_index_script(
    bedpe_file: str,
    refseq_file: Optional[str] = None,
    promoter_file: Optional[str] = None,
    output_file: Optional[str] = None,
    upstream: int = 1000,
    downstream: int = 1001,
    use_interval_tree: bool = True,
    keep_temp: bool = False,
    verbose: bool = False
) -> str:
    """
    Run the shell script version of the index generation.
    
    This function provides a wrapper around the shell script implementation,
    useful for integration with existing shell-based pipelines.
    
    Args:
        bedpe_file: Path to BEDPE file with interaction data
        refseq_file: Path to RefSeq gene annotation file
        promoter_file: Path to pre-generated promoter regions file
        output_file: Path for output file
        upstream: Distance upstream of TSS for promoter regions
        downstream: Distance downstream of TSS for promoter regions
        use_interval_tree: Use IntervalTree for faster lookup
        keep_temp: Keep temporary files for debugging
        verbose: Enable verbose logging
        
    Returns:
        Path to output file
        
    Raises:
        RuntimeError: If shell script execution fails
    """
    logger = setup_logging(verbose)
    
    # Get script path
    script_dir = Path(__file__).parent / "scripts"
    script_path = script_dir / "generate_index.sh"
    
    if not script_path.exists():
        raise FileNotFoundError(f"Shell script not found: {script_path}")
    
    # Build command
    cmd = ["bash", str(script_path)]
    
    # Required arguments
    cmd.extend(["-i", bedpe_file])
    if output_file:
        cmd.extend(["-o", output_file])
    else:
        # Auto-generate output filename
        base_name = bedpe_file.rsplit(".", 1)[0] if "." in bedpe_file else bedpe_file
        output_file = f"{base_name}.promLabel.bedpe.gz"
        cmd.extend(["-o", output_file])
    
    # Optional arguments
    if refseq_file:
        cmd.extend(["-r", refseq_file])
    if promoter_file:
        cmd.extend(["-p", promoter_file])
    
    cmd.extend(["--upstream", str(upstream)])
    cmd.extend(["--downstream", str(downstream)])
    
    if not use_interval_tree:
        cmd.append("--no-interval-tree")
    if keep_temp:
        cmd.append("--keep")
    if verbose:
        cmd.append("--verbose")
    
    logger.info(f"Running shell script: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        logger.info("Shell script completed successfully")
        if verbose and result.stdout:
            logger.info(f"Script output: {result.stdout}")
        
        return output_file
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Shell script failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f": {e.stderr}"
        raise RuntimeError(error_msg)


def generate_promoter_regions(
    refseq_file: str,
    output_file: str,
    upstream: int = 1000,
    downstream: int = 1001,
    verbose: bool = False
) -> str:
    """
    Generate promoter regions from RefSeq gene annotations.
    
    This function is a direct wrapper around the promoter generation functionality.
    
    Args:
        refseq_file: Path to RefSeq gene annotation BED file
        output_file: Path for output promoter BED file
        upstream: Distance upstream of TSS (default: 1000)
        downstream: Distance downstream of TSS (default: 1001)
        verbose: Enable verbose logging
        
    Returns:
        Path to output file
        
    Example:
        >>> promoters = generate_promoter_regions(
        ...     refseq_file="mm10_refseq.bed",
        ...     output_file="mm10_promoters1kb.bed"
        ... )
    """
    return generate_promoters_main(
        refseq_file=refseq_file,
        output_file=output_file,
        upstream=upstream,
        downstream=downstream,
        verbose=verbose
    )


def annotate_ep_interactions(
    bedpe_file: str,
    promoter_file: str,
    output_file: Optional[str] = None,
    use_interval_tree: bool = True,
    verbose: bool = False
) -> str:
    """
    Annotate E-P interactions with promoter/enhancer labels.
    
    This function is a direct wrapper around the E-P annotation functionality.
    
    Args:
        bedpe_file: Path to BEDPE file with interaction data
        promoter_file: Path to promoter regions BED file
        output_file: Path for output file (auto-generated if not provided)
        use_interval_tree: Use IntervalTree for faster lookup
        verbose: Enable verbose logging
        
    Returns:
        Path to output file
        
    Example:
        >>> result = annotate_ep_interactions(
        ...     bedpe_file="interactions.bedpe",
        ...     promoter_file="promoters.bed",
        ...     output_file="annotated.bedpe.gz"
        ... )
    """
    return annotate_ep_main(
        bedpe_file=bedpe_file,
        promoter_file=promoter_file,
        output_file=output_file,
        use_interval_tree=use_interval_tree,
        verbose=verbose
    )


# Legacy compatibility interface
def generate_index(
    interactions_file: str,
    refseq_file: Optional[str] = None,
    promoter_file: Optional[str] = None,
    output_file: Optional[str] = None,
    promoter_upstream: int = 1000,
    promoter_downstream: int = 1001,
    method: str = "python",
    verbose: bool = False
) -> str:
    """
    Legacy interface for generating E-P interaction index.
    
    This function provides backward compatibility with older API versions.
    
    Args:
        interactions_file: Path to BEDPE file with interaction data
        refseq_file: Path to RefSeq gene annotation file
        promoter_file: Path to pre-generated promoter regions file
        output_file: Path for output file
        promoter_upstream: Distance upstream of TSS for promoter regions
        promoter_downstream: Distance downstream of TSS for promoter regions
        method: Processing method ("python" or "shell")
        verbose: Enable verbose logging
        
    Returns:
        Path to output file
    """
    if method == "shell":
        return run_generate_index_script(
            bedpe_file=interactions_file,
            refseq_file=refseq_file,
            promoter_file=promoter_file,
            output_file=output_file,
            upstream=promoter_upstream,
            downstream=promoter_downstream,
            verbose=verbose
        )
    else:
        return generate_interaction_index(
            bedpe_file=interactions_file,
            refseq_file=refseq_file,
            promoter_file=promoter_file,
            output_file=output_file,
            upstream=promoter_upstream,
            downstream=promoter_downstream,
            verbose=verbose
        )


# Module-level convenience functions
__all__ = [
    'generate_interaction_index',
    'run_generate_index_script',
    'generate_promoter_regions',
    'annotate_ep_interactions',
    'generate_index',  # Legacy
] 
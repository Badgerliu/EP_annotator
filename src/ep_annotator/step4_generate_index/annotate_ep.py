#!/usr/bin/env python3
"""
Annotate E-P interactions with promoter/enhancer labels.

This script takes HiCUT interaction data (with associated peaks) and annotates
each interaction endpoint as either Promoter (P) or Enhancer (E) based on
overlap with promoter regions.
"""

import os
import gzip
import logging
import argparse
from pathlib import Path
from typing import Optional, Tuple, Dict, List, TYPE_CHECKING
from collections import defaultdict

# Try to import optional dependencies
try:
    from intervaltree import IntervalTree
    HAS_INTERVALTREE = True
except ImportError:
    HAS_INTERVALTREE = False
    if TYPE_CHECKING:
        from intervaltree import IntervalTree

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def validate_input_files(bedpe_file: str, promoter_file: str, logger: logging.Logger):
    """Validate input files exist and have correct format."""
    # Check files exist
    for file_path, name in [(bedpe_file, "BEDPE"), (promoter_file, "promoter")]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{name} file not found: {file_path}")
    
    # Validate BEDPE file format (should be 12-column from step 3)
    logger.info(f"Validating BEDPE file format: {bedpe_file}")
    with open(bedpe_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= 5:  # Check first 5 lines
                break
            if line.strip():
                cols = line.strip().split('\t')
                if len(cols) < 12:
                    raise ValueError(f"BEDPE file should have at least 12 columns, found {len(cols)} in line {i+1}")
                # Check if coordinates are numeric
                try:
                    int(cols[1])  # posA
                    int(cols[3])  # posB
                except ValueError:
                    raise ValueError(f"Invalid coordinates in BEDPE file line {i+1}")
    
    # Validate promoter file format (should be 4-column BED)
    logger.info(f"Validating promoter file format: {promoter_file}")
    with open(promoter_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= 5:  # Check first 5 lines
                break
            if line.strip():
                cols = line.strip().split('\t')
                if len(cols) < 4:
                    raise ValueError(f"Promoter file should have at least 4 columns, found {len(cols)} in line {i+1}")
                # Check if coordinates are numeric
                try:
                    int(cols[1])  # start
                    int(cols[2])  # end
                except ValueError:
                    raise ValueError(f"Invalid coordinates in promoter file line {i+1}")


def load_promoters_interval_tree(promoter_file: str, logger: logging.Logger) -> Dict[str, 'IntervalTree']:
    """Load promoter regions into IntervalTree data structure for fast lookup."""
    if not HAS_INTERVALTREE:
        raise ImportError("intervaltree is required for this function. Install with: pip install intervaltree")
    
    logger.info("Loading promoter regions into IntervalTree...")
    
    promoters = defaultdict(IntervalTree)  # chr -> tree of (start, end, gene)
    promoter_count = 0
    
    with open(promoter_file, 'r') as f:
        for line in f:
            if line.startswith(("#", "track")) or not line.strip():
                continue
            
            cols = line.strip().split('\t')
            chrom, start, end, gene = cols[0], int(cols[1]), int(cols[2]), cols[3]
            
            promoters[chrom].addi(start, end, gene)
            promoter_count += 1
    
    logger.info(f"Loaded {promoter_count:,} promoter regions for {len(promoters)} chromosomes")
    return promoters


def load_promoters_simple(promoter_file: str, logger: logging.Logger) -> Dict[str, List[Tuple[int, int, str]]]:
    """Load promoter regions into simple list structure for basic lookup."""
    logger.info("Loading promoter regions into simple data structure...")
    
    promoters = defaultdict(list)  # chr -> list of (start, end, gene)
    promoter_count = 0
    
    with open(promoter_file, 'r') as f:
        for line in f:
            if line.startswith(("#", "track")) or not line.strip():
                continue
            
            cols = line.strip().split('\t')
            chrom, start, end, gene = cols[0], int(cols[1]), int(cols[2]), cols[3]
            
            promoters[chrom].append((start, end, gene))
            promoter_count += 1
    
    # Sort promoter regions for each chromosome for binary search
    for chrom in promoters:
        promoters[chrom].sort()
    
    logger.info(f"Loaded {promoter_count:,} promoter regions for {len(promoters)} chromosomes")
    return promoters


def label_position_interval_tree(chrom: str, pos: int, promoters: Dict[str, 'IntervalTree']) -> Tuple[int, str]:
    """Label a position as promoter or enhancer using IntervalTree."""
    if chrom not in promoters:
        return 0, "enhancer"
    
    hits = promoters[chrom].overlap(pos, pos + 1)
    if hits:
        # Take the first gene; for all genes use ','.join({i.data for i in hits})
        gene = next(iter(hits)).data
        return 1, gene
    
    return 0, "enhancer"


def label_position_simple(chrom: str, pos: int, promoters: Dict[str, List[Tuple[int, int, str]]]) -> Tuple[int, str]:
    """Label a position as promoter or enhancer using simple linear search."""
    if chrom not in promoters:
        return 0, "enhancer"
    
    for start, end, gene in promoters[chrom]:
        if start <= pos < end:
            return 1, gene
    
    return 0, "enhancer"


def annotate_ep_interactions(
    bedpe_file: str,
    promoter_file: str,
    output_file: str,
    use_interval_tree: bool = True,
    verbose: bool = False
) -> str:
    """
    Annotate E-P interactions with promoter/enhancer labels.
    
    Args:
        bedpe_file: Path to BEDPE file with interaction data (12 columns from step 3)
        promoter_file: Path to promoter regions BED file (4 columns)
        output_file: Path for output file
        use_interval_tree: Use IntervalTree for faster lookup (requires intervaltree package)
        verbose: Enable verbose logging
        
    Returns:
        Path to output file
    """
    logger = setup_logging(verbose)
    
    logger.info("Starting E-P interaction annotation...")
    logger.info(f"BEDPE file: {bedpe_file}")
    logger.info(f"Promoter file: {promoter_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Method: {'IntervalTree' if use_interval_tree else 'Simple lookup'}")
    
    # Validate inputs
    validate_input_files(bedpe_file, promoter_file, logger)
    
    # Load promoter regions
    if use_interval_tree and HAS_INTERVALTREE:
        promoters = load_promoters_interval_tree(promoter_file, logger)
        label_func = label_position_interval_tree
    else:
        if use_interval_tree and not HAS_INTERVALTREE:
            logger.warning("IntervalTree not available, falling back to simple lookup")
        promoters = load_promoters_simple(promoter_file, logger)
        label_func = label_position_simple
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
    
    # Determine if output should be gzipped
    open_out = gzip.open if output_file.endswith('.gz') else open
    mode = 'wt' if output_file.endswith('.gz') else 'w'
    
    # Initialize counters
    interaction_counts = {"PE": 0, "EP": 0, "PP": 0, "EE": 0}
    total_interactions = 0
    
    # Process interactions
    logger.info("Processing interactions...")
    
    # Set up progress bar if available
    def open_with_progress(file_path):
        f = open(file_path, 'r')
        if HAS_TQDM:
            return tqdm(f, desc="annotating")
        return f
    
    with open_with_progress(bedpe_file) as inp, open_out(output_file, mode) as out:
        for line in inp:
            if not line.strip():
                continue
            
            total_interactions += 1
            cols = line.rstrip().split('\t')
            
            # Left endpoint = col0,1   Right endpoint = col2,3
            chrL, posL = cols[0], int(cols[1])
            chrR, posR = cols[2], int(cols[3])
            
            # Label each endpoint
            l_is_promoter, l_label = label_func(chrL, posL, promoters)
            r_is_promoter, r_label = label_func(chrR, posR, promoters)
            
            # Determine interaction category
            category = ("P" if l_is_promoter else "E") + ("P" if r_is_promoter else "E")
            interaction_counts[category] += 1
            
            # Write output: original columns + left_label + right_label + category
            output_line = '\t'.join(cols + [l_label, r_label, category]) + '\n'
            out.write(output_line)
            
            if total_interactions % 100000 == 0:
                logger.debug(f"Processed {total_interactions:,} interactions...")
    
    # Report results
    logger.info(f"✅ Processed {total_interactions:,} interactions")
    logger.info(f"Output written to: {output_file}")
    
    print(f"\n✅ 写入 {output_file}")
    for category, count in interaction_counts.items():
        print(f"{category}: {count:,d}")
    
    return output_file


def annotate_ep_main(
    bedpe_file: str,
    promoter_file: str,
    output_file: Optional[str] = None,
    use_interval_tree: bool = True,
    verbose: bool = False
) -> str:
    """
    Main function to annotate E-P interactions.
    
    Args:
        bedpe_file: Path to BEDPE file with interaction data
        promoter_file: Path to promoter regions BED file
        output_file: Path for output file (auto-generated if not provided)
        use_interval_tree: Use IntervalTree for faster lookup
        verbose: Enable verbose logging
        
    Returns:
        Path to output file
    """
    # Auto-generate output filename if not provided
    if output_file is None:
        base_name = bedpe_file.rsplit(".", 1)[0] if "." in bedpe_file else bedpe_file
        output_file = f"{base_name}.promLabel.bedpe.gz"
    
    return annotate_ep_interactions(
        bedpe_file=bedpe_file,
        promoter_file=promoter_file,
        output_file=output_file,
        use_interval_tree=use_interval_tree,
        verbose=verbose
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Annotate E-P interactions with promoter/enhancer labels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic annotation
  python annotate_ep.py --bedpe interactions.bedpe --prom promoters.bed
  
  # Specify output file
  python annotate_ep.py --bedpe interactions.bedpe --prom promoters.bed -o output.bedpe.gz
  
  # Use simple lookup method (no IntervalTree)
  python annotate_ep.py --bedpe interactions.bedpe --prom promoters.bed --no-interval-tree
  
  # Verbose output
  python annotate_ep.py --bedpe interactions.bedpe --prom promoters.bed -v
        """
    )
    
    parser.add_argument("--bedpe", required=True,
                       help="Input BEDPE file with interaction data (12 columns from step 3)")
    parser.add_argument("--prom", required=True,
                       help="Input promoter regions BED file (chr start end gene)")
    parser.add_argument("-o", "--out", default=None,
                       help="Output file path (.gz for gzip compression, auto-generated if not provided)")
    parser.add_argument("--no-interval-tree", action="store_true",
                       help="Use simple lookup instead of IntervalTree (slower but no extra dependencies)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    try:
        result = annotate_ep_main(
            bedpe_file=args.bedpe,
            promoter_file=args.prom,
            output_file=args.out,
            use_interval_tree=not args.no_interval_tree,
            verbose=args.verbose
        )
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1) 
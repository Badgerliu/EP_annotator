#!/usr/bin/env python3
"""
Annotate ChIP-seq/CUT&Tag peaks with detailed enhancer-promoter (EP/PE) interactions.

This module takes user-provided ChIP-seq peaks and annotates them with:
- Promoter status (overlapping with promoter regions)
- Enhancer status (involved in EP interactions)
- Detailed interaction information for each peak

Based on the original annotate_peaks_EP_detail.py script.
"""

import argparse
import gzip
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import pybedtools as pbt


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def validate_input_files(peaks_file: str, bedpe_file: str, promoter_file: str, 
                        logger: logging.Logger) -> None:
    """Validate input files exist and are readable."""
    for file_path in [peaks_file, bedpe_file, promoter_file]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file not found: {file_path}")
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"Cannot read input file: {file_path}")
    
    logger.info("✅ All input files validated")


def load_peaks(peaks_file: str, logger: logging.Logger) -> Tuple[pd.DataFrame, pbt.BedTool]:
    """
    Load peaks from BED file and ensure 4 columns (chr, start, end, name).
    
    Args:
        peaks_file: Path to peaks BED file
        logger: Logger instance
        
    Returns:
        DataFrame with peaks and BedTool object
    """
    logger.info(f"Loading peaks from: {peaks_file}")
    
    # Read peak file
    pk = pd.read_csv(peaks_file, sep='\t', header=None, comment='#')
    
    # Ensure we have at least 3 columns
    if pk.shape[1] < 3:
        raise ValueError(f"Peak file must have at least 3 columns (chr, start, end)")
    
    # If no 4th column (name), generate peak names
    if pk.shape[1] < 4:
        pk[3] = [f"peak_{i+1}" for i in range(len(pk))]
    
    # Take only first 4 columns
    pk = pk.iloc[:, :4]
    pk.columns = ["chr", "start", "end", "name"]
    
    # Convert to BedTool
    pk_bt = pbt.BedTool.from_dataframe(pk)
    
    logger.info(f"✅ Loaded {len(pk):,} peaks")
    return pk, pk_bt


def load_promoters(promoter_file: str, logger: logging.Logger) -> Tuple[pd.DataFrame, pbt.BedTool, Dict[str, Set[str]]]:
    """
    Load promoter regions and create mapping.
    
    Args:
        promoter_file: Path to promoter BED file (chr, start, end, gene)
        logger: Logger instance
        
    Returns:
        Tuple of (DataFrame, BedTool, promoter_map)
    """
    logger.info(f"Loading promoters from: {promoter_file}")
    
    # Load promoter data
    prom_df = pd.read_csv(promoter_file, sep='\t', header=None, usecols=[0,1,2,3],
                         names=["chr","start","end","gene"])
    prom_bt = pbt.BedTool.from_dataframe(prom_df)
    
    logger.info(f"✅ Loaded {len(prom_df):,} promoter regions")
    return prom_df, prom_bt, {}


def create_promoter_mapping(peaks_bt: pbt.BedTool, prom_bt: pbt.BedTool, 
                          logger: logging.Logger) -> Dict[str, Set[str]]:
    """
    Create mapping from peak names to overlapping promoter genes.
    
    Args:
        peaks_bt: BedTool of peaks
        prom_bt: BedTool of promoters
        logger: Logger instance
        
    Returns:
        Dictionary mapping peak names to sets of gene names
    """
    logger.info("Creating promoter overlap mapping...")
    
    prom_map = {}
    intersect_result = peaks_bt.intersect(prom_bt, wa=True, wb=True)
    
    for feature in intersect_result:
        peak_name = feature.name  # Peak name is in the 4th column (name)
        gene_name = feature[7]    # Gene name is in the 8th column (4 from peak + 4 from promoter)
        prom_map.setdefault(peak_name, set()).add(gene_name)
    
    overlap_count = len(prom_map)
    logger.info(f"✅ Found {overlap_count} peaks overlapping with promoters")
    return prom_map


def parse_ep_interactions(bedpe_file: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Parse E-P interaction BEDPE file and create endpoint dataframe.
    
    Args:
        bedpe_file: Path to labeled BEDPE file (from step 4)
        logger: Logger instance
        
    Returns:
        DataFrame with endpoint information
    """
    logger.info(f"Parsing E-P interactions from: {bedpe_file}")
    
    def generate_endpoints(file_path: str):
        """Generator for creating endpoint entries from BEDPE."""
        opener = gzip.open if file_path.endswith(".gz") else open
        
        for line in opener(file_path, "rt"):
            line = line.strip()
            if not line:
                continue
                
            cols = line.split('\t')
            if len(cols) < 15:
                continue
                
            # Extract H3K27Ac peak coordinates (columns 4-6 and 8-10)
            l_chr, l_start, l_end = cols[4], int(cols[5]), int(cols[6])
            r_chr, r_start, r_end = cols[8], int(cols[9]), int(cols[10])
            l_label, r_label, category = cols[12], cols[13], cols[14]
            
            # Ensure valid coordinates
            l_start = max(0, l_start)
            r_start = max(0, r_start)
            l_end = max(l_start + 1, l_end)
            r_end = max(r_start + 1, r_end)
            
            # Yield left endpoint with partner info
            yield [l_chr, l_start, l_end, "L", l_label, r_label, category,
                   r_chr, r_start, r_end]
            
            # Yield right endpoint with partner info  
            yield [r_chr, r_start, r_end, "R", r_label, l_label, category,
                   l_chr, l_start, l_end]
    
    # Create DataFrame from endpoints
    end_cols = ["chr", "start", "end", "side", "this_label", "other_label", "cat",
                "p_chr", "p_start", "p_end"]
    endpoints_data = list(generate_endpoints(bedpe_file))
    end_df = pd.DataFrame(endpoints_data, columns=end_cols)
    
    logger.info(f"✅ Generated {len(end_df):,} endpoint entries")
    return end_df


def find_genome_file() -> Optional[str]:
    """Try to find a genome file for coordinate extension."""
    # Look for genome file in common locations
    possible_paths = [
        "mm10.genome",
        "data/mm10.genome", 
        "refGenome/mm10.genome",
        "refGenome/mm10/mm10.genome",
        os.path.join(os.path.dirname(__file__), "mm10.genome"),
        os.path.join(os.path.dirname(__file__), "../../../refGenome/mm10/mm10.genome")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


def extend_endpoints(end_df: pd.DataFrame, extend_bp: int = 1000, 
                    logger: Optional[logging.Logger] = None) -> pbt.BedTool:
    """
    Extend endpoint regions for intersection.
    
    Args:
        end_df: DataFrame with endpoint coordinates
        extend_bp: Base pairs to extend on each side
        logger: Logger instance
        
    Returns:
        Extended BedTool object
    """
    if logger:
        logger.info(f"Extending endpoints by ±{extend_bp} bp...")
    
    # Convert to BedTool
    end_bt = pbt.BedTool.from_dataframe(end_df)
    
    # Always use manual extension to avoid genome file issues
    if logger:
        logger.info("Using manual coordinate extension")
    # Manual extension without genome constraints
    extended_data = []
    for _, row in end_df.iterrows():
        new_start = max(0, row['start'] - extend_bp)
        new_end = row['end'] + extend_bp
        extended_data.append([row['chr'], new_start, new_end] + 
                           list(row[3:]))
    
    extended_df = pd.DataFrame(extended_data, columns=end_df.columns)
    end_bt_extended = pbt.BedTool.from_dataframe(extended_df)
    
    if logger:
        logger.info("✅ Endpoint extension completed")
    return end_bt_extended


def intersect_peaks_with_endpoints(peaks_bt: pbt.BedTool, endpoints_bt: pbt.BedTool,
                                 logger: logging.Logger) -> pd.DataFrame:
    """
    Find intersections between peaks and extended endpoints.
    
    Args:
        peaks_bt: BedTool of peaks
        endpoints_bt: BedTool of extended endpoints
        logger: Logger instance
        
    Returns:
        DataFrame with intersection results
    """
    logger.info("Finding intersections between peaks and E-P endpoints...")
    
    # Perform intersection
    hits_bt = peaks_bt.intersect(endpoints_bt, wa=True, wb=True)
    
    # Define column names for intersection result
    hit_cols = ["p_chr", "p_start", "p_end", "p_name",  # Peak columns
                "e_chr", "e_start", "e_end", "e_side", "e_label", "o_label", "cat",  # Endpoint columns
                "partner_chr", "partner_start", "partner_end"]  # Partner columns
    
    # Read intersection results
    if hits_bt.count() > 0:
        hits_df = pd.read_csv(hits_bt.fn, sep='\t', names=hit_cols, header=None)
        logger.info(f"✅ Found {len(hits_df):,} peak-endpoint intersections")
    else:
        hits_df = pd.DataFrame(columns=hit_cols)
        logger.warning("No intersections found between peaks and endpoints")
    
    return hits_df


def process_peak_interactions(peak_name: str, hits_df: pd.DataFrame) -> Dict[str, str]:
    """
    Process all interactions for a specific peak.
    
    Args:
        peak_name: Name of the peak to process
        hits_df: DataFrame with all intersection results
        
    Returns:
        Dictionary with interaction information
    """
    peak_hits = hits_df[hits_df["p_name"] == peak_name]
    
    # Initialize interaction collections
    interactions = {
        "enhancer_target_genes": set(),    # As enhancer -> target genes
        "regulating_enhancers": set(),     # As promoter <- enhancer locations
        "enhancer_partners": set(),        # EE interactions
        "promoter_partners": set()         # PP interactions
    }
    
    for _, hit in peak_hits.iterrows():
        partner_loc = f"{hit['partner_chr']}:{hit['partner_start']}-{hit['partner_end']}"
        my_label = hit['e_label']
        partner_label = hit['o_label']
        category = hit['cat']
        
        # Classify interactions based on category and labels
        if category == "EP":
            if my_label == "enhancer" and partner_label != "enhancer":
                interactions["enhancer_target_genes"].add(partner_label)
        
        elif category == "PE":
            if my_label != "enhancer" and partner_label == "enhancer":
                interactions["regulating_enhancers"].add(partner_loc)
        
        elif category == "EE":
            if my_label == "enhancer" and partner_label == "enhancer":
                interactions["enhancer_partners"].add(partner_loc)
        
        elif category == "PP":
            if my_label != "enhancer" and partner_label != "enhancer":
                interactions["promoter_partners"].add(partner_label)
    
    # Convert sets to sorted, semicolon-separated strings
    return {k: ";".join(sorted(v)) if v else "" for k, v in interactions.items()}


def annotate_peaks_detailed(peaks_file: str, bedpe_file: str, promoter_file: str,
                          output_file: str, extend_bp: int = 1000, 
                          verbose: bool = False) -> str:
    """
    Main function to annotate peaks with detailed E-P interaction information.
    
    Args:
        peaks_file: Path to query peaks BED file
        bedpe_file: Path to labeled E-P interaction BEDPE file
        promoter_file: Path to promoter regions BED file
        output_file: Path for output TSV file
        extend_bp: Base pairs to extend endpoints for intersection
        verbose: Enable verbose logging
        
    Returns:
        Path to output file
    """
    logger = setup_logging(verbose)
    
    logger.info("Starting detailed peak annotation...")
    logger.info(f"Peaks file: {peaks_file}")
    logger.info(f"BEDPE file: {bedpe_file}")
    logger.info(f"Promoter file: {promoter_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Extension: ±{extend_bp} bp")
    
    # Validate inputs
    validate_input_files(peaks_file, bedpe_file, promoter_file, logger)
    
    # Load data
    peaks_df, peaks_bt = load_peaks(peaks_file, logger)
    prom_df, prom_bt, _ = load_promoters(promoter_file, logger)
    
    # Create promoter mapping
    prom_map = create_promoter_mapping(peaks_bt, prom_bt, logger)
    
    # Parse E-P interactions
    endpoints_df = parse_ep_interactions(bedpe_file, logger)
    
    # Extend endpoints for intersection
    extended_endpoints_bt = extend_endpoints(endpoints_df, extend_bp, logger)
    
    # Find intersections
    hits_df = intersect_peaks_with_endpoints(peaks_bt, extended_endpoints_bt, logger)
    
    # Process each peak
    logger.info("Processing peak annotations...")
    results = []
    
    for _, row in peaks_df.iterrows():
        peak_name = row["name"]
        
        # Basic information
        result = {
            "chr": row["chr"],
            "start": row["start"],
            "end": row["end"],
            "name": peak_name,
            "is_promoter": peak_name in prom_map,
            "overlapping_promoter_genes": ";".join(sorted(prom_map.get(peak_name, [])))
        }
        
        # Add interaction information
        result.update(process_peak_interactions(peak_name, hits_df))
        
        # Determine enhancer status based on interactions
        result["is_enhancer"] = (not result["is_promoter"]) and (
            bool(result["enhancer_target_genes"]) or bool(result["enhancer_partners"])
        )
        
        results.append(result)
    
    # Create output DataFrame
    results_df = pd.DataFrame(results)
    
    # Reorder columns
    output_columns = [
        "chr", "start", "end", "name",
        "is_promoter", "is_enhancer",
        "overlapping_promoter_genes",
        "enhancer_target_genes",
        "regulating_enhancers", 
        "enhancer_partners",
        "promoter_partners"
    ]
    results_df = results_df[output_columns]
    
    # Sort by genomic coordinates
    results_df.sort_values(["chr", "start", "end"], inplace=True)
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
    
    # Write output
    results_df.to_csv(output_file, sep="\t", index=False)
    
    # Report summary statistics
    total_peaks = len(results_df)
    promoter_peaks = results_df['is_promoter'].sum()
    enhancer_peaks = results_df['is_enhancer'].sum()
    neither_peaks = total_peaks - promoter_peaks - enhancer_peaks
    
    logger.info("=== Annotation Summary ===")
    logger.info(f"Total peaks: {total_peaks:,}")
    logger.info(f"Promoter peaks: {promoter_peaks:,} ({promoter_peaks/total_peaks*100:.1f}%)")
    logger.info(f"Enhancer peaks: {enhancer_peaks:,} ({enhancer_peaks/total_peaks*100:.1f}%)")
    logger.info(f"Neither: {neither_peaks:,} ({neither_peaks/total_peaks*100:.1f}%)")
    logger.info(f"✅ Detailed annotation complete → {output_file}")
    
    return output_file


def main():
    """CLI entry point for detailed peak annotation."""
    parser = argparse.ArgumentParser(
        description="Annotate ChIP-seq peaks with detailed E-P interaction information"
    )
    parser.add_argument("--peaks", required=True,
                       help="Path to query peaks BED file")
    parser.add_argument("--bedpe", required=True, 
                       help="Path to labeled E-P interaction BEDPE file (*.promLabel.bedpe.gz)")
    parser.add_argument("--prom", required=True,
                       help="Path to promoter regions BED file")
    parser.add_argument("-o", "--output", default=None,
                       help="Output TSV file (auto-generated if not provided)")
    parser.add_argument("--extend", type=int, default=1000,
                       help="Base pairs to extend endpoints for intersection (default: 1000)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Auto-generate output filename if not provided
    if args.output is None:
        peak_stem = Path(args.peaks).stem
        args.output = f"{peak_stem}_EP_annotation_detail.tsv"
    
    # Run annotation
    annotate_peaks_detailed(
        peaks_file=args.peaks,
        bedpe_file=args.bedpe, 
        promoter_file=args.prom,
        output_file=args.output,
        extend_bp=args.extend,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main() 
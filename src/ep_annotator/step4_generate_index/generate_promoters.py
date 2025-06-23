#!/usr/bin/env python3
"""
Generate promoter regions from RefSeq gene annotations.

This script processes RefSeq gene BED files to extract TSS (Transcription Start Site)
regions and create promoter regions (TSS ± specified distance).
"""

import os
import logging
import argparse
from pathlib import Path
from typing import Optional, Tuple, List


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def validate_refseq_file(refseq_file: str, logger: logging.Logger):
    """Validate RefSeq gene annotation file format."""
    logger.info(f"Validating RefSeq file format: {refseq_file}")
    
    if not os.path.exists(refseq_file):
        raise FileNotFoundError(f"RefSeq file not found: {refseq_file}")
    
    # Check first few lines to validate format
    with open(refseq_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= 5:  # Check first 5 lines
                break
            if line.strip():
                cols = line.strip().split('\t')
                if len(cols) < 6:
                    raise ValueError(f"RefSeq file should have at least 6 columns, found {len(cols)} in line {i+1}")
                
                # Check basic format: chr, start, end, name, score, strand
                try:
                    int(cols[1])  # start
                    int(cols[2])  # end
                except ValueError:
                    raise ValueError(f"Invalid coordinates in RefSeq file line {i+1}")
                
                if cols[5] not in ['+', '-']:
                    raise ValueError(f"Invalid strand '{cols[5]}' in RefSeq file line {i+1}")


def generate_promoter_regions(
    refseq_file: str,
    output_file: str,
    upstream: int = 1000,
    downstream: int = 1001,
    verbose: bool = False
) -> str:
    """
    Generate promoter regions from RefSeq gene annotations.
    
    Args:
        refseq_file: Path to RefSeq gene annotation BED file
        output_file: Path for output promoter BED file
        upstream: Distance upstream of TSS (default: 1000)
        downstream: Distance downstream of TSS (default: 1001)
        verbose: Enable verbose logging
        
    Returns:
        Path to output file
    """
    logger = setup_logging(verbose)
    
    logger.info("Starting promoter region generation...")
    logger.info(f"RefSeq file: {refseq_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Promoter region: TSS -{upstream} to +{downstream}")
    
    # Validate input
    validate_refseq_file(refseq_file, logger)
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
    
    promoter_count = 0
    gene_count = 0
    
    with open(refseq_file, 'r') as inp, open(output_file, 'w') as out:
        for line in inp:
            if line.strip():
                gene_count += 1
                cols = line.strip().split('\t')
                
                # Extract fields: chr, start, end, name, score, strand
                chrom = cols[0]
                gene_start = int(cols[1])
                gene_end = int(cols[2])
                gene_name = cols[3]
                strand = cols[5]
                
                # Calculate TSS based on strand
                if strand == '+':
                    tss = gene_start
                else:  # strand == '-'
                    tss = gene_end - 1
                
                # Calculate promoter region
                prom_start = tss - upstream
                prom_end = tss + downstream
                
                # Avoid negative coordinates
                if prom_start < 0:
                    prom_start = 0
                
                # Write promoter region
                out.write(f"{chrom}\t{prom_start}\t{prom_end}\t{gene_name}\n")
                promoter_count += 1
                
                if promoter_count % 10000 == 0:
                    logger.debug(f"Processed {promoter_count:,} genes...")
    
    logger.info(f"✅ Generated {promoter_count:,} promoter regions from {gene_count:,} genes")
    logger.info(f"Output written to: {output_file}")
    
    return output_file


def generate_promoters_main(
    refseq_file: str,
    output_file: str,
    upstream: int = 1000,
    downstream: int = 1001,
    verbose: bool = False
) -> str:
    """
    Main function to generate promoter regions.
    
    Args:
        refseq_file: Path to RefSeq gene annotation file
        output_file: Path for output promoter file
        upstream: Distance upstream of TSS
        downstream: Distance downstream of TSS
        verbose: Enable verbose logging
        
    Returns:
        Path to output file
    """
    return generate_promoter_regions(
        refseq_file=refseq_file,
        output_file=output_file,
        upstream=upstream,
        downstream=downstream,
        verbose=verbose
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate promoter regions from RefSeq gene annotations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate standard promoter regions (TSS ±1kb)
  python generate_promoters.py -i mm10_refseq.bed -o mm10_promoters1kb.bed
  
  # Custom promoter regions (TSS -500 to +2000)
  python generate_promoters.py -i mm10_refseq.bed -o custom_promoters.bed --upstream 500 --downstream 2000
  
  # Verbose output
  python generate_promoters.py -i mm10_refseq.bed -o promoters.bed -v
        """
    )
    
    parser.add_argument("-i", "--input", required=True,
                       help="Input RefSeq gene annotation BED file")
    parser.add_argument("-o", "--output", required=True,
                       help="Output promoter regions BED file")
    parser.add_argument("--upstream", type=int, default=1000,
                       help="Distance upstream of TSS (default: 1000)")
    parser.add_argument("--downstream", type=int, default=1001,
                       help="Distance downstream of TSS (default: 1001)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    try:
        result = generate_promoters_main(
            refseq_file=args.input,
            output_file=args.output,
            upstream=args.upstream,
            downstream=args.downstream,
            verbose=args.verbose
        )
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1) 
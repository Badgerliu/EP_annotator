#!/usr/bin/env python3
"""
Associate HiCUT chromatin interactions with H3K27Ac CUT&Tag peaks.

This script finds the closest H3K27Ac peak for each endpoint of chromatin interactions
and calculates distances. It can also filter results by distance threshold.
"""

import os
import logging
import argparse
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List
import gzip

# Try to import optional dependencies
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import pybedtools
    HAS_PYBEDTOOLS = True
except ImportError:
    HAS_PYBEDTOOLS = False


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are available."""
    missing = []
    
    # Check for bedtools
    try:
        result = subprocess.run(['bedtools', '--version'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            missing.append('bedtools')
    except FileNotFoundError:
        missing.append('bedtools')
    
    # Check for sort and awk
    for tool in ['sort', 'awk']:
        try:
            subprocess.run([tool, '--version'], 
                          capture_output=True, text=True)
        except FileNotFoundError:
            missing.append(tool)
    
    return missing


def validate_input_files(interaction_file: str, peak_file: str, logger: logging.Logger):
    """Validate input files exist and have correct format."""
    # Check files exist
    for file_path, name in [(interaction_file, "interaction"), (peak_file, "peak")]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"{name} file not found: {file_path}")
    
    # Validate interaction file format (should be 4-column BEDPE)
    logger.info(f"Validating interaction file format: {interaction_file}")
    with open(interaction_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= 5:  # Check first 5 lines
                break
            if line.strip():
                cols = line.strip().split('\t')
                if len(cols) < 4:
                    raise ValueError(f"Interaction file should have at least 4 columns, found {len(cols)} in line {i+1}")
                # Check if coordinates are numeric
                try:
                    int(cols[1])  # posA
                    int(cols[3])  # posB
                except ValueError:
                    raise ValueError(f"Invalid coordinates in interaction file line {i+1}")
    
    # Validate peak file format (should be 3-column BED)
    logger.info(f"Validating peak file format: {peak_file}")
    with open(peak_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= 5:  # Check first 5 lines
                break
            if line.strip():
                cols = line.strip().split('\t')
                if len(cols) < 3:
                    raise ValueError(f"Peak file should have at least 3 columns, found {len(cols)} in line {i+1}")
                # Check if coordinates are numeric
                try:
                    int(cols[1])  # start
                    int(cols[2])  # end
                except ValueError:
                    raise ValueError(f"Invalid coordinates in peak file line {i+1}")


def associate_with_bedtools(interaction_file: str, peak_file: str, output_file: str, 
                          logger: logging.Logger) -> str:
    """
    Associate interactions with peaks using bedtools closest.
    This implements the same logic as annotate_hicut_w_cuttag.sh.
    """
    logger.info("Starting association using bedtools...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        
        # Step 1: Create left endpoint file and find closest peaks
        logger.info("Processing left endpoints...")
        left_temp = temp_dir / "_L.tmp"
        
        # Create left endpoint BED with row numbers and sort peaks first
        sorted_peaks = temp_dir / "sorted_peaks.bed"
        subprocess.run(f'bedtools sort -i "{peak_file}" > "{sorted_peaks}"', 
                      shell=True, check=True)
        
        left_cmd = f"""
        awk 'BEGIN{{OFS="\\t"}}{{print $1,$2,$2+1,NR}}' "{interaction_file}" | \\
        bedtools sort -i - | \\
        bedtools closest -a - -b "{sorted_peaks}" -d -t first | \\
        awk 'BEGIN{{OFS="\\t"}}{{print $4,$1,$6,$7,$8}}' | \\
        sort -k1,1n > "{left_temp}"
        """
        
        result = subprocess.run(left_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Left endpoint processing failed: {result.stderr}")
        
        # Step 2: Create right endpoint file and find closest peaks
        logger.info("Processing right endpoints...")
        right_temp = temp_dir / "_R.tmp"
        
        right_cmd = f"""
        awk 'BEGIN{{OFS="\\t"}}{{print $3,$4,$4+1,NR}}' "{interaction_file}" | \\
        bedtools sort -i - | \\
        bedtools closest -a - -b "{sorted_peaks}" -d -t first | \\
        awk 'BEGIN{{OFS="\\t"}}{{print $4,$1,$6,$7,$8}}' | \\
        sort -k1,1n > "{right_temp}"
        """
        
        result = subprocess.run(right_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Right endpoint processing failed: {result.stderr}")
        
        # Step 3: Combine everything using paste (without process substitution)
        logger.info("Combining results...")
        left_data = temp_dir / "_L_data.tmp"
        right_data = temp_dir / "_R_data.tmp"
        
        # Extract columns from temporary files
        subprocess.run(f'cut -f2- "{left_temp}" > "{left_data}"', shell=True, check=True)
        subprocess.run(f'cut -f2- "{right_temp}" > "{right_data}"', shell=True, check=True)
        
        # Combine using paste
        combine_cmd = f'paste "{interaction_file}" "{left_data}" "{right_data}" > "{output_file}"'
        
        result = subprocess.run(combine_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Combining results failed: {result.stderr}")
    
    # Count results
    with open(output_file, 'r') as f:
        line_count = sum(1 for line in f if line.strip())
    
    logger.info(f"✅ Associated {line_count:,} interactions with peaks")
    return output_file


def associate_with_python(interaction_file: str, peak_file: str, output_file: str,
                         logger: logging.Logger) -> str:
    """
    Pure Python implementation for associating interactions with peaks.
    Uses intervaltree for efficient interval overlap queries.
    """
    if not HAS_PANDAS:
        raise ImportError("pandas is required for Python implementation")
    
    try:
        from intervaltree import IntervalTree
    except ImportError:
        raise ImportError("intervaltree is required for Python implementation")
    
    logger.info("Starting association using Python implementation...")
    
    # Load peaks into interval trees per chromosome
    logger.info("Loading peaks...")
    peak_trees = {}
    peak_data = {}
    
    with open(peak_file, 'r') as f:
        for line in f:
            if line.strip():
                cols = line.strip().split('\t')
                chrom, start, end = cols[0], int(cols[1]), int(cols[2])
                
                if chrom not in peak_trees:
                    peak_trees[chrom] = IntervalTree()
                    peak_data[chrom] = []
                
                peak_idx = len(peak_data[chrom])
                peak_trees[chrom].addi(start, end, peak_idx)
                peak_data[chrom].append((start, end))
    
    logger.info(f"Loaded peaks for {len(peak_trees)} chromosomes")
    
    def find_closest_peak(chrom: str, pos: int) -> Tuple[str, int, int, int]:
        """Find closest peak to a position."""
        if chrom not in peak_trees:
            return chrom, -1, -1, -1
        
        # Find overlapping peaks first
        overlaps = peak_trees[chrom].overlap(pos, pos + 1)
        if overlaps:
            # Use first overlapping peak
            peak_idx = next(iter(overlaps)).data
            start, end = peak_data[chrom][peak_idx]
            return chrom, start, end, 0
        
        # Find closest peak
        min_dist = float('inf')
        closest_peak = None
        
        for start, end in peak_data[chrom]:
            # Distance to peak
            if pos < start:
                dist = start - pos
            elif pos > end:
                dist = pos - end
            else:
                dist = 0
            
            if dist < min_dist:
                min_dist = dist
                closest_peak = (start, end)
        
        if closest_peak:
            return chrom, closest_peak[0], closest_peak[1], min_dist
        else:
            return chrom, -1, -1, -1
    
    # Process interactions
    logger.info("Processing interactions...")
    results = []
    
    with open(interaction_file, 'r') as f:
        for line in f:
            if line.strip():
                cols = line.strip().split('\t')
                chrA, posA, chrB, posB = cols[0], int(cols[1]), cols[2], int(cols[3])
                
                # Find closest peaks for both endpoints
                l_chr, l_start, l_end, l_dist = find_closest_peak(chrA, posA)
                r_chr, r_start, r_end, r_dist = find_closest_peak(chrB, posB)
                
                # Combine results
                result_line = cols + [l_chr, str(l_start), str(l_end), str(l_dist),
                                    r_chr, str(r_start), str(r_end), str(r_dist)]
                results.append('\t'.join(result_line))
    
    # Write results
    with open(output_file, 'w') as f:
        for line in results:
            f.write(line + '\n')
    
    logger.info(f"✅ Associated {len(results):,} interactions with peaks")
    return output_file


def filter_by_distance(input_file: str, output_file: str, max_distance: int,
                      logger: logging.Logger) -> str:
    """Filter interactions by distance threshold to peaks."""
    logger.info(f"Filtering by distance threshold: {max_distance}")
    
    filtered_count = 0
    total_count = 0
    
    with open(input_file, 'r') as inp, open(output_file, 'w') as out:
        for line in inp:
            if line.strip():
                total_count += 1
                cols = line.strip().split('\t')
                
                # Distance columns should be at positions 7 and 11 (0-indexed)
                # Format: chrA posA chrB posB l_chr l_start l_end l_dist r_chr r_start r_end r_dist
                if len(cols) >= 12:
                    try:
                        l_dist = int(cols[7])
                        r_dist = int(cols[11])
                        
                        if l_dist < max_distance and r_dist < max_distance:
                            out.write(line)
                            filtered_count += 1
                    except (ValueError, IndexError):
                        logger.warning(f"Invalid distance values in line: {line.strip()}")
                        continue
    
    logger.info(f"✅ Filtered {filtered_count:,} / {total_count:,} interactions "
               f"({filtered_count/total_count*100:.1f}%)")
    return output_file


def associate_peaks_main(
    interaction_file: str,
    peak_file: str,
    output_file: str,
    distance_threshold: Optional[int] = None,
    method: str = "bedtools",
    verbose: bool = False
) -> str:
    """
    Main function to associate interactions with peaks.
    
    Args:
        interaction_file: Path to HiCUT interaction file (4-column BEDPE)
        peak_file: Path to H3K27Ac peak file (3-column BED)
        output_file: Path for output file
        distance_threshold: Maximum distance for filtering (optional)
        method: "bedtools" or "python"
        verbose: Enable verbose logging
        
    Returns:
        Path to final output file
    """
    logger = setup_logging(verbose)
    
    logger.info("Starting peak association...")
    logger.info(f"Interaction file: {interaction_file}")
    logger.info(f"Peak file: {peak_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Method: {method}")
    if distance_threshold:
        logger.info(f"Distance threshold: {distance_threshold}")
    
    # Validate inputs
    validate_input_files(interaction_file, peak_file, logger)
    
    # Check dependencies
    if method == "bedtools":
        missing = check_dependencies()
        if missing:
            if "python" in ["bedtools", "python"] and not missing == ["python"]:
                logger.warning(f"Missing dependencies for bedtools method: {missing}. "
                              "Falling back to Python method.")
                method = "python"
            else:
                raise RuntimeError(f"Missing required dependencies: {missing}")
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
    
    # Associate interactions with peaks
    if method == "bedtools":
        associated_file = associate_with_bedtools(interaction_file, peak_file, output_file, logger)
    else:
        associated_file = associate_with_python(interaction_file, peak_file, output_file, logger)
    
    # Apply distance filtering if specified
    if distance_threshold:
        filtered_file = output_file.replace('.bedpe', '_filtered.bedpe')
        final_file = filter_by_distance(associated_file, filtered_file, distance_threshold, logger)
        
        # Replace original with filtered
        os.rename(filtered_file, output_file)
        final_file = output_file
    else:
        final_file = associated_file
    
    logger.info(f"✅ Peak association completed: {final_file}")
    return final_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Associate HiCUT interactions with H3K27Ac peaks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic association
  python associate_peaks.py -i interactions.bedpe -p peaks.bed -o output.bedpe
  
  # With distance filtering
  python associate_peaks.py -i interactions.bedpe -p peaks.bed -o output.bedpe -d 2000
  
  # Use Python method instead of bedtools
  python associate_peaks.py -i interactions.bedpe -p peaks.bed -o output.bedpe --method python
        """
    )
    
    parser.add_argument("-i", "--interaction", required=True,
                       help="Input HiCUT interaction file (4-column BEDPE format)")
    parser.add_argument("-p", "--peaks", required=True,
                       help="Input H3K27Ac peak file (3-column BED format)")
    parser.add_argument("-o", "--output", required=True,
                       help="Output file path")
    parser.add_argument("-d", "--distance", type=int,
                       help="Maximum distance threshold for filtering (e.g., 2000)")
    parser.add_argument("--method", choices=["bedtools", "python"], default="bedtools",
                       help="Method to use: bedtools (default) or python")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    try:
        result = associate_peaks_main(
            interaction_file=args.interaction,
            peak_file=args.peaks,
            output_file=args.output,
            distance_threshold=args.distance,
            method=args.method,
            verbose=args.verbose
        )
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1) 
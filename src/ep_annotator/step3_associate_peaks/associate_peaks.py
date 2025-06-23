#!/usr/bin/env python3
"""
Simple peak association - streamlined version of annotate_hicut_w_cuttag.sh

This script finds the closest H3K27Ac peak for each endpoint of chromatin interactions
using the exact same logic as the original shell script, but with minimal Python overhead.
"""

import sys
import subprocess
import tempfile
import os
from pathlib import Path


def associate_peaks_simple(interaction_file, peak_file, output_file, distance_threshold=None):
    """
    Simple peak association using bedtools - direct translation of shell script.
    
    This implements the exact same logic as annotate_hicut_w_cuttag.sh + distance filtering:
    1. Find closest peak for left endpoint
    2. Find closest peak for right endpoint  
    3. Paste results together
    4. Optionally filter by distance threshold (like the original 2kb filter)
    """
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        left_temp = temp_dir / "_L.tmp"
        right_temp = temp_dir / "_R.tmp"
        
        # Sort peaks once (reused for both endpoints)
        sorted_peaks = temp_dir / "sorted_peaks.bed"
        subprocess.run(f'bedtools sort -i "{peak_file}" > "{sorted_peaks}"', 
                      shell=True, check=True)
        
        # Left endpoint processing
        left_cmd = f"""
        awk 'BEGIN{{OFS="\\t"}}{{print $1,$2,$2+1,NR}}' "{interaction_file}" | \\
        bedtools sort -i - | \\
        bedtools closest -a - -b "{sorted_peaks}" -d -t first | \\
        awk 'BEGIN{{OFS="\\t"}}{{print $4,$1,$6,$7,$8}}' | \\
        sort -k1,1n > "{left_temp}"
        """
        
        # Right endpoint processing
        right_cmd = f"""
        awk 'BEGIN{{OFS="\\t"}}{{print $3,$4,$4+1,NR}}' "{interaction_file}" | \\
        bedtools sort -i - | \\
        bedtools closest -a - -b "{sorted_peaks}" -d -t first | \\
        awk 'BEGIN{{OFS="\\t"}}{{print $4,$1,$6,$7,$8}}' | \\
        sort -k1,1n > "{right_temp}"
        """
        
        # Execute both commands
        subprocess.run(left_cmd, shell=True, check=True)
        subprocess.run(right_cmd, shell=True, check=True)
        
        # Combine results using paste
        combine_cmd = f"""
        paste "{interaction_file}" \\
              <(cut -f2- "{left_temp}") \\
              <(cut -f2- "{right_temp}") \\
        > "{output_file}"
        """
        
        subprocess.run(combine_cmd, shell=True, check=True, executable='/bin/bash')
    
    # Apply distance filtering if specified (like original workflow)
    if distance_threshold:
        print(f"应用距离筛选：< {distance_threshold} bp")
        unfiltered_file = output_file.replace('.bedpe', '_unfiltered.bedpe')
        os.rename(output_file, unfiltered_file)
        
        # Count before filtering
        unfiltered_count = int(subprocess.check_output(f'wc -l < "{unfiltered_file}"', shell=True).decode().strip())
        
        # Filter using awk (same as original: awk '$8 < 2000 && $12 < 2000')
        filter_cmd = f"""
        awk '$8 < {distance_threshold} && $12 < {distance_threshold}' "{unfiltered_file}" > "{output_file}"
        """
        subprocess.run(filter_cmd, shell=True, check=True)
        
        # Count after filtering and report
        filtered_count = int(subprocess.check_output(f'wc -l < "{output_file}"', shell=True).decode().strip())
        print(f"筛选前: {unfiltered_count:,} 条互作")
        print(f"筛选后: {filtered_count:,} 条互作 ({filtered_count/unfiltered_count*100:.1f}%)")
        
        # Cleanup unfiltered file
        os.remove(unfiltered_file)
    
    # Count and report final results
    line_count = int(subprocess.check_output(f'wc -l < "{output_file}"', shell=True).decode().strip())
    print(f"✅ 完成！写入 {line_count:,} 条互作到 {output_file}")
    
    return output_file


def main():
    """Simple command line interface - mimics original script usage."""
    if len(sys.argv) < 4 or len(sys.argv) > 6:
        print("Usage: python associate_peaks_simple.py <interaction_file> <peak_file> <output_file> [distance_threshold]")
        print("")
        print("Examples:")
        print("  # Basic association")
        print("  python associate_peaks_simple.py E145_E_HiCUT_union.bedpe E145_E_H3K27ac_CUTTAG_union.bed output.bedpe")
        print("")
        print("  # With distance filtering (like original 2kb filter)")
        print("  python associate_peaks_simple.py E145_E_HiCUT_union.bedpe E145_E_H3K27ac_CUTTAG_union.bed output.bedpe 2000")
        sys.exit(1)
    
    interaction_file = sys.argv[1]
    peak_file = sys.argv[2]
    output_file = sys.argv[3]
    
    # Optional distance threshold
    distance_threshold = None
    if len(sys.argv) == 5:
        try:
            distance_threshold = int(sys.argv[4])
        except ValueError:
            print(f"Error: Distance threshold must be an integer, got: {sys.argv[4]}")
            sys.exit(1)
    
    # Basic validation
    for file_path, name in [(interaction_file, "interaction"), (peak_file, "peak")]:
        if not os.path.exists(file_path):
            print(f"Error: {name} file not found: {file_path}")
            sys.exit(1)
    
    try:
        associate_peaks_simple(interaction_file, peak_file, output_file, distance_threshold)
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
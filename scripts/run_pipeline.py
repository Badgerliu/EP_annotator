#!/usr/bin/env python3
"""
EP_annotator Pipeline Runner

This script provides a simple interface to run the complete EP annotation pipeline
or individual steps using a configuration file.
"""

import argparse
import sys
import os
import yaml
from pathlib import Path

# Add src to path to import ep_annotator
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import ep_annotator
    import ep_annotator.step1_prepare_interactions as step1
    import ep_annotator.step2_prepare_peaks as step2
    import ep_annotator.step3_associate_peaks as step3
    import ep_annotator.step4_generate_index as step4
    import ep_annotator.step5_annotate_peaks as step5
    import ep_annotator.step6_analyze_results as step6
except ImportError as e:
    print(f"Error importing ep_annotator: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def load_config(config_file):
    """Load and validate configuration file."""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def main():
    parser = argparse.ArgumentParser(description="EP_annotator Pipeline Runner")
    parser.add_argument("-c", "--config", required=True, 
                       help="Path to configuration YAML file")
    parser.add_argument("-s", "--step", type=int, choices=range(1, 7),
                       help="Run specific step only (1-6)")
    parser.add_argument("-o", "--output-dir", 
                       help="Override output directory from config")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"EP_annotator version: {ep_annotator.__version__}")
        print(f"Config file: {args.config}")
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)
    
    if args.step:
        print(f"Running step {args.step}...")
        run_single_step(config, args.step, args.output_dir, args.verbose)
    else:
        print("Running complete pipeline...")
        run_complete_pipeline(config, args.output_dir, args.verbose)

def get_output_dir(config, override_dir):
    """Get output directory from config or override."""
    if override_dir:
        return override_dir
    return config.get('output', {}).get('directory', 'results')

def get_output_prefix(config):
    """Get output prefix from config."""
    return config.get('output', {}).get('prefix', 'analysis')

def run_single_step(config, step_num, output_dir=None, verbose=False):
    """Run a single step of the pipeline."""
    output_dir = get_output_dir(config, output_dir)
    output_prefix = get_output_prefix(config)
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        if step_num == 1:
            run_step1(config, output_dir, output_prefix, verbose)
        elif step_num == 2:
            run_step2(config, output_dir, output_prefix, verbose)
        elif step_num == 3:
            run_step3(config, output_dir, output_prefix, verbose)
        elif step_num == 4:
            run_step4(config, output_dir, output_prefix, verbose)
        elif step_num == 5:
            run_step5(config, output_dir, output_prefix, verbose)
        elif step_num == 6:
            run_step6(config, output_dir, output_prefix, verbose)
        else:
            print(f"Invalid step number: {step_num}")
            sys.exit(1)
    except Exception as e:
        print(f"Error running step {step_num}: {e}")
        sys.exit(1)

def run_step1(config, output_dir, output_prefix, verbose):
    """Run Step 1: Prepare interactions."""
    print("Step 1: Preparing HiCUT interaction data...")
    
    input_files = config['input']['hicut_pairs']
    output_file = os.path.join(output_dir, f"{output_prefix}_interactions.bedpe")
    
    # Get step-specific parameters
    step_config = config.get('step1', {})
    
    if len(input_files) == 1:
        # Single file, just validate and copy/link
        result = step1.validate_bedpe_format(input_files[0])
        if result:
            import shutil
            shutil.copy2(input_files[0], output_file)
            print(f"✅ Step 1 completed: {output_file}")
        else:
            raise ValueError("Input BEDPE file validation failed")
    else:
        # Multiple files, merge them
        result = step1.merge_hicut_files(
            input_files=input_files,
            output_file=output_file,
            remove_duplicates=step_config.get('remove_duplicates', True),
            sort_output=step_config.get('sort_output', True),
            verbose=verbose
        )
        print(f"✅ Step 1 completed: {result}")

def run_step2(config, output_dir, output_prefix, verbose):
    """Run Step 2: Prepare peaks."""
    print("Step 2: Preparing H3K27Ac peak data...")
    
    input_files = config['input']['active_peaks']
    output_file = os.path.join(output_dir, f"{output_prefix}_peaks.bed")
    
    # Get step-specific parameters
    step_config = config.get('step2', {})
    
    if len(input_files) == 1:
        # Single file, just validate and copy/link
        result = step2.validate_bed_format(input_files[0])
        if result:
            import shutil
            shutil.copy2(input_files[0], output_file)
            print(f"✅ Step 2 completed: {output_file}")
        else:
            raise ValueError("Input BED file validation failed")
    else:
        # Multiple files, merge them
        result = step2.merge_peak_files(
            input_files=input_files,
            output_file=output_file,
            merge_overlapping=step_config.get('merge_overlapping', True),
            sort_peaks=step_config.get('sort_peaks', True),
            verbose=verbose
        )
        print(f"✅ Step 2 completed: {result}")

def run_step3(config, output_dir, output_prefix, verbose):
    """Run Step 3: Associate peaks."""
    print("Step 3: Associating interactions with peaks...")
    
    # Input files from previous steps or config
    interaction_file = os.path.join(output_dir, f"{output_prefix}_interactions.bedpe")
    peak_file = os.path.join(output_dir, f"{output_prefix}_peaks.bed")
    output_file = os.path.join(output_dir, f"{output_prefix}_associated.bedpe")
    
    # Check if input files exist, otherwise use original inputs
    if not os.path.exists(interaction_file):
        input_files = config['input']['hicut_pairs']
        if len(input_files) == 1:
            interaction_file = input_files[0]
        else:
            raise FileNotFoundError(f"Interaction file not found: {interaction_file}")
    
    if not os.path.exists(peak_file):
        input_files = config['input']['active_peaks']
        if len(input_files) == 1:
            peak_file = input_files[0]
        else:
            raise FileNotFoundError(f"Peak file not found: {peak_file}")
    
    # Get step-specific parameters
    step_config = config.get('step3', {})
    distance_threshold = step_config.get('distance_threshold')
    
    result = step3.associate_interactions_with_peaks(
        interaction_file=interaction_file,
        peak_file=peak_file,
        output_file=output_file,
        distance_threshold=distance_threshold,
        verbose=verbose
    )
    print(f"✅ Step 3 completed: {result}")

def run_step4(config, output_dir, output_prefix, verbose):
    """Run Step 4: Generate index."""
    print("Step 4: Generating enhancer-promoter index...")
    
    # Input file from Step 3
    associated_file = os.path.join(output_dir, f"{output_prefix}_associated.bedpe")
    output_file = os.path.join(output_dir, f"{output_prefix}_index.bedpe.gz")
    
    # Check if input file exists, otherwise use original inputs
    if not os.path.exists(associated_file):
        raise FileNotFoundError(f"Associated interactions file not found: {associated_file}")
    
    # Get RefSeq file from config
    refseq_file = config['input']['tss_bed']
    if not os.path.exists(refseq_file):
        raise FileNotFoundError(f"RefSeq/TSS file not found: {refseq_file}")
    
    # Get step-specific parameters
    step_config = config.get('step4', {})
    promoter_window = step_config.get('promoter_window', 1000)
    
    result = step4.generate_interaction_index(
        bedpe_file=associated_file,
        refseq_file=refseq_file,
        output_file=output_file,
        upstream=promoter_window,
        downstream=promoter_window + 1,
        verbose=verbose
    )
    print(f"✅ Step 4 completed: {result}")

def run_step5(config, output_dir, output_prefix, verbose):
    """Run Step 5: Annotate peaks."""
    print("Step 5: Annotating query peaks...")
    
    # Input files
    index_file = os.path.join(output_dir, f"{output_prefix}_index.bedpe.gz")
    query_peaks = config['input']['query_peaks']
    tss_file = config['input']['tss_bed']
    output_file = os.path.join(output_dir, f"{output_prefix}_peak_annotation.tsv")
    
    # Check if input files exist
    if not os.path.exists(index_file):
        raise FileNotFoundError(f"E-P index file not found: {index_file}")
    
    if not os.path.exists(query_peaks):
        raise FileNotFoundError(f"Query peaks file not found: {query_peaks}")
    
    # Generate promoter file from TSS if needed
    promoter_file = os.path.join(output_dir, f"{output_prefix}_promoters.bed")
    if not os.path.exists(promoter_file):
        print("Generating promoter regions for annotation...")
        step_config = config.get('step4', {})
        promoter_window = step_config.get('promoter_window', 1000)
        
        step4.generate_promoter_regions(
            refseq_file=tss_file,
            output_file=promoter_file,
            upstream=promoter_window,
            downstream=promoter_window + 1,
            verbose=verbose
        )
    
    # Get step-specific parameters
    step_config = config.get('step5', {})
    detailed_output = step_config.get('detailed_output', True)
    
    result = step5.annotate_peaks_detailed(
        peaks_file=query_peaks,
        bedpe_file=index_file,
        promoter_file=promoter_file,
        output_file=output_file,
        extend_bp=1000,
        verbose=verbose
    )
    
    print(f"✅ Step 5 completed: {result}")
    
    # Optionally generate analysis plots and reports
    if detailed_output:
        print("Generating analysis reports...")
        analysis_prefix = os.path.join(output_dir, f"{output_prefix}_analysis")
        step5.analyze_annotation_results(
            annotation_file=result,
            output_prefix=analysis_prefix,
            create_plots=True,
            verbose=verbose
        )

def run_step6(config, output_dir, output_prefix, verbose):
    """Run Step 6: Analyze results."""
    print("Step 6: Analyzing results and generating visualizations...")
    
    # Input files from previous steps
    index_file = os.path.join(output_dir, f"{output_prefix}_index.bedpe.gz")
    annotation_file = os.path.join(output_dir, f"{output_prefix}_peak_annotation.tsv")
    
    # Check which input files exist
    if os.path.exists(index_file):
        input_file = index_file
        analysis_mode = "bedpe"
        print(f"Using BEDPE file: {input_file}")
    elif os.path.exists(annotation_file):
        input_file = annotation_file
        analysis_mode = "annotation"
        print(f"Using annotation file: {input_file}")
    else:
        raise FileNotFoundError(f"No suitable input files found. Expected either:\n"
                              f"  - BEDPE: {index_file}\n"
                              f"  - Annotation: {annotation_file}")
    
    # Generate plots setting from config
    step_config = config.get('step6', {})
    create_plots = step_config.get('plot_format') != 'none'
    
    try:
        if analysis_mode == "bedpe":
            result = step6.analyze_results(
                bedpe_file=input_file,
                output_prefix=os.path.join(output_dir, output_prefix),
                create_plots=create_plots,
                verbose=verbose
            )
        else:  # annotation mode
            result = step6.analyze_from_step5_output(
                annotation_file=input_file,
                output_prefix=os.path.join(output_dir, output_prefix),
                create_plots=create_plots,
                verbose=verbose
            )
        
        print(f"✅ Step 6 completed successfully")
        if create_plots:
            print(f"Generated visualizations and reports")
        else:
            print(f"Generated statistical reports (plots disabled)")
            
        return result
        
    except Exception as e:
        raise RuntimeError(f"Step 6 failed: {str(e)}")

def run_complete_pipeline(config, output_dir=None, verbose=False):
    """Run the complete EP annotation pipeline."""
    print("🚀 Starting complete EP_annotator pipeline...")
    
    for step in range(1, 7):
        print(f"\n{'='*50}")
        run_single_step(config, step, output_dir, verbose)
    
    print(f"\n{'='*50}")
    print("🎉 Complete pipeline finished successfully!")

if __name__ == "__main__":
    main() 
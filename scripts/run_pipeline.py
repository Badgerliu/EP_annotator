#!/usr/bin/env python3
"""
EP_annotator Pipeline Runner

This script provides a simple interface to run the complete EP annotation pipeline
or individual steps using a configuration file.
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path to import ep_annotator
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import ep_annotator
except ImportError as e:
    print(f"Error importing ep_annotator: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

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
    
    # TODO: Implement pipeline logic
    if args.step:
        print(f"Running step {args.step}...")
        run_single_step(args.config, args.step, args.output_dir, args.verbose)
    else:
        print("Running complete pipeline...")
        run_complete_pipeline(args.config, args.output_dir, args.verbose)

def run_single_step(config_file, step_num, output_dir=None, verbose=False):
    """Run a single step of the pipeline."""
    # TODO: Implement single step execution
    print(f"Step {step_num} execution not yet implemented")
    pass

def run_complete_pipeline(config_file, output_dir=None, verbose=False):
    """Run the complete EP annotation pipeline."""
    # TODO: Implement complete pipeline execution
    print("Complete pipeline execution not yet implemented")
    pass

if __name__ == "__main__":
    main() 
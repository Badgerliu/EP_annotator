"""
Step 5: Annotate ChIP-seq Peaks

This module maps user-provided ChIP-seq peaks to the E-P interaction index
to identify target genes and classify interaction types.

The module provides both Python and shell script implementations for:
- Detailed annotation of peaks with E-P interaction information
- Classification of peaks into promoter, enhancer, and neither categories
- Analysis and visualization of annotation results
"""

from .annotate_peaks_detail import (
    annotate_peaks_detailed,
    load_peaks,
    load_promoters,
    create_promoter_mapping,
    parse_ep_interactions,
    extend_endpoints,
    intersect_peaks_with_endpoints,
    process_peak_interactions,
    validate_input_files
)

from .analyze_annotations import (
    analyze_annotation_results,
    load_annotation_results,
    classify_peaks,
    analyze_interaction_types,
    save_classified_peaks,
    create_summary_plot,
    generate_detailed_report
)

__all__ = [
    # Main functions
    'annotate_peaks_detailed',
    'analyze_annotation_results',
    
    # Peak annotation functions
    'load_peaks',
    'load_promoters', 
    'create_promoter_mapping',
    'parse_ep_interactions',
    'extend_endpoints',
    'intersect_peaks_with_endpoints',
    'process_peak_interactions',
    'validate_input_files',
    
    # Analysis functions
    'load_annotation_results',
    'classify_peaks',
    'analyze_interaction_types',
    'save_classified_peaks',
    'create_summary_plot',
    'generate_detailed_report',
    
    # Legacy function (for backward compatibility)
    'annotate_peaks'
]


def annotate_peaks(query_peaks, ep_index, output_file, **kwargs):
    """
    Main function to annotate ChIP-seq peaks using E-P interaction index.
    
    This is a wrapper function that calls the detailed annotation function.
    
    Args:
        query_peaks (str): Path to query ChIP-seq peak BED file
        ep_index (str): Path to E-P interaction index file (labeled BEDPE)
        output_file (str): Path for output annotation file
        **kwargs: Additional parameters including:
            - promoter_file (str): Path to promoter regions BED file
            - extend_bp (int): Base pairs to extend endpoints (default: 1000)
            - verbose (bool): Enable verbose logging
        
    Returns:
        str: Path to detailed annotation file
    """
    # Extract parameters
    promoter_file = kwargs.get('promoter_file')
    if not promoter_file:
        raise ValueError("promoter_file parameter is required")
    
    extend_bp = kwargs.get('extend_bp', 1000)
    verbose = kwargs.get('verbose', False)
    
    return annotate_peaks_detailed(
        peaks_file=query_peaks,
        bedpe_file=ep_index,
        promoter_file=promoter_file,
        output_file=output_file,
        extend_bp=extend_bp,
        verbose=verbose
    ) 
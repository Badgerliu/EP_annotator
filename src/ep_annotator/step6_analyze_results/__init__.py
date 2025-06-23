"""
Step 6: Analyze Results

This module performs comprehensive statistical analysis and visualization of EP interaction
results, including distribution plots, interaction type analysis, and functional enrichment.

The module provides:
- Advanced statistical analysis of interaction data
- Publication-ready visualizations with specific color schemes
- Comprehensive reporting functionality
- Integration with step5 annotation results

Key Features:
- Interaction type pie charts (EP: #7DC69B, PE: #9BD7F3, EE: #D5EAD9, PP: #D8EEFB)
- Distance distribution analysis
- Chromosome distribution plots
- Quality metrics assessment
- Multi-panel summary visualizations
"""

# Import main analysis functions
from .analyze_results import analyze_results, analyze_from_step5_output
from .statistical_analysis import (
    load_bedpe_data,
    calculate_interaction_statistics,
    export_statistics_report,
    analyze_distance_distribution,
    analyze_interaction_types,
    analyze_chromosome_distribution
)
from .visualization import (
    create_interaction_pie_chart,
    create_distance_distribution_plots,
    create_chromosome_distribution_plot,
    create_comprehensive_summary_plot,
    create_all_visualizations
)

__all__ = [
    # Main analysis functions
    'analyze_results',
    'analyze_from_step5_output',
    
    # Statistical analysis functions
    'load_bedpe_data',
    'calculate_interaction_statistics',
    'export_statistics_report',
    'analyze_distance_distribution',
    'analyze_interaction_types',
    'analyze_chromosome_distribution',
    
    # Visualization functions
    'create_interaction_pie_chart',
    'create_distance_distribution_plots',
    'create_chromosome_distribution_plot',
    'create_comprehensive_summary_plot',
    'create_all_visualizations'
]

# Version and metadata
__version__ = "1.0.0"
__author__ = "EP_annotator Development Team"
__description__ = "Comprehensive analysis and visualization for EP interaction results"

# The analyze_results function is imported from .analyze_results module above 
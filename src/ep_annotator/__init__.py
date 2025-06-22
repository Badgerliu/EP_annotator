"""
EP_annotator: A bioinformatics tool for annotating enhancer-promoter interactions.

This package integrates chromatin interaction data (Hi-C) with histone modification 
signals (CUT&Tag) to identify and annotate enhancer-promoter interactions.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "liu.huand@gmail.com"

# Import main modules
from . import step1_prepare_interactions
from . import step2_prepare_peaks  
from . import step3_associate_peaks
from . import step4_generate_index
from . import step5_annotate_peaks
from . import step6_analyze_results
from . import utils
from . import cli

__all__ = [
    'step1_prepare_interactions',
    'step2_prepare_peaks', 
    'step3_associate_peaks',
    'step4_generate_index',
    'step5_annotate_peaks',
    'step6_analyze_results',
    'utils',
    'cli'
] 
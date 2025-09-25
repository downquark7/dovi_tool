"""
Dolby Vision RPU to HDR10+ Metadata Converter

This package provides functionality to extract HDR10+ metadata from Dolby Vision RPU
data using heuristics and machine learning algorithms.
"""

from .converter import DolbyVisionConverter
from .rpu_parser import RPUParser
from .hdr10plus_analyzer import HDR10PlusAnalyzer
from .heuristic_converter import HeuristicConverter
from .ml_converter import MLConverter
from .json_generator import HDR10PlusJSONGenerator
from .validator import MetadataValidator

__version__ = "1.0.0"
__all__ = [
    "DolbyVisionConverter",
    "RPUParser", 
    "HDR10PlusAnalyzer",
    "HeuristicConverter",
    "MLConverter",
    "HDR10PlusJSONGenerator",
    "MetadataValidator"
]
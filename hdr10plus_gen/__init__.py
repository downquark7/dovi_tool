"""
HDR10+ Generator - Convert Dolby Vision RPU to HDR10+ dynamic metadata

This package provides tools for converting Dolby Vision Reference Processing Unit (RPU)
data into HDR10+ dynamic metadata with full SMPTE ST 2094-40 compliance.
"""

__version__ = "1.0.0"
__author__ = "HDR10+ Generator Team"

from .hdr10plus_generator import HDR10PlusGenerator
from .rpu_parser import RPUParser
from .validator import HDR10PlusValidator

__all__ = [
    "HDR10PlusGenerator",
    "RPUParser", 
    "HDR10PlusValidator",
]
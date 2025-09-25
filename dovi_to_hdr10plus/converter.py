"""
Main converter class that orchestrates the conversion from Dolby Vision RPU to HDR10+ metadata.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import numpy as np

from .rpu_parser import RPUParser
from .hdr10plus_analyzer import HDR10PlusAnalyzer
from .heuristic_converter import HeuristicConverter
from .ml_converter import MLConverter
from .json_generator import HDR10PlusJSONGenerator
from .validator import MetadataValidator

logger = logging.getLogger(__name__)


class DolbyVisionConverter:
    """
    Main converter class for converting Dolby Vision RPU metadata to HDR10+ format.
    """
    
    def __init__(self, use_ml: bool = False, model_path: Optional[str] = None):
        """
        Initialize the converter.
        
        Args:
            use_ml: Whether to use machine learning for conversion
            model_path: Path to trained ML model (if using ML)
        """
        self.use_ml = use_ml
        self.model_path = model_path
        
        # Initialize components
        self.rpu_parser = RPUParser()
        self.hdr10plus_analyzer = HDR10PlusAnalyzer()
        self.heuristic_converter = HeuristicConverter()
        self.ml_converter = MLConverter(model_path) if use_ml else None
        self.json_generator = HDR10PlusJSONGenerator()
        self.validator = MetadataValidator()
        
        logger.info(f"Initialized DolbyVisionConverter (ML: {use_ml})")
    
    def convert_rpu_to_hdr10plus(self, input_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Convert Dolby Vision RPU to HDR10+ metadata.
        
        Args:
            input_path: Path to input HEVC file or RPU binary
            
        Returns:
            Dictionary containing HDR10+ metadata
        """
        input_path = Path(input_path)
        logger.info(f"Converting {input_path} to HDR10+ metadata")
        
        try:
            # Step 1: Parse Dolby Vision RPU
            logger.info("Step 1: Parsing Dolby Vision RPU")
            rpu_data = self.rpu_parser.parse_rpu(input_path)
            
            if not rpu_data:
                raise ValueError("Failed to parse RPU data")
            
            # Step 2: Convert using heuristics or ML
            if self.use_ml and self.ml_converter:
                logger.info("Step 2: Converting using machine learning")
                hdr10plus_data = self.ml_converter.convert(rpu_data)
            else:
                logger.info("Step 2: Converting using heuristics")
                hdr10plus_data = self.heuristic_converter.convert(rpu_data)
            
            # Step 3: Validate the converted metadata
            logger.info("Step 3: Validating HDR10+ metadata")
            validation_result = self.validator.validate_hdr10plus(hdr10plus_data)
            
            if not validation_result["valid"]:
                logger.warning(f"Validation warnings: {validation_result['warnings']}")
            
            # Step 4: Generate final JSON structure
            logger.info("Step 4: Generating HDR10+ JSON structure")
            final_metadata = self.json_generator.generate_json(hdr10plus_data)
            
            logger.info("Conversion completed successfully")
            return final_metadata
            
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            raise
    
    def save_hdr10plus_json(self, metadata: Dict[str, Any], output_path: Union[str, Path]) -> None:
        """
        Save HDR10+ metadata to JSON file.
        
        Args:
            metadata: HDR10+ metadata dictionary
            output_path: Path to output JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"HDR10+ metadata saved to {output_path}")
    
    def convert_and_save(self, input_path: Union[str, Path], output_path: Union[str, Path]) -> None:
        """
        Convert RPU to HDR10+ and save to file.
        
        Args:
            input_path: Path to input HEVC file or RPU binary
            output_path: Path to output JSON file
        """
        metadata = self.convert_rpu_to_hdr10plus(input_path)
        self.save_hdr10plus_json(metadata, output_path)
    
    def validate_hdr10plus_file(self, json_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate an existing HDR10+ JSON file.
        
        Args:
            json_path: Path to HDR10+ JSON file
            
        Returns:
            Validation result dictionary
        """
        with open(json_path, 'r') as f:
            metadata = json.load(f)
        
        return self.validator.validate_hdr10plus(metadata)
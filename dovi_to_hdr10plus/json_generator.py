"""
HDR10+ JSON metadata generator.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HDR10PlusJSONGenerator:
    """
    Generator for HDR10+ JSON metadata files.
    """
    
    def __init__(self):
        """Initialize the JSON generator."""
        self.hdr10plus_schema = self._load_hdr10plus_schema()
    
    def _load_hdr10plus_schema(self) -> Dict[str, Any]:
        """Load HDR10+ JSON schema definition."""
        return {
            "version": "1.0",
            "required_fields": [
                "MaxCLL", "MaxFALL", "MasteringDisplay"
            ],
            "optional_fields": [
                "TargetedSystemDisplayMaximumLuminance",
                "TargetedSystemDisplayMinimumLuminance",
                "MaxRGB", "MaxRGBTF", "MinRGB", "MinRGBTF",
                "ToneMappingCurves", "SceneAnalysis"
            ],
            "metadata_fields": [
                "source", "conversion_method", "generation_timestamp",
                "prediction_confidence", "validation_status"
            ]
        }
    
    def generate_json(self, hdr10plus_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate HDR10+ JSON metadata structure.
        
        Args:
            hdr10plus_data: HDR10+ metadata dictionary
            
        Returns:
            Complete HDR10+ JSON metadata structure
        """
        logger.info("Generating HDR10+ JSON metadata structure")
        
        # Create base HDR10+ metadata
        json_metadata = {
            "MaxCLL": hdr10plus_data.get("MaxCLL", 1000),
            "MaxFALL": hdr10plus_data.get("MaxFALL", 100.0),
            "MasteringDisplay": self._generate_mastering_display(hdr10plus_data.get("MasteringDisplay", {}))
        }
        
        # Add optional fields if present
        optional_fields = self._add_optional_fields(hdr10plus_data)
        json_metadata.update(optional_fields)
        
        # Add metadata fields
        metadata_fields = self._add_metadata_fields(hdr10plus_data)
        json_metadata.update(metadata_fields)
        
        # Validate the generated JSON
        validation_result = self._validate_json_structure(json_metadata)
        if not validation_result["valid"]:
            logger.warning(f"JSON validation warnings: {validation_result['warnings']}")
        
        logger.info("HDR10+ JSON metadata structure generated successfully")
        return json_metadata
    
    def _generate_mastering_display(self, mastering_display: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mastering display section."""
        if not mastering_display:
            # Use default BT.2020 mastering display
            return {
                "Primaries": {
                    "Red": [0.708, 0.292],
                    "Green": [0.170, 0.797],
                    "Blue": [0.131, 0.046],
                    "White": [0.3127, 0.3290]
                },
                "Luminance": {
                    "Min": 0.0001,
                    "Max": 1000.0
                }
            }
        
        # Validate and structure primaries
        primaries = mastering_display.get("Primaries", {})
        structured_primaries = self._structure_color_primaries(primaries)
        
        # Validate and structure luminance
        luminance = mastering_display.get("Luminance", {})
        structured_luminance = self._structure_luminance_values(luminance)
        
        return {
            "Primaries": structured_primaries,
            "Luminance": structured_luminance
        }
    
    def _structure_color_primaries(self, primaries: Dict[str, Any]) -> Dict[str, List[float]]:
        """Structure and validate color primaries."""
        structured_primaries = {}
        
        for color in ["Red", "Green", "Blue", "White"]:
            if color in primaries and isinstance(primaries[color], (list, tuple)) and len(primaries[color]) >= 2:
                # Validate and clamp coordinates
                x = max(0.0, min(1.0, float(primaries[color][0])))
                y = max(0.0, min(1.0, float(primaries[color][1])))
                structured_primaries[color] = [x, y]
            else:
                # Use default BT.2020 primaries
                default_primaries = {
                    "Red": [0.708, 0.292],
                    "Green": [0.170, 0.797],
                    "Blue": [0.131, 0.046],
                    "White": [0.3127, 0.3290]
                }
                structured_primaries[color] = default_primaries[color]
        
        return structured_primaries
    
    def _structure_luminance_values(self, luminance: Dict[str, Any]) -> Dict[str, float]:
        """Structure and validate luminance values."""
        min_lum = luminance.get("Min", 0.0001)
        max_lum = luminance.get("Max", 1000.0)
        
        # Validate and clamp values
        min_lum = max(0.0, min(1.0, float(min_lum)))
        max_lum = max(1.0, min(10000.0, float(max_lum)))
        
        return {
            "Min": min_lum,
            "Max": max_lum
        }
    
    def _add_optional_fields(self, hdr10plus_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add optional HDR10+ fields."""
        optional_fields = {}
        
        # Targeted system display luminance
        if "TargetedSystemDisplayMaximumLuminance" in hdr10plus_data:
            optional_fields["TargetedSystemDisplayMaximumLuminance"] = hdr10plus_data["TargetedSystemDisplayMaximumLuminance"]
        
        if "TargetedSystemDisplayMinimumLuminance" in hdr10plus_data:
            optional_fields["TargetedSystemDisplayMinimumLuminance"] = hdr10plus_data["TargetedSystemDisplayMinimumLuminance"]
        
        # RGB values
        for field in ["MaxRGB", "MaxRGBTF", "MinRGB", "MinRGBTF"]:
            if field in hdr10plus_data:
                optional_fields[field] = hdr10plus_data[field]
        
        # Tone mapping curves
        if "ToneMappingCurves" in hdr10plus_data:
            optional_fields["ToneMappingCurves"] = self._structure_tone_mapping_curves(
                hdr10plus_data["ToneMappingCurves"]
            )
        
        # Scene analysis
        if "SceneAnalysis" in hdr10plus_data:
            optional_fields["SceneAnalysis"] = hdr10plus_data["SceneAnalysis"]
        
        return optional_fields
    
    def _structure_tone_mapping_curves(self, tone_mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Structure tone mapping curves for HDR10+ format."""
        structured_curves = {}
        
        for curve_type, curves in tone_mapping.items():
            if isinstance(curves, list):
                structured_curves[curve_type] = []
                for curve in curves:
                    if isinstance(curve, dict) and all(key in curve for key in ["start", "control1", "control2", "end"]):
                        structured_curves[curve_type].append(curve)
                    else:
                        logger.warning(f"Invalid curve format for {curve_type}")
            else:
                logger.warning(f"Invalid curves format for {curve_type}")
        
        return structured_curves
    
    def _add_metadata_fields(self, hdr10plus_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add metadata fields to the JSON."""
        metadata_fields = {}
        
        # Source information
        if "source" in hdr10plus_data:
            metadata_fields["source"] = hdr10plus_data["source"]
        
        if "conversion_method" in hdr10plus_data:
            metadata_fields["conversion_method"] = hdr10plus_data["conversion_method"]
        
        # Generation timestamp
        metadata_fields["generation_timestamp"] = datetime.now().isoformat()
        
        # Prediction confidence (for ML-based conversions)
        if "prediction_confidence" in hdr10plus_data:
            metadata_fields["prediction_confidence"] = hdr10plus_data["prediction_confidence"]
        
        # Validation status
        if "validation_status" in hdr10plus_data:
            metadata_fields["validation_status"] = hdr10plus_data["validation_status"]
        
        return metadata_fields
    
    def _validate_json_structure(self, json_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated JSON structure."""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check required fields
        for field in self.hdr10plus_schema["required_fields"]:
            if field not in json_metadata:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False
        
        # Validate MasteringDisplay structure
        if "MasteringDisplay" in json_metadata:
            mastering_display = json_metadata["MasteringDisplay"]
            
            if "Primaries" not in mastering_display:
                validation_result["errors"].append("Missing MasteringDisplay.Primaries")
                validation_result["valid"] = False
            else:
                primaries = mastering_display["Primaries"]
                for color in ["Red", "Green", "Blue", "White"]:
                    if color not in primaries:
                        validation_result["errors"].append(f"Missing MasteringDisplay.Primaries.{color}")
                        validation_result["valid"] = False
                    elif not isinstance(primaries[color], list) or len(primaries[color]) != 2:
                        validation_result["errors"].append(f"Invalid MasteringDisplay.Primaries.{color} format")
                        validation_result["valid"] = False
            
            if "Luminance" not in mastering_display:
                validation_result["errors"].append("Missing MasteringDisplay.Luminance")
                validation_result["valid"] = False
            else:
                luminance = mastering_display["Luminance"]
                for field in ["Min", "Max"]:
                    if field not in luminance:
                        validation_result["errors"].append(f"Missing MasteringDisplay.Luminance.{field}")
                        validation_result["valid"] = False
                    elif not isinstance(luminance[field], (int, float)):
                        validation_result["errors"].append(f"Invalid MasteringDisplay.Luminance.{field} type")
                        validation_result["valid"] = False
        
        # Validate numeric ranges
        if "MaxCLL" in json_metadata:
            max_cll = json_metadata["MaxCLL"]
            if not isinstance(max_cll, int) or max_cll < 0 or max_cll > 10000:
                validation_result["warnings"].append(f"MaxCLL value {max_cll} may be outside typical range")
        
        if "MaxFALL" in json_metadata:
            max_fall = json_metadata["MaxFALL"]
            if not isinstance(max_fall, (int, float)) or max_fall < 0 or max_fall > 1000:
                validation_result["warnings"].append(f"MaxFALL value {max_fall} may be outside typical range")
        
        return validation_result
    
    def save_json_file(self, json_metadata: Dict[str, Any], output_path: Path) -> None:
        """
        Save HDR10+ JSON metadata to file.
        
        Args:
            json_metadata: HDR10+ JSON metadata dictionary
            output_path: Path to output JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure proper JSON formatting
        formatted_json = self._format_json_for_output(json_metadata)
        
        with open(output_path, 'w') as f:
            json.dump(formatted_json, f, indent=2, ensure_ascii=False)
        
        logger.info(f"HDR10+ JSON metadata saved to {output_path}")
    
    def _format_json_for_output(self, json_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Format JSON metadata for output."""
        # Create a copy to avoid modifying the original
        formatted_json = json_metadata.copy()
        
        # Ensure proper data types
        if "MaxCLL" in formatted_json:
            formatted_json["MaxCLL"] = int(formatted_json["MaxCLL"])
        
        if "MaxFALL" in formatted_json:
            formatted_json["MaxFALL"] = float(formatted_json["MaxFALL"])
        
        # Round floating point numbers to reasonable precision
        if "MasteringDisplay" in formatted_json:
            mastering_display = formatted_json["MasteringDisplay"]
            
            if "Primaries" in mastering_display:
                primaries = mastering_display["Primaries"]
                for color in primaries:
                    if isinstance(primaries[color], list):
                        primaries[color] = [round(float(x), 6) for x in primaries[color]]
            
            if "Luminance" in mastering_display:
                luminance = mastering_display["Luminance"]
                for field in ["Min", "Max"]:
                    if field in luminance:
                        luminance[field] = round(float(luminance[field]), 6)
        
        return formatted_json
    
    def generate_example_json(self) -> Dict[str, Any]:
        """Generate an example HDR10+ JSON metadata file."""
        example_data = {
            "MaxCLL": 1000,
            "MaxFALL": 100.0,
            "MasteringDisplay": {
                "Primaries": {
                    "Red": [0.708, 0.292],
                    "Green": [0.170, 0.797],
                    "Blue": [0.131, 0.046],
                    "White": [0.3127, 0.3290]
                },
                "Luminance": {
                    "Min": 0.0001,
                    "Max": 1000.0
                }
            },
            "TargetedSystemDisplayMaximumLuminance": 1000,
            "TargetedSystemDisplayMinimumLuminance": 0.0001,
            "source": "example_generation",
            "conversion_method": "example",
            "generation_timestamp": datetime.now().isoformat()
        }
        
        return self.generate_json(example_data)
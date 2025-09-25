"""
HDR10+ metadata analyzer and validator.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class HDR10PlusAnalyzer:
    """
    Analyzer for HDR10+ metadata structure and content.
    """
    
    def __init__(self):
        """Initialize the HDR10+ analyzer."""
        self.hdr10plus_schema = self._load_hdr10plus_schema()
    
    def _load_hdr10plus_schema(self) -> Dict[str, Any]:
        """Load HDR10+ metadata schema definition."""
        return {
            "required_fields": [
                "MaxCLL", "MaxFALL", "MasteringDisplay"
            ],
            "mastering_display_required": [
                "Primaries", "Luminance"
            ],
            "primaries_required": [
                "Red", "Green", "Blue", "White"
            ],
            "luminance_required": [
                "Min", "Max"
            ],
            "optional_fields": [
                "TargetedSystemDisplayMaximumLuminance",
                "TargetedSystemDisplayMinimumLuminance",
                "MaxRGB",
                "MaxRGBTF",
                "MinRGB",
                "MinRGBTF"
            ],
            "valid_ranges": {
                "MaxCLL": (0, 10000),
                "MaxFALL": (0.0, 1000.0),
                "MasteringDisplay.Luminance.Min": (0.0, 1.0),
                "MasteringDisplay.Luminance.Max": (1.0, 10000.0),
                "MasteringDisplay.Primaries.Red": (0.0, 1.0),
                "MasteringDisplay.Primaries.Green": (0.0, 1.0),
                "MasteringDisplay.Primaries.Blue": (0.0, 1.0),
                "MasteringDisplay.Primaries.White": (0.0, 1.0)
            }
        }
    
    def analyze_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze HDR10+ metadata and provide insights.
        
        Args:
            metadata: HDR10+ metadata dictionary
            
        Returns:
            Analysis results dictionary
        """
        analysis = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "statistics": {},
            "recommendations": []
        }
        
        # Check required fields
        missing_fields = self._check_required_fields(metadata)
        if missing_fields:
            analysis["errors"].extend([f"Missing required field: {field}" for field in missing_fields])
            analysis["valid"] = False
        
        # Validate field ranges
        range_errors = self._validate_field_ranges(metadata)
        if range_errors:
            analysis["errors"].extend(range_errors)
            analysis["valid"] = False
        
        # Analyze luminance values
        luminance_analysis = self._analyze_luminance_values(metadata)
        analysis["statistics"].update(luminance_analysis)
        
        # Analyze color primaries
        color_analysis = self._analyze_color_primaries(metadata)
        analysis["statistics"].update(color_analysis)
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(metadata, analysis)
        
        return analysis
    
    def _check_required_fields(self, metadata: Dict[str, Any]) -> List[str]:
        """Check for missing required fields."""
        missing = []
        
        for field in self.hdr10plus_schema["required_fields"]:
            if field not in metadata:
                missing.append(field)
        
        # Check nested required fields
        if "MasteringDisplay" in metadata:
            mastering_display = metadata["MasteringDisplay"]
            for field in self.hdr10plus_schema["mastering_display_required"]:
                if field not in mastering_display:
                    missing.append(f"MasteringDisplay.{field}")
        
        return missing
    
    def _validate_field_ranges(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate that fields are within valid ranges."""
        errors = []
        
        for field_path, (min_val, max_val) in self.hdr10plus_schema["valid_ranges"].items():
            value = self._get_nested_value(metadata, field_path)
            if value is not None:
                if isinstance(value, (list, tuple)):
                    # For color primaries, validate each component
                    for i, component in enumerate(value):
                        if not (min_val <= component <= max_val):
                            errors.append(f"{field_path}[{i}] = {component} is outside valid range [{min_val}, {max_val}]")
                else:
                    if not (min_val <= value <= max_val):
                        errors.append(f"{field_path} = {value} is outside valid range [{min_val}, {max_val}]")
        
        return errors
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _analyze_luminance_values(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze luminance values in the metadata."""
        analysis = {}
        
        # Analyze MaxCLL and MaxFALL
        max_cll = metadata.get("MaxCLL", 0)
        max_fall = metadata.get("MaxFALL", 0.0)
        
        analysis["max_cll"] = max_cll
        analysis["max_fall"] = max_fall
        analysis["cll_fall_ratio"] = max_cll / max_fall if max_fall > 0 else 0
        
        # Analyze mastering display luminance
        mastering_display = metadata.get("MasteringDisplay", {})
        luminance = mastering_display.get("Luminance", {})
        
        min_luminance = luminance.get("Min", 0.0)
        max_luminance = luminance.get("Max", 0.0)
        
        analysis["mastering_min_luminance"] = min_luminance
        analysis["mastering_max_luminance"] = max_luminance
        analysis["luminance_range"] = max_luminance - min_luminance
        
        # Check if content exceeds mastering display
        if max_cll > max_luminance:
            analysis["content_exceeds_mastering"] = True
            analysis["excess_luminance"] = max_cll - max_luminance
        else:
            analysis["content_exceeds_mastering"] = False
        
        return analysis
    
    def _analyze_color_primaries(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze color primaries in the metadata."""
        analysis = {}
        
        mastering_display = metadata.get("MasteringDisplay", {})
        primaries = mastering_display.get("Primaries", {})
        
        if primaries:
            # Extract primary coordinates
            red = primaries.get("Red", [0, 0])
            green = primaries.get("Green", [0, 0])
            blue = primaries.get("Blue", [0, 0])
            white = primaries.get("White", [0, 0])
            
            analysis["color_primaries"] = {
                "red": red,
                "green": green,
                "blue": blue,
                "white": white
            }
            
            # Calculate color gamut area (simplified)
            try:
                # Convert to numpy arrays for easier calculation
                red_np = np.array(red)
                green_np = np.array(green)
                blue_np = np.array(blue)
                
                # Calculate triangle area using cross product
                area = 0.5 * abs(np.cross(green_np - red_np, blue_np - red_np))
                analysis["color_gamut_area"] = area
                
                # Compare with standard gamuts
                bt2020_area = 0.5 * abs(np.cross([0.170, 0.797] - [0.708, 0.292], 
                                                [0.131, 0.046] - [0.708, 0.292]))
                analysis["bt2020_gamut_area"] = bt2020_area
                analysis["gamut_coverage"] = area / bt2020_area if bt2020_area > 0 else 0
                
            except Exception as e:
                logger.warning(f"Failed to calculate color gamut area: {e}")
                analysis["color_gamut_area"] = 0
                analysis["gamut_coverage"] = 0
        
        return analysis
    
    def _generate_recommendations(self, metadata: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Check for common issues
        if analysis["statistics"].get("content_exceeds_mastering", False):
            recommendations.append(
                "Content luminance exceeds mastering display maximum. Consider adjusting MaxCLL or mastering display settings."
            )
        
        if analysis["statistics"].get("cll_fall_ratio", 0) > 100:
            recommendations.append(
                "High CLL/FALL ratio detected. This may indicate very bright highlights in the content."
            )
        
        if analysis["statistics"].get("gamut_coverage", 0) < 0.8:
            recommendations.append(
                "Color gamut coverage is low. Consider using wider color primaries for better color reproduction."
            )
        
        # Check for missing optional fields that could improve quality
        if "TargetedSystemDisplayMaximumLuminance" not in metadata:
            recommendations.append(
                "Consider adding TargetedSystemDisplayMaximumLuminance for better display optimization."
            )
        
        return recommendations
    
    def compare_with_standard(self, metadata: Dict[str, Any], standard: str = "bt2020") -> Dict[str, Any]:
        """
        Compare metadata with standard color spaces.
        
        Args:
            metadata: HDR10+ metadata dictionary
            standard: Standard to compare against ("bt2020", "bt709", "dci_p3")
            
        Returns:
            Comparison results
        """
        standards = {
            "bt2020": {
                "primaries": {
                    "Red": [0.708, 0.292],
                    "Green": [0.170, 0.797],
                    "Blue": [0.131, 0.046],
                    "White": [0.3127, 0.3290]
                }
            },
            "bt709": {
                "primaries": {
                    "Red": [0.64, 0.33],
                    "Green": [0.30, 0.60],
                    "Blue": [0.15, 0.06],
                    "White": [0.3127, 0.3290]
                }
            },
            "dci_p3": {
                "primaries": {
                    "Red": [0.68, 0.32],
                    "Green": [0.265, 0.69],
                    "Blue": [0.15, 0.06],
                    "White": [0.3127, 0.3290]
                }
            }
        }
        
        if standard not in standards:
            raise ValueError(f"Unknown standard: {standard}")
        
        comparison = {
            "standard": standard,
            "differences": {},
            "similarity_score": 0.0
        }
        
        mastering_display = metadata.get("MasteringDisplay", {})
        primaries = mastering_display.get("Primaries", {})
        standard_primaries = standards[standard]["primaries"]
        
        if primaries:
            total_diff = 0.0
            for color in ["Red", "Green", "Blue", "White"]:
                if color in primaries and color in standard_primaries:
                    diff = np.linalg.norm(
                        np.array(primaries[color]) - np.array(standard_primaries[color])
                    )
                    comparison["differences"][color] = diff
                    total_diff += diff
            
            # Calculate similarity score (0-1, where 1 is identical)
            max_possible_diff = 4 * np.sqrt(2)  # Maximum possible difference for 4 colors
            comparison["similarity_score"] = max(0, 1 - (total_diff / max_possible_diff))
        
        return comparison
"""
Metadata validator for HDR10+ JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class MetadataValidator:
    """
    Validator for HDR10+ metadata files.
    """
    
    def __init__(self):
        """Initialize the metadata validator."""
        self.validation_rules = self._load_validation_rules()
        self.hdr10plus_standards = self._load_hdr10plus_standards()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules for HDR10+ metadata."""
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
            "field_ranges": {
                "MaxCLL": (0, 10000),
                "MaxFALL": (0.0, 1000.0),
                "MasteringDisplay.Luminance.Min": (0.0, 1.0),
                "MasteringDisplay.Luminance.Max": (1.0, 10000.0),
                "MasteringDisplay.Primaries.Red": (0.0, 1.0),
                "MasteringDisplay.Primaries.Green": (0.0, 1.0),
                "MasteringDisplay.Primaries.Blue": (0.0, 1.0),
                "MasteringDisplay.Primaries.White": (0.0, 1.0)
            },
            "data_types": {
                "MaxCLL": int,
                "MaxFALL": (int, float),
                "MasteringDisplay.Luminance.Min": (int, float),
                "MasteringDisplay.Luminance.Max": (int, float)
            }
        }
    
    def _load_hdr10plus_standards(self) -> Dict[str, Any]:
        """Load HDR10+ standard specifications."""
        return {
            "color_primaries": {
                "bt2020": {
                    "Red": [0.708, 0.292],
                    "Green": [0.170, 0.797],
                    "Blue": [0.131, 0.046],
                    "White": [0.3127, 0.3290]
                },
                "bt709": {
                    "Red": [0.64, 0.33],
                    "Green": [0.30, 0.60],
                    "Blue": [0.15, 0.06],
                    "White": [0.3127, 0.3290]
                },
                "dci_p3": {
                    "Red": [0.68, 0.32],
                    "Green": [0.265, 0.69],
                    "Blue": [0.15, 0.06],
                    "White": [0.3127, 0.3290]
                }
            },
            "luminance_ranges": {
                "typical_min": 0.0001,
                "typical_max": 4000.0,
                "extended_max": 10000.0
            }
        }
    
    def validate_hdr10plus(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate HDR10+ metadata.
        
        Args:
            metadata: HDR10+ metadata dictionary
            
        Returns:
            Validation result dictionary
        """
        logger.info("Validating HDR10+ metadata")
        
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": [],
            "compliance_score": 0.0
        }
        
        # Check required fields
        missing_fields = self._check_required_fields(metadata)
        if missing_fields:
            validation_result["errors"].extend([f"Missing required field: {field}" for field in missing_fields])
            validation_result["valid"] = False
        
        # Validate field types
        type_errors = self._validate_field_types(metadata)
        if type_errors:
            validation_result["errors"].extend(type_errors)
            validation_result["valid"] = False
        
        # Validate field ranges
        range_errors = self._validate_field_ranges(metadata)
        if range_errors:
            validation_result["errors"].extend(range_errors)
            validation_result["valid"] = False
        
        # Validate mastering display structure
        mastering_display_errors = self._validate_mastering_display(metadata.get("MasteringDisplay", {}))
        if mastering_display_errors:
            validation_result["errors"].extend(mastering_display_errors)
            validation_result["valid"] = False
        
        # Check for common issues
        common_issues = self._check_common_issues(metadata)
        validation_result["warnings"].extend(common_issues)
        
        # Validate color primaries
        color_validation = self._validate_color_primaries(metadata.get("MasteringDisplay", {}).get("Primaries", {}))
        validation_result["warnings"].extend(color_validation["warnings"])
        validation_result["recommendations"].extend(color_validation["recommendations"])
        
        # Calculate compliance score
        validation_result["compliance_score"] = self._calculate_compliance_score(metadata, validation_result)
        
        # Generate recommendations
        validation_result["recommendations"].extend(self._generate_recommendations(metadata, validation_result))
        
        logger.info(f"Validation completed - Valid: {validation_result['valid']}, Score: {validation_result['compliance_score']:.2f}")
        return validation_result
    
    def _check_required_fields(self, metadata: Dict[str, Any]) -> List[str]:
        """Check for missing required fields."""
        missing = []
        
        for field in self.validation_rules["required_fields"]:
            if field not in metadata:
                missing.append(field)
        
        # Check nested required fields
        if "MasteringDisplay" in metadata:
            mastering_display = metadata["MasteringDisplay"]
            for field in self.validation_rules["mastering_display_required"]:
                if field not in mastering_display:
                    missing.append(f"MasteringDisplay.{field}")
        
        return missing
    
    def _validate_field_types(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate field data types."""
        errors = []
        
        for field_path, expected_type in self.validation_rules["data_types"].items():
            value = self._get_nested_value(metadata, field_path)
            if value is not None:
                if not isinstance(value, expected_type):
                    errors.append(f"{field_path} should be {expected_type.__name__}, got {type(value).__name__}")
        
        return errors
    
    def _validate_field_ranges(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate field value ranges."""
        errors = []
        
        for field_path, (min_val, max_val) in self.validation_rules["field_ranges"].items():
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
    
    def _validate_mastering_display(self, mastering_display: Dict[str, Any]) -> List[str]:
        """Validate mastering display structure."""
        errors = []
        
        if not mastering_display:
            errors.append("MasteringDisplay is required")
            return errors
        
        # Validate primaries
        primaries = mastering_display.get("Primaries", {})
        if not primaries:
            errors.append("MasteringDisplay.Primaries is required")
        else:
            for color in self.validation_rules["primaries_required"]:
                if color not in primaries:
                    errors.append(f"MasteringDisplay.Primaries.{color} is required")
                elif not isinstance(primaries[color], list) or len(primaries[color]) != 2:
                    errors.append(f"MasteringDisplay.Primaries.{color} must be a list of 2 numbers")
        
        # Validate luminance
        luminance = mastering_display.get("Luminance", {})
        if not luminance:
            errors.append("MasteringDisplay.Luminance is required")
        else:
            for field in self.validation_rules["luminance_required"]:
                if field not in luminance:
                    errors.append(f"MasteringDisplay.Luminance.{field} is required")
                elif not isinstance(luminance[field], (int, float)):
                    errors.append(f"MasteringDisplay.Luminance.{field} must be a number")
        
        return errors
    
    def _check_common_issues(self, metadata: Dict[str, Any]) -> List[str]:
        """Check for common issues in HDR10+ metadata."""
        warnings = []
        
        # Check MaxCLL vs MaxFALL relationship
        max_cll = metadata.get("MaxCLL", 0)
        max_fall = metadata.get("MaxFALL", 0.0)
        
        if max_cll > 0 and max_fall > 0:
            ratio = max_cll / max_fall
            if ratio > 100:
                warnings.append(f"High MaxCLL/MaxFALL ratio ({ratio:.1f}) may indicate very bright highlights")
            elif ratio < 1:
                warnings.append(f"MaxCLL ({max_cll}) is less than MaxFALL ({max_fall}) - this is unusual")
        
        # Check mastering display luminance
        mastering_display = metadata.get("MasteringDisplay", {})
        luminance = mastering_display.get("Luminance", {})
        min_lum = luminance.get("Min", 0.0)
        max_lum = luminance.get("Max", 0.0)
        
        if max_lum > 0 and min_lum > 0:
            if max_lum < min_lum:
                warnings.append("Mastering display max luminance is less than min luminance")
            elif max_lum / min_lum > 100000:
                warnings.append("Very high mastering display luminance range may cause display issues")
        
        # Check if content exceeds mastering display
        if max_cll > max_lum > 0:
            warnings.append(f"MaxCLL ({max_cll}) exceeds mastering display max luminance ({max_lum})")
        
        return warnings
    
    def _validate_color_primaries(self, primaries: Dict[str, Any]) -> Dict[str, Any]:
        """Validate color primaries against standards."""
        result = {
            "warnings": [],
            "recommendations": []
        }
        
        if not primaries:
            return result
        
        # Check if primaries match known standards
        for standard_name, standard_primaries in self.hdr10plus_standards["color_primaries"].items():
            similarity = self._calculate_primaries_similarity(primaries, standard_primaries)
            if similarity > 0.95:
                result["recommendations"].append(f"Color primaries closely match {standard_name.upper()} standard")
                break
        else:
            result["warnings"].append("Color primaries do not closely match any standard color space")
        
        # Check for reasonable color gamut
        try:
            gamut_area = self._calculate_color_gamut_area(primaries)
            bt2020_area = self._calculate_color_gamut_area(self.hdr10plus_standards["color_primaries"]["bt2020"])
            
            if gamut_area < 0.5 * bt2020_area:
                result["warnings"].append("Color gamut area is significantly smaller than BT.2020")
            elif gamut_area > 1.5 * bt2020_area:
                result["warnings"].append("Color gamut area is significantly larger than BT.2020")
            
        except Exception as e:
            result["warnings"].append(f"Could not validate color gamut: {e}")
        
        return result
    
    def _calculate_primaries_similarity(self, primaries1: Dict[str, Any], primaries2: Dict[str, Any]) -> float:
        """Calculate similarity between two sets of color primaries."""
        total_diff = 0.0
        count = 0
        
        for color in ["Red", "Green", "Blue", "White"]:
            if color in primaries1 and color in primaries2:
                try:
                    p1 = np.array(primaries1[color])
                    p2 = np.array(primaries2[color])
                    diff = np.linalg.norm(p1 - p2)
                    total_diff += diff
                    count += 1
                except:
                    continue
        
        if count == 0:
            return 0.0
        
        avg_diff = total_diff / count
        # Convert to similarity score (0-1, where 1 is identical)
        similarity = max(0, 1 - (avg_diff / np.sqrt(2)))
        return similarity
    
    def _calculate_color_gamut_area(self, primaries: Dict[str, Any]) -> float:
        """Calculate color gamut area using triangle area formula."""
        try:
            red = np.array(primaries.get("Red", [0, 0]))
            green = np.array(primaries.get("Green", [0, 0]))
            blue = np.array(primaries.get("Blue", [0, 0]))
            
            # Calculate triangle area using cross product
            area = 0.5 * abs(np.cross(green - red, blue - red))
            return area
        except:
            return 0.0
    
    def _calculate_compliance_score(self, metadata: Dict[str, Any], validation_result: Dict[str, Any]) -> float:
        """Calculate compliance score (0-1) for the metadata."""
        score = 1.0
        
        # Deduct points for errors
        score -= len(validation_result["errors"]) * 0.2
        
        # Deduct points for warnings
        score -= len(validation_result["warnings"]) * 0.05
        
        # Bonus for having optional fields
        optional_fields = ["TargetedSystemDisplayMaximumLuminance", "TargetedSystemDisplayMinimumLuminance"]
        for field in optional_fields:
            if field in metadata:
                score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def _generate_recommendations(self, metadata: Dict[str, Any], validation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Recommendations based on missing optional fields
        if "TargetedSystemDisplayMaximumLuminance" not in metadata:
            recommendations.append("Consider adding TargetedSystemDisplayMaximumLuminance for better display optimization")
        
        if "TargetedSystemDisplayMinimumLuminance" not in metadata:
            recommendations.append("Consider adding TargetedSystemDisplayMinimumLuminance for better display optimization")
        
        # Recommendations based on luminance values
        max_cll = metadata.get("MaxCLL", 0)
        if max_cll > 4000:
            recommendations.append("High MaxCLL detected - ensure target displays can handle this luminance level")
        
        # Recommendations based on color primaries
        mastering_display = metadata.get("MasteringDisplay", {})
        primaries = mastering_display.get("Primaries", {})
        if primaries:
            # Check if using BT.2020 primaries
            bt2020_primaries = self.hdr10plus_standards["color_primaries"]["bt2020"]
            similarity = self._calculate_primaries_similarity(primaries, bt2020_primaries)
            if similarity < 0.9:
                recommendations.append("Consider using BT.2020 color primaries for better compatibility")
        
        return recommendations
    
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
    
    def validate_json_file(self, json_path: Path) -> Dict[str, Any]:
        """
        Validate HDR10+ JSON file.
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            Validation result dictionary
        """
        try:
            with open(json_path, 'r') as f:
                metadata = json.load(f)
            
            return self.validate_hdr10plus(metadata)
            
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "errors": [f"Invalid JSON format: {e}"],
                "warnings": [],
                "recommendations": [],
                "compliance_score": 0.0
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Error reading file: {e}"],
                "warnings": [],
                "recommendations": [],
                "compliance_score": 0.0
            }
    
    def compare_with_standard(self, metadata: Dict[str, Any], standard: str = "bt2020") -> Dict[str, Any]:
        """
        Compare metadata with a standard specification.
        
        Args:
            metadata: HDR10+ metadata dictionary
            standard: Standard to compare against
            
        Returns:
            Comparison result dictionary
        """
        if standard not in self.hdr10plus_standards["color_primaries"]:
            return {
                "error": f"Unknown standard: {standard}",
                "similarity": 0.0
            }
        
        standard_primaries = self.hdr10plus_standards["color_primaries"][standard]
        mastering_display = metadata.get("MasteringDisplay", {})
        primaries = mastering_display.get("Primaries", {})
        
        if not primaries:
            return {
                "error": "No color primaries found in metadata",
                "similarity": 0.0
            }
        
        similarity = self._calculate_primaries_similarity(primaries, standard_primaries)
        
        return {
            "standard": standard,
            "similarity": similarity,
            "match_quality": "excellent" if similarity > 0.95 else "good" if similarity > 0.8 else "poor"
        }
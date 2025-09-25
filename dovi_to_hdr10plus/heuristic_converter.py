"""
Heuristic-based converter from Dolby Vision RPU to HDR10+ metadata.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import interpolate

logger = logging.getLogger(__name__)


class HeuristicConverter:
    """
    Heuristic-based converter for Dolby Vision RPU to HDR10+ metadata.
    Uses rule-based algorithms and heuristics to approximate HDR10+ metadata.
    """
    
    def __init__(self):
        """Initialize the heuristic converter."""
        self.conversion_rules = self._initialize_conversion_rules()
        self.tone_mapping_curves = self._initialize_tone_mapping_curves()
    
    def _initialize_conversion_rules(self) -> Dict[str, Any]:
        """Initialize conversion rules and mappings."""
        return {
            "luminance_mapping": {
                "max_cll_factor": 0.8,  # Conservative factor for MaxCLL
                "max_fall_factor": 0.9,  # Conservative factor for MaxFALL
                "min_luminance_default": 0.0001,
                "max_luminance_default": 1000.0
            },
            "color_primaries": {
                "bt2020": {
                    "Red": [0.708, 0.292],
                    "Green": [0.170, 0.797],
                    "Blue": [0.131, 0.046],
                    "White": [0.3127, 0.3290]
                },
                "dci_p3": {
                    "Red": [0.68, 0.32],
                    "Green": [0.265, 0.69],
                    "Blue": [0.15, 0.06],
                    "White": [0.3127, 0.3290]
                }
            },
            "tone_mapping": {
                "default_trim_slopes": [1.0, 1.0, 1.0],
                "default_trim_offsets": [0.0, 0.0, 0.0],
                "default_trim_power": [1.0, 1.0, 1.0],
                "saturation_gain_factor": 1.0
            }
        }
    
    def _initialize_tone_mapping_curves(self) -> Dict[str, Any]:
        """Initialize tone mapping curve approximations."""
        return {
            "pq_curve": self._generate_pq_curve(),
            "gamma_curves": self._generate_gamma_curves(),
            "bezier_approximations": self._generate_bezier_approximations()
        }
    
    def convert(self, rpu_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Dolby Vision RPU data to HDR10+ metadata using heuristics.
        
        Args:
            rpu_data: Parsed RPU data from RPUParser
            
        Returns:
            HDR10+ metadata dictionary
        """
        logger.info("Starting heuristic conversion from Dolby Vision RPU to HDR10+")
        
        hdr10plus_metadata = {
            "source": "dolby_vision_rpu_conversion",
            "conversion_method": "heuristic",
            "MaxCLL": self._convert_max_cll(rpu_data),
            "MaxFALL": self._convert_max_fall(rpu_data),
            "MasteringDisplay": self._convert_mastering_display(rpu_data),
            "TargetedSystemDisplayMaximumLuminance": self._estimate_target_display_max_luminance(rpu_data),
            "TargetedSystemDisplayMinimumLuminance": self._estimate_target_display_min_luminance(rpu_data)
        }
        
        # Add optional fields if available
        optional_fields = self._extract_optional_fields(rpu_data)
        hdr10plus_metadata.update(optional_fields)
        
        logger.info("Heuristic conversion completed")
        return hdr10plus_metadata
    
    def _convert_max_cll(self, rpu_data: Dict[str, Any]) -> int:
        """Convert MaxCLL from Dolby Vision to HDR10+."""
        content_light = rpu_data.get("content_light_level", {})
        max_cll = content_light.get("max_cll", 0)
        
        # Apply conservative factor to account for different tone mapping
        factor = self.conversion_rules["luminance_mapping"]["max_cll_factor"]
        converted_max_cll = int(max_cll * factor)
        
        # Ensure reasonable bounds
        converted_max_cll = max(0, min(converted_max_cll, 10000))
        
        logger.debug(f"Converted MaxCLL: {max_cll} -> {converted_max_cll}")
        return converted_max_cll
    
    def _convert_max_fall(self, rpu_data: Dict[str, Any]) -> float:
        """Convert MaxFALL from Dolby Vision to HDR10+."""
        content_light = rpu_data.get("content_light_level", {})
        max_fall = content_light.get("max_fall", 0.0)
        
        # Apply conservative factor
        factor = self.conversion_rules["luminance_mapping"]["max_fall_factor"]
        converted_max_fall = max_fall * factor
        
        # Ensure reasonable bounds
        converted_max_fall = max(0.0, min(converted_max_fall, 1000.0))
        
        logger.debug(f"Converted MaxFALL: {max_fall} -> {converted_max_fall}")
        return converted_max_fall
    
    def _convert_mastering_display(self, rpu_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert mastering display information."""
        mastering_display = rpu_data.get("mastering_display", {})
        
        # Use Dolby Vision mastering display if available, otherwise use defaults
        if mastering_display:
            primaries = mastering_display.get("primaries", {})
            luminance = mastering_display.get("luminance", {})
            
            # Validate and convert primaries
            converted_primaries = self._convert_color_primaries(primaries)
            
            # Convert luminance values
            converted_luminance = self._convert_luminance_values(luminance)
            
        else:
            # Use default BT.2020 primaries
            converted_primaries = self.conversion_rules["color_primaries"]["bt2020"]
            converted_luminance = {
                "Min": self.conversion_rules["luminance_mapping"]["min_luminance_default"],
                "Max": self.conversion_rules["luminance_mapping"]["max_luminance_default"]
            }
        
        return {
            "Primaries": converted_primaries,
            "Luminance": converted_luminance
        }
    
    def _convert_color_primaries(self, primaries: Dict[str, Any]) -> Dict[str, List[float]]:
        """Convert and validate color primaries."""
        converted_primaries = {}
        
        for color in ["Red", "Green", "Blue", "White"]:
            if color in primaries:
                primary = primaries[color]
                if isinstance(primary, (list, tuple)) and len(primary) >= 2:
                    # Validate and clamp values
                    x = max(0.0, min(1.0, float(primary[0])))
                    y = max(0.0, min(1.0, float(primary[1])))
                    converted_primaries[color] = [x, y]
                else:
                    # Use default if invalid
                    converted_primaries[color] = self.conversion_rules["color_primaries"]["bt2020"][color]
            else:
                # Use default if missing
                converted_primaries[color] = self.conversion_rules["color_primaries"]["bt2020"][color]
        
        return converted_primaries
    
    def _convert_luminance_values(self, luminance: Dict[str, Any]) -> Dict[str, float]:
        """Convert and validate luminance values."""
        min_lum = luminance.get("min", self.conversion_rules["luminance_mapping"]["min_luminance_default"])
        max_lum = luminance.get("max", self.conversion_rules["luminance_mapping"]["max_luminance_default"])
        
        # Validate and clamp values
        min_lum = max(0.0, min(1.0, float(min_lum)))
        max_lum = max(1.0, min(10000.0, float(max_lum)))
        
        return {
            "Min": min_lum,
            "Max": max_lum
        }
    
    def _estimate_target_display_max_luminance(self, rpu_data: Dict[str, Any]) -> int:
        """Estimate target display maximum luminance."""
        # Use mastering display max luminance as base
        mastering_display = rpu_data.get("mastering_display", {})
        luminance = mastering_display.get("luminance", {})
        max_lum = luminance.get("max", 1000.0)
        
        # Estimate target display based on common HDR displays
        if max_lum >= 4000:
            return 4000
        elif max_lum >= 2000:
            return 2000
        elif max_lum >= 1000:
            return 1000
        else:
            return 600
    
    def _estimate_target_display_min_luminance(self, rpu_data: Dict[str, Any]) -> float:
        """Estimate target display minimum luminance."""
        # Use mastering display min luminance as base
        mastering_display = rpu_data.get("mastering_display", {})
        luminance = mastering_display.get("luminance", {})
        min_lum = luminance.get("min", 0.0001)
        
        # Estimate based on common HDR displays
        if min_lum <= 0.0001:
            return 0.0001
        elif min_lum <= 0.001:
            return 0.001
        else:
            return 0.01
    
    def _extract_optional_fields(self, rpu_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract optional HDR10+ fields from RPU data."""
        optional_fields = {}
        
        # Extract MaxRGB and MinRGB if available
        content_light = rpu_data.get("content_light_level", {})
        if "max_rgb" in content_light:
            optional_fields["MaxRGB"] = content_light["max_rgb"]
        if "min_rgb" in content_light:
            optional_fields["MinRGB"] = content_light["min_rgb"]
        
        # Extract tone mapping information for advanced metadata
        tone_mapping = rpu_data.get("tone_mapping", {})
        if tone_mapping:
            # Convert tone mapping curves to HDR10+ format
            optional_fields["ToneMappingCurves"] = self._convert_tone_mapping_curves(tone_mapping)
        
        return optional_fields
    
    def _convert_tone_mapping_curves(self, tone_mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Dolby Vision tone mapping to HDR10+ compatible format."""
        curves = {}
        
        # Extract trim parameters
        trim_slopes = tone_mapping.get("trim_slopes", self.conversion_rules["tone_mapping"]["default_trim_slopes"])
        trim_offsets = tone_mapping.get("trim_offsets", self.conversion_rules["tone_mapping"]["default_trim_offsets"])
        trim_power = tone_mapping.get("trim_power", self.conversion_rules["tone_mapping"]["default_trim_power"])
        
        # Convert to HDR10+ bezier curve format
        curves["trim_slopes"] = self._convert_to_bezier_curves(trim_slopes)
        curves["trim_offsets"] = self._convert_to_bezier_curves(trim_offsets)
        curves["trim_power"] = self._convert_to_bezier_curves(trim_power)
        
        return curves
    
    def _convert_to_bezier_curves(self, values: List[float]) -> List[Dict[str, Any]]:
        """Convert linear values to bezier curve format."""
        if not values or len(values) < 2:
            return []
        
        # Create bezier control points
        bezier_curves = []
        for i in range(len(values) - 1):
            curve = {
                "start": {"x": i / (len(values) - 1), "y": values[i]},
                "control1": {"x": (i + 0.3) / (len(values) - 1), "y": values[i]},
                "control2": {"x": (i + 0.7) / (len(values) - 1), "y": values[i + 1]},
                "end": {"x": (i + 1) / (len(values) - 1), "y": values[i + 1]}
            }
            bezier_curves.append(curve)
        
        return bezier_curves
    
    def _generate_pq_curve(self) -> np.ndarray:
        """Generate Perceptual Quantizer curve for tone mapping approximation."""
        # Generate PQ curve values
        x = np.linspace(0, 1, 1000)
        # Simplified PQ curve approximation
        y = np.power(x, 0.5)  # Simplified approximation
        return np.column_stack([x, y])
    
    def _generate_gamma_curves(self) -> Dict[str, np.ndarray]:
        """Generate gamma curves for different display types."""
        x = np.linspace(0, 1, 1000)
        curves = {}
        
        for gamma in [1.8, 2.2, 2.4, 2.6]:
            y = np.power(x, 1.0 / gamma)
            curves[f"gamma_{gamma}"] = np.column_stack([x, y])
        
        return curves
    
    def _generate_bezier_approximations(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate bezier curve approximations for common tone mapping scenarios."""
        return {
            "standard": [
                {"start": {"x": 0, "y": 0}, "control1": {"x": 0.3, "y": 0.1}, 
                 "control2": {"x": 0.7, "y": 0.9}, "end": {"x": 1, "y": 1}}
            ],
            "high_contrast": [
                {"start": {"x": 0, "y": 0}, "control1": {"x": 0.2, "y": 0.05}, 
                 "control2": {"x": 0.8, "y": 0.95}, "end": {"x": 1, "y": 1}}
            ],
            "low_contrast": [
                {"start": {"x": 0, "y": 0}, "control1": {"x": 0.4, "y": 0.2}, 
                 "control2": {"x": 0.6, "y": 0.8}, "end": {"x": 1, "y": 1}}
            ]
        }
    
    def apply_scene_analysis(self, rpu_data: Dict[str, Any], hdr10plus_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply scene analysis to improve HDR10+ metadata.
        
        Args:
            rpu_data: Original RPU data
            hdr10plus_metadata: Current HDR10+ metadata
            
        Returns:
            Enhanced HDR10+ metadata with scene analysis
        """
        scene_info = rpu_data.get("scene_info", {})
        
        if scene_info.get("scene_refresh_flag", False):
            # Apply scene-specific adjustments
            scene_changes = scene_info.get("scene_change_detection", [])
            
            if scene_changes:
                # Adjust metadata based on scene changes
                hdr10plus_metadata["SceneAnalysis"] = {
                    "scene_changes": len(scene_changes),
                    "adaptive_metadata": True
                }
                
                # Adjust MaxCLL and MaxFALL based on scene analysis
                if len(scene_changes) > 10:  # High scene change frequency
                    hdr10plus_metadata["MaxCLL"] = int(hdr10plus_metadata["MaxCLL"] * 0.9)
                    hdr10plus_metadata["MaxFALL"] = hdr10plus_metadata["MaxFALL"] * 0.9
        
        return hdr10plus_metadata
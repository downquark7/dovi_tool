"""
HDR10+ Metadata Validator

This module provides validation functionality for HDR10+ dynamic metadata
to ensure compliance with SMPTE ST 2094-40 standards.
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from jsonschema import validate, ValidationError, Draft7Validator
from jsonschema.exceptions import SchemaError


class HDR10PlusValidator:
    """
    Validator for HDR10+ dynamic metadata
    
    This class provides comprehensive validation of HDR10+ metadata
    against the SMPTE ST 2094-40 schema and additional compliance checks.
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the validator
        
        Args:
            schema_path: Path to HDR10+ JSON schema file
        """
        if schema_path is None:
            # Use default schema path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            schema_path = os.path.join(current_dir, 'schemas', 'hdr10plus.json')
        
        self.schema_path = schema_path
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the HDR10+ JSON schema"""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON schema: {e}")
    
    def validate_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Validate an HDR10+ JSON file
        
        Args:
            file_path: Path to the JSON file to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return self.validate_metadata(metadata)
        except FileNotFoundError:
            return False, [f"File not found: {file_path}"]
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate HDR10+ metadata dictionary
        
        Args:
            metadata: HDR10+ metadata dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Schema validation
        try:
            validate(instance=metadata, schema=self.schema)
        except ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
        except SchemaError as e:
            errors.append(f"Schema error: {e}")
        
        # Additional compliance checks
        compliance_errors = self._check_compliance(metadata)
        errors.extend(compliance_errors)
        
        return len(errors) == 0, errors
    
    def _check_compliance(self, metadata: Dict[str, Any]) -> List[str]:
        """Perform additional compliance checks beyond schema validation"""
        errors = []
        
        # Check version format
        version = metadata.get('version', '')
        if not self._is_valid_version(version):
            errors.append(f"Invalid version format: {version}")
        
        # Check luminance ranges
        max_lum = metadata.get('targeted_system_display_maximum_luminance', 0)
        if not (100 <= max_lum <= 10000):
            errors.append(f"Targeted system display max luminance out of range: {max_lum}")
        
        # Check bezier curve consistency
        num_anchors = metadata.get('num_bezier_curve_anchors', 0)
        anchors = metadata.get('bezier_curve_anchors', [])
        if len(anchors) != num_anchors:
            errors.append(f"Bezier curve anchors count mismatch: expected {num_anchors}, got {len(anchors)}")
        
        # Check bezier curve monotonicity
        if anchors:
            monotonic_errors = self._check_bezier_monotonicity(anchors)
            errors.extend(monotonic_errors)
        
        # Check scene/frame metadata
        scene_data = metadata.get('scene_or_frame', [])
        for i, scene in enumerate(scene_data):
            scene_errors = self._check_scene_metadata(scene, i)
            errors.extend(scene_errors)
        
        # Check content light levels
        max_cll = metadata.get('max_content_light_level', 0)
        max_fall = metadata.get('max_frame_average_light_level', 0)
        if max_cll < max_fall:
            errors.append(f"Max content light level ({max_cll}) should be >= max frame average light level ({max_fall})")
        
        return errors
    
    def _is_valid_version(self, version: str) -> bool:
        """Check if version string is valid"""
        try:
            parts = version.split('.')
            if len(parts) != 2:
                return False
            major, minor = int(parts[0]), int(parts[1])
            return major >= 1 and minor >= 0
        except (ValueError, AttributeError):
            return False
    
    def _check_bezier_monotonicity(self, anchors: List[Dict[str, float]]) -> List[str]:
        """Check that bezier curve anchors are monotonically increasing in X"""
        errors = []
        
        if len(anchors) < 2:
            return errors
        
        for i in range(1, len(anchors)):
            prev_x = anchors[i-1].get('x', 0)
            curr_x = anchors[i].get('x', 0)
            if curr_x <= prev_x:
                errors.append(f"Bezier curve anchor {i} X coordinate ({curr_x}) should be > previous ({prev_x})")
        
        return errors
    
    def _check_scene_metadata(self, scene: Dict[str, Any], scene_index: int) -> List[str]:
        """Check individual scene metadata"""
        errors = []
        
        # Check required fields
        required_fields = [
            'targeted_system_display_maximum_luminance',
            'targeted_system_display_actual_peak_luminance_flag',
            'num_bezier_curve_anchors',
            'knee_point_x',
            'knee_point_y',
            'bezier_curve_anchors'
        ]
        
        for field in required_fields:
            if field not in scene:
                errors.append(f"Scene {scene_index} missing required field: {field}")
        
        # Check luminance ranges
        scene_max_lum = scene.get('targeted_system_display_maximum_luminance', 0)
        if not (100 <= scene_max_lum <= 10000):
            errors.append(f"Scene {scene_index} max luminance out of range: {scene_max_lum}")
        
        # Check knee points
        knee_x = scene.get('knee_point_x', 0)
        knee_y = scene.get('knee_point_y', 0)
        if not (0 <= knee_x <= 1):
            errors.append(f"Scene {scene_index} knee point X out of range: {knee_x}")
        if not (0 <= knee_y <= 1):
            errors.append(f"Scene {scene_index} knee point Y out of range: {knee_y}")
        
        # Check bezier anchors consistency
        num_anchors = scene.get('num_bezier_curve_anchors', 0)
        anchors = scene.get('bezier_curve_anchors', [])
        if len(anchors) != num_anchors:
            errors.append(f"Scene {scene_index} bezier anchors count mismatch: expected {num_anchors}, got {len(anchors)}")
        
        # Check luminance distribution if present
        lum_dist = scene.get('luminance_distribution', {})
        if lum_dist:
            dist_errors = self._check_luminance_distribution(lum_dist, scene_index)
            errors.extend(dist_errors)
        
        return errors
    
    def _check_luminance_distribution(self, distribution: Dict[str, float], scene_index: int) -> List[str]:
        """Check luminance distribution data"""
        errors = []
        
        percentiles = ['percentile_10', 'percentile_25', 'percentile_50', 'percentile_75', 
                      'percentile_90', 'percentile_95', 'percentile_99', 'percentile_99_9']
        
        prev_value = 0.0
        for p in percentiles:
            if p in distribution:
                value = distribution[p]
                if value < 0:
                    errors.append(f"Scene {scene_index} {p} cannot be negative: {value}")
                if value < prev_value:
                    errors.append(f"Scene {scene_index} {p} ({value}) should be >= previous percentile ({prev_value})")
                prev_value = value
        
        return errors
    
    def get_validation_report(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a detailed validation report
        
        Args:
            metadata: HDR10+ metadata dictionary
            
        Returns:
            Detailed validation report
        """
        is_valid, errors = self.validate_metadata(metadata)
        
        report = {
            'valid': is_valid,
            'errors': errors,
            'warnings': [],
            'statistics': self._calculate_statistics(metadata)
        }
        
        # Add warnings for potential issues
        warnings = self._generate_warnings(metadata)
        report['warnings'] = warnings
        
        return report
    
    def _calculate_statistics(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metadata statistics"""
        stats = {
            'num_scenes': len(metadata.get('scene_or_frame', [])),
            'global_max_luminance': metadata.get('targeted_system_display_maximum_luminance', 0),
            'global_max_cll': metadata.get('max_content_light_level', 0),
            'global_max_fall': metadata.get('max_frame_average_light_level', 0),
            'num_bezier_anchors': len(metadata.get('bezier_curve_anchors', []))
        }
        
        # Scene statistics
        scenes = metadata.get('scene_or_frame', [])
        if scenes:
            scene_max_lums = [s.get('targeted_system_display_maximum_luminance', 0) for s in scenes]
            stats['scene_max_luminance_range'] = {
                'min': min(scene_max_lums),
                'max': max(scene_max_lums),
                'avg': sum(scene_max_lums) / len(scene_max_lums)
            }
        
        return stats
    
    def _generate_warnings(self, metadata: Dict[str, Any]) -> List[str]:
        """Generate warnings for potential issues"""
        warnings = []
        
        # Check for very low luminance content
        max_cll = metadata.get('max_content_light_level', 0)
        if max_cll < 100:
            warnings.append(f"Very low max content light level: {max_cll} nits")
        
        # Check for high luminance content
        if max_cll > 4000:
            warnings.append(f"Very high max content light level: {max_cll} nits")
        
        # Check bezier curve complexity
        num_anchors = len(metadata.get('bezier_curve_anchors', []))
        if num_anchors > 10:
            warnings.append(f"High number of bezier curve anchors: {num_anchors}")
        
        # Check scene count
        num_scenes = len(metadata.get('scene_or_frame', []))
        if num_scenes > 1000:
            warnings.append(f"High number of scenes: {num_scenes}")
        
        return warnings
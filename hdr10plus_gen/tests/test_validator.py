"""
Tests for HDR10+ Validator
"""

import pytest
import tempfile
import os
import json
from hdr10plus_gen.validator import HDR10PlusValidator


class TestHDR10PlusValidator:
    """Test cases for HDR10+ validator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = HDR10PlusValidator()
        self.valid_metadata = self._create_valid_metadata()
    
    def _create_valid_metadata(self) -> dict:
        """Create valid HDR10+ metadata for testing"""
        return {
            "version": "1.0",
            "targeted_system_display_maximum_luminance": 1000,
            "targeted_system_display_actual_peak_luminance_flag": True,
            "num_bezier_curve_anchors": 3,
            "knee_point_x": 0.5,
            "knee_point_y": 0.5,
            "bezier_curve_anchors": [
                {"x": 0.0, "y": 0.0},
                {"x": 0.5, "y": 0.3},
                {"x": 1.0, "y": 1.0}
            ],
            "mastering_display_actual_peak_luminance_flag": True,
            "max_content_light_level": 1000,
            "max_frame_average_light_level": 400,
            "scene_or_frame": [
                {
                    "targeted_system_display_maximum_luminance": 1000,
                    "targeted_system_display_actual_peak_luminance_flag": True,
                    "num_bezier_curve_anchors": 3,
                    "knee_point_x": 0.4,
                    "knee_point_y": 0.4,
                    "bezier_curve_anchors": [
                        {"x": 0.0, "y": 0.0},
                        {"x": 0.4, "y": 0.2},
                        {"x": 1.0, "y": 1.0}
                    ],
                    "luminance_distribution": {
                        "percentile_10": 10.0,
                        "percentile_25": 25.0,
                        "percentile_50": 50.0,
                        "percentile_75": 75.0,
                        "percentile_90": 90.0,
                        "percentile_95": 95.0,
                        "percentile_99": 99.0,
                        "percentile_99_9": 99.9
                    }
                }
            ]
        }
    
    def test_validate_valid_metadata(self):
        """Test validation of valid metadata"""
        is_valid, errors = self.validator.validate_metadata(self.valid_metadata)
        
        assert is_valid == True
        assert len(errors) == 0
    
    def test_validate_missing_required_field(self):
        """Test validation with missing required field"""
        invalid_metadata = self.valid_metadata.copy()
        del invalid_metadata['version']
        
        is_valid, errors = self.validator.validate_metadata(invalid_metadata)
        
        assert is_valid == False
        assert len(errors) > 0
        assert any('version' in error for error in errors)
    
    def test_validate_invalid_version(self):
        """Test validation with invalid version format"""
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata['version'] = 'invalid'
        
        is_valid, errors = self.validator.validate_metadata(invalid_metadata)
        
        assert is_valid == False
        assert any('version' in error for error in errors)
    
    def test_validate_invalid_luminance_range(self):
        """Test validation with invalid luminance range"""
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata['targeted_system_display_maximum_luminance'] = 50000
        
        is_valid, errors = self.validator.validate_metadata(invalid_metadata)
        
        assert is_valid == False
        assert any('luminance' in error for error in errors)
    
    def test_validate_invalid_knee_points(self):
        """Test validation with invalid knee points"""
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata['knee_point_x'] = 1.5
        invalid_metadata['knee_point_y'] = -0.5
        
        is_valid, errors = self.validator.validate_metadata(invalid_metadata)
        
        assert is_valid == False
        assert any('knee' in error.lower() or 'minimum' in error.lower() for error in errors)
    
    def test_validate_bezier_anchors_mismatch(self):
        """Test validation with bezier anchors count mismatch"""
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata['num_bezier_curve_anchors'] = 5
        # But only 3 anchors provided
        
        is_valid, errors = self.validator.validate_metadata(invalid_metadata)
        
        assert is_valid == False
        assert any('anchors' in error for error in errors)
    
    def test_validate_bezier_anchors_monotonicity(self):
        """Test validation of bezier anchors monotonicity"""
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata['bezier_curve_anchors'] = [
            {"x": 0.5, "y": 0.3},  # Wrong order
            {"x": 0.0, "y": 0.0},
            {"x": 1.0, "y": 1.0}
        ]
        
        is_valid, errors = self.validator.validate_metadata(invalid_metadata)
        
        assert is_valid == False
        assert any('monotonic' in error or 'X coordinate' in error for error in errors)
    
    def test_validate_scene_metadata(self):
        """Test validation of scene metadata"""
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata['scene_or_frame'][0]['targeted_system_display_maximum_luminance'] = 50000
        
        is_valid, errors = self.validator.validate_metadata(invalid_metadata)
        
        assert is_valid == False
        assert any('Scene' in error for error in errors)
    
    def test_validate_luminance_distribution(self):
        """Test validation of luminance distribution"""
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata['scene_or_frame'][0]['luminance_distribution'] = {
            "percentile_10": 50.0,  # Higher than percentile_25
            "percentile_25": 25.0,
            "percentile_50": 50.0,
            "percentile_75": 75.0,
            "percentile_90": 90.0,
            "percentile_95": 95.0,
            "percentile_99": 99.0,
            "percentile_99_9": 99.9
        }
        
        is_valid, errors = self.validator.validate_metadata(invalid_metadata)
        
        assert is_valid == False
        assert any('percentile' in error for error in errors)
    
    def test_validate_content_light_levels(self):
        """Test validation of content light levels"""
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata['max_content_light_level'] = 100
        invalid_metadata['max_frame_average_light_level'] = 200
        
        is_valid, errors = self.validator.validate_metadata(invalid_metadata)
        
        assert is_valid == False
        assert any('light level' in error for error in errors)
    
    def test_validate_file(self):
        """Test validation of JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_metadata, f)
            f.flush()
            
            try:
                is_valid, errors = self.validator.validate_file(f.name)
                assert is_valid == True
                assert len(errors) == 0
            finally:
                os.unlink(f.name)
    
    def test_validate_nonexistent_file(self):
        """Test validation of nonexistent file"""
        is_valid, errors = self.validator.validate_file('nonexistent.json')
        
        assert is_valid == False
        assert len(errors) > 0
        assert any('not found' in error for error in errors)
    
    def test_validate_invalid_json_file(self):
        """Test validation of invalid JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content')
            f.flush()
            
            try:
                is_valid, errors = self.validator.validate_file(f.name)
                assert is_valid == False
                assert any('JSON' in error for error in errors)
            finally:
                os.unlink(f.name)
    
    def test_get_validation_report(self):
        """Test generation of validation report"""
        report = self.validator.get_validation_report(self.valid_metadata)
        
        assert 'valid' in report
        assert 'errors' in report
        assert 'warnings' in report
        assert 'statistics' in report
        
        assert report['valid'] == True
        assert len(report['errors']) == 0
        assert 'num_scenes' in report['statistics']
        assert 'global_max_luminance' in report['statistics']
    
    def test_validation_warnings(self):
        """Test generation of validation warnings"""
        # Create metadata that should generate warnings
        warning_metadata = self.valid_metadata.copy()
        warning_metadata['max_content_light_level'] = 50  # Very low
        warning_metadata['bezier_curve_anchors'] = [{"x": i/10, "y": i/10} for i in range(15)]  # Many anchors
        
        report = self.validator.get_validation_report(warning_metadata)
        
        assert len(report['warnings']) > 0
        assert any('low' in warning.lower() for warning in report['warnings'])
        assert any('anchors' in warning.lower() for warning in report['warnings'])
    
    def test_statistics_calculation(self):
        """Test calculation of metadata statistics"""
        report = self.validator.get_validation_report(self.valid_metadata)
        stats = report['statistics']
        
        assert stats['num_scenes'] == 1
        assert stats['global_max_luminance'] == 1000
        assert stats['global_max_cll'] == 1000
        assert stats['global_max_fall'] == 400
        assert stats['num_bezier_anchors'] == 3
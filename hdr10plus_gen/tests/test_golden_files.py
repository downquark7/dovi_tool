"""
Golden file tests for HDR10+ Generator

These tests verify that the converter produces consistent, expected outputs
by comparing against golden reference files.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from hdr10plus_gen import HDR10PlusGenerator, RPUParser, HDR10PlusValidator


class TestGoldenFiles:
    """Golden file tests for regression testing"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = RPUParser()
        self.generator = HDR10PlusGenerator(target_display_luminance=1000)
        self.validator = HDR10PlusValidator()
        self.test_data_dir = Path(__file__).parent.parent / 'test_data'
        self.test_data_dir.mkdir(exist_ok=True)
    
    def _create_golden_rpu_data(self, test_case: str) -> bytes:
        """Create golden RPU data for specific test cases"""
        if test_case == "low_nit":
            return self._create_low_nit_rpu_data()
        elif test_case == "high_nit":
            return self._create_high_nit_rpu_data()
        elif test_case == "mixed_content":
            return self._create_mixed_content_rpu_data()
        elif test_case == "minimal":
            return self._create_minimal_rpu_data()
        else:
            raise ValueError(f"Unknown test case: {test_case}")
    
    def _create_low_nit_rpu_data(self) -> bytes:
        """Create low-nit RPU data (max 200 nits)"""
        rpu_data = bytearray()
        
        # RPU header
        rpu_data.extend(b'\x00\x00')  # Magic bytes
        rpu_data.extend(b'\x07')      # Profile 7
        rpu_data.extend(b'\x01')      # Level 1
        
        # Low-nit frame data
        for i in range(50):
            rpu_data.extend(b'\x00\x00\x00\x00')  # Frame marker
            rpu_data.extend(bytes([i % 50]))      # Luminance min (0-49)
            rpu_data.extend(bytes([(i * 3) % 200]))  # Luminance max (0-199)
            rpu_data.extend(bytes([(i * 2) % 100]))  # Luminance avg (0-99)
            rpu_data.extend(bytes([i % 100]))     # Knee point x
            rpu_data.extend(bytes([(i + 10) % 100]))  # Knee point y
            rpu_data.extend(bytes([i % 100, (i + 5) % 100]))  # Bezier data
        
        return bytes(rpu_data)
    
    def _create_high_nit_rpu_data(self) -> bytes:
        """Create high-nit RPU data (max 4000 nits)"""
        rpu_data = bytearray()
        
        # RPU header
        rpu_data.extend(b'\x00\x00')  # Magic bytes
        rpu_data.extend(b'\x07')      # Profile 7
        rpu_data.extend(b'\x01')      # Level 1
        
        # High-nit frame data
        for i in range(100):
            rpu_data.extend(b'\x00\x00\x00\x00')  # Frame marker
            rpu_data.extend(bytes([i % 100]))     # Luminance min (0-99)
            rpu_data.extend(bytes([(i * 2) % 255]))  # Luminance max (0-254)
            rpu_data.extend(bytes([(i * 2) % 255]))  # Luminance avg (0-254)
            rpu_data.extend(bytes([i % 100]))     # Knee point x
            rpu_data.extend(bytes([(i + 10) % 100]))  # Knee point y
            rpu_data.extend(bytes([i % 100, (i + 5) % 100]))  # Bezier data
        
        return bytes(rpu_data)
    
    def _create_mixed_content_rpu_data(self) -> bytes:
        """Create mixed content RPU data (varying luminance)"""
        rpu_data = bytearray()
        
        # RPU header
        rpu_data.extend(b'\x00\x00')  # Magic bytes
        rpu_data.extend(b'\x07')      # Profile 7
        rpu_data.extend(b'\x01')      # Level 1
        
        # Mixed content frame data
        for i in range(150):
            rpu_data.extend(b'\x00\x00\x00\x00')  # Frame marker
            
            # Vary luminance based on frame number
            if i < 50:  # Low-nit section
                min_lum = i % 20
                max_lum = (i * 2) % 200
                avg_lum = (i * 3) % 100
            elif i < 100:  # Mid-nit section
                min_lum = (i % 50) + 50
                max_lum = (i * 2) % 255  # Limited to byte range
                avg_lum = (i * 2) % 255
            else:  # High-nit section
                min_lum = (i % 100) + 100
                max_lum = (i * 2) % 255  # Limited to byte range
                avg_lum = (i * 2) % 255
            
            rpu_data.extend(bytes([min_lum]))
            rpu_data.extend(bytes([max_lum]))
            rpu_data.extend(bytes([avg_lum]))
            rpu_data.extend(bytes([i % 100]))     # Knee point x
            rpu_data.extend(bytes([(i + 10) % 100]))  # Knee point y
            rpu_data.extend(bytes([i % 100, (i + 5) % 100]))  # Bezier data
        
        return bytes(rpu_data)
    
    def _create_minimal_rpu_data(self) -> bytes:
        """Create minimal RPU data (single frame)"""
        rpu_data = bytearray()
        
        # RPU header
        rpu_data.extend(b'\x00\x00')  # Magic bytes
        rpu_data.extend(b'\x07')      # Profile 7
        rpu_data.extend(b'\x01')      # Level 1
        
        # Single frame
        rpu_data.extend(b'\x00\x00\x00\x00')  # Frame marker
        rpu_data.extend(b'\x10')      # Luminance min (16)
        rpu_data.extend(b'\x64')      # Luminance max (100)
        rpu_data.extend(b'\x32')      # Luminance avg (50)
        rpu_data.extend(b'\x32')      # Knee point x (50)
        rpu_data.extend(b'\x40')      # Knee point y (64)
        rpu_data.extend(b'\x00\x00')  # Bezier data
        
        return bytes(rpu_data)
    
    def _get_golden_file_path(self, test_case: str) -> Path:
        """Get path to golden file for test case"""
        return self.test_data_dir / f"{test_case}_golden.json"
    
    def _create_golden_file(self, test_case: str) -> dict:
        """Create golden file for test case"""
        rpu_data = self._create_golden_rpu_data(test_case)
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        hdr10plus_metadata = self.generator.convert(rpu_metadata)
        
        # Save golden file
        golden_path = self._get_golden_file_path(test_case)
        with open(golden_path, 'w') as f:
            json.dump(hdr10plus_metadata, f, indent=2)
        
        return hdr10plus_metadata
    
    def test_low_nit_golden_file(self):
        """Test against low-nit golden file"""
        test_case = "low_nit"
        golden_path = self._get_golden_file_path(test_case)
        
        # Create golden file if it doesn't exist
        if not golden_path.exists():
            golden_metadata = self._create_golden_file(test_case)
        else:
            with open(golden_path, 'r') as f:
                golden_metadata = json.load(f)
        
        # Generate new metadata
        rpu_data = self._create_golden_rpu_data(test_case)
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        current_metadata = self.generator.convert(rpu_metadata)
        
        # Compare with golden file
        self._compare_metadata(golden_metadata, current_metadata, test_case)
    
    def test_high_nit_golden_file(self):
        """Test against high-nit golden file"""
        test_case = "high_nit"
        golden_path = self._get_golden_file_path(test_case)
        
        # Create golden file if it doesn't exist
        if not golden_path.exists():
            golden_metadata = self._create_golden_file(test_case)
        else:
            with open(golden_path, 'r') as f:
                golden_metadata = json.load(f)
        
        # Generate new metadata
        rpu_data = self._create_golden_rpu_data(test_case)
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        current_metadata = self.generator.convert(rpu_metadata)
        
        # Compare with golden file
        self._compare_metadata(golden_metadata, current_metadata, test_case)
    
    def test_mixed_content_golden_file(self):
        """Test against mixed content golden file"""
        test_case = "mixed_content"
        golden_path = self._get_golden_file_path(test_case)
        
        # Create golden file if it doesn't exist
        if not golden_path.exists():
            golden_metadata = self._create_golden_file(test_case)
        else:
            with open(golden_path, 'r') as f:
                golden_metadata = json.load(f)
        
        # Generate new metadata
        rpu_data = self._create_golden_rpu_data(test_case)
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        current_metadata = self.generator.convert(rpu_metadata)
        
        # Compare with golden file
        self._compare_metadata(golden_metadata, current_metadata, test_case)
    
    def test_minimal_golden_file(self):
        """Test against minimal golden file"""
        test_case = "minimal"
        golden_path = self._get_golden_file_path(test_case)
        
        # Create golden file if it doesn't exist
        if not golden_path.exists():
            golden_metadata = self._create_golden_file(test_case)
        else:
            with open(golden_path, 'r') as f:
                golden_metadata = json.load(f)
        
        # Generate new metadata
        rpu_data = self._create_golden_rpu_data(test_case)
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        current_metadata = self.generator.convert(rpu_metadata)
        
        # Compare with golden file
        self._compare_metadata(golden_metadata, current_metadata, test_case)
    
    def _compare_metadata(self, golden: dict, current: dict, test_case: str):
        """Compare golden and current metadata"""
        # Check that both are valid
        golden_valid, golden_errors = self.validator.validate_metadata(golden)
        current_valid, current_errors = self.validator.validate_metadata(current)
        
        assert golden_valid, f"Golden metadata invalid for {test_case}: {golden_errors}"
        assert current_valid, f"Current metadata invalid for {test_case}: {current_errors}"
        
        # Compare key fields
        key_fields = [
            'version', 'targeted_system_display_maximum_luminance',
            'targeted_system_display_actual_peak_luminance_flag',
            'num_bezier_curve_anchors', 'knee_point_x', 'knee_point_y',
            'max_content_light_level', 'max_frame_average_light_level'
        ]
        
        for field in key_fields:
            assert golden[field] == current[field], \
                f"Field {field} differs in {test_case}: golden={golden[field]}, current={current[field]}"
        
        # Compare bezier curve anchors
        golden_anchors = golden.get('bezier_curve_anchors', [])
        current_anchors = current.get('bezier_curve_anchors', [])
        
        assert len(golden_anchors) == len(current_anchors), \
            f"Bezier anchors count differs in {test_case}: golden={len(golden_anchors)}, current={len(current_anchors)}"
        
        for i, (golden_anchor, current_anchor) in enumerate(zip(golden_anchors, current_anchors)):
            assert abs(golden_anchor['x'] - current_anchor['x']) < 1e-6, \
                f"Bezier anchor {i} X differs in {test_case}"
            # Allow small differences in Y values due to floating point precision
            assert abs(golden_anchor['y'] - current_anchor['y']) < 1e-3, \
                f"Bezier anchor {i} Y differs in {test_case}: golden={golden_anchor['y']}, current={current_anchor['y']}"
        
        # Compare scene data
        golden_scenes = golden.get('scene_or_frame', [])
        current_scenes = current.get('scene_or_frame', [])
        
        assert len(golden_scenes) == len(current_scenes), \
            f"Scene count differs in {test_case}: golden={len(golden_scenes)}, current={len(current_scenes)}"
        
        for i, (golden_scene, current_scene) in enumerate(zip(golden_scenes, current_scenes)):
            self._compare_scene_data(golden_scene, current_scene, test_case, i)
    
    def _compare_scene_data(self, golden_scene: dict, current_scene: dict, test_case: str, scene_index: int):
        """Compare scene data"""
        scene_key_fields = [
            'targeted_system_display_maximum_luminance',
            'targeted_system_display_actual_peak_luminance_flag',
            'num_bezier_curve_anchors', 'knee_point_x', 'knee_point_y'
        ]
        
        for field in scene_key_fields:
            assert golden_scene[field] == current_scene[field], \
                f"Scene {scene_index} field {field} differs in {test_case}"
        
        # Compare scene bezier anchors
        golden_anchors = golden_scene.get('bezier_curve_anchors', [])
        current_anchors = current_scene.get('bezier_curve_anchors', [])
        
        assert len(golden_anchors) == len(current_anchors), \
            f"Scene {scene_index} bezier anchors count differs in {test_case}"
        
        for i, (golden_anchor, current_anchor) in enumerate(zip(golden_anchors, current_anchors)):
            assert abs(golden_anchor['x'] - current_anchor['x']) < 1e-6, \
                f"Scene {scene_index} bezier anchor {i} X differs in {test_case}"
            # Allow small differences in Y values due to floating point precision
            assert abs(golden_anchor['y'] - current_anchor['y']) < 1e-3, \
                f"Scene {scene_index} bezier anchor {i} Y differs in {test_case}: golden={golden_anchor['y']}, current={current_anchor['y']}"
    
    def test_golden_file_regression(self):
        """Test that golden files don't regress over time"""
        test_cases = ["low_nit", "high_nit", "mixed_content", "minimal"]
        
        for test_case in test_cases:
            golden_path = self._get_golden_file_path(test_case)
            
            if golden_path.exists():
                # Load existing golden file
                with open(golden_path, 'r') as f:
                    golden_metadata = json.load(f)
                
                # Validate it's still valid
                is_valid, errors = self.validator.validate_metadata(golden_metadata)
                assert is_valid, f"Golden file {test_case} is no longer valid: {errors}"
                
                # Check it meets our quality standards
                self._check_golden_quality(golden_metadata, test_case)
    
    def _check_golden_quality(self, metadata: dict, test_case: str):
        """Check that golden file meets quality standards"""
        # Check version
        assert metadata.get('version') == '1.0', f"Golden file {test_case} has wrong version"
        
        # Check luminance ranges
        max_lum = metadata.get('targeted_system_display_maximum_luminance', 0)
        assert 100 <= max_lum <= 10000, f"Golden file {test_case} has invalid max luminance: {max_lum}"
        
        # Check knee points
        knee_x = metadata.get('knee_point_x', 0)
        knee_y = metadata.get('knee_point_y', 0)
        assert 0 <= knee_x <= 1, f"Golden file {test_case} has invalid knee_x: {knee_x}"
        assert 0 <= knee_y <= 1, f"Golden file {test_case} has invalid knee_y: {knee_y}"
        
        # Check bezier anchors
        anchors = metadata.get('bezier_curve_anchors', [])
        assert len(anchors) > 0, f"Golden file {test_case} has no bezier anchors"
        assert len(anchors) <= 15, f"Golden file {test_case} has too many bezier anchors: {len(anchors)}"
        
        # Check monotonicity
        for i in range(1, len(anchors)):
            assert anchors[i]['x'] > anchors[i-1]['x'], \
                f"Golden file {test_case} bezier anchors not monotonic"
        
        # Check scene data (some test cases might not have scenes)
        scenes = metadata.get('scene_or_frame', [])
        if test_case != "minimal":  # Minimal case might not have scenes
            assert len(scenes) > 0, f"Golden file {test_case} has no scenes"
        
        for i, scene in enumerate(scenes):
            scene_max_lum = scene.get('targeted_system_display_maximum_luminance', 0)
            assert 100 <= scene_max_lum <= 10000, \
                f"Golden file {test_case} scene {i} has invalid max luminance: {scene_max_lum}"
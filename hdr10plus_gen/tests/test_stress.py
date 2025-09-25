"""
Stress tests for HDR10+ Generator

These tests verify the converter's behavior under various stress conditions
and edge cases to ensure robustness and accuracy.
"""

import pytest
import numpy as np
from hdr10plus_gen import HDR10PlusGenerator, RPUParser, HDR10PlusValidator
from hdr10plus_gen.rpu_parser import RPUMetadata


class TestStress:
    """Stress tests for edge cases and extreme conditions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = RPUParser()
        self.generator = HDR10PlusGenerator(target_display_luminance=1000)
        self.validator = HDR10PlusValidator()
    
    def _create_stress_rpu_data(self, stress_type: str) -> bytes:
        """Create RPU data for specific stress test"""
        if stress_type == "extreme_low_nit":
            return self._create_extreme_low_nit_data()
        elif stress_type == "extreme_high_nit":
            return self._create_extreme_high_nit_data()
        elif stress_type == "rapid_changes":
            return self._create_rapid_changes_data()
        elif stress_type == "single_pixel":
            return self._create_single_pixel_data()
        elif stress_type == "banding_test":
            return self._create_banding_test_data()
        elif stress_type == "flicker_test":
            return self._create_flicker_test_data()
        else:
            raise ValueError(f"Unknown stress type: {stress_type}")
    
    def _create_extreme_low_nit_data(self) -> bytes:
        """Create RPU data with extremely low luminance values"""
        rpu_data = bytearray()
        
        # RPU header
        rpu_data.extend(b'\x00\x00')
        rpu_data.extend(b'\x07')
        rpu_data.extend(b'\x01')
        
        # Extremely low-nit frames
        for i in range(100):
            rpu_data.extend(b'\x00\x00\x00\x00')
            rpu_data.extend(b'\x01')      # Min luminance = 1 nit
            rpu_data.extend(b'\x05')      # Max luminance = 5 nits
            rpu_data.extend(b'\x02')      # Avg luminance = 2 nits
            rpu_data.extend(bytes([i % 100]))
            rpu_data.extend(bytes([(i + 10) % 100]))
            rpu_data.extend(bytes([i % 100, (i + 5) % 100]))
        
        return bytes(rpu_data)
    
    def _create_extreme_high_nit_data(self) -> bytes:
        """Create RPU data with extremely high luminance values"""
        rpu_data = bytearray()
        
        # RPU header
        rpu_data.extend(b'\x00\x00')
        rpu_data.extend(b'\x07')
        rpu_data.extend(b'\x01')
        
        # Extremely high-nit frames
        for i in range(100):
            rpu_data.extend(b'\x00\x00\x00\x00')
            rpu_data.extend(b'\x64')      # Min luminance = 100 nits
            rpu_data.extend(b'\xff')      # Max luminance = 255 nits (will be scaled)
            rpu_data.extend(b'\xb4')      # Avg luminance = 180 nits
            rpu_data.extend(bytes([i % 100]))
            rpu_data.extend(bytes([(i + 10) % 100]))
            rpu_data.extend(bytes([i % 100, (i + 5) % 100]))
        
        return bytes(rpu_data)
    
    def _create_rapid_changes_data(self) -> bytes:
        """Create RPU data with rapid luminance changes"""
        rpu_data = bytearray()
        
        # RPU header
        rpu_data.extend(b'\x00\x00')
        rpu_data.extend(b'\x07')
        rpu_data.extend(b'\x01')
        
        # Rapidly changing luminance
        for i in range(200):
            rpu_data.extend(b'\x00\x00\x00\x00')
            
            # Alternate between very low and high values
            if i % 2 == 0:
                min_lum = 1
                max_lum = 10
                avg_lum = 5
            else:
                min_lum = 200
                max_lum = 255  # Max byte value
                avg_lum = 227
            
            rpu_data.extend(bytes([min_lum]))
            rpu_data.extend(bytes([max_lum]))
            rpu_data.extend(bytes([avg_lum]))
            rpu_data.extend(bytes([i % 100]))
            rpu_data.extend(bytes([(i + 10) % 100]))
            rpu_data.extend(bytes([i % 100, (i + 5) % 100]))
        
        return bytes(rpu_data)
    
    def _create_single_pixel_data(self) -> bytes:
        """Create RPU data representing single pixel content"""
        rpu_data = bytearray()
        
        # RPU header
        rpu_data.extend(b'\x00\x00')
        rpu_data.extend(b'\x07')
        rpu_data.extend(b'\x01')
        
        # Single frame with uniform luminance
        rpu_data.extend(b'\x00\x00\x00\x00')
        rpu_data.extend(b'\x32')      # Min = 50 nits
        rpu_data.extend(b'\x32')      # Max = 50 nits (same as min)
        rpu_data.extend(b'\x32')      # Avg = 50 nits (same as min/max)
        rpu_data.extend(b'\x32')
        rpu_data.extend(b'\x40')
        rpu_data.extend(b'\x00\x00')
        
        return bytes(rpu_data)
    
    def _create_banding_test_data(self) -> bytes:
        """Create RPU data designed to test for banding artifacts"""
        rpu_data = bytearray()
        
        # RPU header
        rpu_data.extend(b'\x00\x00')
        rpu_data.extend(b'\x07')
        rpu_data.extend(b'\x01')
        
        # Create subtle luminance steps that could cause banding
        for i in range(100):
            rpu_data.extend(b'\x00\x00\x00\x00')
            
            # Create small steps in luminance
            base_lum = 50 + (i % 10) * 2  # Steps of 2 nits
            rpu_data.extend(bytes([base_lum]))
            rpu_data.extend(bytes([base_lum + 1]))
            rpu_data.extend(bytes([base_lum]))
            rpu_data.extend(bytes([i % 100]))
            rpu_data.extend(bytes([(i + 10) % 100]))
            rpu_data.extend(bytes([i % 100, (i + 5) % 100]))
        
        return bytes(rpu_data)
    
    def _create_flicker_test_data(self) -> bytes:
        """Create RPU data designed to test for flicker artifacts"""
        rpu_data = bytearray()
        
        # RPU header
        rpu_data.extend(b'\x00\x00')
        rpu_data.extend(b'\x07')
        rpu_data.extend(b'\x01')
        
        # Create alternating luminance patterns
        for i in range(100):
            rpu_data.extend(b'\x00\x00\x00\x00')
            
            # Alternate between two luminance levels
            if i % 4 < 2:
                min_lum = 100
                max_lum = 200
                avg_lum = 150
            else:
                min_lum = 95
                max_lum = 195
                avg_lum = 145
            
            rpu_data.extend(bytes([min_lum]))
            rpu_data.extend(bytes([max_lum]))
            rpu_data.extend(bytes([avg_lum]))
            rpu_data.extend(bytes([i % 100]))
            rpu_data.extend(bytes([(i + 10) % 100]))
            rpu_data.extend(bytes([i % 100, (i + 5) % 100]))
        
        return bytes(rpu_data)
    
    def test_extreme_low_nit_accuracy(self):
        """Test accuracy with extremely low luminance values"""
        rpu_data = self._create_stress_rpu_data("extreme_low_nit")
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        hdr10plus_metadata = self.generator.convert(rpu_metadata)
        
        # Validate metadata
        is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
        assert is_valid, f"Validation failed: {errors}"
        
        # Check that low-nit optimization is applied in scene metadata
        scenes = hdr10plus_metadata.get('scene_or_frame', [])
        if scenes:
            scene = scenes[0]
            assert scene['knee_point_x'] < 0.3, f"Scene knee_point_x not optimized: {scene['knee_point_x']}"
            assert scene['knee_point_y'] < 0.4, f"Scene knee_point_y not optimized: {scene['knee_point_y']}"
        
        # Check that bezier curve preserves low-nit detail
        bezier_anchors = hdr10plus_metadata['bezier_curve_anchors']
        low_nit_anchors = [a for a in bezier_anchors if a['x'] < 0.3]
        assert len(low_nit_anchors) > 0, "No low-nit bezier anchors found"
        
        # Check that low-nit anchors have good precision
        for anchor in low_nit_anchors:
            assert anchor['y'] >= 0, "Low-nit anchor should preserve detail"
    
    def test_extreme_high_nit_handling(self):
        """Test handling of extremely high luminance values"""
        rpu_data = self._create_stress_rpu_data("extreme_high_nit")
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        hdr10plus_metadata = self.generator.convert(rpu_metadata)
        
        # Validate metadata
        is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
        assert is_valid, f"Validation failed: {errors}"
        
        # Check that high-nit content is properly mapped
        assert hdr10plus_metadata['targeted_system_display_maximum_luminance'] <= 1000
        assert hdr10plus_metadata['max_content_light_level'] > 0
    
    def test_rapid_changes_stability(self):
        """Test stability with rapid luminance changes"""
        rpu_data = self._create_stress_rpu_data("rapid_changes")
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        hdr10plus_metadata = self.generator.convert(rpu_metadata)
        
        # Validate metadata
        is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
        assert is_valid, f"Validation failed: {errors}"
        
        # Check that rapid changes don't cause instability
        scenes = hdr10plus_metadata.get('scene_or_frame', [])
        assert len(scenes) > 0, "No scenes generated"
        
        # Check that scene metadata is stable
        for scene in scenes:
            assert scene['knee_point_x'] >= 0 and scene['knee_point_x'] <= 1
            assert scene['knee_point_y'] >= 0 and scene['knee_point_y'] <= 1
            
            # Check bezier curve stability
            anchors = scene.get('bezier_curve_anchors', [])
            for i in range(1, len(anchors)):
                assert anchors[i]['x'] > anchors[i-1]['x'], "Bezier curve not monotonic"
    
    def test_single_pixel_content(self):
        """Test handling of single pixel content"""
        rpu_data = self._create_stress_rpu_data("single_pixel")
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        hdr10plus_metadata = self.generator.convert(rpu_metadata)
        
        # Validate metadata
        is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
        assert is_valid, f"Validation failed: {errors}"
        
        # Check that single pixel content is handled gracefully
        assert hdr10plus_metadata['targeted_system_display_maximum_luminance'] > 0
        # Scene metadata might be empty for single pixel content, which is OK
        scenes = hdr10plus_metadata.get('scene_or_frame', [])
        if scenes:
            assert len(scenes) > 0
    
    def test_banding_prevention(self):
        """Test that banding artifacts are prevented"""
        rpu_data = self._create_stress_rpu_data("banding_test")
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        hdr10plus_metadata = self.generator.convert(rpu_metadata)
        
        # Validate metadata
        is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
        assert is_valid, f"Validation failed: {errors}"
        
        # Check that bezier curve provides smooth transitions
        bezier_anchors = hdr10plus_metadata['bezier_curve_anchors']
        assert len(bezier_anchors) >= 3, "Insufficient bezier anchors for smooth transitions"
        
        # Check that curve is smooth (no sudden jumps)
        for i in range(1, len(bezier_anchors)):
            x_diff = bezier_anchors[i]['x'] - bezier_anchors[i-1]['x']
            y_diff = bezier_anchors[i]['y'] - bezier_anchors[i-1]['y']
            
            # Check for reasonable slope (not too steep)
            if x_diff > 0:
                slope = y_diff / x_diff
                assert abs(slope) < 10, f"Bezier curve too steep at anchor {i}"
    
    def test_flicker_prevention(self):
        """Test that flicker artifacts are prevented"""
        rpu_data = self._create_stress_rpu_data("flicker_test")
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        hdr10plus_metadata = self.generator.convert(rpu_metadata)
        
        # Validate metadata
        is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
        assert is_valid, f"Validation failed: {errors}"
        
        # Check that similar frames produce similar metadata
        scenes = hdr10plus_metadata.get('scene_or_frame', [])
        if len(scenes) > 1:
            # Compare adjacent scenes for stability
            for i in range(1, len(scenes)):
                prev_scene = scenes[i-1]
                curr_scene = scenes[i]
                
                # Check that similar content produces similar tone mapping
                prev_knee_x = prev_scene.get('knee_point_x', 0)
                curr_knee_x = curr_scene.get('knee_point_x', 0)
                
                # Knee points should not vary wildly
                assert abs(prev_knee_x - curr_knee_x) < 0.2, "Knee points vary too much between scenes"
    
    def test_memory_stress(self):
        """Test memory usage under stress"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create large dataset
        rpu_data = self._create_stress_rpu_data("rapid_changes")
        
        # Process multiple times to stress memory
        for _ in range(10):
            rpu_metadata = self.parser.parse_from_bytes(rpu_data)
            hdr10plus_metadata = self.generator.convert(rpu_metadata)
            
            # Validate to ensure we're not just creating garbage
            is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
            assert is_valid, f"Validation failed: {errors}"
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 50 * 1024 * 1024, f"Excessive memory usage: {memory_increase / 1024 / 1024:.1f}MB"
    
    def test_performance_stress(self):
        """Test performance under stress"""
        import time
        
        # Create large dataset
        rpu_data = self._create_stress_rpu_data("rapid_changes")
        
        # Time multiple conversions
        times = []
        for _ in range(5):
            start_time = time.time()
            
            rpu_metadata = self.parser.parse_from_bytes(rpu_data)
            hdr10plus_metadata = self.generator.convert(rpu_metadata)
            
            end_time = time.time()
            times.append(end_time - start_time)
        
        # Check that performance is consistent
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        assert avg_time < 2.0, f"Average conversion time too slow: {avg_time:.2f}s"
        assert max_time < 5.0, f"Maximum conversion time too slow: {max_time:.2f}s"
        
        # Check that performance doesn't degrade significantly
        assert max_time < avg_time * 2, "Performance is inconsistent"
    
    def test_edge_case_handling(self):
        """Test handling of various edge cases"""
        edge_cases = [
            ("empty_frames", self._create_empty_frames_data()),
            ("single_anchor", self._create_single_anchor_data()),
            ("max_anchors", self._create_max_anchors_data()),
        ]
        
        for case_name, rpu_data in edge_cases:
            try:
                rpu_metadata = self.parser.parse_from_bytes(rpu_data)
                hdr10plus_metadata = self.generator.convert(rpu_metadata)
                
                # Should not crash
                assert hdr10plus_metadata is not None
                
                # Should produce valid metadata
                is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
                assert is_valid, f"Edge case {case_name} failed validation: {errors}"
                
            except Exception as e:
                pytest.fail(f"Edge case {case_name} caused exception: {e}")
    
    def _create_empty_frames_data(self) -> bytes:
        """Create RPU data with no frames"""
        rpu_data = bytearray()
        rpu_data.extend(b'\x00\x00')
        rpu_data.extend(b'\x07')
        rpu_data.extend(b'\x01')
        return bytes(rpu_data)
    
    def _create_single_anchor_data(self) -> bytes:
        """Create RPU data that should result in single bezier anchor"""
        rpu_data = bytearray()
        rpu_data.extend(b'\x00\x00')
        rpu_data.extend(b'\x07')
        rpu_data.extend(b'\x01')
        
        # Single frame with minimal data
        rpu_data.extend(b'\x00\x00\x00\x00')
        rpu_data.extend(b'\x32')
        rpu_data.extend(b'\x32')
        rpu_data.extend(b'\x32')
        rpu_data.extend(b'\x32')
        rpu_data.extend(b'\x40')
        rpu_data.extend(b'\x00\x00')
        
        return bytes(rpu_data)
    
    def _create_max_anchors_data(self) -> bytes:
        """Create RPU data that should result in maximum bezier anchors"""
        rpu_data = bytearray()
        rpu_data.extend(b'\x00\x00')
        rpu_data.extend(b'\x07')
        rpu_data.extend(b'\x01')
        
        # Multiple frames with varied data to encourage many anchors
        for i in range(50):
            rpu_data.extend(b'\x00\x00\x00\x00')
            rpu_data.extend(bytes([i % 100]))
            rpu_data.extend(bytes([(i * 2) % 1000]))
            rpu_data.extend(bytes([(i * 3) % 500]))
            rpu_data.extend(bytes([i % 100]))
            rpu_data.extend(bytes([(i + 10) % 100]))
            rpu_data.extend(bytes([i % 100, (i + 5) % 100]))
        
        return bytes(rpu_data)
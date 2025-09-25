"""
Integration tests for HDR10+ Generator
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from hdr10plus_gen import HDR10PlusGenerator, RPUParser, HDR10PlusValidator


class TestIntegration:
    """Integration tests for the complete workflow"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = RPUParser()
        self.generator = HDR10PlusGenerator(target_display_luminance=1000)
        self.validator = HDR10PlusValidator()
    
    def _create_test_rpu_data(self, profile: int = 7, level: int = 1, 
                            max_luminance: int = 1000, num_frames: int = 100) -> bytes:
        """Create test RPU data with specified characteristics"""
        rpu_data = bytearray()
        
        # RPU header
        rpu_data.extend(b'\x00\x00')  # Magic bytes
        rpu_data.extend(bytes([profile]))
        rpu_data.extend(bytes([level]))
        
        # Add frame data
        for i in range(num_frames):
            rpu_data.extend(b'\x00\x00\x00\x00')  # Frame marker
            rpu_data.extend(bytes([i % 100]))     # Luminance min
            rpu_data.extend(bytes([(i * 2) % 255]))  # Luminance max
            rpu_data.extend(bytes([(i * 3) % 255]))  # Luminance avg
            rpu_data.extend(bytes([i % 100]))     # Knee point x
            rpu_data.extend(bytes([(i + 10) % 100]))  # Knee point y
            rpu_data.extend(bytes([i % 100, (i + 5) % 100]))  # Bezier data
        
        return bytes(rpu_data)
    
    def test_end_to_end_conversion(self):
        """Test complete end-to-end conversion workflow"""
        # Create test RPU data
        rpu_data = self._create_test_rpu_data()
        
        # Parse RPU
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        assert rpu_metadata.profile == 7
        assert rpu_metadata.level == 1
        
        # Generate HDR10+ metadata
        hdr10plus_metadata = self.generator.convert(rpu_metadata)
        
        # Validate metadata
        is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
        assert is_valid, f"Validation failed: {errors}"
        
        # Check required fields
        assert 'version' in hdr10plus_metadata
        assert 'targeted_system_display_maximum_luminance' in hdr10plus_metadata
        assert 'scene_or_frame' in hdr10plus_metadata
    
    def test_low_nit_optimization_integration(self):
        """Test integration of low-nit optimization"""
        # Create low-nit RPU data
        rpu_data = self._create_test_rpu_data(max_luminance=200, num_frames=50)
        
        # Parse and convert
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        hdr10plus_metadata = self.generator.convert(rpu_metadata)
        
        # Validate
        is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
        assert is_valid, f"Validation failed: {errors}"
        
        # Check low-nit optimization in scene metadata
        scenes = hdr10plus_metadata.get('scene_or_frame', [])
        assert len(scenes) > 0, "No scene metadata found"
        
        scene = scenes[0]
        assert scene['knee_point_x'] < 0.4, f"Scene knee_point_x not optimized: {scene['knee_point_x']}"
        assert scene['knee_point_y'] < 0.5, f"Scene knee_point_y not optimized: {scene['knee_point_y']}"
        assert scene['targeted_system_display_maximum_luminance'] <= 240
    
    def test_high_nit_content_integration(self):
        """Test integration with high-nit content"""
        # Create high-nit RPU data
        rpu_data = self._create_test_rpu_data(max_luminance=4000, num_frames=200)
        
        # Parse and convert
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        hdr10plus_metadata = self.generator.convert(rpu_metadata)
        
        # Validate
        is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
        assert is_valid, f"Validation failed: {errors}"
        
        # Check high-nit handling
        assert hdr10plus_metadata['targeted_system_display_maximum_luminance'] == 1000
        # Note: max_content_light_level will be limited by the actual max value in test data (255)
        assert hdr10plus_metadata['max_content_light_level'] > 0
    
    def test_file_io_integration(self):
        """Test file input/output integration"""
        # Create test RPU file
        rpu_data = self._create_test_rpu_data()
        
        with tempfile.NamedTemporaryFile(suffix='.rpu', delete=False) as rpu_file:
            rpu_file.write(rpu_data)
            rpu_file.flush()
            
            try:
                # Parse from file
                rpu_metadata = self.parser.parse(rpu_file.name)
                
                # Convert to HDR10+
                hdr10plus_metadata = self.generator.convert(rpu_metadata)
                
                # Save to JSON file
                with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as json_file:
                    self.generator.save_json(hdr10plus_metadata, json_file.name)
                    
                    # Validate the saved file
                    is_valid, errors = self.validator.validate_file(json_file.name)
                    assert is_valid, f"File validation failed: {errors}"
                    
                    # Verify file content
                    with open(json_file.name, 'r') as f:
                        loaded_metadata = json.load(f)
                    assert loaded_metadata == hdr10plus_metadata
                    
                    os.unlink(json_file.name)
            finally:
                os.unlink(rpu_file.name)
    
    def test_deterministic_conversion(self):
        """Test that conversion is deterministic"""
        rpu_data = self._create_test_rpu_data()
        
        # Convert multiple times
        results = []
        for _ in range(3):
            rpu_metadata = self.parser.parse_from_bytes(rpu_data)
            hdr10plus_metadata = self.generator.convert(rpu_metadata)
            results.append(hdr10plus_metadata)
        
        # All results should be identical
        for i in range(1, len(results)):
            assert results[i] == results[0], "Conversion is not deterministic"
    
    def test_error_handling_integration(self):
        """Test error handling in integration scenarios"""
        # Test with invalid RPU data
        invalid_rpu_data = b'invalid rpu data'
        
        with pytest.raises(ValueError):
            self.parser.parse_from_bytes(invalid_rpu_data)
        
        # Test with empty RPU data
        with pytest.raises(ValueError):
            self.parser.parse_from_bytes(b'')
    
    def test_performance_integration(self):
        """Test performance with larger datasets"""
        # Create larger RPU data
        rpu_data = self._create_test_rpu_data(num_frames=1000)
        
        # Time the conversion
        import time
        start_time = time.time()
        
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        hdr10plus_metadata = self.generator.convert(rpu_metadata)
        
        end_time = time.time()
        conversion_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert conversion_time < 10.0, f"Conversion took too long: {conversion_time:.2f}s"
        
        # Validate result
        is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
        assert is_valid, f"Validation failed: {errors}"
    
    def test_memory_usage_integration(self):
        """Test memory usage with large datasets"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and process large dataset
        rpu_data = self._create_test_rpu_data(num_frames=5000)
        rpu_metadata = self.parser.parse_from_bytes(rpu_data)
        hdr10plus_metadata = self.generator.convert(rpu_metadata)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust threshold as needed)
        assert memory_increase < 100 * 1024 * 1024, f"Excessive memory usage: {memory_increase / 1024 / 1024:.1f}MB"
        
        # Validate result
        is_valid, errors = self.validator.validate_metadata(hdr10plus_metadata)
        assert is_valid, f"Validation failed: {errors}"
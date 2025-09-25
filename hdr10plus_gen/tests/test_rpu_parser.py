"""
Tests for RPU Parser
"""

import pytest
import tempfile
import os
from hdr10plus_gen.rpu_parser import RPUParser, RPUMetadata


class TestRPUParser:
    """Test cases for RPU parser"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = RPUParser()
        self.sample_rpu_data = self._create_sample_rpu_data()
    
    def _create_sample_rpu_data(self) -> bytes:
        """Create sample RPU data for testing"""
        # Create a minimal RPU-like data structure
        rpu_data = bytearray()
        
        # RPU header
        rpu_data.extend(b'\x00\x00')  # Magic bytes
        rpu_data.extend(b'\x07')      # Profile 7
        rpu_data.extend(b'\x01')      # Level 1
        
        # Add some frame data
        for i in range(100):
            rpu_data.extend(b'\x00\x00\x00\x00')  # Frame marker
            rpu_data.extend(bytes([i % 100]))     # Luminance min
            rpu_data.extend(bytes([(i * 2) % 255]))  # Luminance max
            rpu_data.extend(bytes([(i * 3) % 255]))   # Luminance avg
            rpu_data.extend(bytes([i % 100]))     # Knee point x
            rpu_data.extend(bytes([(i + 10) % 100]))  # Knee point y
            rpu_data.extend(bytes([i % 100, (i + 5) % 100]))  # Bezier data
        
        return bytes(rpu_data)
    
    def test_parse_from_bytes(self):
        """Test parsing RPU data from bytes"""
        metadata = self.parser.parse_from_bytes(self.sample_rpu_data)
        
        assert isinstance(metadata, RPUMetadata)
        assert metadata.profile == 7
        assert metadata.level == 1
        assert len(metadata.frame_metadata) > 0
        assert len(metadata.scene_cuts) >= 0
        assert len(metadata.shot_cuts) >= 0
    
    def test_parse_from_file(self):
        """Test parsing RPU data from file"""
        with tempfile.NamedTemporaryFile(suffix='.rpu', delete=False) as f:
            f.write(self.sample_rpu_data)
            f.flush()
            
            try:
                metadata = self.parser.parse(f.name)
                assert isinstance(metadata, RPUMetadata)
                assert metadata.profile == 7
                assert metadata.level == 1
            finally:
                os.unlink(f.name)
    
    def test_parse_invalid_data(self):
        """Test parsing invalid RPU data"""
        invalid_data = b'invalid data'
        
        with pytest.raises(ValueError, match="Invalid RPU data"):
            self.parser.parse_from_bytes(invalid_data)
    
    def test_parse_empty_data(self):
        """Test parsing empty RPU data"""
        with pytest.raises(ValueError, match="No RPU data to parse"):
            self.parser.parse_from_bytes(b'')
    
    def test_get_luminance_statistics(self):
        """Test luminance statistics calculation"""
        frame_data = {
            'luminance_min': 10.0,
            'luminance_max': 800.0,
            'luminance_avg': 200.0
        }
        
        stats = self.parser.get_luminance_statistics(frame_data)
        
        assert 'percentile_10' in stats
        assert 'percentile_50' in stats
        assert 'percentile_99' in stats
        
        # Check that percentiles are in ascending order
        percentiles = [stats[f'percentile_{p}'] for p in [10, 25, 50, 75, 90, 95, 99, 99.9]]
        assert all(percentiles[i] <= percentiles[i+1] for i in range(len(percentiles)-1))
        
        # Check that values are within reasonable bounds
        assert all(0 <= p <= 1000 for p in percentiles)
    
    def test_mastering_display_extraction(self):
        """Test mastering display information extraction"""
        metadata = self.parser.parse_from_bytes(self.sample_rpu_data)
        
        mastering_display = metadata.mastering_display
        assert 'primaries' in mastering_display
        assert 'max_luminance' in mastering_display
        assert 'min_luminance' in mastering_display
        
        primaries = mastering_display['primaries']
        assert 'red' in primaries
        assert 'green' in primaries
        assert 'blue' in primaries
        assert 'white' in primaries
    
    def test_content_light_level_extraction(self):
        """Test content light level information extraction"""
        metadata = self.parser.parse_from_bytes(self.sample_rpu_data)
        
        content_light_level = metadata.content_light_level
        assert 'max_content_light_level' in content_light_level
        assert 'max_frame_average_light_level' in content_light_level
        
        assert content_light_level['max_content_light_level'] > 0
        assert content_light_level['max_frame_average_light_level'] > 0
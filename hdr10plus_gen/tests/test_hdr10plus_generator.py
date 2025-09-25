"""
Tests for HDR10+ Generator
"""

import pytest
import tempfile
import os
import json
from hdr10plus_gen.hdr10plus_generator import HDR10PlusGenerator, ToneMappingParams
from hdr10plus_gen.rpu_parser import RPUMetadata


class TestHDR10PlusGenerator:
    """Test cases for HDR10+ generator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.generator = HDR10PlusGenerator(target_display_luminance=1000)
        self.sample_rpu_metadata = self._create_sample_rpu_metadata()
    
    def _create_sample_rpu_metadata(self) -> RPUMetadata:
        """Create sample RPU metadata for testing"""
        return RPUMetadata(
            profile=7,
            level=1,
            rpu_data=b'sample rpu data',
            scene_cuts=[0, 50, 100],
            shot_cuts=[10, 20, 30, 40, 60, 70, 80, 90],
            frame_metadata=[
                {
                    'frame_number': i,
                    'luminance_min': 10.0 + i,
                    'luminance_max': 500.0 + i * 2,
                    'luminance_avg': 100.0 + i,
                    'tone_mapping_params': {
                        'knee_point_x': 0.3 + (i % 10) * 0.01,
                        'knee_point_y': 0.4 + (i % 10) * 0.01,
                        'bezier_anchors': [
                            {'x': 0.0, 'y': 0.0},
                            {'x': 0.5, 'y': 0.3},
                            {'x': 1.0, 'y': 1.0}
                        ]
                    }
                }
                for i in range(100)
            ],
            mastering_display={
                'primaries': {
                    'red': {'x': 0.680, 'y': 0.320},
                    'green': {'x': 0.265, 'y': 0.690},
                    'blue': {'x': 0.150, 'y': 0.060},
                    'white': {'x': 0.3127, 'y': 0.3290}
                },
                'max_luminance': 4000.0,
                'min_luminance': 0.1
            },
            content_light_level={
                'max_content_light_level': 1000,
                'max_frame_average_light_level': 400
            }
        )
    
    def test_convert_basic(self):
        """Test basic conversion from RPU to HDR10+"""
        hdr10plus_metadata = self.generator.convert(self.sample_rpu_metadata)
        
        # Check required fields
        assert 'version' in hdr10plus_metadata
        assert 'targeted_system_display_maximum_luminance' in hdr10plus_metadata
        assert 'targeted_system_display_actual_peak_luminance_flag' in hdr10plus_metadata
        assert 'num_bezier_curve_anchors' in hdr10plus_metadata
        assert 'knee_point_x' in hdr10plus_metadata
        assert 'knee_point_y' in hdr10plus_metadata
        assert 'bezier_curve_anchors' in hdr10plus_metadata
        assert 'scene_or_frame' in hdr10plus_metadata
    
    def test_convert_low_nit_optimization(self):
        """Test optimization for low-nit content"""
        # Create low-nit RPU metadata
        low_nit_rpu = RPUMetadata(
            profile=7,
            level=1,
            rpu_data=b'low nit data',
            scene_cuts=[],
            shot_cuts=[],
            frame_metadata=[
                {
                    'frame_number': 0,
                    'luminance_min': 5.0,
                    'luminance_max': 200.0,
                    'luminance_avg': 50.0,
                    'tone_mapping_params': {
                        'knee_point_x': 0.2,
                        'knee_point_y': 0.3,
                        'bezier_anchors': []
                    }
                }
            ],
            mastering_display={
                'primaries': {},
                'max_luminance': 1000.0,
                'min_luminance': 0.1
            },
            content_light_level={
                'max_content_light_level': 200,
                'max_frame_average_light_level': 100
            }
        )
        
        hdr10plus_metadata = self.generator.convert(low_nit_rpu)
        
        # Check that low-nit optimization is applied
        assert hdr10plus_metadata['knee_point_x'] < 0.4  # Earlier knee point
        assert hdr10plus_metadata['knee_point_y'] < 0.5  # Lower knee point
        assert hdr10plus_metadata['targeted_system_display_maximum_luminance'] <= 240  # 200 * 1.2
    
    def test_convert_high_nit_content(self):
        """Test handling of high-nit content"""
        high_nit_rpu = RPUMetadata(
            profile=7,
            level=1,
            rpu_data=b'high nit data',
            scene_cuts=[],
            shot_cuts=[],
            frame_metadata=[
                {
                    'frame_number': 0,
                    'luminance_min': 100.0,
                    'luminance_max': 4000.0,
                    'luminance_avg': 2000.0,
                    'tone_mapping_params': {
                        'knee_point_x': 0.5,
                        'knee_point_y': 0.5,
                        'bezier_anchors': []
                    }
                }
            ],
            mastering_display={
                'primaries': {},
                'max_luminance': 4000.0,
                'min_luminance': 0.1
            },
            content_light_level={
                'max_content_light_level': 4000,
                'max_frame_average_light_level': 2000
            }
        )
        
        hdr10plus_metadata = self.generator.convert(high_nit_rpu)
        
        # Check that high-nit content is handled properly
        assert hdr10plus_metadata['targeted_system_display_maximum_luminance'] == 1000
        assert hdr10plus_metadata['knee_point_x'] >= 0.4
        assert hdr10plus_metadata['knee_point_y'] >= 0.4
    
    def test_bezier_curve_generation(self):
        """Test bezier curve anchor generation"""
        hdr10plus_metadata = self.generator.convert(self.sample_rpu_metadata)
        
        bezier_anchors = hdr10plus_metadata['bezier_curve_anchors']
        num_anchors = hdr10plus_metadata['num_bezier_curve_anchors']
        
        assert len(bezier_anchors) == num_anchors
        assert num_anchors > 0
        assert num_anchors <= 15  # HDR10+ limit
        
        # Check that anchors are monotonically increasing in X
        for i in range(1, len(bezier_anchors)):
            assert bezier_anchors[i]['x'] > bezier_anchors[i-1]['x']
            assert 0 <= bezier_anchors[i]['x'] <= 1
            assert 0 <= bezier_anchors[i]['y'] <= 1
    
    def test_scene_metadata_generation(self):
        """Test scene-level metadata generation"""
        hdr10plus_metadata = self.generator.convert(self.sample_rpu_metadata)
        
        scene_data = hdr10plus_metadata['scene_or_frame']
        assert len(scene_data) > 0  # Should have at least one scene
        
        for scene in scene_data:
            assert 'targeted_system_display_maximum_luminance' in scene
            assert 'targeted_system_display_actual_peak_luminance_flag' in scene
            assert 'num_bezier_curve_anchors' in scene
            assert 'knee_point_x' in scene
            assert 'knee_point_y' in scene
            assert 'bezier_curve_anchors' in scene
            assert 'luminance_distribution' in scene
    
    def test_luminance_distribution_calculation(self):
        """Test luminance distribution calculation"""
        hdr10plus_metadata = self.generator.convert(self.sample_rpu_metadata)
        
        scene_data = hdr10plus_metadata['scene_or_frame']
        assert len(scene_data) > 0
        
        for scene in scene_data:
            lum_dist = scene.get('luminance_distribution', {})
            if lum_dist:
                percentiles = ['percentile_10', 'percentile_25', 'percentile_50', 
                             'percentile_75', 'percentile_90', 'percentile_95', 
                             'percentile_99', 'percentile_99_9']
                
                for p in percentiles:
                    if p in lum_dist:
                        assert lum_dist[p] >= 0
                
                # Check monotonicity
                values = [lum_dist[p] for p in percentiles if p in lum_dist]
                for i in range(1, len(values)):
                    assert values[i] >= values[i-1]
    
    def test_save_json(self):
        """Test saving metadata to JSON file"""
        hdr10plus_metadata = self.generator.convert(self.sample_rpu_metadata)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            try:
                self.generator.save_json(hdr10plus_metadata, f.name)
                
                # Verify file was created and contains valid JSON
                with open(f.name, 'r') as f_read:
                    loaded_metadata = json.load(f_read)
                
                assert loaded_metadata == hdr10plus_metadata
            finally:
                os.unlink(f.name)
    
    def test_validate_metadata(self):
        """Test metadata validation"""
        hdr10plus_metadata = self.generator.convert(self.sample_rpu_metadata)
        
        # Should be valid
        assert self.generator.validate_metadata(hdr10plus_metadata) == True
        
        # Test invalid metadata
        invalid_metadata = hdr10plus_metadata.copy()
        del invalid_metadata['version']
        
        assert self.generator.validate_metadata(invalid_metadata) == False
    
    def test_deterministic_output(self):
        """Test that identical inputs produce identical outputs"""
        hdr10plus_metadata1 = self.generator.convert(self.sample_rpu_metadata)
        hdr10plus_metadata2 = self.generator.convert(self.sample_rpu_metadata)
        
        assert hdr10plus_metadata1 == hdr10plus_metadata2
    
    def test_empty_frame_metadata(self):
        """Test handling of empty frame metadata"""
        empty_rpu = RPUMetadata(
            profile=7,
            level=1,
            rpu_data=b'empty data',
            scene_cuts=[],
            shot_cuts=[],
            frame_metadata=[],
            mastering_display={
                'primaries': {},
                'max_luminance': 1000.0,
                'min_luminance': 0.1
            },
            content_light_level={
                'max_content_light_level': 1000,
                'max_frame_average_light_level': 400
            }
        )
        
        hdr10plus_metadata = self.generator.convert(empty_rpu)
        
        # Should still produce valid metadata
        assert 'version' in hdr10plus_metadata
        assert 'scene_or_frame' in hdr10plus_metadata
        assert len(hdr10plus_metadata['scene_or_frame']) == 0
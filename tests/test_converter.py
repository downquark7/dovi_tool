#!/usr/bin/env python3
"""
Test suite for Dolby Vision RPU to HDR10+ converter.
"""

import unittest
import tempfile
import json
from pathlib import Path
import sys

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from dovi_to_hdr10plus import DolbyVisionConverter, RPUParser, HDR10PlusAnalyzer
from dovi_to_hdr10plus.heuristic_converter import HeuristicConverter
from dovi_to_hdr10plus.ml_converter import MLConverter
from dovi_to_hdr10plus.json_generator import HDR10PlusJSONGenerator
from dovi_to_hdr10plus.validator import MetadataValidator


class TestRPUParser(unittest.TestCase):
    """Test cases for RPU parser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = RPUParser()
    
    def test_parser_initialization(self):
        """Test parser initialization."""
        self.assertIsNotNone(self.parser)
        self.assertEqual(self.parser.dovi_tool_path, "dovi_tool")
    
    def test_structure_rpu_data(self):
        """Test RPU data structuring."""
        sample_rpu_info = {
            "version": "1.0",
            "profile": {"level": 5},
            "mastering_display": {
                "red_primary": [0.708, 0.292],
                "green_primary": [0.170, 0.797],
                "blue_primary": [0.131, 0.046],
                "white_point": [0.3127, 0.3290],
                "min_luminance": 0.0001,
                "max_luminance": 1000.0
            },
            "content_light_level": {
                "max_cll": 1000,
                "max_fall": 100.0,
                "average_cll": 50.0
            }
        }
        
        structured_data = self.parser._structure_rpu_data(sample_rpu_info)
        
        self.assertIn("source", structured_data)
        self.assertIn("mastering_display", structured_data)
        self.assertIn("content_light_level", structured_data)
        self.assertEqual(structured_data["source"], "dolby_vision_rpu")
        self.assertEqual(structured_data["content_light_level"]["max_cll"], 1000)


class TestHeuristicConverter(unittest.TestCase):
    """Test cases for heuristic converter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.converter = HeuristicConverter()
    
    def test_converter_initialization(self):
        """Test converter initialization."""
        self.assertIsNotNone(self.converter)
        self.assertIn("luminance_mapping", self.converter.conversion_rules)
        self.assertIn("color_primaries", self.converter.conversion_rules)
    
    def test_convert_max_cll(self):
        """Test MaxCLL conversion."""
        rpu_data = {
            "content_light_level": {
                "max_cll": 2000,
                "max_fall": 200.0
            }
        }
        
        max_cll = self.converter._convert_max_cll(rpu_data)
        self.assertIsInstance(max_cll, int)
        self.assertGreater(max_cll, 0)
        self.assertLessEqual(max_cll, 2000)  # Should be conservative
    
    def test_convert_max_fall(self):
        """Test MaxFALL conversion."""
        rpu_data = {
            "content_light_level": {
                "max_cll": 2000,
                "max_fall": 200.0
            }
        }
        
        max_fall = self.converter._convert_max_fall(rpu_data)
        self.assertIsInstance(max_fall, float)
        self.assertGreater(max_fall, 0)
        self.assertLessEqual(max_fall, 200.0)  # Should be conservative
    
    def test_convert_mastering_display(self):
        """Test mastering display conversion."""
        rpu_data = {
            "mastering_display": {
                "primaries": {
                    "red": [0.708, 0.292],
                    "green": [0.170, 0.797],
                    "blue": [0.131, 0.046],
                    "white": [0.3127, 0.3290]
                },
                "luminance": {
                    "min": 0.0001,
                    "max": 1000.0
                }
            }
        }
        
        mastering_display = self.converter._convert_mastering_display(rpu_data)
        
        self.assertIn("Primaries", mastering_display)
        self.assertIn("Luminance", mastering_display)
        self.assertIn("Red", mastering_display["Primaries"])
        self.assertIn("Min", mastering_display["Luminance"])
    
    def test_full_conversion(self):
        """Test full conversion process."""
        rpu_data = {
            "content_light_level": {
                "max_cll": 1500,
                "max_fall": 150.0,
                "average_cll": 75.0
            },
            "mastering_display": {
                "primaries": {
                    "red": [0.708, 0.292],
                    "green": [0.170, 0.797],
                    "blue": [0.131, 0.046],
                    "white": [0.3127, 0.3290]
                },
                "luminance": {
                    "min": 0.0001,
                    "max": 2000.0
                }
            },
            "scene_info": {
                "scene_refresh_flag": False,
                "frame_count": 1000
            }
        }
        
        hdr10plus_metadata = self.converter.convert(rpu_data)
        
        self.assertIn("MaxCLL", hdr10plus_metadata)
        self.assertIn("MaxFALL", hdr10plus_metadata)
        self.assertIn("MasteringDisplay", hdr10plus_metadata)
        self.assertEqual(hdr10plus_metadata["conversion_method"], "heuristic")


class TestMLConverter(unittest.TestCase):
    """Test cases for ML converter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.converter = MLConverter()
    
    def test_converter_initialization(self):
        """Test converter initialization."""
        self.assertIsNotNone(self.converter)
        self.assertIn("max_cll", self.converter.models)
        self.assertIn("max_fall", self.converter.models)
    
    def test_feature_extraction(self):
        """Test feature extraction from RPU data."""
        rpu_data = {
            "content_light_level": {
                "max_cll": 1000,
                "max_fall": 100.0,
                "average_cll": 50.0
            },
            "mastering_display": {
                "primaries": {
                    "red": [0.708, 0.292],
                    "green": [0.170, 0.797],
                    "blue": [0.131, 0.046],
                    "white": [0.3127, 0.3290]
                },
                "luminance": {
                    "min": 0.0001,
                    "max": 1000.0
                }
            },
            "tone_mapping": {
                "trim_slopes": [1.0, 1.0, 1.0],
                "trim_offsets": [0.0, 0.0, 0.0],
                "trim_power": [1.0, 1.0, 1.0]
            },
            "scene_info": {
                "scene_refresh_flag": False,
                "frame_count": 1000
            }
        }
        
        features = self.converter._extract_features(rpu_data)
        
        self.assertEqual(features.shape, (1, len(self.converter.feature_names)))
        self.assertEqual(features[0, 0], 1000)  # max_cll
        self.assertEqual(features[0, 1], 100.0)  # max_fall
    
    def test_synthetic_data_generation(self):
        """Test synthetic training data generation."""
        training_data = self.converter.generate_synthetic_training_data(num_samples=10)
        
        self.assertEqual(len(training_data), 10)
        for example in training_data:
            self.assertIn("rpu_data", example)
            self.assertIn("hdr10plus_data", example)
            self.assertIn("MaxCLL", example["hdr10plus_data"])


class TestHDR10PlusAnalyzer(unittest.TestCase):
    """Test cases for HDR10+ analyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = HDR10PlusAnalyzer()
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        self.assertIsNotNone(self.analyzer)
        self.assertIn("required_fields", self.analyzer.hdr10plus_schema)
    
    def test_analyze_metadata(self):
        """Test metadata analysis."""
        metadata = {
            "MaxCLL": 1000,
            "MaxFALL": 100.0,
            "MasteringDisplay": {
                "Primaries": {
                    "Red": [0.708, 0.292],
                    "Green": [0.170, 0.797],
                    "Blue": [0.131, 0.046],
                    "White": [0.3127, 0.3290]
                },
                "Luminance": {
                    "Min": 0.0001,
                    "Max": 1000.0
                }
            }
        }
        
        analysis = self.analyzer.analyze_metadata(metadata)
        
        self.assertIn("valid", analysis)
        self.assertIn("warnings", analysis)
        self.assertIn("errors", analysis)
        self.assertIn("statistics", analysis)
        self.assertTrue(analysis["valid"])
    
    def test_compare_with_standard(self):
        """Test comparison with standard color spaces."""
        metadata = {
            "MasteringDisplay": {
                "Primaries": {
                    "Red": [0.708, 0.292],
                    "Green": [0.170, 0.797],
                    "Blue": [0.131, 0.046],
                    "White": [0.3127, 0.3290]
                }
            }
        }
        
        comparison = self.analyzer.compare_with_standard(metadata, "bt2020")
        
        self.assertIn("standard", comparison)
        self.assertIn("similarity", comparison)
        self.assertEqual(comparison["standard"], "bt2020")
        self.assertGreater(comparison["similarity"], 0.9)  # Should be very similar to BT.2020


class TestHDR10PlusJSONGenerator(unittest.TestCase):
    """Test cases for HDR10+ JSON generator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = HDR10PlusJSONGenerator()
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        self.assertIsNotNone(self.generator)
        self.assertIn("required_fields", self.generator.hdr10plus_schema)
    
    def test_generate_example_json(self):
        """Test example JSON generation."""
        example_json = self.generator.generate_example_json()
        
        self.assertIn("MaxCLL", example_json)
        self.assertIn("MaxFALL", example_json)
        self.assertIn("MasteringDisplay", example_json)
        self.assertIsInstance(example_json["MaxCLL"], int)
        self.assertIsInstance(example_json["MaxFALL"], float)
    
    def test_generate_json(self):
        """Test JSON generation from HDR10+ data."""
        hdr10plus_data = {
            "MaxCLL": 1500,
            "MaxFALL": 150.0,
            "MasteringDisplay": {
                "Primaries": {
                    "Red": [0.708, 0.292],
                    "Green": [0.170, 0.797],
                    "Blue": [0.131, 0.046],
                    "White": [0.3127, 0.3290]
                },
                "Luminance": {
                    "Min": 0.0001,
                    "Max": 2000.0
                }
            }
        }
        
        json_metadata = self.generator.generate_json(hdr10plus_data)
        
        self.assertEqual(json_metadata["MaxCLL"], 1500)
        self.assertEqual(json_metadata["MaxFALL"], 150.0)
        self.assertIn("MasteringDisplay", json_metadata)


class TestMetadataValidator(unittest.TestCase):
    """Test cases for metadata validator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = MetadataValidator()
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        self.assertIsNotNone(self.validator)
        self.assertIn("required_fields", self.validator.validation_rules)
    
    def test_validate_hdr10plus(self):
        """Test HDR10+ metadata validation."""
        metadata = {
            "MaxCLL": 1000,
            "MaxFALL": 100.0,
            "MasteringDisplay": {
                "Primaries": {
                    "Red": [0.708, 0.292],
                    "Green": [0.170, 0.797],
                    "Blue": [0.131, 0.046],
                    "White": [0.3127, 0.3290]
                },
                "Luminance": {
                    "Min": 0.0001,
                    "Max": 1000.0
                }
            }
        }
        
        validation_result = self.validator.validate_hdr10plus(metadata)
        
        self.assertIn("valid", validation_result)
        self.assertIn("warnings", validation_result)
        self.assertIn("errors", validation_result)
        self.assertIn("compliance_score", validation_result)
        self.assertTrue(validation_result["valid"])
    
    def test_validate_invalid_metadata(self):
        """Test validation of invalid metadata."""
        invalid_metadata = {
            "MaxCLL": -100,  # Invalid negative value
            "MaxFALL": 100.0,
            # Missing MasteringDisplay
        }
        
        validation_result = self.validator.validate_hdr10plus(invalid_metadata)
        
        self.assertFalse(validation_result["valid"])
        self.assertGreater(len(validation_result["errors"]), 0)
    
    def test_compare_with_standard(self):
        """Test comparison with standard color spaces."""
        metadata = {
            "MasteringDisplay": {
                "Primaries": {
                    "Red": [0.708, 0.292],
                    "Green": [0.170, 0.797],
                    "Blue": [0.131, 0.046],
                    "White": [0.3127, 0.3290]
                }
            }
        }
        
        comparison = self.validator.compare_with_standard(metadata, "bt2020")
        
        self.assertIn("standard", comparison)
        self.assertIn("similarity", comparison)
        self.assertIn("match_quality", comparison)
        self.assertEqual(comparison["standard"], "bt2020")


class TestDolbyVisionConverter(unittest.TestCase):
    """Test cases for main converter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.converter = DolbyVisionConverter(use_ml=False)
    
    def test_converter_initialization(self):
        """Test converter initialization."""
        self.assertIsNotNone(self.converter)
        self.assertFalse(self.converter.use_ml)
        self.assertIsNone(self.converter.ml_converter)
    
    def test_ml_converter_initialization(self):
        """Test ML converter initialization."""
        ml_converter = DolbyVisionConverter(use_ml=True)
        self.assertTrue(ml_converter.use_ml)
        self.assertIsNotNone(ml_converter.ml_converter)


if __name__ == "__main__":
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestRPUParser,
        TestHeuristicConverter,
        TestMLConverter,
        TestHDR10PlusAnalyzer,
        TestHDR10PlusJSONGenerator,
        TestMetadataValidator,
        TestDolbyVisionConverter
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
#!/usr/bin/env python3
"""
Test script for the Dolby Vision RPU to HDR10+ converter
"""

import os
import json
import tempfile
import logging
from dolby_to_hdr10plus import (
    convert_dolby_vision_rpu_to_hdr10plus,
    convert_rpu_file_to_hdr10plus_json,
    DolbyVisionRPUParser,
    HDR10PlusJSONGenerator,
    HDR10PlusMetadata,
    MasteringDisplay,
    ColorPrimaries,
    SceneInfo,
    ToneMapping,
    ColorSaturation
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_rpu_data() -> bytes:
    """Create test RPU data for validation"""
    # This creates a minimal valid RPU structure for testing
    test_data = bytearray()
    
    # RPU header
    test_data.extend([0x01, 0x00])  # RPU type 1, version 0
    test_data.extend([0x00, 0x50])  # RPU size (80 bytes)
    test_data.extend([0x00, 0x00, 0x00, 0x00])  # Reserved
    test_data.extend([0x05, 0x00])  # Profile 5, level 0
    test_data.extend([0x00, 0x00])  # Reserved
    test_data.extend([0x0A])  # 10-bit depth
    test_data.extend([0x01])  # Color space
    test_data.extend([0x09])  # DCI-P3 primaries
    test_data.extend([0x16])  # PQ transfer
    test_data.extend([0x01])  # Identity matrix
    
    # Mastering display metadata (simplified)
    test_data.extend([0x00, 0x00, 0x00, 0x01])  # Min luminance (0.0001)
    test_data.extend([0x44, 0x7A, 0x00, 0x00])  # Max luminance (1000.0)
    
    # Color primaries (DCI-P3)
    test_data.extend([0x3F, 0x2E, 0x14, 0x7B])  # Red X (0.680)
    test_data.extend([0x3E, 0xA3, 0xD7, 0x0A])  # Red Y (0.320)
    test_data.extend([0x3E, 0x87, 0xAE, 0x14])  # Green X (0.265)
    test_data.extend([0x3F, 0x30, 0xA3, 0xD7])  # Green Y (0.690)
    test_data.extend([0x3E, 0x19, 0x99, 0x9A])  # Blue X (0.150)
    test_data.extend([0x3D, 0x75, 0xC2, 0x8F])  # Blue Y (0.060)
    test_data.extend([0x3E, 0xA0, 0x00, 0x00])  # White X (0.3127)
    test_data.extend([0x3E, 0xA8, 0x72, 0xB0])  # White Y (0.3290)
    
    # Content light levels
    test_data.extend([0x00, 0x00, 0x03, 0xE8])  # Max CLL (1000)
    test_data.extend([0x00, 0x00, 0x01, 0x90])  # Max FALL (400)
    
    # Pad to specified size
    while len(test_data) < 80:
        test_data.extend([0x00])
    
    return bytes(test_data)


def test_basic_conversion():
    """Test basic RPU to HDR10+ conversion"""
    print("Testing basic conversion...")
    
    try:
        # Create test RPU data
        rpu_data = create_test_rpu_data()
        print(f"✓ Created test RPU data: {len(rpu_data)} bytes")
        
        # Convert to HDR10+ JSON
        hdr10plus_json = convert_dolby_vision_rpu_to_hdr10plus(
            rpu_data,
            title="Test Dolby Vision Content",
            alternate_version="Test Version 1.0"
        )
        
        print("✓ Conversion successful")
        
        # Parse and validate JSON
        json_data = json.loads(hdr10plus_json)
        print("✓ JSON parsing successful")
        
        # Check required fields
        required_fields = ["Tool", "ToolVersion", "HDR10Plus"]
        for field in required_fields:
            if field not in json_data:
                raise ValueError(f"Missing required field: {field}")
        print("✓ Required fields present")
        
        # Check HDR10+ structure
        hdr10plus = json_data["HDR10Plus"]
        required_hdr_fields = ["MasteringDisplay", "MaxCLL", "MaxFALL", "SceneInfo"]
        for field in required_hdr_fields:
            if field not in hdr10plus:
                raise ValueError(f"Missing required HDR10+ field: {field}")
        print("✓ HDR10+ structure valid")
        
        print("✓ Basic conversion test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Basic conversion test failed: {e}")
        return False


def test_file_conversion():
    """Test file-based conversion"""
    print("\nTesting file conversion...")
    
    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.rpu', delete=False) as rpu_file:
            rpu_path = rpu_file.name
            rpu_file.write(create_test_rpu_data())
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as json_file:
            json_path = json_file.name
        
        print(f"✓ Created temporary files: {rpu_path}, {json_path}")
        
        # Convert file
        convert_rpu_file_to_hdr10plus_json(
            rpu_path,
            json_path,
            title="Test File Content",
            alternate_version="File Test Version"
        )
        
        print("✓ File conversion successful")
        
        # Verify output file
        with open(json_path, 'r') as f:
            content = f.read()
        
        json_data = json.loads(content)
        if json_data["Title"] != "Test File Content":
            raise ValueError("Title not preserved in file conversion")
        
        print("✓ File conversion test passed!")
        return True
        
    except Exception as e:
        print(f"✗ File conversion test failed: {e}")
        return False
    
    finally:
        # Clean up
        for path in [rpu_path, json_path]:
            if os.path.exists(path):
                os.remove(path)
                print(f"✓ Cleaned up: {path}")


def test_validation():
    """Test HDR10+ JSON validation"""
    print("\nTesting validation...")
    
    try:
        # Create valid metadata
        primaries = ColorPrimaries(
            red=(0.680, 0.320),
            green=(0.265, 0.690),
            blue=(0.150, 0.060),
            white=(0.3127, 0.3290)
        )
        
        mastering_display = MasteringDisplay(
            min_luminance=0.0001,
            max_luminance=1000.0,
            primaries=primaries
        )
        
        metadata = HDR10PlusMetadata(
            tool="Test Tool",
            tool_version="1.0.0",
            title="Test Content",
            mastering_display=mastering_display,
            max_cll=1000,
            max_fall=400
        )
        
        # Generate JSON
        generator = HDR10PlusJSONGenerator()
        hdr10plus_json = generator.convert_to_hdr10plus_json(metadata)
        
        # Validate (hdr10plus_json is already a dict, not a string)
        if not generator.validate_hdr10plus_json(hdr10plus_json):
            raise ValueError("Validation failed for valid metadata")
        
        print("✓ Valid metadata validation passed")
        
        # Test invalid metadata
        invalid_json = {"invalid": "structure"}
        if generator.validate_hdr10plus_json(invalid_json):
            raise ValueError("Validation should have failed for invalid metadata")
        
        print("✓ Invalid metadata correctly rejected")
        print("✓ Validation test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Validation test failed: {e}")
        return False


def test_custom_metadata():
    """Test custom metadata creation"""
    print("\nTesting custom metadata...")
    
    try:
        # Create custom metadata
        primaries = ColorPrimaries(
            red=(0.708, 0.292),    # BT.2020
            green=(0.170, 0.797),
            blue=(0.131, 0.046),
            white=(0.3127, 0.3290)
        )
        
        mastering_display = MasteringDisplay(
            min_luminance=0.0001,
            max_luminance=4000.0,
            primaries=primaries
        )
        
        scenes = [
            SceneInfo(
                scene_frame_index=0,
                max_cll=2000,
                max_fall=800,
                tone_mapping=ToneMapping(knee_point=0.8, knee_slope=0.6),
                color_saturation=ColorSaturation(saturation_gain=1.1)
            )
        ]
        
        metadata = HDR10PlusMetadata(
            tool="Custom Test Tool",
            tool_version="2.0.0",
            title="Custom Test Content",
            alternate_version="Custom Version",
            mastering_display=mastering_display,
            max_cll=2000,
            max_fall=800,
            scenes=scenes
        )
        
        # Generate and validate
        generator = HDR10PlusJSONGenerator()
        hdr10plus_json = generator.convert_to_hdr10plus_json(metadata)
        
        if not generator.validate_hdr10plus_json(hdr10plus_json):
            raise ValueError("Custom metadata validation failed")
        
        # Check custom values
        if hdr10plus_json["Tool"] != "Custom Test Tool":
            raise ValueError("Custom tool name not preserved")
        
        if hdr10plus_json["HDR10Plus"]["MaxCLL"] != 2000:
            raise ValueError("Custom MaxCLL not preserved")
        
        print("✓ Custom metadata test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Custom metadata test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("Running Dolby Vision RPU to HDR10+ Converter Tests")
    print("=" * 60)
    
    tests = [
        test_basic_conversion,
        test_file_conversion,
        test_validation,
        test_custom_metadata
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
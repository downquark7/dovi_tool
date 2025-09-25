#!/usr/bin/env python3
"""
Example usage of the Dolby Vision RPU to HDR10+ converter

This script demonstrates how to use the converter with various scenarios.
"""

import os
import json
import logging
from dolby_to_hdr10plus import (
    convert_dolby_vision_rpu_to_hdr10plus,
    convert_rpu_file_to_hdr10plus_json,
    DolbyVisionRPUParser,
    HDR10PlusJSONGenerator
)
from advanced_rpu_parser import analyze_rpu_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_rpu_data() -> bytes:
    """Create sample RPU data for testing purposes"""
    # This is a simplified sample - real RPU data would be more complex
    sample_data = bytearray()
    
    # RPU header (simplified)
    sample_data.extend([0x01, 0x00])  # RPU type and version
    sample_data.extend([0x00, 0x40])  # RPU size (64 bytes)
    sample_data.extend([0x00, 0x00, 0x00, 0x00])  # Reserved
    sample_data.extend([0x05, 0x00])  # Profile and level
    sample_data.extend([0x00, 0x00])  # Reserved
    sample_data.extend([0x0A])  # Bit depth (10-bit)
    sample_data.extend([0x01])  # Color space
    sample_data.extend([0x09])  # Color primaries (DCI-P3)
    sample_data.extend([0x16])  # Transfer characteristics (PQ)
    sample_data.extend([0x01])  # Matrix coefficients
    
    # Add some dummy data to reach the specified size
    while len(sample_data) < 64:
        sample_data.extend([0x00])
    
    return bytes(sample_data)


def example_basic_conversion():
    """Example of basic RPU to HDR10+ conversion"""
    print("=== Basic Conversion Example ===")
    
    # Create sample RPU data
    rpu_data = create_sample_rpu_data()
    print(f"Created sample RPU data: {len(rpu_data)} bytes")
    
    # Convert to HDR10+ JSON
    try:
        hdr10plus_json = convert_dolby_vision_rpu_to_hdr10plus(
            rpu_data,
            title="Sample Dolby Vision Content",
            alternate_version="Test Version 1.0"
        )
        
        print("Conversion successful!")
        print("HDR10+ JSON output:")
        print("-" * 40)
        print(hdr10plus_json)
        
    except Exception as e:
        print(f"Conversion failed: {e}")


def example_file_conversion():
    """Example of file-based conversion"""
    print("\n=== File Conversion Example ===")
    
    # Create sample RPU file
    rpu_file = "sample.rpu"
    output_file = "output_hdr10plus.json"
    
    try:
        # Create sample RPU file
        rpu_data = create_sample_rpu_data()
        with open(rpu_file, 'wb') as f:
            f.write(rpu_data)
        print(f"Created sample RPU file: {rpu_file}")
        
        # Convert file
        convert_rpu_file_to_hdr10plus_json(
            rpu_file,
            output_file,
            title="Sample Dolby Vision Movie",
            alternate_version="Theatrical Release"
        )
        
        print(f"Conversion successful! Output saved to: {output_file}")
        
        # Display the output
        with open(output_file, 'r') as f:
            content = f.read()
        print("\nGenerated HDR10+ JSON:")
        print("-" * 40)
        print(content)
        
    except Exception as e:
        print(f"File conversion failed: {e}")
    
    finally:
        # Clean up
        for file in [rpu_file, output_file]:
            if os.path.exists(file):
                os.remove(file)
                print(f"Cleaned up: {file}")


def example_advanced_parsing():
    """Example of advanced RPU parsing"""
    print("\n=== Advanced Parsing Example ===")
    
    # Create sample RPU file
    rpu_file = "sample_advanced.rpu"
    
    try:
        # Create sample RPU file
        rpu_data = create_sample_rpu_data()
        with open(rpu_file, 'wb') as f:
            f.write(rpu_data)
        print(f"Created sample RPU file: {rpu_file}")
        
        # Analyze the RPU file
        analysis = analyze_rpu_file(rpu_file)
        
        print("RPU Analysis Results:")
        print("-" * 40)
        print(json.dumps(analysis, indent=2))
        
    except Exception as e:
        print(f"Advanced parsing failed: {e}")
    
    finally:
        # Clean up
        if os.path.exists(rpu_file):
            os.remove(rpu_file)
            print(f"Cleaned up: {rpu_file}")


def example_custom_metadata():
    """Example of creating custom HDR10+ metadata"""
    print("\n=== Custom Metadata Example ===")
    
    try:
        # Create custom metadata
        from dolby_to_hdr10plus import HDR10PlusMetadata, MasteringDisplay, ColorPrimaries, SceneInfo, ToneMapping, ColorSaturation
        
        # Custom mastering display
        primaries = ColorPrimaries(
            red=(0.708, 0.292),    # BT.2020 red
            green=(0.170, 0.797),  # BT.2020 green
            blue=(0.131, 0.046),   # BT.2020 blue
            white=(0.3127, 0.3290) # D65 white point
        )
        
        mastering_display = MasteringDisplay(
            min_luminance=0.0001,
            max_luminance=4000.0,  # High brightness mastering display
            primaries=primaries
        )
        
        # Custom scenes
        scenes = [
            SceneInfo(
                scene_frame_index=0,
                max_cll=2000,
                max_fall=800,
                tone_mapping=ToneMapping(knee_point=0.8, knee_slope=0.6),
                color_saturation=ColorSaturation(saturation_gain=1.1)
            ),
            SceneInfo(
                scene_frame_index=100,
                max_cll=1500,
                max_fall=600,
                tone_mapping=ToneMapping(knee_point=0.7, knee_slope=0.5),
                color_saturation=ColorSaturation(saturation_gain=0.9)
            )
        ]
        
        # Create metadata
        metadata = HDR10PlusMetadata(
            tool="Custom HDR10+ Generator",
            tool_version="2.0.0",
            title="Custom HDR Content",
            alternate_version="Director's Cut",
            mastering_display=mastering_display,
            max_cll=2000,
            max_fall=800,
            scenes=scenes
        )
        
        # Generate JSON
        generator = HDR10PlusJSONGenerator()
        hdr10plus_json = generator.convert_to_hdr10plus_json(metadata)
        
        # Validate
        if generator.validate_hdr10plus_json(hdr10plus_json):
            print("Custom metadata validation passed!")
            print("Generated HDR10+ JSON:")
            print("-" * 40)
            print(json.dumps(hdr10plus_json, indent=2))
        else:
            print("Custom metadata validation failed!")
        
    except Exception as e:
        print(f"Custom metadata creation failed: {e}")


def example_batch_conversion():
    """Example of batch conversion of multiple RPU files"""
    print("\n=== Batch Conversion Example ===")
    
    # Create multiple sample RPU files
    rpu_files = []
    output_files = []
    
    try:
        for i in range(3):
            rpu_file = f"sample_{i+1}.rpu"
            output_file = f"output_{i+1}.json"
            
            # Create sample RPU data
            rpu_data = create_sample_rpu_data()
            with open(rpu_file, 'wb') as f:
                f.write(rpu_data)
            
            rpu_files.append(rpu_file)
            output_files.append(output_file)
        
        print(f"Created {len(rpu_files)} sample RPU files")
        
        # Convert all files
        for i, (rpu_file, output_file) in enumerate(zip(rpu_files, output_files)):
            try:
                convert_rpu_file_to_hdr10plus_json(
                    rpu_file,
                    output_file,
                    title=f"Sample Content {i+1}",
                    alternate_version=f"Version {i+1}.0"
                )
                print(f"✓ Converted {rpu_file} -> {output_file}")
            except Exception as e:
                print(f"✗ Failed to convert {rpu_file}: {e}")
        
        print("Batch conversion completed!")
        
    except Exception as e:
        print(f"Batch conversion failed: {e}")
    
    finally:
        # Clean up
        for file in rpu_files + output_files:
            if os.path.exists(file):
                os.remove(file)
        print("Cleaned up all temporary files")


def main():
    """Run all examples"""
    print("Dolby Vision RPU to HDR10+ Converter Examples")
    print("=" * 50)
    
    # Run examples
    example_basic_conversion()
    example_file_conversion()
    example_advanced_parsing()
    example_custom_metadata()
    example_batch_conversion()
    
    print("\nAll examples completed!")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Basic conversion example for HDR10+ Generator

This example shows how to convert a Dolby Vision RPU file to HDR10+ JSON metadata.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from hdr10plus_gen import HDR10PlusGenerator, RPUParser, HDR10PlusValidator


def main():
    """Main function demonstrating basic conversion"""
    
    # Example RPU file path (replace with actual file)
    rpu_file = "sample.rpu"
    
    if not os.path.exists(rpu_file):
        print(f"Error: RPU file '{rpu_file}' not found")
        print("Please provide a valid Dolby Vision RPU file")
        return 1
    
    try:
        # Parse RPU file
        print("Parsing RPU file...")
        parser = RPUParser()
        rpu_metadata = parser.parse(rpu_file)
        
        print(f"Parsed RPU: Profile {rpu_metadata.profile}, Level {rpu_metadata.level}")
        print(f"Found {len(rpu_metadata.frame_metadata)} frames")
        
        # Generate HDR10+ metadata
        print("Generating HDR10+ metadata...")
        generator = HDR10PlusGenerator(target_display_luminance=1000)
        hdr10plus_metadata = generator.convert(rpu_metadata)
        
        # Validate metadata
        print("Validating metadata...")
        validator = HDR10PlusValidator()
        is_valid, errors = validator.validate_metadata(hdr10plus_metadata)
        
        if not is_valid:
            print("Validation failed:")
            for error in errors:
                print(f"  - {error}")
            return 1
        
        print("Validation passed!")
        
        # Save to JSON file
        output_file = "output_hdr10plus.json"
        generator.save_json(hdr10plus_metadata, output_file)
        print(f"HDR10+ metadata saved to {output_file}")
        
        # Display summary
        print("\nConversion Summary:")
        print(f"  Version: {hdr10plus_metadata['version']}")
        print(f"  Target Display Max Luminance: {hdr10plus_metadata['targeted_system_display_maximum_luminance']} nits")
        print(f"  Max Content Light Level: {hdr10plus_metadata['max_content_light_level']} nits")
        print(f"  Max Frame Average Light Level: {hdr10plus_metadata['max_frame_average_light_level']} nits")
        print(f"  Number of Scenes: {len(hdr10plus_metadata.get('scene_or_frame', []))}")
        print(f"  Bezier Curve Anchors: {len(hdr10plus_metadata.get('bezier_curve_anchors', []))}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
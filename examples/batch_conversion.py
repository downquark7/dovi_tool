#!/usr/bin/env python3
"""
Batch conversion example for HDR10+ Generator

This example shows how to convert multiple Dolby Vision RPU files to HDR10+ JSON metadata.
"""

import sys
import os
import glob
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from hdr10plus_gen import HDR10PlusGenerator, RPUParser, HDR10PlusValidator


def convert_rpu_file(rpu_file: str, output_dir: str, target_luminance: int = 1000) -> bool:
    """Convert a single RPU file to HDR10+ JSON"""
    
    try:
        # Parse RPU file
        parser = RPUParser()
        rpu_metadata = parser.parse(rpu_file)
        
        # Generate HDR10+ metadata
        generator = HDR10PlusGenerator(target_display_luminance=target_luminance)
        hdr10plus_metadata = generator.convert(rpu_metadata)
        
        # Validate metadata
        validator = HDR10PlusValidator()
        is_valid, errors = validator.validate_metadata(hdr10plus_metadata)
        
        if not is_valid:
            print(f"  Validation failed: {', '.join(errors)}")
            return False
        
        # Generate output filename
        rpu_path = Path(rpu_file)
        output_file = Path(output_dir) / f"{rpu_path.stem}.json"
        
        # Save to JSON file
        generator.save_json(hdr10plus_metadata, str(output_file))
        
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    """Main function demonstrating batch conversion"""
    
    # Configuration
    input_pattern = "*.rpu"  # Pattern to match RPU files
    output_dir = "output"
    target_luminance = 1000  # Target display luminance in nits
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Find RPU files
    rpu_files = glob.glob(input_pattern)
    
    if not rpu_files:
        print(f"No RPU files found matching pattern '{input_pattern}'")
        print("Please ensure RPU files are in the current directory")
        return 1
    
    print(f"Found {len(rpu_files)} RPU files to convert")
    print(f"Output directory: {output_dir}")
    print(f"Target luminance: {target_luminance} nits")
    print()
    
    # Convert files
    success_count = 0
    error_count = 0
    
    for i, rpu_file in enumerate(rpu_files, 1):
        print(f"[{i}/{len(rpu_files)}] Converting {rpu_file}...")
        
        if convert_rpu_file(rpu_file, output_dir, target_luminance):
            print(f"  ✓ Success")
            success_count += 1
        else:
            print(f"  ✗ Failed")
            error_count += 1
        
        print()
    
    # Summary
    print("Batch Conversion Summary:")
    print(f"  Total files: {len(rpu_files)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {error_count}")
    print(f"  Success rate: {success_count/len(rpu_files)*100:.1f}%")
    
    if error_count > 0:
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
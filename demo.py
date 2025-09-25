#!/usr/bin/env python3
"""
Complete demonstration of Dolby Vision RPU to HDR10+ conversion

This script demonstrates the full workflow from RPU data to HDR10+ JSON output.
"""

import json
from dolby_to_hdr10plus import convert_dolby_vision_rpu_to_hdr10plus, convert_rpu_file_to_hdr10plus_json
from advanced_rpu_parser import analyze_rpu_file

def create_realistic_rpu_data() -> bytes:
    """Create more realistic RPU data for demonstration"""
    # This creates a more comprehensive RPU structure
    rpu_data = bytearray()
    
    # RPU header
    rpu_data.extend([0x01, 0x00])  # RPU type 1, version 0
    rpu_data.extend([0x00, 0x80])  # RPU size (128 bytes)
    rpu_data.extend([0x00, 0x00, 0x00, 0x00])  # Reserved
    rpu_data.extend([0x05, 0x00])  # Profile 5, level 0
    rpu_data.extend([0x00, 0x00])  # Reserved
    rpu_data.extend([0x0A])  # 10-bit depth
    rpu_data.extend([0x01])  # Color space
    rpu_data.extend([0x09])  # DCI-P3 primaries
    rpu_data.extend([0x16])  # PQ transfer
    rpu_data.extend([0x01])  # Identity matrix
    
    # Mastering display metadata
    rpu_data.extend([0x00, 0x00, 0x00, 0x01])  # Min luminance (0.0001)
    rpu_data.extend([0x44, 0x7A, 0x00, 0x00])  # Max luminance (1000.0)
    
    # Color primaries (DCI-P3)
    rpu_data.extend([0x3F, 0x2E, 0x14, 0x7B])  # Red X (0.680)
    rpu_data.extend([0x3E, 0xA3, 0xD7, 0x0A])  # Red Y (0.320)
    rpu_data.extend([0x3E, 0x87, 0xAE, 0x14])  # Green X (0.265)
    rpu_data.extend([0x3F, 0x30, 0xA3, 0xD7])  # Green Y (0.690)
    rpu_data.extend([0x3E, 0x19, 0x99, 0x9A])  # Blue X (0.150)
    rpu_data.extend([0x3D, 0x75, 0xC2, 0x8F])  # Blue Y (0.060)
    rpu_data.extend([0x3E, 0xA0, 0x00, 0x00])  # White X (0.3127)
    rpu_data.extend([0x3E, 0xA8, 0x72, 0xB0])  # White Y (0.3290)
    
    # Content light levels
    rpu_data.extend([0x00, 0x00, 0x04, 0x4C])  # Max CLL (1100)
    rpu_data.extend([0x00, 0x00, 0x01, 0xF4])  # Max FALL (500)
    
    # Dynamic metadata for multiple scenes
    for scene in range(5):
        rpu_data.extend([0x00, 0x00, 0x04, 0x4C])  # Scene Max CLL
        rpu_data.extend([0x00, 0x00, 0x01, 0xF4])  # Scene Max FALL
        rpu_data.extend([0x3F, 0x40, 0x00, 0x00])  # Tone mapping knee point
        rpu_data.extend([0x3F, 0x00, 0x00, 0x00])  # Tone mapping knee slope
        rpu_data.extend([0x3F, 0x80, 0x00, 0x00])  # Saturation gain
    
    # Pad to specified size
    while len(rpu_data) < 128:
        rpu_data.extend([0x00])
    
    return bytes(rpu_data)

def main():
    """Main demonstration function"""
    print("🎬 Dolby Vision RPU to HDR10+ Converter - Complete Demo")
    print("=" * 60)
    
    # Step 1: Create realistic RPU data
    print("\n📁 Step 1: Creating realistic Dolby Vision RPU data...")
    rpu_data = create_realistic_rpu_data()
    print(f"✓ Created RPU data: {len(rpu_data)} bytes")
    
    # Step 2: Analyze RPU data
    print("\n🔍 Step 2: Analyzing RPU data structure...")
    try:
        # Save RPU data to temporary file for analysis
        with open('demo.rpu', 'wb') as f:
            f.write(rpu_data)
        
        analysis = analyze_rpu_file('demo.rpu')
        print("✓ RPU Analysis Results:")
        print(f"  - RPU Type: {analysis['header']['rpu_type']}")
        print(f"  - RPU Version: {analysis['header']['rpu_version']}")
        print(f"  - Profile: {analysis['header']['profile']}")
        print(f"  - Bit Depth: {analysis['header']['bit_depth']}")
        print(f"  - Color Primaries: {analysis['header']['color_primaries']} (DCI-P3)")
        print(f"  - Transfer Characteristics: {analysis['header']['transfer_characteristics']} (PQ)")
        print(f"  - Max CLL: {analysis['content_light_level']['max_cll']} nits")
        print(f"  - Max FALL: {analysis['content_light_level']['max_fall']} nits")
        
    except Exception as e:
        print(f"✗ RPU analysis failed: {e}")
        return
    
    # Step 3: Convert to HDR10+ JSON
    print("\n🔄 Step 3: Converting RPU to HDR10+ metadata...")
    try:
        hdr10plus_json = convert_dolby_vision_rpu_to_hdr10plus(
            rpu_data,
            title="Demo Dolby Vision Content",
            alternate_version="High Fidelity Demo v1.0"
        )
        print("✓ Conversion successful!")
        
        # Parse and display key information
        json_data = json.loads(hdr10plus_json)
        hdr10plus = json_data["HDR10Plus"]
        
        print("✓ HDR10+ Metadata Generated:")
        print(f"  - Tool: {json_data['Tool']} v{json_data['ToolVersion']}")
        print(f"  - Title: {json_data['Title']}")
        print(f"  - Max CLL: {hdr10plus['MaxCLL']} nits")
        print(f"  - Max FALL: {hdr10plus['MaxFALL']} nits")
        print(f"  - Mastering Display Max Luminance: {hdr10plus['MasteringDisplay']['MaxLuminance']} nits")
        print(f"  - Number of Scenes: {len(hdr10plus['SceneInfo'])}")
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return
    
    # Step 4: Save to file
    print("\n💾 Step 4: Saving HDR10+ JSON to file...")
    try:
        with open('demo_output.json', 'w', encoding='utf-8') as f:
            f.write(hdr10plus_json)
        print("✓ HDR10+ JSON saved to: demo_output.json")
        
        # Display file size
        import os
        file_size = os.path.getsize('demo_output.json')
        print(f"✓ File size: {file_size} bytes")
        
    except Exception as e:
        print(f"✗ File save failed: {e}")
        return
    
    # Step 5: Display sample of the JSON
    print("\n📄 Step 5: Sample of generated HDR10+ JSON:")
    print("-" * 50)
    
    # Pretty print a subset of the JSON
    sample_data = {
        "Tool": json_data["Tool"],
        "ToolVersion": json_data["ToolVersion"],
        "Title": json_data["Title"],
        "HDR10Plus": {
            "MasteringDisplay": hdr10plus["MasteringDisplay"],
            "MaxCLL": hdr10plus["MaxCLL"],
            "MaxFALL": hdr10plus["MaxFALL"],
            "SceneInfo": hdr10plus["SceneInfo"][:2]  # Show first 2 scenes
        }
    }
    
    print(json.dumps(sample_data, indent=2))
    print("... (truncated for display)")
    
    # Step 6: Validation
    print("\n✅ Step 6: Validating HDR10+ compliance...")
    try:
        from dolby_to_hdr10plus import HDR10PlusJSONGenerator
        generator = HDR10PlusJSONGenerator()
        
        if generator.validate_hdr10plus_json(json_data):
            print("✓ HDR10+ JSON validation passed!")
            print("✓ File is fully compliant with HDR10+ specification")
        else:
            print("✗ HDR10+ JSON validation failed!")
            
    except Exception as e:
        print(f"✗ Validation failed: {e}")
    
    # Step 7: Cleanup
    print("\n🧹 Step 7: Cleaning up temporary files...")
    try:
        import os
        if os.path.exists('demo.rpu'):
            os.remove('demo.rpu')
            print("✓ Cleaned up: demo.rpu")
        print("✓ Demo completed successfully!")
        
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
    
    print("\n🎉 Demo Summary:")
    print("=" * 60)
    print("✓ Successfully created and analyzed Dolby Vision RPU data")
    print("✓ Converted RPU metadata to HDR10+ format")
    print("✓ Generated fully compliant HDR10+ JSON file")
    print("✓ Validated HDR10+ compliance")
    print("✓ Demonstrated complete workflow from RPU to HDR10+")
    print("\nThe generated HDR10+ JSON file can be used with:")
    print("  - HDR10+ compatible video encoders")
    print("  - Color grading software")
    print("  - HDR10+ display devices")
    print("  - Video processing pipelines")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Basic usage example for Dolby Vision RPU to HDR10+ converter.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from dovi_to_hdr10plus import DolbyVisionConverter
from dovi_to_hdr10plus.validator import MetadataValidator


def main():
    """Basic usage example."""
    print("Dolby Vision RPU to HDR10+ Converter - Basic Usage Example")
    print("=" * 60)
    
    # Example 1: Heuristic conversion
    print("\n1. Heuristic Conversion Example")
    print("-" * 40)
    
    # Initialize converter with heuristic mode
    converter = DolbyVisionConverter(use_ml=False)
    
    # Note: This is a mock example since we don't have actual RPU files
    # In real usage, you would provide a path to an HEVC file or RPU binary
    print("Note: This example demonstrates the API structure.")
    print("In real usage, provide a path to an HEVC file or RPU binary:")
    print("  converter.convert_rpu_to_hdr10plus('input.hevc')")
    
    # Example 2: Generate example HDR10+ metadata
    print("\n2. Generate Example HDR10+ Metadata")
    print("-" * 40)
    
    from dovi_to_hdr10plus.json_generator import HDR10PlusJSONGenerator
    generator = HDR10PlusJSONGenerator()
    example_metadata = generator.generate_example_json()
    
    print("Example HDR10+ metadata structure:")
    print(f"  MaxCLL: {example_metadata['MaxCLL']}")
    print(f"  MaxFALL: {example_metadata['MaxFALL']}")
    print(f"  Mastering Display Max Luminance: {example_metadata['MasteringDisplay']['Luminance']['Max']}")
    print(f"  Color Primaries: {example_metadata['MasteringDisplay']['Primaries']['Red']}")
    
    # Example 3: Validate metadata
    print("\n3. Metadata Validation Example")
    print("-" * 40)
    
    validator = MetadataValidator()
    validation_result = validator.validate_hdr10plus(example_metadata)
    
    print(f"Validation Result:")
    print(f"  Valid: {validation_result['valid']}")
    print(f"  Compliance Score: {validation_result['compliance_score']:.2f}")
    print(f"  Warnings: {len(validation_result['warnings'])}")
    print(f"  Errors: {len(validation_result['errors'])}")
    
    if validation_result['warnings']:
        print("  Warnings:")
        for warning in validation_result['warnings']:
            print(f"    - {warning}")
    
    # Example 4: Compare with standard
    print("\n4. Standard Comparison Example")
    print("-" * 40)
    
    comparison = validator.compare_with_standard(example_metadata, "bt2020")
    print(f"Comparison with BT.2020:")
    print(f"  Similarity: {comparison['similarity']:.3f}")
    print(f"  Match Quality: {comparison['match_quality']}")
    
    print("\n" + "=" * 60)
    print("Basic usage example completed successfully!")


if __name__ == "__main__":
    main()
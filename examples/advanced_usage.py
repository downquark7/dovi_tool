#!/usr/bin/env python3
"""
Advanced usage example for Dolby Vision RPU to HDR10+ converter.
"""

import sys
from pathlib import Path
import json

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from dovi_to_hdr10plus import DolbyVisionConverter, RPUParser, HDR10PlusAnalyzer
from dovi_to_hdr10plus.validator import MetadataValidator


def main():
    """Advanced usage example."""
    print("Dolby Vision RPU to HDR10+ Converter - Advanced Usage Example")
    print("=" * 70)
    
    # Example 1: Custom RPU parsing and analysis
    print("\n1. Custom RPU Parsing and Analysis")
    print("-" * 50)
    
    parser = RPUParser()
    analyzer = HDR10PlusAnalyzer()
    
    # Note: In real usage, you would parse an actual RPU file
    print("Note: This example demonstrates the API structure.")
    print("In real usage, provide a path to an HEVC file or RPU binary:")
    print("  rpu_data = parser.parse_rpu('input.hevc')")
    
    # Example 2: Advanced metadata analysis
    print("\n2. Advanced Metadata Analysis")
    print("-" * 50)
    
    # Create sample metadata for analysis
    sample_metadata = {
        "MaxCLL": 2000,
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
        },
        "TargetedSystemDisplayMaximumLuminance": 1000,
        "TargetedSystemDisplayMinimumLuminance": 0.0001
    }
    
    # Analyze the metadata
    analysis_result = analyzer.analyze_metadata(sample_metadata)
    
    print("Metadata Analysis Results:")
    print(f"  Valid: {analysis_result['valid']}")
    print(f"  Warnings: {len(analysis_result['warnings'])}")
    print(f"  Errors: {len(analysis_result['errors'])}")
    
    if analysis_result['statistics']:
        print("\nStatistics:")
        for key, value in analysis_result['statistics'].items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value}")
    
    if analysis_result['recommendations']:
        print("\nRecommendations:")
        for rec in analysis_result['recommendations']:
            print(f"  - {rec}")
    
    # Example 3: Custom conversion with scene analysis
    print("\n3. Custom Conversion with Scene Analysis")
    print("-" * 50)
    
    from dovi_to_hdr10plus.heuristic_converter import HeuristicConverter
    
    # Create sample RPU data with scene information
    sample_rpu_data = {
        "content_light_level": {
            "max_cll": 2500,
            "max_fall": 200.0,
            "average_cll": 150.0
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
                "max": 4000.0
            }
        },
        "scene_info": {
            "scene_refresh_flag": True,
            "scene_change_detection": [100, 250, 500, 750],
            "frame_count": 1000
        },
        "tone_mapping": {
            "trim_slopes": [1.2, 1.1, 1.3],
            "trim_offsets": [0.1, 0.05, 0.15],
            "trim_power": [1.1, 1.0, 1.2]
        }
    }
    
    # Convert using heuristics
    heuristic_converter = HeuristicConverter()
    hdr10plus_metadata = heuristic_converter.convert(sample_rpu_data)
    
    print("Heuristic conversion completed:")
    print(f"  MaxCLL: {hdr10plus_metadata['MaxCLL']}")
    print(f"  MaxFALL: {hdr10plus_metadata['MaxFALL']}")
    
    # Apply scene analysis
    enhanced_metadata = heuristic_converter.apply_scene_analysis(sample_rpu_data, hdr10plus_metadata)
    
    if "SceneAnalysis" in enhanced_metadata:
        scene_analysis = enhanced_metadata["SceneAnalysis"]
        print(f"  Scene Changes: {scene_analysis.get('scene_changes', 0)}")
        print(f"  Adaptive Metadata: {scene_analysis.get('adaptive_metadata', False)}")
    
    # Example 4: Batch processing simulation
    print("\n4. Batch Processing Simulation")
    print("-" * 50)
    
    # Simulate processing multiple files
    file_list = ["file1.hevc", "file2.hevc", "file3.hevc"]
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    converter = DolbyVisionConverter(use_ml=False)
    
    print(f"Simulating batch processing of {len(file_list)} files:")
    for i, input_file in enumerate(file_list, 1):
        output_file = output_dir / f"output_{i}.json"
        print(f"  {i}. {input_file} -> {output_file}")
        
        # In real usage, you would call:
        # converter.convert_and_save(input_file, output_file)
    
    # Example 5: Custom validation and comparison
    print("\n5. Custom Validation and Comparison")
    print("-" * 50)
    
    validator = MetadataValidator()
    
    # Validate the converted metadata
    validation_result = validator.validate_hdr10plus(enhanced_metadata)
    
    print("Validation Results:")
    print(f"  Valid: {validation_result['valid']}")
    print(f"  Compliance Score: {validation_result['compliance_score']:.2f}")
    
    # Compare with different standards
    standards = ["bt2020", "bt709", "dci_p3"]
    print("\nStandard Comparisons:")
    for standard in standards:
        comparison = validator.compare_with_standard(enhanced_metadata, standard)
        print(f"  {standard.upper()}: {comparison['match_quality']} (similarity: {comparison['similarity']:.3f})")
    
    # Example 6: Export and import functionality
    print("\n6. Export and Import Functionality")
    print("-" * 50)
    
    # Save metadata to file
    output_file = output_dir / "advanced_example.json"
    with open(output_file, 'w') as f:
        json.dump(enhanced_metadata, f, indent=2)
    
    print(f"Metadata saved to: {output_file}")
    
    # Load and validate the saved file
    validation_result = validator.validate_json_file(output_file)
    print(f"Saved file validation: {'Valid' if validation_result['valid'] else 'Invalid'}")
    
    print("\n" + "=" * 70)
    print("Advanced usage example completed successfully!")


if __name__ == "__main__":
    main()
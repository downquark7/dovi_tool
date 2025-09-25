#!/usr/bin/env python3
"""
Complete workflow example for Dolby Vision RPU to HDR10+ converter.
This demonstrates the full pipeline from RPU parsing to HDR10+ JSON generation.
"""

import sys
from pathlib import Path
import json
import tempfile

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent))

from dovi_to_hdr10plus import DolbyVisionConverter, RPUParser, HDR10PlusAnalyzer
from dovi_to_hdr10plus.heuristic_converter import HeuristicConverter
from dovi_to_hdr10plus.ml_converter import MLConverter
from dovi_to_hdr10plus.json_generator import HDR10PlusJSONGenerator
from dovi_to_hdr10plus.validator import MetadataValidator


def create_sample_rpu_data():
    """Create sample RPU data for demonstration."""
    return {
        "source": "dolby_vision_rpu",
        "version": "1.0",
        "profile": {"level": 5},
        "level": {"level": 5},
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
        "content_light_level": {
            "max_cll": 2000,
            "max_fall": 200.0,
            "average_cll": 100.0
        },
        "tone_mapping": {
            "trim_slopes": [1.2, 1.1, 1.3],
            "trim_offsets": [0.1, 0.05, 0.15],
            "trim_power": [1.1, 1.0, 1.2],
            "trim_chroma_weight": [1.0, 1.0, 1.0],
            "trim_saturation_gain": [1.0, 1.0, 1.0]
        },
        "scene_info": {
            "scene_refresh_flag": True,
            "scene_change_detection": [100, 250, 500, 750, 900],
            "frame_count": 1000
        },
        "color_volume": {
            "color_primaries": "bt2020",
            "transfer_characteristics": "pq",
            "matrix_coefficients": "bt2020_ncl"
        }
    }


def demonstrate_heuristic_conversion():
    """Demonstrate heuristic-based conversion."""
    print("=" * 60)
    print("HEURISTIC CONVERSION DEMONSTRATION")
    print("=" * 60)
    
    # Create sample RPU data
    rpu_data = create_sample_rpu_data()
    print("Sample RPU data created")
    
    # Initialize heuristic converter
    converter = HeuristicConverter()
    print("Heuristic converter initialized")
    
    # Convert RPU to HDR10+
    hdr10plus_metadata = converter.convert(rpu_data)
    print("Conversion completed using heuristics")
    
    # Apply scene analysis
    enhanced_metadata = converter.apply_scene_analysis(rpu_data, hdr10plus_metadata)
    print("Scene analysis applied")
    
    # Display results
    print("\nConverted HDR10+ metadata:")
    print(f"  MaxCLL: {enhanced_metadata['MaxCLL']}")
    print(f"  MaxFALL: {enhanced_metadata['MaxFALL']}")
    print(f"  Mastering Display Max Luminance: {enhanced_metadata['MasteringDisplay']['Luminance']['Max']}")
    print(f"  Conversion Method: {enhanced_metadata['conversion_method']}")
    
    if "SceneAnalysis" in enhanced_metadata:
        scene_analysis = enhanced_metadata["SceneAnalysis"]
        print(f"  Scene Changes: {scene_analysis.get('scene_changes', 0)}")
        print(f"  Adaptive Metadata: {scene_analysis.get('adaptive_metadata', False)}")
    
    return enhanced_metadata


def demonstrate_ml_conversion():
    """Demonstrate machine learning-based conversion."""
    print("\n" + "=" * 60)
    print("MACHINE LEARNING CONVERSION DEMONSTRATION")
    print("=" * 60)
    
    # Create sample RPU data
    rpu_data = create_sample_rpu_data()
    print("Sample RPU data created")
    
    # Initialize ML converter
    ml_converter = MLConverter()
    print("ML converter initialized")
    
    # Generate synthetic training data
    print("Generating synthetic training data...")
    training_data = ml_converter.generate_synthetic_training_data(num_samples=50)
    print(f"Generated {len(training_data)} training examples")
    
    # Train the models
    print("Training ML models...")
    training_results = ml_converter.train(training_data)
    print("Training completed")
    
    # Display training results
    print("\nTraining Results:")
    for model_name, results in training_results.items():
        print(f"  {model_name}: MSE={results['mse']:.4f}, R²={results['r2_score']:.4f}")
    
    # Convert using trained model
    hdr10plus_metadata = ml_converter.convert(rpu_data)
    print("\nConversion completed using trained ML model")
    
    # Display results
    print("\nConverted HDR10+ metadata:")
    print(f"  MaxCLL: {hdr10plus_metadata['MaxCLL']}")
    print(f"  MaxFALL: {hdr10plus_metadata['MaxFALL']}")
    print(f"  Conversion Method: {hdr10plus_metadata['conversion_method']}")
    
    if 'prediction_confidence' in hdr10plus_metadata:
        print(f"  Prediction Confidence: {hdr10plus_metadata['prediction_confidence']}")
    
    return hdr10plus_metadata


def demonstrate_validation_and_analysis(metadata):
    """Demonstrate validation and analysis."""
    print("\n" + "=" * 60)
    print("VALIDATION AND ANALYSIS DEMONSTRATION")
    print("=" * 60)
    
    # Initialize validator and analyzer
    validator = MetadataValidator()
    analyzer = HDR10PlusAnalyzer()
    
    # Validate metadata
    print("Validating HDR10+ metadata...")
    validation_result = validator.validate_hdr10plus(metadata)
    
    print(f"\nValidation Results:")
    print(f"  Valid: {validation_result['valid']}")
    print(f"  Compliance Score: {validation_result['compliance_score']:.2f}")
    print(f"  Warnings: {len(validation_result['warnings'])}")
    print(f"  Errors: {len(validation_result['errors'])}")
    
    if validation_result['warnings']:
        print("\nWarnings:")
        for warning in validation_result['warnings']:
            print(f"  - {warning}")
    
    if validation_result['errors']:
        print("\nErrors:")
        for error in validation_result['errors']:
            print(f"  - {error}")
    
    if validation_result['recommendations']:
        print("\nRecommendations:")
        for rec in validation_result['recommendations']:
            print(f"  - {rec}")
    
    # Analyze metadata
    print("\nAnalyzing metadata...")
    analysis_result = analyzer.analyze_metadata(metadata)
    
    print(f"\nAnalysis Results:")
    print(f"  Valid: {analysis_result['valid']}")
    print(f"  Warnings: {len(analysis_result['warnings'])}")
    print(f"  Errors: {len(analysis_result['errors'])}")
    
    if analysis_result['statistics']:
        print("\nStatistics:")
        for key, value in analysis_result['statistics'].items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value}")
    
    # Compare with standards
    print("\nComparing with color space standards...")
    standards = ["bt2020", "bt709", "dci_p3"]
    
    for standard in standards:
        comparison = validator.compare_with_standard(metadata, standard)
        print(f"  {standard.upper()}: {comparison['match_quality']} (similarity: {comparison['similarity']:.3f})")


def demonstrate_json_generation(metadata):
    """Demonstrate JSON generation and file operations."""
    print("\n" + "=" * 60)
    print("JSON GENERATION AND FILE OPERATIONS DEMONSTRATION")
    print("=" * 60)
    
    # Initialize JSON generator
    generator = HDR10PlusJSONGenerator()
    print("JSON generator initialized")
    
    # Generate JSON structure
    print("Generating HDR10+ JSON structure...")
    json_metadata = generator.generate_json(metadata)
    print("JSON structure generated")
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = Path(f.name)
        generator.save_json_file(json_metadata, temp_file)
        print(f"JSON metadata saved to: {temp_file}")
    
    # Validate the saved file
    print("Validating saved JSON file...")
    validator = MetadataValidator()
    file_validation = validator.validate_json_file(temp_file)
    
    print(f"File validation: {'Valid' if file_validation['valid'] else 'Invalid'}")
    print(f"Compliance score: {file_validation['compliance_score']:.2f}")
    
    # Load and display the file
    print("\nSaved JSON content:")
    with open(temp_file, 'r') as f:
        loaded_metadata = json.load(f)
    
    print(json.dumps(loaded_metadata, indent=2))
    
    # Clean up
    temp_file.unlink()
    print(f"\nTemporary file cleaned up: {temp_file}")


def demonstrate_complete_workflow():
    """Demonstrate the complete workflow."""
    print("DOLBY VISION RPU TO HDR10+ CONVERTER")
    print("Complete Workflow Demonstration")
    print("=" * 60)
    
    # Step 1: Heuristic conversion
    heuristic_metadata = demonstrate_heuristic_conversion()
    
    # Step 2: ML conversion
    ml_metadata = demonstrate_ml_conversion()
    
    # Step 3: Validation and analysis (using heuristic result)
    demonstrate_validation_and_analysis(heuristic_metadata)
    
    # Step 4: JSON generation and file operations
    demonstrate_json_generation(heuristic_metadata)
    
    # Step 5: Compare results
    print("\n" + "=" * 60)
    print("CONVERSION COMPARISON")
    print("=" * 60)
    
    print("Heuristic vs ML Conversion Results:")
    print(f"  MaxCLL: {heuristic_metadata['MaxCLL']} vs {ml_metadata['MaxCLL']}")
    print(f"  MaxFALL: {heuristic_metadata['MaxFALL']} vs {ml_metadata['MaxFALL']}")
    
    # Calculate differences
    max_cll_diff = abs(heuristic_metadata['MaxCLL'] - ml_metadata['MaxCLL'])
    max_fall_diff = abs(heuristic_metadata['MaxFALL'] - ml_metadata['MaxFALL'])
    
    print(f"\nDifferences:")
    print(f"  MaxCLL difference: {max_cll_diff}")
    print(f"  MaxFALL difference: {max_fall_diff:.2f}")
    
    print("\n" + "=" * 60)
    print("COMPLETE WORKFLOW DEMONSTRATION FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_complete_workflow()
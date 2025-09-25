#!/usr/bin/env python3
"""
Machine learning training example for Dolby Vision RPU to HDR10+ converter.
"""

import sys
from pathlib import Path
import json

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from dovi_to_hdr10plus import MLConverter


def main():
    """ML training example."""
    print("Dolby Vision RPU to HDR10+ Converter - ML Training Example")
    print("=" * 60)
    
    # Initialize ML converter
    print("\n1. Initializing ML Converter")
    print("-" * 40)
    
    ml_converter = MLConverter()
    print("ML converter initialized with default models")
    
    # Generate synthetic training data
    print("\n2. Generating Synthetic Training Data")
    print("-" * 40)
    
    print("Generating 100 synthetic training examples...")
    training_data = ml_converter.generate_synthetic_training_data(num_samples=100)
    print(f"Generated {len(training_data)} training examples")
    
    # Show example training data structure
    if training_data:
        example = training_data[0]
        print("\nExample training data structure:")
        print("RPU Data keys:", list(example["rpu_data"].keys()))
        print("HDR10+ Data keys:", list(example["hdr10plus_data"].keys()))
    
    # Train the models
    print("\n3. Training ML Models")
    print("-" * 40)
    
    print("Training models on synthetic data...")
    training_results = ml_converter.train(training_data)
    
    print("Training completed! Results:")
    for model_name, results in training_results.items():
        print(f"  {model_name}:")
        print(f"    MSE: {results['mse']:.4f}")
        print(f"    R² Score: {results['r2_score']:.4f}")
    
    # Save the trained model
    print("\n4. Saving Trained Model")
    print("-" * 40)
    
    model_path = "trained_model.pkl"
    ml_converter.save_model(model_path)
    print(f"Model saved to {model_path}")
    
    # Test the trained model
    print("\n5. Testing Trained Model")
    print("-" * 40)
    
    # Generate a test example
    test_rpu_data = ml_converter._generate_synthetic_rpu_data()
    print("Generated test RPU data")
    
    # Convert using the trained model
    hdr10plus_metadata = ml_converter.convert(test_rpu_data)
    print("Conversion completed using trained ML model")
    
    print("\nConverted HDR10+ metadata:")
    print(f"  MaxCLL: {hdr10plus_metadata['MaxCLL']}")
    print(f"  MaxFALL: {hdr10plus_metadata['MaxFALL']}")
    print(f"  Conversion Method: {hdr10plus_metadata['conversion_method']}")
    
    if 'prediction_confidence' in hdr10plus_metadata:
        print(f"  Prediction Confidence: {hdr10plus_metadata['prediction_confidence']}")
    
    # Load the model back to test persistence
    print("\n6. Testing Model Persistence")
    print("-" * 40)
    
    new_ml_converter = MLConverter(model_path=model_path)
    print("Model loaded successfully")
    
    # Test conversion with loaded model
    test_metadata = new_ml_converter.convert(test_rpu_data)
    print("Conversion with loaded model completed")
    
    print("\n" + "=" * 60)
    print("ML training example completed successfully!")
    print(f"Trained model saved as: {model_path}")


if __name__ == "__main__":
    main()
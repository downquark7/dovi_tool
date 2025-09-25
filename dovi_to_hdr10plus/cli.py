"""
Command-line interface for Dolby Vision RPU to HDR10+ converter.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .converter import DolbyVisionConverter
from .validator import MetadataValidator

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Dolby Vision RPU metadata to HDR10+ JSON format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert HEVC file to HDR10+ JSON
  dovi-to-hdr10plus input.hevc output.json
  
  # Use machine learning for conversion
  dovi-to-hdr10plus input.hevc output.json --use-ml --model-path model.pkl
  
  # Validate existing HDR10+ JSON file
  dovi-to-hdr10plus --validate input.json
  
  # Generate example HDR10+ JSON
  dovi-to-hdr10plus --generate-example example.json
        """
    )
    
    # Input/Output arguments
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Input HEVC file or RPU binary file"
    )
    parser.add_argument(
        "output_path",
        nargs="?",
        help="Output HDR10+ JSON file"
    )
    
    # Conversion options
    parser.add_argument(
        "--use-ml",
        action="store_true",
        help="Use machine learning for conversion (requires trained model)"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        help="Path to trained ML model file"
    )
    parser.add_argument(
        "--heuristic-only",
        action="store_true",
        help="Use only heuristic conversion (disable ML)"
    )
    
    # Validation options
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate existing HDR10+ JSON file"
    )
    parser.add_argument(
        "--compare-standard",
        choices=["bt2020", "bt709", "dci_p3"],
        help="Compare with standard color space"
    )
    
    # Utility options
    parser.add_argument(
        "--generate-example",
        action="store_true",
        help="Generate example HDR10+ JSON file"
    )
    parser.add_argument(
        "--rpu-info",
        action="store_true",
        help="Show RPU information without conversion"
    )
    
    # General options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="dovi-to-hdr10plus 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    try:
        if args.validate:
            validate_mode(args)
        elif args.generate_example:
            generate_example_mode(args)
        elif args.rpu_info:
            rpu_info_mode(args)
        else:
            convert_mode(args)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        if args.verbose:
            logger.exception("Full traceback:")
        sys.exit(1)


def convert_mode(args) -> None:
    """Handle conversion mode."""
    if not args.input_path or not args.output_path:
        logger.error("Both input and output paths are required for conversion")
        sys.exit(1)
    
    input_path = Path(args.input_path)
    output_path = Path(args.output_path)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Initialize converter
    use_ml = args.use_ml and not args.heuristic_only
    converter = DolbyVisionConverter(use_ml=use_ml, model_path=args.model_path)
    
    # Perform conversion
    logger.info(f"Converting {input_path} to {output_path}")
    converter.convert_and_save(input_path, output_path)
    
    # Validate output if requested
    if args.compare_standard:
        validator = MetadataValidator()
        validation_result = validator.validate_json_file(output_path)
        
        if validation_result["valid"]:
            logger.info(f"Validation passed - Compliance score: {validation_result['compliance_score']:.2f}")
            
            # Compare with standard
            with open(output_path, 'r') as f:
                import json
                metadata = json.load(f)
            
            comparison = validator.compare_with_standard(metadata, args.compare_standard)
            logger.info(f"Comparison with {args.compare_standard.upper()}: {comparison['match_quality']} (similarity: {comparison['similarity']:.3f})")
        else:
            logger.warning("Validation failed:")
            for error in validation_result["errors"]:
                logger.warning(f"  - {error}")
    
    logger.info("Conversion completed successfully")


def validate_mode(args) -> None:
    """Handle validation mode."""
    if not args.input_path:
        logger.error("Input JSON file path is required for validation")
        sys.exit(1)
    
    input_path = Path(args.input_path)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    if not input_path.suffix.lower() == '.json':
        logger.error("Input file must be a JSON file for validation")
        sys.exit(1)
    
    # Validate file
    validator = MetadataValidator()
    validation_result = validator.validate_json_file(input_path)
    
    # Print results
    print(f"\nValidation Results for {input_path}:")
    print(f"Valid: {'Yes' if validation_result['valid'] else 'No'}")
    print(f"Compliance Score: {validation_result['compliance_score']:.2f}")
    
    if validation_result["errors"]:
        print(f"\nErrors ({len(validation_result['errors'])}):")
        for error in validation_result["errors"]:
            print(f"  - {error}")
    
    if validation_result["warnings"]:
        print(f"\nWarnings ({len(validation_result['warnings'])}):")
        for warning in validation_result["warnings"]:
            print(f"  - {warning}")
    
    if validation_result["recommendations"]:
        print(f"\nRecommendations ({len(validation_result['recommendations'])}):")
        for recommendation in validation_result["recommendations"]:
            print(f"  - {recommendation}")
    
    # Compare with standard if requested
    if args.compare_standard:
        with open(input_path, 'r') as f:
            import json
            metadata = json.load(f)
        
        comparison = validator.compare_with_standard(metadata, args.compare_standard)
        print(f"\nComparison with {args.compare_standard.upper()}:")
        print(f"  Similarity: {comparison['similarity']:.3f}")
        print(f"  Match Quality: {comparison['match_quality']}")
    
    if not validation_result["valid"]:
        sys.exit(1)


def generate_example_mode(args) -> None:
    """Handle example generation mode."""
    if not args.output_path:
        logger.error("Output path is required for example generation")
        sys.exit(1)
    
    output_path = Path(args.output_path)
    
    # Generate example
    from .json_generator import HDR10PlusJSONGenerator
    generator = HDR10PlusJSONGenerator()
    example_json = generator.generate_example_json()
    
    # Save example
    generator.save_json_file(example_json, output_path)
    logger.info(f"Example HDR10+ JSON file generated: {output_path}")


def rpu_info_mode(args) -> None:
    """Handle RPU info mode."""
    if not args.input_path:
        logger.error("Input file path is required for RPU info")
        sys.exit(1)
    
    input_path = Path(args.input_path)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Get RPU info
    from .rpu_parser import RPUParser
    parser = RPUParser()
    
    # Parse RPU data
    rpu_data = parser.parse_rpu(input_path)
    if not rpu_data:
        logger.error("Failed to parse RPU data")
        sys.exit(1)
    
    # Print RPU information
    print(f"\nRPU Information for {input_path}:")
    print(f"Source: {rpu_data.get('source', 'unknown')}")
    print(f"Version: {rpu_data.get('version', 'unknown')}")
    
    # Content light level
    content_light = rpu_data.get("content_light_level", {})
    if content_light:
        print(f"\nContent Light Level:")
        print(f"  MaxCLL: {content_light.get('max_cll', 'N/A')}")
        print(f"  MaxFALL: {content_light.get('max_fall', 'N/A')}")
        print(f"  Average CLL: {content_light.get('average_cll', 'N/A')}")
    
    # Mastering display
    mastering_display = rpu_data.get("mastering_display", {})
    if mastering_display:
        print(f"\nMastering Display:")
        luminance = mastering_display.get("luminance", {})
        print(f"  Min Luminance: {luminance.get('min', 'N/A')}")
        print(f"  Max Luminance: {luminance.get('max', 'N/A')}")
        
        primaries = mastering_display.get("primaries", {})
        if primaries:
            print(f"  Color Primaries:")
            for color, coords in primaries.items():
                print(f"    {color}: {coords}")
    
    # Scene info
    scene_info = rpu_data.get("scene_info", {})
    if scene_info:
        print(f"\nScene Information:")
        print(f"  Scene Refresh Flag: {scene_info.get('scene_refresh_flag', 'N/A')}")
        print(f"  Frame Count: {scene_info.get('frame_count', 'N/A')}")
    
    # Get summary from dovi_tool
    summary = parser.get_rpu_summary(input_path)
    if summary:
        print(f"\nDetailed RPU Summary:")
        print(summary)


if __name__ == "__main__":
    main()
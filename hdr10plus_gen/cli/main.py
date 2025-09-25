"""
Command Line Interface for HDR10+ Generator

This module provides the CLI interface for converting Dolby Vision RPU
data to HDR10+ dynamic metadata.
"""

import click
import os
import json
from pathlib import Path
from typing import Optional
from ..rpu_parser import RPUParser
from ..hdr10plus_generator import HDR10PlusGenerator
from ..validator import HDR10PlusValidator


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """HDR10+ Generator - Convert Dolby Vision RPU to HDR10+ dynamic metadata"""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--target-luminance', '-t', type=int, default=1000,
              help='Target display maximum luminance in nits (default: 1000)')
@click.option('--validate', is_flag=True, default=True,
              help='Validate output metadata (default: True)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
def convert(input_file: str, output_file: str, target_luminance: int, 
           validate: bool, verbose: bool):
    """Convert a single Dolby Vision RPU file to HDR10+ JSON"""
    
    if verbose:
        click.echo(f"Converting {input_file} to {output_file}")
        click.echo(f"Target luminance: {target_luminance} nits")
    
    try:
        # Parse RPU file
        if verbose:
            click.echo("Parsing RPU file...")
        parser = RPUParser()
        rpu_metadata = parser.parse(input_file)
        
        if verbose:
            click.echo(f"Parsed RPU: Profile {rpu_metadata.profile}, Level {rpu_metadata.level}")
            click.echo(f"Found {len(rpu_metadata.frame_metadata)} frames")
        
        # Generate HDR10+ metadata
        if verbose:
            click.echo("Generating HDR10+ metadata...")
        generator = HDR10PlusGenerator(target_display_luminance=target_luminance)
        hdr10plus_metadata = generator.convert(rpu_metadata)
        
        # Validate if requested
        if validate:
            if verbose:
                click.echo("Validating metadata...")
            validator = HDR10PlusValidator()
            is_valid, errors = validator.validate_metadata(hdr10plus_metadata)
            
            if not is_valid:
                click.echo("Validation failed:", err=True)
                for error in errors:
                    click.echo(f"  - {error}", err=True)
                raise click.Abort()
            
            if verbose:
                click.echo("Validation passed")
        
        # Save output
        if verbose:
            click.echo(f"Saving to {output_file}")
        generator.save_json(hdr10plus_metadata, output_file)
        
        click.echo(f"Successfully converted {input_file} to {output_file}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False))
@click.argument('output_dir', type=click.Path())
@click.option('--target-luminance', '-t', type=int, default=1000,
              help='Target display maximum luminance in nits (default: 1000)')
@click.option('--pattern', '-p', default='*.rpu',
              help='File pattern to match (default: *.rpu)')
@click.option('--validate', is_flag=True, default=True,
              help='Validate output metadata (default: True)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
def batch(input_dir: str, output_dir: str, target_luminance: int,
          pattern: str, validate: bool, verbose: bool):
    """Batch convert multiple RPU files to HDR10+ JSON"""
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find RPU files
    rpu_files = list(input_path.glob(pattern))
    
    if not rpu_files:
        click.echo(f"No files found matching pattern '{pattern}' in {input_dir}")
        return
    
    if verbose:
        click.echo(f"Found {len(rpu_files)} files to convert")
    
    # Process files
    success_count = 0
    error_count = 0
    
    for rpu_file in rpu_files:
        try:
            # Generate output filename
            output_file = output_path / f"{rpu_file.stem}.json"
            
            if verbose:
                click.echo(f"Converting {rpu_file.name}...")
            
            # Convert file
            convert_single_file(str(rpu_file), str(output_file), target_luminance, validate, False)
            success_count += 1
            
        except Exception as e:
            click.echo(f"Error converting {rpu_file.name}: {e}", err=True)
            error_count += 1
    
    click.echo(f"Batch conversion complete: {success_count} successful, {error_count} errors")


@cli.command()
@click.argument('metadata_file', type=click.Path(exists=True))
@click.option('--report', '-r', is_flag=True,
              help='Generate detailed validation report')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
def validate(metadata_file: str, report: bool, verbose: bool):
    """Validate HDR10+ JSON metadata file"""
    
    try:
        validator = HDR10PlusValidator()
        
        if verbose:
            click.echo(f"Validating {metadata_file}...")
        
        is_valid, errors = validator.validate_file(metadata_file)
        
        if is_valid:
            click.echo("✓ Validation passed")
            
            if report:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                validation_report = validator.get_validation_report(metadata)
                
                click.echo("\nValidation Report:")
                click.echo(f"  Scenes: {validation_report['statistics']['num_scenes']}")
                click.echo(f"  Global Max Luminance: {validation_report['statistics']['global_max_luminance']} nits")
                click.echo(f"  Max Content Light Level: {validation_report['statistics']['global_max_cll']} nits")
                click.echo(f"  Max Frame Average Light Level: {validation_report['statistics']['global_max_fall']} nits")
                click.echo(f"  Bezier Curve Anchors: {validation_report['statistics']['num_bezier_anchors']}")
                
                if validation_report['warnings']:
                    click.echo("\nWarnings:")
                    for warning in validation_report['warnings']:
                        click.echo(f"  - {warning}")
        else:
            click.echo("✗ Validation failed:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            raise click.Abort()
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--input-dir', '-i', type=click.Path(exists=True),
              help='Input directory containing test files')
@click.option('--output-dir', '-o', type=click.Path(),
              help='Output directory for test results')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
def test(input_dir: Optional[str], output_dir: Optional[str], verbose: bool):
    """Run the built-in test suite"""
    
    if verbose:
        click.echo("Running HDR10+ Generator test suite...")
    
    # Import and run tests
    try:
        import pytest
        import sys
        
        test_args = ['-v'] if verbose else []
        if input_dir:
            test_args.extend(['--input-dir', input_dir])
        if output_dir:
            test_args.extend(['--output-dir', output_dir])
        
        exit_code = pytest.main(test_args)
        
        if exit_code == 0:
            click.echo("✓ All tests passed")
        else:
            click.echo("✗ Some tests failed", err=True)
            sys.exit(exit_code)
            
    except ImportError:
        click.echo("pytest not installed. Install with: pip install pytest", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error running tests: {e}", err=True)
        raise click.Abort()


def convert_single_file(input_file: str, output_file: str, target_luminance: int,
                       validate: bool, verbose: bool):
    """Helper function to convert a single file (used by batch command)"""
    # Parse RPU file
    parser = RPUParser()
    rpu_metadata = parser.parse(input_file)
    
    # Generate HDR10+ metadata
    generator = HDR10PlusGenerator(target_display_luminance=target_luminance)
    hdr10plus_metadata = generator.convert(rpu_metadata)
    
    # Validate if requested
    if validate:
        validator = HDR10PlusValidator()
        is_valid, errors = validator.validate_metadata(hdr10plus_metadata)
        
        if not is_valid:
            raise ValueError(f"Validation failed: {', '.join(errors)}")
    
    # Save output
    generator.save_json(hdr10plus_metadata, output_file)


def main():
    """Main entry point for CLI"""
    cli()


if __name__ == '__main__':
    main()
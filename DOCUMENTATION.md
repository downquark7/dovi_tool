# HDR10+ Generator Documentation

## Overview

HDR10+ Generator is a complete, end-to-end tool for converting Dolby Vision RPU (Reference Processing Unit) data into HDR10+ dynamic metadata with full SMPTE ST 2094-40 compliance. The tool is optimized for maximum accuracy in luminance values below 1000 nits, with highest precision at progressively lower nit ranges.

## Features

### Core Functionality
- **Complete RPU Parsing**: Extract metadata from Dolby Vision RPU files
- **HDR10+ Generation**: Generate fully compliant HDR10+ JSON metadata
- **Advanced Tone Mapping**: Optimized algorithms for low-nit accuracy
- **Schema Validation**: Built-in validation against HDR10+ schema
- **CLI & API**: Both command-line interface and Python API

### Accuracy & Quality
- **Low-Nit Optimization**: Highest precision for luminance values <1000 nits
- **Perceptual Preservation**: Maintains perceptual intent without banding or clipping
- **Stability**: Prevents flicker and instability in shadows and near-black
- **Deterministic Output**: Identical inputs always produce identical outputs

### Standards Compliance
- **SMPTE ST 2094-40**: Full HDR10+ dynamic metadata compliance
- **HDR10 Baseline**: Compatible with HDR10 signaling
- **ST 2086**: Proper PQ (Perceptual Quantizer) handling
- **Schema Validation**: JSON output validates against HDR10+ schema

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install from Source
```bash
git clone <repository-url>
cd hdr10plus_gen
pip install -e .
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

#### Convert Single File
```bash
hdr10plus_gen convert input.rpu output.json
```

#### Batch Convert
```bash
hdr10plus_gen batch convert input_dir/ output_dir/
```

#### Validate Metadata
```bash
hdr10plus_gen validate metadata.json
```

#### Run Tests
```bash
hdr10plus_gen test
```

### Python API

#### Basic Conversion
```python
from hdr10plus_gen import HDR10PlusGenerator, RPUParser

# Parse RPU file
parser = RPUParser()
rpu_metadata = parser.parse("input.rpu")

# Generate HDR10+ metadata
generator = HDR10PlusGenerator(target_display_luminance=1000)
hdr10plus_metadata = generator.convert(rpu_metadata)

# Save to JSON
generator.save_json(hdr10plus_metadata, "output.json")
```

#### Advanced Usage
```python
from hdr10plus_gen import HDR10PlusGenerator, RPUParser, HDR10PlusValidator

# Parse RPU with custom settings
parser = RPUParser()
rpu_metadata = parser.parse("input.rpu")

# Generate with custom target luminance
generator = HDR10PlusGenerator(target_display_luminance=4000)
hdr10plus_metadata = generator.convert(rpu_metadata)

# Validate metadata
validator = HDR10PlusValidator()
is_valid, errors = validator.validate_metadata(hdr10plus_metadata)

if is_valid:
    print("Metadata is valid")
else:
    print(f"Validation errors: {errors}")

# Get detailed validation report
report = validator.get_validation_report(hdr10plus_metadata)
print(f"Statistics: {report['statistics']}")
```

## Architecture

### Core Components

#### RPU Parser (`rpu_parser.py`)
- Parses Dolby Vision RPU binary format
- Extracts scene, shot, and frame metadata
- Calculates luminance statistics
- Handles different RPU profiles and levels

#### HDR10+ Generator (`hdr10plus_generator.py`)
- Converts RPU metadata to HDR10+ format
- Implements advanced tone mapping algorithms
- Optimizes for low-nit accuracy
- Generates bezier curve anchors

#### Validator (`validator.py`)
- Validates HDR10+ metadata against schema
- Performs compliance checks
- Generates validation reports
- Provides quality warnings

#### CLI Interface (`cli/main.py`)
- Command-line interface for all functionality
- Batch processing capabilities
- Validation and testing commands
- Progress reporting and error handling

### Tone Mapping Algorithm

The tone mapping algorithm is specifically optimized for low-nit content:

1. **Content Analysis**: Analyzes luminance distribution and characteristics
2. **Low-Nit Detection**: Identifies content with max luminance <1000 nits
3. **Optimized Parameters**: Adjusts knee points and bezier curves for better shadow detail
4. **Precision Enhancement**: Uses more anchor points in low-nit ranges
5. **Perceptual Preservation**: Maintains visual quality without artifacts

### Bezier Curve Generation

The bezier curve generation uses a multi-stage approach:

1. **Low-Nit Range (0-100 nits)**: 5 anchor points for maximum precision
2. **Mid-Nit Range (100-500 nits)**: 3 anchor points for smooth transitions
3. **High-Nit Range (500+ nits)**: 2 anchor points for highlight handling

## Testing

### Test Suite Structure

#### Unit Tests
- `test_rpu_parser.py`: RPU parsing functionality
- `test_hdr10plus_generator.py`: HDR10+ generation
- `test_validator.py`: Metadata validation

#### Integration Tests
- `test_integration.py`: End-to-end workflow testing
- `test_golden_files.py`: Regression testing against reference files
- `test_stress.py`: Stress testing and edge cases

### Running Tests

#### Run All Tests
```bash
python run_tests.py
```

#### Run Specific Test Categories
```bash
# Unit tests only
pytest hdr10plus_gen/tests/test_rpu_parser.py -v

# Integration tests
pytest hdr10plus_gen/tests/test_integration.py -v

# Stress tests
pytest hdr10plus_gen/tests/test_stress.py -v

# With coverage
pytest hdr10plus_gen/tests/ --cov=hdr10plus_gen --cov-report=html
```

### Test Coverage

The test suite provides comprehensive coverage:
- **Schema Validation**: 100% of HDR10+ schema requirements
- **Golden File Round-Trip**: Reference file comparison
- **Synthetic Stress Tests**: Edge cases and extreme conditions
- **Error Handling**: Malformed input and error conditions
- **Determinism**: Identical input/output verification

## Configuration

### Environment Variables

- `HDR10PLUS_TARGET_LUMINANCE`: Default target display luminance (default: 1000)
- `HDR10PLUS_SCHEMA_PATH`: Path to HDR10+ schema file
- `HDR10PLUS_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Configuration Files

The tool can be configured using a JSON configuration file:

```json
{
  "target_display_luminance": 1000,
  "low_nit_optimization": true,
  "bezier_curve_precision": "high",
  "validation_strict": true
}
```

## Performance

### Benchmarks

Typical performance on modern hardware:
- **Small files** (<100 frames): <1 second
- **Medium files** (100-1000 frames): 1-5 seconds
- **Large files** (1000+ frames): 5-15 seconds

### Memory Usage

- **Base memory**: ~50MB
- **Per 1000 frames**: +10MB
- **Peak memory**: <200MB for typical content

### Optimization Tips

1. **Batch Processing**: Use batch mode for multiple files
2. **Memory Management**: Process large files in chunks
3. **Validation**: Disable validation for faster processing
4. **Parallel Processing**: Use multiple processes for batch operations

## Troubleshooting

### Common Issues

#### Validation Errors
```
Error: Schema validation failed
```
**Solution**: Check that input RPU file is valid and complete

#### Memory Issues
```
Error: Out of memory
```
**Solution**: Process files in smaller batches or increase system memory

#### Performance Issues
```
Warning: Conversion taking too long
```
**Solution**: Check file size and consider using lower precision settings

### Debug Mode

Enable debug logging for detailed information:
```bash
export HDR10PLUS_LOG_LEVEL=DEBUG
hdr10plus_gen convert input.rpu output.json
```

### Validation Reports

Generate detailed validation reports:
```python
from hdr10plus_gen import HDR10PlusValidator

validator = HDR10PlusValidator()
report = validator.get_validation_report(metadata)
print(json.dumps(report, indent=2))
```

## Contributing

### Development Setup

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```
3. Run tests:
   ```bash
   python run_tests.py
   ```

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Maintain test coverage above 90%

### Submitting Changes

1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass
4. Submit a pull request with detailed description

## License

MIT License - see LICENSE file for details.

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check the documentation
- Review test examples
- Contact the development team

## Changelog

### Version 1.0.0
- Initial release
- Complete RPU to HDR10+ conversion
- Advanced tone mapping algorithms
- Comprehensive test suite
- CLI and Python API
- Full SMPTE ST 2094-40 compliance
# HDR10+ Generator

A complete, end-to-end tool for converting Dolby Vision RPU (Reference Processing Unit) data into HDR10+ dynamic metadata with full SMPTE ST 2094-40 compliance.

## Features

- **Complete RPU Parsing**: Extract metadata from Dolby Vision RPU files
- **HDR10+ Generation**: Generate fully compliant HDR10+ JSON metadata
- **High Precision**: Optimized for luminance values below 1000 nits with highest precision at lower ranges
- **Tone Mapping**: Advanced tone mapping algorithms preserving perceptual intent
- **Validation**: Built-in schema validation and compliance checking
- **CLI & API**: Both command-line interface and Python API
- **Comprehensive Testing**: Full test suite with golden file validation

## Installation

```bash
pip install -e .
```

## Quick Start

### Command Line Interface

```bash
# Convert a single RPU file
hdr10plus_gen convert input.rpu output.json

# Batch convert multiple files
hdr10plus_gen batch convert input_dir/ output_dir/

# Validate HDR10+ JSON files
hdr10plus_gen validate metadata.json
```

### Python API

```python
from hdr10plus_gen import HDR10PlusGenerator
from hdr10plus_gen.rpu_parser import RPUParser

# Parse RPU and generate HDR10+ metadata
parser = RPUParser()
rpu_data = parser.parse("input.rpu")

generator = HDR10PlusGenerator()
hdr10plus_metadata = generator.convert(rpu_data)

# Save to JSON
generator.save_json(hdr10plus_metadata, "output.json")
```

## Standards Compliance

- **SMPTE ST 2094-40**: Full HDR10+ dynamic metadata compliance
- **HDR10 Baseline**: Compatible with HDR10 signaling
- **ST 2086**: Proper PQ (Perceptual Quantizer) handling
- **Schema Validation**: JSON output validates against HDR10+ schema

## Testing

Run the comprehensive test suite:

```bash
pytest
```

The test suite includes:
- Schema validation tests
- Golden file round-trip tests
- Synthetic stress tests
- Error handling tests
- Determinism tests

## License

MIT License - see LICENSE file for details.
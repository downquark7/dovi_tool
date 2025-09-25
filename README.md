# Dolby Vision RPU to HDR10+ Metadata Converter

A comprehensive Python library for converting Dolby Vision Reference Processing Unit (RPU) data into HDR10+ metadata and generating fully compliant HDR10+ JSON files.

## Features

- **Complete RPU Parsing**: Supports parsing of Dolby Vision RPU data with support for multiple RPU types
- **HDR10+ Compliance**: Generates fully compliant HDR10+ JSON metadata files
- **High Fidelity Conversion**: Maintains maximum accuracy and fidelity to the source Dolby Vision content
- **Advanced Metadata Extraction**: Extracts mastering display information, content light levels, and dynamic metadata
- **Validation**: Built-in validation ensures HDR10+ JSON compliance
- **Multiple Interfaces**: Both programmatic API and command-line interfaces

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from dolby_to_hdr10plus import convert_dolby_vision_rpu_to_hdr10plus

# Read RPU data from file
with open('input.rpu', 'rb') as f:
    rpu_data = f.read()

# Convert to HDR10+ JSON
hdr10plus_json = convert_dolby_vision_rpu_to_hdr10plus(
    rpu_data,
    title="My Dolby Vision Content",
    alternate_version="Theatrical Release"
)

# Save to file
with open('output.json', 'w') as f:
    f.write(hdr10plus_json)
```

### Command Line Usage

```bash
# Convert RPU file to HDR10+ JSON
python dolby_to_hdr10plus.py input.rpu output.json "Content Title" "Version Description"

# Analyze RPU file structure
python advanced_rpu_parser.py input.rpu
```

## API Reference

### Main Functions

#### `convert_dolby_vision_rpu_to_hdr10plus(rpu_data, title="", alternate_version="")`

Convert Dolby Vision RPU data to HDR10+ JSON metadata.

**Parameters:**
- `rpu_data` (bytes): Raw RPU data
- `title` (str): Content title for metadata
- `alternate_version` (str): Version description for metadata

**Returns:**
- `str`: JSON string containing HDR10+ metadata

## Examples

See `example_usage.py` for comprehensive examples including:
- Basic conversion
- File-based conversion
- Advanced RPU parsing
- Custom metadata creation
- Batch conversion

## Requirements

- Python 3.7+
- numpy >= 1.21.0
- structlog >= 22.0.0
- typing-extensions >= 4.0.0

## License

MIT License
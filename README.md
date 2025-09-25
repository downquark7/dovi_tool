# Dolby Vision RPU to HDR10+ Metadata Converter

This tool extracts HDR10+ metadata from Dolby Vision RPU (Reference Processing Unit) data and produces valid HDR10+ JSON metadata files using heuristics and machine learning algorithms.

## Features

- **Dolby Vision RPU Parsing**: Extract and analyze RPU metadata using dovi_tool integration
- **Heuristic Conversion**: Rule-based algorithms to approximate HDR10+ metadata
- **Machine Learning**: Tunable ML models for improved conversion accuracy
- **HDR10+ JSON Generation**: Generate compliant HDR10+ metadata files
- **Validation Tools**: Verify generated metadata against HDR10+ standards

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install dovi_tool (required for RPU extraction):
```bash
cargo install dovi_tool
```

## Usage

### Command Line Interface

```bash
# Convert Dolby Vision RPU to HDR10+ JSON
python -m dovi_to_hdr10plus.cli input.hevc output.json

# Use machine learning model for conversion
python -m dovi_to_hdr10plus.cli input.hevc output.json --use-ml

# Validate existing HDR10+ metadata
python -m dovi_to_hdr10plus.cli --validate input.json
```

### Python API

```python
from dovi_to_hdr10plus import DolbyVisionConverter

# Initialize converter
converter = DolbyVisionConverter()

# Convert RPU to HDR10+ metadata
hdr10plus_metadata = converter.convert_rpu_to_hdr10plus("input.hevc")

# Save to JSON file
converter.save_hdr10plus_json(hdr10plus_metadata, "output.json")
```

## Architecture

- `rpu_parser.py`: Dolby Vision RPU extraction and parsing
- `hdr10plus_analyzer.py`: HDR10+ metadata analysis and validation
- `heuristic_converter.py`: Rule-based conversion algorithms
- `ml_converter.py`: Machine learning-based conversion
- `json_generator.py`: HDR10+ JSON metadata generation
- `validator.py`: Metadata validation tools

## Limitations

Due to the proprietary nature of Dolby Vision's tone mapping algorithms, exact conversion to HDR10+ is not possible. This tool uses heuristics and machine learning to approximate the conversion process. Results should be validated for accuracy and compatibility.
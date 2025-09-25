# Dolby Vision RPU to HDR10+ Converter

This document describes the Dolby Vision RPU to HDR10+ dynamic metadata converter implemented in dovi_tool.

## Overview

The converter transforms Dolby Vision Reference Processing Unit (RPU) data into HDR10+ dynamic metadata conforming to SMPTE ST 2094-40 standards. It prioritizes accuracy for luminance values below 1000 nits, with highest precision at progressively lower nit ranges.

## Features

- **High Precision Mode**: Optimized for low-nit content (<1000 nits) with logarithmic distribution calculation
- **Scene Detection**: Automatic scene detection based on luminance changes
- **Schema Validation**: Built-in HDR10+ JSON schema validation
- **Multiple Input Support**: Convert single or multiple RPU files
- **Configurable Parameters**: Customizable target display luminance, peak brightness source, and scene detection thresholds

## Usage

### Command Line Interface

```bash
# Convert single RPU file to HDR10+ JSON
dovi_tool convert-to-hdr10plus -i input.rpu -o output.json

# Convert multiple RPU files with scene detection
dovi_tool convert-to-hdr10plus -i rpu1.bin rpu2.bin rpu3.bin -o output.json

# Enable high precision mode for low-nit content
dovi_tool convert-to-hdr10plus -i input.rpu -o output.json --high-precision-mode

# Set target display maximum luminance
dovi_tool convert-to-hdr10plus -i input.rpu -o output.json --target-display-max-luminance 1000

# Configure scene detection threshold
dovi_tool convert-to-hdr10plus -i rpu1.bin rpu2.bin -o output.json --scene-detection-threshold 0.2
```

### Command Options

- `-i, --input`: Input RPU file(s) to convert (required)
- `-o, --output`: Output HDR10+ JSON file (required)
- `--target-display-max-luminance`: Target system display maximum luminance in nits (0 = use source)
- `--peak-brightness-source`: Peak brightness source for HDR10+ metadata (max, average)
- `--high-precision-mode`: Enable high precision mode for low-nit content
- `--scene-detection-threshold`: Scene detection threshold for grouping frames (0.0-1.0)
- `--max-scenes`: Maximum number of scenes to process (0 = no limit)
- `--validate-output`: Validate output against HDR10+ schema
- `-v, --verbose`: Enable verbose output

## API Usage

### Basic Conversion

```rust
use dovi_tool::dovi::hdr10plus_converter::{Hdr10PlusConverter, Hdr10PlusConverterConfig};
use dolby_vision::rpu::dovi_rpu::DoviRpu;

// Create converter configuration
let config = Hdr10PlusConverterConfig {
    high_precision_mode: true,
    scene_detection_threshold: 0.1,
    ..Default::default()
};

let converter = Hdr10PlusConverter::new(config);

// Convert single RPU
let rpu = DoviRpu::parse_unspec62_nalu(&rpu_data)?;
let hdr10plus_metadata = converter.convert_single_rpu(&rpu)?;

// Convert multiple RPUs
let rpus = vec![rpu1, rpu2, rpu3];
let hdr10plus_metadata = converter.convert_multiple_rpus(&rpus)?;
```

### File-based Conversion

```rust
// Convert single file
converter.convert_file_to_file("input.rpu", "output.json")?;

// Convert multiple files
let input_files = vec!["rpu1.bin", "rpu2.bin", "rpu3.bin"];
converter.convert_files_to_file(&input_files, "output.json")?;
```

## Configuration Options

### Hdr10PlusConverterConfig

- `target_display_max_luminance`: Target system display maximum luminance (None = use source)
- `peak_brightness_source`: Peak brightness source (Max, Average)
- `high_precision_mode`: Enable high precision mode for low-nit content
- `scene_detection_threshold`: Luminance change threshold for scene detection (0.0-1.0)
- `max_scenes`: Maximum number of scenes to process (None = no limit)

## Output Format

The converter generates HDR10+ JSON metadata conforming to SMPTE ST 2094-40 with the following structure:

```json
{
  "JSONInfo": {
    "HDR10plusProfile": "A",
    "Version": "1.0"
  },
  "SceneInfo": [
    {
      "SceneId": 0,
      "SceneFrameIndex": 0,
      "SequenceFrameIndex": 0,
      "NumberOfWindows": 1,
      "TargetedSystemDisplayMaximumLuminance": 0,
      "LuminanceParameters": {
        "AverageRGB": 1000,
        "MaxScl": [10000, 10000, 10000],
        "LuminanceDistributions": {
          "DistributionIndex": [1, 5, 10, 25, 50, 75, 90, 95, 99],
          "DistributionValues": [100, 500, 1000, 2500, 5000, 7500, 9000, 9500, 9900]
        }
      }
    }
  ],
  "SceneInfoSummary": {
    "SceneFirstFrameIndex": [0],
    "SceneFrameNumbers": [1]
  },
  "ToolInfo": {
    "Tool": "dovi_tool",
    "Version": "2.3.1"
  }
}
```

## Technical Details

### Luminance Mapping

The converter extracts luminance information from Dolby Vision RPU metadata blocks:

- **Level 1**: Min, max, and average PQ values
- **Level 2**: Trim parameters for tone mapping
- **Level 5**: Active area information
- **Level 6**: Mastering display characteristics

### High Precision Mode

When enabled, the converter uses logarithmic distribution calculation for better accuracy in low-nit content:

```rust
// High precision distribution calculation
let log_min = if min_nits > 0.0 { min_nits.log10() } else { -6.0 };
let log_max = max_nits.log10();
let log_avg = avg_nits.log10();
```

### Scene Detection

Scenes are detected based on luminance changes between frames:

```rust
let luminance_change = (avg2 - avg1).abs() / avg1;
if luminance_change > threshold {
    // Start new scene
}
```

## Validation

The converter includes built-in schema validation to ensure output conforms to HDR10+ standards:

```rust
use dovi_tool::dovi::hdr10plus_schema::Hdr10PlusSchemaValidator;

let validator = Hdr10PlusSchemaValidator::new();
validator.validate(&json_value)?;
```

## Testing

The converter includes comprehensive tests:

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end conversion testing
- **Golden File Tests**: Round-trip validation with expected outputs
- **Stress Tests**: Synthetic patterns for edge case validation
- **Error Handling Tests**: Invalid input handling
- **Determinism Tests**: Consistent output across runs

Run tests with:

```bash
cargo test hdr10plus_converter
cargo test hdr10plus_golden_tests
```

## Examples

### Convert Single RPU File

```bash
dovi_tool convert-to-hdr10plus -i movie.rpu -o movie_hdr10plus.json --high-precision-mode --verbose
```

### Convert Multiple RPU Files with Scene Detection

```bash
dovi_tool convert-to-hdr10plus -i scene1.rpu scene2.rpu scene3.rpu -o output.json --scene-detection-threshold 0.15 --max-scenes 5
```

### Batch Convert with Custom Target Display

```bash
dovi_tool convert-to-hdr10plus -i *.rpu -o batch_output.json --target-display-max-luminance 1000 --peak-brightness-source average
```

## Error Handling

The converter handles various error conditions gracefully:

- **Invalid RPU Data**: Clear error messages for malformed input
- **Missing Metadata**: Uses default values when metadata blocks are missing
- **Schema Validation**: Detailed validation error reporting
- **File I/O Errors**: Proper error propagation for file operations

## Performance Considerations

- **Memory Usage**: Efficient processing of large RPU files
- **CPU Usage**: Optimized algorithms for real-time processing
- **I/O**: Minimal file system operations
- **Scalability**: Handles multiple input files efficiently

## Integration

The converter integrates seamlessly with the existing dovi_tool architecture:

- **CLI Integration**: New command added to existing command structure
- **Module Structure**: Follows established coding patterns
- **Error Handling**: Uses project's error handling conventions
- **Logging**: Integrates with existing logging system
- **Testing**: Follows project's testing standards

## Future Enhancements

Potential future improvements:

- **Advanced Tone Mapping**: More sophisticated tone mapping algorithms
- **Color Space Support**: Additional color space conversions
- **Batch Processing**: Enhanced batch processing capabilities
- **Real-time Processing**: Streaming conversion support
- **Quality Metrics**: Output quality assessment tools
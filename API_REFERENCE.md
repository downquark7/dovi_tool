# API Reference

## DolbyVisionConverter

Main converter class for converting Dolby Vision RPU metadata to HDR10+ format.

### Constructor

```python
DolbyVisionConverter(use_ml=False, model_path=None)
```

**Parameters:**
- `use_ml` (bool): Whether to use machine learning for conversion
- `model_path` (str, optional): Path to trained ML model file

### Methods

#### convert_rpu_to_hdr10plus(input_path)

Convert Dolby Vision RPU to HDR10+ metadata.

**Parameters:**
- `input_path` (str or Path): Path to input HEVC file or RPU binary

**Returns:**
- `Dict[str, Any]`: HDR10+ metadata dictionary

#### save_hdr10plus_json(metadata, output_path)

Save HDR10+ metadata to JSON file.

**Parameters:**
- `metadata` (Dict[str, Any]): HDR10+ metadata dictionary
- `output_path` (str or Path): Path to output JSON file

#### convert_and_save(input_path, output_path)

Convert RPU to HDR10+ and save to file.

**Parameters:**
- `input_path` (str or Path): Path to input HEVC file or RPU binary
- `output_path` (str or Path): Path to output JSON file

#### validate_hdr10plus_file(json_path)

Validate an existing HDR10+ JSON file.

**Parameters:**
- `json_path` (str or Path): Path to HDR10+ JSON file

**Returns:**
- `Dict[str, Any]`: Validation result dictionary

## RPUParser

Parser for Dolby Vision RPU metadata using dovi_tool.

### Constructor

```python
RPUParser(dovi_tool_path="dovi_tool")
```

**Parameters:**
- `dovi_tool_path` (str): Path to dovi_tool executable

### Methods

#### parse_rpu(input_path)

Parse Dolby Vision RPU from input file.

**Parameters:**
- `input_path` (Path): Path to input HEVC file or RPU binary

**Returns:**
- `Optional[Dict[str, Any]]`: Parsed RPU data dictionary or None if parsing fails

#### get_rpu_summary(input_path)

Get a human-readable summary of RPU data.

**Parameters:**
- `input_path` (Path): Path to input file

**Returns:**
- `Optional[str]`: Summary string or None if parsing fails

## HeuristicConverter

Heuristic-based converter for Dolby Vision RPU to HDR10+ metadata.

### Constructor

```python
HeuristicConverter()
```

### Methods

#### convert(rpu_data)

Convert Dolby Vision RPU data to HDR10+ metadata using heuristics.

**Parameters:**
- `rpu_data` (Dict[str, Any]): Parsed RPU data from RPUParser

**Returns:**
- `Dict[str, Any]`: HDR10+ metadata dictionary

#### apply_scene_analysis(rpu_data, hdr10plus_metadata)

Apply scene analysis to improve HDR10+ metadata.

**Parameters:**
- `rpu_data` (Dict[str, Any]): Original RPU data
- `hdr10plus_metadata` (Dict[str, Any]): Current HDR10+ metadata

**Returns:**
- `Dict[str, Any]`: Enhanced HDR10+ metadata with scene analysis

## MLConverter

Machine learning-based converter for Dolby Vision RPU to HDR10+ metadata.

### Constructor

```python
MLConverter(model_path=None)
```

**Parameters:**
- `model_path` (str, optional): Path to pre-trained model file

### Methods

#### convert(rpu_data)

Convert Dolby Vision RPU data to HDR10+ metadata using ML models.

**Parameters:**
- `rpu_data` (Dict[str, Any]): Parsed RPU data from RPUParser

**Returns:**
- `Dict[str, Any]`: HDR10+ metadata dictionary

#### train(training_data, validation_data=None)

Train the ML models on provided data.

**Parameters:**
- `training_data` (List[Dict[str, Any]]): List of training examples
- `validation_data` (List[Dict[str, Any]], optional): Optional validation data

**Returns:**
- `Dict[str, Any]`: Training results dictionary

#### save_model(model_path)

Save trained models to file.

**Parameters:**
- `model_path` (str): Path to save model file

#### load_model(model_path)

Load trained models from file.

**Parameters:**
- `model_path` (str): Path to model file

#### generate_synthetic_training_data(num_samples=1000)

Generate synthetic training data for model training.

**Parameters:**
- `num_samples` (int): Number of synthetic examples to generate

**Returns:**
- `List[Dict[str, Any]]`: List of synthetic training examples

## HDR10PlusAnalyzer

Analyzer for HDR10+ metadata structure and content.

### Constructor

```python
HDR10PlusAnalyzer()
```

### Methods

#### analyze_metadata(metadata)

Analyze HDR10+ metadata and provide insights.

**Parameters:**
- `metadata` (Dict[str, Any]): HDR10+ metadata dictionary

**Returns:**
- `Dict[str, Any]`: Analysis results dictionary

#### compare_with_standard(metadata, standard="bt2020")

Compare metadata with standard color spaces.

**Parameters:**
- `metadata` (Dict[str, Any]): HDR10+ metadata dictionary
- `standard` (str): Standard to compare against ("bt2020", "bt709", "dci_p3")

**Returns:**
- `Dict[str, Any]`: Comparison results dictionary

## HDR10PlusJSONGenerator

Generator for HDR10+ JSON metadata files.

### Constructor

```python
HDR10PlusJSONGenerator()
```

### Methods

#### generate_json(hdr10plus_data)

Generate HDR10+ JSON metadata structure.

**Parameters:**
- `hdr10plus_data` (Dict[str, Any]): HDR10+ metadata dictionary

**Returns:**
- `Dict[str, Any]`: Complete HDR10+ JSON metadata structure

#### generate_example_json()

Generate an example HDR10+ JSON metadata file.

**Returns:**
- `Dict[str, Any]`: Example HDR10+ metadata dictionary

#### save_json_file(json_metadata, output_path)

Save HDR10+ JSON metadata to file.

**Parameters:**
- `json_metadata` (Dict[str, Any]): HDR10+ JSON metadata dictionary
- `output_path` (Path): Path to output JSON file

## MetadataValidator

Validator for HDR10+ metadata files.

### Constructor

```python
MetadataValidator()
```

### Methods

#### validate_hdr10plus(metadata)

Validate HDR10+ metadata.

**Parameters:**
- `metadata` (Dict[str, Any]): HDR10+ metadata dictionary

**Returns:**
- `Dict[str, Any]`: Validation result dictionary

#### validate_json_file(json_path)

Validate HDR10+ JSON file.

**Parameters:**
- `json_path` (Path): Path to JSON file

**Returns:**
- `Dict[str, Any]`: Validation result dictionary

#### compare_with_standard(metadata, standard="bt2020")

Compare metadata with a standard specification.

**Parameters:**
- `metadata` (Dict[str, Any]): HDR10+ metadata dictionary
- `standard` (str): Standard to compare against

**Returns:**
- `Dict[str, Any]`: Comparison result dictionary

## Data Structures

### RPU Data Structure

```python
{
    "source": "dolby_vision_rpu",
    "version": "1.0",
    "profile": {...},
    "level": {...},
    "mastering_display": {
        "primaries": {
            "red": [float, float],
            "green": [float, float],
            "blue": [float, float],
            "white": [float, float]
        },
        "luminance": {
            "min": float,
            "max": float
        }
    },
    "content_light_level": {
        "max_cll": int,
        "max_fall": float,
        "average_cll": float
    },
    "tone_mapping": {
        "trim_slopes": [float, float, float],
        "trim_offsets": [float, float, float],
        "trim_power": [float, float, float],
        "trim_chroma_weight": [float, float, float],
        "trim_saturation_gain": [float, float, float]
    },
    "scene_info": {
        "scene_refresh_flag": bool,
        "scene_change_detection": [int, ...],
        "frame_count": int
    },
    "color_volume": {
        "color_primaries": str,
        "transfer_characteristics": str,
        "matrix_coefficients": str
    }
}
```

### HDR10+ Metadata Structure

```python
{
    "MaxCLL": int,
    "MaxFALL": float,
    "MasteringDisplay": {
        "Primaries": {
            "Red": [float, float],
            "Green": [float, float],
            "Blue": [float, float],
            "White": [float, float]
        },
        "Luminance": {
            "Min": float,
            "Max": float
        }
    },
    "TargetedSystemDisplayMaximumLuminance": int,  # Optional
    "TargetedSystemDisplayMinimumLuminance": float,  # Optional
    "MaxRGB": float,  # Optional
    "MaxRGBTF": float,  # Optional
    "MinRGB": float,  # Optional
    "MinRGBTF": float,  # Optional
    "ToneMappingCurves": {...},  # Optional
    "SceneAnalysis": {...},  # Optional
    "source": str,  # Metadata
    "conversion_method": str,  # Metadata
    "generation_timestamp": str,  # Metadata
    "prediction_confidence": {...},  # Metadata (ML only)
    "validation_status": {...}  # Metadata
}
```

### Validation Result Structure

```python
{
    "valid": bool,
    "warnings": [str, ...],
    "errors": [str, ...],
    "recommendations": [str, ...],
    "compliance_score": float,  # 0.0 to 1.0
    "statistics": {...}
}
```
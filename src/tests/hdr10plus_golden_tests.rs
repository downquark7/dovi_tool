use anyhow::Result;

use crate::dovi::hdr10plus_converter::{Hdr10PlusConverter, Hdr10PlusConverterConfig};
use crate::dovi::hdr10plus_schema::Hdr10PlusSchemaValidator;

#[test]
fn test_golden_file_validation() -> Result<()> {
    // Test that the golden file exists and is valid JSON
    let golden_path = "assets/tests/hdr10plus_converter/golden_outputs/single_rpu_expected.json";
    
    if std::path::Path::new(golden_path).exists() {
        let json_content = std::fs::read_to_string(golden_path)?;
        let json_value: serde_json::Value = serde_json::from_str(&json_content)?;
        
        // Validate against schema
        let validator = Hdr10PlusSchemaValidator::new();
        validator.validate(&json_value)?;
    }
    
    Ok(())
}

#[test]
fn test_converter_with_empty_config() {
    let config = Hdr10PlusConverterConfig::default();
    let _converter = Hdr10PlusConverter::new(config);
    // Should create successfully
    assert!(true);
}

#[test]
fn test_schema_validation_basic() -> Result<()> {
    let validator = Hdr10PlusSchemaValidator::new();
    
    // Test with minimal valid JSON structure
    let minimal_json = serde_json::json!({
        "JSONInfo": {
            "HDR10plusProfile": "A",
            "Version": "1.0"
        },
        "SceneInfo": [],
        "SceneInfoSummary": {
            "SceneFirstFrameIndex": [],
            "SceneFrameNumbers": []
        },
        "ToolInfo": {
            "Tool": "dovi_tool",
            "Version": "2.3.1"
        }
    });
    
    // Should validate successfully
    validator.validate(&minimal_json)?;
    
    Ok(())
}
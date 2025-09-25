use anyhow::{Result, anyhow};
use serde_json::{Value, Map};
use std::collections::HashSet;

/// HDR10+ JSON schema validator based on SMPTE ST 2094-40
pub struct Hdr10PlusSchemaValidator {
    required_fields: HashSet<String>,
    optional_fields: HashSet<String>,
}

impl Hdr10PlusSchemaValidator {
    pub fn new() -> Self {
        let mut required_fields = HashSet::new();
        required_fields.insert("JSONInfo".to_string());
        required_fields.insert("SceneInfo".to_string());
        required_fields.insert("SceneInfoSummary".to_string());
        required_fields.insert("ToolInfo".to_string());

        let mut optional_fields = HashSet::new();
        optional_fields.insert("MasteringDisplayColorVolume".to_string());
        optional_fields.insert("ContentLightLevel".to_string());

        Self {
            required_fields,
            optional_fields,
        }
    }

    /// Validate HDR10+ JSON metadata against the schema
    pub fn validate(&self, json: &Value) -> Result<()> {
        let obj = json.as_object().ok_or_else(|| {
            anyhow::anyhow!("Root must be a JSON object")
        })?;

        // Check required fields
        for field in &self.required_fields {
            if !obj.contains_key(field) {
                return Err(anyhow::anyhow!("Missing required field: {}", field));
            }
        }

        // Validate JSONInfo
        self.validate_json_info(obj.get("JSONInfo").unwrap())?;

        // Validate SceneInfo
        self.validate_scene_info(obj.get("SceneInfo").unwrap())?;

        // Validate SceneInfoSummary
        self.validate_scene_info_summary(obj.get("SceneInfoSummary").unwrap())?;

        // Validate ToolInfo
        self.validate_tool_info(obj.get("ToolInfo").unwrap())?;

        // Validate optional fields if present
        if let Some(mdcv) = obj.get("MasteringDisplayColorVolume") {
            self.validate_mastering_display_color_volume(mdcv)?;
        }

        if let Some(cll) = obj.get("ContentLightLevel") {
            self.validate_content_light_level(cll)?;
        }

        Ok(())
    }

    fn validate_json_info(&self, json_info: &Value) -> Result<()> {
        let obj = json_info.as_object().ok_or_else(|| {
            anyhow::anyhow!("JSONInfo must be an object")
        })?;

        // Check required fields
        let hdr10plus_profile = obj.get("HDR10plusProfile")
            .and_then(|v| v.as_str())
            .ok_or_else(|| anyhow::anyhow!("JSONInfo.HDR10plusProfile is required"))?;

        if hdr10plus_profile != "A" {
            return Err(anyhow::anyhow!("JSONInfo.HDR10plusProfile must be 'A'"));
        }

        let version = obj.get("Version")
            .and_then(|v| v.as_str())
            .ok_or_else(|| anyhow::anyhow!("JSONInfo.Version is required"))?;

        if !version.starts_with("1.") {
            return Err(anyhow::anyhow!("JSONInfo.Version must start with '1.'"));
        }

        Ok(())
    }

    fn validate_scene_info(&self, scene_info: &Value) -> Result<()> {
        let array = scene_info.as_array().ok_or_else(|| {
            anyhow::anyhow!("SceneInfo must be an array")
        })?;

        // Allow empty SceneInfo arrays for minimal valid JSON
        // if array.is_empty() {
        //     return Err(anyhow::anyhow!("SceneInfo cannot be empty"));
        // }

        for (i, scene) in array.iter().enumerate() {
            self.validate_scene_info_item(scene, i)?;
        }

        Ok(())
    }

    fn validate_scene_info_item(&self, scene: &Value, index: usize) -> Result<()> {
        let obj = scene.as_object().ok_or_else(|| {
            anyhow::anyhow!("SceneInfo[{}] must be an object", index)
        })?;

        // Check required fields
        let required_scene_fields = [
            "SceneId", "SceneFrameIndex", "SequenceFrameIndex",
            "NumberOfWindows", "TargetedSystemDisplayMaximumLuminance",
            "LuminanceParameters"
        ];

        for field in &required_scene_fields {
            if !obj.contains_key(*field) {
                return Err(anyhow::anyhow!("SceneInfo[{}] missing required field: {}", index, field));
            }
        }

        // Validate LuminanceParameters
        self.validate_luminance_parameters(obj.get("LuminanceParameters").unwrap(), index)?;

        // Validate numeric fields
        self.validate_uint_field(obj, "SceneId", 0, u32::MAX as u64, index)?;
        self.validate_uint_field(obj, "SceneFrameIndex", 0, u32::MAX as u64, index)?;
        self.validate_uint_field(obj, "SequenceFrameIndex", 0, u32::MAX as u64, index)?;
        self.validate_uint_field(obj, "NumberOfWindows", 1, 1, index)?; // Must be 1
        self.validate_uint_field(obj, "TargetedSystemDisplayMaximumLuminance", 0, 10000, index)?;

        Ok(())
    }

    fn validate_luminance_parameters(&self, lum_params: &Value, scene_index: usize) -> Result<()> {
        let obj = lum_params.as_object().ok_or_else(|| {
            anyhow::anyhow!("SceneInfo[{}].LuminanceParameters must be an object", scene_index)
        })?;

        // Check required fields
        let required_lum_fields = [
            "AverageRGB", "MaxScl", "LuminanceDistributions"
        ];

        for field in &required_lum_fields {
            if !obj.contains_key(*field) {
                return Err(anyhow::anyhow!("SceneInfo[{}].LuminanceParameters missing required field: {}", scene_index, field));
            }
        }

        // Validate AverageRGB
        let avg_rgb = obj.get("AverageRGB")
            .and_then(|v| v.as_u64())
            .ok_or_else(|| anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.AverageRGB must be a number", scene_index))?;

        if avg_rgb > 100000 {
            return Err(anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.AverageRGB must be <= 100000", scene_index));
        }

        // Validate MaxScl
        self.validate_max_scl(obj.get("MaxScl").unwrap(), scene_index)?;

        // Validate LuminanceDistributions
        self.validate_luminance_distributions(obj.get("LuminanceDistributions").unwrap(), scene_index)?;

        Ok(())
    }

    fn validate_max_scl(&self, max_scl: &Value, scene_index: usize) -> Result<()> {
        let array = max_scl.as_array().ok_or_else(|| {
            anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.MaxScl must be an array", scene_index)
        })?;

        if array.len() != 3 {
            return Err(anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.MaxScl must have exactly 3 elements", scene_index));
        }

        for (i, value) in array.iter().enumerate() {
            let val = value.as_u64().ok_or_else(|| {
                anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.MaxScl[{}] must be a number", scene_index, i)
            })?;

            if val == 0 || val > 100000 {
                return Err(anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.MaxScl[{}] must be > 0 and <= 100000", scene_index, i));
            }
        }

        Ok(())
    }

    fn validate_luminance_distributions(&self, distributions: &Value, scene_index: usize) -> Result<()> {
        let obj = distributions.as_object().ok_or_else(|| {
            anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.LuminanceDistributions must be an object", scene_index)
        })?;

        // Check required fields
        let required_dist_fields = ["DistributionIndex", "DistributionValues"];

        for field in &required_dist_fields {
            if !obj.contains_key(*field) {
                return Err(anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.LuminanceDistributions missing required field: {}", scene_index, field));
            }
        }

        // Validate DistributionIndex
        let dist_index = obj.get("DistributionIndex")
            .and_then(|v| v.as_array())
            .ok_or_else(|| anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.LuminanceDistributions.DistributionIndex must be an array", scene_index))?;

        if dist_index.len() != 9 {
            return Err(anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.LuminanceDistributions.DistributionIndex must have exactly 9 elements", scene_index));
        }

        let expected_percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99];
        for (i, value) in dist_index.iter().enumerate() {
            let val = value.as_u64().ok_or_else(|| {
                anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.LuminanceDistributions.DistributionIndex[{}] must be a number", scene_index, i)
            })?;

            if val != expected_percentiles[i] as u64 {
                return Err(anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.LuminanceDistributions.DistributionIndex[{}] must be {}", scene_index, i, expected_percentiles[i]));
            }
        }

        // Validate DistributionValues
        let dist_values = obj.get("DistributionValues")
            .and_then(|v| v.as_array())
            .ok_or_else(|| anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.LuminanceDistributions.DistributionValues must be an array", scene_index))?;

        if dist_values.len() != 9 {
            return Err(anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.LuminanceDistributions.DistributionValues must have exactly 9 elements", scene_index));
        }

        for (i, value) in dist_values.iter().enumerate() {
            let val = value.as_u64().ok_or_else(|| {
                anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.LuminanceDistributions.DistributionValues[{}] must be a number", scene_index, i)
            })?;

            if val > 100000 {
                return Err(anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.LuminanceDistributions.DistributionValues[{}] must be <= 100000", scene_index, i));
            }
        }

        // Validate that distribution values are in ascending order
        for i in 1..dist_values.len() {
            let prev = dist_values[i-1].as_u64().unwrap();
            let curr = dist_values[i].as_u64().unwrap();
            if curr < prev {
                return Err(anyhow::anyhow!("SceneInfo[{}].LuminanceParameters.LuminanceDistributions.DistributionValues must be in ascending order", scene_index));
            }
        }

        Ok(())
    }

    fn validate_scene_info_summary(&self, summary: &Value) -> Result<()> {
        let obj = summary.as_object().ok_or_else(|| {
            anyhow::anyhow!("SceneInfoSummary must be an object")
        })?;

        // Check required fields
        let required_summary_fields = ["SceneFirstFrameIndex", "SceneFrameNumbers"];

        for field in &required_summary_fields {
            if !obj.contains_key(*field) {
                return Err(anyhow::anyhow!("SceneInfoSummary missing required field: {}", field));
            }
        }

        // Validate arrays have same length
        let first_frames = obj.get("SceneFirstFrameIndex")
            .and_then(|v| v.as_array())
            .ok_or_else(|| anyhow::anyhow!("SceneInfoSummary.SceneFirstFrameIndex must be an array"))?;

        let frame_numbers = obj.get("SceneFrameNumbers")
            .and_then(|v| v.as_array())
            .ok_or_else(|| anyhow::anyhow!("SceneInfoSummary.SceneFrameNumbers must be an array"))?;

        if first_frames.len() != frame_numbers.len() {
            return Err(anyhow::anyhow!("SceneInfoSummary.SceneFirstFrameIndex and SceneFrameNumbers must have the same length"));
        }

        // Validate array elements
        for (i, value) in first_frames.iter().enumerate() {
            let val = value.as_u64().ok_or_else(|| {
                anyhow::anyhow!("SceneInfoSummary.SceneFirstFrameIndex[{}] must be a number", i)
            })?;

            if val > u32::MAX as u64 {
                return Err(anyhow::anyhow!("SceneInfoSummary.SceneFirstFrameIndex[{}] must be <= {}", i, u32::MAX));
            }
        }

        for (i, value) in frame_numbers.iter().enumerate() {
            let val = value.as_u64().ok_or_else(|| {
                anyhow::anyhow!("SceneInfoSummary.SceneFrameNumbers[{}] must be a number", i)
            })?;

            if val == 0 || val > u32::MAX as u64 {
                return Err(anyhow::anyhow!("SceneInfoSummary.SceneFrameNumbers[{}] must be > 0 and <= {}", i, u32::MAX));
            }
        }

        Ok(())
    }

    fn validate_tool_info(&self, tool_info: &Value) -> Result<()> {
        let obj = tool_info.as_object().ok_or_else(|| {
            anyhow::anyhow!("ToolInfo must be an object")
        })?;

        // Check required fields
        let required_tool_fields = ["Tool", "Version"];

        for field in &required_tool_fields {
            if !obj.contains_key(*field) {
                return Err(anyhow::anyhow!("ToolInfo missing required field: {}", field));
            }
        }

        // Validate string fields
        let tool = obj.get("Tool")
            .and_then(|v| v.as_str())
            .ok_or_else(|| anyhow::anyhow!("ToolInfo.Tool must be a string"))?;

        if tool.is_empty() {
            return Err(anyhow::anyhow!("ToolInfo.Tool cannot be empty"));
        }

        let version = obj.get("Version")
            .and_then(|v| v.as_str())
            .ok_or_else(|| anyhow::anyhow!("ToolInfo.Version must be a string"))?;

        if version.is_empty() {
            return Err(anyhow::anyhow!("ToolInfo.Version cannot be empty"));
        }

        Ok(())
    }

    fn validate_mastering_display_color_volume(&self, mdcv: &Value) -> Result<()> {
        let obj = mdcv.as_object().ok_or_else(|| {
            anyhow::anyhow!("MasteringDisplayColorVolume must be an object")
        })?;

        // Validate required fields for MasteringDisplayColorVolume
        let required_mdcv_fields = [
            "MasteringDisplayPrimariesX", "MasteringDisplayPrimariesY",
            "MasteringDisplayWhitePointX", "MasteringDisplayWhitePointY",
            "MasteringDisplayMaxLuminance", "MasteringDisplayMinLuminance"
        ];

        for field in &required_mdcv_fields {
            if !obj.contains_key(*field) {
                return Err(anyhow::anyhow!("MasteringDisplayColorVolume missing required field: {}", field));
            }
        }

        Ok(())
    }

    fn validate_content_light_level(&self, cll: &Value) -> Result<()> {
        let obj = cll.as_object().ok_or_else(|| {
            anyhow::anyhow!("ContentLightLevel must be an object")
        })?;

        // Validate required fields for ContentLightLevel
        let required_cll_fields = ["MaxContentLightLevel", "MaxFrameAverageLightLevel"];

        for field in &required_cll_fields {
            if !obj.contains_key(*field) {
                return Err(anyhow::anyhow!("ContentLightLevel missing required field: {}", field));
            }
        }

        Ok(())
    }

    fn validate_uint_field(&self, obj: &Map<String, Value>, field: &str, min: u64, max: u64, scene_index: usize) -> Result<()> {
        let value = obj.get(field)
            .and_then(|v| v.as_u64())
            .ok_or_else(|| anyhow::anyhow!("SceneInfo[{}].{} must be a number", scene_index, field))?;

        if value < min || value > max {
            return Err(anyhow::anyhow!("SceneInfo[{}].{} must be between {} and {}", scene_index, field, min, max));
        }

        Ok(())
    }
}

impl Default for Hdr10PlusSchemaValidator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_valid_hdr10plus_metadata() {
        let validator = Hdr10PlusSchemaValidator::new();
        
        let valid_metadata = json!({
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
                "Version": "1.0.0"
            }
        });

        assert!(validator.validate(&valid_metadata).is_ok());
    }

    #[test]
    fn test_invalid_missing_required_field() {
        let validator = Hdr10PlusSchemaValidator::new();
        
        let invalid_metadata = json!({
            "JSONInfo": {
                "HDR10plusProfile": "A",
                "Version": "1.0"
            },
            "SceneInfo": [],
            "SceneInfoSummary": {
                "SceneFirstFrameIndex": [],
                "SceneFrameNumbers": []
            }
            // Missing ToolInfo
        });

        assert!(validator.validate(&invalid_metadata).is_err());
    }

    #[test]
    fn test_invalid_distribution_values_order() {
        let validator = Hdr10PlusSchemaValidator::new();
        
        let invalid_metadata = json!({
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
                            "DistributionValues": [1000, 500, 1000, 2500, 5000, 7500, 9000, 9500, 9900] // Not ascending
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
                "Version": "1.0.0"
            }
        });

        assert!(validator.validate(&invalid_metadata).is_err());
    }
}
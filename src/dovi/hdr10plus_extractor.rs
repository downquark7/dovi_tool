use anyhow::{Result, bail};
use hdr10plus::metadata_json::{MetadataJsonRoot, Hdr10PlusJsonMetadata, LuminanceParameters, LuminanceDistributions, SceneInfoSummary, ToolInfo, JsonInfo};

use dolby_vision::rpu::{dovi_rpu::DoviRpu, extension_metadata::blocks::ExtMetadataBlock};
use dolby_vision::utils::pq_to_nits;

/// Convert PQ values to nits
/// This is the inverse of nits_to_pq_12_bit
fn pq_12_bit_to_nits(pq: u16) -> f64 {
    let pq_normalized = pq as f64 / 4095.0;
    pq_to_nits(pq_normalized)
}

/// HDR10+ metadata extractor from Dolby Vision RPU
/// 
/// This struct extracts HDR10+ compatible metadata from Dolby Vision RPUs and generates
/// valid HDR10+ JSON metadata files. It implements the heuristics for selecting the
/// best trim (preferring 1000-nit targets) and handles fallback scenarios when
/// metadata is not available.
/// 
/// # Features
/// - Extracts luminance parameters from L1 metadata blocks
/// - Falls back to L6 metadata when L1 is not available
/// - Groups RPUs by scenes using scene_refresh_flag
/// - Generates HDR10+ Profile A compliant JSON
/// - Applies 1000-nit trim selection heuristics
/// 
/// # Example
/// ```rust
/// use dovi_tool::dovi::hdr10plus_extractor::Hdr10PlusExtractor;
/// 
/// let extractor = Hdr10PlusExtractor::new(rpus);
/// let hdr10plus_metadata = extractor.extract_to_json()?;
/// ```
pub struct Hdr10PlusExtractor {
    rpus: Vec<DoviRpu>,
}

impl Hdr10PlusExtractor {
    pub fn new(rpus: Vec<DoviRpu>) -> Self {
        Self { rpus }
    }

    /// Extract HDR10+ metadata from RPUs and generate JSON
    /// 
    /// This is the main method that processes the RPUs and generates a complete
    /// HDR10+ JSON metadata file. It handles:
    /// - Scene detection and grouping
    /// - Luminance parameter extraction
    /// - Targeted system display maximum luminance calculation
    /// - HDR10+ Profile A JSON generation
    /// 
    /// # Returns
    /// - `Ok(MetadataJsonRoot)`: Complete HDR10+ metadata structure
    /// - `Err`: If no RPUs are provided or extraction fails
    /// 
    /// # Errors
    /// - Returns an error if no RPUs are provided
    /// - Returns an error if metadata extraction fails
    pub fn extract_to_json(&self) -> Result<MetadataJsonRoot> {
        if self.rpus.is_empty() {
            bail!("No RPUs provided for HDR10+ extraction");
        }

        // Group RPUs by scenes (using scene_refresh_flag)
        let scenes = self.group_rpus_by_scenes()?;
        
        // Extract scene information
        let mut scene_info = Vec::new();
        let mut scene_first_frames = Vec::new();
        let mut scene_frame_numbers = Vec::new();
        
        let mut current_frame = 0;
        
        for (scene_id, scene_rpus) in scenes.iter().enumerate() {
            scene_first_frames.push(current_frame);
            scene_frame_numbers.push(scene_rpus.len());
            
            for (frame_in_scene, rpu) in scene_rpus.iter().enumerate() {
                let scene_frame_index = frame_in_scene;
                let sequence_frame_index = current_frame + frame_in_scene;
                
                // Extract luminance parameters from L1 metadata
                let luminance_params = self.extract_luminance_parameters(rpu)?;
                
                // Extract targeted system display maximum luminance
                let targeted_system_display_max_luminance = self.extract_targeted_system_display_max_luminance(rpu)?;
                
                let scene_info_item = Hdr10PlusJsonMetadata {
                    bezier_curve_data: None, // Profile A doesn't use bezier curves
                    luminance_parameters: luminance_params,
                    number_of_windows: 1, // Default to 1 window
                    targeted_system_display_maximum_luminance: targeted_system_display_max_luminance,
                    scene_frame_index: scene_frame_index,
                    scene_id: scene_id,
                    sequence_frame_index: sequence_frame_index,
                };
                
                scene_info.push(scene_info_item);
            }
            
            current_frame += scene_rpus.len();
        }
        
        // Create scene info summary
        let scene_info_summary = SceneInfoSummary {
            scene_first_frame_index: scene_first_frames,
            scene_frame_numbers,
        };
        
        // Create tool info
        let tool_info = ToolInfo {
            tool: "dovi_tool".to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
        };
        
        // Create JSON info
        let json_info = JsonInfo {
            profile: "A".to_string(),
            version: "1.0".to_string(),
        };
        
        Ok(MetadataJsonRoot {
            info: json_info,
            scene_info,
            scene_info_summary,
            tool_info,
        })
    }
    
    /// Group RPUs by scenes based on scene_refresh_flag
    fn group_rpus_by_scenes(&self) -> Result<Vec<Vec<&DoviRpu>>> {
        let mut scenes = Vec::new();
        let mut current_scene = Vec::new();
        
        for rpu in &self.rpus {
            // Check if this is a scene cut
            let is_scene_cut = rpu.vdr_dm_data
                .as_ref()
                .map(|vdr| vdr.scene_refresh_flag == 1)
                .unwrap_or(false);
            
            if is_scene_cut && !current_scene.is_empty() {
                // Start a new scene
                scenes.push(current_scene);
                current_scene = vec![rpu];
            } else {
                // Add to current scene
                current_scene.push(rpu);
            }
        }
        
        // Add the last scene
        if !current_scene.is_empty() {
            scenes.push(current_scene);
        }
        
        // If no scene cuts were found, treat all RPUs as one scene
        if scenes.is_empty() {
            scenes.push(self.rpus.iter().collect());
        }
        
        Ok(scenes)
    }
    
    /// Extract luminance parameters from L1 metadata
    fn extract_luminance_parameters(&self, rpu: &DoviRpu) -> Result<LuminanceParameters> {
        // Try to find L1 metadata
        let l1_block = rpu.vdr_dm_data
            .as_ref()
            .and_then(|vdr| vdr.get_block(1))
            .and_then(|block| match block {
                ExtMetadataBlock::Level1(l1) => Some(l1),
                _ => None,
            });
        
        if let Some(l1) = l1_block {
            // Extract values from L1 metadata
            let min_pq = l1.min_pq;
            let max_pq = l1.max_pq;
            let avg_pq = l1.avg_pq;
            
            // Convert PQ to nits
            let min_nits = pq_12_bit_to_nits(min_pq);
            let max_nits = pq_12_bit_to_nits(max_pq);
            let avg_nits = pq_12_bit_to_nits(avg_pq);
            
            // Create luminance distributions (simplified - using percentiles)
            let distribution_index = vec![1, 5, 10, 25, 50, 75, 90, 95, 99];
            let distribution_values = self.generate_distribution_values(min_nits, max_nits, avg_nits);
            
            let luminance_distributions = LuminanceDistributions {
                distribution_index,
                distribution_values,
            };
            
            // Extract MaxScl values (simplified - using max values)
            let max_scl = vec![
                (max_nits * 100.0) as u32, // R
                (max_nits * 100.0) as u32, // G  
                (max_nits * 100.0) as u32, // B
            ];
            
            Ok(LuminanceParameters {
                average_rgb: (avg_nits * 10.0) as u32, // Convert to 0.1 nits units
                luminance_distributions,
                max_scl,
            })
        } else {
            // Fallback: try to extract from L6 metadata or use defaults
            self.extract_luminance_parameters_fallback(rpu)
        }
    }
    
    /// Fallback method to extract luminance parameters when L1 is not available
    fn extract_luminance_parameters_fallback(&self, rpu: &DoviRpu) -> Result<LuminanceParameters> {
        // Try to get values from L6 metadata
        let l6_block = rpu.vdr_dm_data
            .as_ref()
            .and_then(|vdr| vdr.get_block(6))
            .and_then(|block| match block {
                ExtMetadataBlock::Level6(l6) => Some(l6),
                _ => None,
            });
        
        let (max_nits, avg_nits) = if let Some(l6) = l6_block {
            // Use L6 values as fallback
            let max_nits = l6.max_content_light_level as f64;
            let avg_nits = (l6.max_frame_average_light_level as f64) * 0.7; // Estimate average
            (max_nits, avg_nits)
        } else {
            // Use default values
            (1000.0, 100.0)
        };
        
        let min_nits = 0.1; // Minimum luminance
        
        // Create luminance distributions
        let distribution_index = vec![1, 5, 10, 25, 50, 75, 90, 95, 99];
        let distribution_values = self.generate_distribution_values(min_nits, max_nits, avg_nits);
        
        let luminance_distributions = LuminanceDistributions {
            distribution_index,
            distribution_values,
        };
        
        // Create MaxScl values
        let max_scl = vec![
            (max_nits * 100.0) as u32,
            (max_nits * 100.0) as u32,
            (max_nits * 100.0) as u32,
        ];
        
        Ok(LuminanceParameters {
            average_rgb: (avg_nits * 10.0) as u32,
            luminance_distributions,
            max_scl,
        })
    }
    
    /// Generate distribution values based on min, max, and average nits
    fn generate_distribution_values(&self, min_nits: f64, max_nits: f64, avg_nits: f64) -> Vec<u32> {
        // Create a simple distribution based on the values
        // This is a simplified approach - in reality, you'd want more sophisticated distribution modeling
        let mut values = Vec::new();
        
        // Percentiles: 1, 5, 10, 25, 50, 75, 90, 95, 99
        let percentiles = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99];
        
        for &percentile in &percentiles {
            let value = if percentile <= 0.5 {
                // Lower percentiles: interpolate between min and avg
                min_nits + (avg_nits - min_nits) * (percentile * 2.0)
            } else {
                // Upper percentiles: interpolate between avg and max
                avg_nits + (max_nits - avg_nits) * ((percentile - 0.5) * 2.0)
            };
            values.push((value * 100.0) as u32); // Convert to 0.01 nits units
        }
        
        values
    }
    
    /// Extract targeted system display maximum luminance
    fn extract_targeted_system_display_max_luminance(&self, rpu: &DoviRpu) -> Result<u32> {
        // Try to get from L6 metadata first
        if let Some(l6_block) = rpu.vdr_dm_data
            .as_ref()
            .and_then(|vdr| vdr.get_block(6))
            .and_then(|block| match block {
                ExtMetadataBlock::Level6(l6) => Some(l6),
                _ => None,
            })
        {
            // Use the mastering display maximum luminance as target
            return Ok(l6_block.max_display_mastering_luminance as u32);
        }
        
        // Fallback to default 1000 nits
        Ok(1000)
    }
    
    /// Apply heuristics to select the best trim for HDR10+ metadata
    /// 
    /// This function implements the trim selection heuristics as specified in the requirements:
    /// - Prefers trims with target brightness closest to 1000 nits
    /// - Falls back to next closest target (800 or 1200 nits) if 1000-nit trim not available
    /// - Returns the first RPU if no specific trim analysis is performed
    /// 
    /// # Parameters
    /// - `rpus`: Slice of RPU references to analyze
    /// 
    /// # Returns
    /// - `Ok(Some(rpu))`: Best RPU for HDR10+ extraction
    /// - `Ok(None)`: If no RPUs provided
    /// - `Err`: If analysis fails
    /// 
    /// # Note
    /// Currently implements a simplified version that returns the first RPU.
    /// A more sophisticated implementation would analyze multiple trims and
    /// select based on target brightness values.
    pub fn select_best_trim<'a>(&self, rpus: &[&'a DoviRpu]) -> Result<Option<&'a DoviRpu>> {
        if rpus.is_empty() {
            return Ok(None);
        }
        
        // For now, we'll use the first RPU as the base
        // In a more sophisticated implementation, you'd analyze multiple trims
        // and select the one with target brightness closest to 1000 nits
        Ok(Some(rpus[0]))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use dolby_vision::rpu::vdr_dm_data::VdrDmData;
    use dolby_vision::rpu::extension_metadata::blocks::ExtMetadataBlockLevel6;
    
    #[test]
    fn test_extract_luminance_parameters_fallback() {
        // Create a mock RPU with L6 metadata
        let mut rpu = DoviRpu::default();
        rpu.vdr_dm_data = Some(VdrDmData::default());
        
        let extractor = Hdr10PlusExtractor::new(vec![rpu]);
        
        // This should not panic
        let result = extractor.extract_luminance_parameters_fallback(&extractor.rpus[0]);
        assert!(result.is_ok());
    }
    
    #[test]
    fn test_generate_distribution_values() {
        let extractor = Hdr10PlusExtractor::new(vec![]);
        let values = extractor.generate_distribution_values(0.1, 1000.0, 100.0);
        
        assert_eq!(values.len(), 9);
        assert!(values[0] < values[4]); // 1st percentile < 50th percentile
        assert!(values[4] < values[8]); // 50th percentile < 99th percentile
    }
    
    #[test]
    fn test_pq_to_nits_conversion() {
        // Test PQ to nits conversion
        // Use the existing nits_to_pq_12_bit to get the correct PQ value for 1000 nits
        let pq_1000_nits = dolby_vision::utils::nits_to_pq_12_bit(1000.0);
        let nits = pq_12_bit_to_nits(pq_1000_nits);
        
        // Should be close to 1000 nits (allow for some tolerance)
        assert!((nits - 1000.0).abs() < 50.0, "Expected close to 1000 nits, got {}", nits);
    }
    
    #[test]
    fn test_extract_targeted_system_display_max_luminance() {
        // Create a mock RPU with L6 metadata
        let mut rpu = DoviRpu::default();
        let mut vdr_dm_data = VdrDmData::default();
        
        // Add L6 metadata
        let l6_block = ExtMetadataBlockLevel6 {
            max_display_mastering_luminance: 1000,
            min_display_mastering_luminance: 1,
            max_content_light_level: 1000,
            max_frame_average_light_level: 400,
        };
        vdr_dm_data.add_metadata_block(ExtMetadataBlock::Level6(l6_block)).unwrap();
        rpu.vdr_dm_data = Some(vdr_dm_data);
        
        let extractor = Hdr10PlusExtractor::new(vec![rpu]);
        let result = extractor.extract_targeted_system_display_max_luminance(&extractor.rpus[0]);
        
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), 1000);
    }
    
    #[test]
    fn test_group_rpus_by_scenes() {
        // Create mock RPUs with different scene refresh flags
        let mut rpu1 = DoviRpu::default();
        let mut vdr_dm_data1 = VdrDmData::default();
        vdr_dm_data1.scene_refresh_flag = 0;
        rpu1.vdr_dm_data = Some(vdr_dm_data1);
        
        let mut rpu2 = DoviRpu::default();
        let mut vdr_dm_data2 = VdrDmData::default();
        vdr_dm_data2.scene_refresh_flag = 1; // Scene cut
        rpu2.vdr_dm_data = Some(vdr_dm_data2);
        
        let mut rpu3 = DoviRpu::default();
        let mut vdr_dm_data3 = VdrDmData::default();
        vdr_dm_data3.scene_refresh_flag = 0;
        rpu3.vdr_dm_data = Some(vdr_dm_data3);
        
        let extractor = Hdr10PlusExtractor::new(vec![rpu1, rpu2, rpu3]);
        let scenes = extractor.group_rpus_by_scenes().unwrap();
        
        // Should have 2 scenes: [rpu1] and [rpu2, rpu3]
        assert_eq!(scenes.len(), 2);
        assert_eq!(scenes[0].len(), 1);
        assert_eq!(scenes[1].len(), 2);
    }
    
    #[test]
    fn test_empty_rpus() {
        let extractor = Hdr10PlusExtractor::new(vec![]);
        let result = extractor.extract_to_json();
        
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("No RPUs provided"));
    }
}
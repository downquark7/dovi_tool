use anyhow::Result;
use hdr10plus::metadata::PeakBrightnessSource;
use hdr10plus::metadata_json::MetadataJsonRoot;
use std::path::Path;

use dolby_vision::rpu::dovi_rpu::DoviRpu;
use dolby_vision::rpu::extension_metadata::blocks::ExtMetadataBlock;
use dolby_vision::rpu::extension_metadata::{DmData, WithExtMetadataBlocks};

/// Convert PQ 12-bit value to nits
fn pq_12_bit_to_nits(pq: u16) -> f64 {
    let pq_normalized = pq as f64 / 4095.0;
    let linear = if pq_normalized <= 0.0 {
        0.0
    } else if pq_normalized >= 1.0 {
        10000.0
    } else {
        let numerator = pq_normalized.powf(1.0 / 78.84375) - 0.8359375;
        let denominator = 18.8515625 - 18.6875 * pq_normalized.powf(1.0 / 78.84375);
        (numerator / denominator).powf(2.0) * 10000.0
    };
    linear
}

/// Configuration for RPU to HDR10+ conversion
#[derive(Debug, Clone)]
pub struct Hdr10PlusConverterConfig {
    /// Target system display maximum luminance (0 = use source)
    pub target_display_max_luminance: Option<u16>,
    /// Peak brightness source for HDR10+ metadata
    pub peak_brightness_source: PeakBrightnessSource,
    /// Enable high precision mode for low-nit content
    pub high_precision_mode: bool,
    /// Scene detection threshold for grouping frames
    pub scene_detection_threshold: f64,
    /// Maximum number of scenes to process
    pub max_scenes: Option<usize>,
}

impl Default for Hdr10PlusConverterConfig {
    fn default() -> Self {
        Self {
            target_display_max_luminance: None,
            peak_brightness_source: PeakBrightnessSource::MaxScl,
            high_precision_mode: true,
            scene_detection_threshold: 0.1, // 10% luminance change threshold
            max_scenes: None,
        }
    }
}

/// Scene information for HDR10+ metadata
#[derive(Debug, Clone)]
struct SceneInfo {
    scene_id: u32,
    start_frame: u32,
    end_frame: u32,
    frames: Vec<FrameMetadata>,
}

/// Frame-level metadata extracted from RPU
#[derive(Debug, Clone)]
struct FrameMetadata {
    frame_index: u32,
    min_pq: u16,
    max_pq: u16,
    avg_pq: u16,
    target_max_pq: Option<u16>,
    trim_params: Option<TrimParameters>,
    active_area: Option<ActiveArea>,
    mastering_display: Option<MasteringDisplayInfo>,
}

/// Trim parameters from Level 2 metadata
#[derive(Debug, Clone)]
struct TrimParameters {
    trim_slope: u16,
    trim_offset: u16,
    trim_power: u16,
    trim_chroma_weight: u16,
    trim_saturation_gain: u16,
    ms_weight: i16,
}

/// Active area information from Level 5 metadata
#[derive(Debug, Clone)]
struct ActiveArea {
    left_offset: u16,
    right_offset: u16,
    top_offset: u16,
    bottom_offset: u16,
}

/// Mastering display information from Level 6 metadata
#[derive(Debug, Clone)]
struct MasteringDisplayInfo {
    max_display_mastering_luminance: u16,
    min_display_mastering_luminance: u16,
    max_content_light_level: u16,
    max_frame_average_light_level: u16,
}

/// Main converter for Dolby Vision RPU to HDR10+ metadata
pub struct Hdr10PlusConverter {
    config: Hdr10PlusConverterConfig,
}

impl Hdr10PlusConverter {
    /// Create a new converter with the given configuration
    pub fn new(config: Hdr10PlusConverterConfig) -> Self {
        Self { config }
    }

    /// Convert a single RPU to HDR10+ metadata
    pub fn convert_single_rpu(&self, rpu: &DoviRpu) -> Result<MetadataJsonRoot> {
        let frame_metadata = self.extract_frame_metadata(rpu)?;
        let scene_info = self.create_single_scene(frame_metadata);
        
        self.build_hdr10plus_metadata(vec![scene_info])
    }

    /// Convert multiple RPUs to HDR10+ metadata with scene detection
    pub fn convert_multiple_rpus(&self, rpus: &[DoviRpu]) -> Result<MetadataJsonRoot> {
        let mut frame_metadata = Vec::new();
        
        for (i, rpu) in rpus.iter().enumerate() {
            let metadata = self.extract_frame_metadata(rpu)?;
            frame_metadata.push((i as u32, metadata));
        }

        let scenes = self.detect_scenes(frame_metadata)?;
        self.build_hdr10plus_metadata(scenes)
    }

    /// Extract frame metadata from RPU
    fn extract_frame_metadata(&self, rpu: &DoviRpu) -> Result<FrameMetadata> {
        let mut min_pq = 0u16;
        let mut max_pq = 4095u16;
        let mut avg_pq = 2048u16;
        let mut target_max_pq = None;
        let mut trim_params = None;
        let mut active_area = None;
        let mut mastering_display = None;

        // Extract metadata from extension blocks
        if let Some(vdr_dm_data) = &rpu.vdr_dm_data {
            if let Some(DmData::V40(cmv40)) = &vdr_dm_data.cmv40_metadata {
                for block in cmv40.blocks_ref() {
                    match block {
                        ExtMetadataBlock::Level1(level1) => {
                            min_pq = level1.min_pq;
                            max_pq = level1.max_pq;
                            avg_pq = level1.avg_pq;
                        }
                        ExtMetadataBlock::Level2(level2) => {
                            target_max_pq = Some(level2.target_max_pq);
                            trim_params = Some(TrimParameters {
                                trim_slope: level2.trim_slope,
                                trim_offset: level2.trim_offset,
                                trim_power: level2.trim_power,
                                trim_chroma_weight: level2.trim_chroma_weight,
                                trim_saturation_gain: level2.trim_saturation_gain,
                                ms_weight: level2.ms_weight,
                            });
                        }
                        ExtMetadataBlock::Level5(level5) => {
                            active_area = Some(ActiveArea {
                                left_offset: level5.active_area_left_offset,
                                right_offset: level5.active_area_right_offset,
                                top_offset: level5.active_area_top_offset,
                                bottom_offset: level5.active_area_bottom_offset,
                            });
                        }
                        ExtMetadataBlock::Level6(level6) => {
                            mastering_display = Some(MasteringDisplayInfo {
                                max_display_mastering_luminance: level6.max_display_mastering_luminance,
                                min_display_mastering_luminance: level6.min_display_mastering_luminance,
                                max_content_light_level: level6.max_content_light_level,
                                max_frame_average_light_level: level6.max_frame_average_light_level,
                            });
                        }
                        _ => {} // Ignore other metadata blocks
                    }
                }
            }
        }

        Ok(FrameMetadata {
            frame_index: 0, // Will be set by caller
            min_pq,
            max_pq,
            avg_pq,
            target_max_pq,
            trim_params,
            active_area,
            mastering_display,
        })
    }

    /// Create a single scene from frame metadata
    fn create_single_scene(&self, frame_metadata: FrameMetadata) -> SceneInfo {
        SceneInfo {
            scene_id: 0,
            start_frame: 0,
            end_frame: 0,
            frames: vec![frame_metadata],
        }
    }

    /// Detect scenes based on luminance changes
    fn detect_scenes(&self, frame_metadata: Vec<(u32, FrameMetadata)>) -> Result<Vec<SceneInfo>> {
        let mut scenes = Vec::new();
        let mut current_scene = Vec::new();
        let mut scene_id = 0u32;

        for (frame_index, mut metadata) in frame_metadata {
            metadata.frame_index = frame_index;
            
            if current_scene.is_empty() {
                current_scene.push(metadata);
                continue;
            }

            // Check if this frame belongs to the current scene
            let last_frame = &current_scene.last().unwrap();
            let luminance_change = self.calculate_luminance_change(last_frame, &metadata);

            if luminance_change > self.config.scene_detection_threshold {
                // Start new scene
                if !current_scene.is_empty() {
                    scenes.push(SceneInfo {
                        scene_id,
                        start_frame: current_scene[0].frame_index,
                        end_frame: current_scene.last().unwrap().frame_index,
                        frames: current_scene,
                    });
                    scene_id += 1;
                }
                current_scene = vec![metadata];
            } else {
                current_scene.push(metadata);
            }
        }

        // Add the last scene
        if !current_scene.is_empty() {
            scenes.push(SceneInfo {
                scene_id,
                start_frame: current_scene[0].frame_index,
                end_frame: current_scene.last().unwrap().frame_index,
                frames: current_scene,
            });
        }

        // Limit number of scenes if configured
        if let Some(max_scenes) = self.config.max_scenes {
            if scenes.len() > max_scenes {
                scenes.truncate(max_scenes);
            }
        }

        Ok(scenes)
    }

    /// Calculate luminance change between two frames
    fn calculate_luminance_change(&self, frame1: &FrameMetadata, frame2: &FrameMetadata) -> f64 {
        let avg1 = pq_12_bit_to_nits(frame1.avg_pq);
        let avg2 = pq_12_bit_to_nits(frame2.avg_pq);
        
        if avg1 == 0.0 {
            return 1.0; // Maximum change if first frame is black
        }
        
        (avg2 - avg1).abs() / avg1
    }

    /// Build HDR10+ metadata from scene information
    fn build_hdr10plus_metadata(&self, scenes: Vec<SceneInfo>) -> Result<MetadataJsonRoot> {
        let mut scene_info = Vec::new();
        let mut scene_first_frame_index = Vec::new();
        let mut scene_frame_numbers = Vec::new();

        for scene in scenes {
            scene_first_frame_index.push(scene.start_frame);
            scene_frame_numbers.push((scene.end_frame - scene.start_frame + 1) as u32);

            for frame in scene.frames {
                let luminance_params = self.build_luminance_parameters(&frame)?;
                
                scene_info.push(hdr10plus::metadata_json::Hdr10PlusJsonMetadata {
                    scene_id: scene.scene_id as usize,
                    scene_frame_index: (frame.frame_index - scene.start_frame) as usize,
                    sequence_frame_index: frame.frame_index as usize,
                    number_of_windows: 1,
                    targeted_system_display_maximum_luminance: self.config.target_display_max_luminance.unwrap_or(0) as u32,
                    luminance_parameters: luminance_params,
                    bezier_curve_data: None,
                });
            }
        }

        Ok(MetadataJsonRoot {
            info: hdr10plus::metadata_json::JsonInfo {
                profile: "A".to_string(),
                version: "1.0".to_string(),
            },
            scene_info,
            scene_info_summary: hdr10plus::metadata_json::SceneInfoSummary {
                scene_first_frame_index: scene_first_frame_index.into_iter().map(|x| x as usize).collect(),
                scene_frame_numbers: scene_frame_numbers.into_iter().map(|x| x as usize).collect(),
            },
            tool_info: hdr10plus::metadata_json::ToolInfo {
                tool: "dovi_tool".to_string(),
                version: env!("CARGO_PKG_VERSION").to_string(),
            },
        })
    }

    /// Build luminance parameters for a frame
    fn build_luminance_parameters(&self, frame: &FrameMetadata) -> Result<hdr10plus::metadata_json::LuminanceParameters> {
        // Convert PQ values to nits
        let min_nits = pq_12_bit_to_nits(frame.min_pq);
        let max_nits = pq_12_bit_to_nits(frame.max_pq);
        let avg_nits = pq_12_bit_to_nits(frame.avg_pq);

        // Calculate distribution values for HDR10+
        let distribution_values = self.calculate_distribution_values(frame)?;
        
        // Calculate MaxScl values (RGB scaling factors)
        let max_scl = self.calculate_max_scl(frame)?;

        // Calculate average RGB
        let average_rgb = (avg_nits * 1000.0) as u32;

        Ok(hdr10plus::metadata_json::LuminanceParameters {
            average_rgb,
            max_scl,
            luminance_distributions: hdr10plus::metadata_json::LuminanceDistributions {
                distribution_index: vec![1, 5, 10, 25, 50, 75, 90, 95, 99],
                distribution_values,
            },
        })
    }

    /// Calculate distribution values for HDR10+ metadata
    fn calculate_distribution_values(&self, frame: &FrameMetadata) -> Result<Vec<u32>> {
        let min_nits = pq_12_bit_to_nits(frame.min_pq);
        let max_nits = pq_12_bit_to_nits(frame.max_pq);
        let avg_nits = pq_12_bit_to_nits(frame.avg_pq);

        // For high precision mode, use more accurate distribution calculation
        if self.config.high_precision_mode {
            self.calculate_high_precision_distribution(min_nits, max_nits, avg_nits)
        } else {
            self.calculate_standard_distribution(min_nits, max_nits, avg_nits)
        }
    }

    /// Calculate high precision distribution values for low-nit content
    fn calculate_high_precision_distribution(&self, min_nits: f64, max_nits: f64, avg_nits: f64) -> Result<Vec<u32>> {
        let mut distribution = Vec::new();
        
        // Use logarithmic distribution for better low-nit precision
        let log_min = if min_nits > 0.0 { min_nits.log10() } else { -6.0 };
        let log_max = max_nits.log10();
        let log_avg = avg_nits.log10();
        
        let percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99];
        
        for &percentile in &percentiles {
            let p = percentile as f64 / 100.0;
            
            // Use weighted interpolation between min, avg, and max
            let value = if p <= 0.5 {
                // Lower half: interpolate between min and avg
                let t = p * 2.0;
                let log_val = log_min + t * (log_avg - log_min);
                10_f64.powf(log_val)
            } else {
                // Upper half: interpolate between avg and max
                let t = (p - 0.5) * 2.0;
                let log_val = log_avg + t * (log_max - log_avg);
                10_f64.powf(log_val)
            };
            
            // Convert to HDR10+ format (multiply by 1000 for precision)
            let hdr10plus_value = (value * 1000.0) as u32;
            distribution.push(hdr10plus_value);
        }
        
        Ok(distribution)
    }

    /// Calculate standard distribution values
    fn calculate_standard_distribution(&self, min_nits: f64, max_nits: f64, _avg_nits: f64) -> Result<Vec<u32>> {
        let mut distribution = Vec::new();
        
        let percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99];
        
        for &percentile in &percentiles {
            let p = percentile as f64 / 100.0;
            
            // Linear interpolation between min and max
            let value = min_nits + p * (max_nits - min_nits);
            
            // Convert to HDR10+ format
            let hdr10plus_value = (value * 1000.0) as u32;
            distribution.push(hdr10plus_value);
        }
        
        Ok(distribution)
    }

    /// Calculate MaxScl values (RGB scaling factors)
    fn calculate_max_scl(&self, frame: &FrameMetadata) -> Result<Vec<u32>> {
        let max_nits = pq_12_bit_to_nits(frame.max_pq);
        
        // For now, use equal scaling for RGB channels
        // In a more sophisticated implementation, this would consider
        // the actual color distribution from the RPU data
        let max_scl_value = (max_nits * 1000.0) as u32;
        
        Ok(vec![max_scl_value, max_scl_value, max_scl_value])
    }
}

/// Utility functions for conversion
impl Hdr10PlusConverter {
    /// Convert RPU file to HDR10+ JSON file
    pub fn convert_file_to_file<P: AsRef<Path>>(
        &self,
        input_path: P,
        output_path: P,
    ) -> Result<()> {
        let rpu_data = std::fs::read(input_path)?;
        let rpu = DoviRpu::parse_unspec62_nalu(&rpu_data)?;
        
        let hdr10plus_metadata = self.convert_single_rpu(&rpu)?;
        
        let json_string = serde_json::to_string_pretty(&hdr10plus_metadata)?;
        std::fs::write(output_path, json_string)?;
        
        Ok(())
    }

    /// Convert multiple RPU files to HDR10+ JSON file
    pub fn convert_files_to_file<P: AsRef<Path>>(
        &self,
        input_paths: &[P],
        output_path: P,
    ) -> Result<()> {
        let mut rpus = Vec::new();
        
        for path in input_paths {
            let rpu_data = std::fs::read(path)?;
            let rpu = DoviRpu::parse_unspec62_nalu(&rpu_data)?;
            rpus.push(rpu);
        }
        
        let hdr10plus_metadata = self.convert_multiple_rpus(&rpus)?;
        
        let json_string = serde_json::to_string_pretty(&hdr10plus_metadata)?;
        std::fs::write(output_path, json_string)?;
        
        Ok(())
    }
}

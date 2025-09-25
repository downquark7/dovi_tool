use anyhow::{Result, bail};
use std::path::Path;

use crate::commands::ConvertToHdr10PlusArgs;
use crate::dovi::hdr10plus_converter::{Hdr10PlusConverter, Hdr10PlusConverterConfig};
use crate::dovi::hdr10plus_schema::Hdr10PlusSchemaValidator;
use dolby_vision::rpu::dovi_rpu::DoviRpu;
use hdr10plus::metadata::PeakBrightnessSource;

pub struct Hdr10PlusConverterImpl;

impl Hdr10PlusConverterImpl {
    /// Execute the convert-to-hdr10plus command
    pub fn convert_to_hdr10plus(args: ConvertToHdr10PlusArgs) -> Result<()> {
        if args.verbose {
            println!("Starting Dolby Vision RPU to HDR10+ conversion...");
            println!("Input files: {:?}", args.input);
            println!("Output file: {:?}", args.output);
        }

        // Validate input files exist
        for input_path in &args.input {
            if !input_path.exists() {
                bail!("Input file does not exist: {:?}", input_path);
            }
        }

        // Parse peak brightness source
        let peak_brightness_source = match args.peak_brightness_source.as_str() {
            "histogram" => PeakBrightnessSource::Histogram,
            "histogram99" => PeakBrightnessSource::Histogram99,
            "maxscl" => PeakBrightnessSource::MaxScl,
            "maxscl_luminance" => PeakBrightnessSource::MaxSclLuminance,
            _ => {
                bail!("Invalid peak brightness source: {}", args.peak_brightness_source);
            }
        };

        // Create converter configuration
        let config = Hdr10PlusConverterConfig {
            target_display_max_luminance: if args.target_display_max_luminance == 0 {
                None
            } else {
                Some(args.target_display_max_luminance)
            },
            peak_brightness_source,
            high_precision_mode: args.high_precision_mode,
            scene_detection_threshold: args.scene_detection_threshold,
            max_scenes: args.max_scenes,
        };

        let converter = Hdr10PlusConverter::new(config);

        // Convert based on number of input files
        if args.input.len() == 1 {
            if args.verbose {
                println!("Converting single RPU file...");
            }
            converter.convert_file_to_file(&args.input[0], &args.output)?;
        } else {
            if args.verbose {
                println!("Converting {} RPU files with scene detection...", args.input.len());
            }
            converter.convert_files_to_file(&args.input, args.output.clone())?;
        }

        if args.verbose {
            println!("Conversion completed successfully!");
        }

        // Validate output if requested
        if args.validate_output {
            if args.verbose {
                println!("Validating output against HDR10+ schema...");
            }
            Self::validate_output(&args.output)?;
            if args.verbose {
                println!("Output validation passed!");
            }
        }

        Ok(())
    }

    /// Validate the output JSON file against HDR10+ schema
    fn validate_output<P: AsRef<Path>>(output_path: P) -> Result<()> {
        let json_content = std::fs::read_to_string(output_path)?;
        let json_value: serde_json::Value = serde_json::from_str(&json_content)?;
        
        let validator = Hdr10PlusSchemaValidator::new();
        validator.validate(&json_value)?;
        
        Ok(())
    }

    /// Convert a single RPU to HDR10+ metadata (for testing)
    pub fn convert_single_rpu_to_json(rpu: &DoviRpu, config: Hdr10PlusConverterConfig) -> Result<serde_json::Value> {
        let converter = Hdr10PlusConverter::new(config);
        let metadata = converter.convert_single_rpu(rpu)?;
        Ok(serde_json::to_value(metadata)?)
    }

    /// Convert multiple RPUs to HDR10+ metadata (for testing)
    pub fn convert_multiple_rpus_to_json(rpus: &[DoviRpu], config: Hdr10PlusConverterConfig) -> Result<serde_json::Value> {
        let converter = Hdr10PlusConverter::new(config);
        let metadata = converter.convert_multiple_rpus(rpus)?;
        Ok(serde_json::to_value(metadata)?)
    }
}

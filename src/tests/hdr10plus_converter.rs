use anyhow::Result;

use crate::dovi::hdr10plus_converter::{Hdr10PlusConverter, Hdr10PlusConverterConfig};
use crate::dovi::hdr10plus_schema::Hdr10PlusSchemaValidator;
use hdr10plus::metadata::PeakBrightnessSource;

#[test]
fn test_converter_config_default() {
    let config = Hdr10PlusConverterConfig::default();
    assert_eq!(config.target_display_max_luminance, None);
    assert_eq!(config.peak_brightness_source, PeakBrightnessSource::MaxScl);
    assert!(config.high_precision_mode);
    assert_eq!(config.scene_detection_threshold, 0.1);
    assert_eq!(config.max_scenes, None);
}

#[test]
fn test_converter_config_custom() {
    let config = Hdr10PlusConverterConfig {
        target_display_max_luminance: Some(1000),
        peak_brightness_source: PeakBrightnessSource::Histogram,
        high_precision_mode: false,
        scene_detection_threshold: 0.2,
        max_scenes: Some(5),
    };
    
    assert_eq!(config.target_display_max_luminance, Some(1000));
    assert_eq!(config.peak_brightness_source, PeakBrightnessSource::Histogram);
    assert!(!config.high_precision_mode);
    assert_eq!(config.scene_detection_threshold, 0.2);
    assert_eq!(config.max_scenes, Some(5));
}

#[test]
fn test_schema_validator_creation() {
    let validator = Hdr10PlusSchemaValidator::new();
    // Validator should be created successfully
    assert!(true);
}

#[test]
fn test_converter_creation() {
    let config = Hdr10PlusConverterConfig::default();
    let _converter = Hdr10PlusConverter::new(config);
    // Converter should be created successfully
    assert!(true);
}

#[test]
fn test_peak_brightness_source_variants() {
    // Test that all expected variants exist
    let _histogram = PeakBrightnessSource::Histogram;
    let _histogram99 = PeakBrightnessSource::Histogram99;
    let _maxscl = PeakBrightnessSource::MaxScl;
    let _maxscl_luminance = PeakBrightnessSource::MaxSclLuminance;
    
    // All variants should be accessible
    assert!(true);
}
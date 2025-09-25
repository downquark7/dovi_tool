use clap::{Args, ValueHint};
use std::path::PathBuf;

#[derive(Args, Debug)]
pub struct ConvertToHdr10PlusArgs {
    /// Input RPU file(s) to convert
    #[arg(
        short = 'i',
        long,
        help = "Input RPU file(s) to convert",
        value_hint = ValueHint::FilePath,
        required = true
    )]
    pub input: Vec<PathBuf>,

    /// Output HDR10+ JSON file
    #[arg(
        short = 'o',
        long,
        help = "Output HDR10+ JSON file",
        value_hint = ValueHint::FilePath,
        required = true
    )]
    pub output: PathBuf,

    /// Target system display maximum luminance (0 = use source)
    #[arg(
        long,
        help = "Target system display maximum luminance in nits (0 = use source)",
        default_value = "0"
    )]
    pub target_display_max_luminance: u16,

    /// Peak brightness source for HDR10+ metadata
    #[arg(
        long,
        help = "Peak brightness source for HDR10+ metadata (histogram, histogram99, maxscl, maxscl_luminance)",
        default_value = "maxscl"
    )]
    pub peak_brightness_source: String,

    /// Enable high precision mode for low-nit content
    #[arg(
        long,
        help = "Enable high precision mode for low-nit content (<1000 nits)",
        default_value = "true"
    )]
    pub high_precision_mode: bool,

    /// Scene detection threshold for grouping frames
    #[arg(
        long,
        help = "Scene detection threshold for grouping frames (0.0-1.0)",
        default_value = "0.1"
    )]
    pub scene_detection_threshold: f64,

    /// Maximum number of scenes to process
    #[arg(
        long,
        help = "Maximum number of scenes to process (0 = no limit)"
    )]
    pub max_scenes: Option<usize>,

    /// Validate output against HDR10+ schema
    #[arg(
        long,
        help = "Validate output against HDR10+ schema",
        default_value = "true"
    )]
    pub validate_output: bool,

    /// Verbose output
    #[arg(
        short = 'v',
        long,
        help = "Enable verbose output"
    )]
    pub verbose: bool,
}
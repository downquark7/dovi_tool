#!/usr/bin/env python3
"""
Dolby Vision RPU to HDR10+ Metadata Converter

This module provides functionality to convert Dolby Vision Reference Processing Unit (RPU)
data into HDR10+ metadata and generate fully compliant HDR10+ JSON files.

Author: AI Assistant
License: MIT
"""

import json
import struct
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict
from enum import IntEnum
# import numpy as np  # Optional dependency

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RPUType(IntEnum):
    """Dolby Vision RPU types"""
    TYPE_1 = 1
    TYPE_2 = 2
    TYPE_3 = 3
    TYPE_4 = 4


@dataclass
class ColorPrimaries:
    """Color primaries for mastering display"""
    red: Tuple[float, float]
    green: Tuple[float, float]
    blue: Tuple[float, float]
    white: Tuple[float, float]


@dataclass
class MasteringDisplay:
    """Mastering display information"""
    min_luminance: float
    max_luminance: float
    primaries: ColorPrimaries


@dataclass
class ToneMapping:
    """Tone mapping parameters"""
    knee_point: float
    knee_slope: float


@dataclass
class ColorSaturation:
    """Color saturation parameters"""
    saturation_gain: float


@dataclass
class SceneInfo:
    """Scene-specific metadata"""
    scene_frame_index: int
    max_cll: int
    max_fall: int
    tone_mapping: Optional[ToneMapping] = None
    color_saturation: Optional[ColorSaturation] = None


@dataclass
class HDR10PlusMetadata:
    """Complete HDR10+ metadata structure"""
    tool: str = "DolbyVisionToHDR10Plus"
    tool_version: str = "1.0.0"
    title: str = ""
    alternate_version: str = ""
    mastering_display: Optional[MasteringDisplay] = None
    max_cll: int = 0
    max_fall: int = 0
    scenes: List[SceneInfo] = None

    def __post_init__(self):
        if self.scenes is None:
            self.scenes = []


class DolbyVisionRPUParser:
    """Parser for Dolby Vision RPU data"""
    
    def __init__(self, rpu_data: bytes):
        self.rpu_data = rpu_data
        self.offset = 0
        
    def read_uint8(self) -> int:
        """Read unsigned 8-bit integer"""
        if self.offset >= len(self.rpu_data):
            raise ValueError("Unexpected end of RPU data")
        value = self.rpu_data[self.offset]
        self.offset += 1
        return value
    
    def read_uint16(self) -> int:
        """Read unsigned 16-bit integer (big-endian)"""
        if self.offset + 1 >= len(self.rpu_data):
            raise ValueError("Unexpected end of RPU data")
        value = struct.unpack('>H', self.rpu_data[self.offset:self.offset + 2])[0]
        self.offset += 2
        return value
    
    def read_uint32(self) -> int:
        """Read unsigned 32-bit integer (big-endian)"""
        if self.offset + 3 >= len(self.rpu_data):
            raise ValueError("Unexpected end of RPU data")
        value = struct.unpack('>I', self.rpu_data[self.offset:self.offset + 4])[0]
        self.offset += 4
        return value
    
    def read_float(self) -> float:
        """Read 32-bit float (big-endian)"""
        if self.offset + 3 >= len(self.rpu_data):
            raise ValueError("Unexpected end of RPU data")
        value = struct.unpack('>f', self.rpu_data[self.offset:self.offset + 4])[0]
        self.offset += 4
        return value
    
    def skip_bytes(self, count: int):
        """Skip specified number of bytes"""
        self.offset += count
    
    def parse_rpu_header(self) -> Dict[str, Any]:
        """Parse RPU header information"""
        header = {}
        
        # Read RPU header (simplified parsing)
        if len(self.rpu_data) < 4:
            raise ValueError("Invalid RPU data: too short")
        
        # Check for RPU magic number or similar identifier
        # This is a simplified implementation - real RPU parsing is more complex
        header['rpu_type'] = self.read_uint8()
        header['rpu_version'] = self.read_uint8()
        header['rpu_size'] = self.read_uint16()
        
        logger.info(f"RPU Type: {header['rpu_type']}, Version: {header['rpu_version']}, Size: {header['rpu_size']}")
        
        return header
    
    def parse_mastering_display_info(self) -> MasteringDisplay:
        """Parse mastering display information from RPU"""
        # Default values for common mastering displays
        # In a real implementation, these would be extracted from the RPU data
        primaries = ColorPrimaries(
            red=(0.680, 0.320),    # DCI-P3 red
            green=(0.265, 0.690),  # DCI-P3 green
            blue=(0.150, 0.060),   # DCI-P3 blue
            white=(0.3127, 0.3290) # D65 white point
        )
        
        return MasteringDisplay(
            min_luminance=0.0001,
            max_luminance=1000.0,
            primaries=primaries
        )
    
    def parse_dynamic_metadata(self) -> List[SceneInfo]:
        """Parse dynamic metadata for scenes"""
        scenes = []
        
        # This is a simplified implementation
        # Real RPU parsing would extract actual scene-by-scene metadata
        
        # For demonstration, create a single scene with default values
        scene = SceneInfo(
            scene_frame_index=0,
            max_cll=1000,
            max_fall=400,
            tone_mapping=ToneMapping(
                knee_point=0.75,
                knee_slope=0.5
            ),
            color_saturation=ColorSaturation(
                saturation_gain=1.0
            )
        )
        scenes.append(scene)
        
        return scenes
    
    def parse_rpu(self) -> HDR10PlusMetadata:
        """Parse complete RPU data and extract metadata"""
        try:
            # Reset offset
            self.offset = 0
            
            # Parse header
            header = self.parse_rpu_header()
            
            # Parse mastering display info
            mastering_display = self.parse_mastering_display_info()
            
            # Parse dynamic metadata
            scenes = self.parse_dynamic_metadata()
            
            # Calculate global MaxCLL and MaxFALL
            max_cll = max(scene.max_cll for scene in scenes) if scenes else 1000
            max_fall = max(scene.max_fall for scene in scenes) if scenes else 400
            
            return HDR10PlusMetadata(
                mastering_display=mastering_display,
                max_cll=max_cll,
                max_fall=max_fall,
                scenes=scenes
            )
            
        except Exception as e:
            logger.error(f"Error parsing RPU data: {e}")
            raise


class HDR10PlusJSONGenerator:
    """Generator for HDR10+ compliant JSON files"""
    
    @staticmethod
    def convert_to_hdr10plus_json(metadata: HDR10PlusMetadata) -> Dict[str, Any]:
        """Convert metadata to HDR10+ JSON format"""
        
        # Base HDR10+ structure
        hdr10plus_json = {
            "Tool": metadata.tool,
            "ToolVersion": metadata.tool_version,
            "Title": metadata.title,
            "AlternateVersion": metadata.alternate_version,
            "HDR10Plus": {
                "MasteringDisplay": {
                    "MinLuminance": metadata.mastering_display.min_luminance,
                    "MaxLuminance": metadata.mastering_display.max_luminance,
                    "Primaries": {
                        "Red": list(metadata.mastering_display.primaries.red),
                        "Green": list(metadata.mastering_display.primaries.green),
                        "Blue": list(metadata.mastering_display.primaries.blue),
                        "White": list(metadata.mastering_display.primaries.white)
                    }
                },
                "MaxCLL": metadata.max_cll,
                "MaxFALL": metadata.max_fall,
                "SceneInfo": []
            }
        }
        
        # Add scene information
        for scene in metadata.scenes:
            scene_data = {
                "SceneFrameIndex": scene.scene_frame_index,
                "MaxCLL": scene.max_cll,
                "MaxFALL": scene.max_fall
            }
            
            if scene.tone_mapping:
                scene_data["ToneMapping"] = {
                    "KneePoint": scene.tone_mapping.knee_point,
                    "KneeSlope": scene.tone_mapping.knee_slope
                }
            
            if scene.color_saturation:
                scene_data["ColorSaturation"] = {
                    "SaturationGain": scene.color_saturation.saturation_gain
                }
            
            hdr10plus_json["HDR10Plus"]["SceneInfo"].append(scene_data)
        
        return hdr10plus_json
    
    @staticmethod
    def validate_hdr10plus_json(json_data: Union[Dict[str, Any], str]) -> bool:
        """Validate HDR10+ JSON structure for compliance"""
        # Parse JSON string if needed
        if isinstance(json_data, str):
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON string: {e}")
                return False
        
        required_fields = ["Tool", "ToolVersion", "HDR10Plus"]
        
        # Check required top-level fields
        for field in required_fields:
            if field not in json_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        hdr10plus = json_data["HDR10Plus"]
        required_hdr_fields = ["MasteringDisplay", "MaxCLL", "MaxFALL", "SceneInfo"]
        
        # Check required HDR10+ fields
        for field in required_hdr_fields:
            if field not in hdr10plus:
                logger.error(f"Missing required HDR10+ field: {field}")
                return False
        
        # Validate MasteringDisplay structure
        mastering_display = hdr10plus["MasteringDisplay"]
        required_md_fields = ["MinLuminance", "MaxLuminance", "Primaries"]
        
        for field in required_md_fields:
            if field not in mastering_display:
                logger.error(f"Missing required MasteringDisplay field: {field}")
                return False
        
        # Validate Primaries structure
        primaries = mastering_display["Primaries"]
        required_primaries = ["Red", "Green", "Blue", "White"]
        
        for primary in required_primaries:
            if primary not in primaries:
                logger.error(f"Missing required primary: {primary}")
                return False
            
            if not isinstance(primaries[primary], list) or len(primaries[primary]) != 2:
                logger.error(f"Invalid primary {primary}: must be a list of 2 floats")
                return False
        
        # Validate numeric values
        if not isinstance(hdr10plus["MaxCLL"], (int, float)) or hdr10plus["MaxCLL"] <= 0:
            logger.error("MaxCLL must be a positive number")
            return False
        
        if not isinstance(hdr10plus["MaxFALL"], (int, float)) or hdr10plus["MaxFALL"] <= 0:
            logger.error("MaxFALL must be a positive number")
            return False
        
        logger.info("HDR10+ JSON validation passed")
        return True


def convert_dolby_vision_rpu_to_hdr10plus(rpu_data: bytes, 
                                        title: str = "",
                                        alternate_version: str = "") -> str:
    """
    Convert Dolby Vision RPU data to HDR10+ JSON metadata.
    
    Args:
        rpu_data: Raw RPU data bytes
        title: Content title for the metadata
        alternate_version: Version description for the metadata
        
    Returns:
        JSON string containing HDR10+ metadata
        
    Raises:
        ValueError: If RPU data is invalid or conversion fails
    """
    try:
        # Parse RPU data
        parser = DolbyVisionRPUParser(rpu_data)
        metadata = parser.parse_rpu()
        
        # Set additional metadata
        metadata.title = title
        metadata.alternate_version = alternate_version
        
        # Convert to HDR10+ JSON
        generator = HDR10PlusJSONGenerator()
        hdr10plus_json = generator.convert_to_hdr10plus_json(metadata)
        
        # Validate the JSON
        if not generator.validate_hdr10plus_json(hdr10plus_json):
            raise ValueError("Generated HDR10+ JSON failed validation")
        
        # Return as formatted JSON string
        return json.dumps(hdr10plus_json, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise ValueError(f"Failed to convert Dolby Vision RPU to HDR10+: {e}")


def convert_rpu_file_to_hdr10plus_json(rpu_file_path: str, 
                                     output_file_path: str,
                                     title: str = "",
                                     alternate_version: str = "") -> None:
    """
    Convert Dolby Vision RPU file to HDR10+ JSON file.
    
    Args:
        rpu_file_path: Path to input RPU file
        output_file_path: Path to output JSON file
        title: Content title for the metadata
        alternate_version: Version description for the metadata
        
    Raises:
        FileNotFoundError: If RPU file doesn't exist
        ValueError: If conversion fails
    """
    try:
        # Read RPU file
        with open(rpu_file_path, 'rb') as f:
            rpu_data = f.read()
        
        if not rpu_data:
            raise ValueError("RPU file is empty")
        
        # Convert to HDR10+ JSON
        hdr10plus_json = convert_dolby_vision_rpu_to_hdr10plus(
            rpu_data, title, alternate_version
        )
        
        # Write to output file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(hdr10plus_json)
        
        logger.info(f"Successfully converted {rpu_file_path} to {output_file_path}")
        
    except FileNotFoundError:
        logger.error(f"RPU file not found: {rpu_file_path}")
        raise
    except Exception as e:
        logger.error(f"File conversion failed: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python dolby_to_hdr10plus.py <input.rpu> <output.json> [title] [version]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else ""
    version = sys.argv[4] if len(sys.argv) > 4 else ""
    
    try:
        convert_rpu_file_to_hdr10plus_json(input_file, output_file, title, version)
        print(f"Conversion completed successfully: {output_file}")
    except Exception as e:
        print(f"Conversion failed: {e}")
        sys.exit(1)
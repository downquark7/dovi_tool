"""
Dolby Vision RPU (Reference Processing Unit) parser using dovi_tool integration.
"""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class RPUParser:
    """
    Parser for Dolby Vision RPU metadata using dovi_tool.
    """
    
    def __init__(self, dovi_tool_path: str = "dovi_tool"):
        """
        Initialize the RPU parser.
        
        Args:
            dovi_tool_path: Path to dovi_tool executable
        """
        self.dovi_tool_path = dovi_tool_path
        self._check_dovi_tool()
    
    def _check_dovi_tool(self) -> None:
        """Check if dovi_tool is available."""
        try:
            result = subprocess.run([self.dovi_tool_path, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"dovi_tool found: {result.stdout.strip()}")
            else:
                raise FileNotFoundError("dovi_tool not found or not working")
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.error(f"dovi_tool check failed: {e}")
            raise RuntimeError("dovi_tool is required but not found. Please install it with: cargo install dovi_tool")
    
    def parse_rpu(self, input_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse Dolby Vision RPU from input file.
        
        Args:
            input_path: Path to input HEVC file or RPU binary
            
        Returns:
            Parsed RPU data dictionary or None if parsing fails
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return None
        
        try:
            # Check if input is already an RPU file or needs extraction
            if input_path.suffix.lower() == '.bin' and self._is_rpu_file(input_path):
                logger.info("Input appears to be an RPU file, parsing directly")
                return self._parse_rpu_binary(input_path)
            else:
                logger.info("Extracting RPU from HEVC file")
                return self._extract_and_parse_rpu(input_path)
                
        except Exception as e:
            logger.error(f"Failed to parse RPU: {e}")
            return None
    
    def _is_rpu_file(self, file_path: Path) -> bool:
        """Check if file is likely an RPU binary file."""
        try:
            with open(file_path, 'rb') as f:
                # Check for RPU magic bytes or structure
                header = f.read(16)
                # This is a heuristic - RPU files typically start with specific patterns
                return len(header) >= 4 and header[0:4] != b'\x00\x00\x00\x00'
        except:
            return False
    
    def _extract_and_parse_rpu(self, hevc_path: Path) -> Optional[Dict[str, Any]]:
        """Extract RPU from HEVC file and parse it."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_rpu = Path(temp_dir) / "extracted_rpu.bin"
            
            # Extract RPU using dovi_tool
            try:
                cmd = [self.dovi_tool_path, "extract-rpu", "-i", str(hevc_path), "-o", str(temp_rpu)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    logger.error(f"dovi_tool extract-rpu failed: {result.stderr}")
                    return None
                
                if not temp_rpu.exists():
                    logger.error("RPU extraction failed - no output file created")
                    return None
                
                return self._parse_rpu_binary(temp_rpu)
                
            except subprocess.TimeoutExpired:
                logger.error("RPU extraction timed out")
                return None
            except Exception as e:
                logger.error(f"RPU extraction failed: {e}")
                return None
    
    def _parse_rpu_binary(self, rpu_path: Path) -> Optional[Dict[str, Any]]:
        """Parse RPU binary file and extract metadata."""
        try:
            # Get RPU info using dovi_tool
            cmd = [self.dovi_tool_path, "info", "-i", str(rpu_path), "--json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"dovi_tool info failed: {result.stderr}")
                return None
            
            # Parse JSON output
            rpu_info = json.loads(result.stdout)
            
            # Extract and structure the metadata
            parsed_data = self._structure_rpu_data(rpu_info)
            
            logger.info("Successfully parsed RPU metadata")
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse dovi_tool JSON output: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to parse RPU binary: {e}")
            return None
    
    def _structure_rpu_data(self, rpu_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure the raw RPU data into a more usable format.
        
        Args:
            rpu_info: Raw RPU info from dovi_tool
            
        Returns:
            Structured RPU data
        """
        structured_data = {
            "source": "dolby_vision_rpu",
            "version": rpu_info.get("version", "unknown"),
            "profile": rpu_info.get("profile", {}),
            "level": rpu_info.get("level", {}),
            "mastering_display": self._extract_mastering_display(rpu_info),
            "content_light_level": self._extract_content_light_level(rpu_info),
            "tone_mapping": self._extract_tone_mapping_data(rpu_info),
            "scene_info": self._extract_scene_info(rpu_info),
            "color_volume": self._extract_color_volume(rpu_info),
            "raw_data": rpu_info  # Keep raw data for reference
        }
        
        return structured_data
    
    def _extract_mastering_display(self, rpu_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract mastering display information."""
        mastering_display = rpu_info.get("mastering_display", {})
        
        return {
            "primaries": {
                "red": mastering_display.get("red_primary", [0.708, 0.292]),
                "green": mastering_display.get("green_primary", [0.170, 0.797]),
                "blue": mastering_display.get("blue_primary", [0.131, 0.046]),
                "white": mastering_display.get("white_point", [0.3127, 0.3290])
            },
            "luminance": {
                "min": mastering_display.get("min_luminance", 0.0001),
                "max": mastering_display.get("max_luminance", 1000.0)
            }
        }
    
    def _extract_content_light_level(self, rpu_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content light level information."""
        content_light = rpu_info.get("content_light_level", {})
        
        return {
            "max_cll": content_light.get("max_cll", 0),
            "max_fall": content_light.get("max_fall", 0.0),
            "average_cll": content_light.get("average_cll", 0.0)
        }
    
    def _extract_tone_mapping_data(self, rpu_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract tone mapping related data."""
        tone_mapping = rpu_info.get("tone_mapping", {})
        
        return {
            "target_display": tone_mapping.get("target_display", {}),
            "trim_slopes": tone_mapping.get("trim_slopes", []),
            "trim_offsets": tone_mapping.get("trim_offsets", []),
            "trim_power": tone_mapping.get("trim_power", []),
            "trim_chroma_weight": tone_mapping.get("trim_chroma_weight", []),
            "trim_saturation_gain": tone_mapping.get("trim_saturation_gain", [])
        }
    
    def _extract_scene_info(self, rpu_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract scene-related information."""
        scene_info = rpu_info.get("scene_info", {})
        
        return {
            "scene_refresh_flag": scene_info.get("scene_refresh_flag", False),
            "scene_change_detection": scene_info.get("scene_change_detection", []),
            "frame_count": scene_info.get("frame_count", 0)
        }
    
    def _extract_color_volume(self, rpu_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract color volume information."""
        color_volume = rpu_info.get("color_volume", {})
        
        return {
            "color_primaries": color_volume.get("color_primaries", "bt2020"),
            "transfer_characteristics": color_volume.get("transfer_characteristics", "pq"),
            "matrix_coefficients": color_volume.get("matrix_coefficients", "bt2020_ncl")
        }
    
    def get_rpu_summary(self, input_path: Path) -> Optional[str]:
        """
        Get a human-readable summary of RPU data.
        
        Args:
            input_path: Path to input file
            
        Returns:
            Summary string or None if parsing fails
        """
        try:
            cmd = [self.dovi_tool_path, "info", "-i", str(input_path), "-s"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"Failed to get RPU summary: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get RPU summary: {e}")
            return None
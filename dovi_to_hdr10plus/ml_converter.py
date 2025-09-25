"""
Machine learning-based converter from Dolby Vision RPU to HDR10+ metadata.
"""

import logging
import pickle
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib

logger = logging.getLogger(__name__)


class MLConverter:
    """
    Machine learning-based converter for Dolby Vision RPU to HDR10+ metadata.
    Uses trained models to predict HDR10+ parameters from Dolby Vision metadata.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the ML converter.
        
        Args:
            model_path: Path to pre-trained model file
        """
        self.model_path = model_path
        self.models = {}
        self.scalers = {}
        self.feature_names = []
        self.is_trained = False
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
        else:
            self._initialize_default_models()
    
    def _initialize_default_models(self) -> None:
        """Initialize default ML models."""
        self.models = {
            "max_cll": RandomForestRegressor(n_estimators=100, random_state=42),
            "max_fall": RandomForestRegressor(n_estimators=100, random_state=42),
            "mastering_max_luminance": Ridge(alpha=1.0),
            "mastering_min_luminance": Ridge(alpha=1.0),
            "color_primaries": GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        
        # Initialize scalers for each model
        for model_name in self.models.keys():
            self.scalers[model_name] = StandardScaler()
        
        # Define feature names for RPU data
        self.feature_names = [
            "rpu_max_cll", "rpu_max_fall", "rpu_avg_cll",
            "mastering_max_lum", "mastering_min_lum",
            "red_x", "red_y", "green_x", "green_y", "blue_x", "blue_y",
            "white_x", "white_y", "trim_slope_0", "trim_slope_1", "trim_slope_2",
            "trim_offset_0", "trim_offset_1", "trim_offset_2",
            "trim_power_0", "trim_power_1", "trim_power_2",
            "scene_refresh_flag", "frame_count"
        ]
    
    def convert(self, rpu_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Dolby Vision RPU data to HDR10+ metadata using ML models.
        
        Args:
            rpu_data: Parsed RPU data from RPUParser
            
        Returns:
            HDR10+ metadata dictionary
        """
        if not self.is_trained:
            logger.warning("ML models not trained, falling back to heuristic conversion")
            return self._fallback_heuristic_conversion(rpu_data)
        
        logger.info("Starting ML-based conversion from Dolby Vision RPU to HDR10+")
        
        # Extract features from RPU data
        features = self._extract_features(rpu_data)
        
        # Predict HDR10+ parameters
        hdr10plus_metadata = {
            "source": "dolby_vision_rpu_conversion",
            "conversion_method": "machine_learning",
            "MaxCLL": self._predict_max_cll(features),
            "MaxFALL": self._predict_max_fall(features),
            "MasteringDisplay": self._predict_mastering_display(features),
            "TargetedSystemDisplayMaximumLuminance": self._predict_target_display_max_luminance(features),
            "TargetedSystemDisplayMinimumLuminance": self._predict_target_display_min_luminance(features)
        }
        
        # Add confidence scores
        hdr10plus_metadata["prediction_confidence"] = self._calculate_confidence_scores(features)
        
        logger.info("ML-based conversion completed")
        return hdr10plus_metadata
    
    def _extract_features(self, rpu_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from RPU data for ML models."""
        features = np.zeros(len(self.feature_names))
        
        # Content light level features
        content_light = rpu_data.get("content_light_level", {})
        features[0] = content_light.get("max_cll", 0)  # rpu_max_cll
        features[1] = content_light.get("max_fall", 0.0)  # rpu_max_fall
        features[2] = content_light.get("average_cll", 0.0)  # rpu_avg_cll
        
        # Mastering display features
        mastering_display = rpu_data.get("mastering_display", {})
        luminance = mastering_display.get("luminance", {})
        features[3] = luminance.get("max", 1000.0)  # mastering_max_lum
        features[4] = luminance.get("min", 0.0001)  # mastering_min_lum
        
        # Color primaries features
        primaries = mastering_display.get("primaries", {})
        red = primaries.get("red", [0.708, 0.292])
        green = primaries.get("green", [0.170, 0.797])
        blue = primaries.get("blue", [0.131, 0.046])
        white = primaries.get("white", [0.3127, 0.3290])
        
        features[5:7] = red  # red_x, red_y
        features[7:9] = green  # green_x, green_y
        features[9:11] = blue  # blue_x, blue_y
        features[11:13] = white  # white_x, white_y
        
        # Tone mapping features
        tone_mapping = rpu_data.get("tone_mapping", {})
        trim_slopes = tone_mapping.get("trim_slopes", [1.0, 1.0, 1.0])
        trim_offsets = tone_mapping.get("trim_offsets", [0.0, 0.0, 0.0])
        trim_power = tone_mapping.get("trim_power", [1.0, 1.0, 1.0])
        
        features[13:16] = trim_slopes[:3]  # trim_slope_0, trim_slope_1, trim_slope_2
        features[16:19] = trim_offsets[:3]  # trim_offset_0, trim_offset_1, trim_offset_2
        features[19:22] = trim_power[:3]  # trim_power_0, trim_power_1, trim_power_2
        
        # Scene information features
        scene_info = rpu_data.get("scene_info", {})
        features[22] = 1.0 if scene_info.get("scene_refresh_flag", False) else 0.0  # scene_refresh_flag
        features[23] = scene_info.get("frame_count", 0)  # frame_count
        
        return features.reshape(1, -1)
    
    def _predict_max_cll(self, features: np.ndarray) -> int:
        """Predict MaxCLL using trained model."""
        if "max_cll" not in self.models:
            return 1000  # Default fallback
        
        scaled_features = self.scalers["max_cll"].transform(features)
        prediction = self.models["max_cll"].predict(scaled_features)[0]
        return max(0, min(int(prediction), 10000))
    
    def _predict_max_fall(self, features: np.ndarray) -> float:
        """Predict MaxFALL using trained model."""
        if "max_fall" not in self.models:
            return 100.0  # Default fallback
        
        scaled_features = self.scalers["max_fall"].transform(features)
        prediction = self.models["max_fall"].predict(scaled_features)[0]
        return max(0.0, min(prediction, 1000.0))
    
    def _predict_mastering_display(self, features: np.ndarray) -> Dict[str, Any]:
        """Predict mastering display parameters."""
        # Predict luminance values
        max_lum = self._predict_mastering_max_luminance(features)
        min_lum = self._predict_mastering_min_luminance(features)
        
        # Predict color primaries (simplified - using default BT.2020 for now)
        primaries = {
            "Red": [0.708, 0.292],
            "Green": [0.170, 0.797],
            "Blue": [0.131, 0.046],
            "White": [0.3127, 0.3290]
        }
        
        return {
            "Primaries": primaries,
            "Luminance": {
                "Min": min_lum,
                "Max": max_lum
            }
        }
    
    def _predict_mastering_max_luminance(self, features: np.ndarray) -> float:
        """Predict mastering display maximum luminance."""
        if "mastering_max_luminance" not in self.models:
            return 1000.0  # Default fallback
        
        scaled_features = self.scalers["mastering_max_luminance"].transform(features)
        prediction = self.models["mastering_max_luminance"].predict(scaled_features)[0]
        return max(1.0, min(prediction, 10000.0))
    
    def _predict_mastering_min_luminance(self, features: np.ndarray) -> float:
        """Predict mastering display minimum luminance."""
        if "mastering_min_luminance" not in self.models:
            return 0.0001  # Default fallback
        
        scaled_features = self.scalers["mastering_min_luminance"].transform(features)
        prediction = self.models["mastering_min_luminance"].predict(scaled_features)[0]
        return max(0.0, min(prediction, 1.0))
    
    def _predict_target_display_max_luminance(self, features: np.ndarray) -> int:
        """Predict target display maximum luminance."""
        # Use a simple heuristic based on mastering display max luminance
        max_lum = self._predict_mastering_max_luminance(features)
        
        if max_lum >= 4000:
            return 4000
        elif max_lum >= 2000:
            return 2000
        elif max_lum >= 1000:
            return 1000
        else:
            return 600
    
    def _predict_target_display_min_luminance(self, features: np.ndarray) -> float:
        """Predict target display minimum luminance."""
        # Use a simple heuristic based on mastering display min luminance
        min_lum = self._predict_mastering_min_luminance(features)
        
        if min_lum <= 0.0001:
            return 0.0001
        elif min_lum <= 0.001:
            return 0.001
        else:
            return 0.01
    
    def _calculate_confidence_scores(self, features: np.ndarray) -> Dict[str, float]:
        """Calculate confidence scores for predictions."""
        confidence_scores = {}
        
        for model_name, model in self.models.items():
            if hasattr(model, 'predict_proba'):
                # For models that support probability prediction
                try:
                    scaled_features = self.scalers[model_name].transform(features)
                    proba = model.predict_proba(scaled_features)
                    confidence_scores[model_name] = float(np.max(proba))
                except:
                    confidence_scores[model_name] = 0.5  # Default confidence
            else:
                # For regression models, use a simple heuristic
                confidence_scores[model_name] = 0.7  # Default confidence
        
        return confidence_scores
    
    def _fallback_heuristic_conversion(self, rpu_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to heuristic conversion when ML models are not available."""
        from .heuristic_converter import HeuristicConverter
        
        heuristic_converter = HeuristicConverter()
        return heuristic_converter.convert(rpu_data)
    
    def train(self, training_data: List[Dict[str, Any]], validation_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Train the ML models on provided data.
        
        Args:
            training_data: List of training examples with 'rpu_data' and 'hdr10plus_data' keys
            validation_data: Optional validation data
            
        Returns:
            Training results dictionary
        """
        logger.info(f"Training ML models on {len(training_data)} examples")
        
        # Prepare training data
        X, y = self._prepare_training_data(training_data)
        
        # Split data for training and validation
        if validation_data:
            X_val, y_val = self._prepare_training_data(validation_data)
        else:
            X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
            y = y_train
        
        # Train each model
        training_results = {}
        
        for model_name, model in self.models.items():
            logger.info(f"Training {model_name} model")
            
            # Prepare target data for this model
            y_model = self._prepare_target_data(y, model_name)
            
            # Scale features
            scaler = self.scalers[model_name]
            X_scaled = scaler.fit_transform(X)
            
            # Train model
            model.fit(X_scaled, y_model)
            
            # Evaluate model
            X_val_scaled = scaler.transform(X_val)
            y_val_model = self._prepare_target_data(y_val, model_name)
            y_pred = model.predict(X_val_scaled)
            
            mse = mean_squared_error(y_val_model, y_pred)
            r2 = r2_score(y_val_model, y_pred)
            
            training_results[model_name] = {
                "mse": mse,
                "r2_score": r2,
                "feature_importance": getattr(model, 'feature_importances_', None)
            }
            
            logger.info(f"{model_name} - MSE: {mse:.4f}, R²: {r2:.4f}")
        
        self.is_trained = True
        logger.info("ML model training completed")
        
        return training_results
    
    def _prepare_training_data(self, data: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """Prepare training data for ML models."""
        X = []
        y = []
        
        for example in data:
            rpu_data = example.get("rpu_data", {})
            hdr10plus_data = example.get("hdr10plus_data", {})
            
            if rpu_data and hdr10plus_data:
                features = self._extract_features(rpu_data)
                X.append(features.flatten())
                y.append(hdr10plus_data)
        
        return np.array(X), y
    
    def _prepare_target_data(self, y_data: List[Dict[str, Any]], model_name: str) -> np.ndarray:
        """Prepare target data for specific model."""
        targets = []
        
        for hdr10plus_data in y_data:
            if model_name == "max_cll":
                targets.append(hdr10plus_data.get("MaxCLL", 1000))
            elif model_name == "max_fall":
                targets.append(hdr10plus_data.get("MaxFALL", 100.0))
            elif model_name == "mastering_max_luminance":
                mastering_display = hdr10plus_data.get("MasteringDisplay", {})
                luminance = mastering_display.get("Luminance", {})
                targets.append(luminance.get("Max", 1000.0))
            elif model_name == "mastering_min_luminance":
                mastering_display = hdr10plus_data.get("MasteringDisplay", {})
                luminance = mastering_display.get("Luminance", {})
                targets.append(luminance.get("Min", 0.0001))
            else:
                targets.append(0.0)  # Default fallback
        
        return np.array(targets)
    
    def save_model(self, model_path: str) -> None:
        """Save trained models to file."""
        model_data = {
            "models": self.models,
            "scalers": self.scalers,
            "feature_names": self.feature_names,
            "is_trained": self.is_trained
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"ML models saved to {model_path}")
    
    def load_model(self, model_path: str) -> None:
        """Load trained models from file."""
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.models = model_data["models"]
        self.scalers = model_data["scalers"]
        self.feature_names = model_data["feature_names"]
        self.is_trained = model_data["is_trained"]
        
        logger.info(f"ML models loaded from {model_path}")
    
    def generate_synthetic_training_data(self, num_samples: int = 1000) -> List[Dict[str, Any]]:
        """Generate synthetic training data for model training."""
        logger.info(f"Generating {num_samples} synthetic training examples")
        
        training_data = []
        
        for i in range(num_samples):
            # Generate synthetic RPU data
            rpu_data = self._generate_synthetic_rpu_data()
            
            # Generate corresponding HDR10+ data using heuristics
            from .heuristic_converter import HeuristicConverter
            heuristic_converter = HeuristicConverter()
            hdr10plus_data = heuristic_converter.convert(rpu_data)
            
            # Add some noise to make it more realistic
            hdr10plus_data = self._add_noise_to_metadata(hdr10plus_data)
            
            training_data.append({
                "rpu_data": rpu_data,
                "hdr10plus_data": hdr10plus_data
            })
        
        return training_data
    
    def _generate_synthetic_rpu_data(self) -> Dict[str, Any]:
        """Generate synthetic RPU data for training."""
        return {
            "content_light_level": {
                "max_cll": np.random.randint(100, 4000),
                "max_fall": np.random.uniform(10.0, 500.0),
                "average_cll": np.random.uniform(50.0, 200.0)
            },
            "mastering_display": {
                "primaries": {
                    "red": [0.708 + np.random.normal(0, 0.01), 0.292 + np.random.normal(0, 0.01)],
                    "green": [0.170 + np.random.normal(0, 0.01), 0.797 + np.random.normal(0, 0.01)],
                    "blue": [0.131 + np.random.normal(0, 0.01), 0.046 + np.random.normal(0, 0.01)],
                    "white": [0.3127, 0.3290]
                },
                "luminance": {
                    "min": np.random.uniform(0.0001, 0.01),
                    "max": np.random.uniform(1000.0, 4000.0)
                }
            },
            "tone_mapping": {
                "trim_slopes": [np.random.uniform(0.5, 2.0) for _ in range(3)],
                "trim_offsets": [np.random.uniform(-0.5, 0.5) for _ in range(3)],
                "trim_power": [np.random.uniform(0.5, 2.0) for _ in range(3)]
            },
            "scene_info": {
                "scene_refresh_flag": np.random.choice([True, False]),
                "frame_count": np.random.randint(100, 10000)
            }
        }
    
    def _add_noise_to_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Add noise to metadata to make it more realistic."""
        # Add noise to MaxCLL
        if "MaxCLL" in metadata:
            metadata["MaxCLL"] = max(0, int(metadata["MaxCLL"] + np.random.normal(0, 50)))
        
        # Add noise to MaxFALL
        if "MaxFALL" in metadata:
            metadata["MaxFALL"] = max(0.0, metadata["MaxFALL"] + np.random.normal(0, 10.0))
        
        return metadata
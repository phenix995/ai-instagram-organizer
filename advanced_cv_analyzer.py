#!/usr/bin/env python3
"""
Advanced Computer Vision Photo Analyzer for Instagram Quality Detection
"""

import cv2
import numpy as np
from PIL import Image, ImageStat, ImageFilter
from typing import Dict, Tuple, List
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TechnicalMetrics:
    """Technical quality metrics from computer vision"""
    sharpness_score: float      # 0-10 (Laplacian variance)
    exposure_score: float       # 0-10 (histogram analysis)
    contrast_score: float       # 0-10 (RMS contrast)
    color_vibrancy: float       # 0-10 (saturation analysis)
    composition_score: float    # 0-10 (rule of thirds, leading lines)
    noise_level: float          # 0-10 (10 = low noise)
    dynamic_range: float        # 0-10 (histogram spread)
    face_quality: float         # 0-10 (if faces detected)

class AdvancedCVAnalyzer:
    """Computer vision-based photo quality analyzer"""
    
    def __init__(self):
        # Load face detection cascade
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except:
            logger.warning("Face detection not available")
            self.face_cascade = None
    
    def analyze_technical_quality(self, image_path: str) -> TechnicalMetrics:
        """Comprehensive technical analysis using computer vision"""
        
        # Load image
        img_pil = Image.open(image_path)
        img_cv = cv2.imread(image_path)
        img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Calculate all metrics
        sharpness = self._calculate_sharpness(img_gray)
        exposure = self._calculate_exposure_quality(img_pil)
        contrast = self._calculate_contrast(img_gray)
        vibrancy = self._calculate_color_vibrancy(img_pil)
        composition = self._calculate_composition_score(img_gray)
        noise = self._calculate_noise_level(img_gray)
        dynamic_range = self._calculate_dynamic_range(img_gray)
        face_quality = self._calculate_face_quality(img_cv) if self.face_cascade else 5.0
        
        return TechnicalMetrics(
            sharpness_score=sharpness,
            exposure_score=exposure,
            contrast_score=contrast,
            color_vibrancy=vibrancy,
            composition_score=composition,
            noise_level=noise,
            dynamic_range=dynamic_range,
            face_quality=face_quality
        )
    
    def _calculate_sharpness(self, img_gray: np.ndarray) -> float:
        """Calculate image sharpness using Laplacian variance"""
        laplacian_var = cv2.Laplacian(img_gray, cv2.CV_64F).var()
        # Normalize to 0-10 scale (empirically determined thresholds)
        if laplacian_var > 1000:
            return 10.0
        elif laplacian_var > 500:
            return 8.0 + (laplacian_var - 500) / 250
        elif laplacian_var > 100:
            return 5.0 + (laplacian_var - 100) / 133.33
        else:
            return max(0.0, laplacian_var / 20)
    
    def _calculate_exposure_quality(self, img_pil: Image.Image) -> float:
        """Analyze exposure quality using histogram"""
        # Convert to grayscale for luminance analysis
        gray = img_pil.convert('L')
        histogram = gray.histogram()
        
        total_pixels = sum(histogram)
        
        # Calculate percentages in different brightness ranges
        shadows = sum(histogram[0:64]) / total_pixels  # 0-25%
        midtones = sum(histogram[64:192]) / total_pixels  # 25-75%
        highlights = sum(histogram[192:256]) / total_pixels  # 75-100%
        
        # Penalize clipping (too many pure blacks or whites)
        black_clipping = histogram[0] / total_pixels
        white_clipping = histogram[255] / total_pixels
        
        # Good exposure has balanced distribution
        balance_score = 10.0 - (abs(shadows - 0.2) + abs(midtones - 0.6) + abs(highlights - 0.2)) * 10
        clipping_penalty = (black_clipping + white_clipping) * 20
        
        return max(0.0, min(10.0, balance_score - clipping_penalty))
    
    def _calculate_contrast(self, img_gray: np.ndarray) -> float:
        """Calculate RMS contrast"""
        mean_intensity = np.mean(img_gray)
        rms_contrast = np.sqrt(np.mean((img_gray - mean_intensity) ** 2))
        
        # Normalize to 0-10 scale
        normalized_contrast = min(10.0, rms_contrast / 10.0)
        return normalized_contrast
    
    def _calculate_color_vibrancy(self, img_pil: Image.Image) -> float:
        """Calculate color vibrancy and saturation"""
        if img_pil.mode != 'RGB':
            img_pil = img_pil.convert('RGB')
        
        # Convert to HSV for saturation analysis
        hsv = img_pil.convert('HSV')
        h, s, v = hsv.split()
        
        # Calculate average saturation
        sat_stats = ImageStat.Stat(s)
        avg_saturation = sat_stats.mean[0]
        
        # Calculate color diversity (number of unique colors)
        colors = img_pil.getcolors(maxcolors=256*256*256)
        if colors:
            unique_colors = len(colors)
            color_diversity = min(10.0, unique_colors / 10000)
        else:
            color_diversity = 5.0
        
        # Combine saturation and diversity
        vibrancy_score = (avg_saturation / 25.5) * 0.7 + color_diversity * 0.3
        return min(10.0, vibrancy_score)
    
    def _calculate_composition_score(self, img_gray: np.ndarray) -> float:
        """Analyze composition using rule of thirds and edge detection"""
        height, width = img_gray.shape
        
        # Rule of thirds analysis
        third_h, third_w = height // 3, width // 3
        
        # Calculate variance in each third section
        sections = [
            img_gray[0:third_h, 0:third_w],
            img_gray[0:third_h, third_w:2*third_w],
            img_gray[0:third_h, 2*third_w:width],
            img_gray[third_h:2*third_h, 0:third_w],
            img_gray[third_h:2*third_h, third_w:2*third_w],
            img_gray[third_h:2*third_h, 2*third_w:width],
            img_gray[2*third_h:height, 0:third_w],
            img_gray[2*third_h:height, third_w:2*third_w],
            img_gray[2*third_h:height, 2*third_w:width]
        ]
        
        variances = [np.var(section) for section in sections]
        
        # Good composition has varied interest across sections
        composition_balance = np.std(variances) / 1000  # Normalize
        
        # Edge detection for leading lines
        edges = cv2.Canny(img_gray, 50, 150)
        edge_density = np.sum(edges > 0) / (height * width)
        
        # Combine metrics
        composition_score = min(10.0, composition_balance * 5 + edge_density * 50)
        return composition_score
    
    def _calculate_noise_level(self, img_gray: np.ndarray) -> float:
        """Estimate noise level using high-frequency content"""
        # Apply Gaussian blur and subtract from original
        blurred = cv2.GaussianBlur(img_gray, (5, 5), 0)
        noise = cv2.absdiff(img_gray, blurred)
        
        # Calculate noise metric
        noise_level = np.mean(noise)
        
        # Convert to 0-10 scale (10 = low noise)
        noise_score = max(0.0, 10.0 - noise_level / 5.0)
        return noise_score
    
    def _calculate_dynamic_range(self, img_gray: np.ndarray) -> float:
        """Calculate dynamic range from histogram"""
        histogram = cv2.calcHist([img_gray], [0], None, [256], [0, 256])
        
        # Find 1st and 99th percentiles to ignore outliers
        total_pixels = img_gray.shape[0] * img_gray.shape[1]
        cumsum = np.cumsum(histogram.flatten())
        
        p1_idx = np.where(cumsum >= total_pixels * 0.01)[0][0]
        p99_idx = np.where(cumsum >= total_pixels * 0.99)[0][0]
        
        dynamic_range = p99_idx - p1_idx
        
        # Normalize to 0-10 scale
        return min(10.0, dynamic_range / 25.5)
    
    def _calculate_face_quality(self, img_cv: np.ndarray) -> float:
        """Analyze face quality if faces are present"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return 5.0  # Neutral score for no faces
        
        face_scores = []
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            
            # Face size score (larger faces generally better for Instagram)
            face_area = w * h
            total_area = img_cv.shape[0] * img_cv.shape[1]
            size_ratio = face_area / total_area
            size_score = min(10.0, size_ratio * 100)  # Optimal around 10% of image
            
            # Face sharpness
            face_sharpness = cv2.Laplacian(face_roi, cv2.CV_64F).var()
            sharpness_score = min(10.0, face_sharpness / 100)
            
            # Face positioning (rule of thirds)
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            img_center_x = img_cv.shape[1] // 2
            img_center_y = img_cv.shape[0] // 2
            
            # Distance from center (some offset is good)
            center_distance = np.sqrt((face_center_x - img_center_x)**2 + (face_center_y - img_center_y)**2)
            max_distance = np.sqrt(img_center_x**2 + img_center_y**2)
            position_score = 10.0 - (center_distance / max_distance) * 5  # Slight penalty for being too far from center
            
            face_score = (size_score * 0.4 + sharpness_score * 0.4 + position_score * 0.2)
            face_scores.append(face_score)
        
        return np.mean(face_scores)

def integrate_cv_analysis(image_path: str, existing_analysis: Dict) -> Dict:
    """Integrate computer vision analysis with existing AI analysis"""
    cv_analyzer = AdvancedCVAnalyzer()
    
    try:
        cv_metrics = cv_analyzer.analyze_technical_quality(image_path)
        
        # Enhance existing analysis with CV metrics
        enhanced_analysis = existing_analysis.copy()
        
        # Override technical scores with CV analysis
        enhanced_analysis['technical_score'] = (
            cv_metrics.sharpness_score * 0.25 +
            cv_metrics.exposure_score * 0.20 +
            cv_metrics.contrast_score * 0.15 +
            cv_metrics.composition_score * 0.20 +
            cv_metrics.noise_level * 0.10 +
            cv_metrics.dynamic_range * 0.10
        )
        
        # Boost visual appeal with color vibrancy
        enhanced_analysis['visual_appeal'] = min(10.0, 
            existing_analysis.get('visual_appeal', 5.0) * 0.7 + 
            cv_metrics.color_vibrancy * 0.3
        )
        
        # Add CV-specific metrics
        enhanced_analysis['cv_metrics'] = {
            'sharpness': cv_metrics.sharpness_score,
            'exposure': cv_metrics.exposure_score,
            'contrast': cv_metrics.contrast_score,
            'vibrancy': cv_metrics.color_vibrancy,
            'composition': cv_metrics.composition_score,
            'noise_level': cv_metrics.noise_level,
            'dynamic_range': cv_metrics.dynamic_range,
            'face_quality': cv_metrics.face_quality
        }
        
        return enhanced_analysis
        
    except Exception as e:
        logger.error(f"CV analysis failed for {image_path}: {e}")
        return existing_analysis
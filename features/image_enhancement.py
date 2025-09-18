# Image Enhancement Features

import os
from typing import Dict
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def auto_enhance_image(image_path: str, output_path: str) -> bool:
    """Automatically enhance image for Instagram"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Auto-adjust brightness and contrast
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.1)  # Slight brightness boost
            
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.15)  # Increase contrast
            
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)  # Boost saturation
            
            # Slight sharpening
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
            
            img.save(output_path, "JPEG", quality=95)
            return True
            
    except Exception as e:
        logger.error(f"Could not enhance image {image_path}: {e}")
        return False

def create_instagram_formats(image_path: str, output_dir: str) -> Dict[str, str]:
    """Create multiple Instagram-optimized formats"""
    formats = {}
    
    try:
        with Image.open(image_path) as img:
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            
            # Square format (1:1)
            square_img = crop_to_square(img)
            square_path = os.path.join(output_dir, f"{base_name}_square.jpg")
            square_img.save(square_path, "JPEG", quality=95)
            formats['square'] = square_path
            
            # Story format (9:16)
            story_img = crop_to_story(img)
            story_path = os.path.join(output_dir, f"{base_name}_story.jpg")
            story_img.save(story_path, "JPEG", quality=95)
            formats['story'] = story_path
            
            # Reel format (9:16 with padding)
            reel_img = create_reel_format(img)
            reel_path = os.path.join(output_dir, f"{base_name}_reel.jpg")
            reel_img.save(reel_path, "JPEG", quality=95)
            formats['reel'] = reel_path
            
    except Exception as e:
        logger.error(f"Could not create formats for {image_path}: {e}")
    
    return formats

def crop_to_square(img: Image.Image) -> Image.Image:
    """Crop image to square format"""
    width, height = img.size
    size = min(width, height)
    
    left = (width - size) // 2
    top = (height - size) // 2
    right = left + size
    bottom = top + size
    
    return img.crop((left, top, right, bottom))

def crop_to_story(img: Image.Image) -> Image.Image:
    """Crop image to story format (9:16)"""
    width, height = img.size
    target_ratio = 9/16
    
    if width/height > target_ratio:
        # Image is too wide
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        return img.crop((left, 0, left + new_width, height))
    else:
        # Image is too tall
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        return img.crop((0, top, width, top + new_height))
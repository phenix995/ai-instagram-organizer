#!/usr/bin/env python3
"""
Enhanced Instagram Photo Analyzer with Advanced Categorization and Selection
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, Counter
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class PhotoScore:
    """Comprehensive photo scoring system"""
    technical_quality: float  # 0-10
    visual_appeal: float      # 0-10
    engagement_potential: float # 0-10
    uniqueness: float         # 0-10
    story_value: float        # 0-10
    composite_score: float    # Weighted average
    tier: str                 # premium, excellent, good, average, poor
    
    def __post_init__(self):
        # Calculate weighted composite score
        weights = {
            'technical_quality': 0.15,
            'visual_appeal': 0.25,
            'engagement_potential': 0.30,
            'uniqueness': 0.20,
            'story_value': 0.10
        }
        
        self.composite_score = (
            self.technical_quality * weights['technical_quality'] +
            self.visual_appeal * weights['visual_appeal'] +
            self.engagement_potential * weights['engagement_potential'] +
            self.uniqueness * weights['uniqueness'] +
            self.story_value * weights['story_value']
        )
        
        # Determine tier based on composite score
        if self.composite_score >= 8.5:
            self.tier = "premium"
        elif self.composite_score >= 7.5:
            self.tier = "excellent"
        elif self.composite_score >= 6.0:
            self.tier = "good"
        elif self.composite_score >= 4.0:
            self.tier = "average"
        else:
            self.tier = "poor"

@dataclass
class PhotoCategory:
    """Enhanced photo categorization"""
    primary: str      # landscape, portrait, food, architecture, etc.
    secondary: str    # sunset, beach, street_art, etc.
    mood: str         # peaceful, energetic, romantic, etc.
    setting: str      # indoor, outdoor, urban, nature, etc.
    time_of_day: str  # golden_hour, blue_hour, midday, night, etc.
    season: str       # spring, summer, fall, winter, unknown
    people_count: int # 0=none, 1=solo, 2-5=small_group, 6+=large_group
    
class EnhancedPhotoAnalyzer:
    """Advanced photo analysis with sophisticated categorization"""
    
    def __init__(self):
        self.category_weights = {
            'landscape': {'visual_appeal': 1.2, 'uniqueness': 1.1},
            'portrait': {'engagement_potential': 1.3, 'story_value': 1.2},
            'food': {'visual_appeal': 1.3, 'engagement_potential': 1.1},
            'architecture': {'technical_quality': 1.2, 'uniqueness': 1.1},
            'lifestyle': {'engagement_potential': 1.2, 'story_value': 1.3},
            'action': {'uniqueness': 1.3, 'engagement_potential': 1.2},
            'macro': {'technical_quality': 1.3, 'uniqueness': 1.2},
            'street': {'story_value': 1.3, 'uniqueness': 1.2},
            'travel': {'engagement_potential': 1.2, 'story_value': 1.1},
            'nature': {'visual_appeal': 1.1, 'uniqueness': 1.1}
        }
    
    def analyze_photo_advanced(self, analysis_data: Dict) -> Tuple[PhotoScore, PhotoCategory]:
        """Convert AI analysis to structured scoring and categorization"""
        
        # Extract scores with fallbacks
        technical = analysis_data.get('technical_score', 5.0)
        visual = analysis_data.get('visual_appeal', 5.0)
        engagement = analysis_data.get('engagement_score', 5.0)
        uniqueness = analysis_data.get('uniqueness', 5.0)
        story = analysis_data.get('story_potential', 5.0)
        
        # Create category
        category = PhotoCategory(
            primary=analysis_data.get('category', 'unknown'),
            secondary=analysis_data.get('subcategory', 'unknown'),
            mood=analysis_data.get('mood', 'neutral'),
            setting=self._determine_setting(analysis_data),
            time_of_day=self._determine_time_of_day(analysis_data),
            season=self._determine_season(analysis_data),
            people_count=self._determine_people_count(analysis_data)
        )
        
        # Apply category-specific weights
        if category.primary in self.category_weights:
            weights = self.category_weights[category.primary]
            technical *= weights.get('technical_quality', 1.0)
            visual *= weights.get('visual_appeal', 1.0)
            engagement *= weights.get('engagement_potential', 1.0)
            uniqueness *= weights.get('uniqueness', 1.0)
            story *= weights.get('story_value', 1.0)
        
        # Cap at 10.0
        technical = min(technical, 10.0)
        visual = min(visual, 10.0)
        engagement = min(engagement, 10.0)
        uniqueness = min(uniqueness, 10.0)
        story = min(story, 10.0)
        
        score = PhotoScore(
            technical_quality=technical,
            visual_appeal=visual,
            engagement_potential=engagement,
            uniqueness=uniqueness,
            story_value=story,
            composite_score=0,  # Will be calculated in __post_init__
            tier=""  # Will be calculated in __post_init__
        )
        
        return score, category
    
    def _determine_setting(self, analysis: Dict) -> str:
        """Determine photo setting from analysis"""
        location = (analysis.get('location') or '').lower()
        category = (analysis.get('category') or '').lower()
        
        if any(word in location for word in ['indoor', 'inside', 'room', 'kitchen', 'restaurant']):
            return 'indoor'
        elif any(word in location for word in ['city', 'urban', 'street', 'building']):
            return 'urban'
        elif any(word in location for word in ['nature', 'forest', 'mountain', 'beach', 'lake']):
            return 'nature'
        else:
            return 'outdoor'
    
    def _determine_time_of_day(self, analysis: Dict) -> str:
        """Determine time of day from analysis"""
        strengths = ' '.join(analysis.get('strengths', [])).lower()
        location = (analysis.get('location') or '').lower()
        
        if any(word in strengths + location for word in ['golden hour', 'sunset', 'sunrise']):
            return 'golden_hour'
        elif any(word in strengths + location for word in ['blue hour', 'twilight', 'dusk']):
            return 'blue_hour'
        elif any(word in strengths + location for word in ['night', 'dark', 'evening']):
            return 'night'
        elif any(word in strengths + location for word in ['bright', 'midday', 'noon']):
            return 'midday'
        else:
            return 'unknown'
    
    def _determine_season(self, analysis: Dict) -> str:
        """Determine season from analysis"""
        location = (analysis.get('location') or '').lower()
        mood = (analysis.get('mood') or '').lower()
        
        if any(word in location + mood for word in ['snow', 'winter', 'cold', 'frost']):
            return 'winter'
        elif any(word in location + mood for word in ['spring', 'bloom', 'fresh', 'green']):
            return 'spring'
        elif any(word in location + mood for word in ['summer', 'beach', 'hot', 'sunny']):
            return 'summer'
        elif any(word in location + mood for word in ['fall', 'autumn', 'leaves', 'orange']):
            return 'fall'
        else:
            return 'unknown'
    
    def _determine_people_count(self, analysis: Dict) -> int:
        """Determine number of people from analysis"""
        category = (analysis.get('category') or '').lower()
        subcategory = (analysis.get('subcategory') or '').lower()
        location = (analysis.get('location') or '').lower()
        
        if category == 'portrait':
            if any(word in subcategory + location for word in ['group', 'family', 'friends']):
                return 3  # Small group
            else:
                return 1  # Solo portrait
        elif any(word in subcategory + location for word in ['crowd', 'party', 'event']):
            return 6  # Large group
        elif any(word in subcategory + location for word in ['couple', 'pair']):
            return 2
        else:
            return 0  # No people or unknown

class SmartPostCreator:
    """Advanced post creation with diversity optimization"""
    
    def __init__(self, post_size: int = 10):
        self.post_size = post_size
        self.diversity_weights = {
            'category_diversity': 0.3,
            'mood_diversity': 0.2,
            'time_diversity': 0.2,
            'setting_diversity': 0.15,
            'quality_consistency': 0.15
        }
    
    def create_optimized_posts(self, photos_data: List[Dict]) -> List[List[Dict]]:
        """Create posts with optimal diversity and quality"""
        
        # Filter and categorize photos
        premium_photos = [p for p in photos_data if p['score'].tier == 'premium']
        excellent_photos = [p for p in photos_data if p['score'].tier == 'excellent']
        good_photos = [p for p in photos_data if p['score'].tier == 'good']
        
        logger.info(f"Photo tiers: {len(premium_photos)} premium, {len(excellent_photos)} excellent, {len(good_photos)} good")
        
        posts = []
        
        # Strategy 1: Premium posts (best of the best)
        if len(premium_photos) >= self.post_size:
            premium_posts = self._create_diverse_posts(premium_photos, max_posts=3)
            posts.extend(premium_posts)
        
        # Strategy 2: Mixed excellence posts
        mixed_pool = excellent_photos + premium_photos
        if len(mixed_pool) >= self.post_size:
            mixed_posts = self._create_diverse_posts(mixed_pool, max_posts=5)
            posts.extend(mixed_posts)
        
        # Strategy 3: Theme-based posts
        theme_posts = self._create_theme_posts(good_photos + excellent_photos)
        posts.extend(theme_posts)
        
        # Strategy 4: Chronological posts from remaining
        remaining_photos = [p for p in photos_data if not self._is_photo_used(p, posts)]
        if len(remaining_photos) >= self.post_size:
            chrono_posts = self._create_chronological_posts(remaining_photos)
            posts.extend(chrono_posts)
        
        return posts
    
    def _create_diverse_posts(self, photos: List[Dict], max_posts: int = None) -> List[List[Dict]]:
        """Create posts optimized for diversity"""
        if len(photos) < self.post_size:
            return []
        
        posts = []
        available_photos = photos.copy()
        
        post_count = min(len(photos) // self.post_size, max_posts or float('inf'))
        
        for _ in range(int(post_count)):
            if len(available_photos) < self.post_size:
                break
                
            post = self._select_diverse_photo_set(available_photos)
            if post:
                posts.append(post)
                # Remove selected photos from available pool
                available_photos = [p for p in available_photos if p not in post]
        
        return posts
    
    def _select_diverse_photo_set(self, photos: List[Dict]) -> List[Dict]:
        """Select a diverse set of photos for one post"""
        if len(photos) < self.post_size:
            return []
        
        # Start with highest scoring photo
        selected = [max(photos, key=lambda p: p['score'].composite_score)]
        remaining = [p for p in photos if p != selected[0]]
        
        # Select remaining photos to maximize diversity
        while len(selected) < self.post_size and remaining:
            best_photo = None
            best_diversity_score = -1
            
            for candidate in remaining:
                diversity_score = self._calculate_diversity_score(selected, candidate)
                if diversity_score > best_diversity_score:
                    best_diversity_score = diversity_score
                    best_photo = candidate
            
            if best_photo:
                selected.append(best_photo)
                remaining.remove(best_photo)
        
        return selected
    
    def _calculate_diversity_score(self, selected_photos: List[Dict], candidate: Dict) -> float:
        """Calculate how much diversity a candidate photo adds"""
        if not selected_photos:
            return candidate['score'].composite_score
        
        # Category diversity
        selected_categories = [p['category'].primary for p in selected_photos]
        category_diversity = 1.0 if candidate['category'].primary not in selected_categories else 0.3
        
        # Mood diversity
        selected_moods = [p['category'].mood for p in selected_photos]
        mood_diversity = 1.0 if candidate['category'].mood not in selected_moods else 0.5
        
        # Time diversity
        selected_times = [p['category'].time_of_day for p in selected_photos]
        time_diversity = 1.0 if candidate['category'].time_of_day not in selected_times else 0.4
        
        # Setting diversity
        selected_settings = [p['category'].setting for p in selected_photos]
        setting_diversity = 1.0 if candidate['category'].setting not in selected_settings else 0.6
        
        # Quality consistency (prefer similar quality levels)
        avg_quality = np.mean([p['score'].composite_score for p in selected_photos])
        quality_consistency = 1.0 - abs(candidate['score'].composite_score - avg_quality) / 10.0
        
        # Weighted diversity score
        diversity_score = (
            category_diversity * self.diversity_weights['category_diversity'] +
            mood_diversity * self.diversity_weights['mood_diversity'] +
            time_diversity * self.diversity_weights['time_diversity'] +
            setting_diversity * self.diversity_weights['setting_diversity'] +
            quality_consistency * self.diversity_weights['quality_consistency']
        )
        
        # Boost by photo quality
        return diversity_score * (candidate['score'].composite_score / 10.0)
    
    def _create_theme_posts(self, photos: List[Dict]) -> List[List[Dict]]:
        """Create posts based on themes/categories"""
        # Group by primary category
        category_groups = defaultdict(list)
        for photo in photos:
            category_groups[photo['category'].primary].append(photo)
        
        theme_posts = []
        
        # Create posts for categories with enough photos
        for category, category_photos in category_groups.items():
            if len(category_photos) >= self.post_size:
                # Sort by quality and take best ones
                category_photos.sort(key=lambda p: p['score'].composite_score, reverse=True)
                
                # Create posts from this category
                for i in range(0, len(category_photos), self.post_size):
                    post_photos = category_photos[i:i + self.post_size]
                    if len(post_photos) == self.post_size:
                        theme_posts.append(post_photos)
        
        return theme_posts
    
    def _create_chronological_posts(self, photos: List[Dict]) -> List[List[Dict]]:
        """Create chronological posts from remaining photos"""
        # Sort by date
        photos.sort(key=lambda p: p['datetime'])
        
        posts = []
        for i in range(0, len(photos), self.post_size):
            post_photos = photos[i:i + self.post_size]
            if len(post_photos) == self.post_size:
                posts.append(post_photos)
        
        return posts
    
    def _is_photo_used(self, photo: Dict, posts: List[List[Dict]]) -> bool:
        """Check if photo is already used in any post"""
        for post in posts:
            if photo in post:
                return True
        return False

def generate_enhanced_analysis_prompt() -> str:
    """Generate the enhanced AI analysis prompt"""
    return """You are an expert Instagram content strategist and photographer. Analyze this image comprehensively and provide a JSON object with these exact keys:

TECHNICAL QUALITY (Rate 1-10):
- "technical_score": Overall technical quality (focus, exposure, composition, lighting, noise)
- "visual_appeal": Visual aesthetics (colors, balance, wow factor, artistic merit)

CONTENT ANALYSIS:
- "category": Primary category (landscape, portrait, food, architecture, lifestyle, action, macro, street, travel, nature, abstract, wildlife)
- "subcategory": Specific type (sunset, beach, mountain, city_skyline, group_photo, street_art, etc.)
- "location": Describe the location/setting in detail
- "mood": Emotional tone (peaceful, energetic, romantic, adventurous, cozy, dramatic, mysterious, joyful, melancholic)

INSTAGRAM POTENTIAL (Rate 1-10):
- "engagement_score": Likely engagement (likes, comments, shares, saves)
- "story_potential": Storytelling and narrative value
- "uniqueness": How unique/standout this image is
- "viral_potential": Potential for viral spread or high reach

ENGAGEMENT FACTORS:
- "strengths": List 2-4 strongest elements (e.g., "dramatic lighting", "unique perspective", "vibrant colors", "emotional connection")
- "weaknesses": List 1-2 areas for improvement (e.g., "slightly blurry", "cluttered composition", "poor lighting")

POSTING STRATEGY:
- "best_time": Suggested posting time ("golden_hour", "morning", "afternoon", "evening", "weekend", "weekday")
- "caption_style": Suggested style ("storytelling", "inspirational", "informative", "casual", "poetic", "humorous")
- "hashtag_focus": Primary hashtag category ("travel", "lifestyle", "nature", "food", "portrait", "architecture")

ADDITIONAL CONTEXT:
- "season_indicators": Any seasonal elements visible
- "people_present": Estimate number of people (0, 1, 2-5, 6+)
- "time_of_day_indicators": Visual clues about time (lighting, shadows, etc.)

Return ONLY the JSON object, no other text. Be precise and honest in your ratings."""

# Example usage and integration functions
def integrate_enhanced_analyzer(config, analyzed_data: List[Dict]) -> List[Dict]:
    """Integrate enhanced analyzer with existing system and all advanced features"""
    from advanced_cv_analyzer import integrate_cv_analysis
    from instagram_engagement_predictor import enhance_with_engagement_prediction
    from semantic_context_analyzer import apply_semantic_contextual_filtering
    
    analyzer = EnhancedPhotoAnalyzer()
    enhanced_data = []
    
    logger.info("Starting enhanced analysis with computer vision and engagement prediction...")
    
    for data in analyzed_data:
        if data and data.get('analysis'):
            # Step 1: Enhance with computer vision analysis
            cv_enhanced_analysis = integrate_cv_analysis(data['path'], data['analysis'])
            
            # Step 2: Create enhanced scoring and categorization
            score, category = analyzer.analyze_photo_advanced(cv_enhanced_analysis)
            
            # Step 3: Create enhanced photo data
            enhanced_photo = {
                'path': data['path'],
                'datetime': data['datetime'],
                'analysis': cv_enhanced_analysis,
                'score': score,
                'category': category,
                'instagram_worthy': score.tier in ['premium', 'excellent'] or score.composite_score >= config.enhanced_algorithm.quality_thresholds.minimum_posting_score
            }
            
            # Step 4: Add engagement prediction
            enhanced_photo = enhance_with_engagement_prediction(enhanced_photo)
            
            enhanced_data.append(enhanced_photo)
    
    # Step 5: Apply semantic contextual filtering
    if config.contextual_filtering.enable_contextual_filtering:
        enhanced_data = apply_semantic_contextual_filtering(
            enhanced_data, 
            config.contextual_filtering.max_photos_per_context
        )
    
    logger.info(f"Enhanced analysis complete: {len(enhanced_data)} photos processed")
    return enhanced_data

def create_smart_posts(enhanced_data: List[Dict], config) -> List[List[Dict]]:
    """Create smart posts using enhanced data"""
    post_creator = SmartPostCreator(config.post_size)
    
    # Filter only Instagram-worthy photos
    worthy_photos = [p for p in enhanced_data if p['instagram_worthy']]
    
    if not worthy_photos:
        logger.warning("No Instagram-worthy photos found with enhanced analysis")
        return []
    
    logger.info(f"Creating smart posts from {len(worthy_photos)} worthy photos")
    posts = post_creator.create_optimized_posts(worthy_photos)
    
    return posts
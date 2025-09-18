#!/usr/bin/env python3
"""
Instagram Engagement Prediction Model
Based on real Instagram performance patterns and trends
"""

import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EngagementFactors:
    """Instagram-specific engagement factors"""
    optimal_posting_time: float     # 0-10 based on time of day
    hashtag_competition: float      # 0-10 (10 = low competition)
    trend_alignment: float          # 0-10 (alignment with current trends)
    audience_match: float           # 0-10 (match with target audience)
    viral_potential: float          # 0-10 (likelihood of viral spread)
    story_shareability: float       # 0-10 (likelihood of story shares)
    save_potential: float           # 0-10 (likelihood of saves)

class InstagramEngagementPredictor:
    """Predict Instagram engagement based on current platform trends"""
    
    def __init__(self):
        # Instagram algorithm preferences (updated for 2024/2025)
        self.algorithm_weights = {
            'recency': 0.15,           # How recent the post is
            'engagement_velocity': 0.25, # Early engagement rate
            'relationship': 0.20,       # User relationship strength
            'interest': 0.25,          # Content interest alignment
            'time_spent': 0.15         # Time spent viewing
        }
        
        # Content type performance multipliers
        self.content_multipliers = {
            'portrait': 1.3,           # Faces perform well
            'landscape': 0.9,          # Lower engagement typically
            'food': 1.4,               # High engagement category
            'lifestyle': 1.2,          # Good performance
            'travel': 1.1,             # Solid performance
            'architecture': 0.8,       # Lower engagement
            'nature': 1.0,             # Baseline
            'street': 1.1,             # Good storytelling potential
            'action': 1.3,             # High engagement
            'macro': 0.9               # Niche audience
        }
        
        # Optimal posting times (hour of day, 0-23)
        self.optimal_times = {
            'weekday': [6, 7, 8, 11, 12, 17, 18, 19, 20, 21],  # Peak engagement hours
            'weekend': [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        }
        
        # Current Instagram trends (update regularly)
        self.trending_elements = {
            'golden_hour': 1.4,        # Always popular
            'authentic_moments': 1.3,   # Raw, unfiltered content
            'behind_scenes': 1.2,      # Story-driven content
            'seasonal_content': 1.1,    # Timely content
            'user_generated': 1.3,     # Community content
            'educational': 1.2,        # Value-driven content
            'emotional_story': 1.4,    # Emotional connection
            'local_spots': 1.1,        # Local discovery
            'sustainability': 1.2,     # Environmental consciousness
            'wellness': 1.3            # Health and wellness
        }
    
    def predict_engagement(self, photo_data: Dict, posting_time: datetime = None) -> EngagementFactors:
        """Predict Instagram engagement for a photo"""
        
        if posting_time is None:
            posting_time = datetime.now()
        
        # Calculate each engagement factor
        time_score = self._calculate_optimal_time_score(posting_time)
        hashtag_score = self._calculate_hashtag_competition(photo_data)
        trend_score = self._calculate_trend_alignment(photo_data)
        audience_score = self._calculate_audience_match(photo_data)
        viral_score = self._calculate_viral_potential(photo_data)
        story_score = self._calculate_story_shareability(photo_data)
        save_score = self._calculate_save_potential(photo_data)
        
        return EngagementFactors(
            optimal_posting_time=time_score,
            hashtag_competition=hashtag_score,
            trend_alignment=trend_score,
            audience_match=audience_score,
            viral_potential=viral_score,
            story_shareability=story_score,
            save_potential=save_score
        )
    
    def _calculate_optimal_time_score(self, posting_time: datetime) -> float:
        """Calculate score based on optimal posting time"""
        hour = posting_time.hour
        is_weekend = posting_time.weekday() >= 5
        
        optimal_hours = self.optimal_times['weekend' if is_weekend else 'weekday']
        
        if hour in optimal_hours:
            # Peak hours get full score
            return 10.0
        elif hour in [h-1 for h in optimal_hours] or hour in [h+1 for h in optimal_hours]:
            # Adjacent hours get good score
            return 7.5
        else:
            # Off-peak hours get lower score
            return 4.0
    
    def _calculate_hashtag_competition(self, photo_data: Dict) -> float:
        """Estimate hashtag competition level"""
        category = photo_data.get('category', {}).get('primary', 'unknown')
        
        # High competition categories (harder to get discovered)
        high_competition = ['food', 'travel', 'lifestyle', 'portrait']
        medium_competition = ['nature', 'architecture', 'street']
        low_competition = ['macro', 'abstract', 'action']
        
        if category in high_competition:
            base_score = 4.0
        elif category in medium_competition:
            base_score = 6.5
        else:
            base_score = 8.0
        
        # Adjust based on uniqueness
        uniqueness = photo_data.get('score', {}).get('uniqueness', 5.0)
        uniqueness_bonus = (uniqueness - 5.0) * 0.5
        
        return min(10.0, max(0.0, base_score + uniqueness_bonus))
    
    def _calculate_trend_alignment(self, photo_data: Dict) -> float:
        """Calculate alignment with current Instagram trends"""
        analysis = photo_data.get('analysis', {})
        category = photo_data.get('category', {})
        
        trend_score = 5.0  # Base score
        
        # Check for trending elements
        strengths = ' '.join(analysis.get('strengths', [])).lower()
        location = (analysis.get('location') or '').lower()
        mood = (category.get('mood') or '').lower()
        time_of_day = (category.get('time_of_day') or '').lower()
        
        content_text = f"{strengths} {location} {mood} {time_of_day}"
        
        for trend_element, multiplier in self.trending_elements.items():
            if trend_element.replace('_', ' ') in content_text:
                trend_score *= multiplier
                break
        
        # Seasonal bonus
        current_month = datetime.now().month
        if current_month in [12, 1, 2] and 'winter' in content_text:
            trend_score *= 1.2
        elif current_month in [3, 4, 5] and 'spring' in content_text:
            trend_score *= 1.2
        elif current_month in [6, 7, 8] and 'summer' in content_text:
            trend_score *= 1.2
        elif current_month in [9, 10, 11] and ('fall' in content_text or 'autumn' in content_text):
            trend_score *= 1.2
        
        return min(10.0, trend_score)
    
    def _calculate_audience_match(self, photo_data: Dict) -> float:
        """Calculate how well photo matches target audience"""
        category = photo_data.get('category', {})
        analysis = photo_data.get('analysis', {})
        
        primary_category = category.get('primary', 'unknown')
        mood = category.get('mood', 'neutral')
        people_count = category.get('people_count', 0)
        
        # Base score from category performance
        base_score = self.content_multipliers.get(primary_category, 1.0) * 5.0
        
        # People in photos generally perform better
        if people_count > 0:
            people_bonus = min(2.0, people_count * 0.5)
            base_score += people_bonus
        
        # Emotional content performs better
        emotional_moods = ['joyful', 'romantic', 'adventurous', 'peaceful', 'dramatic']
        if mood in emotional_moods:
            base_score += 1.0
        
        # Story potential adds engagement
        story_potential = analysis.get('story_potential', 5.0)
        story_bonus = (story_potential - 5.0) * 0.3
        base_score += story_bonus
        
        return min(10.0, max(0.0, base_score))
    
    def _calculate_viral_potential(self, photo_data: Dict) -> float:
        """Calculate potential for viral spread"""
        analysis = photo_data.get('analysis', {})
        category = photo_data.get('category', {})
        score = photo_data.get('score', {})
        
        # Base viral potential from uniqueness and visual appeal
        uniqueness = score.get('uniqueness', 5.0)
        visual_appeal = score.get('visual_appeal', 5.0)
        
        viral_base = (uniqueness * 0.6 + visual_appeal * 0.4)
        
        # Viral content characteristics
        viral_multiplier = 1.0
        
        # Unexpected or surprising content
        if uniqueness > 8.0:
            viral_multiplier *= 1.3
        
        # Emotional impact
        mood = category.get('mood', 'neutral')
        if mood in ['dramatic', 'joyful', 'mysterious', 'adventurous']:
            viral_multiplier *= 1.2
        
        # Visual wow factor
        if visual_appeal > 8.5:
            viral_multiplier *= 1.2
        
        # Story potential
        story_potential = analysis.get('story_potential', 5.0)
        if story_potential > 8.0:
            viral_multiplier *= 1.1
        
        return min(10.0, viral_base * viral_multiplier)
    
    def _calculate_story_shareability(self, photo_data: Dict) -> float:
        """Calculate likelihood of being shared to stories"""
        category = photo_data.get('category', {})
        analysis = photo_data.get('analysis', {})
        
        # Story-friendly content types
        story_friendly_categories = ['lifestyle', 'food', 'travel', 'portrait']
        primary_category = category.get('primary', 'unknown')
        
        if primary_category in story_friendly_categories:
            base_score = 7.5
        else:
            base_score = 5.0
        
        # People in photos are more shareable
        people_count = category.get('people_count', 0)
        if people_count > 0:
            base_score += min(2.0, people_count * 0.5)
        
        # Relatable content is more shareable
        mood = category.get('mood', 'neutral')
        relatable_moods = ['joyful', 'cozy', 'peaceful', 'adventurous']
        if mood in relatable_moods:
            base_score += 1.0
        
        return min(10.0, base_score)
    
    def _calculate_save_potential(self, photo_data: Dict) -> float:
        """Calculate likelihood of being saved"""
        category = photo_data.get('category', {})
        analysis = photo_data.get('analysis', {})
        score = photo_data.get('score', {})
        
        # Save-worthy content types
        save_worthy_categories = ['food', 'travel', 'architecture', 'nature']
        primary_category = category.get('primary', 'unknown')
        
        if primary_category in save_worthy_categories:
            base_score = 7.0
        else:
            base_score = 5.0
        
        # High visual appeal gets saved
        visual_appeal = score.get('visual_appeal', 5.0)
        if visual_appeal > 8.0:
            base_score += 2.0
        elif visual_appeal > 7.0:
            base_score += 1.0
        
        # Inspirational content gets saved
        mood = category.get('mood', 'neutral')
        if mood in ['peaceful', 'romantic', 'adventurous', 'dramatic']:
            base_score += 1.0
        
        # Unique content gets saved for reference
        uniqueness = score.get('uniqueness', 5.0)
        if uniqueness > 8.0:
            base_score += 1.5
        
        return min(10.0, base_score)
    
    def calculate_overall_engagement_score(self, engagement_factors: EngagementFactors) -> float:
        """Calculate overall predicted engagement score"""
        weights = {
            'optimal_posting_time': 0.15,
            'hashtag_competition': 0.10,
            'trend_alignment': 0.20,
            'audience_match': 0.25,
            'viral_potential': 0.15,
            'story_shareability': 0.10,
            'save_potential': 0.05
        }
        
        overall_score = (
            engagement_factors.optimal_posting_time * weights['optimal_posting_time'] +
            engagement_factors.hashtag_competition * weights['hashtag_competition'] +
            engagement_factors.trend_alignment * weights['trend_alignment'] +
            engagement_factors.audience_match * weights['audience_match'] +
            engagement_factors.viral_potential * weights['viral_potential'] +
            engagement_factors.story_shareability * weights['story_shareability'] +
            engagement_factors.save_potential * weights['save_potential']
        )
        
        return min(10.0, overall_score)

def enhance_with_engagement_prediction(photo_data: Dict) -> Dict:
    """Enhance photo data with Instagram engagement prediction"""
    predictor = InstagramEngagementPredictor()
    
    try:
        engagement_factors = predictor.predict_engagement(photo_data)
        overall_engagement = predictor.calculate_overall_engagement_score(engagement_factors)
        
        # Update the photo's engagement score
        enhanced_data = photo_data.copy()
        if 'score' in enhanced_data:
            # Blend AI engagement score with prediction
            ai_engagement = enhanced_data['score'].engagement_potential
            blended_engagement = (ai_engagement * 0.4 + overall_engagement * 0.6)
            enhanced_data['score'].engagement_potential = blended_engagement
        
        # Add detailed engagement prediction
        enhanced_data['engagement_prediction'] = {
            'overall_score': overall_engagement,
            'factors': engagement_factors,
            'recommended_posting_times': predictor.optimal_times,
            'category_multiplier': predictor.content_multipliers.get(
                photo_data.get('category', {}).get('primary', 'unknown'), 1.0
            )
        }
        
        return enhanced_data
        
    except Exception as e:
        logger.error(f"Engagement prediction failed: {e}")
        return photo_data
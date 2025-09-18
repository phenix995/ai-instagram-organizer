# Advanced Hashtag Intelligence

import requests
from collections import Counter
import re
from typing import List, Dict

class HashtagOptimizer:
    def __init__(self):
        self.trending_hashtags = self.load_trending_hashtags()
        self.niche_hashtags = self.load_niche_hashtags()
    
    def optimize_hashtags(self, generated_hashtags: List[str], theme: str, location: str) -> Dict:
        """Optimize hashtags for better reach and engagement"""
        
        # Categorize hashtags by size/competition
        optimized = {
            'high_competition': [],    # 1M+ posts
            'medium_competition': [],  # 100K-1M posts  
            'low_competition': [],     # <100K posts
            'trending': [],
            'niche': [],
            'location_based': []
        }
        
        for hashtag in generated_hashtags:
            category = self.categorize_hashtag(hashtag, theme, location)
            optimized[category].append(hashtag)
        
        # Add strategic hashtags
        optimized['trending'].extend(self.get_trending_for_theme(theme))
        optimized['location_based'].extend(self.get_location_hashtags(location))
        optimized['niche'].extend(self.get_niche_hashtags(theme))
        
        return self.balance_hashtag_mix(optimized)
    
    def categorize_hashtag(self, hashtag: str, theme: str, location: str) -> str:
        """Categorize hashtag by competition level"""
        # This would ideally connect to Instagram API or hashtag databases
        # For now, using heuristics based on hashtag patterns
        
        if len(hashtag) < 6 or hashtag in ['love', 'instagood', 'photooftheday']:
            return 'high_competition'
        elif len(hashtag) < 12:
            return 'medium_competition'
        else:
            return 'low_competition'
    
    def get_trending_for_theme(self, theme: str) -> List[str]:
        """Get trending hashtags for specific theme"""
        theme_trends = {
            'travel': ['wanderlust2024', 'travelgram', 'exploremore'],
            'food': ['foodie', 'instafood', 'yummy'],
            'nature': ['naturephotography', 'outdoors', 'wilderness'],
            'city': ['citylife', 'urban', 'architecture']
        }
        
        return theme_trends.get(theme.lower(), [])
    
    def get_location_hashtags(self, location: str) -> List[str]:
        """Generate location-based hashtags"""
        if not location or location == 'Unknown':
            return []
        
        # Extract city/state/country from location description
        location_tags = []
        words = re.findall(r'\b[A-Z][a-z]+\b', location)
        
        for word in words:
            if len(word) > 3:  # Avoid short words
                location_tags.append(word.lower())
                location_tags.append(f"visit{word.lower()}")
        
        return location_tags[:3]  # Limit to 3 location tags
    
    def balance_hashtag_mix(self, categorized: Dict) -> List[str]:
        """Create balanced mix of hashtags for optimal reach"""
        
        final_hashtags = []
        
        # Strategic mix: 30% high, 50% medium, 20% low competition
        final_hashtags.extend(categorized['high_competition'][:9])
        final_hashtags.extend(categorized['medium_competition'][:15])
        final_hashtags.extend(categorized['low_competition'][:6])
        
        # Add trending and niche
        final_hashtags.extend(categorized['trending'][:3])
        final_hashtags.extend(categorized['niche'][:2])
        final_hashtags.extend(categorized['location_based'][:3])
        
        # Remove duplicates and limit to 30
        final_hashtags = list(dict.fromkeys(final_hashtags))[:30]
        
        return final_hashtags
    
    def load_trending_hashtags(self) -> List[str]:
        """Load current trending hashtags (would connect to real API)"""
        return ['trending2024', 'viral', 'explore', 'fyp']
    
    def load_niche_hashtags(self) -> Dict[str, List[str]]:
        """Load niche hashtags by category"""
        return {
            'photography': ['shotoniphone', 'mobilephotography', 'photooftheday'],
            'travel': ['solotravel', 'backpacking', 'wanderlust'],
            'lifestyle': ['dailylife', 'mood', 'vibes']
        }
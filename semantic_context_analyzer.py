#!/usr/bin/env python3
"""
Semantic Context Analyzer for Intelligent Photo Grouping
Uses advanced NLP and semantic similarity for context understanding
"""

import numpy as np
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import logging
from dataclasses import dataclass
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class SemanticContext:
    """Semantic context representation"""
    location_entities: Set[str]      # Extracted location entities
    activity_entities: Set[str]      # Activities/actions
    object_entities: Set[str]        # Objects/subjects
    emotion_entities: Set[str]       # Emotional descriptors
    time_entities: Set[str]          # Time-related entities
    semantic_vector: np.ndarray      # Semantic representation vector
    context_hash: str                # Unique context identifier

class SemanticContextAnalyzer:
    """Advanced semantic analysis for photo context understanding"""
    
    def __init__(self):
        # Semantic categories and their keywords
        self.semantic_categories = {
            'location_indicators': {
                'beach': ['beach', 'ocean', 'sea', 'shore', 'sand', 'waves', 'coastal'],
                'mountain': ['mountain', 'peak', 'summit', 'alpine', 'hiking', 'trail', 'elevation'],
                'city': ['city', 'urban', 'street', 'building', 'downtown', 'skyline', 'metropolitan'],
                'forest': ['forest', 'trees', 'woods', 'nature', 'wilderness', 'trail', 'canopy'],
                'indoor': ['indoor', 'inside', 'room', 'interior', 'home', 'restaurant', 'cafe'],
                'water': ['lake', 'river', 'pond', 'waterfall', 'stream', 'reflection', 'aquatic']
            },
            'activity_indicators': {
                'dining': ['eating', 'food', 'meal', 'restaurant', 'dining', 'cuisine', 'dish'],
                'travel': ['travel', 'vacation', 'trip', 'journey', 'explore', 'adventure', 'destination'],
                'social': ['friends', 'family', 'group', 'gathering', 'celebration', 'party', 'together'],
                'recreation': ['fun', 'play', 'game', 'sport', 'activity', 'leisure', 'entertainment'],
                'work': ['work', 'office', 'business', 'professional', 'meeting', 'conference', 'career'],
                'relaxation': ['relax', 'peaceful', 'calm', 'quiet', 'serene', 'meditation', 'rest']
            },
            'emotion_indicators': {
                'joy': ['happy', 'joyful', 'cheerful', 'excited', 'delighted', 'elated', 'blissful'],
                'peace': ['peaceful', 'calm', 'serene', 'tranquil', 'quiet', 'still', 'meditative'],
                'energy': ['energetic', 'dynamic', 'vibrant', 'lively', 'active', 'spirited', 'intense'],
                'romance': ['romantic', 'intimate', 'loving', 'tender', 'affectionate', 'passionate', 'dreamy'],
                'adventure': ['adventurous', 'exciting', 'thrilling', 'bold', 'daring', 'wild', 'epic'],
                'nostalgia': ['nostalgic', 'vintage', 'classic', 'timeless', 'memories', 'reminiscent', 'retro']
            },
            'time_indicators': {
                'morning': ['morning', 'dawn', 'sunrise', 'early', 'breakfast', 'fresh', 'beginning'],
                'afternoon': ['afternoon', 'midday', 'lunch', 'bright', 'sunny', 'warm', 'peak'],
                'evening': ['evening', 'sunset', 'dusk', 'dinner', 'golden', 'warm', 'ending'],
                'night': ['night', 'dark', 'stars', 'moon', 'lights', 'illuminated', 'nocturnal']
            }
        }
        
        # Semantic similarity thresholds
        self.similarity_thresholds = {
            'very_similar': 0.85,    # Almost identical context
            'similar': 0.70,         # Similar context
            'related': 0.55,         # Somewhat related
            'different': 0.40        # Different context
        }
    
    def extract_semantic_context(self, photo_data: Dict) -> SemanticContext:
        """Extract semantic context from photo analysis"""
        analysis = photo_data.get('analysis', {})
        category = photo_data.get('category', {})
        
        # Combine all text for analysis
        text_content = self._combine_text_content(analysis, category)
        
        # Extract entities
        location_entities = self._extract_entities(text_content, 'location_indicators')
        activity_entities = self._extract_entities(text_content, 'activity_indicators')
        object_entities = self._extract_objects(analysis)
        emotion_entities = self._extract_entities(text_content, 'emotion_indicators')
        time_entities = self._extract_entities(text_content, 'time_indicators')
        
        # Create semantic vector
        semantic_vector = self._create_semantic_vector(
            location_entities, activity_entities, object_entities, 
            emotion_entities, time_entities
        )
        
        # Generate context hash
        context_hash = self._generate_context_hash(
            location_entities, activity_entities, emotion_entities
        )
        
        return SemanticContext(
            location_entities=location_entities,
            activity_entities=activity_entities,
            object_entities=object_entities,
            emotion_entities=emotion_entities,
            time_entities=time_entities,
            semantic_vector=semantic_vector,
            context_hash=context_hash
        )
    
    def _combine_text_content(self, analysis: Dict, category: Dict) -> str:
        """Combine all textual content for analysis"""
        text_parts = []
        
        # From analysis
        text_parts.extend([
            analysis.get('location', ''),
            analysis.get('mood', ''),
            ' '.join(analysis.get('strengths', [])),
            analysis.get('category', ''),
            analysis.get('subcategory', '')
        ])
        
        # From category
        text_parts.extend([
            category.get('primary', ''),
            category.get('secondary', ''),
            category.get('mood', ''),
            category.get('setting', ''),
            category.get('time_of_day', ''),
            category.get('season', '')
        ])
        
        return ' '.join(text_parts).lower()
    
    def _extract_entities(self, text: str, category_type: str) -> Set[str]:
        """Extract entities of a specific category type"""
        entities = set()
        
        if category_type not in self.semantic_categories:
            return entities
        
        for entity_type, keywords in self.semantic_categories[category_type].items():
            for keyword in keywords:
                if keyword in text:
                    entities.add(entity_type)
                    break
        
        return entities
    
    def _extract_objects(self, analysis: Dict) -> Set[str]:
        """Extract object entities from analysis"""
        objects = set()
        
        # From category and subcategory
        category = (analysis.get('category') or '').lower()
        subcategory = (analysis.get('subcategory') or '').lower()
        
        # Common Instagram objects
        object_keywords = {
            'person': ['person', 'people', 'portrait', 'face', 'human'],
            'food': ['food', 'meal', 'dish', 'cuisine', 'cooking', 'eating'],
            'animal': ['animal', 'pet', 'dog', 'cat', 'bird', 'wildlife'],
            'vehicle': ['car', 'bike', 'motorcycle', 'boat', 'plane', 'transport'],
            'building': ['building', 'architecture', 'house', 'structure', 'construction'],
            'plant': ['plant', 'flower', 'tree', 'garden', 'botanical', 'vegetation'],
            'technology': ['phone', 'computer', 'camera', 'device', 'gadget', 'tech'],
            'art': ['art', 'painting', 'sculpture', 'creative', 'artistic', 'design']
        }
        
        text_content = f"{category} {subcategory} {analysis.get('location', '')}"
        
        for obj_type, keywords in object_keywords.items():
            for keyword in keywords:
                if keyword in text_content:
                    objects.add(obj_type)
                    break
        
        return objects
    
    def _create_semantic_vector(self, location_entities: Set[str], activity_entities: Set[str], 
                               object_entities: Set[str], emotion_entities: Set[str], 
                               time_entities: Set[str]) -> np.ndarray:
        """Create a semantic vector representation"""
        
        # Define vector dimensions
        all_locations = set()
        all_activities = set()
        all_objects = set()
        all_emotions = set()
        all_times = set()
        
        # Collect all possible entities
        for category in self.semantic_categories.values():
            if isinstance(category, dict):
                all_locations.update(category.keys()) if 'location' in str(category) else None
                all_activities.update(category.keys()) if 'activity' in str(category) else None
                all_emotions.update(category.keys()) if 'emotion' in str(category) else None
                all_times.update(category.keys()) if 'time' in str(category) else None
        
        # Create binary vector
        vector_parts = []
        
        # Location vector
        for loc in sorted(self.semantic_categories['location_indicators'].keys()):
            vector_parts.append(1.0 if loc in location_entities else 0.0)
        
        # Activity vector
        for act in sorted(self.semantic_categories['activity_indicators'].keys()):
            vector_parts.append(1.0 if act in activity_entities else 0.0)
        
        # Emotion vector
        for emo in sorted(self.semantic_categories['emotion_indicators'].keys()):
            vector_parts.append(1.0 if emo in emotion_entities else 0.0)
        
        # Time vector
        for time in sorted(self.semantic_categories['time_indicators'].keys()):
            vector_parts.append(1.0 if time in time_entities else 0.0)
        
        # Object vector (simplified)
        common_objects = ['person', 'food', 'animal', 'building', 'plant', 'technology']
        for obj in common_objects:
            vector_parts.append(1.0 if obj in object_entities else 0.0)
        
        return np.array(vector_parts)
    
    def _generate_context_hash(self, location_entities: Set[str], 
                              activity_entities: Set[str], 
                              emotion_entities: Set[str]) -> str:
        """Generate a unique hash for the context"""
        # Combine key entities for hashing
        key_entities = sorted(list(location_entities)) + \
                      sorted(list(activity_entities)) + \
                      sorted(list(emotion_entities))
        
        return '_'.join(key_entities) if key_entities else 'unknown_context'
    
    def calculate_semantic_similarity(self, context1: SemanticContext, 
                                    context2: SemanticContext) -> float:
        """Calculate semantic similarity between two contexts"""
        
        # Vector similarity (cosine similarity)
        vector_sim = self._cosine_similarity(context1.semantic_vector, context2.semantic_vector)
        
        # Entity overlap similarity
        entity_sim = self._calculate_entity_similarity(context1, context2)
        
        # Combine similarities
        overall_similarity = (vector_sim * 0.6 + entity_sim * 0.4)
        
        return overall_similarity
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            return 0.0
        
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def _calculate_entity_similarity(self, context1: SemanticContext, 
                                   context2: SemanticContext) -> float:
        """Calculate similarity based on entity overlap"""
        
        # Calculate Jaccard similarity for each entity type
        location_sim = self._jaccard_similarity(context1.location_entities, context2.location_entities)
        activity_sim = self._jaccard_similarity(context1.activity_entities, context2.activity_entities)
        emotion_sim = self._jaccard_similarity(context1.emotion_entities, context2.emotion_entities)
        object_sim = self._jaccard_similarity(context1.object_entities, context2.object_entities)
        time_sim = self._jaccard_similarity(context1.time_entities, context2.time_entities)
        
        # Weighted average
        weights = {
            'location': 0.3,
            'activity': 0.25,
            'emotion': 0.2,
            'object': 0.15,
            'time': 0.1
        }
        
        weighted_similarity = (
            location_sim * weights['location'] +
            activity_sim * weights['activity'] +
            emotion_sim * weights['emotion'] +
            object_sim * weights['object'] +
            time_sim * weights['time']
        )
        
        return weighted_similarity
    
    def _jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """Calculate Jaccard similarity between two sets"""
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def group_photos_by_semantic_context(self, photos_data: List[Dict]) -> Dict[str, List[Dict]]:
        """Group photos by semantic context"""
        
        # Extract contexts for all photos
        photo_contexts = []
        for photo in photos_data:
            context = self.extract_semantic_context(photo)
            photo_contexts.append((photo, context))
        
        # Group by similarity
        groups = defaultdict(list)
        processed = set()
        
        for i, (photo1, context1) in enumerate(photo_contexts):
            if i in processed:
                continue
            
            group_key = context1.context_hash
            groups[group_key].append(photo1)
            processed.add(i)
            
            # Find similar photos
            for j, (photo2, context2) in enumerate(photo_contexts[i+1:], i+1):
                if j in processed:
                    continue
                
                similarity = self.calculate_semantic_similarity(context1, context2)
                
                if similarity >= self.similarity_thresholds['similar']:
                    groups[group_key].append(photo2)
                    processed.add(j)
        
        return dict(groups)
    
    def select_best_from_context_group(self, group_photos: List[Dict], 
                                     max_photos: int = 3) -> List[Dict]:
        """Select the best photos from a context group"""
        
        if len(group_photos) <= max_photos:
            return group_photos
        
        # Sort by composite score
        sorted_photos = sorted(group_photos, 
                             key=lambda p: p.get('score', {}).get('composite_score', 0), 
                             reverse=True)
        
        # Select top photos with diversity consideration
        selected = [sorted_photos[0]]  # Always take the best
        
        for photo in sorted_photos[1:]:
            if len(selected) >= max_photos:
                break
            
            # Check if this photo adds diversity
            if self._adds_diversity(photo, selected):
                selected.append(photo)
        
        # Fill remaining slots with highest scoring photos
        while len(selected) < max_photos and len(selected) < len(sorted_photos):
            for photo in sorted_photos:
                if photo not in selected:
                    selected.append(photo)
                    break
        
        return selected
    
    def _adds_diversity(self, candidate_photo: Dict, selected_photos: List[Dict]) -> bool:
        """Check if candidate photo adds diversity to selection"""
        
        candidate_context = self.extract_semantic_context(candidate_photo)
        
        for selected_photo in selected_photos:
            selected_context = self.extract_semantic_context(selected_photo)
            similarity = self.calculate_semantic_similarity(candidate_context, selected_context)
            
            if similarity > self.similarity_thresholds['very_similar']:
                return False  # Too similar to existing selection
        
        return True

def apply_semantic_contextual_filtering(photos_data: List[Dict], 
                                      max_photos_per_context: int = 3) -> List[Dict]:
    """Apply semantic contextual filtering to photo collection"""
    
    analyzer = SemanticContextAnalyzer()
    
    try:
        # Group photos by semantic context
        context_groups = analyzer.group_photos_by_semantic_context(photos_data)
        
        logger.info(f"Found {len(context_groups)} semantic context groups")
        
        # Select best photos from each group
        filtered_photos = []
        for group_key, group_photos in context_groups.items():
            logger.info(f"Context '{group_key}': {len(group_photos)} photos")
            
            best_photos = analyzer.select_best_from_context_group(
                group_photos, max_photos_per_context
            )
            filtered_photos.extend(best_photos)
        
        logger.info(f"Filtered from {len(photos_data)} to {len(filtered_photos)} photos")
        
        return filtered_photos
        
    except Exception as e:
        logger.error(f"Semantic contextual filtering failed: {e}")
        return photos_data  # Return original data on failure
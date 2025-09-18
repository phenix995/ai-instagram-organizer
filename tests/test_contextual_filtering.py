#!/usr/bin/env python3
"""
Test script for AI-based contextual similarity filtering
"""

import json
import os
from datetime import datetime
from ai_instagram_organizer import Config, filter_contextually_similar_images, calculate_contextual_similarity

def create_test_photos():
    """Create test photo data with various contextual similarities"""
    
    # Group 1: Multiple sunset landscape photos (should be filtered)
    sunset_photos = []
    for i in range(4):
        sunset_photos.append({
            'path': f'/test/sunset_{i+1}.jpg',
            'datetime': datetime.now(),
            'analysis': {
                'category': 'landscape',
                'subcategory': 'sunset',
                'location': 'beach with golden hour lighting',
                'mood': 'peaceful',
                'people_present': '0',
                'technical_score': 7 + i * 0.5,
                'engagement_score': 8 + i * 0.3,
                'visual_appeal': 8.5 + i * 0.2
            },
            'enhanced': {
                'composite_score': 7.8 + i * 0.4,
                'tier': 'excellent' if i >= 2 else 'good',
                'category': 'landscape'
            }
        })
    
    # Group 2: Portrait photos of same person (should be filtered)
    portrait_photos = []
    for i in range(3):
        portrait_photos.append({
            'path': f'/test/portrait_{i+1}.jpg',
            'datetime': datetime.now(),
            'analysis': {
                'category': 'portrait',
                'subcategory': 'individual portrait',
                'location': 'outdoor setting with natural lighting',
                'mood': 'happy',
                'people_present': '1',
                'technical_score': 8 + i * 0.2,
                'engagement_score': 7.5 + i * 0.3,
                'visual_appeal': 8 + i * 0.1
            },
            'enhanced': {
                'composite_score': 8.1 + i * 0.3,
                'tier': 'excellent',
                'category': 'portrait'
            }
        })
    
    # Group 3: Food photos from same meal (should be filtered)
    food_photos = []
    for i in range(3):
        food_photos.append({
            'path': f'/test/food_{i+1}.jpg',
            'datetime': datetime.now(),
            'analysis': {
                'category': 'food',
                'subcategory': 'restaurant meal',
                'location': 'indoor restaurant setting',
                'mood': 'appetizing',
                'people_present': '0',
                'technical_score': 7.5 + i * 0.3,
                'engagement_score': 6.8 + i * 0.4,
                'visual_appeal': 7.8 + i * 0.2
            },
            'enhanced': {
                'composite_score': 7.2 + i * 0.4,
                'tier': 'good',
                'category': 'food'
            }
        })
    
    # Unique photos (should NOT be filtered)
    unique_photos = [
        {
            'path': '/test/architecture_1.jpg',
            'datetime': datetime.now(),
            'analysis': {
                'category': 'architecture',
                'subcategory': 'modern building',
                'location': 'urban cityscape',
                'mood': 'impressive',
                'people_present': '0',
                'technical_score': 8.5,
                'engagement_score': 7.8,
                'visual_appeal': 8.2
            },
            'enhanced': {
                'composite_score': 8.1,
                'tier': 'excellent',
                'category': 'architecture'
            }
        },
        {
            'path': '/test/nature_1.jpg',
            'datetime': datetime.now(),
            'analysis': {
                'category': 'nature',
                'subcategory': 'wildlife',
                'location': 'forest with natural lighting',
                'mood': 'serene',
                'people_present': '0',
                'technical_score': 9.0,
                'engagement_score': 8.5,
                'visual_appeal': 9.2
            },
            'enhanced': {
                'composite_score': 8.9,
                'tier': 'premium',
                'category': 'nature'
            }
        }
    ]
    
    return sunset_photos + portrait_photos + food_photos + unique_photos

def test_contextual_similarity():
    """Test contextual similarity calculation"""
    print("=== Testing Contextual Similarity Calculation ===\n")
    
    test_photos = create_test_photos()
    
    # Test similarity between sunset photos
    sunset1 = test_photos[0]
    sunset2 = test_photos[1]
    similarity = calculate_contextual_similarity(sunset1, sunset2)
    print(f"Sunset photo similarity: {similarity:.3f} (should be high ~0.8+)")
    
    # Test similarity between different categories
    sunset = test_photos[0]
    architecture = test_photos[-2]
    similarity = calculate_contextual_similarity(sunset, architecture)
    print(f"Sunset vs Architecture similarity: {similarity:.3f} (should be low ~0.2-)")
    
    # Test similarity between portraits
    portrait1 = test_photos[4]
    portrait2 = test_photos[5]
    similarity = calculate_contextual_similarity(portrait1, portrait2)
    print(f"Portrait similarity: {similarity:.3f} (should be high ~0.8+)")
    
    print()

def test_contextual_filtering():
    """Test the full contextual filtering process"""
    print("=== Testing Contextual Filtering Process ===\n")
    
    # Create test config
    config = Config()
    config.enable_contextual_filtering = True
    config.contextual_similarity_threshold = 0.7
    config.contextual_selection_strategy = 'highest_score'
    
    test_photos = create_test_photos()
    
    print(f"Original photos: {len(test_photos)}")
    print("Expected groups:")
    print("- 4 sunset photos → 1 best")
    print("- 3 portrait photos → 1 best") 
    print("- 3 food photos → 1 best")
    print("- 2 unique photos → 2 kept")
    print("Expected result: 5 photos total\n")
    
    # Apply contextual filtering
    filtered_photos = filter_contextually_similar_images(test_photos, config)
    
    print(f"Filtered photos: {len(filtered_photos)}")
    print("Kept photos:")
    for photo in filtered_photos:
        category = photo['enhanced']['category']
        score = photo['enhanced']['composite_score']
        tier = photo['enhanced']['tier']
        print(f"- {os.path.basename(photo['path'])}: {category} ({tier}, score: {score:.2f})")
    
    print()

def test_different_strategies():
    """Test different selection strategies"""
    print("=== Testing Different Selection Strategies ===\n")
    
    test_photos = create_test_photos()
    
    strategies = [
        'highest_score',
        'most_unique', 
        'best_technical',
        'best_engagement'
    ]
    
    for strategy in strategies:
        config = Config()
        config.enable_contextual_filtering = True
        config.contextual_similarity_threshold = 0.7
        config.contextual_selection_strategy = strategy
        
        filtered_photos = filter_contextually_similar_images(test_photos, config)
        
        print(f"Strategy: {strategy}")
        print(f"Photos kept: {len(filtered_photos)}")
        
        # Show sunset group selection (first 4 photos are sunsets)
        sunset_kept = [p for p in filtered_photos if 'sunset' in p['path']]
        if sunset_kept:
            sunset = sunset_kept[0]
            score = sunset['enhanced']['composite_score']
            tech = sunset['analysis']['technical_score']
            eng = sunset['analysis']['engagement_score']
            print(f"Sunset selected: {os.path.basename(sunset['path'])} (composite: {score:.2f}, tech: {tech}, engagement: {eng})")
        
        print()

def test_threshold_sensitivity():
    """Test how different thresholds affect filtering"""
    print("=== Testing Threshold Sensitivity ===\n")
    
    test_photos = create_test_photos()
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    for threshold in thresholds:
        config = Config()
        config.enable_contextual_filtering = True
        config.contextual_similarity_threshold = threshold
        config.contextual_selection_strategy = 'highest_score'
        
        filtered_photos = filter_contextually_similar_images(test_photos, config)
        
        print(f"Threshold {threshold}: {len(filtered_photos)} photos kept (from {len(test_photos)} original)")
    
    print()

def main():
    """Run all contextual filtering tests"""
    print("🧠 AI-Based Contextual Similarity Filtering Test\n")
    print("This test demonstrates how AI analysis can identify and filter")
    print("photos with similar context (same scene, person, meal, etc.)\n")
    
    test_contextual_similarity()
    test_contextual_filtering()
    test_different_strategies()
    test_threshold_sensitivity()
    
    print("✅ All tests completed!")
    print("\nTo use contextual filtering in your workflow:")
    print("1. Enable in config.json: 'enable_contextual_filtering': true")
    print("2. Adjust threshold (0.7 recommended for balanced filtering)")
    print("3. Choose selection strategy based on your needs:")
    print("   - 'highest_score': Best overall quality")
    print("   - 'most_unique': Most different from others in group")
    print("   - 'best_technical': Best technical quality")
    print("   - 'best_engagement': Highest engagement potential")

if __name__ == "__main__":
    main()
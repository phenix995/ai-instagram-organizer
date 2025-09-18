#!/usr/bin/env python3
"""
Demo script showing contextual filtering in action with real-world scenarios
"""

import json
from datetime import datetime
from ai_instagram_organizer import Config, filter_contextually_similar_images

def create_hawaii_photo_collection():
    """Create a realistic Hawaii photo collection with contextual similarities"""
    
    photos = []
    
    # Scenario 1: Multiple sunset beach photos (should be filtered to 1-2 best)
    sunset_photos = [
        {
            'path': '/hawaii/sunset_beach_1.jpg',
            'datetime': datetime(2024, 8, 15, 19, 30),
            'analysis': {
                'category': 'landscape',
                'subcategory': 'sunset beach',
                'location': 'beach with golden hour lighting and palm trees',
                'mood': 'peaceful',
                'people_present': '0',
                'technical_score': 8.2,
                'engagement_score': 9.1,
                'visual_appeal': 8.8
            },
            'enhanced': {
                'composite_score': 8.7,
                'tier': 'excellent',
                'category': 'landscape'
            }
        },
        {
            'path': '/hawaii/sunset_beach_2.jpg',
            'datetime': datetime(2024, 8, 15, 19, 35),
            'analysis': {
                'category': 'landscape',
                'subcategory': 'sunset beach',
                'location': 'beach with golden hour lighting and waves',
                'mood': 'peaceful',
                'people_present': '0',
                'technical_score': 7.8,
                'engagement_score': 8.9,
                'visual_appeal': 8.5
            },
            'enhanced': {
                'composite_score': 8.4,
                'tier': 'excellent',
                'category': 'landscape'
            }
        },
        {
            'path': '/hawaii/sunset_beach_3.jpg',
            'datetime': datetime(2024, 8, 15, 19, 40),
            'analysis': {
                'category': 'landscape',
                'subcategory': 'sunset beach',
                'location': 'beach with golden hour lighting and silhouettes',
                'mood': 'peaceful',
                'people_present': '0',
                'technical_score': 9.1,
                'engagement_score': 9.3,
                'visual_appeal': 9.2
            },
            'enhanced': {
                'composite_score': 9.2,
                'tier': 'premium',
                'category': 'landscape'
            }
        }
    ]
    
    # Scenario 2: Multiple food photos from same luau (should be filtered to 1 best)
    luau_food_photos = [
        {
            'path': '/hawaii/luau_food_1.jpg',
            'datetime': datetime(2024, 8, 16, 18, 0),
            'analysis': {
                'category': 'food',
                'subcategory': 'traditional hawaiian meal',
                'location': 'outdoor luau setting with traditional decorations',
                'mood': 'festive',
                'people_present': '0',
                'technical_score': 7.5,
                'engagement_score': 8.2,
                'visual_appeal': 8.0
            },
            'enhanced': {
                'composite_score': 7.9,
                'tier': 'good',
                'category': 'food'
            }
        },
        {
            'path': '/hawaii/luau_food_2.jpg',
            'datetime': datetime(2024, 8, 16, 18, 5),
            'analysis': {
                'category': 'food',
                'subcategory': 'traditional hawaiian meal',
                'location': 'outdoor luau setting with tropical fruits',
                'mood': 'festive',
                'people_present': '0',
                'technical_score': 8.1,
                'engagement_score': 8.5,
                'visual_appeal': 8.3
            },
            'enhanced': {
                'composite_score': 8.3,
                'tier': 'excellent',
                'category': 'food'
            }
        }
    ]
    
    # Scenario 3: Multiple hiking photos from same trail (should be filtered to 1-2 best)
    hiking_photos = [
        {
            'path': '/hawaii/hike_waterfall_1.jpg',
            'datetime': datetime(2024, 8, 17, 10, 30),
            'analysis': {
                'category': 'nature',
                'subcategory': 'waterfall hike',
                'location': 'tropical forest trail with waterfall view',
                'mood': 'adventurous',
                'people_present': '1',
                'technical_score': 8.8,
                'engagement_score': 8.7,
                'visual_appeal': 9.0
            },
            'enhanced': {
                'composite_score': 8.8,
                'tier': 'excellent',
                'category': 'nature'
            }
        },
        {
            'path': '/hawaii/hike_waterfall_2.jpg',
            'datetime': datetime(2024, 8, 17, 10, 45),
            'analysis': {
                'category': 'nature',
                'subcategory': 'waterfall hike',
                'location': 'tropical forest trail with lush vegetation',
                'mood': 'adventurous',
                'people_present': '1',
                'technical_score': 8.3,
                'engagement_score': 8.1,
                'visual_appeal': 8.5
            },
            'enhanced': {
                'composite_score': 8.3,
                'tier': 'excellent',
                'category': 'nature'
            }
        }
    ]
    
    # Unique photos that should NOT be filtered
    unique_photos = [
        {
            'path': '/hawaii/snorkeling_underwater.jpg',
            'datetime': datetime(2024, 8, 18, 14, 0),
            'analysis': {
                'category': 'action',
                'subcategory': 'underwater photography',
                'location': 'underwater coral reef with tropical fish',
                'mood': 'exciting',
                'people_present': '1',
                'technical_score': 9.2,
                'engagement_score': 9.5,
                'visual_appeal': 9.3
            },
            'enhanced': {
                'composite_score': 9.3,
                'tier': 'premium',
                'category': 'action'
            }
        },
        {
            'path': '/hawaii/volcano_night.jpg',
            'datetime': datetime(2024, 8, 19, 21, 0),
            'analysis': {
                'category': 'landscape',
                'subcategory': 'volcanic activity',
                'location': 'volcanic crater with glowing lava at night',
                'mood': 'dramatic',
                'people_present': '0',
                'technical_score': 8.9,
                'engagement_score': 9.8,
                'visual_appeal': 9.5
            },
            'enhanced': {
                'composite_score': 9.4,
                'tier': 'premium',
                'category': 'landscape'
            }
        },
        {
            'path': '/hawaii/cultural_dance.jpg',
            'datetime': datetime(2024, 8, 20, 19, 30),
            'analysis': {
                'category': 'lifestyle',
                'subcategory': 'cultural performance',
                'location': 'outdoor stage with traditional hawaiian dancers',
                'mood': 'energetic',
                'people_present': '6+',
                'technical_score': 8.4,
                'engagement_score': 8.8,
                'visual_appeal': 8.6
            },
            'enhanced': {
                'composite_score': 8.6,
                'tier': 'excellent',
                'category': 'lifestyle'
            }
        }
    ]
    
    return sunset_photos + luau_food_photos + hiking_photos + unique_photos

def demo_contextual_filtering():
    """Demonstrate contextual filtering with realistic scenarios"""
    
    print("🏝️  Hawaii Photo Collection - Contextual Filtering Demo")
    print("=" * 60)
    
    # Create realistic photo collection
    photos = create_hawaii_photo_collection()
    
    print(f"\n📸 Original Collection: {len(photos)} photos")
    print("\nPhoto breakdown:")
    print("- 3 sunset beach photos (similar context)")
    print("- 2 luau food photos (similar context)")  
    print("- 2 hiking waterfall photos (similar context)")
    print("- 3 unique photos (different contexts)")
    
    # Test different contextual filtering settings
    scenarios = [
        {
            'name': 'Strict Filtering (0.8 threshold)',
            'threshold': 0.8,
            'strategy': 'highest_score',
            'description': 'Very strict - only filters nearly identical contexts'
        },
        {
            'name': 'Balanced Filtering (0.7 threshold)', 
            'threshold': 0.7,
            'strategy': 'highest_score',
            'description': 'Recommended - good balance of filtering and variety'
        },
        {
            'name': 'Aggressive Filtering (0.6 threshold)',
            'threshold': 0.6, 
            'strategy': 'highest_score',
            'description': 'Aggressive - filters more loosely similar contexts'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🎯 {scenario['name']}")
        print(f"   {scenario['description']}")
        print("-" * 50)
        
        # Configure contextual filtering
        config = Config()
        config.enable_contextual_filtering = True
        config.contextual_similarity_threshold = scenario['threshold']
        config.contextual_selection_strategy = scenario['strategy']
        
        # Apply filtering
        filtered_photos = filter_contextually_similar_images(photos, config)
        
        print(f"📊 Results: {len(filtered_photos)} photos kept (from {len(photos)} original)")
        
        # Show what was kept
        categories = {}
        for photo in filtered_photos:
            category = photo['enhanced']['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(photo)
        
        print("   Photos kept by category:")
        for category, cat_photos in categories.items():
            print(f"   - {category.title()}: {len(cat_photos)} photos")
            for photo in cat_photos:
                score = photo['enhanced']['composite_score']
                tier = photo['enhanced']['tier']
                filename = photo['path'].split('/')[-1]
                print(f"     • {filename} ({tier}, score: {score})")
    
    print(f"\n💡 Key Benefits of Contextual Filtering:")
    print("- Eliminates repetitive content (multiple sunset shots)")
    print("- Keeps only the best photo from similar scenes")
    print("- Preserves unique, diverse content")
    print("- Improves overall feed quality and engagement")
    print("- Saves time by auto-selecting best photos")
    
    print(f"\n⚙️  Configuration Tips:")
    print("- Use 0.7 threshold for balanced filtering")
    print("- Use 0.8+ for conservative filtering (travel/events)")
    print("- Use 0.6 for aggressive filtering (large collections)")
    print("- 'highest_score' strategy works best for most cases")

if __name__ == "__main__":
    demo_contextual_filtering()
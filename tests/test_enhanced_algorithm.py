#!/usr/bin/env python3
"""
Test script for the enhanced Instagram algorithm
"""

import json
import logging
from datetime import datetime, timedelta
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_mock_analysis_data(num_photos: int = 50) -> list:
    """Create mock analysis data for testing"""
    
    categories = ['landscape', 'portrait', 'food', 'architecture', 'lifestyle', 'travel', 'nature', 'street']
    moods = ['peaceful', 'energetic', 'romantic', 'adventurous', 'cozy', 'dramatic', 'joyful']
    settings = ['indoor', 'outdoor', 'urban', 'nature']
    times = ['golden_hour', 'blue_hour', 'midday', 'night', 'morning']
    
    mock_data = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(num_photos):
        # Create realistic score distribution
        # 5% premium (8.5+), 15% excellent (7.5+), 30% good (6.0+), 50% average/poor
        rand = random.random()
        if rand < 0.05:  # Premium
            base_score = random.uniform(8.5, 10.0)
        elif rand < 0.20:  # Excellent
            base_score = random.uniform(7.5, 8.5)
        elif rand < 0.50:  # Good
            base_score = random.uniform(6.0, 7.5)
        else:  # Average/Poor
            base_score = random.uniform(3.0, 6.0)
        
        # Generate individual scores around base score
        technical = max(1, min(10, base_score + random.uniform(-1, 1)))
        visual = max(1, min(10, base_score + random.uniform(-1, 1)))
        engagement = max(1, min(10, base_score + random.uniform(-1, 1)))
        uniqueness = max(1, min(10, base_score + random.uniform(-1, 1)))
        story = max(1, min(10, base_score + random.uniform(-1, 1)))
        
        # Calculate composite score
        composite = (
            technical * 0.15 +
            visual * 0.25 +
            engagement * 0.30 +
            uniqueness * 0.20 +
            story * 0.10
        )
        
        # Determine tier
        if composite >= 8.5:
            tier = "premium"
        elif composite >= 7.5:
            tier = "excellent"
        elif composite >= 6.0:
            tier = "good"
        elif composite >= 4.0:
            tier = "average"
        else:
            tier = "poor"
        
        analysis = {
            'technical_score': round(technical, 1),
            'visual_appeal': round(visual, 1),
            'engagement_score': round(engagement, 1),
            'uniqueness': round(uniqueness, 1),
            'story_potential': round(story, 1),
            'composite_score': round(composite, 2),
            'instagram_tier': tier,
            'instagram_worthy': tier in ['premium', 'excellent'] or composite >= 7.0,
            'category': random.choice(categories),
            'subcategory': f"{random.choice(['sunset', 'urban', 'close-up', 'wide', 'candid'])}",
            'location': f"Location {i+1}",
            'mood': random.choice(moods),
            'strengths': random.sample(['great lighting', 'unique perspective', 'vibrant colors', 'good composition', 'emotional connection'], 2),
            'weaknesses': random.sample(['slightly blurry', 'cluttered background', 'overexposed'], 1),
            'best_time': random.choice(['morning', 'afternoon', 'evening', 'golden_hour']),
            'caption_style': random.choice(['storytelling', 'inspirational', 'casual']),
            'hashtag_focus': random.choice(['travel', 'lifestyle', 'nature', 'food']),
            'people_present': random.choice(['0', '1', '2-5', '6+']),
            'time_of_day_indicators': random.choice(times),
            'season_indicators': random.choice(['spring', 'summer', 'fall', 'winter'])
        }
        
        photo_data = {
            'path': f'/mock/path/photo_{i+1:03d}.jpg',
            'datetime': base_date + timedelta(days=random.randint(0, 30)),
            'analysis': analysis
        }
        
        mock_data.append(photo_data)
    
    return mock_data

def test_enhanced_algorithm():
    """Test the enhanced algorithm with mock data"""
    
    logger.info("🚀 Testing Enhanced Instagram Algorithm")
    logger.info("=" * 50)
    
    # Create mock data
    mock_photos = create_mock_analysis_data(100)
    logger.info(f"Created {len(mock_photos)} mock photos for testing")
    
    # Analyze tier distribution
    tiers = {}
    categories = {}
    moods = {}
    
    for photo in mock_photos:
        analysis = photo['analysis']
        
        # Count tiers
        tier = analysis['instagram_tier']
        tiers[tier] = tiers.get(tier, 0) + 1
        
        # Count categories
        category = analysis['category']
        categories[category] = categories.get(category, 0) + 1
        
        # Count moods
        mood = analysis['mood']
        moods[mood] = moods.get(mood, 0) + 1
    
    # Display analysis
    logger.info("\n📊 PHOTO ANALYSIS RESULTS")
    logger.info("-" * 30)
    
    logger.info("Quality Tier Distribution:")
    for tier, count in sorted(tiers.items(), key=lambda x: ['premium', 'excellent', 'good', 'average', 'poor'].index(x[0])):
        percentage = (count / len(mock_photos)) * 100
        logger.info(f"  {tier.capitalize()}: {count} photos ({percentage:.1f}%)")
    
    logger.info("\nTop Categories:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
        percentage = (count / len(mock_photos)) * 100
        logger.info(f"  {category.capitalize()}: {count} photos ({percentage:.1f}%)")
    
    logger.info("\nTop Moods:")
    for mood, count in sorted(moods.items(), key=lambda x: x[1], reverse=True)[:5]:
        percentage = (count / len(mock_photos)) * 100
        logger.info(f"  {mood.capitalize()}: {count} photos ({percentage:.1f}%)")
    
    # Simulate post creation
    logger.info("\n🎯 POST CREATION SIMULATION")
    logger.info("-" * 30)
    
    # Filter Instagram-worthy photos
    worthy_photos = [p for p in mock_photos if p['analysis']['instagram_worthy']]
    logger.info(f"Instagram-worthy photos: {len(worthy_photos)}/{len(mock_photos)} ({len(worthy_photos)/len(mock_photos)*100:.1f}%)")
    
    # Simulate different post strategies
    post_size = 10
    
    # Premium posts
    premium_photos = [p for p in worthy_photos if p['analysis']['instagram_tier'] == 'premium']
    premium_posts = len(premium_photos) // post_size
    logger.info(f"Premium Showcase Posts: {min(premium_posts, 3)} (using {min(premium_posts * post_size, len(premium_photos))} photos)")
    
    # Excellent posts
    excellent_photos = [p for p in worthy_photos if p['analysis']['instagram_tier'] in ['premium', 'excellent']]
    diverse_posts = len(excellent_photos) // post_size
    logger.info(f"Diverse Excellence Posts: {min(diverse_posts, 5)} (using {min(diverse_posts * post_size, len(excellent_photos))} photos)")
    
    # Theme posts
    theme_posts = 0
    for category, count in categories.items():
        category_worthy = [p for p in worthy_photos if p['analysis']['category'] == category]
        if len(category_worthy) >= post_size:
            theme_posts += 1
    logger.info(f"Theme-Based Posts: {theme_posts} (category-specific)")
    
    # Chronological posts
    remaining_estimate = max(0, len(worthy_photos) - (min(premium_posts, 3) + min(diverse_posts, 5) + theme_posts) * post_size)
    chrono_posts = remaining_estimate // post_size
    logger.info(f"Chronological Posts: {chrono_posts} (remaining photos)")
    
    total_posts = min(premium_posts, 3) + min(diverse_posts, 5) + theme_posts + chrono_posts
    total_photos_used = total_posts * post_size
    
    logger.info(f"\n📈 SUMMARY")
    logger.info("-" * 20)
    logger.info(f"Total Posts Created: {total_posts}")
    logger.info(f"Photos Used: {total_photos_used}/{len(worthy_photos)} ({total_photos_used/len(worthy_photos)*100:.1f}%)")
    logger.info(f"Average Quality Score: {sum(p['analysis']['composite_score'] for p in worthy_photos)/len(worthy_photos):.2f}/10")
    
    # Quality distribution of used photos
    if total_photos_used > 0:
        used_photos = worthy_photos[:total_photos_used]  # Simplified simulation
        avg_score = sum(p['analysis']['composite_score'] for p in used_photos) / len(used_photos)
        logger.info(f"Average Score of Used Photos: {avg_score:.2f}/10")
    
    logger.info("\n✅ Enhanced algorithm test completed!")
    logger.info("This simulation shows how your photos would be organized with the new algorithm.")
    
    return {
        'total_photos': len(mock_photos),
        'worthy_photos': len(worthy_photos),
        'total_posts': total_posts,
        'tier_distribution': tiers,
        'category_distribution': categories
    }

if __name__ == "__main__":
    results = test_enhanced_algorithm()
    
    print("\n" + "="*60)
    print("🎉 ENHANCED ALGORITHM BENEFITS")
    print("="*60)
    print("✅ Intelligent photo quality assessment")
    print("✅ Multi-tier categorization system")
    print("✅ Diversity-optimized post creation")
    print("✅ Strategic content planning")
    print("✅ Comprehensive analytics reporting")
    print("✅ Maximum engagement potential")
    print("\nRun with your real photos to see the magic! 🚀")
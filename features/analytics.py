# Analytics and Performance Tracking

import os
import json
from collections import Counter
from typing import Dict, List
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_photo_patterns(analyzed_data: List[Dict]) -> Dict:
    """Analyze patterns in photo data for insights"""
    
    # Theme analysis
    themes = [data['analysis'].get('theme', 'Unknown') for data in analyzed_data]
    theme_counts = Counter(themes)
    
    # Location analysis  
    locations = [data['analysis'].get('location', 'Unknown') for data in analyzed_data]
    location_counts = Counter(locations)
    
    # Quality score distribution
    quality_scores = [data['analysis'].get('quality_score', 0) for data in analyzed_data]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    # Time-based patterns
    hours = [data['datetime'].hour for data in analyzed_data]
    hour_counts = Counter(hours)
    
    # Instagram worthiness rate
    worthy_count = sum(1 for data in analyzed_data if data['analysis'].get('instagram_worthy', False))
    worthy_rate = worthy_count / len(analyzed_data) if analyzed_data else 0
    
    return {
        'total_photos': len(analyzed_data),
        'instagram_worthy_rate': worthy_rate,
        'average_quality_score': avg_quality,
        'top_themes': theme_counts.most_common(5),
        'top_locations': location_counts.most_common(5),
        'best_photo_hours': hour_counts.most_common(3),
        'quality_distribution': {
            'high': len([s for s in quality_scores if s >= 8]),
            'medium': len([s for s in quality_scores if 5 <= s < 8]),
            'low': len([s for s in quality_scores if s < 5])
        }
    }

def generate_analytics_report(analytics: Dict, output_path: str) -> None:
    """Generate a comprehensive analytics report"""
    
    with open(output_path, 'w') as f:
        f.write("📊 INSTAGRAM PHOTO ANALYTICS REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"📸 Total Photos Analyzed: {analytics['total_photos']}\n")
        f.write(f"✨ Instagram Worthy Rate: {analytics['instagram_worthy_rate']:.1%}\n")
        f.write(f"⭐ Average Quality Score: {analytics['average_quality_score']:.1f}/10\n\n")
        
        f.write("🎨 TOP THEMES:\n")
        for theme, count in analytics['top_themes']:
            f.write(f"  • {theme}: {count} photos\n")
        
        f.write("\n📍 TOP LOCATIONS:\n")
        for location, count in analytics['top_locations']:
            f.write(f"  • {location}: {count} photos\n")
        
        f.write("\n⏰ BEST PHOTO HOURS:\n")
        for hour, count in analytics['best_photo_hours']:
            f.write(f"  • {hour}:00: {count} photos\n")
        
        f.write("\n📈 QUALITY DISTRIBUTION:\n")
        f.write(f"  • High Quality (8-10): {analytics['quality_distribution']['high']} photos\n")
        f.write(f"  • Medium Quality (5-7): {analytics['quality_distribution']['medium']} photos\n")
        f.write(f"  • Low Quality (1-4): {analytics['quality_distribution']['low']} photos\n")

def create_analytics_visualizations(analytics: Dict, output_dir: str) -> None:
    """Create visual charts for analytics"""
    
    # Theme distribution pie chart
    themes, counts = zip(*analytics['top_themes']) if analytics['top_themes'] else ([], [])
    
    plt.figure(figsize=(10, 6))
    plt.pie(counts, labels=themes, autopct='%1.1f%%')
    plt.title('Photo Themes Distribution')
    plt.savefig(os.path.join(output_dir, 'themes_distribution.png'))
    plt.close()
    
    # Quality score histogram
    quality_data = analytics['quality_distribution']
    categories = ['Low (1-4)', 'Medium (5-7)', 'High (8-10)']
    values = [quality_data['low'], quality_data['medium'], quality_data['high']]
    
    plt.figure(figsize=(8, 6))
    plt.bar(categories, values, color=['red', 'orange', 'green'])
    plt.title('Photo Quality Distribution')
    plt.ylabel('Number of Photos')
    plt.savefig(os.path.join(output_dir, 'quality_distribution.png'))
    plt.close()
# Instagram Scheduling Features

import datetime
import random
from typing import List, Dict

def generate_posting_schedule(posts_count: int, start_date: datetime.datetime = None) -> List[Dict]:
    """Generate optimal posting times based on engagement patterns"""
    if not start_date:
        start_date = datetime.datetime.now()
    
    # Optimal posting times (research-based)
    optimal_times = [
        (11, 0),  # 11 AM
        (14, 0),  # 2 PM  
        (17, 0),  # 5 PM
        (19, 0),  # 7 PM
    ]
    
    schedule = []
    current_date = start_date
    
    for i in range(posts_count):
        # Space posts 1-3 days apart
        days_gap = random.choice([1, 2, 3])
        current_date += datetime.timedelta(days=days_gap)
        
        # Choose optimal time
        hour, minute = random.choice(optimal_times)
        post_time = current_date.replace(hour=hour, minute=minute)
        
        schedule.append({
            'post_number': i + 1,
            'scheduled_time': post_time,
            'day_of_week': post_time.strftime('%A'),
            'optimal_score': calculate_engagement_score(post_time)
        })
    
    return schedule

def calculate_engagement_score(post_time: datetime.datetime) -> float:
    """Calculate expected engagement based on time/day"""
    # Higher scores for weekdays, optimal hours
    day_scores = {0: 0.8, 1: 0.9, 2: 0.9, 3: 0.9, 4: 0.8, 5: 0.6, 6: 0.7}
    hour_scores = {11: 0.9, 14: 0.8, 17: 0.9, 19: 0.7}
    
    day_score = day_scores.get(post_time.weekday(), 0.5)
    hour_score = hour_scores.get(post_time.hour, 0.5)
    
    return (day_score + hour_score) / 2
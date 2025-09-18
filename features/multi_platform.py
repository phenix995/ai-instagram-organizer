# Multi-Platform Content Export

import os
from pathlib import Path
from typing import List, Dict

def create_platform_variants(post_dir: str, images: List[str], content: Dict) -> None:
    """Create platform-specific variants of content"""
    
    platforms_dir = os.path.join(post_dir, "platform_variants")
    Path(platforms_dir).mkdir(exist_ok=True)
    
    # Instagram variants
    create_instagram_variants(platforms_dir, images, content)
    
    # TikTok/Reels variants  
    create_tiktok_variants(platforms_dir, images, content)
    
    # Twitter variants
    create_twitter_variants(platforms_dir, images, content)
    
    # LinkedIn variants
    create_linkedin_variants(platforms_dir, images, content)

def create_instagram_variants(output_dir: str, images: List[str], content: Dict) -> None:
    """Create Instagram-specific content"""
    
    ig_dir = os.path.join(output_dir, "instagram")
    Path(ig_dir).mkdir(exist_ok=True)
    
    # Feed post
    with open(os.path.join(ig_dir, "feed_post.txt"), "w") as f:
        f.write("INSTAGRAM FEED POST\n")
        f.write("=" * 30 + "\n\n")
        f.write(f"Caption: {content['caption_options'][0]}\n\n")
        f.write("Hashtags:\n")
        hashtags = " ".join([f"#{tag}" for tag in content['hashtags'][:30]])
        f.write(hashtags)
    
    # Story content
    with open(os.path.join(ig_dir, "story_content.txt"), "w") as f:
        f.write("INSTAGRAM STORY IDEAS\n")
        f.write("=" * 30 + "\n\n")
        f.write("Story 1: Behind the scenes\n")
        f.write("Story 2: Location tag with poll\n") 
        f.write("Story 3: Photo carousel with music\n")

def create_tiktok_variants(output_dir: str, images: List[str], content: Dict) -> None:
    """Create TikTok/Reels content"""
    
    tiktok_dir = os.path.join(output_dir, "tiktok_reels")
    Path(tiktok_dir).mkdir(exist_ok=True)
    
    with open(os.path.join(tiktok_dir, "video_script.txt"), "w") as f:
        f.write("TIKTOK/REELS VIDEO SCRIPT\n")
        f.write("=" * 35 + "\n\n")
        f.write("Hook (0-3s): Attention-grabbing opening\n")
        f.write("Content (3-15s): Main story/reveal\n")
        f.write("CTA (15-30s): Call to action\n\n")
        f.write(f"Caption: {content['caption_options'][1] if len(content['caption_options']) > 1 else content['caption_options'][0]}\n\n")
        f.write("Trending hashtags:\n")
        trending_tags = ["fyp", "viral", "trending", "explore"]
        f.write(" ".join([f"#{tag}" for tag in trending_tags + content['hashtags'][:10]]))

def create_twitter_variants(output_dir: str, images: List[str], content: Dict) -> None:
    """Create Twitter/X content"""
    
    twitter_dir = os.path.join(output_dir, "twitter")
    Path(twitter_dir).mkdir(exist_ok=True)
    
    with open(os.path.join(twitter_dir, "tweet_thread.txt"), "w") as f:
        f.write("TWITTER THREAD\n")
        f.write("=" * 20 + "\n\n")
        
        # Break caption into tweet-sized chunks
        caption = content['caption_options'][0]
        tweets = break_into_tweets(caption)
        
        for i, tweet in enumerate(tweets, 1):
            f.write(f"Tweet {i}/{len(tweets)}:\n")
            f.write(f"{tweet}\n\n")
        
        f.write("Hashtags (use sparingly):\n")
        f.write(" ".join([f"#{tag}" for tag in content['hashtags'][:5]]))

def break_into_tweets(text: str, max_length: int = 280) -> List[str]:
    """Break long text into tweet-sized chunks"""
    
    sentences = text.split('. ')
    tweets = []
    current_tweet = ""
    
    for sentence in sentences:
        if len(current_tweet + sentence) < max_length - 20:  # Leave room for thread numbering
            current_tweet += sentence + ". "
        else:
            if current_tweet:
                tweets.append(current_tweet.strip())
            current_tweet = sentence + ". "
    
    if current_tweet:
        tweets.append(current_tweet.strip())
    
    return tweets

def create_linkedin_variants(output_dir: str, images: List[str], content: Dict) -> None:
    """Create LinkedIn content"""
    
    linkedin_dir = os.path.join(output_dir, "linkedin")
    Path(linkedin_dir).mkdir(exist_ok=True)
    
    with open(os.path.join(linkedin_dir, "professional_post.txt"), "w") as f:
        f.write("LINKEDIN POST\n")
        f.write("=" * 20 + "\n\n")
        
        # Make caption more professional
        professional_caption = make_professional_tone(content['caption_options'][0])
        f.write(f"Caption:\n{professional_caption}\n\n")
        
        f.write("Professional hashtags:\n")
        prof_hashtags = ["leadership", "growth", "inspiration", "journey", "experience"]
        f.write(" ".join([f"#{tag}" for tag in prof_hashtags]))

def make_professional_tone(caption: str) -> str:
    """Convert casual caption to professional tone"""
    
    # Simple tone adjustments
    professional = caption.replace("amazing", "remarkable")
    professional = professional.replace("awesome", "impressive") 
    professional = professional.replace("so cool", "fascinating")
    
    # Add professional framing
    professional = f"Reflecting on this experience... {professional}\n\nWhat moments have shaped your perspective recently?"
    
    return professional
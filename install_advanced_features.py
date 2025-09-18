#!/usr/bin/env python3
"""
Installation script for advanced Instagram photo analyzer features
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def check_opencv():
    """Check if OpenCV is properly installed"""
    try:
        import cv2
        print(f"✅ OpenCV version {cv2.__version__} is installed")
        return True
    except ImportError:
        print("❌ OpenCV not found")
        return False

def main():
    """Install all required packages for advanced features"""
    print("🚀 Installing advanced Instagram photo analyzer dependencies...")
    
    # Required packages for advanced features
    packages = [
        "opencv-python",      # Computer vision analysis
        "numpy",              # Numerical computations
        "scikit-learn",       # Machine learning utilities
        "scipy",              # Scientific computing
        "matplotlib",         # Plotting (for analytics)
        "seaborn",           # Statistical visualization
        "pandas",            # Data manipulation
        "nltk",              # Natural language processing
        "textblob",          # Text processing
    ]
    
    failed_packages = []
    
    for package in packages:
        if not install_package(package):
            failed_packages.append(package)
    
    # Special check for OpenCV
    if not check_opencv():
        print("\n🔧 Trying alternative OpenCV installation...")
        if not install_package("opencv-python-headless"):
            failed_packages.append("opencv-python")
    
    # Download NLTK data
    try:
        import nltk
        print("📥 Downloading NLTK data...")
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('vader_lexicon', quiet=True)
        print("✅ NLTK data downloaded")
    except Exception as e:
        print(f"⚠️ NLTK data download failed: {e}")
    
    # Summary
    if failed_packages:
        print(f"\n❌ Failed to install: {', '.join(failed_packages)}")
        print("Please install these manually or check your Python environment.")
        return False
    else:
        print("\n🎉 All advanced features installed successfully!")
        print("\nYou can now use:")
        print("- Computer vision quality analysis")
        print("- Instagram engagement prediction")
        print("- Semantic context analysis")
        print("- Advanced photo filtering")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
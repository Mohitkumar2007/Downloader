#!/usr/bin/env python3
"""
Test script to verify yt-dlp functionality
"""
import yt_dlp
import sys

def test_ytdlp():
    """Test basic yt-dlp functionality"""
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll (short video)
    
    try:
        # Test info extraction
        print("Testing yt-dlp info extraction...")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            
        print(f"✅ Successfully extracted info:")
        print(f"   Title: {info.get('title', 'N/A')}")
        print(f"   Duration: {info.get('duration', 'N/A')} seconds")
        print(f"   Uploader: {info.get('uploader', 'N/A')}")
        print(f"   View count: {info.get('view_count', 'N/A'):,}")
        
        # Test format availability
        formats = info.get('formats', [])
        video_formats = [f for f in formats if f.get('vcodec') != 'none']
        audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
        
        print(f"   Available video formats: {len(video_formats)}")
        print(f"   Available audio formats: {len(audio_formats)}")
        
        print("\n✅ yt-dlp is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing yt-dlp: {e}")
        return False

if __name__ == "__main__":
    print("Testing yt-dlp installation and functionality...\n")
    success = test_ytdlp()
    
    if success:
        print("\n🎉 All tests passed! Your YouTube downloader should work correctly.")
    else:
        print("\n⚠️ Tests failed. Please check your yt-dlp installation.")
        sys.exit(1)
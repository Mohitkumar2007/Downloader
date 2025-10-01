import streamlit as st
import yt_dlp
import os
import requests
from PIL import Image
import io
import json
from datetime import datetime
import time
import re
from urllib.parse import urlparse
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import platform
from pathlib import Path
# --- Initialize session state ---
if 'download_history' not in st.session_state:
    st.session_state.download_history = []
if 'dark_theme' not in st.session_state:
    st.session_state.dark_theme = False

# --- Helper Functions ---
def get_default_download_path():
    """Get the system's default Downloads folder"""
    try:
        system = platform.system()
        if system == "Windows":
            # Windows Downloads folder
            downloads_path = Path.home() / "Downloads"
        elif system == "Darwin":  # macOS
            downloads_path = Path.home() / "Downloads"
        elif system == "Linux":
            # Try common Linux download locations
            downloads_path = Path.home() / "Downloads"
            if not downloads_path.exists():
                downloads_path = Path.home() / "downloads"
        else:
            # Fallback to home directory
            downloads_path = Path.home() / "Downloads"
        
        # Create the directory if it doesn't exist
        downloads_path.mkdir(exist_ok=True)
        return str(downloads_path)
    
    except Exception as e:
        # Fallback to current directory downloads folder
        fallback_path = os.path.join(os.getcwd(), "downloads")
        os.makedirs(fallback_path, exist_ok=True)
        return fallback_path

def create_robust_session():
    """Create a session with retry strategy and user agent rotation"""
    session = requests.Session()
    
    # Add retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Rotate user agents to avoid detection
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    session.headers.update({'User-Agent': random.choice(user_agents)})
    return session

def get_video_info(url, max_retries=3):
    """Get video information using yt-dlp with error handling and retries"""
    for attempt in range(max_retries):
        try:
            # Add random delay to avoid rate limiting
            if attempt > 0:
                time.sleep(random.uniform(1, 3))
            
            # Configure yt-dlp options for info extraction
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info, None
            
        except Exception as e:
            error_msg = str(e).lower()
            if "403" in error_msg or "forbidden" in error_msg:
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ Attempt {attempt + 1} failed (403 Forbidden). Retrying in {2 + attempt} seconds...")
                    time.sleep(2 + attempt)
                    continue
                else:
                    return None, "❌ **403 Forbidden Error**: This video may be restricted, private, or YouTube is blocking requests. Try:\n\n" \
                                "1. **Wait a few minutes** and try again\n" \
                                "2. **Check if the video is public** and available\n" \
                                "3. **Try a different video** to test\n" \
                                "4. **Use a VPN** if you're in a restricted region\n\n" \
                                "**Note**: YouTube actively blocks automated downloads. This is normal behavior."
            elif "private" in error_msg or "unavailable" in error_msg:
                return None, "❌ **Video Unavailable**: This video is private, deleted, or restricted in your region."
            elif "age" in error_msg:
                return None, "❌ **Age Restricted**: This video requires age verification and cannot be downloaded."
            else:
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ Attempt {attempt + 1} failed: {str(e)[:100]}... Retrying...")
                    time.sleep(1 + attempt)
                    continue
                else:
                    return None, f"❌ **Error**: {str(e)}"
    
    return None, "❌ **Max retries exceeded**: Unable to access the video after multiple attempts."

def add_to_history(item_type, title, file_name, download_time):
    """Add download to history"""
    history_item = {
        'type': item_type,
        'title': title,
        'file_name': file_name,
        'download_time': download_time
    }
    st.session_state.download_history.insert(0, history_item)
    if len(st.session_state.download_history) > 50:  # Keep only last 50 downloads
        st.session_state.download_history = st.session_state.download_history[:50]

def show_mobile_download_success(file_name, file_type):
    """Show mobile-friendly download success message"""
    st.markdown(f"""
    <div style='
        background: linear-gradient(135deg, #00C851 0%, #007E33 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,200,81,0.3);
    '>
        <h3 style='color: white; margin: 0 0 0.5rem 0;'>🎉 Download Successful!</h3>
        <p style='color: #E8F5E8; margin: 0.5rem 0; font-size: 16px;'>
            <strong>{file_type}:</strong> {file_name[:30]}{'...' if len(file_name) > 30 else ''}
        </p>
        <div style='background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; margin: 10px 0;'>
            <p style='color: white; margin: 0; font-size: 14px;'>
                📱 <strong>Mobile:</strong> File saved to Downloads folder<br>
                💻 <strong>Desktop:</strong> Check your Downloads directory
            </p>
        </div>
        <p style='color: #E8F5E8; margin: 0; font-size: 12px;'>
            Tap the download button below to save to your device
        </p>
    </div>
    """, unsafe_allow_html=True)

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def format_duration(seconds):
    """Convert seconds to human readable duration"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

# --- Mobile-responsive CSS ---
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .stApp {
        max-width: 100%;
        padding: 0.5rem;
    }
    
    /* Mobile-friendly button styling */
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        border: none;
        padding: 0.75rem 1rem;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* Responsive columns for mobile */
    @media (max-width: 768px) {
        .row-widget.stHorizontal {
            flex-direction: column;
        }
        
        .stButton > button {
            margin-bottom: 0.5rem;
        }
        
        .stSelectbox, .stTextInput {
            margin-bottom: 1rem;
        }
        
        /* Make metrics stack vertically on mobile */
        .metric-container {
            display: flex;
            flex-direction: column;
        }
    }
    
    /* Improve text input for mobile */
    .stTextInput > div > div > input {
        font-size: 16px;
        padding: 12px;
        border-radius: 10px;
    }
    
    /* Better textarea for mobile */
    .stTextArea textarea {
        font-size: 16px;
        padding: 12px;
        border-radius: 10px;
        min-height: 120px;
    }
    
    /* Responsive images */
    .stImage {
        max-width: 100%;
        height: auto;
    }
    
    /* Mobile-friendly expanders */
    .streamlit-expanderHeader {
        font-size: 16px;
        padding: 12px;
    }
    
    /* Better spacing for mobile */
    .element-container {
        margin-bottom: 1rem;
    }
    
    /* Responsive sidebar */
    .css-1d391kg {
        padding: 1rem 0.5rem;
    }
    
    /* Download button styling */
    .download-button {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        border: none;
        padding: 15px 25px;
        border-radius: 25px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    
    .download-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- App Title ---
st.markdown("""
<div style='text-align: center; padding: 1rem 0;'>
    <h1 style='color: #FF4B4B; font-size: clamp(1.5rem, 5vw, 2.5rem); margin-bottom: 0.5rem;'>🎬 Advanced Downloader</h1>
</div>
""", unsafe_allow_html=True)

# --- Theme Toggle ---
col_theme1, col_theme2, col_theme3 = st.columns([1, 1, 4])
with col_theme1:
    if st.button("🌙" if not st.session_state.dark_theme else "☀️", help="Toggle dark/light theme"):
        st.session_state.dark_theme = not st.session_state.dark_theme
        st.rerun()

# --- Download Path Settings ---
st.sidebar.header("⚙️ Settings")

# Mobile-friendly sidebar notice
st.sidebar.markdown("""
<div style='background: #f0f2f6; padding: 10px; border-radius: 8px; margin-bottom: 1rem;'>
    <p style='margin: 0; font-size: 12px; color: #666;'>
        📱 <strong>Mobile Tip:</strong> Swipe from left edge to access settings
    </p>
</div>
""", unsafe_allow_html=True)

# Get system default Downloads folder
default_downloads = get_default_download_path()

# Display current default path
st.sidebar.info(f"📂 **Default Download Location:**\n`{default_downloads}`")

# Option to use custom path
use_custom_path = st.sidebar.checkbox("📁 Use Custom Download Path", help="Check to specify a different download location")

if use_custom_path:
    custom_path = st.sidebar.text_input(
        "📁 Custom Download Path:", 
        placeholder=default_downloads,
        help="Enter full path where you want files downloaded"
    )
    download_path = custom_path if custom_path else default_downloads
    
    # Validate custom path
    if custom_path:
        try:
            Path(custom_path).mkdir(parents=True, exist_ok=True)
            st.sidebar.success(f"✅ Custom path: `{custom_path}`")
        except Exception as e:
            st.sidebar.error(f"❌ Invalid path, using default: `{default_downloads}`")
            download_path = default_downloads
else:
    download_path = default_downloads

st.sidebar.markdown(f"**📥 Files will be saved to:**\n`{download_path}`")

# --- Troubleshooting Section ---
st.sidebar.markdown("---")
with st.sidebar.expander("🛠️ Troubleshooting Guide", expanded=False):
    st.markdown("""
    **🔇 No Audio in Downloaded Video?**
    
    ✅ **Solution:**
    - Choose options marked "w/ Audio"
    - Avoid "Best Quality" unless you need max resolution
    
    **📋 HTTP Error 403: Forbidden**
    
    🔄 **Quick Fixes:**
    - Wait 5-10 minutes before trying again
    - Try a different video first
    - Copy URL directly from YouTube
    
    📋 **Why this happens:**
    - YouTube blocks automated downloads
    - Too many requests from your IP
    - Video has regional restrictions
    
    💡 **Mobile Tips:**
    - Use Wi-Fi for better downloads
    - Download one video at a time
    - Paste URLs carefully (long-press)
    - Files save to Downloads automatically
    """)

st.sidebar.markdown("---")
st.sidebar.info("🔥 **Pro Tip**: If downloads fail, try waiting a few minutes between attempts. YouTube actively prevents bulk downloading.")

# --- Download Location Info ---
st.info(f"📂 **Files will be saved to your Downloads folder:** `{os.path.basename(download_path)}`")

# --- Mobile-specific help ---
st.markdown("""
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
    <h4 style='color: white; margin: 0 0 0.5rem 0;'>📱 Mobile Users Guide</h4>
    <div style='color: #f0f0f0; font-size: 14px;'>
        <p style='margin: 0.3rem 0;'>✅ <strong>Paste URLs:</strong> Long-press in URL field to paste YouTube links</p>
        <p style='margin: 0.3rem 0;'>✅ <strong>Download files:</strong> Tap download button to save to your device</p>
        <p style='margin: 0.3rem 0;'>✅ <strong>Audio guaranteed:</strong> Choose "w/ Audio" options for video with sound</p>
        <p style='margin: 0.3rem 0;'>✅ <strong>File location:</strong> Files save to your Downloads folder automatically</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Toggle options ---
st.header("📥 Choose Download Type")

# Mobile-responsive layout for download type selection
if st.container():
    # For mobile: stack vertically, for desktop: show in columns
    col1, col2 = st.columns(2)
    with col1:
        toggle_video = st.checkbox("🎥 Download Video", help="Download YouTube videos with audio")
        toggle_image = st.checkbox("🖼️ Download Image", help="Download images or YouTube thumbnails")
    with col2:
        toggle_audio = st.checkbox("🎵 Audio Only", help="Extract audio from YouTube videos")
        toggle_batch = st.checkbox("📚 Batch Download", help="Download multiple videos or playlists")

# --- VIDEO DOWNLOADER ---
if toggle_video:
    st.markdown(
        "<h1 style='text-align: center;color: #FF0000;'>🎥 YouTube Video Downloader</h1>",
        unsafe_allow_html=True
    )
    
    # Audio guarantee information
    st.info("🔊 **Audio Guarantee**: Choose options marked 'w/ Audio' to ensure your video has sound! This prevents the common issue of downloading video-only files.")

    video_link = st.text_input("Enter YouTube video URL:", key="video_url", placeholder="https://www.youtube.com/watch?v=...")
    
    # Enhanced quality and format selection with audio guarantee (mobile-responsive)
    st.markdown("### 🎯 Video Settings")
    
    # Stack vertically on mobile for better UX
    video_format = st.selectbox(
        "📹 Video Format:", 
        ["mp4", "webm"], 
        key="video_format", 
        help="MP4 is more compatible, WebM may have better compression"
    )
    
    quality_option = st.selectbox(
        "🎯 Quality:", 
        ["Best w/ Audio (Recommended)", "720p w/ Audio", "480p w/ Audio", "360p w/ Audio", "Best Quality (May need audio merge)"], 
        key="video_quality", 
        help="Options with 'w/ Audio' guarantee sound!"
    )
    
    # Audio handling option
    st.info("� **Audio Guarantee**: All 'w/ Audio' options ensure your video has sound. 'Best Quality' may require audio merging for highest resolution.")

    download_video_btn = st.button("📥 Download Video", key="video_btn", use_container_width=True, type="primary")

    if download_video_btn and video_link:
        # Enhanced error handling with retries
        with st.spinner("🔍 Fetching video information... (This may take a moment)"):
            video_info, error_msg = get_video_info(video_link)
        
        if error_msg:
            st.error(error_msg)
            st.info("💡 **Troubleshooting Tips:**\n"
                   "- Make sure the URL is a valid YouTube video link\n"
                   "- Try copying the URL directly from YouTube\n"
                   "- Some videos may be region-locked or have restrictions\n"
                   "- Wait a few minutes before trying again")
        else:
            try:
                # Display video info and thumbnail with better layout
                st.subheader(f"📺 {video_info.get('title', 'Unknown Title')}")
                
                # Video information in organized columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    views = video_info.get('view_count', 0)
                    st.metric("👀 Views", f"{views:,}" if views else "N/A")
                    duration = video_info.get('duration', 0)
                    st.metric("⏱️ Duration", format_duration(duration) if duration else "N/A")
                with col2:
                    uploader = video_info.get('uploader', 'Unknown')
                    st.metric("👤 Channel", uploader)
                    upload_date = video_info.get('upload_date', '')
                    if upload_date:
                        formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                        st.metric("📅 Upload Date", formatted_date)
                    else:
                        st.metric("📅 Upload Date", "N/A")
                with col3:
                    like_count = video_info.get('like_count', 0)
                    st.metric("� Likes", f"{like_count:,}" if like_count else "N/A")
                
                # Thumbnail in separate section with proper spacing
                st.markdown("---")
                col_thumb_center, col_empty1, col_empty2 = st.columns([2, 1, 1])
                with col_thumb_center:
                    thumbnail_url = video_info.get('thumbnail', '')
                    if thumbnail_url:
                        st.image(thumbnail_url, caption="🖼️ Video Thumbnail", use_column_width=True)

                # Show available formats
                st.markdown("---")
                st.subheader("🎥 Available Video Formats")
                
                # Get available formats from video info
                formats = video_info.get('formats', [])
                
                # Filter and organize formats (more flexible format matching)
                video_formats = []
                for f in formats:
                    if f.get('vcodec') != 'none':  # Has video
                        height = f.get('height', 0)
                        fps = f.get('fps', 0)
                        filesize = f.get('filesize', 0)
                        has_audio = f.get('acodec') != 'none'
                        ext = f.get('ext', '')
                        
                        # Accept the format if it matches user preference OR is a common video format
                        format_acceptable = (
                            ext == video_format or  # Exact match
                            ext in ['mp4', 'webm', 'mkv'] or  # Common video formats
                            (video_format == 'mp4' and ext in ['m4v', 'mov']) or  # MP4-compatible
                            (video_format == 'webm' and ext in ['webm', 'mkv'])  # WebM-compatible
                        )
                        
                        if format_acceptable and height and height >= 144:  # Minimum quality filter
                            quality_info = f"{height}p"
                            if fps:
                                quality_info += f" ({fps}fps)"
                            if filesize:
                                quality_info += f" - {format_file_size(filesize)}"
                            quality_info += f" - {ext.upper()}"
                            quality_info += " - " + ("With Audio" if has_audio else "Video Only")
                            video_formats.append((height, quality_info, f, has_audio, ext))
                
                # Sort by quality (height) and prefer formats with audio
                video_formats.sort(key=lambda x: (x[0], x[3]), reverse=True)
                
                if video_formats:
                    available_qualities = [f"{q[0]}p ({q[4]})" for q in video_formats[:5]]  # Show top 5 with format
                    st.info(f"📋 Available qualities: {', '.join(available_qualities)}")
                    
                    # Debug info in expander
                    with st.expander("🔍 Debug: Format Details"):
                        st.write(f"Total formats found: {len(video_formats)}")
                        for i, (height, info, fmt, audio, ext) in enumerate(video_formats[:3]):
                            st.write(f"{i+1}. {height}p - {ext} - {'Audio' if audio else 'No Audio'} - ID: {fmt.get('format_id', 'N/A')}")
                else:
                    st.warning("⚠️ No video formats found. Trying alternative approach...")
                    # Try to get any available formats
                    all_formats = video_info.get('formats', [])
                    st.write(f"Total formats available: {len(all_formats)}")
                    
                    if all_formats:
                        # Show some format details for debugging
                        with st.expander("🔍 All Available Formats"):
                            for i, f in enumerate(all_formats[:10]):
                                vcodec = f.get('vcodec', 'none')
                                acodec = f.get('acodec', 'none')
                                ext = f.get('ext', 'unknown')
                                height = f.get('height', 'N/A')
                                st.write(f"{i+1}. {ext} - {height}p - Video: {vcodec != 'none'} - Audio: {acodec != 'none'}")
                
                # Map quality options to selection logic
                quality_map = {
                    "Best w/ Audio (Recommended)": "best_with_audio",
                    "720p w/ Audio": "720p_with_audio", 
                    "480p w/ Audio": "480p_with_audio",
                    "360p w/ Audio": "360p_with_audio",
                    "Best Quality (May need audio merge)": "best_quality"
                }
                
                selection_type = quality_map.get(quality_option, "best_with_audio")
                selected_format = None
                has_audio = True
                
                # Select format based on user choice
                if selection_type == "best_with_audio":
                    # Find best quality format with audio
                    for height, info, fmt, audio, ext in video_formats:
                        if audio:
                            selected_format = fmt
                            has_audio = audio
                            break
                elif selection_type.endswith("_with_audio"):
                    # Find specific quality with audio
                    target_height = int(selection_type.split('p')[0])
                    for height, info, fmt, audio, ext in video_formats:
                        if audio and height <= target_height:
                            selected_format = fmt
                            has_audio = audio
                            break
                    
                    # Fallback to any format with audio if target not found
                    if not selected_format:
                        for height, info, fmt, audio, ext in video_formats:
                            if audio:
                                selected_format = fmt
                                has_audio = audio
                                st.warning(f"⚠️ {target_height}p with audio not available. Using {height}p with audio instead.")
                                break
                else:  # best_quality
                    # Get highest quality (may not have audio)
                    if video_formats:
                        selected_format = video_formats[0][2]
                        has_audio = video_formats[0][3]
                        if not has_audio:
                            st.warning("🔇 **No Audio Warning**: This high-quality stream contains video only. Audio will be missing!")
                
                # Final fallback: use yt-dlp's default format selection if no format found
                if not selected_format and video_formats:
                    # Just use the first available format
                    selected_format = video_formats[0][2]  
                    has_audio = video_formats[0][3]
                    st.info("ℹ️ Using best available format.")

                if selected_format:
                    file_size = selected_format.get('filesize', 0)
                    height = selected_format.get('height', 0)
                    fps = selected_format.get('fps', 0)
                    fps_info = f" @ {fps}fps" if fps else ""
                    
                    # Audio status indicator
                    if has_audio:
                        st.success(f"✅ **Selected Format with Audio:**")
                        audio_status = "🔊 With Audio"
                    else:
                        st.error(f"🔇 **Selected Format (NO AUDIO):**")
                        audio_status = "🔇 Video Only"
                    
                    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                    with col_s1:
                        st.metric("🎯 Quality", f"{height}p{fps_info}" if height else "Default")
                    with col_s2:
                        st.metric("📁 File Size", format_file_size(file_size) if file_size else "Unknown")
                    with col_s3:
                        st.metric("🔊 Audio", audio_status)
                    with col_s4:
                        st.metric("📺 Format", selected_format.get('ext', 'mp4').upper())
                    
                    # Clear warning for video-only streams
                    if not has_audio:
                        st.error("⚠️ **IMPORTANT:** This video will have NO SOUND! Choose a 'w/ Audio' option instead.")
                        
                        # Don't allow download of video-only streams
                        if st.button("🔊 I want version WITH audio instead", key="force_audio", type="primary"):
                            st.rerun()
                        st.stop()  # Prevent download of video-only content

                    # Download with yt-dlp
                    try:
                        download_label = "🔊 Downloading video with audio..." if has_audio else "📹 Downloading video (no audio)..."
                        with st.spinner(download_label):
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            os.makedirs(download_path, exist_ok=True)
                            
                            # Configure yt-dlp options for download
                            if selected_format and 'format_id' in selected_format:
                                # Use specific format if found
                                format_selector = str(selected_format['format_id'])
                            else:
                                # Fallback to yt-dlp's smart selection
                                audio_guaranteed = "w/ Audio" in quality_option
                                if audio_guaranteed:
                                    if video_format == 'mp4':
                                        format_selector = 'best[ext=mp4][acodec!=none]/best[acodec!=none]/best'
                                    else:  # webm
                                        format_selector = 'best[ext=webm][acodec!=none]/best[acodec!=none]/best'
                                else:
                                    format_selector = 'best[ext=' + video_format + ']/best'
                            
                            ydl_opts = {
                                'format': format_selector,
                                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                                'noplaylist': True,
                            }
                            
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([video_link])
                                
                            progress_bar.progress(100)
                            status_text.text("Download completed!")
                            
                            # Find the downloaded file
                            title = video_info.get('title', 'video')
                            # Clean title for filename
                            clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                            file_name = f"{clean_title}.{video_format}"
                            file_path = os.path.join(download_path, file_name)
                            
                            # Find actual downloaded file (yt-dlp might modify filename)
                            actual_files = [f for f in os.listdir(download_path) if f.startswith(clean_title[:20])]
                            if actual_files:
                                file_name = actual_files[-1]  # Get most recent
                                file_path = os.path.join(download_path, file_name)

                        # Add to history with audio status
                        video_type = "Video (with Audio)" if has_audio else "Video (No Audio)"
                        add_to_history(video_type, video_info.get('title', 'Unknown'), file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                        # Mobile-friendly download success notification
                        show_mobile_download_success(file_name, video_type)
                        
                        # Provide download button with audio confirmation
                        if os.path.exists(file_path):
                            download_button_label = "🔊 Save Video (with Audio)" if has_audio else "📹 Save Video (NO AUDIO)"
                            
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    label=download_button_label,
                                    data=f,
                                    file_name=file_name,
                                    mime="video/mp4",
                                    use_container_width=True,
                                    type="primary"
                                )
                        
                        if not has_audio:
                            st.warning("⚠️ Video downloaded but has NO AUDIO! 🔇")
                    
                    except Exception as download_error:
                        error_msg = str(download_error).lower()
                        if "403" in error_msg or "forbidden" in error_msg:
                            st.error("❌ **Download Failed (403 Forbidden)**\n\n"
                                   "YouTube has blocked this download request. This happens when:\n"
                                   "- YouTube detects automated downloading\n"
                                   "- The video has download restrictions\n"
                                   "- Too many requests from your IP\n\n"
                                   "**Try again later or use a different video.**")
                        else:
                            st.error(f"❌ Download failed: {download_error}")
                else:
                    # Last resort: try yt-dlp's default format selection
                    st.warning("⚠️ Using yt-dlp's automatic format selection...")
                    try:
                        with st.spinner("Downloading with automatic format selection..."):
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            os.makedirs(download_path, exist_ok=True)
                            
                            # Use yt-dlp's smart defaults
                            audio_guaranteed = "w/ Audio" in quality_option
                            if audio_guaranteed:
                                format_selector = 'best[acodec!=none]/best'  # Prefer formats with audio
                            else:
                                format_selector = 'best'  # Best available quality
                            
                            ydl_opts = {
                                'format': format_selector,
                                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                                'noplaylist': True,
                            }
                            
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([video_link])
                                
                            progress_bar.progress(100)
                            status_text.text("Download completed!")
                            
                            # Find the downloaded file
                            title = video_info.get('title', 'video')
                            clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                            
                            # Find actual downloaded file
                            actual_files = [f for f in os.listdir(download_path) if f.startswith(clean_title[:20])]
                            if actual_files:
                                file_name = actual_files[-1]
                                file_path = os.path.join(download_path, file_name)
                                
                                # Add to history
                                add_to_history("Video (Auto Format)", video_info.get('title', 'Unknown'), file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                
                                # Provide download button
                                with open(file_path, "rb") as f:
                                    st.download_button(
                                        label="📥 Save Video (Auto Format)",
                                        data=f,
                                        file_name=file_name,
                                        mime="video/mp4"
                                    )
                                st.success("✅ Video downloaded with automatic format selection!")
                            else:
                                st.error("❌ Could not find downloaded file.")
                    
                    except Exception as e:
                        st.error(f"❌ Download failed even with automatic format selection: {e}")
                        st.info("💡 **Suggestions:**\n"
                               "- Try a different video\n"
                               "- Check your internet connection\n"
                               "- The video might have restrictions")

            except Exception as e:
                st.error(f"❌ An error occurred while processing video info: {e}")

# --- AUDIO DOWNLOADER ---
if toggle_audio:
    st.markdown(
        "<h1 style='text-align: center;color: #FF0000;'>🎵 YouTube Audio Downloader</h1>",
        unsafe_allow_html=True
    )

    audio_link = st.text_input("Enter YouTube video URL:", key="audio_url", placeholder="Paste YouTube URL here...")
    
    # Audio format selection with MP3 option (mobile-responsive)
    st.markdown("### 🎵 Audio Settings")
    audio_format = st.selectbox(
        "🎧 Audio Format:", 
        ["mp3", "m4a", "webm"], 
        key="audio_format",
        help="MP3 is most compatible, M4A for Apple devices, WebM for smaller files"
    )
    
    # Note about FFmpeg requirement for MP3
    if audio_format == "mp3":
        st.info("🔧 **Note**: MP3 conversion requires FFmpeg. If you don't have FFmpeg, choose M4A format instead.")
    
    download_audio_btn = st.button("🎵 Download Audio", key="audio_btn", use_container_width=True, type="primary")

    if download_audio_btn and audio_link:
        # Enhanced error handling with retries
        with st.spinner("🔍 Fetching audio information... (This may take a moment)"):
            audio_info, error_msg = get_video_info(audio_link)
        
        if error_msg:
            st.error(error_msg)
            st.info("💡 **Troubleshooting Tips:**\n"
                   "- Make sure the URL is a valid YouTube video link\n"
                   "- Try copying the URL directly from YouTube\n"
                   "- Some videos may be region-locked or have restrictions\n"
                   "- Wait a few minutes before trying again")
        else:
            try:
                # Display audio info with better layout
                st.subheader(f"🎵 {audio_info.get('title', 'Unknown Title')}")
                
                # Audio information in organized columns
                col1, col2 = st.columns(2)
                with col1:
                    duration = audio_info.get('duration', 0)
                    st.metric("⏱️ Duration", format_duration(duration) if duration else "N/A")
                with col2:
                    uploader = audio_info.get('uploader', 'Unknown')
                    st.metric("👤 Channel", uploader)
                
                # Thumbnail in separate section with proper spacing
                st.markdown("---")
                col_thumb_center, col_empty1, col_empty2 = st.columns([2, 1, 1])
                with col_thumb_center:
                    thumbnail_url = audio_info.get('thumbnail', '')
                    if thumbnail_url:
                        st.image(thumbnail_url, caption="🎵 Audio Thumbnail", use_column_width=True)

                # Enhanced audio format selection using yt-dlp
                st.markdown("---")
                st.subheader("🎵 Available Audio Formats")
                
                # Get available audio formats
                formats = audio_info.get('formats', [])
                audio_formats = []
                
                for f in formats:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':  # Audio only
                        ext = f.get('ext', '')
                        abr = f.get('abr', 0)
                        filesize = f.get('filesize', 0)
                        
                        if ext == audio_format or (not audio_formats and ext in ['m4a', 'webm', 'mp3']):
                            audio_formats.append((abr or 0, f, ext, filesize))
                
                # Sort by bitrate (highest first)
                audio_formats.sort(key=lambda x: x[0], reverse=True)
                
                if audio_formats:
                    selected_audio = audio_formats[0][1]  # Best quality
                    bitrate = audio_formats[0][0]
                    filesize = audio_formats[0][3]
                    
                    st.info(f"🎵 Selected Audio Quality: **{bitrate}kbps** - {format_file_size(filesize) if filesize else 'Unknown size'}")
                    
                    # Show available audio qualities
                    available_audio = [f"{int(abr)}kbps ({ext})" for abr, f, ext, fs in audio_formats[:3] if abr]
                    if available_audio:
                        st.info(f"📋 Available audio qualities: {', '.join(available_audio)}")

                    # Download with yt-dlp
                    try:
                        with st.spinner("Downloading audio..."):
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            os.makedirs(download_path, exist_ok=True)
                            
                            # Configure yt-dlp for audio download with format conversion
                            ydl_opts = {
                                'format': 'bestaudio/best',
                                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                                'noplaylist': True,
                            }
                            
                            # Add post-processor for MP3 conversion if needed
                            if audio_format == "mp3":
                                ydl_opts['postprocessors'] = [{
                                    'key': 'FFmpegExtractAudio',
                                    'preferredcodec': 'mp3',
                                    'preferredquality': '192',
                                }]
                            elif audio_format == "m4a":
                                ydl_opts['postprocessors'] = [{
                                    'key': 'FFmpegExtractAudio',
                                    'preferredcodec': 'm4a',
                                    'preferredquality': '192',
                                }]
                            
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([audio_link])
                            
                            progress_bar.progress(100)
                            status_text.text("Download completed!")
                            
                            # Find the downloaded file
                            title = audio_info.get('title', 'audio')
                            clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                            
                            # Find actual downloaded file
                            actual_files = [f for f in os.listdir(download_path) if f.startswith(clean_title[:20])]
                            if actual_files:
                                file_name = actual_files[-1]  # Get most recent
                                file_path = os.path.join(download_path, file_name)
                            else:
                                # Fallback filename
                                file_name = f"{clean_title}.{selected_audio.get('ext', 'm4a')}"
                                file_path = os.path.join(download_path, file_name)

                        # Add to history
                        add_to_history("Audio", audio_info.get('title', 'Unknown'), file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                        # Mobile-friendly download success notification
                        show_mobile_download_success(file_name, "Audio")

                        # Provide download button
                        if os.path.exists(file_path):
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    label="🎵 Save Audio to Device",
                                    data=f,
                                    file_name=file_name,
                                    mime="audio/mp4",
                                    use_container_width=True,
                                    type="primary"
                                )
                    
                    except Exception as download_error:
                        error_msg = str(download_error).lower()
                        if "403" in error_msg or "forbidden" in error_msg:
                            st.error("❌ **Download Failed (403 Forbidden)**\n\n"
                                   "YouTube has blocked this download request. This happens when:\n"
                                   "- YouTube detects automated downloading\n"
                                   "- The audio has download restrictions\n"
                                   "- Too many requests from your IP\n\n"
                                   "**Try again later or use a different video.**")
                        else:
                            st.error(f"❌ Download failed: {download_error}")
                else:
                    st.error("No audio stream found.")

            except Exception as e:
                st.error(f"❌ An error occurred while processing audio info: {e}")

# --- BATCH DOWNLOADER ---
if toggle_batch:
    st.markdown(
        "<h1 style='text-align: center;color: #FF0000;'>📚 Batch Downloader</h1>",
        unsafe_allow_html=True
    )

    batch_option = st.radio("Batch Download Type:", ["Multiple URLs", "YouTube Playlist"], key="batch_type")
    
    if batch_option == "Multiple URLs":
        urls_text = st.text_area(
            "Enter YouTube URLs (one per line):", 
            key="batch_urls", 
            height=150,
            placeholder="https://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...\n..."
        )
        batch_format = st.selectbox("Download as:", ["Video", "Audio Only"], key="batch_format")
        
        if st.button("📚 Download All", key="batch_btn", use_container_width=True, type="primary"):
            urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
            if urls:
                progress_container = st.container()
                with progress_container:
                    overall_progress = st.progress(0)
                    status_text = st.empty()
                    
                    successful_downloads = 0
                    failed_downloads = 0
                    
                    for i, url in enumerate(urls):
                        try:
                            status_text.text(f"Processing {i+1}/{len(urls)}: {url}")
                            
                            # Configure yt-dlp options for batch download
                            if batch_format == "Video":
                                ydl_opts = {
                                    'format': 'best[ext=mp4]/best',
                                    'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                                    'noplaylist': True,
                                }
                            else:  # Audio
                                ydl_opts = {
                                    'format': 'bestaudio/best',
                                    'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                                    'noplaylist': True,
                                    'postprocessors': [{
                                        'key': 'FFmpegExtractAudio',
                                        'preferredcodec': 'mp3',
                                        'preferredquality': '192',
                                    }],
                                }
                            
                            os.makedirs(download_path, exist_ok=True)
                            
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                info = ydl.extract_info(url, download=False)
                                title = info.get('title', 'Unknown')
                                ydl.download([url])
                                
                                # Find downloaded file
                                clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                                actual_files = [f for f in os.listdir(download_path) if f.startswith(clean_title[:20])]
                                file_name = actual_files[-1] if actual_files else f"{clean_title}.mp4"
                                
                                add_to_history(batch_format, title, file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                successful_downloads += 1
                                
                        except Exception as e:
                            st.error(f"Failed to download {url}: {e}")
                            failed_downloads += 1
                        
                        overall_progress.progress((i + 1) / len(urls))
                    
                    status_text.text(f"Batch download completed!")
                    st.success(f"✅ Successfully downloaded: {successful_downloads}")
                    if failed_downloads > 0:
                        st.warning(f"⚠️ Failed downloads: {failed_downloads}")
    
    elif batch_option == "YouTube Playlist":
        playlist_url = st.text_input(
            "Enter YouTube Playlist URL:", 
            key="playlist_url",
            placeholder="https://www.youtube.com/playlist?list=..."
        )
        playlist_format = st.selectbox("Download as:", ["Video", "Audio Only"], key="playlist_format")
        
        if playlist_url and st.button("📋 Load Playlist Info", key="playlist_info_btn", use_container_width=True):
            try:
                with st.spinner("Loading playlist information..."):
                    ydl_opts = {
                        'quiet': True,
                        'extract_flat': True,
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        playlist_info = ydl.extract_info(playlist_url, download=False)
                        
                    playlist_title = playlist_info.get('title', 'Unknown Playlist')
                    entries = playlist_info.get('entries', [])
                    
                    st.success(f"Playlist: {playlist_title}")
                    st.info(f"Total videos: {len(entries)}")
                    
                    # Show first few video titles
                    st.subheader("Preview (first 5 videos):")
                    for i, entry in enumerate(entries[:5]):
                        title = entry.get('title', '[Unable to load title]')
                        st.write(f"{i+1}. {title}")
                    
                    if len(entries) > 5:
                        st.write(f"... and {len(entries) - 5} more videos")
                        
            except Exception as e:
                st.error(f"Error loading playlist: {e}")
        
        if playlist_url and st.button("📚 Download Playlist", key="playlist_download_btn", use_container_width=True, type="primary"):
            try:
                with st.spinner("Processing playlist..."):
                    ydl_opts = {
                        'quiet': True,
                        'extract_flat': True,
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        playlist_info = ydl.extract_info(playlist_url, download=False)
                        
                    entries = playlist_info.get('entries', [])
                    urls = [f"https://www.youtube.com/watch?v={entry['id']}" for entry in entries if entry.get('id')]
                
                progress_container = st.container()
                with progress_container:
                    overall_progress = st.progress(0)
                    status_text = st.empty()
                    
                    successful_downloads = 0
                    failed_downloads = 0
                    
                    for i, url in enumerate(urls):
                        try:
                            status_text.text(f"Downloading {i+1}/{len(urls)}")
                            
                            # Configure yt-dlp options
                            if playlist_format == "Video":
                                ydl_opts = {
                                    'format': 'best[ext=mp4]/best',
                                    'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                                    'noplaylist': True,
                                }
                            else:  # Audio
                                ydl_opts = {
                                    'format': 'bestaudio/best',
                                    'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                                    'noplaylist': True,
                                    'postprocessors': [{
                                        'key': 'FFmpegExtractAudio',
                                        'preferredcodec': 'mp3',
                                        'preferredquality': '192',
                                    }],
                                }
                            
                            os.makedirs(download_path, exist_ok=True)
                            
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                info = ydl.extract_info(url, download=False)
                                title = info.get('title', 'Unknown')
                                ydl.download([url])
                                
                                # Find downloaded file
                                clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                                actual_files = [f for f in os.listdir(download_path) if f.startswith(clean_title[:20])]
                                file_name = actual_files[-1] if actual_files else f"{clean_title}.mp4"
                                
                                add_to_history(playlist_format, title, file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                successful_downloads += 1
                                
                        except Exception as e:
                            st.error(f"Failed to download {url}: {e}")
                            failed_downloads += 1
                        
                        overall_progress.progress((i + 1) / len(urls))
                    
                    status_text.text(f"Playlist download completed!")
                    st.success(f"✅ Successfully downloaded: {successful_downloads}")
                    if failed_downloads > 0:
                        st.warning(f"⚠️ Failed downloads: {failed_downloads}")
                        
            except Exception as e:
                st.error(f"Error downloading playlist: {e}")

# --- IMAGE DOWNLOADER ---
if toggle_image:
    st.markdown(
        "<h1 style='text-align: center;color: #FF0000;'>🖼️ Advanced Image Downloader</h1>",
        unsafe_allow_html=True
    )

    # Image download options
    image_option = st.radio("Image Source:", ["Single Image URL", "YouTube Thumbnail", "Batch Image URLs"], key="image_option")
    
    if image_option == "Single Image URL":
        image_link = st.text_input(
            "Enter Image URL:", 
            key="image_url",
            placeholder="https://example.com/image.jpg"
        )
        
        # Image format and resize options (mobile-responsive)
        st.markdown("### 🎨 Image Settings")
        
        image_format = st.selectbox(
            "💾 Save as:", 
            ["Original", "JPEG", "PNG", "WebP"], 
            key="img_format",
            help="JPEG for photos, PNG for graphics, WebP for smaller files"
        )
        
        resize_option = st.selectbox(
            "📐 Resize:", 
            ["Original Size", "1920x1080", "1280x720", "800x600", "Custom"], 
            key="img_resize",
            help="Choose size that works best for your device"
        )
        
        if resize_option == "Custom":
            st.markdown("#### 📏 Custom Dimensions")
            col_w, col_h = st.columns(2)
            with col_w:
                custom_width = st.number_input(
                    "Width (px):", 
                    min_value=1, 
                    value=800, 
                    key="custom_w",
                    help="Image width in pixels"
                )
            with col_h:
                custom_height = st.number_input(
                    "Height (px):", 
                    min_value=1, 
                    value=600, 
                    key="custom_h",
                    help="Image height in pixels"
                )
        
        download_image_btn = st.button("🖼️ Download Image", key="image_btn", use_container_width=True, type="primary")

        if download_image_btn and image_link:
            try:
                with st.spinner("Downloading image..."):
                    response = requests.get(image_link)
                    if response.status_code != 200:
                        st.error("Failed to retrieve image. Check the URL.")
                    else:
                        image_data = response.content
                        
                        # Validate and process image
                        try:
                            img = Image.open(io.BytesIO(image_data))
                            original_size = img.size
                            st.success(f"✅ Image loaded: {original_size[0]}x{original_size[1]} pixels")
                            
                            # Resize if needed
                            if resize_option != "Original Size":
                                if resize_option == "Custom":
                                    new_size = (custom_width, custom_height)
                                else:
                                    size_map = {
                                        "1920x1080": (1920, 1080),
                                        "1280x720": (1280, 720),
                                        "800x600": (800, 600)
                                    }
                                    new_size = size_map[resize_option]
                                
                                img = img.resize(new_size, Image.Resampling.LANCZOS)
                                st.info(f"🔄 Resized to: {new_size[0]}x{new_size[1]} pixels")
                            
                            # Display image
                            st.image(img, caption="Downloaded Image", use_column_width=True)
                            
                            # Convert format if needed
                            file_name = os.path.basename(urlparse(image_link).path) or "downloaded_image"
                            
                            if image_format != "Original":
                                # Convert to RGB if saving as JPEG
                                if image_format == "JPEG" and img.mode in ("RGBA", "P"):
                                    img = img.convert("RGB")
                                
                                # Save in specified format
                                img_buffer = io.BytesIO()
                                img.save(img_buffer, format=image_format)
                                image_data = img_buffer.getvalue()
                                
                                # Update file extension
                                file_name = os.path.splitext(file_name)[0] + f".{image_format.lower()}"
                                mime_type = f"image/{image_format.lower()}"
                            else:
                                mime_type = "image/jpeg"
                            
                            # Add to history
                            add_to_history("Image", file_name, file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            
                            # Download button
                            st.download_button(
                                label="📥 Save Image to Device",
                                data=image_data,
                                file_name=file_name,
                                mime=mime_type
                            )
                            st.success("✅ Image ready for download!")
                            
                        except Exception as e:
                            st.error(f"Cannot process this image: {e}")

            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
    
    elif image_option == "YouTube Thumbnail":
        youtube_link = st.text_input(
            "Enter YouTube Video URL:", 
            key="yt_thumb_url",
            placeholder="https://www.youtube.com/watch?v=..."
        )
        thumb_quality = st.selectbox("Thumbnail Quality:", ["maxresdefault", "hqdefault", "mqdefault", "sddefault"], key="thumb_quality")
        
        if youtube_link and st.button("🖼️ Download Thumbnail", key="yt_thumb_btn", use_container_width=True, type="primary"):
            try:
                with st.spinner("Fetching thumbnail..."):
                    # Get video info using yt-dlp
                    ydl_opts = {
                        'quiet': True,
                        'no_warnings': True,
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(youtube_link, download=False)
                        
                    video_id = info.get('id', '')
                    title = info.get('title', 'Unknown Video')
                    
                    # Try different thumbnail qualities
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/{thumb_quality}.jpg"
                    
                    response = requests.get(thumbnail_url)
                    if response.status_code == 200:
                        image_data = response.content
                        img = Image.open(io.BytesIO(image_data))
                        
                        st.image(img, caption=f"Thumbnail: {title}", use_column_width=True)
                        
                        file_name = f"{title}_{thumb_quality}.jpg"
                        # Clean filename
                        file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
                        
                        add_to_history("Thumbnail", title, file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        
                        st.download_button(
                            label="📥 Save Thumbnail",
                            data=image_data,
                            file_name=file_name,
                            mime="image/jpeg"
                        )
                        st.success("✅ Thumbnail ready!")
                    else:
                        st.error("Failed to fetch thumbnail.")
                        
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
    
    elif image_option == "Batch Image URLs":
        batch_image_urls = st.text_area(
            "Enter Image URLs (one per line):", 
            key="batch_image_urls", 
            height=150,
            placeholder="https://example.com/image1.jpg\nhttps://example.com/image2.png\n..."
        )
        batch_img_format = st.selectbox("Convert all to:", ["Keep Original", "JPEG", "PNG", "WebP"], key="batch_img_format")
        
        if st.button("🖼️ Download All Images", key="batch_img_btn", use_container_width=True, type="primary"):
            urls = [url.strip() for url in batch_image_urls.split('\n') if url.strip()]
            if urls:
                progress_container = st.container()
                with progress_container:
                    overall_progress = st.progress(0)
                    status_text = st.empty()
                    
                    successful_downloads = 0
                    failed_downloads = 0
                    
                    for i, url in enumerate(urls):
                        try:
                            status_text.text(f"Downloading image {i+1}/{len(urls)}")
                            response = requests.get(url)
                            
                            if response.status_code == 200:
                                image_data = response.content
                                img = Image.open(io.BytesIO(image_data))
                                
                                file_name = os.path.basename(urlparse(url).path) or f"image_{i+1}.jpg"
                                
                                if batch_img_format != "Keep Original":
                                    if batch_img_format == "JPEG" and img.mode in ("RGBA", "P"):
                                        img = img.convert("RGB")
                                    
                                    img_buffer = io.BytesIO()
                                    img.save(img_buffer, format=batch_img_format)
                                    image_data = img_buffer.getvalue()
                                    file_name = os.path.splitext(file_name)[0] + f".{batch_img_format.lower()}"
                                
                                # Save locally
                                os.makedirs(download_path, exist_ok=True)
                                local_path = os.path.join(download_path, file_name)
                                with open(local_path, 'wb') as f:
                                    f.write(image_data)
                                
                                add_to_history("Image", file_name, file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                successful_downloads += 1
                            else:
                                failed_downloads += 1
                                
                        except Exception as e:
                            st.error(f"Failed to download {url}: {e}")
                            failed_downloads += 1
                        
                        overall_progress.progress((i + 1) / len(urls))
                    
                    status_text.text(f"Batch image download completed!")
                    st.success(f"✅ Successfully downloaded: {successful_downloads} images")
                    if failed_downloads > 0:
                        st.warning(f"⚠️ Failed downloads: {failed_downloads}")

# --- DOWNLOAD HISTORY ---
if st.sidebar.button("📜 View Download History", use_container_width=True):
    st.header("📜 Download History")
    
    if st.session_state.download_history:
        for i, item in enumerate(st.session_state.download_history):
            with st.expander(f"{item['type']} - {item['title'][:50]}{'...' if len(item['title']) > 50 else ''}"):
                st.write(f"**Type:** {item['type']}")
                st.write(f"**Title:** {item['title']}")
                st.write(f"**File:** {item['file_name']}")
                st.write(f"**Downloaded:** {item['download_time']}")
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.download_history = []
            st.success("History cleared!")
            st.rerun()
    else:
        st.info("No downloads yet!")

# --- FILE MANAGER ---
if st.sidebar.button("📁 View Downloaded Files", use_container_width=True):
    st.header("📁 Downloaded Files")
    
    # Show current download location
    st.info(f"📂 **Download Location:** `{download_path}`")
    
    # Button to open Downloads folder (Windows/Mac/Linux compatible)
    col_open1, col_open2 = st.columns(2)
    with col_open1:
        if st.button("🗂️ Open Downloads Folder", help="Open the downloads folder in your file explorer", use_container_width=True):
            try:
                system = platform.system()
                if system == "Windows":
                    os.startfile(download_path)
                elif system == "Darwin":  # macOS
                    os.system(f"open '{download_path}'")
                elif system == "Linux":
                    os.system(f"xdg-open '{download_path}'")
                st.success("📂 Downloads folder opened!")
            except Exception as e:
                st.error(f"❌ Could not open folder: {e}")
    
    with col_open2:
        if st.button("📋 Copy Path", help="Copy the download path to clipboard", use_container_width=True):
            try:
                # For web deployment, show the path for manual copy
                st.code(download_path, language=None)
                st.success("📋 Path displayed above for copying!")
            except Exception:
                st.info(f"📋 Copy this path: `{download_path}`")
    
    # File listing
    if os.path.exists(download_path):
        files = [f for f in os.listdir(download_path) if os.path.isfile(os.path.join(download_path, f))]
        if files:
            st.subheader(f"📄 Files ({len(files)} total)")
            
            # Sort files by modification time (newest first)
            files.sort(key=lambda x: os.path.getmtime(os.path.join(download_path, x)), reverse=True)
            
            # Mobile-responsive file listing
            for file in files:
                file_path = os.path.join(download_path, file)
                file_size = os.path.getsize(file_path)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # File type icon
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in ['.mp4', '.webm', '.avi', '.mov']:
                    icon = "🎥"
                elif file_ext in ['.mp3', '.wav', '.m4a']:
                    icon = "🎵"
                elif file_ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                    icon = "🖼️"
                else:
                    icon = "📄"
                
                # Mobile-friendly file display with expander
                with st.expander(f"{icon} {file[:30]}{'...' if len(file) > 30 else ''}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**📁 File:** {file}")
                        st.write(f"**📊 Size:** {format_file_size(file_size)}")
                    with col2:
                        st.write(f"**📅 Modified:** {file_modified.strftime('%m/%d %H:%M')}")
                        # Delete button for individual files
                        if st.button(f"🗑️ Delete {file[:20]}{'...' if len(file) > 20 else ''}", key=f"delete_{file}", help=f"Delete {file}", use_container_width=True):
                            try:
                                os.remove(file_path)
                                st.success(f"🗑️ Deleted {file}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Could not delete {file}: {e}")
        else:
            st.info("📂 No files in download folder yet!")
    else:
        st.info("📂 Download folder doesn't exist yet!")

# --- STATISTICS ---
if st.sidebar.button("📊 Statistics", use_container_width=True):
    st.header("📊 Download Statistics")
    
    if st.session_state.download_history:
        total_downloads = len(st.session_state.download_history)
        
        # Count by type
        type_counts = {}
        for item in st.session_state.download_history:
            type_counts[item['type']] = type_counts.get(item['type'], 0) + 1
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Downloads", total_downloads)
        with col2:
            most_common_type = max(type_counts, key=type_counts.get) if type_counts else "None"
            st.metric("Most Downloaded Type", most_common_type)
        
        st.subheader("Download Types")
        for download_type, count in type_counts.items():
            st.write(f"**{download_type}:** {count}")
    else:
        st.info("No statistics available yet!")

# --- Mobile-Responsive Footer ---
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin: 20px 0;'>
        <h4 style='color: white; margin-bottom: 10px;'>🎬 Advanced Downloader v3.1</h4>
        <p style='color: #f0f0f0; margin: 5px 0;'>Made with ❤️ by <a href="https://github.com/Mohitkumar2007" style='color: #FFD700;'>Mohit Kumar A</a></p>
        <p style='font-size: clamp(10px, 2.5vw, 12px); color: #e0e0e0; margin: 10px 0;'>📱 Mobile Optimized • 🔊 Audio Guaranteed • 📁 Downloads Folder • ✨ Smart Quality Selection</p>
        <div style='margin-top: 15px; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 10px;'>
            <p style='color: #FFD700; font-size: clamp(10px, 2.5vw, 12px); margin: 0;'>🚀 <strong>Pro Tip for Mobile Users:</strong></p>
            <p style='color: #f0f0f0; font-size: clamp(8px, 2vw, 10px); margin: 5px 0 0 0;'>Tap and hold download links to save directly to your device!</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
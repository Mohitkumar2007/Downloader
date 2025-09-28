import streamlit as st
from pytubefix import YouTube, Playlist
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

# --- Initialize session state ---
if 'download_history' not in st.session_state:
    st.session_state.download_history = []
if 'dark_theme' not in st.session_state:
    st.session_state.dark_theme = False

# --- Helper Functions ---
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

def create_youtube_object(url, max_retries=3):
    """Create YouTube object with error handling and retries"""
    for attempt in range(max_retries):
        try:
            # Add random delay to avoid rate limiting
            if attempt > 0:
                time.sleep(random.uniform(1, 3))
            
            # Create YouTube object with custom session
            yt = YouTube(url)
            
            # Test if we can access basic info
            _ = yt.title  # This will trigger the actual request
            return yt, None
            
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

# --- App Title ---
st.title("🎬 Advanced Downloader for Chethana")

# --- Theme Toggle ---
col_theme1, col_theme2, col_theme3 = st.columns([1, 1, 4])
with col_theme1:
    if st.button("🌙" if not st.session_state.dark_theme else "☀️"):
        st.session_state.dark_theme = not st.session_state.dark_theme
        st.rerun()

# --- Custom Download Path ---
st.sidebar.header("⚙️ Settings")
custom_path = st.sidebar.text_input("📁 Custom Download Path (optional):", placeholder="downloads")
download_path = custom_path if custom_path else "downloads"

# --- Troubleshooting Section ---
with st.sidebar.expander("🛠️ Troubleshooting 403 Errors"):
    st.markdown("""
    **If you see "HTTP Error 403: Forbidden":**
    
    🔄 **Quick Fixes:**
    - Wait 5-10 minutes before trying again
    - Try a different video first
    - Copy URL directly from YouTube
    - Check if video is public/available
    
    📋 **Why this happens:**
    - YouTube blocks automated downloads
    - Too many requests from your IP
    - Video has regional restrictions
    - Video is private/deleted/age-restricted
    
    💡 **Tips:**
    - Use shorter, older videos first
    - Avoid popular/trending videos
    - Don't download too many videos quickly
    - Try using a VPN if region-locked
    """)

st.sidebar.markdown("---")
st.sidebar.info("🔥 **Pro Tip**: If downloads fail, try waiting a few minutes between attempts. YouTube actively prevents bulk downloading.")

# --- Toggle options ---
st.header("📥 Choose Download Type")
col1, col2, col3, col4 = st.columns(4)
with col1:
    toggle_video = st.checkbox("🎥 Download Video")
with col2:
    toggle_audio = st.checkbox("🎵 Audio Only")
with col3:
    toggle_image = st.checkbox("🖼️ Download Image")
with col4:
    toggle_batch = st.checkbox("📚 Batch Download")

# --- VIDEO DOWNLOADER ---
if toggle_video:
    st.markdown(
        "<h1 style='text-align: center;color: #FF0000;'>🎥 YouTube Video Downloader</h1>",
        unsafe_allow_html=True
    )

    video_link = st.text_input("Enter YouTube video URL:", key="video_url")
    
    # Enhanced quality and format selection
    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        video_format = st.selectbox("📹 Video Format:", ["mp4", "webm"], key="video_format", help="MP4 is more compatible, WebM may have better compression")
    with col_q2:
        quality_option = st.selectbox("🎯 Quality:", ["Best Available (HD)", "1080p (Full HD)", "720p (HD)", "480p (SD)", "360p (Low)", "240p (Mobile)"], key="video_quality", help="Higher quality = larger file size")
    with col_q3:
        stream_type = st.selectbox("📺 Stream Type:", ["Progressive (Video+Audio)", "Adaptive (Video Only)"], key="stream_type", help="Progressive: All-in-one file, Adaptive: Higher quality but video only")

    download_video_btn = st.button("📥 Download Video", key="video_btn")

    if download_video_btn and video_link:
        # Enhanced error handling with retries
        with st.spinner("🔍 Fetching video information... (This may take a moment)"):
            yt, error_msg = create_youtube_object(video_link)
        
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
                st.subheader(f"📺 {yt.title}")
                
                # Video information in organized columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("👀 Views", f"{yt.views:,}" if yt.views else "N/A")
                    st.metric("⏱️ Duration", format_duration(yt.length))
                with col2:
                    st.metric("👤 Channel", yt.author)
                    st.metric("📅 Upload Date", yt.publish_date.strftime("%Y-%m-%d") if yt.publish_date else "N/A")
                with col3:
                    st.metric("📊 Rating", f"{yt.rating}/5" if yt.rating else "N/A")
                
                # Thumbnail in separate section with proper spacing
                st.markdown("---")
                col_thumb_center, col_empty1, col_empty2 = st.columns([2, 1, 1])
                with col_thumb_center:
                    st.image(yt.thumbnail_url, caption="🖼️ Video Thumbnail", use_column_width=True)

                # Show available streams with better quality selection
                st.markdown("---")
                st.subheader("🎥 Available Video Streams")
                
                # Get all available streams
                all_streams = yt.streams.filter(file_extension=video_format, type='video')
                
                # Display available qualities
                available_qualities = []
                for stream in all_streams:
                    if stream.resolution:
                        quality_info = f"{stream.resolution} ({stream.fps}fps) - {format_file_size(stream.filesize) if hasattr(stream, 'filesize') else 'Unknown size'}"
                        available_qualities.append((stream.resolution, quality_info, stream))
                
                if available_qualities:
                    st.info(f"📋 Available qualities: {', '.join([q[0] for q in available_qualities])}")
                
                # Enhanced stream selection logic with better quality handling
                selected_stream = None
                
                # Map quality options to resolution values
                quality_map = {
                    "Best Available (HD)": None,
                    "1080p (Full HD)": "1080p",
                    "720p (HD)": "720p", 
                    "480p (SD)": "480p",
                    "360p (Low)": "360p",
                    "240p (Mobile)": "240p"
                }
                
                target_quality = quality_map.get(quality_option)
                prefer_progressive = stream_type == "Progressive (Video+Audio)"
                
                if quality_option == "Best Available (HD)":
                    if prefer_progressive:
                        # Get best progressive stream (video + audio combined)
                        selected_stream = yt.streams.filter(
                            file_extension=video_format, 
                            progressive=True
                        ).order_by('resolution').desc().first()
                    
                    # If no progressive or user prefers adaptive, get best adaptive video
                    if not selected_stream or not prefer_progressive:
                        selected_stream = yt.streams.filter(
                            file_extension=video_format, 
                            adaptive=True, 
                            type='video'
                        ).order_by('resolution').desc().first()
                    
                    # Final fallback
                    if not selected_stream:
                        selected_stream = yt.streams.get_highest_resolution()
                        
                else:
                    # Specific quality requested
                    if prefer_progressive:
                        # Try progressive stream at target quality
                        selected_stream = yt.streams.filter(
                            file_extension=video_format, 
                            progressive=True, 
                            res=target_quality
                        ).first()
                    
                    # If no progressive stream or user prefers adaptive
                    if not selected_stream or not prefer_progressive:
                        selected_stream = yt.streams.filter(
                            file_extension=video_format, 
                            adaptive=True, 
                            type='video',
                            res=target_quality
                        ).first()
                    
                    # Fallback to closest available quality
                    if not selected_stream:
                        quality_fallback = ["720p", "480p", "360p", "1080p", "240p"]
                        if target_quality in quality_fallback:
                            quality_fallback.remove(target_quality)
                        quality_fallback.insert(0, target_quality)
                        
                        for fallback_quality in quality_fallback[1:]:  # Skip first (original target)
                            if prefer_progressive:
                                selected_stream = yt.streams.filter(
                                    file_extension=video_format, 
                                    progressive=True, 
                                    res=fallback_quality
                                ).first()
                            else:
                                selected_stream = yt.streams.filter(
                                    file_extension=video_format, 
                                    adaptive=True, 
                                    type='video',
                                    res=fallback_quality
                                ).first()
                            
                            if selected_stream:
                                st.warning(f"⚠️ {target_quality} not available. Using {fallback_quality} instead.")
                                break
                    
                    # Final fallback
                    if not selected_stream:
                        selected_stream = yt.streams.get_highest_resolution()
                        st.warning(f"⚠️ Requested quality not available. Using highest available quality.")

                if selected_stream:
                    file_size = selected_stream.filesize if hasattr(selected_stream, 'filesize') else 0
                    fps_info = f" @ {selected_stream.fps}fps" if hasattr(selected_stream, 'fps') and selected_stream.fps else ""
                    stream_type_info = "Progressive" if selected_stream.is_progressive else "Adaptive"
                    
                    st.success(f"✅ **Selected Stream:**")
                    col_s1, col_s2, col_s3 = st.columns(3)
                    with col_s1:
                        st.metric("🎯 Quality", f"{selected_stream.resolution or 'Default'}{fps_info}")
                    with col_s2:
                        st.metric("📁 File Size", format_file_size(file_size))
                    with col_s3:
                        st.metric("📺 Type", stream_type_info)
                    
                    if not selected_stream.is_progressive:
                        st.warning("⚠️ **Note:** Adaptive streams contain video only. Audio will need to be downloaded separately if needed.")

                    # Download with progress
                    try:
                        with st.spinner("Downloading video..."):
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            os.makedirs(download_path, exist_ok=True)
                            file_path = selected_stream.download(output_path=download_path)
                            file_name = os.path.basename(file_path)
                            
                            progress_bar.progress(100)
                            status_text.text("Download completed!")

                        # Add to history
                        add_to_history("Video", yt.title, file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                        # Provide download button
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="📥 Save Video to Device",
                                data=f,
                                file_name=file_name,
                                mime="video/mp4"
                            )
                        st.success("✅ Video download ready!")
                    
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
                    st.error("No suitable stream found for the selected format and quality.")

            except Exception as e:
                st.error(f"❌ An error occurred while processing video info: {e}")

# --- AUDIO DOWNLOADER ---
if toggle_audio:
    st.markdown(
        "<h1 style='text-align: center;color: #FF0000;'>🎵 YouTube Audio Downloader</h1>",
        unsafe_allow_html=True
    )

    audio_link = st.text_input("Enter YouTube video URL:", key="audio_url")
    
    # Audio format selection
    audio_format = st.selectbox("Audio Format:", ["mp4", "webm"], key="audio_format")
    
    download_audio_btn = st.button("🎵 Download Audio", key="audio_btn")

    if download_audio_btn and audio_link:
        # Enhanced error handling with retries
        with st.spinner("🔍 Fetching audio information... (This may take a moment)"):
            yt, error_msg = create_youtube_object(audio_link)
        
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
                st.subheader(f"🎵 {yt.title}")
                
                # Audio information in organized columns
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("⏱️ Duration", format_duration(yt.length))
                with col2:
                    st.metric("👤 Channel", yt.author)
                
                # Thumbnail in separate section with proper spacing
                st.markdown("---")
                col_thumb_center, col_empty1, col_empty2 = st.columns([2, 1, 1])
                with col_thumb_center:
                    st.image(yt.thumbnail_url, caption="🎵 Audio Thumbnail", use_column_width=True)

                # Enhanced audio stream selection
                st.markdown("---")
                st.subheader("🎵 Available Audio Streams")
                
                # Get best quality audio stream
                audio_streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
                
                if audio_format == "mp4":
                    audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
                elif audio_format == "webm":
                    audio_stream = yt.streams.filter(only_audio=True, file_extension='webm').order_by('abr').desc().first()
                
                # Fallback to any audio stream
                if not audio_stream:
                    audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()

                if audio_stream:
                    file_size = audio_stream.filesize if hasattr(audio_stream, 'filesize') else 0
                    bitrate = audio_stream.abr or 'Default'
                    st.info(f"🎵 Selected Audio Quality: **{bitrate}** - {format_file_size(file_size)}")
                    
                    # Show available audio qualities
                    available_audio = [f"{stream.abr} ({stream.mime_type})" for stream in audio_streams[:3] if stream.abr]
                    if available_audio:
                        st.info(f"📋 Available audio qualities: {', '.join(available_audio)}")

                    # Download with progress
                    try:
                        with st.spinner("Downloading audio..."):
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            os.makedirs(download_path, exist_ok=True)
                            file_path = audio_stream.download(output_path=download_path)
                            file_name = os.path.basename(file_path)
                            
                            progress_bar.progress(100)
                            status_text.text("Download completed!")

                        # Add to history
                        add_to_history("Audio", yt.title, file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                        # Provide download button
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="🎵 Save Audio to Device",
                                data=f,
                                file_name=file_name,
                                mime="audio/mp4"
                            )
                        st.success("✅ Audio download ready!")
                    
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
        urls_text = st.text_area("Enter YouTube URLs (one per line):", key="batch_urls", height=150)
        batch_format = st.selectbox("Download as:", ["Video", "Audio Only"], key="batch_format")
        
        if st.button("📚 Download All", key="batch_btn"):
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
                            yt = YouTube(url)
                            
                            if batch_format == "Video":
                                stream = yt.streams.get_highest_resolution()
                            else:
                                stream = yt.streams.filter(only_audio=True).first()
                            
                            if stream:
                                os.makedirs(download_path, exist_ok=True)
                                file_path = stream.download(output_path=download_path)
                                file_name = os.path.basename(file_path)
                                add_to_history(batch_format, yt.title, file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                successful_downloads += 1
                            else:
                                failed_downloads += 1
                                
                        except Exception as e:
                            st.error(f"Failed to download {url}: {e}")
                            failed_downloads += 1
                        
                        overall_progress.progress((i + 1) / len(urls))
                    
                    status_text.text(f"Batch download completed!")
                    st.success(f"✅ Successfully downloaded: {successful_downloads}")
                    if failed_downloads > 0:
                        st.warning(f"⚠️ Failed downloads: {failed_downloads}")
    
    elif batch_option == "YouTube Playlist":
        playlist_url = st.text_input("Enter YouTube Playlist URL:", key="playlist_url")
        playlist_format = st.selectbox("Download as:", ["Video", "Audio Only"], key="playlist_format")
        
        if playlist_url and st.button("📋 Load Playlist Info", key="playlist_info_btn"):
            try:
                with st.spinner("Loading playlist information..."):
                    playlist = Playlist(playlist_url)
                    st.success(f"Playlist: {playlist.title}")
                    st.info(f"Total videos: {len(playlist.video_urls)}")
                    
                    # Show first few video titles
                    st.subheader("Preview (first 5 videos):")
                    for i, video_url in enumerate(playlist.video_urls[:5]):
                        try:
                            yt = YouTube(video_url)
                            st.write(f"{i+1}. {yt.title}")
                        except:
                            st.write(f"{i+1}. [Unable to load title]")
                    
                    if len(playlist.video_urls) > 5:
                        st.write(f"... and {len(playlist.video_urls) - 5} more videos")
                        
            except Exception as e:
                st.error(f"Error loading playlist: {e}")
        
        if playlist_url and st.button("📚 Download Playlist", key="playlist_download_btn"):
            try:
                with st.spinner("Processing playlist..."):
                    playlist = Playlist(playlist_url)
                    urls = list(playlist.video_urls)
                
                progress_container = st.container()
                with progress_container:
                    overall_progress = st.progress(0)
                    status_text = st.empty()
                    
                    successful_downloads = 0
                    failed_downloads = 0
                    
                    for i, url in enumerate(urls):
                        try:
                            status_text.text(f"Downloading {i+1}/{len(urls)}")
                            yt = YouTube(url)
                            
                            if playlist_format == "Video":
                                stream = yt.streams.get_highest_resolution()
                            else:
                                stream = yt.streams.filter(only_audio=True).first()
                            
                            if stream:
                                os.makedirs(download_path, exist_ok=True)
                                file_path = stream.download(output_path=download_path)
                                file_name = os.path.basename(file_path)
                                add_to_history(playlist_format, yt.title, file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                successful_downloads += 1
                            else:
                                failed_downloads += 1
                                
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
        image_link = st.text_input("Enter Image URL:", key="image_url")
        
        # Image format and resize options
        col_format, col_resize = st.columns(2)
        with col_format:
            image_format = st.selectbox("Save as:", ["Original", "JPEG", "PNG", "WebP"], key="img_format")
        with col_resize:
            resize_option = st.selectbox("Resize:", ["Original Size", "1920x1080", "1280x720", "800x600", "Custom"], key="img_resize")
        
        if resize_option == "Custom":
            col_w, col_h = st.columns(2)
            with col_w:
                custom_width = st.number_input("Width:", min_value=1, value=800, key="custom_w")
            with col_h:
                custom_height = st.number_input("Height:", min_value=1, value=600, key="custom_h")
        
        download_image_btn = st.button("🖼️ Download Image", key="image_btn")

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
        youtube_link = st.text_input("Enter YouTube Video URL:", key="yt_thumb_url")
        thumb_quality = st.selectbox("Thumbnail Quality:", ["maxresdefault", "hqdefault", "mqdefault", "sddefault"], key="thumb_quality")
        
        if youtube_link and st.button("🖼️ Download Thumbnail", key="yt_thumb_btn"):
            try:
                with st.spinner("Fetching thumbnail..."):
                    yt = YouTube(youtube_link)
                    
                    # Try different thumbnail qualities
                    video_id = yt.video_id
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/{thumb_quality}.jpg"
                    
                    response = requests.get(thumbnail_url)
                    if response.status_code == 200:
                        image_data = response.content
                        img = Image.open(io.BytesIO(image_data))
                        
                        st.image(img, caption=f"Thumbnail: {yt.title}", use_column_width=True)
                        
                        file_name = f"{yt.title}_{thumb_quality}.jpg"
                        # Clean filename
                        file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
                        
                        add_to_history("Thumbnail", yt.title, file_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        
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
        batch_image_urls = st.text_area("Enter Image URLs (one per line):", key="batch_image_urls", height=150)
        batch_img_format = st.selectbox("Convert all to:", ["Keep Original", "JPEG", "PNG", "WebP"], key="batch_img_format")
        
        if st.button("🖼️ Download All Images", key="batch_img_btn"):
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
if st.sidebar.button("📜 View Download History"):
    st.header("📜 Download History")
    
    if st.session_state.download_history:
        for i, item in enumerate(st.session_state.download_history):
            with st.expander(f"{item['type']} - {item['title'][:50]}{'...' if len(item['title']) > 50 else ''}"):
                st.write(f"**Type:** {item['type']}")
                st.write(f"**Title:** {item['title']}")
                st.write(f"**File:** {item['file_name']}")
                st.write(f"**Downloaded:** {item['download_time']}")
        
        if st.button("🗑️ Clear History"):
            st.session_state.download_history = []
            st.success("History cleared!")
            st.rerun()
    else:
        st.info("No downloads yet!")

# --- FILE MANAGER ---
if st.sidebar.button("📁 View Downloaded Files"):
    st.header("📁 Downloaded Files")
    
    if os.path.exists(download_path):
        files = os.listdir(download_path)
        if files:
            for file in files:
                file_path = os.path.join(download_path, file)
                file_size = os.path.getsize(file_path)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"📄 {file}")
                with col2:
                    st.write(f"{format_file_size(file_size)}")
                with col3:
                    st.write(f"{file_modified.strftime('%m/%d %H:%M')}")
        else:
            st.info("No files in download folder yet!")
    else:
        st.info("Download folder doesn't exist yet!")

# --- STATISTICS ---
if st.sidebar.button("📊 Statistics"):
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

# --- Footer ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; padding: 20px;'>"
    "<h5>🎬 Advanced Downloader</h5>"
    "<p>Made with ❤️ by <span style='color: #0320fc;'>Mohit Kumar A</span> for <span style='color: #0320fc;'>Chethana</span></p>"
    "</div>",
    unsafe_allow_html=True
)

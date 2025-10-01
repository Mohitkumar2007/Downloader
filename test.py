import streamlit as st
import yt_dlp
import requests
from PIL import Image
import io
import os
import re

st.set_page_config(page_title="🎬 Advanced Downloader", layout="wide")
st.title("🎬 Advanced Downloader (Cloud Edition)")

st.info("Note: Files downloaded here are temporary. Use the download button to save them locally. On cloud, files are deleted when the app restarts.")

# Tabs for Download Types
tab1, tab2, tab3 = st.tabs(["YouTube Video/Audio", "Image Downloader", "Batch Download"])

# --- YouTube Video/Audio Tab ---
with tab1:
    st.header("YouTube Download")
    url = st.text_input("Enter YouTube URL")
    download_type = st.selectbox("Download Type", ["Video (mp4/webm)", "Audio (m4a/webm/mp3)"])
    video_quality = st.selectbox("Video Quality", ["best", "720p", "480p", "360p"])
    audio_format = st.selectbox("Audio Format", ["m4a", "webm", "mp3"])

    if st.button("Download", key="yt_download"):
        if url:
            try:
                # Set format string for yt-dlp
                if "Video" in download_type:
                    fmt_str = "bestvideo+bestaudio/best"
                    if video_quality != "best":
                        fmt_str = f"bestvideo[height<={video_quality.replace('p','')}]+bestaudio/best[height<={video_quality.replace('p','')}]"
                    ext = "mp4"
                else:
                    fmt_str = "bestaudio/best"
                    ext = audio_format

                fname = "downloaded." + ext

                ydl_opts = {
                    "format": fmt_str,
                    "outtmpl": fname,
                    "noplaylist": True,
                    "quiet": True,
                }
                # If mp3, set postprocessing
                if download_type == "Audio (m4a/webm/mp3)" and audio_format == "mp3":
                    ydl_opts["postprocessors"] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                elif download_type == "Audio (m4a/webm/mp3)" and audio_format == "m4a":
                    ydl_opts["postprocessors"] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'm4a',
                        'preferredquality': '192',
                    }]
                # Download
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', 'video')
                    # Try to find actual filename
                    files = [f for f in os.listdir('.') if f.startswith('downloaded') and not f.endswith('.py')]
                    if files:
                        fname = files[-1]
                    # Serve download
                    with open(fname, "rb") as f:
                        st.download_button(
                            f"Download {title}.{ext}",
                            f,
                            file_name=f"{re.sub(r'[<>:\"/\\\\|?*]', '_', title)}.{ext}",
                        )
                    os.remove(fname)
            except Exception as e:
                st.error(str(e))

# --- Image Downloader Tab ---
with tab2:
    st.header("Image Downloader")
    img_url = st.text_input("Enter Image URL")
    img_format = st.selectbox("Save as", ["Original", "JPEG", "PNG", "WebP"])
    if st.button("Download Image", key="img_download"):
        try:
            resp = requests.get(img_url)
            img = Image.open(io.BytesIO(resp.content))
            buf = io.BytesIO()
            file_name = "image.jpg"
            mime_type = "image/jpeg"
            if img_format == "Original":
                img.save(buf, format=img.format)
                file_name = os.path.basename(img_url) or "image.jpg"
                mime_type = "image/jpeg"
            else:
                fmt = img_format
                if fmt == "JPEG" and img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(buf, format=fmt)
                file_name = f"image.{fmt.lower()}"
                mime_type = f"image/{fmt.lower()}"
            st.image(img)
            st.download_button("Download Image", buf.getvalue(), file_name, mime=mime_type)
        except Exception as e:
            st.error(str(e))

# --- Batch Download Tab ---
with tab3:
    st.header("Batch YouTube Download")
    batch_type = st.radio("Batch Type", ["Multiple URLs", "YouTube Playlist"])
    if batch_type == "Multiple URLs":
        urls_text = st.text_area("Enter YouTube URLs (one per line)")
        batch_format = st.selectbox("Download as", ["Video", "Audio"])
        if st.button("Download All", key="batch_download"):
            urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
            st.info(f"Downloading {len(urls)} items. Please wait.")
            for i, url in enumerate(urls):
                try:
                    ext = "mp4" if batch_format == "Video" else "m4a"
                    fname = f"batch_{i+1}.{ext}"
                    ydl_opts = {
                        "format": "best" if batch_format == "Video" else "bestaudio/best",
                        "outtmpl": fname,
                        "noplaylist": True,
                        "quiet": True,
                    }
                    if batch_format == "Audio":
                        ydl_opts["postprocessors"] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'm4a',
                            'preferredquality': '192',
                        }]
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        title = info.get('title', f"batch_{i+1}")
                        with open(fname, "rb") as f:
                            st.download_button(
                                f"Download {title}.{ext}",
                                f,
                                file_name=f"{re.sub(r'[<>:\"/\\\\|?*]', '_', title)}.{ext}",
                            )
                        os.remove(fname)
                except Exception as e:
                    st.error(f"Failed: {url}\n{e}")
    else:
        playlist_url = st.text_input("Enter YouTube Playlist URL")
        batch_format = st.selectbox("Download as", ["Video", "Audio"])
        if st.button("Download Playlist", key="playlist_download"):
            try:
                ydl_opts = {
                    "quiet": True,
                    "extract_flat": True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    playlist_info = ydl.extract_info(playlist_url, download=False)
                entries = playlist_info.get('entries', [])
                urls = [f"https://www.youtube.com/watch?v={entry['id']}" for entry in entries if entry.get('id')]
                st.info(f"Playlist: {playlist_info.get('title','Unknown')}\nVideos: {len(urls)}")
                for i, url in enumerate(urls):
                    try:
                        ext = "mp4" if batch_format == "Video" else "m4a"
                        fname = f"playlist_{i+1}.{ext}"
                        ydl_opts = {
                            "format": "best" if batch_format == "Video" else "bestaudio/best",
                            "outtmpl": fname,
                            "noplaylist": True,
                            "quiet": True,
                        }
                        if batch_format == "Audio":
                            ydl_opts["postprocessors"] = [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'm4a',
                                'preferredquality': '192',
                            }]
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            title = info.get('title', f"playlist_{i+1}")
                            with open(fname, "rb") as f:
                                st.download_button(
                                    f"Download {title}.{ext}",
                                    f,
                                    file_name=f"{re.sub(r'[<>:\"/\\\\|?*]', '_', title)}.{ext}",
                                )
                            os.remove(fname)
                    except Exception as e:
                        st.error(f"Failed: {url}\n{e}")
            except Exception as e:
                st.error(str(e))

# --- Footer ---
st.markdown("""
<hr>
<div style='text-align: center; color: #888;'>
    <p>Made with ❤️ by <a href="https://github.com/Mohitkumar2007" target="_blank" style="color:#FF4B4B;">Mohit Kumar A</a></p>
    <small>Cloud Edition • Audio/Video/Image Download • Streamlit</small>
</div>
""", unsafe_allow_html=True)
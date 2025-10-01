# 🎬 Advanced YouTube Video Downloader

A powerful, feature-rich YouTube video and audio downloader built with Streamlit and Python.

## ✨ Features

### 🎥 Video Downloader
- **Quality Selection**: Choose from Highest, 1080p, 720p, 480p, 360p
- **Format Options**: MP4 or WebM support
- **Detailed Video Info**: Views, duration, upload date, channel, rating
- **File Size Display**: Shows download size before downloading
- **Progress Indicators**: Visual progress bars during downloads

### 🎵 Audio Downloader
- **Extract Audio**: Download just the audio from YouTube videos
- **Format Selection**: MP4 or WebM audio formats
- **Audio Quality Info**: Shows bitrate and file size

### 📚 Batch Download
- **Multiple URLs**: Download multiple YouTube videos at once
- **Playlist Support**: Download entire YouTube playlists
- **Batch Progress**: Track progress for multiple downloads

### 🖼️ Advanced Image Downloader
- **Multiple Sources**: Direct URLs, YouTube thumbnails, batch URLs
- **Format Conversion**: Convert to JPEG, PNG, or WebP
- **Image Resizing**: Preset sizes or custom dimensions
- **Thumbnail Quality**: Choose thumbnail resolution

### ⚙️ Management Features
- **Custom Download Path**: Choose where files are saved
- **Download History**: Track all downloads with timestamps
- **File Manager**: View downloaded files with sizes and dates
- **Statistics**: Download analytics and usage patterns
- **Theme Toggle**: Light/Dark theme support

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Mohitkumar2007/Downloader.git
   cd Downloader
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

1. **Run the application:**
   ```bash
   streamlit run main.py
   ```

2. **Open your browser** and navigate to `http://localhost:8501`

3. **Choose your download type:**
   - 🎥 Video Download
   - 🎵 Audio Only
   - 🖼️ Image Download
   - 📚 Batch Download

4. **Enter URLs** and customize your download settings

5. **Download** and enjoy your content!

## 📋 Requirements

- Python 3.8+
- Streamlit 1.50.0
- yt-dlp 2024.12.13
- Pillow 10.4.0
- requests 2.32.3
- urllib3 2.2.3
- Additional dependencies (see requirements.txt)

## 📁 Project Structure

```
Downloader/
├── main.py              # Main Streamlit application
├── test_ytdlp.py       # Test file for yt-dlp functionality
├── requirements.txt     # Python dependencies
├── README.md           # Project documentation
├── LICENSE             # MIT License
├── pyvenv.cfg          # Virtual environment configuration
├── downloads/          # Downloaded files directory
├── Scripts/            # Virtual environment scripts
├── Lib/               # Virtual environment libraries
└── Include/           # Virtual environment headers
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Mohit Kumar A**
- Created with ❤️ for Chethana

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for powerful YouTube downloading capabilities
- [Streamlit](https://streamlit.io/) for the amazing web framework
- [Pillow](https://pillow.readthedocs.io/) for image processing
- [PyArrow](https://arrow.apache.org/docs/python/) for efficient data processing

## ⚠️ Disclaimer

This tool is for educational and personal use only. Please respect YouTube's Terms of Service and copyright laws. Always ensure you have permission to download content.

---

**⭐ If you find this project useful, please give it a star!**
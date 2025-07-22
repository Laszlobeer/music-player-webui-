# 🎧 NEO AUDIO - Modern Web-Based Audio Player

## 🌟 Overview
NEO AUDIO is a sleek, modern web-based audio player that allows you to:
- Scan and play your local music collection
- Create and manage playlists
- Access your music library from any device on your local network
- Enjoy a Spotify-like experience with album art and metadata



## 🛠 Installation

### Prerequisites
- Python 3.6+
- Pip package manager

### Step-by-Step Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/neo-audio-player.git
   cd neo-audio-player
   ```

2. **Install required packages:**
   ```bash
   pip install flask mutagen pillow
   ```

3. **Create the required directories:**
   ```bash
   mkdir audio_files playlist_images templates
   ```

4. **Place the HTML file:**
   - Move `player.html` to the `templates` directory

5. **Add your music files:**
   - Place your audio files (MP3, WAV, FLAC) in the `audio_files` directory

## 🚀 Running the Player
```bash
python deepseek_python_20250722_e2b37f.py
```

After starting the server, you'll see a message like:
```
Access player at: http://192.168.1.5:5000
```

Open this URL in any web browser on your local network to access the player!

## 🌐 Network Access
All devices on your local network can access the player using your computer's IP address:
- Windows: `ipconfig` (look for IPv4 Address)
- Mac/Linux: `ifconfig` (look for inet address)
- Access URL: `http://<your-ip>:5000`

## 🎶 Features
- 🎵 **Audio Library Scanning**: Automatically scans your audio files and extracts metadata
- 📁 **Playlist Management**: Create, edit, and delete playlists
- ⏯ **Playback Controls**: Play, pause, skip, shuffle, repeat modes
- 🔊 **Volume Control**: Adjust volume with a slider
- ⏱ **Progress Tracking**: See current time and duration
- 🖼 **Album Art Display**: Visual representation of currently playing track
- 🔄 **Drag & Drop**: Reorder tracks in playlists
- 🌈 **Modern UI**: Dark theme with accent colors

## 🧩 Technical Details
- **Backend**: Python Flask
- **Metadata Handling**: Mutagen library
- **Image Processing**: Pillow (PIL)
- **Frontend**: HTML5, CSS3, JavaScript

## 🤝 Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## 📜 License
This project is licensed under the MIT License.

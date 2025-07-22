import os
import sys
import mimetypes
import logging
import random
from flask import Flask, render_template, send_file, jsonify, request, Response
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configuration
MUSIC_FOLDER = Path('music')  # Default music folder
if not MUSIC_FOLDER.exists():
    MUSIC_FOLDER.mkdir()
    logging.info(f"Created music folder at {MUSIC_FOLDER.absolute()}")

# Supported audio formats
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac', '.m4a'}

def scan_music_folder(folder_path):
    """Scan the music folder and return a list of music files with metadata"""
    music_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in AUDIO_EXTENSIONS:
                try:
                    # Get file stats for metadata
                    stat = file_path.stat()
                    music_files.append({
                        'path': str(file_path),
                        'name': file_path.stem,
                        'file_name': file,
                        'size': stat.st_size,
                        'modified': stat.st_mtime
                    })
                except Exception as e:
                    logging.error(f"Error processing {file_path}: {e}")
    return music_files

@app.route('/')
def index():
    """Render the main player interface"""
    return render_template('index.html')

@app.route('/music')
def list_music():
    """Return a JSON list of music files"""
    try:
        music_files = scan_music_folder(MUSIC_FOLDER)
        return jsonify({'songs': music_files})
    except Exception as e:
        logging.error(f"Error scanning music folder: {e}")
        return jsonify({'error': 'Could not scan music folder'}), 500

@app.route('/play/<path:filename>')
def play_music(filename):
    """Serve a music file for playback"""
    # Security: Ensure the requested file is within the music folder
    file_path = MUSIC_FOLDER / filename
    if not file_path.exists() or MUSIC_FOLDER not in file_path.parents:
        return "File not found", 404
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = 'audio/mpeg'  # Default to MP3 if unknown
    
    # Use send_file for efficient file serving
    return send_file(
        file_path,
        mimetype=mime_type,
        as_attachment=False
    )

@app.route('/cover/<path:filename>')
def get_cover(filename):
    """Placeholder for album cover images"""
    # In a real app, you would extract album art from music files
    # For this demo, we'll return a placeholder image
    
    # Generate a unique color based on filename for placeholder
    color_hash = hash(filename) % 0xFFFFFF
    color = f"#{color_hash:06x}"
    
    # Create a simple SVG placeholder
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
        <rect width="200" height="200" fill="{color}"/>
        <text x="100" y="100" font-family="Arial" font-size="20" fill="white" text-anchor="middle" dominant-baseline="middle">Album Art</text>
    </svg>'''
    
    return Response(svg, mimetype='image/svg+xml')

@app.route('/shuffle')
def shuffle_playlist():
    """Return a shuffled list of music files"""
    try:
        music_files = scan_music_folder(MUSIC_FOLDER)
        random.shuffle(music_files)
        return jsonify({'songs': music_files})
    except Exception as e:
        logging.error(f"Error shuffling music: {e}")
        return jsonify({'error': 'Could not shuffle music'}), 500

if __name__ == '__main__':
    # Allow specifying a custom music folder via command line
    if len(sys.argv) > 1:
        custom_folder = Path(sys.argv[1])
        if custom_folder.exists() and custom_folder.is_dir():
            MUSIC_FOLDER = custom_folder
            logging.info(f"Using custom music folder: {MUSIC_FOLDER}")
        else:
            logging.warning(f"Invalid music folder: {custom_folder}. Using default.")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)

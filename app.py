import os
import random
from flask import Flask, render_template, send_from_directory, request, jsonify, session, send_file
from mutagen import File
import socket
import json
import uuid
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
app.config['AUDIO_FOLDER'] = 'audio_files'
app.config['PLAYLIST_IMAGE_FOLDER'] = 'playlist_images'
app.secret_key = 'your_secret_key_here'  # Needed for session management

# Create folders if not exists
os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)
os.makedirs(app.config['PLAYLIST_IMAGE_FOLDER'], exist_ok=True)

def get_local_ip():
    """Get the local IP address for network access"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def scan_audio_files():
    """Scan for audio files and extract metadata"""
    audio_files = []
    supported_formats = ('.mp3', '.wav', '.ogg', '.flac', '.m4a')
    
    for root, _, files in os.walk(app.config['AUDIO_FOLDER']):
        for file in files:
            if file.lower().endswith(supported_formats):
                file_path = os.path.join(root, file)
                try:
                    audio = File(file_path)
                    duration = audio.info.length if audio else 0
                    
                    # Get metadata
                    title = file
                    artist = "Unknown Artist"
                    album = "Unknown Album"
                    
                    if audio:
                        if 'title' in audio:
                            title = audio['title'][0]
                        elif 'TIT2' in audio:
                            title = audio['TIT2'].text[0]
                            
                        if 'artist' in audio:
                            artist = audio['artist'][0]
                        elif 'TPE1' in audio:
                            artist = audio['TPE1'].text[0]
                            
                        if 'album' in audio:
                            album = audio['album'][0]
                        elif 'TALB' in audio:
                            album = audio['TALB'].text[0]
                    
                    audio_files.append({
                        'path': file_path.replace('\\', '/'),
                        'title': title,
                        'artist': artist,
                        'album': album,
                        'filename': file,
                        'duration': format_time(duration),
                        'size': os.path.getsize(file_path)
                    })
                except Exception as e:
                    print(f"Error processing {file}: {str(e)}")
                    audio_files.append({
                        'path': file_path.replace('\\', '/'),
                        'title': file,
                        'artist': "Unknown Artist",
                        'album': "Unknown Album",
                        'filename': file,
                        'duration': '0:00',
                        'size': os.path.getsize(file_path)
                    })
    
    return audio_files

def format_time(seconds):
    """Convert seconds to MM:SS format"""
    if seconds is None:
        return "0:00"
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def format_file_size(size):
    """Convert file size to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"

def generate_thumbnail(image_path, size=(200, 200)):
    """Generate thumbnail for playlist image"""
    try:
        img = Image.open(image_path)
        img.thumbnail(size)
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return None

@app.route('/')
def index():
    # Initialize player state if not exists
    if 'playlists' not in session:
        session['playlists'] = {}
        session['current_playlist_id'] = None
        session['current_track'] = None
        session['current_time'] = 0
        session['volume'] = 0.7
        session['shuffle'] = False
        session['repeat'] = 'none'  # none, one, all
        session['playback_state'] = 'paused'
    
    files = scan_audio_files()
    
    # Create a default playlist if none exists
    if not session['playlists']:
        playlist_id = str(uuid.uuid4())
        session['playlists'][playlist_id] = {
            'id': playlist_id,
            'name': 'My Playlist',
            'image': None,
            'tracks': [file['path'] for file in files]
        }
        session['current_playlist_id'] = playlist_id
    
    return render_template('player.html')

@app.route('/api/network-address')
def network_address():
    return jsonify({"address": get_local_ip()})

@app.route('/api/audio-files')
def get_audio_files():
    return jsonify(scan_audio_files())

@app.route('/api/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(app.config['AUDIO_FOLDER'], filename)

@app.route('/api/player-state', methods=['GET', 'POST'])
def player_state():
    if request.method == 'POST':
        data = request.json
        
        # Update session with new state
        if 'current_track' in data:
            session['current_track'] = data['current_track']
        if 'current_time' in data:
            session['current_time'] = data['current_time']
        if 'volume' in data:
            session['volume'] = data['volume']
        if 'shuffle' in data:
            session['shuffle'] = data['shuffle']
        if 'repeat' in data:
            session['repeat'] = data['repeat']
        if 'playback_state' in data:
            session['playback_state'] = data['playback_state']
        if 'current_playlist_id' in data:
            session['current_playlist_id'] = data['current_playlist_id']
        
        session.modified = True
        return jsonify({"status": "success"})
    
    # GET request - return current state
    return jsonify({
        "current_track": session.get('current_track'),
        "current_time": session.get('current_time', 0),
        "volume": session.get('volume', 0.7),
        "shuffle": session.get('shuffle', False),
        "repeat": session.get('repeat', 'none'),
        "playback_state": session.get('playback_state', 'paused'),
        "current_playlist_id": session.get('current_playlist_id')
    })

@app.route('/api/playlists', methods=['GET'])
def get_playlists():
    return jsonify(list(session.get('playlists', {}).values()))

@app.route('/api/playlists', methods=['POST'])
def create_playlist():
    data = request.json
    name = data.get('name', 'New Playlist')
    
    playlist_id = str(uuid.uuid4())
    session['playlists'][playlist_id] = {
        'id': playlist_id,
        'name': name,
        'image': None,
        'tracks': []
    }
    
    session.modified = True
    return jsonify(session['playlists'][playlist_id]), 201

@app.route('/api/playlists/<playlist_id>', methods=['PUT'])
def update_playlist(playlist_id):
    data = request.json
    name = data.get('name')
    
    if playlist_id in session['playlists']:
        if name:
            session['playlists'][playlist_id]['name'] = name
        session.modified = True
        return jsonify(session['playlists'][playlist_id])
    
    return jsonify({"error": "Playlist not found"}), 404

@app.route('/api/playlists/<playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    if playlist_id in session['playlists']:
        # If deleting the current playlist, reset current playlist
        if session.get('current_playlist_id') == playlist_id:
            other_playlists = [id for id in session['playlists'].keys() if id != playlist_id]
            session['current_playlist_id'] = other_playlists[0] if other_playlists else None
        
        del session['playlists'][playlist_id]
        session.modified = True
        return jsonify({"status": "success"})
    
    return jsonify({"error": "Playlist not found"}), 404

@app.route('/api/playlists/<playlist_id>/image', methods=['POST'])
def upload_playlist_image(playlist_id):
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if playlist_id in session['playlists']:
        filename = secure_filename(f"{playlist_id}.jpg")
        file_path = os.path.join(app.config['PLAYLIST_IMAGE_FOLDER'], filename)
        file.save(file_path)
        
        # Generate thumbnail
        thumbnail = generate_thumbnail(file_path)
        
        session['playlists'][playlist_id]['image'] = thumbnail
        session.modified = True
        
        return jsonify({"status": "success", "thumbnail": thumbnail})
    
    return jsonify({"error": "Playlist not found"}), 404

@app.route('/api/playlists/<playlist_id>/tracks', methods=['POST'])
def add_track_to_playlist(playlist_id):
    data = request.json
    track_path = data.get('track_path')
    
    if not track_path:
        return jsonify({"error": "Missing track_path"}), 400
    
    if playlist_id in session['playlists']:
        if track_path not in session['playlists'][playlist_id]['tracks']:
            session['playlists'][playlist_id]['tracks'].append(track_path)
            session.modified = True
        return jsonify(session['playlists'][playlist_id])
    
    return jsonify({"error": "Playlist not found"}), 404

@app.route('/api/playlists/<playlist_id>/tracks/<int:track_index>', methods=['DELETE'])
def remove_track_from_playlist(playlist_id, track_index):
    if playlist_id in session['playlists']:
        playlist = session['playlists'][playlist_id]
        if track_index < 0 or track_index >= len(playlist['tracks']):
            return jsonify({"error": "Invalid track index"}), 400
        
        # If the track being removed is the current track and it's playing, stop it
        removed_track = playlist['tracks'][track_index]
        if session.get('current_track') == removed_track:
            session['current_track'] = None
            session['playback_state'] = 'paused'
        
        del playlist['tracks'][track_index]
        session.modified = True
        return jsonify(playlist)
    
    return jsonify({"error": "Playlist not found"}), 404

@app.route('/api/next-track', methods=['GET'])
def next_track():
    current_playlist_id = session.get('current_playlist_id')
    if not current_playlist_id or current_playlist_id not in session['playlists']:
        return jsonify({"error": "No playlist selected"}), 400
    
    playlist = session['playlists'][current_playlist_id]
    playlist_tracks = playlist['tracks']
    current_track = session.get('current_track')
    current_index = playlist_tracks.index(current_track) if current_track in playlist_tracks else -1
    
    if not playlist_tracks:
        return jsonify({"error": "Playlist is empty"}), 400
    
    # Handle repeat one mode
    if session.get('repeat') == 'one' and current_track:
        return jsonify({
            "next_track": current_track,
            "current_index": current_index
        })
    
    # Handle shuffle
    if session.get('shuffle'):
        # Create a shuffled list without the current track
        available_tracks = [t for t in playlist_tracks if t != current_track]
        if available_tracks:
            next_track = random.choice(available_tracks)
            current_index = playlist_tracks.index(next_track)
            return jsonify({
                "next_track": next_track,
                "current_index": current_index
            })
    
    # Normal next track
    if current_index == -1:
        next_index = 0
    else:
        next_index = current_index + 1
        if next_index >= len(playlist_tracks):
            if session.get('repeat') == 'all':
                next_index = 0
            else:
                return jsonify({"next_track": None, "end_of_playlist": True})
    
    return jsonify({
        "next_track": playlist_tracks[next_index],
        "current_index": next_index
    })

@app.route('/api/previous-track', methods=['GET'])
def previous_track():
    current_playlist_id = session.get('current_playlist_id')
    if not current_playlist_id or current_playlist_id not in session['playlists']:
        return jsonify({"error": "No playlist selected"}), 400
    
    playlist = session['playlists'][current_playlist_id]
    playlist_tracks = playlist['tracks']
    current_track = session.get('current_track')
    current_index = playlist_tracks.index(current_track) if current_track in playlist_tracks else -1
    
    if not playlist_tracks:
        return jsonify({"error": "Playlist is empty"}), 400
    
    # Handle repeat one mode
    if session.get('repeat') == 'one' and current_track:
        return jsonify({
            "prev_track": current_track,
            "current_index": current_index
        })
    
    # Handle shuffle - in shuffle mode, previous goes to beginning of track
    if session.get('shuffle'):
        return jsonify({
            "prev_track": current_track,
            "current_index": current_index,
            "restart": True
        })
    
    # Normal previous track
    if current_index == -1:
        prev_index = len(playlist_tracks) - 1
    else:
        prev_index = current_index - 1
        if prev_index < 0:
            if session.get('repeat') == 'all':
                prev_index = len(playlist_tracks) - 1
            else:
                return jsonify({"prev_track": None, "start_of_playlist": True})
    
    return jsonify({
        "prev_track": playlist_tracks[prev_index],
        "current_index": prev_index
    })

if __name__ == '__main__':
    local_ip = get_local_ip()
    print(f"Access player at: http://{local_ip}:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
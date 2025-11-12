import streamlit as st
import json
import secrets
import string
from pathlib import Path
from datetime import datetime, timedelta
import requests
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import PlainTextResponse
import uvicorn
import threading
import time
import socket

# Streamlit App
class StreamKeyManager:
    def __init__(self):
        self.data_file = Path("/app/data/streams.json")
        self.load_streams()
    
    def load_streams(self):
        """Load existing streams from JSON file"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {"streams": [], "active_streams": {}}
    
    def save_streams(self, data):
        """Save streams to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_stream_key(self, length=12):
        """Generate a secure random stream key"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def create_stream(self, name, description="", expires_hours=24):
        """Create a new stream with generated key"""
        data = self.load_streams()
        
        stream_key = self.generate_stream_key()
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        stream = {
            "id": len(data["streams"]) + 1,
            "name": name,
            "description": description,
            "stream_key": stream_key,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "is_active": False,
            "last_used": None
        }
        
        data["streams"].append(stream)
        self.save_streams(data)
        
        return stream
    
    def get_stream_info(self, stream_key):
        """Get stream information by key"""
        data = self.load_streams()
        for stream in data["streams"]:
            if stream["stream_key"] == stream_key:
                return stream
        return None
    
    def update_stream_status(self, stream_key, is_active):
        """Update stream active status"""
        data = self.load_streams()
        
        # Update in streams list
        for stream in data["streams"]:
            if stream["stream_key"] == stream_key:
                stream["is_active"] = is_active
                stream["last_used"] = datetime.now().isoformat() if is_active else stream["last_used"]
        
        # Update in active streams
        if is_active:
            data["active_streams"][stream_key] = datetime.now().isoformat()
        else:
            data["active_streams"].pop(stream_key, None)
        
        self.save_streams(data)
    
    def delete_stream(self, stream_id):
        """Delete a stream by ID"""
        data = self.load_streams()
        
        # Find and remove the stream
        stream_to_delete = None
        for i, stream in enumerate(data["streams"]):
            if stream["id"] == stream_id:
                stream_to_delete = stream
                # Remove from streams list
                data["streams"].pop(i)
                break
        
        if stream_to_delete:
            # Remove from active streams if it's active
            stream_key = stream_to_delete.get("stream_key")
            if stream_key and stream_key in data["active_streams"]:
                data["active_streams"].pop(stream_key, None)
            
            self.save_streams(data)
            return True
        
        return False

def main_streamlit_app():
    """Streamlit web interface"""
    # Initialize FastAPI server if needed (only once)
    start_fastapi_if_needed()
    
    st.set_page_config(
        page_title="Self-Hosted RTMP Stream Manager",
        page_icon="🎥",
        layout="wide"
    )
    
    st.title("🎥 Self-Hosted RTMP Stream Manager")
    st.write("Generate and manage stream keys for your VPS RTMP server")
    
    manager = StreamKeyManager()
    data = manager.load_streams()
    
    # Get your VPS IP (you might want to set this manually)
    vps_ip = st.text_input("Your VPS IP Address", placeholder="192.168.1.100 or your-domain.com")
    
    # Create new stream
    with st.form("create_stream"):
        st.subheader("Create New Stream Key")
        
        col1, col2 = st.columns(2)
        with col1:
            stream_name = st.text_input("Stream Name", placeholder="My TV Station")
            stream_desc = st.text_area("Description", placeholder="Live TV broadcast")
        with col2:
            expires = st.number_input("Expires after (hours)", min_value=1, max_value=720, value=24)
        
        submitted = st.form_submit_button("Generate Stream Key")
        
        if submitted and stream_name:
            new_stream = manager.create_stream(stream_name, stream_desc, expires)
            
            st.success("✅ Stream Key Generated!")
            
            # Display stream information
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Stream Details:**")
                st.write(f"Name: {new_stream['name']}")
                st.write(f"Stream Key: `{new_stream['stream_key']}`")
                st.write(f"Expires: {datetime.fromisoformat(new_stream['expires_at']).strftime('%Y-%m-%d %H:%M')}")
            
            with col2:
                if vps_ip:
                    rtmp_url = f"rtmp://{vps_ip}:1940/live/{new_stream['stream_key']}"
                    hls_url = f"http://{vps_ip}:8088/hls/{new_stream['stream_key']}.m3u8"
                    
                    st.write("**vMix Configuration:**")
                    st.code(f"URL: {rtmp_url}", language="bash")
                    st.write("**In vMix:** Settings → Streaming → Add Destination → Custom")
                    
                    st.write("**📺 Watch Stream:**")
                    st.code(f"HLS: {hls_url}", language="bash")
                    st.write("**Copy HLS URL to:** VLC Media Player → Media → Open Network Stream")
    
    # Show existing streams
    st.subheader("📊 Existing Streams")
    if data["streams"]:
        for stream in data["streams"]:
            with st.expander(f"🔴 {stream['name']} - {stream['stream_key']} {'(LIVE)' if stream['is_active'] else '(offline)'}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Description:** {stream['description']}")
                    st.write(f"**Created:** {datetime.fromisoformat(stream['created_at']).strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Expires:** {datetime.fromisoformat(stream['expires_at']).strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Status:** {'🟢 LIVE' if stream['is_active'] else '🔴 Offline'}")
                
                with col2:
                    if vps_ip:
                        rtmp_url = f"rtmp://{vps_ip}:1940/live/{stream['stream_key']}"
                        hls_url = f"http://{vps_ip}:8088/hls/{stream['stream_key']}.m3u8"
                        
                        st.write("**RTMP URL (for streaming):**")
                        st.code(f"{rtmp_url}", language="bash")
                        
                        if stream['is_active']:
                            st.write("**📺 Watch Stream (HLS):**")
                            st.code(f"{hls_url}", language="bash")
                            st.info("💡 Copy this URL to VLC: Media → Open Network Stream")
                        else:
                            st.write("**📺 Watch URL (when live):**")
                            st.code(f"HLS: {hls_url}", language="bash")
                    
                    # Delete button with confirmation
                    delete_key = f"delete_{stream['id']}"
                    if delete_key not in st.session_state:
                        st.session_state[delete_key] = False
                    
                    if st.session_state[delete_key]:
                        # Show confirmation
                        st.warning(f"⚠️ Are you sure you want to delete '{stream['name']}'?")
                        col_confirm1, col_confirm2 = st.columns(2)
                        with col_confirm1:
                            if st.button("✅ Confirm Delete", key=f"confirm_{stream['id']}"):
                                if manager.delete_stream(stream['id']):
                                    st.success(f"✅ Stream '{stream['name']}' deleted successfully!")
                                    st.session_state[delete_key] = False
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to delete stream")
                        with col_confirm2:
                            if st.button("❌ Cancel", key=f"cancel_{stream['id']}"):
                                st.session_state[delete_key] = False
                                st.rerun()
                    else:
                        if st.button(f"🗑️ Delete {stream['name']}", key=f"btn_{stream['id']}"):
                            st.session_state[delete_key] = True
                            st.rerun()
    
    # Active streams monitoring
    st.subheader("📈 Active Streams Monitor")
    if data["active_streams"]:
        for stream_key, start_time in data["active_streams"].items():
            stream_info = manager.get_stream_info(stream_key)
            if stream_info:
                st.success(f"🟢 {stream_info['name']} - Streaming since {datetime.fromisoformat(start_time).strftime('%H:%M:%S')}")
                if vps_ip:
                    hls_url = f"http://{vps_ip}:8088/hls/{stream_key}.m3u8"
                    st.code(f"Watch: {hls_url}", language="bash")
                    
                    # Embedded HLS player for browser playback
                    st.markdown("### 🎥 Watch in Browser")
                    player_html = f"""
                    <video id="video" width="100%" height="auto" controls autoplay>
                        <source src="{hls_url}" type="application/x-mpegURL">
                        Your browser does not support the video tag or HLS playback.
                    </video>
                    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
                    <script>
                        var video = document.getElementById('video');
                        var videoSrc = '{hls_url}';
                        if (Hls.isSupported()) {{
                            var hls = new Hls();
                            hls.loadSource(videoSrc);
                            hls.attachMedia(video);
                            hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                                video.play();
                            }});
                        }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                            video.src = videoSrc;
                            video.addEventListener('loadedmetadata', function() {{
                                video.play();
                            }});
                        }}
                    </script>
                    """
                    st.components.v1.html(player_html, height=500)
    else:
        st.info("No active streams")
    
    # RTMP Stats Link
    if vps_ip:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔍 Diagnostics")
        stats_url = f"http://{vps_ip}:8088/stat"
        player_url = f"http://{vps_ip}:8088/player.html"
        st.sidebar.write("**RTMP Stats:**")
        st.sidebar.markdown(f"[Open Stats Page]({stats_url})")
        st.sidebar.write("**🎥 Video Player:**")
        st.sidebar.markdown(f"[Open Player Page]({player_url})")
        st.sidebar.write("Use the player page to watch streams in your browser.")
    
    # Server statistics
    st.sidebar.title("Server Info")
    st.sidebar.write(f"**Total Streams:** {len(data['streams'])}")
    st.sidebar.write(f"**Active Streams:** {len(data['active_streams'])}")
    
    st.sidebar.title("Quick Guide")
    st.sidebar.write("""
    1. **Generate** a stream key
    2. **Use in vMix**: Settings → Streaming → Custom
    3. **URL**: rtmp://YOUR-VPS-IP/live/STREAM-KEY
    4. **Start streaming** from vMix
    """)

# FastAPI for RTMP callbacks
app = FastAPI()
manager = StreamKeyManager()

# Global flag to track if FastAPI server is running
_fastapi_running = False
_fastapi_lock = threading.Lock()

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except OSError:
            return True

@app.post("/api/stream/start")
async def stream_started(
    call: str = Form(None),
    addr: str = Form(None),
    clientid: str = Form(None),
    app: str = Form(None),
    flashVer: str = Form(None),
    swfUrl: str = Form(None),
    tcUrl: str = Form(None),
    pageUrl: str = Form(None),
    name: str = Form(None)  # This is the stream key from RTMP
):
    """Called when a stream starts publishing"""
    # Nginx RTMP sends the stream key as 'name' parameter
    stream_key = name
    if not stream_key:
        return PlainTextResponse("Invalid request: missing stream key", status_code=400)
    
    stream_info = manager.get_stream_info(stream_key)
    if stream_info:
        manager.update_stream_status(stream_key, True)
        return PlainTextResponse("OK", status_code=200)
    return PlainTextResponse("Invalid stream key", status_code=403)

@app.post("/api/stream/stop")
async def stream_stopped(
    call: str = Form(None),
    addr: str = Form(None),
    clientid: str = Form(None),
    app: str = Form(None),
    flashVer: str = Form(None),
    swfUrl: str = Form(None),
    tcUrl: str = Form(None),
    pageUrl: str = Form(None),
    name: str = Form(None)  # This is the stream key from RTMP
):
    """Called when a stream stops publishing"""
    # Nginx RTMP sends the stream key as 'name' parameter
    stream_key = name
    if not stream_key:
        return PlainTextResponse("Invalid request: missing stream key", status_code=400)
    
    stream_info = manager.get_stream_info(stream_key)
    if stream_info:
        manager.update_stream_status(stream_key, False)
        return PlainTextResponse("OK", status_code=200)
    return PlainTextResponse("Invalid stream key", status_code=403)

@app.get("/api/streams")
async def get_streams():
    """Get all streams"""
    return manager.load_streams()

def run_fastapi():
    """Run FastAPI server in background"""
    global _fastapi_running
    try:
        uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")
    except Exception as e:
        print(f"FastAPI server error: {e}")
    finally:
        _fastapi_running = False

def start_fastapi_if_needed():
    """Start FastAPI server only if not already running"""
    global _fastapi_running
    
    with _fastapi_lock:
        # Check if port is already in use (by our own server)
        if is_port_in_use(8004):
            # Port is in use, assume server is already running
            _fastapi_running = True
            return
        
        if _fastapi_running:
            return
        
        # Start the server
        _fastapi_running = True
        api_thread = threading.Thread(target=run_fastapi, daemon=True)
        api_thread.start()
        # Give it a moment to start
        time.sleep(0.5)

if __name__ == "__main__":
    # Start FastAPI in background thread (only if not already running)
    start_fastapi_if_needed()
    
    # Run Streamlit app
    main_streamlit_app()
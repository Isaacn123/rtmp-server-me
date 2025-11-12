import streamlit as st
import json
import secrets
import string
from pathlib import Path
from datetime import datetime, timedelta
import requests
from fastapi import FastAPI, HTTPException
import uvicorn
import threading
import time

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

def main_streamlit_app():
    """Streamlit web interface"""
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
                    rtmp_url = f"rtmp://{vps_ip}:1936/live/{new_stream['stream_key']}"
                    st.write("**vMix Configuration:**")
                    st.code(f"URL: {rtmp_url}", language="bash")
                    
                    st.write("**In vMix:** Settings → Streaming → Add Destination → Custom")
                    st.write(f"**URL:** `{rtmp_url}`")
    
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
                        rtmp_url = f"rtmp://{vps_ip}/live/{stream['stream_key']}"
                        st.code(f"URL: {rtmp_url}", language="bash")
                    
                    if st.button(f"Delete {stream['name']}", key=f"delete_{stream['id']}"):
                        # Remove stream logic would go here
                        st.warning("Delete functionality to be implemented")
    
    # Active streams monitoring
    st.subheader("📈 Active Streams Monitor")
    if data["active_streams"]:
        for stream_key, start_time in data["active_streams"].items():
            stream_info = manager.get_stream_info(stream_key)
            if stream_info:
                st.success(f"🟢 {stream_info['name']} - Streaming since {datetime.fromisoformat(start_time).strftime('%H:%M:%S')}")
    else:
        st.info("No active streams")
    
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

@app.post("/api/stream/start")
async def stream_started(stream_key: str):
    """Called when a stream starts publishing"""
    stream_info = manager.get_stream_info(stream_key)
    if stream_info:
        manager.update_stream_status(stream_key, True)
        return {"status": "ok", "message": f"Stream {stream_info['name']} started"}
    return {"status": "error", "message": "Invalid stream key"}

@app.post("/api/stream/stop")
async def stream_stopped(stream_key: str):
    """Called when a stream stops publishing"""
    stream_info = manager.get_stream_info(stream_key)
    if stream_info:
        manager.update_stream_status(stream_key, False)
        return {"status": "ok", "message": f"Stream {stream_info['name']} stopped"}
    return {"status": "error", "message": "Invalid stream key"}

@app.get("/api/streams")
async def get_streams():
    """Get all streams"""
    return manager.load_streams()

def run_fastapi():
    """Run FastAPI server in background"""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    # Start FastAPI in background thread
    api_thread = threading.Thread(target=run_fastapi, daemon=True)
    api_thread.start()
    
    # Run Streamlit app
    main_streamlit_app()
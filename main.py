import os
import json
import numpy as np
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydub import AudioSegment
import uuid

app = FastAPI(title="Sing To Me API")

# Mount the static directory to serve frontend and clips
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/songs", StaticFiles(directory="data/songs"), name="songs")

# Optional: Add HF_TOKEN to environment variables on Render to avoid rate limits
HF_TOKEN = os.environ.get("HF_TOKEN", "")
API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def load_all_embeddings():
    songs = []
    embed_dir = os.path.join("data", "embeddings")
    if not os.path.exists(embed_dir):
        return songs
        
    for filename in os.listdir(embed_dir):
        if filename.endswith(".json"):
            with open(os.path.join(embed_dir, filename), 'r', encoding='utf-8') as f:
                songs.append(json.load(f))
    return songs

@app.get("/api/search")
def search_lyrics(q: str):
    if not q:
        return {"results": []}
        
    # Generate embedding for the query using Hugging Face API (Lightweight for production)
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": [q]})
        response.raise_for_status()
        query_embedding = np.array(response.json()[0])
    except Exception as e:
        print(f"API Error: {e}")
        raise HTTPException(status_code=503, detail="AI Search API is currently unavailable or rate limited. Please try again or provide an HF_TOKEN.")
    
    songs = load_all_embeddings()
    matches = []
    
    for song in songs:
        for i, line in enumerate(song['lines']):
            line_embed = np.array(line['embedding'])
            score = cosine_similarity(query_embedding, line_embed)
            
            # Context (add prev and next lines to the text for better UX)
            text_context = line['text']
            # If score is high enough, we can consider merging adjacent lines later
            
            matches.append({
                "song_id": song["id"],
                "title": song["title"],
                "artist": song["artist"],
                "text": line["text"],
                "start": line["start"],
                "end": line["end"],
                "score": float(score)
            })
            
    # Sort by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)
    
    # Return top 10
    return {"results": matches[:10]}

@app.post("/api/clip")
def create_clip(song_id: str, start: int, end: int):
    audio_path = os.path.join("data", "songs", f"{song_id}.mp3")
    
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Song audio not found")
        
    # Make sure we don't end up with negative duration
    if end <= start:
        end = start + 5000
        
    # Load and slice the audio
    # pydub works in milliseconds
    print(f"Slicing {song_id}.mp3 from {start} to {end}")
    try:
        audio = AudioSegment.from_mp3(audio_path)
        
        # Add some padding to capture the full phrase nicely
        pad_start = max(0, start - 500)
        pad_end = min(len(audio), end + 500)
        
        clip = audio[pad_start:pad_end]
        
        # Generate unique filename
        clip_filename = f"clip_{song_id}_{start}_{uuid.uuid4().hex[:8]}.mp3"
        
        clips_dir = os.path.join("static", "clips")
        os.makedirs(clips_dir, exist_ok=True)
        
        clip_path = os.path.join(clips_dir, clip_filename)
        
        clip.export(clip_path, format="mp3")
        
        return {"url": f"/static/clips/{clip_filename}"}
    except Exception as e:
        print(f"Error creating clip: {e}")
        raise HTTPException(status_code=500, detail="Failed to create audio clip")

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")

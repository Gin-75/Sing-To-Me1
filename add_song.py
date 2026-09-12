import argparse
import json
import os
import re
import requests
import subprocess
from sentence_transformers import SentenceTransformer

# Initialize the embedding model
print("Loading AI embedding model (this might take a moment)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def search_lrclib(query):
    url = f"https://lrclib.net/api/search?q={requests.utils.quote(query)}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json()
        if results:
            for res in results:
                if res.get('syncedLyrics'):
                    return res
    return None

def parse_synced_lyrics(synced_lyrics):
    lines = []
    for line in synced_lyrics.split('\n'):
        match = re.match(r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)', line)
        if match:
            minutes, seconds, ms, text = match.groups()
            # ms could be 2 or 3 digits. if 2, it's centiseconds.
            if len(ms) == 2:
                ms = int(ms) * 10
            else:
                ms = int(ms)
            start_time_ms = int(minutes) * 60000 + int(seconds) * 1000 + ms
            text = text.strip()
            if text:
                lines.append({
                    "start": start_time_ms,
                    "text": text
                })
    
    # Calculate end times based on the start time of the next line
    for i in range(len(lines)):
        if i < len(lines) - 1:
            lines[i]['end'] = lines[i+1]['start']
        else:
            lines[i]['end'] = lines[i]['start'] + 5000 # Add 5 seconds for the last line
            
    return lines

def download_youtube_audio(query, output_path):
    # yt-dlp command to search and download best audio
    # Append 'official audio' for better quality and no MV intros
    search_query = f"{query} official audio"
    command = [
        "yt-dlp",
        f"ytsearch1:{search_query}",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", output_path
    ]
    print(f"Downloading audio for '{search_query}'...")
    subprocess.run(command, check=True)

def ingest_song(query):
    print(f"Searching lyrics for: {query}")
    track_info = search_lrclib(query)
    
    if not track_info:
        print("Could not find synchronized lyrics for this song on lrclib.net.")
        return

    song_id = str(track_info['id'])
    song_name = f"{track_info['artistName']} - {track_info['trackName']}"
    print(f"Found match: {song_name}")
    
    # Paths
    audio_path = os.path.join("data", "songs", f"{song_id}.mp3")
    embed_path = os.path.join("data", "embeddings", f"{song_id}.json")
    
    # 1. Download Audio
    if not os.path.exists(audio_path):
        download_youtube_audio(song_name + " audio", audio_path)
    else:
        print("Audio already exists, skipping download.")
        
    # 2. Parse Lyrics
    lines = parse_synced_lyrics(track_info['syncedLyrics'])
    if not lines:
        print("Failed to parse lyrics or empty lyrics.")
        return
        
    # 3. Generate Embeddings
    print("Generating AI embeddings for lyrics...")
    texts = [line['text'] for line in lines]
    embeddings = model.encode(texts).tolist()
    
    # Store everything together
    for i, line in enumerate(lines):
        line['embedding'] = embeddings[i]
        
    song_data = {
        "id": song_id,
        "title": track_info['trackName'],
        "artist": track_info['artistName'],
        "lines": lines
    }
    
    # 4. Save to JSON
    with open(embed_path, 'w', encoding='utf-8') as f:
        json.dump(song_data, f)
        
    print(f"Successfully ingested {song_name}!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest a song into Sing To Me")
    parser.add_argument("query", type=str, help="The song name and artist to search for")
    args = parser.parse_args()
    
    ingest_song(args.query)

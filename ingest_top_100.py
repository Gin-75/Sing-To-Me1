import subprocess
import time

songs = [
    "Adele - Rolling in the Deep", "Ed Sheeran - Shape of You", "The Weeknd - Blinding Lights",
    "Mark Ronson - Uptown Funk", "Billie Eilish - Bad Guy", "Drake - God's Plan",
    "Imagine Dragons - Believer", "Post Malone - Sunflower", "Dua Lipa - Levitating",
    "Luis Fonsi - Despacito", "Justin Bieber - Sorry", "Maroon 5 - Sugar",
    "Katy Perry - Roar", "OneRepublic - Counting Stars", "Taylor Swift - Blank Space",
    "Ed Sheeran - Perfect", "The Chainsmokers - Closer", "John Legend - All of Me",
    "Passenger - Let Her Go", "Avicii - Wake Me Up", "Adele - Someone Like You",
    "Pharrell Williams - Happy", "Sia - Chandelier", "Wiz Khalifa - See You Again",
    "Bruno Mars - Just The Way You Are", "Eminem - Love The Way You Lie", "Rihanna - Diamonds",
    "Coldplay - Yellow", "Oasis - Wonderwall", "Nirvana - Smells Like Teen Spirit",
    "Queen - Bohemian Rhapsody", "The Beatles - Hey Jude", "Michael Jackson - Billie Jean",
    "Whitney Houston - I Will Always Love You", "Journey - Don't Stop Believin'",
    "Eagles - Hotel California", "ABBA - Dancing Queen", "Madonna - Like a Prayer",
    "Prince - Purple Rain", "Bon Jovi - Livin' On A Prayer", "AC/DC - Back In Black",
    "Guns N' Roses - Sweet Child O' Mine", "U2 - With Or Without You", "The Police - Every Breath You Take",
    "TLC - Waterfalls", "Britney Spears - Toxic", "Backstreet Boys - I Want It That Way",
    "Spice Girls - Wannabe", "Eminem - Lose Yourself", "Beyonce - Crazy In Love",
    "Outkast - Hey Ya!", "The Killers - Mr. Brightside", "Kelly Clarkson - Since U Been Gone",
    "Linkin Park - In The End", "Evanescence - Bring Me To Life", "Red Hot Chili Peppers - Californication",
    "Coldplay - Viva La Vida", "Kings of Leon - Sex on Fire", "Adele - Set Fire To The Rain",
    "Gotye - Somebody That I Used To Know", "Carly Rae Jepsen - Call Me Maybe",
    "Hozier - Take Me To Church", "Shawn Mendes - Stitches", "Charlie Puth - Attention",
    "Ariana Grande - 7 rings", "Olivia Rodrigo - drivers license", "Harry Styles - As It Was",
    "Glass Animals - Heat Waves", "The Kid LAROI - STAY", "Lil Nas X - Old Town Road",
    "Lady Gaga - Bad Romance", "P!nk - Just Give Me A Reason", "Sam Smith - Stay With Me",
    "Lorde - Royals", "Miley Cyrus - Wrecking Ball", "Katy Perry - Firework",
    "Taylor Swift - Shake It Off", "Meghan Trainor - All About That Bass",
    "Justin Timberlake - Can't Stop The Feeling!", "Drake - One Dance", "The Weeknd - Starboy",
    "Camila Cabello - Havana", "Cardi B - I Like It", "Marshmello - Happier",
    "Post Malone - Circles", "Billie Eilish - everything i wanted", "Dua Lipa - Don't Start Now",
    "Doja Cat - Say So", "BTS - Dynamite", "The Weeknd - Save Your Tears",
    "Ed Sheeran - Bad Habits", "Olivia Rodrigo - good 4 u", "Elton John - Cold Heart",
    "Adele - Easy On Me", "Harry Styles - Watermelon Sugar", "Taylor Swift - Anti-Hero",
    "Miley Cyrus - Flowers", "SZA - Kill Bill", "Morgan Wallen - Last Night",
    "Luke Combs - Fast Car", "Doja Cat - Paint The Town Red"
]

print(f"Starting bulk ingestion of {len(songs)} songs...")

import sys

success = 0
failed = 0

for song in songs:
    print(f"\n[{success+failed+1}/{len(songs)}] Ingesting: {song}")
    try:
        # Run add_song.py for each song using the same Python executable (venv)
        result = subprocess.run([sys.executable, "add_song.py", song], capture_output=True, text=True, encoding="utf-8")
        if result.returncode == 0:
            print(f"Success: {song}")
            success += 1
        else:
            print(f"Failed: {song}")
            print(result.stdout)
            print(result.stderr)
            failed += 1
    except Exception as e:
        print(f"Error processing {song}: {e}")
        failed += 1
        
    # Small pause to be nice to APIs
    time.sleep(2)

print(f"\nBulk ingestion complete! Success: {success} | Failed: {failed}")

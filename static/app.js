document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const resultsContainer = document.getElementById('results-container');
    const loading = document.getElementById('loading');
    
    const modal = document.getElementById('clip-result-modal');
    const closeBtn = document.querySelector('.close-btn');
    const clipLyricText = document.getElementById('clip-lyric-text');
    const clipSongInfo = document.getElementById('clip-song-info');
    const clipAudio = document.getElementById('clip-audio');
    const downloadBtn = document.getElementById('download-btn');
    
    // Editor controls
    const fullSongAudio = document.getElementById('full-song-audio');
    const startTimeDisplay = document.getElementById('start-time-display');
    const endTimeDisplay = document.getElementById('end-time-display');
    const applyEditsBtn = document.getElementById('apply-edits-btn');
    const playPauseBtn = document.getElementById('play-pause-btn');
    const audioSlider = document.getElementById('audio-slider');
    const playhead = document.getElementById('playhead');
    const finalClipContainer = document.getElementById('final-clip-container');

    let currentClip = { songId: null, start: 0, end: 0 };
    let sliderCreated = false;

    const formatTime = (ms) => {
        if (ms < 0) ms = 0;
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    };

    const updatePlayhead = () => {
        if (!fullSongAudio.duration) return;
        const percent = (fullSongAudio.currentTime / fullSongAudio.duration) * 100;
        playhead.style.left = `${percent}%`;
    };

    fullSongAudio.addEventListener('timeupdate', () => {
        updatePlayhead();
        // Pause if we hit the end of the clip selection
        if (fullSongAudio.currentTime * 1000 >= currentClip.end && !fullSongAudio.paused) {
            fullSongAudio.pause();
        }
    });
    
    fullSongAudio.addEventListener('play', () => playPauseBtn.innerText = "⏸");
    fullSongAudio.addEventListener('pause', () => playPauseBtn.innerText = "▶");

    playPauseBtn.addEventListener('click', () => {
        if (fullSongAudio.paused) {
            // If playhead is outside bounds or at the end, reset to start
            const currentMs = fullSongAudio.currentTime * 1000;
            if (currentMs < currentClip.start || currentMs >= currentClip.end - 100) {
                fullSongAudio.currentTime = currentClip.start / 1000;
            }
            fullSongAudio.play();
        } else {
            fullSongAudio.pause();
        }
    });

    const initSlider = (durationMs, startMs, endMs) => {
        if (sliderCreated) {
            audioSlider.noUiSlider.destroy();
        }
        noUiSlider.create(audioSlider, {
            start: [startMs, endMs],
            connect: true,
            range: {
                'min': 0,
                'max': durationMs
            }
        });
        sliderCreated = true;

        audioSlider.noUiSlider.on('update', (values) => {
            currentClip.start = parseFloat(values[0]);
            currentClip.end = parseFloat(values[1]);
            startTimeDisplay.innerText = formatTime(currentClip.start);
            endTimeDisplay.innerText = formatTime(currentClip.end);
        });

        audioSlider.noUiSlider.on('slide', (values, handle) => {
            if (handle === 0) {
                fullSongAudio.currentTime = currentClip.start / 1000;
            } else {
                fullSongAudio.currentTime = currentClip.end / 1000;
            }
        });
    };

    applyEditsBtn.addEventListener('click', async () => {
        applyEditsBtn.innerText = "Creating...";
        applyEditsBtn.disabled = true;
        
        try {
            const response = await fetch(`/api/clip?song_id=${currentClip.songId}&start=${Math.floor(currentClip.start)}&end=${Math.floor(currentClip.end)}`, { method: 'POST' });
            const data = await response.json();
            
            if (response.ok) {
                clipAudio.src = data.url;
                downloadBtn.href = data.url;
                finalClipContainer.style.display = 'block';
                fullSongAudio.pause();
                clipAudio.play();
            } else {
                alert("Failed to create clip: " + (data.detail || "Unknown error"));
            }
        } catch (error) {
            console.error("Editor error:", error);
            alert("Error connecting to server.");
        } finally {
            applyEditsBtn.innerText = "Create New Clip";
            applyEditsBtn.disabled = false;
        }
    });

    // Search function
    const performSearch = async () => {
        const query = searchInput.value.trim();
        if (!query) return;

        resultsContainer.innerHTML = '';
        loading.classList.remove('hidden');

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            loading.classList.add('hidden');
            
            if (data.results && data.results.length > 0) {
                renderResults(data.results);
            } else {
                resultsContainer.innerHTML = `<p style="text-align: center; color: var(--text-muted); font-size: 1.2rem; padding: 2rem;">No matching lyrics found. Try something else!</p>`;
            }
        } catch (error) {
            loading.classList.add('hidden');
            resultsContainer.innerHTML = `<p style="color: red; text-align: center;">Something went wrong. Please try again.</p>`;
        }
    };

    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });

    const renderResults = (results) => {
        results.forEach(result => {
            const matchPercentage = Math.round(result.score * 100);
            const card = document.createElement('div');
            card.className = 'result-card';
            
            card.innerHTML = `
                <div class="result-info">
                    <p class="lyric-text">"${result.text}"</p>
                    <div class="song-meta">
                        <span class="match-score">${matchPercentage}% Match</span>
                        <span>•</span>
                        <span><strong>${result.title}</strong> by ${result.artist}</span>
                    </div>
                </div>
                <button class="create-clip-btn" data-id="${result.song_id}" data-start="${result.start}" data-end="${result.end}" data-lyric="${result.text}" data-title="${result.title}" data-artist="${result.artist}">
                    Edit & Clip
                </button>
            `;
            resultsContainer.appendChild(card);
        });

        document.querySelectorAll('.create-clip-btn').forEach(btn => {
            btn.addEventListener('click', handleCreateClip);
        });
    };

    const handleCreateClip = (e) => {
        const btn = e.target;
        const songId = btn.getAttribute('data-id');
        const start = parseInt(btn.getAttribute('data-start'));
        const end = parseInt(btn.getAttribute('data-end'));
        const lyric = btn.getAttribute('data-lyric');
        const title = btn.getAttribute('data-title');
        const artist = btn.getAttribute('data-artist');

        // Initialize editor state
        currentClip.songId = songId;
        currentClip.start = start;
        currentClip.end = end;
        
        clipLyricText.innerText = `"${lyric}"`;
        clipSongInfo.innerText = `${title} - ${artist}`;
        
        finalClipContainer.style.display = 'none';
        modal.classList.remove('hidden');

        // Load full song and init slider
        fullSongAudio.src = `/songs/${songId}.mp3`;
        fullSongAudio.onloadedmetadata = () => {
            initSlider(fullSongAudio.duration * 1000, start, end);
            fullSongAudio.currentTime = start / 1000;
            fullSongAudio.play();
        };
    };

    // Modal close logic
    const closeModal = () => {
        modal.classList.add('hidden');
        clipAudio.pause();
        fullSongAudio.pause();
    };
    
    closeBtn.addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
});

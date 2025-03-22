document.addEventListener('DOMContentLoaded', () => {
    const micButton = document.getElementById('mic-button');
    const recordingStatus = document.getElementById('recording-status');
    const recordingAnimation = document.getElementById('recording-animation');
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    
    let isRecording = false;
    
    // Mic button click handler - toggles recording
    micButton.addEventListener('click', async () => {
        if (!isRecording) {
            await startRecording();
        } else {
            await stopRecording();
        }
    });
    
    // Start recording function
    async function startRecording() {
        try {
            const response = await fetch('/api/start_recording', { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'success') {
                isRecording = true;
                recordingStatus.textContent = 'Listening...';
                micButton.classList.add('recording');
                recordingAnimation.classList.add('active');
            }
        } catch (error) {
            console.error('Error starting recording:', error);
            recordingStatus.textContent = 'Failed to start recording';
        }
    }
    
    // Stop recording function
    async function stopRecording() {
        try {
            const response = await fetch('/api/stop_recording', { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'success') {
                isRecording = false;
                recordingStatus.textContent = 'Processing...';
                
                // Show results when processing is done
                setTimeout(() => {
                    recordingStatus.textContent = 'Not recording';
                    micButton.classList.remove('recording');
                    recordingAnimation.classList.remove('active');
                    
                    // Fill the search input with the transcript
                    if (data.transcript) {
                        searchInput.value = data.transcript;
                        performSearch(data.transcript);
                    }
                }, 1000);
            }
        } catch (error) {
            console.error('Error stopping recording:', error);
            recordingStatus.textContent = 'Failed to stop recording';
            micButton.classList.remove('recording');
            recordingAnimation.classList.remove('active');
            isRecording = false;
        }
    }
    
    // Perform search
    function performSearch(query) {
        if (query && query.trim()) {
            console.log('Searching for:', query);
            
            // Create form data for the request
            const formData = new FormData();
            formData.append('query', query);
            formData.append('result_count', 10);
            formData.append('search_mode', 'standard');
            formData.append('show_metrics', true);
            
            // Send search request to backend
            fetch('/search', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                console.log('Search results:', data);
                if (data.results && data.results.length > 0) {
                    // Automatically submit search - result display would depend on your UI
                    // For now, just show an alert with the first result
                    const topResult = data.results[0];
                    alert(`Top result: ${topResult.title} (${topResult.similarity_percent}% match)`);
                } else {
                    alert('No results found for: ' + query);
                }
            })
            .catch(error => {
                console.error('Search error:', error);
                alert('Error performing search');
            });
        }
    }
    
    // Search button click handler
    searchButton.addEventListener('click', () => {
        const searchQuery = searchInput.value.trim();
        if (searchQuery) {
            performSearch(searchQuery);
        }
    });
    
    // Allow pressing Enter in the search input to search
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const searchQuery = searchInput.value.trim();
            if (searchQuery) {
                performSearch(searchQuery);
            }
        }
    });
});

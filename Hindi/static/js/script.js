/**
 * JavaScript for Hindi Semantic Search web application
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const searchForm = document.getElementById('search-form');
    const queryInput = document.getElementById('query');
    const resultsContainer = document.getElementById('results');
    const loadingIndicator = document.getElementById('loading');
    const searchStats = document.getElementById('search-stats');
    const recentSearchesList = document.getElementById('recent-searches-list');
    const themeSwitch = document.getElementById('theme-switch');
    const gridViewBtn = document.getElementById('grid-view-btn');
    const listViewBtn = document.getElementById('list-view-btn');
    const visualizationContainer = document.getElementById('visualization-container');
    const recordButton = document.getElementById('record-button');
    
    // Recording state
    let isRecording = false;
    
    // Audio recording functionality
    recordButton.addEventListener('click', function() {
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
    });
    
    function startRecording() {
        // First check if the browser supports the necessary APIs
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            searchStats.textContent = 'Browser does not support audio recording';
            return;
        }
        
        // First get system info to check if recording is possible
        fetch('/api/system_info')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const sysInfo = data.system_info;
                    
                    // Show warning if using simulation mode
                    if (sysInfo.simulation_mode) {
                        searchStats.textContent = 'Using simulation mode (no real microphone)';
                    }
                    
                    // Continue with recording request after checking system info
                    return requestMicrophoneAccess();
                } else {
                    throw new Error(data.message || 'Failed to get system information');
                }
            })
            .catch(error => {
                console.error('Error checking system info:', error);
                // Continue anyway, as the server will fall back to simulation if needed
                return requestMicrophoneAccess();
            });
    }
    
    function requestMicrophoneAccess() {
        // Request microphone permission to ensure it's available
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                // Stop the stream - we just need the permission
                stream.getTracks().forEach(track => track.stop());
                
                // Now make the server-side recording request
                return fetch('/api/start_recording', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    // Add empty JSON object as body to prevent parsing errors
                    body: JSON.stringify({})
                });
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.message || `Server responded with status ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    isRecording = true;
                    recordButton.classList.add('recording');
                    recordButton.innerHTML = '<i class="fas fa-stop-circle"></i>';
                    
                    // Show recording status
                    searchStats.textContent = 'Recording... Speak now';
                } else {
                    throw new Error(data.message || 'Unknown error');
                }
            })
            .catch(error => {
                console.error('Error starting recording:', error);
                searchStats.textContent = `Error starting recording: ${error.message}`;
                
                // Show system info and troubleshooting options
                const troubleshootLink = document.createElement('a');
                troubleshootLink.href = "#";
                troubleshootLink.textContent = "Click here to troubleshoot audio issues";
                troubleshootLink.className = "troubleshoot-link";
                troubleshootLink.onclick = showAudioDiagnostics;
                
                searchStats.appendChild(document.createElement('br'));
                searchStats.appendChild(troubleshootLink);
            });
    }
    
    function stopRecording() {
        fetch('/api/stop_recording', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            isRecording = false;
            recordButton.classList.remove('recording');
            recordButton.innerHTML = '<i class="fas fa-microphone"></i>';
            
            if (data.status === 'success' && data.transcript) {
                // Set the transcript as the search query
                queryInput.value = data.transcript;
                
                // Show transcription success message
                searchStats.textContent = `Transcribed: "${data.transcript}"`;
                
                // Automatically perform search with the transcript
                performSearch(data.transcript);
                saveRecentSearch(data.transcript);
            } else {
                searchStats.textContent = `Transcription failed: ${data.transcript || 'Unknown error'}`;
            }
        })
        .catch(error => {
            isRecording = false;
            recordButton.classList.remove('recording');
            recordButton.innerHTML = '<i class="fas fa-microphone"></i>';
            console.error('Error stopping recording:', error);
            searchStats.textContent = 'Error processing recording';
        });
    }
    
    // New function to show audio diagnostics
    function showAudioDiagnostics() {
        searchStats.textContent = 'Loading system information...';
        
        fetch('/api/system_info')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const sysInfo = data.system_info;
                    let diagnosticHTML = '<div class="audio-diagnostics">';
                    diagnosticHTML += '<h3>System Diagnostics</h3>';
                    
                    // System information section
                    diagnosticHTML += '<div class="system-info">';
                    diagnosticHTML += `<p><strong>Operating System:</strong> ${sysInfo.os} ${sysInfo.os_version}</p>`;
                    diagnosticHTML += `<p><strong>Python Version:</strong> ${sysInfo.python_version}</p>`;
                    diagnosticHTML += `<p><strong>Server Environment:</strong> ${sysInfo.server_env || 'development'}</p>`;
                    diagnosticHTML += `<p><strong>Simulation Mode:</strong> ${sysInfo.simulation_mode ? 'Enabled' : 'Disabled'}</p>`;
                    diagnosticHTML += `<p><strong>Recording Capability:</strong> ${sysInfo.can_record ? 'Available' : 'Unavailable'}</p>`;
                    diagnosticHTML += '</div>';
                    
                    // Audio devices section
                    if (sysInfo.devices && sysInfo.devices.length > 0) {
                        diagnosticHTML += '<h4>Audio Devices</h4>';
                        diagnosticHTML += '<ul class="device-list">';
                        
                        sysInfo.devices.forEach(device => {
                            const isUsable = device.inputs > 0;
                            diagnosticHTML += `<li class="${isUsable ? 'usable' : 'not-usable'}">`;
                            diagnosticHTML += `<strong>${device.name}</strong>`;
                            diagnosticHTML += `<br>Inputs: ${device.inputs}, Outputs: ${device.outputs}`;
                            if (device.default_input) diagnosticHTML += ' <span class="default-badge">Default Input</span>';
                            diagnosticHTML += '</li>';
                        });
                        
                        diagnosticHTML += '</ul>';
                    } else {
                        diagnosticHTML += '<p class="warning">No audio devices detected on the server</p>';
                    }
                    
                    // Troubleshooting tips
                    diagnosticHTML += '<h4>Troubleshooting Tips</h4>';
                    diagnosticHTML += '<ol>';
                    diagnosticHTML += '<li>Make sure your microphone is connected and not muted</li>';
                    diagnosticHTML += '<li>Check if your browser has permission to access the microphone</li>';
                    diagnosticHTML += '<li>Try reloading the page</li>';
                    diagnosticHTML += '<li>Check if another application is using your microphone</li>';
                    
                    // Server-specific tips
                    if (!sysInfo.can_record) {
                        diagnosticHTML += '<li class="important">The server appears to be in an environment without audio capture capability</li>';
                        diagnosticHTML += '<li>Simulation mode will be used instead of real microphone input</li>';
                    }
                    
                    diagnosticHTML += '</ol>';
                    diagnosticHTML += '</div>';
                    
                    resultsContainer.innerHTML = diagnosticHTML;
                } else {
                    searchStats.textContent = 'Error loading system information';
                }
            })
            .catch(error => {
                console.error('Error getting system info:', error);
                searchStats.textContent = 'Error getting system information';
            });
            
        return false; // Prevent default link behavior
    }
    
    // Utility function to format field values
    function formatFieldValue(value) {
        // Simply return the value as is if defined, otherwise return 'N/A'
        return value !== undefined && value !== null && value !== '' ? value : 'N/A';
    }
    
    // Safely parse JSON with improved error handling
    function safeJSONParse(jsonString, fallback) {
        // If empty or not a string, return fallback
        if (!jsonString || typeof jsonString !== 'string') return fallback;
        
        try {
            // Clean the string of potential problematic characters
            const cleanedString = jsonString
                .replace(/[\u0000-\u001F]+/g, '') // Remove control characters
                .replace(/\\"/g, '"')             // Fix escaped quotes
                .replace(/'/g, '"')               // Replace single quotes with double quotes
                .replace(/\t/g, '    ');          // Replace tabs with spaces
            
            return JSON.parse(cleanedString);
        } catch (error) {
            console.error('JSON Parse Error:', error.message);
            
            // Try to identify problematic line and position
            if (error.message.includes('at line')) {
                try {
                    const errorInfo = error.message.match(/at line (\d+) column (\d+)/);
                    if (errorInfo) {
                        const line = parseInt(errorInfo[1]);
                        const column = parseInt(errorInfo[2]);
                        const lines = jsonString.split('\n');
                        
                        if (lines.length >= line) {
                            const errorLine = lines[line - 1];
                            console.error(`Problematic line: ${errorLine}`);
                            console.error(`Error position: ${'-'.repeat(column-1)}^`);
                        }
                    }
                } catch (logError) {
                    console.error('Error while logging JSON error details:', logError);
                }
            }
            
            // Clear potentially corrupted data
            if (typeof localStorage !== 'undefined') {
                localStorage.removeItem('recentSearches');
            }
            return fallback;
        }
    }
    
    // Initialize app with defaults if localStorage is corrupted
    function initializeAppDefaults() {
        // Clear localStorage entirely as it may be corrupted
        try {
            localStorage.clear();
            console.info('localStorage cleared due to corruption');
        } catch (e) {
            console.error('Failed to clear localStorage:', e);
        }
        
        // Set default theme
        document.documentElement.setAttribute('data-theme', 'light');
        if (themeSwitch) themeSwitch.checked = false;
        
        // Clear recent searches UI
        if (recentSearchesList) recentSearchesList.innerHTML = '';
    }
    
    // Set initial theme from localStorage or default to light
    try {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        themeSwitch.checked = savedTheme === 'dark';
    } catch (error) {
        console.error('Error loading theme preference:', error);
        document.documentElement.setAttribute('data-theme', 'light');
        themeSwitch.checked = false;
    }
    
    // Load recent searches from local storage
    loadRecentSearches();
    
    // Theme toggle functionality
    themeSwitch.addEventListener('change', function() {
        try {
            if (this.checked) {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
            }
            
            // Update visualization if it exists
            if (window.resultChart) {
                updateChartColors();
            }
        } catch (error) {
            console.error('Error saving theme preference:', error);
        }
    });
    
    // View toggle functionality
    gridViewBtn.addEventListener('click', function() {
        resultsContainer.className = 'results-container grid-view';
        gridViewBtn.classList.add('active');
        listViewBtn.classList.remove('active');
        localStorage.setItem('viewMode', 'grid');
    });
    
    listViewBtn.addEventListener('click', function() {
        resultsContainer.className = 'results-container list-view';
        listViewBtn.classList.add('active');
        gridViewBtn.classList.remove('active');
        localStorage.setItem('viewMode', 'list');
    });
    
    // Restore view mode preference
    const viewMode = localStorage.getItem('viewMode') || 'grid';
    if (viewMode === 'list') {
        listViewBtn.click();
    }
    
    // Search form submission
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (query) {
            performSearch(query);
            saveRecentSearch(query);
        }
    });
    
    // Function to perform search
    function performSearch(query) {
        // Show loading indicator
        loadingIndicator.style.display = 'flex';
        resultsContainer.innerHTML = '';
        searchStats.textContent = '';
        visualizationContainer.style.display = 'none';
        
        // Get top-k value
        const topK = document.getElementById('top-k').value;
        
        // Create form data for POST request
        const formData = new FormData();
        formData.append('query', query);
        formData.append('top_k', topK);
        
        // Send the search request
        fetch('/search', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.text().then(text => {
                try {
                    return JSON.parse(text);
                } catch (error) {
                    console.error('Error parsing response JSON:', error);
                    console.error('Response text:', text);
                    throw new Error('Invalid JSON response from server');
                }
            });
        })
        .then(data => {
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
            
            if (data.error) {
                searchStats.textContent = `Error: ${data.error}`;
                return;
            }
            
            // Show search stats
            searchStats.textContent = `Found ${data.count} results in ${data.elapsed} seconds`;
            
            // Create visualization if we have results
            if (data.results && data.results.length > 0) {
                createVisualization(data.results);
                visualizationContainer.style.display = 'block';
            }
            
            // Display results with staggered animation
            displayResults(data.results);
        })
        .catch(error => {
            loadingIndicator.style.display = 'none';
            searchStats.textContent = `Error: ${error.message}`;
            console.error('Search error:', error);
        });
    }
    
    // Function to display search results with staggered animation
    function displayResults(results) {
        resultsContainer.innerHTML = '';
        
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results"><i class="fas fa-search"></i><p>No results found</div>';
            return;
        }
        
        // Get template
        const template = document.getElementById('result-template');
        
        // Use staggered animation delay for each card
        results.forEach((result, index) => {
            // Clone the template
            const resultElement = document.importNode(template.content, true);
            const doc = result.document;
            
            // Calculate score percentage
            const scorePercentage = Math.round(result.score * 100);
            
            // Set the content
            resultElement.querySelector('.rank-badge').textContent = `#${result.rank}`;
            resultElement.querySelector('.score-badge').textContent = `${scorePercentage}%`;
            resultElement.querySelector('.description').textContent = doc.description;
            
            // Use the formatting utility for classification fields
            resultElement.querySelector('.section-value').textContent = formatFieldValue(doc.section);
            resultElement.querySelector('.division-value').textContent = formatFieldValue(doc.division);
            resultElement.querySelector('.group-value').textContent = formatFieldValue(doc.group);
            resultElement.querySelector('.class-value').textContent = formatFieldValue(doc.class);
            resultElement.querySelector('.subclass-value').textContent = formatFieldValue(doc.subclass);
            
            // Add color to score badge based on score
            const scoreBadge = resultElement.querySelector('.score-badge');
            if (scorePercentage >= 80) {
                scoreBadge.style.backgroundColor = 'var(--success-color)';
            } else if (scorePercentage >= 50) {
                scoreBadge.style.backgroundColor = 'var(--warning-color)';
            } else {
                scoreBadge.style.backgroundColor = 'var(--danger-color)';
            }
            
            // Add staggered animation delay
            const card = resultElement.querySelector('.result-card');
            card.style.animationDelay = `${index * 0.1}s`;
            
            resultsContainer.appendChild(resultElement);
        });
    }
    
    // Function to create visualization of results
    function createVisualization(results) {
        // Prepare data for visualization
        let labels = results.slice(0, 10).map(result => {
            const doc = result.document;
            // Create short label from description (max 20 chars)
            const shortDesc = doc.description.length > 20 ? 
                doc.description.substring(0, 20) + '...' : 
                doc.description;
            return shortDesc;
        });
        
        let scores = results.slice(0, 10).map(result => Math.round(result.score * 100));
        
        // Get theme colors
        const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark';
        const textColor = isDarkTheme ? '#f9fafb' : '#1f2937';
        const gridColor = isDarkTheme ? '#374151' : '#e5e7eb';
        
        // Create chart
        visualizationContainer.innerHTML = '<canvas id="resultsChart"></canvas>';
        const ctx = document.getElementById('resultsChart').getContext('2d');
        
        // Define gradient for bars
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        if (isDarkTheme) {
            gradient.addColorStop(0, 'rgba(129, 140, 248, 1)');
            gradient.addColorStop(1, 'rgba(99, 102, 241, 0.2)');
        } else {
            gradient.addColorStop(0, 'rgba(99, 102, 241, 1)');
            gradient.addColorStop(1, 'rgba(129, 140, 248, 0.2)');
        }
        
        window.resultChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Similarity Score (%)',
                    data: scores,
                    backgroundColor: gradient,
                    borderColor: isDarkTheme ? 'rgba(129, 140, 248, 1)' : 'rgba(99, 102, 241, 1)',
                    borderWidth: 1,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: textColor
                        }
                    },
                    title: {
                        display: true,
                        text: 'Top Search Results by Similarity',
                        color: textColor,
                        font: {
                            size: 16
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: gridColor
                        },
                        ticks: {
                            color: textColor
                        }
                    },
                    x: {
                        grid: {
                            color: gridColor
                        },
                        ticks: {
                            color: textColor
                        }
                    }
                },
                animation: {
                    duration: 1500
                }
            }
        });
    }
    
    // Update chart colors on theme change
    function updateChartColors() {
        if (window.resultChart) {
            const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark';
            const textColor = isDarkTheme ? '#f9fafb' : '#1f2937';
            const gridColor = isDarkTheme ? '#374151' : '#e5e7eb';
            
            // Update chart colors
            window.resultChart.options.plugins.legend.labels.color = textColor;
            window.resultChart.options.plugins.title.color = textColor;
            window.resultChart.options.scales.y.grid.color = gridColor;
            window.resultChart.options.scales.x.grid.color = gridColor;
            window.resultChart.options.scales.y.ticks.color = textColor;
            window.resultChart.options.scales.x.ticks.color = textColor;
            
            // Update gradient
            const ctx = document.getElementById('resultsChart').getContext('2d');
            const gradient = ctx.createLinearGradient(0, 0, 0, 400);
            if (isDarkTheme) {
                gradient.addColorStop(0, 'rgba(129, 140, 248, 1)');
                gradient.addColorStop(1, 'rgba(99, 102, 241, 0.2)');
            } else {
                gradient.addColorStop(0, 'rgba(99, 102, 241, 1)');
                gradient.addColorStop(1, 'rgba(129, 140, 248, 0.2)');
            }
            
            window.resultChart.data.datasets[0].backgroundColor = gradient;
            window.resultChart.data.datasets[0].borderColor = isDarkTheme ? 
                'rgba(129, 140, 248, 1)' : 'rgba(99, 102, 241, 1)';
            
            window.resultChart.update();
        }
    }
    
    // Function to save recent search to localStorage
    function saveRecentSearch(query) {
        if (!query || typeof query !== 'string') return;
        
        try {
            // Get existing searches or initialize empty array if none exist
            let recentSearches = [];
            
            try {
                const storedSearches = localStorage.getItem('recentSearches');
                if (storedSearches) {
                    const parsedSearches = safeJSONParse(storedSearches, null);
                    if (Array.isArray(parsedSearches)) {
                        recentSearches = parsedSearches;
                    }
                }
            } catch (parseError) {
                console.error('Error parsing stored searches, resetting:', parseError);
                recentSearches = [];
            }
            
            // Ensure we have a valid array
            if (!Array.isArray(recentSearches)) {
                recentSearches = [];
            }
            
            // Remove duplicates
            recentSearches = recentSearches.filter(item => 
                item && typeof item === 'string' && item !== query
            );
            
            // Add new query to the beginning
            recentSearches.unshift(query);
            
            // Keep only the last 10 searches
            recentSearches = recentSearches.slice(0, 10);
            
            // Store the updated searches
            localStorage.setItem('recentSearches', JSON.stringify(recentSearches));
            
            // Update the UI
            loadRecentSearches();
        } catch (error) {
            console.error('Error saving recent searches:', error);
            // Attempt to reset the storage if corrupted
            try {
                localStorage.removeItem('recentSearches');
            } catch (e) {
                console.error('Failed to remove corrupted data:', e);
            }
        }
    }
    
    // Function to load recent searches from localStorage
    function loadRecentSearches() {
        // Clear the current list
        recentSearchesList.innerHTML = '';
        
        try {
            const storedSearches = localStorage.getItem('recentSearches');
            if (!storedSearches) return;
            
            let recentSearches = safeJSONParse(storedSearches, []);
            
            // Validate that we have an array
            if (!Array.isArray(recentSearches)) {
                console.error('Stored searches is not an array, resetting');
                localStorage.removeItem('recentSearches');
                return;
            }
            
            // Filter out invalid entries
            recentSearches = recentSearches.filter(query => 
                query && typeof query === 'string'
            );
            
            // Build the UI
            recentSearches.forEach(query => {
                const li = document.createElement('li');
                li.textContent = query;
                li.addEventListener('click', () => {
                    queryInput.value = query;
                    performSearch(query);
                });
                recentSearchesList.appendChild(li);
            });
        } catch (error) {
            console.error('Error loading recent searches:', error);
            try {
                // Reset recent searches if there's an error
                localStorage.removeItem('recentSearches');
            } catch (e) {
                console.error('Failed to remove corrupted data:', e);
                // If we can't even remove the item, try to reset everything
                initializeAppDefaults();
            }
        }
    }
    
    // Keyboard shortcut for search input focus
    document.addEventListener('keydown', function(e) {
        // Ctrl+/ or Cmd+/ to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            queryInput.focus();
        }
    });
    
    // Focus search input on page load
    setTimeout(() => {
        queryInput.focus();
    }, 500);
});

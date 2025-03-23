document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('results-container');
    const validResultsList = document.getElementById('valid-results-list');
    const otherResultsList = document.getElementById('other-results-list');
    const loadingSpinner = document.getElementById('loading-spinner');
    const noResults = document.getElementById('no-results');
    const noValidResults = document.getElementById('no-valid-results');
    const noOtherResults = document.getElementById('no-other-results');
    
    // Performance metrics elements
    const performanceMetrics = document.getElementById('performance-metrics');
    const searchTimeSpan = document.getElementById('search-time');
    const indexTimeSpan = document.getElementById('index-time');
    const resultsCountSpan = document.getElementById('results-count');
    
    // Form elements for advanced search
    const resultCountSelect = document.getElementById('result-count');
    const searchModeSelect = document.getElementById('search-mode');
    const showPerformanceCheckbox = document.getElementById('show-performance');
    const advancedSearchToggle = document.getElementById('advanced-search-toggle');
    const advancedSearchOptions = document.getElementById('advanced-search-options');
    const toggleIcon = document.getElementById('toggle-icon');
    
    // Toggle advanced search options
    if (advancedSearchToggle) {
        advancedSearchToggle.addEventListener('click', function() {
            if (advancedSearchOptions.style.display === 'none' || !advancedSearchOptions.style.display) {
                advancedSearchOptions.style.display = 'block';
                toggleIcon.textContent = '▲';
            } else {
                advancedSearchOptions.style.display = 'none';
                toggleIcon.textContent = '▼';
            }
        });
    }
    
    // Admin panel elements
    const adminToggle = document.getElementById('admin-toggle');
    const adminPanel = document.getElementById('admin-panel');
    const rebuildIndexBtn = document.getElementById('rebuild-index-btn');
    const rebuildStatus = document.getElementById('rebuild-status');
    const getStatsBtn = document.getElementById('get-stats-btn');
    const indexStats = document.getElementById('index-stats');
    
    // Admin panel toggle
    adminToggle.addEventListener('click', function() {
        adminPanel.style.display = adminPanel.style.display === 'none' ? 'block' : 'none';
    });
    
    // Rebuild index functionality
    if (rebuildIndexBtn) {
        rebuildIndexBtn.addEventListener('click', function() {
            rebuildStatus.style.display = 'block';
            rebuildStatus.innerHTML = '<div class="alert alert-info">Rebuilding FAISS index, please wait...</div>';
            rebuildIndexBtn.disabled = true;
            
            fetch('/rebuild-index', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    rebuildStatus.innerHTML = '<div class="alert alert-success">Index rebuilt successfully!</div>';
                } else {
                    rebuildStatus.innerHTML = `<div class="alert alert-danger">Error: ${data.message}</div>`;
                }
                rebuildIndexBtn.disabled = false;
            })
            .catch(error => {
                rebuildStatus.innerHTML = `<div class="alert alert-danger">Error: ${error}</div>`;
                rebuildIndexBtn.disabled = false;
            });
        });
    }
    
    // Get index stats functionality
    if (getStatsBtn) {
        getStatsBtn.addEventListener('click', function() {
            indexStats.style.display = 'block';
            indexStats.innerHTML = '<div class="alert alert-info">Fetching index statistics...</div>';
            getStatsBtn.disabled = true;
            
            fetch('/get-index-stats')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    let statsHtml = '<div class="alert alert-success">';
                    statsHtml += '<h5>FAISS Index Statistics</h5>';
                    statsHtml += '<ul class="list-group mt-2">';
                    
                    for (const [key, value] of Object.entries(data.stats)) {
                        statsHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">
                                        <span>${key.replace(/_/g, ' ').charAt(0).toUpperCase() + key.replace(/_/g, ' ').slice(1)}</span>
                                        <span class="badge bg-primary rounded-pill">${value}</span>
                                    </li>`;
                    }
                    
                    statsHtml += '</ul></div>';
                    indexStats.innerHTML = statsHtml;
                } else {
                    indexStats.innerHTML = `<div class="alert alert-danger">Error: ${data.message}</div>`;
                }
                getStatsBtn.disabled = false;
            })
            .catch(error => {
                indexStats.innerHTML = `<div class="alert alert-danger">Error: ${error}</div>`;
                getStatsBtn.disabled = false;
            });
        });
    }
    
    // Clear embedding cache functionality
    const clearCacheBtn = document.getElementById('clear-cache-btn');
    const clearCacheStatus = document.getElementById('clear-cache-status');
    
    if (clearCacheBtn) {
        clearCacheBtn.addEventListener('click', function() {
            clearCacheStatus.style.display = 'block';
            clearCacheStatus.innerHTML = '<div class="alert alert-info">Clearing embedding cache...</div>';
            clearCacheBtn.disabled = true;
            
            fetch('/clear-embedding-cache', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    clearCacheStatus.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                } else {
                    clearCacheStatus.innerHTML = `<div class="alert alert-danger">Error: ${data.message}</div>`;
                }
                clearCacheBtn.disabled = false;
            })
            .catch(error => {
                clearCacheStatus.innerHTML = `<div class="alert alert-danger">Error: ${error}</div>`;
                clearCacheBtn.disabled = false;
            });
        });
    }
    
    // Language management
    const langButtons = document.querySelectorAll('.btn-language');
    let currentLanguage = localStorage.getItem('selectedLanguage') || 'english';
    
    // Set initial language
    setActiveLanguage(currentLanguage);
    applyTranslations(currentLanguage);
    
    // Language button click handlers
    langButtons.forEach(button => {
        button.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            setActiveLanguage(lang);
            applyTranslations(lang);
            localStorage.setItem('selectedLanguage', lang);
            
            // Update language on server if API exists
            fetch('/api/set-language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ language: lang })
            })
            .then(response => response.json())
            .catch(error => {
                console.error('Error updating language:', error);
            });
            
            // Log for debugging
            console.log('Language changed to:', lang);
        });
    });
    
    function setActiveLanguage(lang) {
        const langButtons = document.querySelectorAll('.btn-language');
        langButtons.forEach(btn => {
            if (btn.getAttribute('data-lang') === lang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
    
    function applyTranslations(lang) {
        const translations = {
            'english': {
                'header': 'NIC Code Semantic Search',
                'subtitle': 'Search for industry codes and descriptions using natural language',
                'search_placeholder': 'Describe a business activity or industry...',
                'search_button': 'Search',
                'advanced': 'Advanced Search Options',
                'results-to-show': 'Results to show',
                'search-mode': 'Search mode',
                'standard': 'Standard',
                'strict': 'Strict',
                'relaxed': 'Relaxed',
                'show-metrics': 'Show performance metrics',
                'searching': 'Searching for matching NIC codes...',
                'no_results': 'No results found. Try a different search term.',
                'error_message': 'An error occurred while processing your search. Please try again later.',
                'examples': 'Example searches: "bakery", "software development", "wheat farming", "manufacture of plastic products"'
            },
            'hindi': {
                'header': 'एनआईसी कोड सिमेंटिक सर्च',
                'subtitle': 'प्राकृतिक भाषा का उपयोग करके उद्योग कोड और विवरण खोजें',
                'search_placeholder': 'व्यावसायिक गतिविधि या उद्योग का वर्णन करें...',
                'search_button': 'खोज',
                'advanced': 'उन्नत खोज विकल्प',
                'results-to-show': 'दिखाने के लिए परिणाम',
                'search-mode': 'खोज मोड',
                'standard': 'मानक',
                'strict': 'सख्त',
                'relaxed': 'आराम',
                'show-metrics': 'प्रदर्शन मेट्रिक्स दिखाएं',
                'searching': 'मिलान एनआईसी कोड खोज रहा है...',
                'no_results': 'कोई परिणाम नहीं मिला। कोई अलग खोज शब्द आज़माएं।',
                'error_message': 'आपकी खोज को संसाधित करते समय एक त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।',
                'examples': 'उदाहरण खोज: "बेकरी", "सॉफ्टवेयर विकास", "गेहूं की खेती", "प्लास्टिक उत्पादों का निर्माण"'
            }
        };
        
        // Apply translations to elements with t-* classes
        const dict = translations[lang] || translations['english'];
        document.querySelectorAll('[class*="t-"]').forEach(elem => {
            // Extract translation keys from class names (t-key)
            const classes = elem.className.split(' ');
            for (const cls of classes) {
                if (cls.startsWith('t-')) {
                    const key = cls.substring(2);
                    if (dict[key]) {
                        elem.textContent = dict[key];
                    }
                }
            }
        });
        
        // Update search placeholder
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.placeholder = dict.search_placeholder;
        
        // Apply RTL styling for Hindi if needed
        document.body.classList.toggle('rtl-support', lang === 'hindi');
        
        // Set html lang attribute for better font rendering
        document.documentElement.setAttribute('lang', lang);
    }

    // Search form submission logic
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const query = searchInput.value.trim();
        if (query === '') return;
        
        // Get the advanced search parameters
        const resultCount = resultCountSelect ? resultCountSelect.value : 10;
        const searchMode = searchModeSelect ? searchModeSelect.value : 'standard';
        const showMetrics = showPerformanceCheckbox ? showPerformanceCheckbox.checked : false;
        
        // Get current language
        const currentLanguage = localStorage.getItem('selectedLanguage') || 'english';
        
        // Reset performance metrics display
        performanceMetrics.style.display = 'none';
        
        // Show loading spinner
        loadingSpinner.style.display = 'block';
        
        // Hide results while loading
        resultsContainer.style.display = 'none';
        
        // Reset results display
        noResults.style.display = 'none';
        validResultsList.innerHTML = '';
        otherResultsList.innerHTML = '';
        noValidResults.style.display = 'none';
        noOtherResults.style.display = 'none';
        
        // For Hindi, use JSON format with the language parameter
        if (currentLanguage === 'hindi') {
            fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    count: resultCount,
                    mode: searchMode,
                    metrics: showMetrics,
                    language: 'hindi'
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Process search results
                processSearchResults(data, showMetrics);
            })
            .catch(error => {
                // Handle errors
                console.error('Search error:', error);
                loadingSpinner.style.display = 'none';
                noResults.textContent = 'An error occurred while processing your request.';
                noResults.style.display = 'block';
            });
        } else {
            // For English searches, keep the existing form data approach
            const formData = new FormData();
            formData.append('query', query);
            formData.append('result_count', resultCount);
            formData.append('search_mode', searchMode);
            formData.append('show_metrics', showMetrics);
            
            fetch('/search', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Process search results
                processSearchResults(data, showMetrics);
            })
            .catch(error => {
                // Handle errors
                console.error('Search error:', error);
                loadingSpinner.style.display = 'none';
                noResults.textContent = 'An error occurred while processing your request.';
                noResults.style.display = 'block';
            });
        }
    });

    function processSearchResults(data, showMetrics) {
        // Hide loading spinner
        loadingSpinner.style.display = 'none';
        
        // Show results container
        resultsContainer.style.display = 'block';
        
        // Display performance metrics if requested and available
        if (showMetrics && data.metrics) {
            searchTimeSpan.textContent = data.metrics.total_time_ms;
            indexTimeSpan.textContent = data.metrics.index_time_ms;
            resultsCountSpan.textContent = data.metrics.results_count;
            performanceMetrics.style.display = 'block';
        }
        
        if (data.error) {
            console.error("Search error:", data.error);
            noResults.style.display = 'block';
            noResults.textContent = `Error: ${data.error}. Please try again.`;
            return;
        }
        
        // Debug the data structure
        console.log("Search results received:", data);
        
        const results = data.results || [];
        
        if (results.length === 0) {
            noResults.style.display = 'block';
            noResults.textContent = 'No matches found. Try a different search term.';
            return;
        }
        
        // Process and display results
        let validResultsCount = 0;
        let otherResultsCount = 0;
        
        results.forEach((result, index) => {
            try {
                // Validate result object
                if (!result || typeof result !== 'object') {
                    console.error(`Invalid result at index ${index}:`, result);
                    return;
                }
                
                // Make sure similarity exists and is a number
                if (typeof result.similarity !== 'number') {
                    console.error(`Invalid similarity score for result at index ${index}:`, result);
                    result.similarity = 0;  // Set default value
                }
                
                // Get the subClass and class values and convert to string
                let subClass = result['Sub-Class'] || '';
                subClass = String(subClass).trim();
                
                let classVal = result.Class || '';
                classVal = String(classVal).trim();
                
                // Instead of converting to integers, just use the original values
                const formattedSubClass = subClass;
                const formattedClass = classVal;
                const formattedGroup = result.Group || '';
                const formattedDivision = result.Division || '';
                
                // Create result card
                const resultCard = document.createElement('div');
                resultCard.className = 'result-card';
                resultCard.setAttribute('data-index', index);
                
                // Format similarity score as integer percentage (no decimal places)
                const similarityPercent = Math.round(result.similarity * 100);
                
                // Get badge color based on similarity
                let badgeColor = 'secondary';
                if (similarityPercent >= 90) badgeColor = 'success';
                else if (similarityPercent >= 70) badgeColor = 'primary';
                else if (similarityPercent >= 50) badgeColor = 'info';
                else if (similarityPercent >= 30) badgeColor = 'warning';
                else badgeColor = 'danger';
                
                // Safely get properties with fallbacks
                const section = result.Section || 'N/A';
                const division = result.Division || 'N/A';
                const group = result.Group || 'N/A';
                const description = result.Description || 'No description available';
                
                // Determine if this is a valid result (has non-empty, non-null, non-"nan" Sub-Class)
                const isValidSubClass = subClass && 
                                      subClass !== 'N/A' && 
                                      subClass.toLowerCase() !== 'nan' &&
                                      subClass !== 'undefined' && 
                                      subClass !== 'null';
                
                // Determine if this is a result with valid Class but invalid Sub-Class
                const hasValidClass = classVal && 
                                    classVal !== 'N/A' && 
                                    classVal.toLowerCase() !== 'nan' &&
                                    classVal !== 'undefined' && 
                                    classVal !== 'null';
                
                // Use Sub-Class as title for valid results, otherwise use Class
                const title = isValidSubClass ? formattedSubClass : (hasValidClass ? `Class: ${formattedClass}` : `Result #${index + 1}`);
                
                // Check if description is long enough to truncate
                const isTruncatable = description.length > 300;
                const truncatedClass = isTruncatable ? 'truncated' : '';
                
                // Prepare HTML for card content
                resultCard.innerHTML = `
                    <div class="result-title">
                        <h4>${title}</h4>
                        <span class="badge bg-${badgeColor} similarity-badge">${similarityPercent}% Match</span>
                    </div>
                    <div>
                        <span class="badge bg-primary section-badge">Section: ${section}</span>
                    </div>
                    
                    <!-- Description right after the section -->
                    <div class="description-text ${truncatedClass}">${description}</div>
                    
                    <div class="code-hierarchy">
                        <div class="code-item">
                            <span class="code-item-label">Division:</span> ${formattedDivision}
                        </div>
                        <div class="code-item">
                            <span class="code-item-label">Group:</span> ${formattedGroup}
                        </div>
                        <div class="code-item">
                            <span class="code-item-label">Class:</span> ${formattedClass}
                        </div>
                        <div class="code-item">
                            <span class="code-item-label">Sub-Class:</span> ${isValidSubClass ? formattedSubClass : 'N/A'}
                        </div>
                    </div>
                    
                    <div class="detail-grid">
                        ${isValidSubClass ? `
                        <div class="detail-item">
                            <div class="detail-label">Industry Code</div>
                            <div class="detail-value">${formattedSubClass}</div>
                        </div>
                        ` : ''}
                        <div class="detail-item">
                            <div class="detail-label">Section</div>
                            <div class="detail-value">${section}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Division</div>
                            <div class="detail-value">${formattedDivision}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Group</div>
                            <div class="detail-value">${formattedGroup}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Class</div>
                            <div class="detail-value">${formattedClass}</div>
                        </div>
                        ${isValidSubClass ? `
                        <div class="detail-item">
                            <div class="detail-label">Sub-Class</div>
                            <div class="detail-value">${formattedSubClass}</div>
                        </div>
                        ` : ''}
                        <div class="detail-item">
                            <div class="detail-label">Similarity Score</div>
                            <div class="detail-value">${similarityPercent}%</div>
                        </div>
                    </div>
                    
                    <div class="expand-indicator">
                        <span class="expand-text">Click to view more details <i class="expand-icon">▼</i></span>
                        <span class="collapse-text">Click to collapse <i class="expand-icon">▼</i></span>
                    </div>
                `;
                
                // Add click event listener to make card expandable
                resultCard.addEventListener('click', function(event) {
                    // Toggle the expanded class
                    this.classList.toggle('expanded');
                });
                
                // Add to appropriate container based on validity criteria
                if (isValidSubClass) {
                    validResultsList.appendChild(resultCard);
                    validResultsCount++;
                } else if (hasValidClass) {
                    // Only add to other results if it has a valid Class but invalid Sub-Class
                    otherResultsList.appendChild(resultCard);
                    otherResultsCount++;
                } // If neither valid Sub-Class nor valid Class, don't show
                
            } catch (err) {
                console.error(`Error rendering result at index ${index}:`, err);
            }
        });
        
        // Show appropriate messages if either column is empty
        if (validResultsCount === 0) {
            noValidResults.style.display = 'block';
        }
        
        if (otherResultsCount === 0) {
            noOtherResults.style.display = 'block';
        }
        
        // If both columns are empty, show the main no results message
        if (validResultsCount === 0 && otherResultsCount === 0) {
            noResults.style.display = 'block';
            noResults.textContent = 'No results found. Try a different search term.';
        }
    }

    let isRecording = false;

    function toggleRecording() {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    }

    function startRecording() {
        fetch('/api/start_recording', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    isRecording = true;
                    document.getElementById('mic-button').innerText = '⏹️';
                }
            });
    }

    function stopRecording() {
        fetch('/api/stop_recording', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    isRecording = false;
                    document.getElementById('mic-button').innerText = '🎤';
                    document.getElementById('search-input').value = data.transcript;
                }
            });
    }

    document.getElementById('mic-button').addEventListener('click', toggleRecording);
});

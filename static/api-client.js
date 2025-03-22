/**
 * Client-side script to interact with the FastAPI backend
 */

// API Client for NIC Code Semantic Search

// Initialize the API client object
window.apiClient = {
    // Search function using JSON
    searchWithJson: async function(query, resultCount, searchMode, showMetrics) {
        const currentLang = localStorage.getItem('selectedLanguage') || 'english';
        console.log('Searching with language:', currentLang);
        
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                count: resultCount,
                mode: searchMode,
                metrics: showMetrics,
                language: currentLang
            })
        });
        return await response.json();
    },
    
    // Get current language
    getCurrentLanguage: async function() {
        try {
            const response = await fetch('/api/languages');
            return await response.json();
        } catch (error) {
            console.error('Error getting current language:', error);
            return { current: 'english' };
        }
    },
    
    // Set language
    setLanguage: async function(language) {
        try {
            const response = await fetch('/api/set-language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ language: language })
            });
            return await response.json();
        } catch (error) {
            console.error('Error setting language:', error);
            return { status: 'error', message: error.toString() };
        }
    },
    
    // Perform admin operations
    performAdminOperation: async function(operation) {
        let endpoint = '';
        switch(operation) {
            case 'rebuild-index':
                endpoint = '/rebuild-index';
                break;
            case 'clear-embedding-cache':
                endpoint = '/clear-embedding-cache';
                break;
            default:
                throw new Error(`Unknown operation: ${operation}`);
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        return await response.json();
    },
    
    // Get index stats
    getIndexStats: async function() {
        const response = await fetch('/get-index-stats');
        const data = await response.json();
        if (data.status === 'success') {
            return data.stats;
        } else {
            throw new Error(data.message || 'Failed to get index stats');
        }
    }
};

console.log('API client initialized');

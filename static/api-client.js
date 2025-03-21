/**
 * Client-side script to interact with the FastAPI backend
 */

// Function to handle search using Fetch API for JSON payload
async function searchWithJson(query, resultCount, searchMode, showMetrics) {
    try {
        console.log("Sending JSON search request:", {
            query, 
            result_count: parseInt(resultCount), 
            search_mode: searchMode, 
            show_metrics: showMetrics
        });
        
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                result_count: parseInt(resultCount),
                search_mode: searchMode,
                show_metrics: showMetrics
            })
        });

        // First, get the raw text of the response for debugging
        const responseText = await response.text();
        console.log("Raw response:", responseText);
        
        if (!response.ok) {
            console.error(`Error response: ${response.status} ${response.statusText}`, responseText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Parse the text as JSON
        try {
            return JSON.parse(responseText);
        } catch (jsonError) {
            console.error("Failed to parse JSON response:", jsonError);
            throw new Error("Invalid JSON response from server");
        }
    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
}

// Function to handle search using FormData
async function searchWithFormData(query, resultCount, searchMode, showMetrics) {
    try {
        // Create form data for the request
        const formData = new FormData();
        formData.append('query', query);
        formData.append('result_count', resultCount);
        formData.append('search_mode', searchMode);
        formData.append('show_metrics', showMetrics.toString());
        
        console.log("Sending form data search request");
        
        const response = await fetch('/search', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Error response: ${response.status} ${response.statusText}`, errorText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
}

// Function to handle admin operations
async function performAdminOperation(endpoint) {
    try {
        const response = await fetch(`/${endpoint}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Admin operation error (${endpoint}):`, error);
        throw error;
    }
}

// Function to get index statistics
async function getIndexStats() {
    try {
        const response = await fetch('/get-index-stats');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Get stats error:", error);
        throw error;
    }
}

// Export functions for use in main script.js
window.apiClient = {
    searchWithJson,
    searchWithFormData,
    performAdminOperation,
    getIndexStats
};

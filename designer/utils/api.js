// API utility functions

// Load resources from the server
async function loadResources() {
    console.log('Loading resources...');
    try {
        const response = await fetch('/api/resources');
        if (response.ok) {
            const data = await response.json();
            console.log('Resources loaded:', data);
            return data;
        }
        return [];
    } catch (err) {
        console.error('Failed to load resources:', err);
        return [];
    }
}

// Load configuration from the server
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            const data = await response.json();
            return data;
        }
        return { project_name: '', api_base_url: '' };
    } catch (err) {
        console.error('Failed to load config:', err);
        return { project_name: '', api_base_url: '' };
    }
}

// Load a specific resource
async function loadResource(resourceName) {
    try {
        const response = await fetch(`/api/resource/${resourceName}`);
        if (response.ok) {
            const data = await response.json();
            return data;
        }
        return null;
    } catch (err) {
        console.error('Failed to load resource:', err);
        return null;
    }
}

// Delete a resource
async function deleteResource(resourceName) {
    try {
        const response = await fetch(`/api/resource/${resourceName}`, {
            method: 'DELETE'
        });
        
        return response.ok;
    } catch (err) {
        console.error('Failed to delete resource:', err);
        return false;
    }
}

// Save configuration
async function saveConfig(config) {
    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });
        
        return response.ok;
    } catch (err) {
        console.error('Failed to save config:', err);
        return false;
    }
}

// Generate API from JSON
async function generateApi(jsonContent) {
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(jsonContent)
        });
        
        return await response.json();
    } catch (err) {
        console.error('Failed to generate:', err);
        return { success: false, error: 'Failed to generate' };
    }
}

// Sync API implementation
async function syncApi() {
    try {
        const response = await fetch('/sync', {
            method: 'POST',
        });
        
        return await response.json();
    } catch (err) {
        console.error('Failed to sync:', err);
        return { success: false, error: 'Failed to sync' };
    }
}

// Make functions available globally
window.loadResources = loadResources;
window.loadConfig = loadConfig;
window.loadResource = loadResource;
window.deleteResource = deleteResource;
window.saveConfig = saveConfig;
window.generateApi = generateApi;
window.syncApi = syncApi;

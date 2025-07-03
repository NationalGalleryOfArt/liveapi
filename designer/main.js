const { useState, useEffect } = React;

// All components and utilities are available globally
// through script tags in index.html

// Default API template
const defaultApiInfo = {
    "api_name": "Items API",
    "api_description": "API for managing items",
    "x-resource-type": "SQLModelResource", // Options: DefaultResource, SQLModelResource
    "objects": [
        {
            "name": "items",
            "description": "Items in the system",
            "fields": {
                "id": "integer",
                "name": "string",
                "description": "string",
                "active": "boolean"
            },
            "example": {
                "id": 1,
                "name": "Widget A",
                "description": "A standard widget",
                "active": true
            }
        }
    ]
};

// Global editor instance
let editor = null;

function App() {
    // State variables
    const [jsonContent, setJsonContent] = useState(null);
    const [isNewApiModalOpen, setIsNewApiModalOpen] = useState(true);
    const [copyStatus, setCopyStatus] = useState('');
    const [generateStatus, setGenerateStatus] = useState('');
    const [syncStatus, setSyncStatus] = useState('');
    const [previewKey, setPreviewKey] = useState(Date.now());
    const [resources, setResources] = useState([]);
    const [selectedResource, setSelectedResource] = useState(null);
    const [projectConfig, setProjectConfig] = useState({ project_name: '', api_base_url: '' });

    // Initialize Monaco editor
    useEffect(() => {
        configureMonaco();
        
        if (!editor) {
            editor = createEditor('monaco-editor', jsonContent ? JSON.stringify(jsonContent, null, 2) : '', (parsed) => {
                setJsonContent(parsed);
            });
        }

        return () => {
            if (editor) {
                editor.dispose();
                editor = null;
            }
        };
    }, []);

    // Update editor content when jsonContent changes
    useEffect(() => {
        if (editor && jsonContent) {
            const currentValue = editor.getValue();
            const newValue = JSON.stringify(jsonContent, null, 2);
            if (currentValue !== newValue) {
                editor.setValue(newValue);
            }
        } else if (editor && !jsonContent) {
            editor.setValue('');
        }
    }, [jsonContent]);

    // Load resources and config on initial load
    useEffect(() => {
        const initializeApp = async () => {
            const resourcesData = await loadResources();
            setResources(resourcesData);
            
            const configData = await loadConfig();
            setProjectConfig(configData);
            
            // Check for OpenAPI preview
            fetch('/api/openapi.json')
                .then(response => {
                    if (response.ok) {
                        setPreviewKey(Date.now());
                    }
                })
                .catch(() => {});
                
            // Force open the modal after a short delay to ensure component is fully rendered
            setTimeout(() => {
                console.log('Forcing modal open on initial load');
                setIsNewApiModalOpen(true);
                
                // Check resources after another short delay
                setTimeout(() => {
                    console.log('Checking resources after delay:', resourcesData);
                    if (resourcesData.length > 0) {
                        console.log('Resources found after delay, closing modal');
                        setIsNewApiModalOpen(false);
                    } else {
                        console.log('No resources found after delay, keeping modal open');
                    }
                }, 500);
            }, 500);
        };
        
        initializeApp();
    }, []);

    // Handle modal visibility based on resources
    useEffect(() => {
        console.log('Resources changed:', resources);
        if (resources.length === 0) {
            console.log('No resources found, opening modal');
            setIsNewApiModalOpen(true);
        } else {
            console.log('Resources found, closing modal');
            setIsNewApiModalOpen(false);
        }
    }, [resources]);

    // Handler functions
    const handleNewApiClick = () => {
        setIsNewApiModalOpen(true);
    };

    const handleNewApiSubmit = async (formData) => {
        console.log('Creating new API with form data:', formData);
        
        // Create a new API info object with the user's input
        const newApiInfo = {
            api_name: `${formData.objectName} API`,
            api_description: `API for managing ${formData.objectName.toLowerCase()}`,
            "x-resource-type": "SQLModelResource",
            objects: [
                {
                    name: formData.objectName.toLowerCase(),
                    description: formData.objectDescription || `${formData.objectName} in the system`,
                    fields: {
                        id: "integer",
                        name: "string",
                        description: "string",
                        active: "boolean"
                    },
                    example: {
                        id: 1,
                        name: `Sample ${formData.objectName}`,
                        description: `A sample ${formData.objectName.toLowerCase()}`,
                        active: true
                    }
                }
            ]
        };
        
        console.log('New API info:', newApiInfo);

        setSelectedResource(null);
        setJsonContent(newApiInfo);
        if (editor) {
            editor.setValue(JSON.stringify(newApiInfo, null, 2));
        }
        setIsNewApiModalOpen(false);
        // Automatically generate the new API
        await handleGenerate();
    };

    const handleResourceSelect = async (resourceName) => {
        if (!resourceName) {
            handleNewApiClick();
            return;
        }

        const resourceData = await loadResource(resourceName);
        if (resourceData) {
            setJsonContent(resourceData);
            setSelectedResource(resourceName);
        }
    };

    const handleResourceDelete = async (resourceName) => {
        if (!confirm(`Delete resource "${resourceName}"?`)) {
            return;
        }

        const success = await deleteResource(resourceName);
        if (success) {
            const resourcesData = await loadResources();
            setResources(resourcesData);
            
            if (selectedResource === resourceName) {
                setSelectedResource(null);
                setJsonContent(null); // Clear the editor
            }
        }
    };

    const handleConfigSave = async (config) => {
        const success = await saveConfig(config);
        if (success) {
            setProjectConfig(config);
            return true;
        }
        return false;
    };

    const handleGenerate = async () => {
        setGenerateStatus('Generating...');
        
        const result = await generateApi(jsonContent);
        
        if (result.success) {
            setGenerateStatus('Generated!');
            const resourcesData = await loadResources();
            setResources(resourcesData);
            
            // Always select the newly created/updated resource
            if (result.resource_name) {
                setSelectedResource(result.resource_name);
            }
            
            let retries = 0;
            const maxRetries = 10;
            const checkAndRefresh = async () => {
                try {
                    const checkResponse = await fetch('/api/openapi.json');
                    if (checkResponse.ok) {
                        setPreviewKey(Date.now());
                        setGenerateStatus('');
                    } else {
                        retries++;
                        if (retries < maxRetries) {
                            setTimeout(checkAndRefresh, 200);
                        } else {
                            setPreviewKey(Date.now());
                            setGenerateStatus('');
                        }
                    }
                } catch (err) {
                    retries++;
                    if (retries < maxRetries) {
                        setTimeout(checkAndRefresh, 200);
                    } else {
                        setPreviewKey(Date.now());
                        setGenerateStatus('');
                    }
                }
            };
            
            checkAndRefresh();
        } else {
            setGenerateStatus('Error: ' + result.error);
            setTimeout(() => setGenerateStatus(''), 3000);
        }
    };
    
    const handleSync = async () => {
        setSyncStatus('Syncing...');
        
        const result = await syncApi();
        
        if (result.success) {
            setSyncStatus('Synced!');
            alert('API implementation generated successfully!\n\nYou can now run `liveapi run` to test out the API server implementation.');
            setTimeout(() => setSyncStatus(''), 2000);
        } else {
            setSyncStatus('Error: ' + result.error);
            setTimeout(() => setSyncStatus(''), 3000);
        }
    };

    return (
        <>
        <div className="h-screen flex flex-col bg-gray-50">
            <Header 
                projectConfig={projectConfig} 
                onSaveConfig={handleConfigSave} 
            />

            <div className="flex-1 flex overflow-hidden">
                <ResourceList 
                    resources={resources} 
                    selectedResource={selectedResource} 
                    onResourceSelect={handleResourceSelect} 
                    onResourceDelete={handleResourceDelete} 
                />

                <Editor 
                    jsonContent={jsonContent} 
                    onGenerate={handleGenerate} 
                    onSync={handleSync} 
                    generateStatus={generateStatus} 
                    syncStatus={syncStatus} 
                />

                <Preview previewKey={previewKey} />
            </div>
        </div>
        <NewApiModal
            isOpen={isNewApiModalOpen}
            onClose={() => setIsNewApiModalOpen(false)}
            onSubmit={handleNewApiSubmit}
        />
        </>
    );
}

// Initialize the application
ReactDOM.render(<App />, document.getElementById('root'));

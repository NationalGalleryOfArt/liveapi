const { useState } = React;

function Header({ projectConfig, onSaveConfig }) {
    const [editingConfig, setEditingConfig] = useState(false);
    const [tempConfig, setTempConfig] = useState({ ...projectConfig });

    const handleConfigSave = async () => {
        const success = await onSaveConfig(tempConfig);
        if (success) {
            setEditingConfig(false);
        }
    };

    return (
        <header className="bg-white shadow-sm border-b">
            <div className="px-4 py-3">
                <div className="flex items-center justify-between mb-2">
                    <h1 className="text-2xl font-bold text-gray-800">LiveAPI Designer</h1>
                    <div className="flex items-center gap-4">
                        {editingConfig ? (
                            <div className="flex items-center gap-2">
                                <input
                                    type="text"
                                    value={tempConfig.project_name}
                                    onChange={(e) => setTempConfig({...tempConfig, project_name: e.target.value})}
                                    className="px-2 py-1 border rounded"
                                    placeholder="Project name"
                                />
                                <input
                                    type="text"
                                    value={tempConfig.api_base_url}
                                    onChange={(e) => setTempConfig({...tempConfig, api_base_url: e.target.value})}
                                    className="px-2 py-1 border rounded"
                                    placeholder="API base URL"
                                />
                                <button
                                    onClick={handleConfigSave}
                                    className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
                                >
                                    Save
                                </button>
                                <button
                                    onClick={() => {
                                        setEditingConfig(false);
                                        setTempConfig({ ...projectConfig });
                                    }}
                                    className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700"
                                >
                                    Cancel
                                </button>
                            </div>
                        ) : (
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                <span className="font-semibold">{projectConfig.project_name || 'Unnamed Project'}</span>
                                {projectConfig.api_base_url && (
                                    <span className="text-gray-500">• {projectConfig.api_base_url}</span>
                                )}
                                <button
                                    onClick={() => setEditingConfig(true)}
                                    className="px-2 py-1 text-blue-600 hover:bg-blue-50 rounded"
                                >
                                    Edit
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}

// Make component available globally
window.Header = Header;

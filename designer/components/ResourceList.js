function ResourceList({ resources, selectedResource, onResourceSelect, onResourceDelete }) {
    return (
        <div className="w-1/4 flex flex-col border-r bg-white">
            <div className="p-4 border-b flex items-center justify-between bg-[#1b1b1b]">
                <h2 className="text-lg font-semibold text-white">API Resources</h2>
                <button
                    onClick={() => onResourceSelect(null)}
                    className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                >
                    New API
                </button>
            </div>
            <div className="flex-1 overflow-y-auto">
                {resources.map(resource => (
                    <div 
                        key={resource.name} 
                        className={`p-3 cursor-pointer border-b ${selectedResource === resource.name ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
                        onClick={() => onResourceSelect(resource.name)}
                    >
                        <div className="flex justify-between items-center">
                            <span className="font-semibold">{resource.api_name}</span>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onResourceDelete(resource.name);
                                }}
                                className="text-red-500 hover:text-red-700"
                            >
                                Delete
                            </button>
                        </div>
                        <p className="text-sm text-gray-600">{resource.name}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}

// Make component available globally
window.ResourceList = ResourceList;

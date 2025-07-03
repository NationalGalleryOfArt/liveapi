function Editor({ jsonContent, onGenerate, onSync, generateStatus, syncStatus }) {
    return (
        <div className="w-1/2 flex flex-col border-r">
            <div className="p-4 bg-[#1b1b1b] border-b flex items-center justify-between">
                <h2 className="text-xl font-semibold text-white">API Design JSON</h2>
                <div className="flex items-center gap-2">
                    <button
                        onClick={onGenerate}
                        className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                    >
                        {generateStatus || 'Save API'}
                    </button>
                    <button
                        onClick={onSync}
                        className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                    >
                        {syncStatus || 'Autogenerate APIs'}
                    </button>
                </div>
            </div>
            <div className="flex-1" id="monaco-editor"></div>
        </div>
    );
}

// Make component available globally
window.Editor = Editor;

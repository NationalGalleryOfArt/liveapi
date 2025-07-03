// Monaco Editor Configuration
function configureMonaco() {
    require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.40.0/min/vs' } });
    window.MonacoEnvironment = {
        getWorkerUrl: function(workerId, label) {
            return `data:text/javascript;charset=utf-8,${encodeURIComponent(`
                self.MonacoEnvironment = {
                    baseUrl: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.40.0/min/'
                };
                importScripts('https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.40.0/min/vs/base/worker/workerMain.js');`
            )}`;
        }
    };
}

// Create and initialize Monaco editor
function createEditor(containerId, initialValue, onChange) {
    let editor = null;
    
    require(['vs/editor/editor.main'], function() {
        editor = monaco.editor.create(document.getElementById(containerId), {
            value: initialValue || '',
            language: 'json',
            theme: 'vs-dark',
            automaticLayout: true,
            minimap: { enabled: false },
            fontSize: 14,
            scrollBeyondLastLine: false
        });

        if (onChange) {
            editor.onDidChangeModelContent(() => {
                try {
                    const value = editor.getValue();
                    const parsed = JSON.parse(value);
                    onChange(parsed);
                } catch (e) {
                    // Invalid JSON, ignore
                }
            });
        }
    });
    
    return editor;
}

// Make functions available globally
window.configureMonaco = configureMonaco;
window.createEditor = createEditor;

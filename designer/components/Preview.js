function Preview({ previewKey }) {
    return (
        <div className="w-1/2 flex flex-col">
            <div className="flex-1 bg-gray-100">
                <iframe
                    key={previewKey}
                    src={`preview.html?t=${previewKey}`}
                    className="w-full h-full"
                    title="OpenAPI Preview"
                />
            </div>
        </div>
    );
}

// Make component available globally
window.Preview = Preview;

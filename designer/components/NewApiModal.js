const { useState } = React;
// Using the Modal component from the global scope
// (imported via script tag in index.html)

function NewApiModal({ isOpen, onClose, onSubmit }) {
    const [newApiForm, setNewApiForm] = useState({
        objectName: '',
        objectDescription: ''
    });

    const handleSubmit = () => {
        onSubmit(newApiForm);
        setNewApiForm({
            objectName: '',
            objectDescription: ''
        });
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Create New API"
        >
            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Object Name
                    </label>
                    <input
                        type="text"
                        value={newApiForm.objectName}
                        onChange={(e) => setNewApiForm({
                            ...newApiForm,
                            objectName: e.target.value
                        })}
                        placeholder="e.g., Product, User, Order"
                        className="w-full px-3 py-2 border rounded-md"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Object Description
                    </label>
                    <input
                        type="text"
                        value={newApiForm.objectDescription}
                        onChange={(e) => setNewApiForm({
                            ...newApiForm,
                            objectDescription: e.target.value
                        })}
                        placeholder="e.g., Products in the inventory"
                        className="w-full px-3 py-2 border rounded-md"
                    />
                </div>
                <div className="flex justify-end gap-2 mt-6">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-gray-600 hover:text-gray-800"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSubmit}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                        disabled={!newApiForm.objectName.trim()}
                    >
                        Create
                    </button>
                </div>
            </div>
        </Modal>
    );
}

// Make component available globally
window.NewApiModal = NewApiModal;

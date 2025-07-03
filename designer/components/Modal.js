const { useState, useEffect } = React;

function Modal({ isOpen, onClose, onSubmit, title, children }) {
    console.log('Modal render, isOpen:', isOpen);
    if (!isOpen) return null;
    
    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-96">
                <h3 className="text-lg font-semibold mb-4">{title}</h3>
                {children}
            </div>
        </div>
    );
}

// Make component available globally
window.Modal = Modal;

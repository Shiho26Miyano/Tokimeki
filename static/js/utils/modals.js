/**
 * Modal Management Utilities
 */

class ModalManager {
    constructor() {
        this.activeModals = new Map();
        this.init();
    }

    init() {
        this.setupHoverModals();
    }

    setupHoverModals() {
        // Handle hover-triggered modals for "How it works" buttons
        const howItWorksButtons = document.querySelectorAll('.how-it-works-btn');
        
        howItWorksButtons.forEach(button => {
            let modal = null;
            let timeoutId = null;
            
            button.addEventListener('mouseenter', () => {
                const targetId = button.getAttribute('data-bs-target');
                modal = new bootstrap.Modal(document.querySelector(targetId));
                modal.show();
            });
            
            button.addEventListener('mouseleave', () => {
                if (timeoutId) {
                    clearTimeout(timeoutId);
                }
                timeoutId = setTimeout(() => {
                    if (modal) {
                        modal.hide();
                    }
                }, 300); // Small delay to prevent immediate closing
            });
            
            // Also close modal when mouse leaves the modal itself
            const targetId = button.getAttribute('data-bs-target');
            const modalElement = document.querySelector(targetId);
            if (modalElement) {
                modalElement.addEventListener('mouseenter', () => {
                    if (timeoutId) {
                        clearTimeout(timeoutId);
                    }
                });
                
                modalElement.addEventListener('mouseleave', () => {
                    if (modal) {
                        modal.hide();
                    }
                });
            }
        });
    }

    showModal(modalId) {
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            this.activeModals.set(modalId, modal);
        }
    }

    hideModal(modalId) {
        const modal = this.activeModals.get(modalId);
        if (modal) {
            modal.hide();
            this.activeModals.delete(modalId);
        }
    }

    hideAllModals() {
        this.activeModals.forEach(modal => modal.hide());
        this.activeModals.clear();
    }
}

// Initialize modal manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.modalManager = new ModalManager();
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModalManager;
}

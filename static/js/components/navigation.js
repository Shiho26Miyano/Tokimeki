/**
 * Navigation Component
 */

class NavigationComponent {
    constructor() {
        this.navContainer = null;
        this.init();
    }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }

    initialize() {
        this.navContainer = document.getElementById('left-nav-container');
        if (this.navContainer) {
            this.setupNavigation();
        }
    }

    setupNavigation() {
        // Navigation is handled by TabManager
        console.log('Navigation component initialized');
    }

    // Method to programmatically switch tabs
    switchToTab(tabName) {
        const targetTab = document.querySelector(`[data-bs-target="#${tabName}-content"]`);
        if (targetTab) {
            targetTab.click();
        }
    }

    // Method to get current active tab
    getActiveTab() {
        const activeTab = document.querySelector('.nav-link.active');
        if (activeTab) {
            return activeTab.getAttribute('data-bs-target').replace('#', '').replace('-content', '');
        }
        return null;
    }
}

// Initialize navigation component
window.navigationComponent = new NavigationComponent();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NavigationComponent;
}

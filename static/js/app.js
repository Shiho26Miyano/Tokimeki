/**
 * Main Application Initialization
 */

// Import utilities
import './utils/cache.js';
import './utils/tabs.js';
import './utils/modals.js';
import './utils/loading.js';
import './utils/component-loader.js';

// Import components
import './components/navigation.js';
import './components/futures-exploratorium.js';
import './components/futurequant-dashboard.js';
import './components/minigolf-strategy.js';
import './components/rag-bi.js';
import './components/chatbot.js';
import './components/ai-platform-comparables.js';
import './components/market-overtime.js';
import './components/volatility-explorer.js';
import './components/hf-signal-tool.js';

class TokimekiApp {
    constructor() {
        this.initialized = false;
        this.init();
    }

    init() {
        if (this.initialized) return;
        
        console.log('Initializing Tokimeki App...');
        
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeApp());
        } else {
            this.initializeApp();
        }
    }

    async initializeApp() {
        try {
            // Initialize core utilities
            this.initializeUtilities();
            
            // Initialize components (async)
            await this.initializeComponents();
            
            // Set up global event listeners
            this.setupGlobalEventListeners();
            
            this.initialized = true;
            console.log('Tokimeki App initialized successfully');
        } catch (error) {
            console.error('Error initializing Tokimeki App:', error);
        }
    }

    initializeUtilities() {
        // Utilities are auto-initialized when imported
        console.log('Utilities initialized');
    }

    async initializeComponents() {
        // Load all components dynamically
        if (window.componentLoader) {
            await window.componentLoader.loadAllComponents();
        }
        console.log('Components initialized');
    }

    setupGlobalEventListeners() {
        // Global error handling
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            if (window.loadingManager) {
                window.loadingManager.showError('An unexpected error occurred');
            }
        });

        // Global unhandled promise rejection handling
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            if (window.loadingManager) {
                window.loadingManager.showError('An unexpected error occurred');
            }
        });
    }

    // Public API methods
    getTabManager() {
        return window.tabManager;
    }

    getModalManager() {
        return window.modalManager;
    }

    getLoadingManager() {
        return window.loadingManager;
    }
}

// Initialize the app
window.tokimekiApp = new TokimekiApp();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TokimekiApp;
}

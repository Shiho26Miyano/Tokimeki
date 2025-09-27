/**
 * Tab Management Utilities
 */

class TabManager {
    constructor() {
        this.activeTab = null;
        this.init();
    }

    init() {
        this.setupTabListeners();
        this.handleActiveTabFromStorage();
    }

    setupTabListeners() {
        // Debug Bootstrap tabs
        const tabLinks = document.querySelectorAll('#main-nav .nav-link');
        tabLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                console.log('Tab clicked:', e.target.textContent);
                console.log('Target:', e.target.getAttribute('data-bs-target'));
            });
        });
        
        // Ensure Bootstrap tabs are working
        const tabElements = document.querySelectorAll('[data-bs-toggle="pill"]');
        tabElements.forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                console.log('Tab shown:', e.target.textContent);
                this.activeTab = e.target.getAttribute('data-bs-target').replace('#', '').replace('-content', '');
                this.onTabChange(this.activeTab);
            });
        });
    }

    handleActiveTabFromStorage() {
        // Check if we should activate a specific tab (from monitoring page navigation)
        const activeTab = localStorage.getItem('activeTab');
        if (activeTab) {
            const targetTab = document.querySelector(`[data-bs-target="#${activeTab}-content"]`);
            if (targetTab) {
                // Remove active class from current tab
                const currentActive = document.querySelector('.nav-link.active');
                const currentPane = document.querySelector('.tab-pane.show.active');
                
                if (currentActive) currentActive.classList.remove('active');
                if (currentPane) currentPane.classList.remove('show', 'active');
                
                // Activate the target tab
                targetTab.classList.add('active');
                const targetPane = document.querySelector(`#${activeTab}-content`);
                if (targetPane) {
                    targetPane.classList.add('show', 'active');
                }
                
                // Clear the stored tab
                localStorage.removeItem('activeTab');
            }
        }
    }

    onTabChange(tabName) {
        // Handle tab-specific initialization
        switch(tabName) {
            case 'futures-exploratorium':
                this.initializeFuturesExploratorium();
                break;
            case 'futurequant-dashboard':
                this.initializeFutureQuantDashboard();
                break;
            case 'minigolf-strategy':
                this.initializeMiniGolfStrategy();
                break;
            case 'rag-bi':
                this.initializeRAGBI();
                break;
            case 'deepseek-chatbot':
                this.initializeChatbot();
                break;
            case 'ai-platform-comparables':
                this.initializeAIPlatformComparables();
                break;
            case 'market-overtime':
                this.initializeMarketOvertime();
                break;
            case 'volatility-explorer':
                this.initializeVolatilityExplorer();
                break;
            case 'hf-signal-tool':
                this.initializeHFSignalTool();
                break;
        }
    }

    initializeFuturesExploratorium() {
        // Initialize Futures Exploratorium specific functionality
        console.log('Initializing Futures Exploratorium');
    }

    initializeFutureQuantDashboard() {
        // Initialize FutureQuant Dashboard specific functionality
        console.log('Initializing FutureQuant Dashboard');
    }

    initializeMiniGolfStrategy() {
        // Initialize Mini Golf Strategy specific functionality
        console.log('Initializing Mini Golf Strategy');
    }

    initializeRAGBI() {
        // Initialize RAG BI specific functionality
        console.log('Initializing RAG BI');
    }

    initializeChatbot() {
        // Initialize Chatbot specific functionality
        console.log('Initializing Chatbot');
    }

    initializeAIPlatformComparables() {
        // Initialize AI Platform Comparables specific functionality
        console.log('Initializing AI Platform Comparables');
    }

    initializeMarketOvertime() {
        // Initialize Market Overtime specific functionality
        console.log('Initializing Market Overtime');
    }

    initializeVolatilityExplorer() {
        // Initialize Volatility Explorer specific functionality
        console.log('Initializing Volatility Explorer');
    }

    initializeHFSignalTool() {
        // Initialize HF Signal Tool specific functionality
        console.log('Initializing HF Signal Tool');
    }
}

// Initialize tab manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.tabManager = new TabManager();
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TabManager;
}

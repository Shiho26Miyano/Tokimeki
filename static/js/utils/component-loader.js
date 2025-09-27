/**
 * Component Loader Utility
 * Dynamically loads HTML content for components
 */

class ComponentLoader {
    constructor() {
        this.loadedComponents = new Set();
        this.componentCache = new Map();
    }

    async loadComponent(componentName, containerId) {
        try {
            // Check if component is already loaded
            if (this.loadedComponents.has(componentName)) {
                console.log(`Component ${componentName} already loaded`);
                return;
            }

            // Check cache first
            if (this.componentCache.has(componentName)) {
                this.renderComponent(componentName, containerId);
                return;
            }

            // Load component HTML
            const response = await fetch(`components/${componentName}.html`);
            if (!response.ok) {
                throw new Error(`Failed to load component: ${componentName}`);
            }

            const html = await response.text();
            this.componentCache.set(componentName, html);
            this.renderComponent(componentName, containerId);
            this.loadedComponents.add(componentName);

        } catch (error) {
            console.error(`Error loading component ${componentName}:`, error);
            this.showError(`Failed to load ${componentName} component`);
        }
    }

    renderComponent(componentName, containerId) {
        const container = document.getElementById(containerId);
        if (container && this.componentCache.has(componentName)) {
            container.innerHTML = this.componentCache.get(componentName);
            console.log(`Rendered component ${componentName} in ${containerId}`);
        }
    }

    async loadAllComponents() {
        const components = [
            { name: 'futures-exploratorium', container: 'futures-exploratorium-root' },
            { name: 'futurequant-dashboard', container: 'futurequant-dashboard-root' },
            { name: 'minigolf-strategy', container: 'minigolf-strategy-root' },
            { name: 'rag-bi', container: 'rag-bi-root' },
            { name: 'chatbot', container: 'chatbot-root' },
            { name: 'ai-platform-comparables', container: 'ai-platform-comparables-root' },
            { name: 'market-overtime', container: 'market-overtime-root' },
            { name: 'volatility-explorer', container: 'volatility-explorer-root' },
            { name: 'hf-signal-tool', container: 'hf-signal-tool-root' }
        ];

        for (const component of components) {
            await this.loadComponent(component.name, component.container);
        }
    }

    showError(message) {
        if (window.loadingManager) {
            window.loadingManager.showError(message);
        } else {
            console.error(message);
        }
    }

    // Method to reload a specific component
    async reloadComponent(componentName, containerId) {
        this.loadedComponents.delete(componentName);
        this.componentCache.delete(componentName);
        await this.loadComponent(componentName, containerId);
    }
}

// Initialize component loader
window.componentLoader = new ComponentLoader();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ComponentLoader;
}

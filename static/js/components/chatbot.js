/**
 * Chatbot Component
 */

class ChatbotComponent {
    constructor() {
        this.container = null;
        this.initialized = false;
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
        this.container = document.getElementById('deepseek-chatbot-content');
        if (this.container && !this.initialized) {
            this.setupComponent();
            this.initialized = true;
        }
    }

    setupComponent() {
        console.log('Chatbot component initialized');
    }

    refresh() {
        console.log('Refreshing Chatbot');
    }

    destroy() {
        console.log('Destroying Chatbot');
        this.initialized = false;
    }
}

window.chatbotComponent = new ChatbotComponent();

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatbotComponent;
}

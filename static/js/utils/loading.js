/**
 * Loading Timer Utilities
 */

class LoadingManager {
    constructor() {
        this.loadingTimers = new Map();
    }

    startLoadingTimer(elementId, operationType = 'operation') {
        const progressBar = document.getElementById(elementId.replace('Loading', 'Progress'));
        const timerElement = document.getElementById(elementId.replace('Loading', 'Timer'));
        const loadingText = document.getElementById(elementId.replace('Loading', 'Text'));
        
        // Clear any existing timer
        this.stopLoadingTimer(elementId);
        
        // Reset progress bar
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.classList.add('progress-bar-animated');
        }
        
        // Reset timer text
        if (timerElement) {
            timerElement.textContent = 'Starting...';
        }
        
        let seconds = 0;
        const timerInterval = setInterval(() => {
            seconds++;
            
            // Update progress bar (simulate progress)
            if (progressBar) {
                const progress = Math.min((seconds / 30) * 100, 95); // Max 95% until complete
                progressBar.style.width = `${progress}%`;
            }
            
            // Update timer text
            if (timerElement) {
                timerElement.textContent = `${seconds}s`;
            }
            
            // Update loading text based on operation and time
            if (loadingText) {
                if (seconds < 2) {
                    loadingText.textContent = `Starting ${operationType}...`;
                } else if (seconds < 5) {
                    loadingText.textContent = `Processing ${operationType}...`;
                } else if (seconds < 15) {
                    loadingText.textContent = `Finalizing ${operationType}...`;
                } else {
                    loadingText.textContent = `Complex analysis in progress...`;
                }
            }
        }, 100);
        
        // Store timer for cleanup
        this.loadingTimers.set(elementId, timerInterval);
        
        return timerInterval;
    }

    stopLoadingTimer(elementId) {
        const progressBar = document.getElementById(elementId.replace('Loading', 'Progress'));
        const timerElement = document.getElementById(elementId.replace('Loading', 'Timer'));
        
        // Clear interval
        if (this.loadingTimers.has(elementId)) {
            clearInterval(this.loadingTimers.get(elementId));
            this.loadingTimers.delete(elementId);
        }
        
        // Complete progress bar
        if (progressBar) {
            progressBar.style.width = '100%';
            progressBar.classList.remove('progress-bar-animated');
        }
        
        // Update timer text
        if (timerElement) {
            timerElement.textContent = 'Complete!';
        }
    }

    resetLoadingTimer(elementId) {
        const progressBar = document.getElementById(elementId.replace('Loading', 'Progress'));
        const timerElement = document.getElementById(elementId.replace('Loading', 'Timer'));
        
        // Clear any existing timer
        this.stopLoadingTimer(elementId);
        
        // Reset progress bar
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.classList.add('progress-bar-animated');
        }
        
        // Reset timer text
        if (timerElement) {
            timerElement.textContent = 'Starting...';
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => errorDiv.style.display = 'none', 5000);
        }
    }

    showSuccess(message) {
        const successDiv = document.getElementById('successMessage');
        if (successDiv) {
            successDiv.textContent = message;
            successDiv.style.display = 'block';
            setTimeout(() => successDiv.style.display = 'none', 3000);
        }
    }

    hideMessages() {
        const errorDiv = document.getElementById('errorMessage');
        const successDiv = document.getElementById('successMessage');
        if (errorDiv) errorDiv.style.display = 'none';
        if (successDiv) successDiv.style.display = 'none';
    }

    scrollToElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    }
}

// Initialize loading manager
window.loadingManager = new LoadingManager();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingManager;
}

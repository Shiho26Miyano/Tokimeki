/**
 * Cache Management Utilities
 */

// Auto-clear cache and force reload
function forceReload() {
    // Clear browser cache
    if ('caches' in window) {
        caches.keys().then(function(names) {
            for (let name of names) {
                caches.delete(name);
            }
        });
    }
    
    // Force reload without cache
    window.location.reload(true);
}

// Auto-clear cache on page load
function clearCacheOnLoad() {
    // Clear any stored cache
    if ('localStorage' in window) {
        localStorage.clear();
    }
    if ('sessionStorage' in window) {
        sessionStorage.clear();
    }
}

// Initialize cache management
window.addEventListener('load', clearCacheOnLoad);

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { forceReload, clearCacheOnLoad };
}

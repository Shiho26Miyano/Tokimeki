/**
 * LSW Game Logic - Sliding Window Algorithm
 * Implements the Longest Substring Without Repeating Characters algorithm
 */

class LSWGameLogic {
    constructor(inputString) {
        this.inputString = inputString || '';
        this.reset();
    }

    reset() {
        this.L = 0; // Left pointer
        this.R = 0; // Right pointer
        this.maxLen = 0;
        this.lastSeen = {}; // Map of character to last seen index
        this.currentStep = 0;
        this.isComplete = false;
        this.history = []; // Store state at each step
        this.duplicateDetected = false;
        this.duplicateChar = null;
    }

    /**
     * Get the current state snapshot
     */
    getState() {
        return {
            L: this.L,
            R: this.R,
            maxLen: this.maxLen,
            currentStep: this.currentStep,
            isComplete: this.isComplete,
            substring: this.inputString.substring(this.L, this.R + 1),
            lastSeen: { ...this.lastSeen },
            duplicateDetected: this.duplicateDetected,
            duplicateChar: this.duplicateChar
        };
    }

    /**
     * Execute one step of the algorithm
     * Returns true if step was executed, false if already complete
     */
    step() {
        if (this.isComplete) {
            return false;
        }

        this.duplicateDetected = false;
        this.duplicateChar = null;

        if (this.R >= this.inputString.length) {
            this.isComplete = true;
            return false;
        }

        const currentChar = this.inputString[this.R];

        // Check for duplicate
        if (this.lastSeen[currentChar] !== undefined && this.lastSeen[currentChar] >= this.L) {
            // Duplicate found within current window
            this.duplicateDetected = true;
            this.duplicateChar = currentChar;
            this.L = this.lastSeen[currentChar] + 1;
        }

        // Update last seen position
        this.lastSeen[currentChar] = this.R;

        // Update max length
        const currentLen = this.R - this.L + 1;
        this.maxLen = Math.max(this.maxLen, currentLen);

        // Save state to history
        this.history.push(this.getState());

        // Move right pointer
        this.R++;
        this.currentStep++;

        // Check if complete
        if (this.R >= this.inputString.length) {
            this.isComplete = true;
        }

        return true;
    }

    /**
     * Execute all steps at once (for testing)
     */
    runAll() {
        while (this.step()) {
            // Continue until complete
        }
        return this.maxLen;
    }

    /**
     * Set new input string and reset
     */
    setInput(newInput) {
        this.inputString = newInput || '';
        this.reset();
    }

    /**
     * Get character at index with bounds checking
     */
    getCharAt(index) {
        if (index < 0 || index >= this.inputString.length) {
            return null;
        }
        return this.inputString[index];
    }

    /**
     * Check if index is within current window [L, R]
     */
    isInWindow(index) {
        return index >= this.L && index <= this.R;
    }

    /**
     * Check if character at index is a duplicate
     */
    isDuplicate(index) {
        if (index < 0 || index >= this.inputString.length) {
            return false;
        }
        const char = this.inputString[index];
        return this.lastSeen[char] !== undefined && 
               this.lastSeen[char] < index && 
               this.lastSeen[char] >= this.L;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LSWGameLogic;
}


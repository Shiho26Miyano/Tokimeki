/**
 * LSW Game Page - Longest Substring Without Repeating Characters
 * Interactive educational page demonstrating the Sliding Window algorithm
 */

(function() {
    'use strict';
    
    function defineComponent() {
        if (typeof React === 'undefined' || typeof React.Component === 'undefined') {
            console.log('React not available yet for LSWGamePage, retrying in 100ms...');
            setTimeout(defineComponent, 100);
            return;
        }
        
        console.log('React available, defining LSWGamePage component...');

        const { useState, useEffect, useRef, useCallback } = React;

        // Import or define LSWGameLogic inline
        class LSWGameLogic {
            constructor(inputString) {
                this.inputString = inputString || '';
                this.reset();
            }

            reset() {
                this.L = 0;
                this.R = 0;
                this.maxLen = 0;
                this.lastSeen = {};
                this.currentStep = 0;
                this.isComplete = false;
                this.history = [];
                this.duplicateDetected = false;
                this.duplicateChar = null;
            }

            getState() {
                // R points to the next character to process, so current window is [L, R)
                // But for display, we want to show up to the last processed character
                const endIdx = Math.min(this.R, this.inputString.length);
                return {
                    L: this.L,
                    R: this.R,
                    maxLen: this.maxLen,
                    currentStep: this.currentStep,
                    isComplete: this.isComplete,
                    substring: this.inputString.substring(this.L, endIdx),
                    lastSeen: { ...this.lastSeen },
                    duplicateDetected: this.duplicateDetected,
                    duplicateChar: this.duplicateChar
                };
            }

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

                if (this.lastSeen[currentChar] !== undefined && this.lastSeen[currentChar] >= this.L) {
                    this.duplicateDetected = true;
                    this.duplicateChar = currentChar;
                    this.L = this.lastSeen[currentChar] + 1;
                }

                this.lastSeen[currentChar] = this.R;
                const currentLen = this.R - this.L + 1;
                this.maxLen = Math.max(this.maxLen, currentLen);

                this.history.push(this.getState());
                this.R++;
                this.currentStep++;

                if (this.R >= this.inputString.length) {
                    this.isComplete = true;
                }

                return true;
            }

            setInput(newInput) {
                this.inputString = newInput || '';
                this.reset();
            }
        }

        function LSWGamePage() {
            const [inputString, setInputString] = useState('abcabcbb');
            const gameLogicRef = useRef(new LSWGameLogic('abcabcbb'));
            const [currentState, setCurrentState] = useState(() => gameLogicRef.current.getState());
            const [isAutoPlaying, setIsAutoPlaying] = useState(false);
            const [message, setMessage] = useState('Click "Next Step" to start!');
            const [updateTrigger, setUpdateTrigger] = useState(0);
            const autoPlayIntervalRef = useRef(null);

            // Apply new string
            const handleApplyString = () => {
                gameLogicRef.current = new LSWGameLogic(inputString);
                setCurrentState(gameLogicRef.current.getState());
                setIsAutoPlaying(false);
                setUpdateTrigger(prev => prev + 1);
                setMessage('String loaded. Click "Next Step" to begin!');
            };

            // Reset game
            const handleReset = () => {
                gameLogicRef.current = new LSWGameLogic(inputString);
                setCurrentState(gameLogicRef.current.getState());
                setIsAutoPlaying(false);
                setUpdateTrigger(prev => prev + 1);
                setMessage('Game reset. Click "Next Step" to start!');
            };

            // Next step
            const handleNextStep = useCallback(() => {
                if (gameLogicRef.current.isComplete) {
                    setMessage(`Algorithm complete! Maximum length: ${gameLogicRef.current.maxLen}`);
                    return;
                }

                const stepped = gameLogicRef.current.step();
                if (stepped) {
                    const newState = gameLogicRef.current.getState();
                    setCurrentState(newState);
                    setUpdateTrigger(prev => prev + 1);
                    
                    if (newState.duplicateDetected) {
                        setMessage(`Duplicate detected: '${newState.duplicateChar}' at index ${newState.R - 1}. Moving L to ${newState.L}.`);
                    } else {
                        setMessage(`Processing character '${inputString[newState.R - 1]}' at index ${newState.R - 1}. Current window length: ${newState.R - newState.L}.`);
                    }
                } else {
                    setMessage(`Algorithm complete! Maximum length: ${gameLogicRef.current.maxLen}`);
                    setUpdateTrigger(prev => prev + 1);
                }
            }, [inputString]);

            // Toggle auto play
            const handleToggleAutoPlay = () => {
                if (isAutoPlaying) {
                    setIsAutoPlaying(false);
                    if (autoPlayIntervalRef.current) {
                        clearInterval(autoPlayIntervalRef.current);
                        autoPlayIntervalRef.current = null;
                    }
                    setMessage('Auto Play stopped.');
                } else {
                    if (gameLogicRef.current.isComplete) {
                        handleReset();
                    }
                    setIsAutoPlaying(true);
                    setMessage('Auto Play started...');
                }
            };

            // Auto play effect
            useEffect(() => {
                if (!isAutoPlaying) {
                    if (autoPlayIntervalRef.current) {
                        clearInterval(autoPlayIntervalRef.current);
                        autoPlayIntervalRef.current = null;
                    }
                    return;
                }

                if (gameLogicRef.current.isComplete) {
                    setIsAutoPlaying(false);
                    setMessage(`Algorithm complete! Maximum length: ${gameLogicRef.current.maxLen}`);
                    return;
                }

                autoPlayIntervalRef.current = setInterval(() => {
                    if (gameLogicRef.current.isComplete) {
                        setIsAutoPlaying(false);
                        setMessage(`Algorithm complete! Maximum length: ${gameLogicRef.current.maxLen}`);
                        return;
                    }
                    
                    const stepped = gameLogicRef.current.step();
                    if (stepped) {
                        const newState = gameLogicRef.current.getState();
                        setCurrentState(newState);
                        setUpdateTrigger(prev => prev + 1);
                        
                        if (newState.duplicateDetected) {
                            setMessage(`Duplicate detected: '${newState.duplicateChar}' at index ${newState.R - 1}. Moving L to ${newState.L}.`);
                        } else {
                            setMessage(`Processing character '${inputString[newState.R - 1]}' at index ${newState.R - 1}. Current window length: ${newState.R - newState.L}.`);
                        }
                    } else {
                        setIsAutoPlaying(false);
                        setMessage(`Algorithm complete! Maximum length: ${gameLogicRef.current.maxLen}`);
                        setUpdateTrigger(prev => prev + 1);
                    }
                }, 500);

                return () => {
                    if (autoPlayIntervalRef.current) {
                        clearInterval(autoPlayIntervalRef.current);
                        autoPlayIntervalRef.current = null;
                    }
                };
            }, [isAutoPlaying, speed, inputString]);

            // Render character cells
            const renderCharCells = () => {
                return inputString.split('').map((char, index) => {
                    // R points to next character to process, so window is [L, R)
                    const isInWindow = index >= currentState.L && index < currentState.R;
                    const isLeftPointer = index === currentState.L;
                    const isRightPointer = index === currentState.R - 1;
                    const isDuplicate = currentState.duplicateDetected && 
                                       index === currentState.R - 1 && 
                                       currentState.duplicateChar === char;

                    let cellClass = 'lsw-char-cell';
                    if (isDuplicate) {
                        cellClass += ' is-duplicate';
                    } else if (isLeftPointer) {
                        cellClass += ' is-left-pointer';
                    } else if (isRightPointer) {
                        cellClass += ' is-right-pointer';
                    } else if (isInWindow) {
                        cellClass += ' in-window';
                    }

                    return (
                        <div key={index} className={cellClass}>
                            <span>{char}</span>
                            <div className="index-label">{index}</div>
                        </div>
                    );
                });
            };

            return (
                <div className="lsw-game-container">
                    <div className="lsw-game-header">
                        <h1>Longest Substring Without Repeating Characters</h1>
                        <p>Interactive sliding window algorithm visualization</p>
                    </div>

                    <div className="lsw-main-board">
                        {/* Input Section */}
                        <div className="lsw-input-section">
                            <input
                                type="text"
                                className="lsw-input-field"
                                value={inputString}
                                onChange={(e) => setInputString(e.target.value)}
                                placeholder="Enter string (e.g., abcabcbb)"
                            />
                            <button className="lsw-apply-btn" onClick={handleApplyString}>
                                Apply
                            </button>
                        </div>

                        {/* Status Section */}
                        <div className="lsw-status-section">
                            <div className="lsw-status-card left-pointer">
                                <div className="lsw-status-label">Left Pointer</div>
                                <div className="lsw-status-value">{currentState.L}</div>
                            </div>
                            <div className="lsw-status-card right-pointer">
                                <div className="lsw-status-label">Right Pointer</div>
                                <div className="lsw-status-value">{currentState.R}</div>
                            </div>
                            <div className="lsw-status-card max-length">
                                <div className="lsw-status-label">Max Length</div>
                                <div className="lsw-status-value max-length">{currentState.maxLen}</div>
                            </div>
                        </div>

                        {/* Visualization */}
                        <div className="lsw-visualization">
                            <div className="lsw-string-display">
                                {renderCharCells()}
                            </div>
                            <div className="lsw-window-container">
                                <div className="lsw-window-content">
                                    {currentState.substring || '—'}
                                </div>
                            </div>
                        </div>

                        {/* Message Box */}
                        <div className={`lsw-message-box ${currentState.isComplete ? 'success' : 'info'}`}>
                            <p className="lsw-message-text">{message}</p>
                        </div>

                        {/* Controls */}
                        <div className="lsw-controls">
                            <div className="lsw-controls-row">
                                <button 
                                    className="lsw-btn primary" 
                                    onClick={handleNextStep}
                                    disabled={gameLogicRef.current.isComplete}
                                >
                                    Next Step
                                </button>
                                <button 
                                    className={`lsw-btn ${isAutoPlaying ? 'auto-play-active' : ''}`}
                                    onClick={handleToggleAutoPlay}
                                >
                                    {isAutoPlaying ? '⏸ Stop Auto Play' : '▶ Auto Play'}
                                </button>
                                <button className="lsw-btn" onClick={handleReset}>
                                    Reset
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        // Make component globally available
        window.LSWGamePage = LSWGamePage;
        console.log('✅ LSWGamePage component defined');
    }

    // Start trying to define the component
    defineComponent();
})();


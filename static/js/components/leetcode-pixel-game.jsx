/**
 * Algorithm Pixel Game
 * Interactive pixel-style mini game for learning algorithms
 */

(function() {
    'use strict';
    
    function defineComponent() {
        if (typeof React === 'undefined' || typeof React.Component === 'undefined') {
            console.log('React not available yet for AlgorithmPixelGame, retrying in 100ms...');
            setTimeout(defineComponent, 100);
            return;
        }
        
        console.log('React available, defining AlgorithmPixelGame component...');
        
        const { useState, useEffect, useRef, useCallback } = React;
        
        // Pixel art style constants
        const PIXEL_SIZE = 40;
        const COLORS = {
            primary: '#4A90E2',
            secondary: '#7B68EE',
            success: '#50C878',
            danger: '#FF6B6B',
            warning: '#FFD93D',
            background: '#2C3E50',
            grid: '#34495E',
            text: '#ECF0F1'
        };
        
        // Algorithm problems database - 3 medium problems demonstrating different data structures
        const PROBLEMS = [
            {
                id: 'valid-parentheses',
                title: 'Valid Parentheses',
                difficulty: 'Medium',
                description: 'Use a Stack to match parentheses!',
                problem: 'Given a string s containing just the characters \'(\', \')\', \'{\', \'}\', \'[\' and \']\', determine if the input string is valid.',
                example: {
                    input: '()[]{}',
                    solution: true
                },
                visualType: 'stack',
                dataStructure: 'Stack',
                template: `function isValid(s) {
    // TODO: Implement stack-based solution
    // Hint: Use a stack to track opening brackets
    // When you see a closing bracket, check if it matches the top of stack
    
    const stack = [];
    
    for (let char of s) {
        // Your code here
        
    }
    
    return stack.length === 0;
}`,
                solution: `function isValid(s) {
    const stack = [];
    const pairs = {
        ')': '(',
        ']': '[',
        '}': '{'
    };
    
    for (let char of s) {
        if (pairs[char]) {
            // Closing bracket
            if (stack.length === 0 || stack.pop() !== pairs[char]) {
                return false;
            }
        } else {
            // Opening bracket
            stack.push(char);
        }
    }
    
    return stack.length === 0;
}`,
                hints: [
                    'Use a stack to store opening brackets',
                    'When you see a closing bracket, check if it matches the top of the stack',
                    'If it matches, pop from stack. If not, return false',
                    'At the end, the stack should be empty for valid parentheses'
                ],
                testCases: [
                    { input: '()', expected: true },
                    { input: '()[]{}', expected: true },
                    { input: '(]', expected: false },
                    { input: '([)]', expected: false },
                    { input: '{[]}', expected: true }
                ]
            },
            {
                id: 'three-sum',
                title: '3Sum',
                difficulty: 'Medium',
                description: 'Use Two Pointers to find triplets!',
                problem: 'Given an integer array nums, return all the triplets [nums[i], nums[j], nums[k]] such that i != j, i != k, and j != k, and nums[i] + nums[j] + nums[k] == 0.',
                example: {
                    nums: [-1, 0, 1, 2, -1, -4],
                    solution: [[-1, -1, 2], [-1, 0, 1]]
                },
                visualType: 'array',
                dataStructure: 'Array & Two Pointers',
                template: `function threeSum(nums) {
    // TODO: Implement two-pointer solution
    // Hint: Sort the array first, then use two pointers
    // Fix one number, use two pointers for the other two
    
    const result = [];
    
    // Sort the array
    nums.sort((a, b) => a - b);
    
    for (let i = 0; i < nums.length - 2; i++) {
        // Skip duplicates
        if (i > 0 && nums[i] === nums[i - 1]) continue;
        
        let left = i + 1;
        let right = nums.length - 1;
        
        // Your code here - use two pointers
        
    }
    
    return result;
}`,
                solution: `function threeSum(nums) {
    const result = [];
    nums.sort((a, b) => a - b);
    
    for (let i = 0; i < nums.length - 2; i++) {
        if (i > 0 && nums[i] === nums[i - 1]) continue;
        
        let left = i + 1;
        let right = nums.length - 1;
        
        while (left < right) {
            const sum = nums[i] + nums[left] + nums[right];
            
            if (sum === 0) {
                result.push([nums[i], nums[left], nums[right]]);
                while (left < right && nums[left] === nums[left + 1]) left++;
                while (left < right && nums[right] === nums[right - 1]) right--;
                left++;
                right--;
            } else if (sum < 0) {
                left++;
            } else {
                right--;
            }
        }
    }
    
    return result;
}`,
                hints: [
                    'Sort the array first to use two pointers',
                    'Fix one number (i), use two pointers (left, right) for the other two',
                    'If sum < 0, move left pointer right. If sum > 0, move right pointer left',
                    'Skip duplicates to avoid duplicate triplets in result'
                ],
                testCases: [
                    { input: [-1, 0, 1, 2, -1, -4], expected: [[-1, -1, 2], [-1, 0, 1]] },
                    { input: [0, 1, 1], expected: [] },
                    { input: [0, 0, 0], expected: [[0, 0, 0]] }
                ]
            },
            {
                id: 'longest-palindrome',
                title: 'Longest Palindromic Substring',
                difficulty: 'Medium',
                description: 'Use Expand Around Centers algorithm!',
                problem: 'Given a string s, return the longest palindromic substring in s.',
                example: {
                    input: 'babad',
                    solution: 'bab' // or 'aba'
                },
                visualType: 'string',
                dataStructure: 'String & Expand Around Centers',
                template: `function longestPalindrome(s) {
    // TODO: Implement expand around centers
    // Hint: Check both odd and even length palindromes
    // Expand from each center and find the longest
    
    let longest = '';
    
    for (let i = 0; i < s.length; i++) {
        // Check odd length (center at i)
        // Your code here
        
        // Check even length (center between i and i+1)
        // Your code here
        
    }
    
    return longest;
}

function expandAroundCenter(s, left, right) {
    // Helper function to expand and find palindrome
    // Your code here
}`,
                solution: `function longestPalindrome(s) {
    let longest = '';
    
    for (let i = 0; i < s.length; i++) {
        // Odd length palindrome
        const odd = expandAroundCenter(s, i, i);
        // Even length palindrome
        const even = expandAroundCenter(s, i, i + 1);
        
        const current = odd.length > even.length ? odd : even;
        if (current.length > longest.length) {
            longest = current;
        }
    }
    
    return longest;
}

function expandAroundCenter(s, left, right) {
    while (left >= 0 && right < s.length && s[left] === s[right]) {
        left--;
        right++;
    }
    return s.substring(left + 1, right);
}`,
                hints: [
                    'For each position, check both odd and even length palindromes',
                    'Odd length: center at position i',
                    'Even length: center between positions i and i+1',
                    'Expand outward from center while characters match',
                    'Keep track of the longest palindrome found'
                ],
                testCases: [
                    { input: 'babad', expected: 'bab' },
                    { input: 'cbbd', expected: 'bb' },
                    { input: 'a', expected: 'a' },
                    { input: 'ac', expected: 'a' }
                ]
            }
        ];
        
        function AlgorithmPixelGame() {
            const [currentProblem, setCurrentProblem] = useState(0);
            const [gameState, setGameState] = useState('ready'); // ready, playing, solved, failed
            const [score, setScore] = useState(0);
            const [moves, setMoves] = useState(0);
            const [selectedIndices, setSelectedIndices] = useState([]);
            const [animationStep, setAnimationStep] = useState(0);
            const [showHint, setShowHint] = useState(false);
            const [arrayData, setArrayData] = useState([]);
            const [stringData, setStringData] = useState('');
            const [stack, setStack] = useState([]);
            const [isAnimating, setIsAnimating] = useState(false);
            const animationRef = useRef(null);
            
            const problem = PROBLEMS[currentProblem];
            
            // Initialize game data based on problem type
            useEffect(() => {
                if (problem) {
                    setGameState('ready');
                    setSelectedIndices([]);
                    setMoves(0);
                    setAnimationStep(0);
                    setShowHint(false);
                    setStack([]);
                    
                    if (problem.example.nums) {
                        setArrayData([...problem.example.nums]);
                        setStringData('');
                    } else if (problem.example.input) {
                        setStringData(problem.example.input);
                        setArrayData([]);
                    }
                }
            }, [currentProblem]);
            
            // Handle element click based on problem type
            const handleElementClick = useCallback((index) => {
                if (isAnimating || gameState === 'solved') return;
                
                setGameState('playing');
                setMoves(moves + 1);
                
                if (problem.id === 'valid-parentheses') {
                    // Stack-based: push/pop parentheses
                    const char = stringData[index];
                    const isOpen = ['(', '[', '{'].includes(char);
                    
                    if (isOpen) {
                        // Push to stack
                        const newStack = [...stack, { char, index }];
                        setStack(newStack);
                        setSelectedIndices([...selectedIndices, index]);
                    } else {
                        // Try to match with top of stack
                        if (stack.length > 0) {
                            const top = stack[stack.length - 1];
                            const matches = 
                                (top.char === '(' && char === ')') ||
                                (top.char === '[' && char === ']') ||
                                (top.char === '{' && char === '}');
                            
                            if (matches) {
                                // Pop from stack
                                const newStack = stack.slice(0, -1);
                                setStack(newStack);
                                setSelectedIndices(selectedIndices.filter(i => i !== top.index).concat(index));
                                
                                // Check if solved (all matched and at end of string)
                                if (newStack.length === 0 && index === stringData.length - 1) {
                                    setTimeout(() => {
                                        setGameState('solved');
                                        setScore(score + (150 - moves * 5));
                                        playSuccessAnimation();
                                    }, 300);
                                }
                            } else {
                                // Invalid match - reset
                                setTimeout(() => {
                                    setStack([]);
                                    setSelectedIndices([]);
                                }, 1000);
                            }
                        } else {
                            // No opening bracket to match - invalid
                            setTimeout(() => {
                                setSelectedIndices([]);
                            }, 1000);
                        }
                    }
                } else if (problem.id === 'three-sum') {
                    // Two pointers: select three elements
                    if (selectedIndices.length < 3) {
                        if (!selectedIndices.includes(index)) {
                            const newSelection = [...selectedIndices, index].sort((a, b) => a - b);
                            setSelectedIndices(newSelection);
                            
                            if (newSelection.length === 3) {
                                const sum = arrayData[newSelection[0]] + arrayData[newSelection[1]] + arrayData[newSelection[2]];
                                if (sum === 0) {
                                    setTimeout(() => {
                                        setGameState('solved');
                                        setScore(score + (150 - moves * 5));
                                        playSuccessAnimation();
                                    }, 300);
                                } else {
                                    setTimeout(() => {
                                        setSelectedIndices([]);
                                    }, 1500);
                                }
                            }
                        }
                    } else {
                        setSelectedIndices([index]);
                    }
                } else if (problem.id === 'longest-palindrome') {
                    // Expand around centers: select center and expand
                    if (selectedIndices.length === 0) {
                        setSelectedIndices([index]);
                    } else if (selectedIndices.length === 1) {
                        // Try expanding from center
                        const center = selectedIndices[0];
                        let left = center;
                        let right = index;
                        
                        // Check if it's a valid palindrome
                        let isValid = true;
                        while (left <= right) {
                            if (stringData[left] !== stringData[right]) {
                                isValid = false;
                                break;
                            }
                            left++;
                            right--;
                        }
                        
                        if (isValid) {
                            const newSelection = [];
                            for (let i = selectedIndices[0]; i <= index; i++) {
                                newSelection.push(i);
                            }
                            setSelectedIndices(newSelection);
                            
                            // Check if it's the longest palindrome
                            const currentLength = newSelection.length;
                            const solutionLength = problem.example.solution.length;
                            if (currentLength >= solutionLength) {
                                setTimeout(() => {
                                    setGameState('solved');
                                    setScore(score + (150 - moves * 5));
                                    playSuccessAnimation();
                                }, 300);
                            }
                        } else {
                            setTimeout(() => {
                                setSelectedIndices([]);
                            }, 1000);
                        }
                    } else {
                        setSelectedIndices([index]);
                    }
                }
            }, [selectedIndices, arrayData, stringData, stack, moves, score, problem, gameState, isAnimating]);
            
            // Play success animation
            const playSuccessAnimation = () => {
                setIsAnimating(true);
                let step = 0;
                animationRef.current = setInterval(() => {
                    setAnimationStep(step);
                    step++;
                    if (step > 10) {
                        clearInterval(animationRef.current);
                        setIsAnimating(false);
                        setAnimationStep(0);
                    }
                }, 100);
            };
            
            // Reset game
            const resetGame = () => {
                if (problem) {
                    if (problem.example.nums) {
                        setArrayData([...problem.example.nums]);
                        setStringData('');
                    } else if (problem.example.input) {
                        setStringData(problem.example.input);
                        setArrayData([]);
                    }
                    setGameState('ready');
                    setSelectedIndices([]);
                    setStack([]);
                    setMoves(0);
                    setAnimationStep(0);
                    setShowHint(false);
                }
            };
            
            // Next problem
            const nextProblem = () => {
                if (currentProblem < PROBLEMS.length - 1) {
                    setCurrentProblem(currentProblem + 1);
                }
            };
            
            // Previous problem
            const prevProblem = () => {
                if (currentProblem > 0) {
                    setCurrentProblem(currentProblem - 1);
                }
            };
            
            // Render pixel-style element (for arrays or strings)
            const renderPixelElement = (value, index) => {
                const isSelected = selectedIndices.includes(index);
                const isAnimating = animationStep > 0 && gameState === 'solved';
                const inStack = problem.id === 'valid-parentheses' && stack.some(s => s.index === index);
                
                return (
                    <div
                        key={index}
                        onClick={() => handleElementClick(index)}
                        style={{
                            width: PIXEL_SIZE,
                            height: PIXEL_SIZE,
                            backgroundColor: inStack ? COLORS.secondary :
                                           isSelected ? COLORS.warning : 
                                           isAnimating ? COLORS.success : COLORS.primary,
                            border: `3px solid ${isSelected ? COLORS.danger : inStack ? COLORS.secondary : COLORS.grid}`,
                            borderRadius: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '18px',
                            fontWeight: 'bold',
                            color: COLORS.text,
                            cursor: gameState === 'solved' ? 'default' : 'pointer',
                            transition: 'all 0.3s ease',
                            transform: isAnimating ? `scale(${1 + Math.sin(animationStep) * 0.2})` : 'scale(1)',
                            boxShadow: isSelected ? `0 0 20px ${COLORS.warning}` : 
                                      inStack ? `0 0 15px ${COLORS.secondary}` :
                                      isAnimating ? `0 0 20px ${COLORS.success}` : 'none',
                            position: 'relative'
                        }}
                    >
                        <span>{value}</span>
                        {problem.id === 'three-sum' && (
                            <div style={{
                                position: 'absolute',
                                top: -8,
                                fontSize: '10px',
                                color: COLORS.text,
                                backgroundColor: COLORS.background,
                                padding: '2px 4px',
                                borderRadius: '4px'
                            }}>
                                {index}
                            </div>
                        )}
                    </div>
                );
            };
            
            // Render stack visualization
            const renderStack = () => {
                return (
                    <div style={{
                        marginTop: '2rem',
                        padding: '1rem',
                        backgroundColor: COLORS.grid,
                        borderRadius: '8px',
                        minHeight: '100px'
                    }}>
                        <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: COLORS.text }}>
                            <strong>Stack:</strong>
                        </div>
                        <div style={{
                            display: 'flex',
                            flexDirection: 'column-reverse',
                            gap: '0.5rem',
                            alignItems: 'center'
                        }}>
                            {stack.length === 0 ? (
                                <div style={{ color: COLORS.text, opacity: 0.5 }}>Empty</div>
                            ) : (
                                stack.map((item, idx) => (
                                    <div
                                        key={idx}
                                        style={{
                                            width: PIXEL_SIZE,
                                            height: PIXEL_SIZE,
                                            backgroundColor: COLORS.secondary,
                                            border: `3px solid ${COLORS.primary}`,
                                            borderRadius: '8px',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontSize: '18px',
                                            fontWeight: 'bold',
                                            color: COLORS.text
                                        }}
                                    >
                                        {item.char}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                );
            };
            
            return (
                <div style={{
                    minHeight: '100vh',
                    backgroundColor: COLORS.background,
                    color: COLORS.text,
                    padding: '2rem',
                    fontFamily: '"Courier New", monospace'
                }}>
                    <div style={{
                        maxWidth: '1200px',
                        margin: '0 auto'
                    }}>
                        {/* Header */}
                        <div style={{
                            textAlign: 'center',
                            marginBottom: '2rem'
                        }}>
                            <h1 style={{
                                fontSize: '2.5rem',
                                marginBottom: '0.5rem',
                                textShadow: `3px 3px 0px ${COLORS.grid}`,
                                color: COLORS.text
                            }}                            >
                                🎮 Algorithm Pixel Game
                            </h1>
                            <div style={{
                                display: 'flex',
                                justifyContent: 'center',
                                gap: '1rem',
                                marginTop: '1rem'
                            }}>
                                <div style={{
                                    backgroundColor: COLORS.grid,
                                    padding: '0.5rem 1rem',
                                    borderRadius: '8px'
                                }}>
                                    Score: <strong>{score}</strong>
                                </div>
                                <div style={{
                                    backgroundColor: COLORS.grid,
                                    padding: '0.5rem 1rem',
                                    borderRadius: '8px'
                                }}>
                                    Moves: <strong>{moves}</strong>
                                </div>
                            </div>
                        </div>
                        
                        {/* Problem Info */}
                        <div style={{
                            backgroundColor: COLORS.grid,
                            padding: '1.5rem',
                            borderRadius: '12px',
                            marginBottom: '2rem',
                            border: `3px solid ${COLORS.primary}`
                        }}>
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                marginBottom: '1rem'
                            }}>
                                <h2 style={{ margin: 0, fontSize: '1.5rem' }}>
                                    {problem.title}
                                </h2>
                                <span style={{
                                    backgroundColor: problem.difficulty === 'Easy' ? COLORS.success :
                                                   problem.difficulty === 'Medium' ? COLORS.warning : COLORS.danger,
                                    padding: '0.25rem 0.75rem',
                                    borderRadius: '6px',
                                    fontSize: '0.9rem',
                                    fontWeight: 'bold'
                                }}>
                                    {problem.difficulty}
                                </span>
                            </div>
                            <p style={{ marginBottom: '1rem', lineHeight: '1.6' }}>
                                {problem.description}
                            </p>
                            <div style={{
                                backgroundColor: COLORS.background,
                                padding: '1rem',
                                borderRadius: '8px',
                                marginTop: '1rem',
                                fontSize: '0.9rem'
                            }}>
                                <strong>Data Structure:</strong> {problem.dataStructure}
                            </div>
                            {showHint && (
                                <div style={{
                                    backgroundColor: COLORS.warning,
                                    color: COLORS.background,
                                    padding: '1rem',
                                    borderRadius: '8px',
                                    marginTop: '1rem'
                                }}>
                                    <strong>Hint:</strong> {problem.problem}
                                </div>
                            )}
                        </div>
                        
                        {/* Game Area */}
                        <div style={{
                            backgroundColor: COLORS.grid,
                            padding: '2rem',
                            borderRadius: '12px',
                            marginBottom: '2rem',
                            minHeight: '300px',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}>
                            {gameState === 'solved' && (
                                <div style={{
                                    fontSize: '2rem',
                                    marginBottom: '1rem',
                                    animation: 'bounce 0.5s ease'
                                }}>
                                    🎉 Success! 🎉
                                </div>
                            )}
                            
                            <div style={{
                                display: 'flex',
                                gap: '1rem',
                                flexWrap: 'wrap',
                                justifyContent: 'center',
                                alignItems: 'center'
                            }}>
                                {problem.id === 'valid-parentheses' || problem.id === 'longest-palindrome' ? 
                                    stringData.split('').map((char, index) => renderPixelElement(char, index)) :
                                    arrayData.map((value, index) => renderPixelElement(value, index))
                                }
                            </div>
                            
                            {/* Stack visualization for parentheses problem */}
                            {problem.id === 'valid-parentheses' && renderStack()}
                            
                            {/* Show sum for 3Sum */}
                            {problem.id === 'three-sum' && selectedIndices.length === 3 && (
                                <div style={{
                                    marginTop: '2rem',
                                    fontSize: '1.2rem',
                                    color: COLORS.warning
                                }}>
                                    Sum: {arrayData[selectedIndices[0]]} + {arrayData[selectedIndices[1]]} + {arrayData[selectedIndices[2]]} = {arrayData[selectedIndices[0]] + arrayData[selectedIndices[1]] + arrayData[selectedIndices[2]]}
                                </div>
                            )}
                            
                            {/* Show selected substring for palindrome */}
                            {problem.id === 'longest-palindrome' && selectedIndices.length > 1 && (
                                <div style={{
                                    marginTop: '2rem',
                                    fontSize: '1.2rem',
                                    color: COLORS.warning
                                }}>
                                    Selected: "{selectedIndices.map(i => stringData[i]).join('')}"
                                </div>
                            )}
                        </div>
                        
                        {/* Controls */}
                        <div style={{
                            display: 'flex',
                            gap: '1rem',
                            justifyContent: 'center',
                            flexWrap: 'wrap'
                        }}>
                            <button
                                onClick={resetGame}
                                style={{
                                    backgroundColor: COLORS.secondary,
                                    color: COLORS.text,
                                    border: 'none',
                                    padding: '0.75rem 1.5rem',
                                    borderRadius: '8px',
                                    fontSize: '1rem',
                                    fontWeight: 'bold',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease'
                                }}
                                onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
                                onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
                            >
                                🔄 Reset
                            </button>
                            
                            <button
                                onClick={() => setShowHint(!showHint)}
                                style={{
                                    backgroundColor: COLORS.warning,
                                    color: COLORS.background,
                                    border: 'none',
                                    padding: '0.75rem 1.5rem',
                                    borderRadius: '8px',
                                    fontSize: '1rem',
                                    fontWeight: 'bold',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease'
                                }}
                                onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
                                onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
                            >
                                💡 {showHint ? 'Hide' : 'Show'} Hint
                            </button>
                            
                            {gameState === 'solved' && (
                                <button
                                    onClick={nextProblem}
                                    style={{
                                        backgroundColor: COLORS.success,
                                        color: COLORS.text,
                                        border: 'none',
                                        padding: '0.75rem 1.5rem',
                                        borderRadius: '8px',
                                        fontSize: '1rem',
                                        fontWeight: 'bold',
                                        cursor: 'pointer',
                                        transition: 'all 0.3s ease'
                                    }}
                                    onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
                                    onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
                                >
                                    ➡️ Next Problem
                                </button>
                            )}
                        </div>
                        
                        {/* Problem Navigation */}
                        <div style={{
                            display: 'flex',
                            justifyContent: 'center',
                            gap: '1rem',
                            marginTop: '2rem'
                        }}>
                            <button
                                onClick={prevProblem}
                                disabled={currentProblem === 0}
                                style={{
                                    backgroundColor: currentProblem === 0 ? COLORS.grid : COLORS.primary,
                                    color: COLORS.text,
                                    border: 'none',
                                    padding: '0.5rem 1rem',
                                    borderRadius: '8px',
                                    cursor: currentProblem === 0 ? 'not-allowed' : 'pointer',
                                    opacity: currentProblem === 0 ? 0.5 : 1
                                }}
                            >
                                ⬅️ Prev
                            </button>
                            <span style={{
                                padding: '0.5rem 1rem',
                                backgroundColor: COLORS.grid,
                                borderRadius: '8px'
                            }}>
                                Problem {currentProblem + 1} / {PROBLEMS.length}
                            </span>
                            <button
                                onClick={nextProblem}
                                disabled={currentProblem === PROBLEMS.length - 1}
                                style={{
                                    backgroundColor: currentProblem === PROBLEMS.length - 1 ? COLORS.grid : COLORS.primary,
                                    color: COLORS.text,
                                    border: 'none',
                                    padding: '0.5rem 1rem',
                                    borderRadius: '8px',
                                    cursor: currentProblem === PROBLEMS.length - 1 ? 'not-allowed' : 'pointer',
                                    opacity: currentProblem === PROBLEMS.length - 1 ? 0.5 : 1
                                }}
                            >
                                Next ➡️
                            </button>
                        </div>
                    </div>
                    
                    <style>{`
                        @keyframes bounce {
                            0%, 100% { transform: translateY(0); }
                            50% { transform: translateY(-20px); }
                        }
                    `}</style>
                </div>
            );
        }
        
        // Make component globally available
        window.AlgorithmPixelGame = AlgorithmPixelGame;
        console.log('✅ AlgorithmPixelGame component defined');
    }
    
    // Start trying to define the component
    defineComponent();
})();


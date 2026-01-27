/**
 * Algorithm Pixel Game - Visual Learning Tool
 * Interactive visual guide to understand and memorize algorithms
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
        const COLORS = {
            primary: '#4A90E2',
            secondary: '#7B68EE',
            success: '#50C878',
            danger: '#FF6B6B',
            warning: '#FFD93D',
            background: '#2C3E50',
            grid: '#34495E',
            text: '#ECF0F1',
            highlight: '#FFD700'
        };
        
        // Algorithm problems with visual step-by-step guides
        const PROBLEMS = [
            {
                id: 'valid-parentheses',
                title: 'Valid Parentheses',
                difficulty: 'Medium',
                dataStructure: 'Stack',
                why: 'Stack is perfect because we need to match the MOST RECENT opening bracket (Last In First Out - LIFO)',
                concept: 'Think of it like stacking plates - you remove the top plate first. Opening brackets go on the stack, closing brackets remove the most recent opening bracket.',
                example: {
                    input: '()[]{}',
                    solution: true
                },
                steps: [
                    {
                        step: 1,
                        action: 'Start with an empty stack',
                        explanation: 'We use a stack to keep track of opening brackets',
                        visual: { stack: [], currentChar: '(', index: 0, highlight: [0] }
                    },
                    {
                        step: 2,
                        action: 'See opening bracket "(" - push to stack',
                        explanation: 'Opening brackets go on the stack (like stacking plates)',
                        visual: { stack: ['('], currentChar: ')', index: 1, highlight: [1] }
                    },
                    {
                        step: 3,
                        action: 'See closing bracket ")" - check if it matches top of stack',
                        explanation: 'Closing bracket ")" matches opening "(" - pop from stack',
                        visual: { stack: [], currentChar: '[', index: 2, highlight: [2] }
                    },
                    {
                        step: 4,
                        action: 'See opening bracket "[" - push to stack',
                        explanation: 'Another opening bracket goes on the stack',
                        visual: { stack: ['['], currentChar: ']', index: 3, highlight: [3] }
                    },
                    {
                        step: 5,
                        action: 'See closing bracket "]" - matches top "[", pop from stack',
                        explanation: 'The brackets match, so we remove it from the stack',
                        visual: { stack: [], currentChar: '{', index: 4, highlight: [4] }
                    },
                    {
                        step: 6,
                        action: 'See opening bracket "{" - push to stack',
                        explanation: 'Final opening bracket goes on the stack',
                        visual: { stack: ['{'], currentChar: '}', index: 5, highlight: [5] }
                    },
                    {
                        step: 7,
                        action: 'See closing bracket "}" - matches top "{", pop from stack',
                        explanation: 'Final match! Stack is now empty',
                        visual: { stack: [], currentChar: null, index: 6, highlight: [] }
                    },
                    {
                        step: 8,
                        action: 'Stack is empty - all brackets matched!',
                        explanation: 'If stack is empty at the end, the string is valid',
                        visual: { stack: [], currentChar: null, index: 6, highlight: [] }
                    }
                ]
            },
            {
                id: 'three-sum',
                title: '3Sum',
                difficulty: 'Medium',
                dataStructure: 'Array & Two Pointers',
                why: 'After sorting, we can use two pointers to efficiently find pairs that sum to a target. Fix one number, then search for the other two.',
                concept: 'Like finding two people whose heights add up to a target - sort everyone by height, then use two pointers to search efficiently.',
                example: {
                    nums: [-1, 0, 1, 2, -1, -4],
                    solution: [[-1, -1, 2], [-1, 0, 1]]
                },
                steps: [
                    {
                        step: 1,
                        action: 'Sort the array: [-4, -1, -1, 0, 1, 2]',
                        explanation: 'Sorting allows us to use two pointers efficiently',
                        visual: { array: [-4, -1, -1, 0, 1, 2], i: 0, left: 1, right: 5, highlight: [0] }
                    },
                    {
                        step: 2,
                        action: 'Fix i=0 (value -4), use two pointers left=1, right=5',
                        explanation: 'We fix one number and search for two others that sum to 0',
                        visual: { array: [-4, -1, -1, 0, 1, 2], i: 0, left: 1, right: 5, highlight: [0, 1, 5] }
                    },
                    {
                        step: 3,
                        action: 'Sum = -4 + (-1) + 2 = -3. Too small, move left pointer right',
                        explanation: 'When sum < 0, we need larger numbers, so move left pointer right',
                        visual: { array: [-4, -1, -1, 0, 1, 2], i: 0, left: 2, right: 5, highlight: [0, 2, 5] }
                    },
                    {
                        step: 4,
                        action: 'Continue searching... No valid triplets starting with -4',
                        explanation: 'We skip to next i when pointers cross',
                        visual: { array: [-4, -1, -1, 0, 1, 2], i: 1, left: 2, right: 5, highlight: [1, 2, 5] }
                    },
                    {
                        step: 5,
                        action: 'Fix i=1 (value -1), left=2, right=5. Sum = -1 + (-1) + 2 = 0 ✓',
                        explanation: 'Found a valid triplet! Add to result and move both pointers',
                        visual: { array: [-4, -1, -1, 0, 1, 2], i: 1, left: 3, right: 4, highlight: [1, 2, 5], found: [[-1, -1, 2]] }
                    },
                    {
                        step: 6,
                        action: 'Continue with i=1, left=3, right=4. Sum = -1 + 0 + 1 = 0 ✓',
                        explanation: 'Another valid triplet found!',
                        visual: { array: [-4, -1, -1, 0, 1, 2], i: 1, left: 4, right: 3, highlight: [1, 3, 4], found: [[-1, -1, 2], [-1, 0, 1]] }
                    }
                ]
            },
            {
                id: 'longest-palindrome',
                title: 'Longest Palindromic Substring',
                difficulty: 'Medium',
                dataStructure: 'String & Expand Around Centers',
                why: 'Instead of checking all substrings (O(n³)), we check each possible center and expand outward (O(n²)). Much more efficient!',
                concept: 'Like ripples in water - start from a center point and expand outward. Check both odd-length (center at char) and even-length (center between chars) palindromes.',
                example: {
                    input: 'babad',
                    solution: 'bab'
                },
                steps: [
                    {
                        step: 1,
                        action: 'Start at position 0: "b"',
                        explanation: 'Check odd-length palindrome centered at "b"',
                        visual: { string: 'babad', center: 0, left: 0, right: 0, highlight: [0] }
                    },
                    {
                        step: 2,
                        action: 'Expand: left=-1 (out of bounds), right=1. Stop. Length = 1',
                        explanation: 'Cannot expand further, palindrome is just "b"',
                        visual: { string: 'babad', center: 1, left: 1, right: 1, highlight: [1] }
                    },
                    {
                        step: 3,
                        action: 'Center at position 1: "a". Expand: left=0 ("b"), right=2 ("b")',
                        explanation: 'Characters match! Continue expanding',
                        visual: { string: 'babad', center: 1, left: 0, right: 2, highlight: [0, 1, 2] }
                    },
                    {
                        step: 4,
                        action: 'Expand further: left=-1, right=3. Stop. Found "bab" (length 3)',
                        explanation: 'This is the longest palindrome found so far!',
                        visual: { string: 'babad', center: 1, left: -1, right: 3, highlight: [0, 1, 2], longest: 'bab' }
                    },
                    {
                        step: 5,
                        action: 'Check even-length: center between 1-2. "a" != "b", no palindrome',
                        explanation: 'Even-length palindromes have center between two characters',
                        visual: { string: 'babad', center: 1.5, left: 1, right: 2, highlight: [1, 2] }
                    },
                    {
                        step: 6,
                        action: 'Continue checking other centers... Final answer: "bab"',
                        explanation: 'We check all possible centers and keep the longest palindrome',
                        visual: { string: 'babad', longest: 'bab', highlight: [0, 1, 2] }
                    }
                ]
            }
        ];
        
        function AlgorithmPixelGame() {
            const [currentProblem, setCurrentProblem] = useState(0);
            const [currentStep, setCurrentStep] = useState(0);
            const [isPlaying, setIsPlaying] = useState(false);
            const [showWhy, setShowWhy] = useState(false);
            const [showConcept, setShowConcept] = useState(false);
            const [autoPlay, setAutoPlay] = useState(false);
            const [speed, setSpeed] = useState(1500); // milliseconds
            const autoPlayRef = useRef(null);
            
            const problem = PROBLEMS[currentProblem];
            const totalSteps = problem.steps.length;
            
            // Reset state when problem changes
            useEffect(() => {
                setCurrentStep(0);
                setIsPlaying(false);
                setAutoPlay(false);
                setShowWhy(false);
                setShowConcept(false);
            }, [currentProblem]);
            
            // Auto-play functionality
            useEffect(() => {
                if (autoPlay && isPlaying && currentStep < totalSteps - 1) {
                    autoPlayRef.current = setTimeout(() => {
                        setCurrentStep(prev => Math.min(prev + 1, totalSteps - 1));
                    }, speed);
                } else if (currentStep >= totalSteps - 1) {
                    setIsPlaying(false);
                    setAutoPlay(false);
                }
                
                return () => {
                    if (autoPlayRef.current) {
                        clearTimeout(autoPlayRef.current);
                    }
                };
            }, [autoPlay, isPlaying, currentStep, totalSteps, speed]);
            
            const nextStep = () => {
                if (currentStep < totalSteps - 1) {
                    setCurrentStep(currentStep + 1);
                }
            };
            
            const prevStep = () => {
                if (currentStep > 0) {
                    setCurrentStep(currentStep - 1);
                }
            };
            
            const reset = () => {
                setCurrentStep(0);
                setIsPlaying(false);
                setAutoPlay(false);
            };
            
            const startPlaythrough = () => {
                setCurrentStep(0);
                setIsPlaying(true);
            };
            
            const toggleAutoPlay = () => {
                if (!isPlaying) {
                    startPlaythrough();
                }
                setAutoPlay(!autoPlay);
            };
            
            // Next problem
            const nextProblem = () => {
                if (currentProblem < PROBLEMS.length - 1) {
                    setCurrentProblem(currentProblem + 1);
                    setCurrentStep(0);
                    setIsPlaying(false);
                    setAutoPlay(false);
                }
            };
            
            // Previous problem
            const prevProblem = () => {
                if (currentProblem > 0) {
                    setCurrentProblem(currentProblem - 1);
                    setCurrentStep(0);
                    setIsPlaying(false);
                    setAutoPlay(false);
                }
            };
            
            const currentStepData = problem.steps[currentStep];
            const visual = currentStepData.visual;
            
            // Render visual elements based on problem type
            const renderVisualization = () => {
                if (problem.id === 'valid-parentheses') {
                    return (
                        <div>
                            <div style={{ marginBottom: '1rem' }}>
                                <div style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>Input String:</div>
                                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                                    {problem.example.input.split('').map((char, idx) => (
                                        <div
                                            key={idx}
                                            style={{
                                                width: '50px',
                                                height: '50px',
                                                backgroundColor: visual.highlight.includes(idx) ? COLORS.highlight :
                                                               idx === visual.index ? COLORS.primary : COLORS.grid,
                                                border: `3px solid ${visual.highlight.includes(idx) ? COLORS.warning : COLORS.grid}`,
                                                borderRadius: '8px',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                fontSize: '24px',
                                                fontWeight: 'bold',
                                                color: COLORS.text,
                                                transition: 'all 0.3s ease'
                                            }}
                                        >
                                            {char}
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>Stack (LIFO - Last In First Out):</div>
                                <div style={{
                                    minHeight: '200px',
                                    backgroundColor: COLORS.grid,
                                    borderRadius: '8px',
                                    padding: '1rem',
                                    display: 'flex',
                                    flexDirection: 'column-reverse',
                                    alignItems: 'center',
                                    gap: '0.5rem'
                                }}>
                                    {visual.stack.length === 0 ? (
                                        <div style={{ color: COLORS.text, opacity: 0.5 }}>Empty Stack</div>
                                    ) : (
                                        visual.stack.map((item, idx) => (
                                            <div
                                                key={idx}
                                                style={{
                                                    width: '60px',
                                                    height: '60px',
                                                    backgroundColor: COLORS.secondary,
                                                    border: '3px solid',
                                                    borderColor: COLORS.primary,
                                                    borderRadius: '8px',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    fontSize: '28px',
                                                    fontWeight: 'bold',
                                                    color: COLORS.text,
                                                    animation: idx === visual.stack.length - 1 ? 'pulse 1s infinite' : 'none'
                                                }}
                                            >
                                                {item}
                                            </div>
                                        ))
                                    )}
                                </div>
                                <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: COLORS.text, opacity: 0.7 }}>
                                    💡 Stack = Like stacking plates. Remove top plate first!
                                </div>
                            </div>
                        </div>
                    );
                } else if (problem.id === 'three-sum') {
                    return (
                        <div>
                            <div style={{ marginBottom: '1rem' }}>
                                <div style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>Sorted Array:</div>
                                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                                    {visual.array.map((num, idx) => {
                                        const isI = idx === visual.i;
                                        const isLeft = idx === visual.left;
                                        const isRight = idx === visual.right;
                                        const isHighlighted = visual.highlight.includes(idx);
                                        
                                        return (
                                            <div
                                                key={idx}
                                                style={{
                                                    width: '60px',
                                                    height: '60px',
                                                    backgroundColor: isI ? COLORS.danger :
                                                                   isLeft ? COLORS.success :
                                                                   isRight ? COLORS.warning :
                                                                   isHighlighted ? COLORS.highlight : COLORS.grid,
                                                    border: `3px solid ${isHighlighted ? COLORS.primary : COLORS.grid}`,
                                                    borderRadius: '8px',
                                                    display: 'flex',
                                                    flexDirection: 'column',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    fontSize: '18px',
                                                    fontWeight: 'bold',
                                                    color: COLORS.text,
                                                    position: 'relative'
                                                }}
                                            >
                                                <span>{num}</span>
                                                {isI && <div style={{ fontSize: '10px', position: 'absolute', top: -8 }}>i</div>}
                                                {isLeft && <div style={{ fontSize: '10px', position: 'absolute', top: -8 }}>L</div>}
                                                {isRight && <div style={{ fontSize: '10px', position: 'absolute', top: -8 }}>R</div>}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                            {visual.found && visual.found.length > 0 && (
                                <div style={{
                                    backgroundColor: COLORS.success,
                                    padding: '1rem',
                                    borderRadius: '8px',
                                    marginTop: '1rem'
                                }}>
                                    <strong>Found Triplets:</strong>
                                    {visual.found.map((triplet, idx) => (
                                        <div key={idx} style={{ marginTop: '0.5rem' }}>
                                            [{triplet.join(', ')}]
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                } else if (problem.id === 'longest-palindrome') {
                    return (
                        <div>
                            <div style={{ marginBottom: '1rem' }}>
                                <div style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>String:</div>
                                <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                                    {visual.string.split('').map((char, idx) => {
                                        const isHighlighted = visual.highlight.includes(idx);
                                        const isCenter = idx === Math.floor(visual.center);
                                        
                                        return (
                                            <div
                                                key={idx}
                                                style={{
                                                    width: '50px',
                                                    height: '50px',
                                                    backgroundColor: isCenter ? COLORS.danger :
                                                                   isHighlighted ? COLORS.highlight : COLORS.grid,
                                                    border: `3px solid ${isHighlighted ? COLORS.primary : COLORS.grid}`,
                                                    borderRadius: '8px',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    fontSize: '24px',
                                                    fontWeight: 'bold',
                                                    color: COLORS.text,
                                                    position: 'relative'
                                                }}
                                            >
                                                {char}
                                                {isCenter && <div style={{ fontSize: '10px', position: 'absolute', top: -8 }}>C</div>}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                            {visual.longest && (
                                <div style={{
                                    backgroundColor: COLORS.success,
                                    padding: '1rem',
                                    borderRadius: '8px',
                                    marginTop: '1rem',
                                    textAlign: 'center',
                                    fontSize: '1.2rem',
                                    fontWeight: 'bold'
                                }}>
                                    Longest Palindrome: "{visual.longest}"
                                </div>
                            )}
                            <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: COLORS.text, opacity: 0.7 }}>
                                💡 Expand outward from center like ripples in water!
                            </div>
                        </div>
                    );
                }
            };
            
            return (
                <div style={{
                    minHeight: '100vh',
                    backgroundColor: COLORS.background,
                    color: COLORS.text,
                    padding: '2rem',
                    fontFamily: '"Courier New", monospace'
                }}>
                    <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
                        {/* Header */}
                        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                            <h1 style={{
                                fontSize: '2.5rem',
                                marginBottom: '0.5rem',
                                textShadow: `3px 3px 0px ${COLORS.grid}`,
                                color: COLORS.text
                            }}>
                                🎮 Algorithm Visual Learning
                            </h1>
                            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem' }}>
                                <div style={{ backgroundColor: COLORS.grid, padding: '0.5rem 1rem', borderRadius: '8px' }}>
                                    Problem {currentProblem + 1} / {PROBLEMS.length}
                                </div>
                                <div style={{ backgroundColor: COLORS.grid, padding: '0.5rem 1rem', borderRadius: '8px' }}>
                                    Step {currentStep + 1} / {totalSteps}
                                </div>
                            </div>
                        </div>
                        
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
                            {/* Left Column - Problem Info & Controls */}
                            <div>
                                {/* Problem Info */}
                                <div style={{
                                    backgroundColor: COLORS.grid,
                                    padding: '1.5rem',
                                    borderRadius: '12px',
                                    marginBottom: '1rem',
                                    border: `3px solid ${COLORS.primary}`
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                        <h2 style={{ margin: 0, fontSize: '1.5rem' }}>{problem.title}</h2>
                                        <span style={{
                                            backgroundColor: COLORS.warning,
                                            padding: '0.25rem 0.75rem',
                                            borderRadius: '6px',
                                            fontSize: '0.9rem',
                                            fontWeight: 'bold'
                                        }}>
                                            {problem.difficulty}
                                        </span>
                                    </div>
                                    <div style={{
                                        backgroundColor: COLORS.background,
                                        padding: '1rem',
                                        borderRadius: '8px',
                                        marginBottom: '1rem',
                                        fontSize: '0.9rem'
                                    }}>
                                        <strong>Data Structure:</strong> {problem.dataStructure}
                                    </div>
                                    
                                    {/* Why Button */}
                                    <button
                                        onClick={() => setShowWhy(!showWhy)}
                                        style={{
                                            width: '100%',
                                            backgroundColor: showWhy ? COLORS.secondary : COLORS.primary,
                                            color: COLORS.text,
                                            border: 'none',
                                            padding: '0.75rem',
                                            borderRadius: '8px',
                                            fontSize: '1rem',
                                            fontWeight: 'bold',
                                            cursor: 'pointer',
                                            marginBottom: '0.5rem'
                                        }}
                                    >
                                        ❓ Why {problem.dataStructure}?
                                    </button>
                                    {showWhy && (
                                        <div style={{
                                            backgroundColor: COLORS.secondary,
                                            padding: '1rem',
                                            borderRadius: '8px',
                                            marginBottom: '0.5rem',
                                            fontSize: '0.9rem'
                                        }}>
                                            {problem.why}
                                        </div>
                                    )}
                                    
                                    {/* Concept Button */}
                                    <button
                                        onClick={() => setShowConcept(!showConcept)}
                                        style={{
                                            width: '100%',
                                            backgroundColor: showConcept ? COLORS.success : COLORS.primary,
                                            color: COLORS.text,
                                            border: 'none',
                                            padding: '0.75rem',
                                            borderRadius: '8px',
                                            fontSize: '1rem',
                                            fontWeight: 'bold',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        💡 Key Concept
                                    </button>
                                    {showConcept && (
                                        <div style={{
                                            backgroundColor: COLORS.success,
                                            padding: '1rem',
                                            borderRadius: '8px',
                                            marginTop: '0.5rem',
                                            fontSize: '0.9rem'
                                        }}>
                                            {problem.concept}
                                        </div>
                                    )}
                                </div>
                                
                                {/* Step-by-Step Guide */}
                                <div style={{
                                    backgroundColor: COLORS.grid,
                                    padding: '1.5rem',
                                    borderRadius: '12px',
                                    marginBottom: '1rem'
                                }}>
                                    <h3 style={{ marginTop: 0 }}>📖 Step {currentStep + 1}: {currentStepData.action}</h3>
                                    <div style={{
                                        backgroundColor: COLORS.background,
                                        padding: '1rem',
                                        borderRadius: '8px',
                                        marginTop: '1rem',
                                        fontSize: '0.95rem',
                                        lineHeight: '1.6'
                                    }}>
                                        {currentStepData.explanation}
                                    </div>
                                </div>
                                
                                {/* Controls */}
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                    <button
                                        onClick={startPlaythrough}
                                        disabled={isPlaying}
                                        style={{
                                            width: '100%',
                                            backgroundColor: COLORS.success,
                                            color: COLORS.text,
                                            border: 'none',
                                            padding: '0.75rem',
                                            borderRadius: '8px',
                                            fontSize: '1rem',
                                            fontWeight: 'bold',
                                            cursor: isPlaying ? 'not-allowed' : 'pointer',
                                            opacity: isPlaying ? 0.6 : 1
                                        }}
                                    >
                                        ▶️ Start Walkthrough
                                    </button>
                                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                                        <button
                                            onClick={prevStep}
                                            disabled={currentStep === 0}
                                            style={{
                                                flex: 1,
                                                backgroundColor: currentStep === 0 ? COLORS.grid : COLORS.secondary,
                                                color: COLORS.text,
                                                border: 'none',
                                                padding: '0.75rem',
                                                borderRadius: '8px',
                                                fontSize: '1rem',
                                                fontWeight: 'bold',
                                                cursor: currentStep === 0 ? 'not-allowed' : 'pointer',
                                                opacity: currentStep === 0 ? 0.6 : 1
                                            }}
                                        >
                                            ⬅️ Prev
                                        </button>
                                        <button
                                            onClick={nextStep}
                                            disabled={currentStep >= totalSteps - 1}
                                            style={{
                                                flex: 1,
                                                backgroundColor: currentStep >= totalSteps - 1 ? COLORS.grid : COLORS.secondary,
                                                color: COLORS.text,
                                                border: 'none',
                                                padding: '0.75rem',
                                                borderRadius: '8px',
                                                fontSize: '1rem',
                                                fontWeight: 'bold',
                                                cursor: currentStep >= totalSteps - 1 ? 'not-allowed' : 'pointer',
                                                opacity: currentStep >= totalSteps - 1 ? 0.6 : 1
                                            }}
                                        >
                                            Next ➡️
                                        </button>
                                    </div>
                                    <button
                                        onClick={toggleAutoPlay}
                                        style={{
                                            width: '100%',
                                            backgroundColor: autoPlay ? COLORS.danger : COLORS.warning,
                                            color: COLORS.text,
                                            border: 'none',
                                            padding: '0.75rem',
                                            borderRadius: '8px',
                                            fontSize: '1rem',
                                            fontWeight: 'bold',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        {autoPlay ? '⏸️ Pause' : '▶️ Auto Play'}
                                    </button>
                                    <button
                                        onClick={reset}
                                        style={{
                                            width: '100%',
                                            backgroundColor: COLORS.grid,
                                            color: COLORS.text,
                                            border: 'none',
                                            padding: '0.75rem',
                                            borderRadius: '8px',
                                            fontSize: '1rem',
                                            fontWeight: 'bold',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        🔄 Reset
                                    </button>
                                    <div style={{ marginTop: '0.5rem' }}>
                                        <label style={{ fontSize: '0.9rem', display: 'block', marginBottom: '0.5rem' }}>
                                            Speed: {speed}ms
                                        </label>
                                        <input
                                            type="range"
                                            min="500"
                                            max="3000"
                                            step="500"
                                            value={speed}
                                            onChange={(e) => setSpeed(parseInt(e.target.value))}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                </div>
                                
                                {/* Navigation */}
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem' }}>
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
                                        ⬅️ Prev Problem
                                    </button>
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
                                        Next Problem ➡️
                                    </button>
                                </div>
                            </div>
                            
                            {/* Right Column - Visualization */}
                            <div>
                                <div style={{
                                    backgroundColor: COLORS.grid,
                                    padding: '2rem',
                                    borderRadius: '12px',
                                    minHeight: '500px'
                                }}>
                                    <h3 style={{ marginTop: 0, marginBottom: '1.5rem' }}>🎨 Visual Walkthrough</h3>
                                    {renderVisualization()}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <style>{`
                        @keyframes pulse {
                            0%, 100% { transform: scale(1); }
                            50% { transform: scale(1.1); }
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

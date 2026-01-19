"""
LSW Game API Endpoints
Longest Substring Without Repeating Characters - Interactive Game Backend
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

router = APIRouter()


class LSWGameRequest(BaseModel):
    """Request model for LSW game algorithm"""
    input_string: str = Field(..., description="Input string to process", min_length=1, max_length=1000)
    step_count: Optional[int] = Field(None, description="Number of steps to execute (None = run to completion)")


class LSWGameStep(BaseModel):
    """Single step in the algorithm"""
    step_number: int
    left_pointer: int
    right_pointer: int
    current_char: str
    current_window: str
    max_length: int
    is_duplicate: bool
    duplicate_char: Optional[str] = None
    last_seen: Dict[str, int]
    message: str


class LSWGameResponse(BaseModel):
    """Response model for LSW game"""
    success: bool
    input_string: str
    max_length: int
    total_steps: int
    steps: List[LSWGameStep]
    final_state: Dict
    execution_time_ms: float


class LSWGameValidateRequest(BaseModel):
    """Request to validate algorithm result"""
    input_string: str
    user_answer: int
    steps: Optional[List[Dict]] = None


class LSWGameValidateResponse(BaseModel):
    """Validation response"""
    correct: bool
    expected_max_length: int
    user_answer: int
    message: str
    details: Optional[Dict] = None


class LSWGameAlgorithm:
    """LSW Algorithm implementation"""
    
    @staticmethod
    def solve(input_string: str, max_steps: Optional[int] = None) -> LSWGameResponse:
        """
        Solve the LSW problem and return step-by-step execution
        
        Args:
            input_string: Input string to process
            max_steps: Maximum number of steps to execute (None = complete)
        
        Returns:
            LSWGameResponse with all steps
        """
        import time
        start_time = time.time()
        
        L = 0
        R = 0
        max_len = 0
        last_seen = {}
        steps = []
        step_number = 0
        
        input_string = input_string or ""
        n = len(input_string)
        
        while R < n:
            if max_steps and step_number >= max_steps:
                break
                
            step_number += 1
            current_char = input_string[R]
            is_duplicate = False
            duplicate_char = None
            message = ""
            
            # Check for duplicate
            if current_char in last_seen and last_seen[current_char] >= L:
                is_duplicate = True
                duplicate_char = current_char
                L = last_seen[current_char] + 1
                message = f"Duplicate '{duplicate_char}' found at index {R}. Moving L to {L}."
            else:
                message = f"Processing '{current_char}' at index {R}. Current window length: {R - L + 1}."
            
            # Update last seen
            last_seen[current_char] = R
            
            # Update max length
            current_len = R - L + 1
            max_len = max(max_len, current_len)
            
            # Get current window
            current_window = input_string[L:R+1]
            
            # Create step
            step = LSWGameStep(
                step_number=step_number,
                left_pointer=L,
                right_pointer=R,
                current_char=current_char,
                current_window=current_window,
                max_length=max_len,
                is_duplicate=is_duplicate,
                duplicate_char=duplicate_char,
                last_seen=last_seen.copy(),
                message=message
            )
            steps.append(step)
            
            # Move right pointer
            R += 1
        
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return LSWGameResponse(
            success=True,
            input_string=input_string,
            max_length=max_len,
            total_steps=step_number,
            steps=steps,
            final_state={
                "L": L,
                "R": R,
                "max_len": max_len,
                "last_seen": last_seen,
                "is_complete": R >= n
            },
            execution_time_ms=execution_time
        )
    
    @staticmethod
    def validate(input_string: str, user_answer: int) -> LSWGameValidateResponse:
        """
        Validate user's answer against correct algorithm result
        
        Args:
            input_string: Input string
            user_answer: User's answer for max length
        
        Returns:
            Validation response
        """
        result = LSWGameAlgorithm.solve(input_string)
        correct = result.max_length == user_answer
        
        message = (
            f"Correct! The longest substring without repeating characters is {result.max_length}."
            if correct
            else f"Incorrect. Expected {result.max_length}, but you answered {user_answer}."
        )
        
        return LSWGameValidateResponse(
            correct=correct,
            expected_max_length=result.max_length,
            user_answer=user_answer,
            message=message,
            details={
                "input_string": input_string,
                "total_steps": result.total_steps,
                "execution_time_ms": result.execution_time_ms
            }
        )


@router.post("/solve", response_model=LSWGameResponse)
async def solve_lsw_game(request: LSWGameRequest):
    """
    Solve the LSW problem step-by-step
    
    Returns complete execution trace with all steps
    """
    try:
        result = LSWGameAlgorithm.solve(
            request.input_string,
            max_steps=request.step_count
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error solving LSW problem: {str(e)}")


@router.post("/step", response_model=LSWGameStep)
async def execute_single_step(
    input_string: str,
    left_pointer: int = 0,
    right_pointer: int = 0,
    max_length: int = 0,
    last_seen: Dict[str, int] = {}
):
    """
    Execute a single step of the algorithm
    
    Useful for interactive step-by-step execution
    """
    try:
        if right_pointer >= len(input_string):
            raise HTTPException(status_code=400, detail="Algorithm already complete")
        
        L = left_pointer
        R = right_pointer
        max_len = max_length
        last_seen_dict = last_seen.copy()
        
        current_char = input_string[R]
        is_duplicate = False
        duplicate_char = None
        message = ""
        
        # Check for duplicate
        if current_char in last_seen_dict and last_seen_dict[current_char] >= L:
            is_duplicate = True
            duplicate_char = current_char
            L = last_seen_dict[current_char] + 1
            message = f"Duplicate '{duplicate_char}' found at index {R}. Moving L to {L}."
        else:
            message = f"Processing '{current_char}' at index {R}. Current window length: {R - L + 1}."
        
        # Update last seen
        last_seen_dict[current_char] = R
        
        # Update max length
        current_len = R - L + 1
        max_len = max(max_len, current_len)
        
        # Get current window
        current_window = input_string[L:R+1]
        
        return LSWGameStep(
            step_number=1,  # Single step
            left_pointer=L,
            right_pointer=R + 1,  # R will be incremented after this step
            current_char=current_char,
            current_window=current_window,
            max_length=max_len,
            is_duplicate=is_duplicate,
            duplicate_char=duplicate_char,
            last_seen=last_seen_dict,
            message=message
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error executing step: {str(e)}")


@router.post("/validate", response_model=LSWGameValidateResponse)
async def validate_answer(request: LSWGameValidateRequest):
    """
    Validate user's answer against the correct algorithm result
    """
    try:
        result = LSWGameAlgorithm.validate(request.input_string, request.user_answer)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error validating answer: {str(e)}")


@router.get("/examples")
async def get_example_strings():
    """
    Get example strings for testing
    
    Returns common test cases with expected results
    """
    examples = [
        {
            "input_string": "abcabcbb",
            "expected_max_length": 3,
            "description": "Basic example with repeating pattern"
        },
        {
            "input_string": "pwwkew",
            "expected_max_length": 3,
            "description": "Example with overlapping windows"
        },
        {
            "input_string": "bbbbb",
            "expected_max_length": 1,
            "description": "All same characters"
        },
        {
            "input_string": "dvdf",
            "expected_max_length": 3,
            "description": "Edge case with duplicate in middle"
        },
        {
            "input_string": "a",
            "expected_max_length": 1,
            "description": "Single character"
        },
        {
            "input_string": "",
            "expected_max_length": 0,
            "description": "Empty string"
        }
    ]
    
    return {
        "success": True,
        "examples": examples,
        "count": len(examples)
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "lsw-game",
        "timestamp": datetime.utcnow().isoformat()
    }


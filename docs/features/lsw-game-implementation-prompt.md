# TOKIMEKI – LSW GAME IMPLEMENTATION PROMPT (SINGLE FILE)

## ROLE

You are GPT-5 running inside my IDE with full access to this Tokimeki repository.

Frontend is React (user-interactive SPA).

Backend is Python (FastAPI).

Your task is to implement a new interactive educational page:

**"Longest Substring Without Repeating Characters – Pixel Game"**.

====================================================

## HIGH-LEVEL GOAL

====================================================

Add a new user-interactive page to the existing React frontend that visually and

interactively demonstrates the Sliding Window algorithm for:

**Longest Substring Without Repeating Characters**.

This page must behave like existing pages (route/tab/page),

not as a static demo.

====================================================

## CONSTRAINTS

====================================================

• Frontend: React (no framework changes)

• Backend: Python FastAPI (backend API implemented - see BACKEND IMPLEMENTATION section)

• No breaking changes to existing pages

• No heavy external UI libraries

• Keep implementation modular and readable

• Pixel-game UI style (approved palette, NOT monochrome green)

====================================================

## FEATURE REQUIREMENTS (MANDATORY)

====================================================

### UI:

• Input string editor

• Visual input string cells

• Sliding window visualization (L..R)

• Left pointer (L) and Right pointer (R)

• Max Length display

• Status / message box

• Timeline / index markers

### Controls:

• Next Step

• Auto Play (toggle)

• Reset

• Speed slider (ms)

• Apply new string

### ALGORITHM:

• Correct Sliding Window logic

• Maintain lastSeen map

• On duplicate:

    if lastSeen[ch] >= L:

        L = lastSeen[ch] + 1

• Update R every step

• Update maxLen = max(maxLen, R - L + 1)

• Stop Auto Play at end of string

====================================================

## BACKEND IMPLEMENTATION

====================================================

**Python FastAPI Backend has been implemented** with the following endpoints:

### API Endpoints:

1. **`POST /api/v1/lsw-game/solve`**
   - Solves the entire algorithm step-by-step
   - Returns complete execution trace with all steps
   - Request: `{ "input_string": "abcabcbb", "step_count": null }`
   - Response: Complete step-by-step execution with max length

2. **`POST /api/v1/lsw-game/step`**
   - Executes a single step of the algorithm
   - Useful for interactive step-by-step execution
   - Parameters: `input_string`, `left_pointer`, `right_pointer`, `max_length`, `last_seen`

3. **`POST /api/v1/lsw-game/validate`**
   - Validates user's answer against correct algorithm result
   - Request: `{ "input_string": "abcabcbb", "user_answer": 3 }`
   - Response: Validation result with feedback

4. **`GET /api/v1/lsw-game/examples`**
   - Returns common test cases with expected results
   - Includes: "abcabcbb" → 3, "pwwkew" → 3, "bbbbb" → 1, etc.

5. **`GET /api/v1/lsw-game/health`**
   - Health check endpoint

### Backend Files:

- **`app/api/v1/endpoints/lsw_game.py`** - Main API endpoint implementation
- **`app/api/v1/api.py`** - Router registration (includes lsw_game router)

### Backend Features:

- Complete algorithm implementation in Python
- Step-by-step execution tracking
- Answer validation
- Test examples endpoint
- Performance metrics (execution time)

**Note:** The frontend works standalone (no backend required), but the backend is available for validation, statistics, and future features like progress tracking.

====================================================

## FRONTEND IMPLEMENTATION PLAN

====================================================

1. Add a new React page/component

   Suggested name:

     `LSWGamePage.jsx`

2. Register route or tab

   Follow existing routing or navigation architecture.

   Page must be navigable like other user-interactive pages.

3. Component structure (recommended):

   ```
   components/lsw-game/
     ├── LSWGamePage.jsx
     ├── LSWGameView.jsx
     ├── lswGameLogic.js
     └── lswGame.css
   ```

4. State management:

   • Use React hooks

   • No global state required

====================================================

## UI / VISUAL GUIDELINES

====================================================

• Pixel-style cards and blocks

• Window looks like a "glass container"

• L/R pointers visually distinct

• Duplicate event triggers:

  – brief visual alert (border flash or shake)

• Responsive layout

====================================================

## ACCEPTANCE CRITERIA

====================================================

• Page loads without console errors

• Navigation to page works

• Next Step behaves correctly

• Auto Play respects speed slider

• Reset works without refresh

• Input change restarts algorithm

### Correctness checks:

• `abcabcbb` → 3

• `pwwkew` → 3

• `bbbbb` → 1

====================================================

## DO NOT DO

====================================================

• Do not rewrite existing architecture

• Backend API is already implemented (see BACKEND IMPLEMENTATION section)

• Do not introduce React state libraries

====================================================

## FINAL STEP

====================================================

After implementation:

• Summarize changed files

• Explain where page is registered

• Provide quick manual test steps

• Fix any errors found during run

---

**END OF PROMPT**


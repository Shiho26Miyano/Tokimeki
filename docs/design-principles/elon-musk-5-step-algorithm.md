# Elon Musk's 5-Step Design Algorithm

## The 5-Step Algorithm (Design Process)

### Step 1: Make Requirements Less Dumb

**Question every requirement, even if it comes from a smart person.**

**What it means for the team:**
- Presume all requirements are suspicious, regardless of who proposed them
- Each requirement must be bound to a **named person** (not a department) who must defend why it exists
- Ask: Why does it exist? What are the quantified boundaries? What happens if we remove it?
- If no one is willing to vouch for a requirement, treat it as priority for deletion
- **Danger**: Requirements from intelligent people are especially dangerous because you may not question them enough

---

### Step 2: Delete Parts/Processes

**If you aren't adding things back in 10% of the time, you aren't deleting enough.**

**What it means for the team:**
- Deletion always takes priority over addition
- Actively search for parts, mechanisms, document approvals, tests, meetings that can be directly removed
- Most teams bias toward adding "just in case" elements rather than removing them
- **10% rule**: If you're not occasionally adding things back in 10% of the time, you're clearly not deleting enough
- Make deletion part of daily work, not just during major overhauls
- For extreme goals (e.g., reusable rockets), unnecessary mass or process will directly cause mission failure

---

### Step 3: Simplify/Optimize

**Only after steps 1 and 2 are done.**

**What it means for the team:**
- **Most common error of a smart engineer**: Optimizing something that should not exist
- Only after confirming "this thing must stay" are you qualified to spend time optimizing it
- Avoid wasting engineering resources polishing a part or process that shouldn't exist
- Goal: Achieve same or better functionality with fewer parts, simpler geometry, fewer custom part numbers
- Simplification includes interfaces and responsibility boundaries - reduce cross-team communication friction
- Final state: Any new engineer can quickly understand the design without thick documentation

---

### Step 4: Accelerate Cycle Time

**Speed up production.**

**What it means for the team:**
- Minimize time from design change to actual test result feedback - form high-frequency closed loops
- Accept that hardware will iterate as frequently as software, not pursuing perfect design in one go
- High production rate = high iteration rate = faster progress
- Eliminate waiting, scheduling, and approval times that don't create actual learning or output
- Use real test data to correct intuition and models, not endless meetings and simulations
- **Warning**: "If you're digging your grave, don't dig it faster" - only accelerate after steps 1-3

---

### Step 5: Automate

**Automation is the last step, for proven stable processes.**

**What it means for the team:**
- Never automate unclear processes - otherwise you're just making errors expensive and fast
- Before introducing automation, confirm: requirements are reasonable, no unnecessary steps, design simplified
- Value of automation: Increase capacity, reduce variation - not to mask poor process design
- Remove in-process testing once high acceptance rates are achieved
- Any automation station that proves to be executing unnecessary work should be deleted
- Automate the boring, repetitive tasks once the process is proven stable

---

## Key Principles

> "The best part is no part. The best process is no process."

> "If you're not occasionally adding things back in 10% of the time, you're clearly not deleting enough."

> "The most common error of a smart engineer is to optimize a thing that should not exist."

---

## Sequence is Critical

**The sequence is critical** - each step must be completed before moving to the next. Musk emphasizes repeating these steps "to an annoying degree" in meetings.

---

## Application

See [Market Pulse Design Principles](../features/marketpulse/design-principles.md) for application example.

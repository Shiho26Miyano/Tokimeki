/**
 * Decision Reflection Dashboard
 * Converts bad market events into reusable trading principles
 * Vanilla JS implementation (converted from React)
 */

class DecisionReflectionDashboard {
    constructor() {
        console.log('DecisionReflectionDashboard constructor called');
        
        // Preset scenarios
        this.presets = [
            {
                id: "macro_event",
                label: "Macro event misplay",
                angerThought: "CPI spiked, I panicked and flipped positions at the worst time.",
                value: "Macro interpretation & timing",
                trigger: "Reacted to headline instead of plan",
                goal: "Trade macro releases only with predefined scenarios",
                nextStep: "Write CPI scenario matrix before next release",
                boundary: "No position changes within first 5 minutes post-release",
            },
            {
                id: "earnings",
                label: "Earnings overreaction",
                angerThought: "Stock beat earnings but I exited too early out of fear.",
                value: "Conviction & process trust",
                trigger: "Fear of giving back gains",
                goal: "Hold through earnings when thesis intact",
                nextStep: "Define earnings hold rules in playbook",
                boundary: "No discretionary exit without thesis break",
            },
            {
                id: "drawdown",
                label: "Drawdown spiral",
                angerThought: "After two losses, I revenge traded and doubled the drawdown.",
                value: "Risk control & emotional discipline",
                trigger: "Loss-induced urgency",
                goal: "Stop trading after max daily loss",
                nextStep: "Set hard daily loss limit in platform",
                boundary: "No trades after hitting daily max loss",
            },
        ];
        
        // State
        this.intensity = 62;
        this.presetId = "macro_event";
        this.preset = this.presets.find(p => p.id === this.presetId) || this.presets[0];
        
        this.angerThought = this.preset.angerThought;
        this.value = this.preset.value;
        this.trigger = this.preset.trigger;
        this.goal = this.preset.goal;
        this.nextStep = this.preset.nextStep;
        this.boundary = this.preset.boundary;
        
        this.step = 1;
        this.mode = "with"; // "with" | "without"
        this.data = [];
        this.score = 0;
        
        // Chart instances
        this.trajectoryChart = null;
        this.recoveryChart = null;
        
        this.init();
    }
    
    clamp(n, a, b) {
        return Math.max(a, Math.min(b, n));
    }
    
    scoreLabel(n) {
        if (n < 25) return "Low";
        if (n < 55) return "Moderate";
        if (n < 80) return "High";
        return "Very High";
    }
    
    async init() {
        console.log('Initializing Decision Reflection Dashboard...');
        this.container = document.getElementById('decision-reflection-dashboard');
        if (!this.container) {
            console.error('Decision reflection dashboard container not found');
            return;
        }
        
        await this.loadTrajectoryData();
        this.render();
        // Event listeners are set up in render() after DOM is ready
    }
    
    async loadTrajectoryData() {
        try {
            console.log(`Loading trajectory data: intensity=${this.intensity}, mode=${this.mode}`);
            const url = `/api/v1/decision-reflection/trajectory?intensity=${this.intensity}&days=14&mode=${this.mode}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${await response.text()}`);
            }
            
            const result = await response.json();
            console.log('Trajectory data loaded:', result);
            
            this.data = result.data.map(day => ({
                day: `D${day.day}`,
                without_rumination: day.without_rumination,
                without_focus: day.without_focus,
                without_effort: day.without_effort,
                without_recovery: day.without_recovery,
                with_rumination: day.with_rumination,
                with_focus: day.with_focus,
                with_effort: day.with_effort,
                with_recovery: day.with_recovery,
            }));
            
            this.score = result.score;
            
        } catch (error) {
            console.error('Error loading trajectory data:', error);
            // Fallback to client-side computation
            this.data = this.buildData(this.intensity, 14);
            this.score = this.calculateScore();
        }
    }
    
    buildData(intensity, days = 14) {
        const base = this.clamp(intensity / 100, 0, 1);
        const data = [];
        let rum = 0.35 + base * 0.45;
        let eff = 0.25 + base * 0.35;
        let focus = 0.15 + base * 0.25;
        
        for (let i = 0; i < days; i++) {
            const t = i / (days - 1);
            
            const without_rumination = this.clamp(rum + 0.12 * Math.sin(6 * t) + 0.08 * (1 - t), 0, 1);
            const without_focus = this.clamp(focus + 0.06 * Math.sin(9 * t) - 0.05 * t, 0, 1);
            const without_effort = this.clamp(eff + 0.08 * Math.sin(7 * t) - 0.02, 0, 1);
            
            const with_rumination = this.clamp(rum * (1 - 0.55 * t) - 0.04 * Math.sin(5 * t), 0, 1);
            const with_focus = this.clamp(focus + 0.55 * t - 0.03 * Math.sin(6 * t), 0, 1);
            const with_effort = this.clamp(eff + 0.35 * t - 0.02 * Math.sin(7 * t), 0, 1);
            
            const with_recovery = this.clamp(0.35 + 0.55 * t - 0.25 * with_rumination, 0, 1);
            const without_recovery = this.clamp(0.25 + 0.25 * t - 0.35 * without_rumination, 0, 1);
            
            data.push({
                day: `D${i + 1}`,
                without_rumination: Math.round(without_rumination * 100),
                without_focus: Math.round(without_focus * 100),
                without_effort: Math.round(without_effort * 100),
                without_recovery: Math.round(without_recovery * 100),
                with_rumination: Math.round(with_rumination * 100),
                with_focus: Math.round(with_focus * 100),
                with_effort: Math.round(with_effort * 100),
                with_recovery: Math.round(with_recovery * 100),
            });
            
            rum = this.clamp(rum - 0.01, 0, 1);
            eff = this.clamp(eff + 0.004, 0, 1);
            focus = this.clamp(focus + 0.003, 0, 1);
        }
        
        return data;
    }
    
    calculateScore() {
        if (!this.data || this.data.length === 0) return 0;
        
        const last = this.data[this.data.length - 1];
        const focus = last[`${this.mode}_focus`];
        const effort = last[`${this.mode}_effort`];
        const recovery = last[`${this.mode}_recovery`];
        const rumination = last[`${this.mode}_rumination`];
        
        const raw = (
            0.35 * focus +
            0.3 * effort +
            0.25 * recovery -
            0.35 * rumination +
            0.15 * this.intensity
        );
        
        return this.clamp(Math.round(raw), 0, 100);
    }
    
    setupEventListeners() {
        // Intensity slider
        const intensitySlider = this.container.querySelector('#intensity-slider');
        if (intensitySlider) {
            intensitySlider.addEventListener('input', (e) => {
                this.intensity = parseInt(e.target.value, 10);
                this.updateIntensityDisplay();
                this.loadTrajectoryData().then(() => {
                    this.updateCharts();
                    this.updateScore();
                });
            });
        }
        
        // Mode toggle
        const reflectBtn = this.container.querySelector('#mode-reflect');
        const ignoreBtn = this.container.querySelector('#mode-ignore');
        if (reflectBtn) {
            reflectBtn.addEventListener('click', () => {
                this.mode = "with";
                this.updateModeButtons();
                this.loadTrajectoryData().then(() => {
                    this.updateCharts();
                    this.updateScore();
                });
            });
        }
        if (ignoreBtn) {
            ignoreBtn.addEventListener('click', () => {
                this.mode = "without";
                this.updateModeButtons();
                this.loadTrajectoryData().then(() => {
                    this.updateCharts();
                    this.updateScore();
                });
            });
        }
        
        // Preset buttons
        this.presets.forEach(preset => {
            const btn = this.container.querySelector(`#preset-${preset.id}`);
            if (btn) {
                btn.addEventListener('click', () => {
                    this.loadPreset(preset.id);
                });
            }
        });
        
        // Step buttons
        [1, 2, 3].forEach(stepNum => {
            const btn = this.container.querySelector(`#step-${stepNum}`);
            if (btn) {
                btn.addEventListener('click', () => {
                    this.step = stepNum;
                    this.updateStepButtons();
                });
            }
        });
        
        // Next button
        const nextBtn = this.container.querySelector('#next-btn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.step = this.clamp(this.step + 1, 1, 3);
                this.updateStepButtons();
            });
        }
        
        // Reset button
        const resetBtn = this.container.querySelector('#reset-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.mode = "with";
                this.step = 1;
                this.updateModeButtons();
                this.updateStepButtons();
                this.loadTrajectoryData().then(() => {
                    this.updateCharts();
                    this.updateScore();
                });
            });
        }
        
        // Transformation view button
        const transformBtn = this.container.querySelector('#transform-btn');
        if (transformBtn) {
            transformBtn.addEventListener('click', () => {
                this.mode = "with";
                this.step = 3;
                this.updateModeButtons();
                this.updateStepButtons();
            });
        }
        
        // Form inputs
        const inputs = ['angerThought', 'value', 'trigger', 'goal', 'nextStep', 'boundary'];
        inputs.forEach(field => {
            const input = this.container.querySelector(`#input-${field}`);
            if (input) {
                input.addEventListener('input', (e) => {
                    this[field] = e.target.value;
                    this.updateSummary();
                });
            }
        });
    }
    
    loadPreset(presetId) {
        const preset = this.presets.find(p => p.id === presetId) || this.presets[0];
        this.presetId = presetId;
        this.preset = preset;
        this.angerThought = preset.angerThought;
        this.value = preset.value;
        this.trigger = preset.trigger;
        this.goal = preset.goal;
        this.nextStep = preset.nextStep;
        this.boundary = preset.boundary;
        this.step = 1;
        
        this.updatePresetButtons();
        this.updateFormInputs();
        this.updateStepButtons();
        this.updateSummary();
    }
    
    updateIntensityDisplay() {
        const display = this.container.querySelector('#intensity-value');
        if (display) {
            display.textContent = this.intensity;
        }
    }
    
    updateModeButtons() {
        const reflectBtn = this.container.querySelector('#mode-reflect');
        const ignoreBtn = this.container.querySelector('#mode-ignore');
        if (reflectBtn && ignoreBtn) {
            if (this.mode === "with") {
                reflectBtn.classList.remove('btn-light');
                reflectBtn.classList.add('btn-dark');
                ignoreBtn.classList.remove('btn-dark');
                ignoreBtn.classList.add('btn-light');
            } else {
                reflectBtn.classList.remove('btn-dark');
                reflectBtn.classList.add('btn-light');
                ignoreBtn.classList.remove('btn-light');
                ignoreBtn.classList.add('btn-dark');
            }
        }
    }
    
    updatePresetButtons() {
        this.presets.forEach(preset => {
            const btn = this.container.querySelector(`#preset-${preset.id}`);
            if (btn) {
                if (preset.id === this.presetId) {
                    btn.classList.remove('btn-light');
                    btn.classList.add('btn-dark');
                } else {
                    btn.classList.remove('btn-dark');
                    btn.classList.add('btn-light');
                }
            }
        });
    }
    
    updateStepButtons() {
        [1, 2, 3].forEach(stepNum => {
            const btn = this.container.querySelector(`#step-${stepNum}`);
            if (btn) {
                if (stepNum === this.step) {
                    btn.classList.remove('btn-light');
                    btn.classList.add('btn-dark');
                } else {
                    btn.classList.remove('btn-dark');
                    btn.classList.add('btn-light');
                }
            }
        });
        
        // Update step content visibility - highlight active step
        [1, 2, 3].forEach(stepNum => {
            const stepContent = this.container.querySelector(`#step-content-${stepNum}`);
            if (stepContent) {
                if (stepNum === this.step) {
                    stepContent.classList.add('ring-2');
                    stepContent.classList.add('ring-neutral-900');
                } else {
                    stepContent.classList.remove('ring-2');
                    stepContent.classList.remove('ring-neutral-900');
                }
            }
        });
    }
    
    updateFormInputs() {
        const inputs = {
            'angerThought': this.angerThought,
            'value': this.value,
            'trigger': this.trigger,
            'goal': this.goal,
            'nextStep': this.nextStep,
            'boundary': this.boundary
        };
        
        Object.entries(inputs).forEach(([field, value]) => {
            const input = this.container.querySelector(`#input-${field}`);
            if (input) {
                input.value = value;
            }
        });
    }
    
    updateScore() {
        const scoreDisplay = this.container.querySelector('#score-value');
        if (scoreDisplay) {
            scoreDisplay.textContent = this.score;
        }
        
        const headline = this.container.querySelector('#headline');
        if (headline) {
            const label = this.scoreLabel(this.score);
            if (this.mode === "without") {
                headline.textContent = `Ignore reflection → ${label} decision quality`;
            } else {
                headline.textContent = `Reflect & upgrade rules → ${label} decision quality`;
            }
        }
    }
    
    updateSummary() {
        const summary = this.container.querySelector('#principle-summary');
        if (summary) {
            summary.innerHTML = `
                <div class="d-flex align-items-start gap-2">
                    <i class="fas fa-check-circle mt-1"></i>
                    <span><strong>Decision failure:</strong> ${this.value}</span>
                </div>
                <div class="d-flex align-items-start gap-2">
                    <i class="fas fa-check-circle mt-1"></i>
                    <span><strong>Trading principle:</strong> ${this.goal}</span>
                </div>
                <div class="d-flex align-items-start gap-2">
                    <i class="fas fa-check-circle mt-1"></i>
                    <span><strong>Next step:</strong> ${this.nextStep}</span>
                </div>
                <div class="d-flex align-items-start gap-2">
                    <i class="fas fa-check-circle mt-1"></i>
                    <span><strong>Risk constraint:</strong> ${this.boundary}</span>
                </div>
            `;
        }
    }
    
    updateCharts() {
        this.renderTrajectoryChart();
        this.renderRecoveryChart();
    }
    
    renderTrajectoryChart() {
        const canvas = this.container.querySelector('#trajectory-chart');
        if (!canvas || typeof Chart === 'undefined') {
            console.warn('Trajectory chart canvas or Chart.js not available');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart
        if (this.trajectoryChart) {
            this.trajectoryChart.destroy();
        }
        
        const focusKey = `${this.mode}_focus`;
        const ruminationKey = `${this.mode}_rumination`;
        const effortKey = `${this.mode}_effort`;
        
        this.trajectoryChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.data.map(d => d.day),
                datasets: [
                    {
                        label: 'Decision Clarity (plan adherence)',
                        data: this.data.map(d => d[focusKey]),
                        borderColor: '#16a34a',
                        backgroundColor: 'rgba(22, 163, 74, 0.1)',
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 0,
                    },
                    {
                        label: 'Error Carryover (revenge risk)',
                        data: this.data.map(d => d[ruminationKey]),
                        borderColor: '#dc2626',
                        borderDash: [6, 4],
                        backgroundColor: 'rgba(220, 38, 38, 0.1)',
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 0,
                    },
                    {
                        label: 'Discipline (rule execution)',
                        data: this.data.map(d => d[effortKey]),
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                        },
                    },
                },
            },
        });
    }
    
    renderRecoveryChart() {
        const canvas = this.container.querySelector('#recovery-chart');
        if (!canvas || typeof Chart === 'undefined') {
            console.warn('Recovery chart canvas or Chart.js not available');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart
        if (this.recoveryChart) {
            this.recoveryChart.destroy();
        }
        
        const recoveryKey = `${this.mode}_recovery`;
        
        this.recoveryChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.data.map(d => d.day),
                datasets: [
                    {
                        label: 'Recovery',
                        data: this.data.map(d => d[recoveryKey]),
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.35)',
                        tension: 0.4,
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                        },
                    },
                },
            },
        });
    }
    
    render() {
        if (!this.container) return;
        
        const headline = this.mode === "without" 
            ? `Ignore reflection → ${this.scoreLabel(this.score)} decision quality`
            : `Reflect & upgrade rules → ${this.scoreLabel(this.score)} decision quality`;
        
        this.container.innerHTML = `
            <div class="decision-reflection-container" style="min-height: 100vh; background: #fafafa; padding: 1.5rem 1rem; width: 100%;">
                <div class="container-fluid" style="max-width: 1100px; margin: 0 auto; width: 100%;">
                    <!-- Header -->
                    <div class="row mb-3">
                        <div class="col-12">
                            <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-end gap-3">
                                <div style="flex: 1;">
                                    <div class="d-inline-flex align-items-center gap-2 rounded-pill bg-white border px-3 py-1 mb-1" style="font-size: 0.7rem; font-weight: 500;">
                                        <span>🔥</span>
                                        <span>Pain → Reflection → Progress (Trader / Investor Demo)</span>
                                    </div>
                                    <h1 class="h3 fw-semibold mb-1" style="font-size: 1.5rem; line-height: 1.2; color: #1a1a1a;">
                                        Turn pain into <span style="text-decoration: underline; text-decoration-color: rgba(0,0,0,0.2);">better decisions & PnL</span>
                                    </h1>
                                    <p class="text-muted mb-0" style="font-size: 0.8rem; max-width: 500px; line-height: 1.3;">
                                        This is a tiny interactive story: you start with a painful trading or investing experience, then choose whether to ignore it (react & repeat) or reflect on it (diagnose & improve decisions).
                                    </p>
                                </div>
                                
                                <div class="d-flex flex-column flex-sm-row gap-2" style="flex-shrink: 0;">
                                    <div class="rounded-2xl border bg-white p-2 shadow-sm" style="border-radius: 0.75rem;">
                                        <div class="text-xs fw-medium text-muted mb-1" style="font-size: 0.65rem;">Scenario</div>
                                        <div class="d-flex flex-wrap gap-1">
                                            ${this.presets.map(preset => `
                                                <button 
                                                    id="preset-${preset.id}"
                                                    class="btn btn-sm rounded-pill border-0 ${preset.id === this.presetId ? 'btn-dark' : 'btn-light'}"
                                                    style="font-size: 0.7rem; padding: 0.2rem 0.6rem; font-weight: 500;"
                                                >
                                                    ${preset.label}
                                                </button>
                                            `).join('')}
                                        </div>
                                    </div>
                                    
                                    <div class="rounded-2xl border bg-white p-2 shadow-sm" style="border-radius: 0.75rem;">
                                        <div class="text-xs fw-medium text-muted mb-1" style="font-size: 0.65rem;">Mode</div>
                                        <div class="d-flex gap-1">
                                            <button 
                                                id="mode-reflect"
                                                class="btn btn-sm rounded-pill border-0 ${this.mode === 'with' ? 'btn-dark' : 'btn-light'}"
                                                style="font-size: 0.7rem; padding: 0.2rem 0.6rem; font-weight: 500;"
                                            >
                                                Reflect
                                            </button>
                                            <button 
                                                id="mode-ignore"
                                                class="btn btn-sm rounded-pill border-0 ${this.mode === 'without' ? 'btn-dark' : 'btn-light'}"
                                                style="font-size: 0.7rem; padding: 0.2rem 0.6rem; font-weight: 500;"
                                            >
                                                Ignore
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Intensity + Score -->
                    <div class="row mb-3 g-3">
                        <div class="col-12 col-md-4">
                            <div class="rounded-2xl border bg-white p-4 shadow-sm" style="border-radius: 1.25rem;">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <div style="flex: 1;">
                                        <div class="fw-semibold mb-1" style="font-size: 0.875rem;">Decision impact intensity</div>
                                        <div class="text-muted small" style="font-size: 0.75rem;">How much did this event negatively impact your PnL or decision quality?</div>
                                    </div>
                                    <div class="d-inline-flex align-items-center gap-2 rounded-pill border bg-light px-2 py-1 shadow-sm" style="flex-shrink: 0;">
                                        <i class="fas fa-bolt" style="font-size: 0.75rem;"></i>
                                        <span class="fw-semibold" id="intensity-value" style="font-size: 0.875rem;">${this.intensity}</span>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <input 
                                        type="range" 
                                        id="intensity-slider"
                                        class="form-range" 
                                        min="0" 
                                        max="100" 
                                        value="${this.intensity}"
                                        style="width: 100%;"
                                    />
                                    <div class="d-flex justify-content-between text-muted small mt-1" style="font-size: 0.7rem;">
                                        <span>0 no impact</span>
                                        <span>100 severe pain</span>
                                    </div>
                                </div>
                                
                                <div class="d-flex flex-column gap-2">
                                    <div class="d-flex align-items-start gap-2 rounded border bg-white p-2 shadow-sm">
                                        <div class="rounded border bg-white p-1.5 shadow-sm" style="padding: 0.4rem;">
                                            <i class="fas fa-brain" style="font-size: 0.75rem;"></i>
                                        </div>
                                        <div>
                                            <div class="small fw-semibold" style="font-size: 0.75rem;">What a bad decision really is</div>
                                            <div class="small text-muted" style="font-size: 0.7rem; line-height: 1.3;">A feedback signal that your decision process broke under pressure. The problem isn't the loss — it's whether the process improves.</div>
                                        </div>
                                    </div>
                                    <div class="d-flex align-items-start gap-2 rounded border bg-white p-2 shadow-sm">
                                        <div class="rounded border bg-white p-1.5 shadow-sm" style="padding: 0.4rem;">
                                            <i class="fas fa-shield-alt" style="font-size: 0.75rem;"></i>
                                        </div>
                                        <div>
                                            <div class="small fw-semibold" style="font-size: 0.75rem;">Investor move</div>
                                            <div class="small text-muted" style="font-size: 0.7rem; line-height: 1.3;">Convert feedback into: (1) diagnosis (2) principle (3) future constraint.</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-12 col-md-8">
                            <div class="rounded-2xl border bg-white p-4 shadow-sm" style="border-radius: 1.25rem;">
                                <div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-2 mb-3">
                                    <div style="flex: 1;">
                                        <div class="fw-semibold mb-1" id="headline" style="font-size: 0.8rem;">${headline}</div>
                                        <div class="text-muted small" style="font-size: 0.7rem; line-height: 1.3;">
                                            A simplified metric: higher clarity, disciplined action, and system resilience — lower repeated mistakes.
                                        </div>
                                    </div>
                                    <div class="d-flex align-items-center gap-2" style="flex-shrink: 0;">
                                        <div class="rounded-2xl border bg-neutral-50 px-3 py-2 shadow-sm" style="background: #f5f5f5;">
                                            <div class="text-xs fw-medium text-muted mb-0" style="font-size: 0.65rem;">Decision Quality Score</div>
                                            <div class="text-2xl fw-semibold" id="score-value" style="font-size: 1.5rem;">${this.score}</div>
                                        </div>
                                        <button 
                                            id="reset-btn"
                                            class="btn btn-outline-secondary rounded-2xl border shadow-sm px-3 py-2"
                                            style="font-size: 0.75rem;"
                                        >
                                            <i class="fas fa-redo"></i> Reset
                                        </button>
                                    </div>
                                </div>
                                
                                <div class="row g-3">
                                    <div class="col-12 col-md-6">
                                        <div class="rounded-2xl border bg-neutral-50 p-3" style="background: #f5f5f5; border-radius: 0.75rem;">
                                            <div class="text-xs fw-semibold text-muted mb-2" style="font-size: 0.65rem;">Decision trajectory after a bad trade (14 sessions)</div>
                                            <div style="height: 160px; position: relative;">
                                                <canvas id="trajectory-chart"></canvas>
                                            </div>
                                            <div class="text-xs text-muted mt-2" style="font-size: 0.65rem; line-height: 1.3;">
                                                Green line should rise, red line should fall. Toggle Reflect vs Ignore to see whether mistakes decay or compound.
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="col-12 col-md-6">
                                        <div class="rounded-2xl border bg-neutral-50 p-3" style="background: #f5f5f5; border-radius: 0.75rem;">
                                            <div class="text-xs fw-semibold text-muted mb-2" style="font-size: 0.65rem;">Recovery (ability to bounce back)</div>
                                            <div style="height: 160px; position: relative;">
                                                <canvas id="recovery-chart"></canvas>
                                            </div>
                                            <div class="text-xs text-muted mt-2" style="font-size: 0.65rem; line-height: 1.3;">
                                                More recovery = you can act with steadiness instead of spiraling.
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- The 3-step converter -->
                    <div class="mb-3">
                        <div class="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-end gap-2 mb-3">
                            <div style="flex: 1;">
                                <h2 class="h5 fw-semibold mb-1" style="font-size: 1.1rem;">The engine: Event → Decision → Diagnosis → Principle</h2>
                                <p class="text-muted small mb-0" style="font-size: 0.75rem; max-width: 500px; line-height: 1.3;">
                                    Your demo moment: show that pain becomes progress when it's systematically reflected and turned into principles.
                                </p>
                            </div>
                            <div class="d-flex gap-2" style="flex-shrink: 0;">
                                ${[1, 2, 3].map(n => `
                                    <button 
                                        id="step-${n}"
                                        class="btn rounded-pill border shadow-sm ${n === this.step ? 'btn-dark' : 'btn-light'}"
                                        style="padding: 0.4rem 0.9rem; font-size: 0.8rem; font-weight: 500;"
                                    >
                                        Step ${n}
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                        
                        <div class="row g-3 mb-3">
                            ${this.renderStep(1)}
                            ${this.renderStep(2)}
                            ${this.renderStep(3)}
                        </div>
                        
                        <!-- Output card -->
                        <div class="rounded-2xl border bg-white p-4 shadow-sm" style="border-radius: 1.25rem;">
                            <div class="d-flex flex-column flex-md-row justify-content-between align-items-start gap-3">
                                <div style="flex: 1;">
                                    <div class="d-inline-flex align-items-center gap-2 rounded-pill border bg-neutral-50 px-2 py-1 shadow-sm mb-2" style="font-size: 0.7rem; font-weight: 500;">
                                        <i class="fas fa-bullseye" style="font-size: 0.7rem;"></i>
                                        <span>Your Trading Principle</span>
                                    </div>
                                    <div class="d-flex flex-column gap-2 small" id="principle-summary" style="font-size: 0.8rem;">
                                        ${this.getSummaryHTML()}
                                    </div>
                                </div>
                                
                                <div class="d-flex flex-column gap-2" style="flex-shrink: 0;">
                                    <button 
                                        id="next-btn"
                                        class="btn btn-dark rounded-2xl shadow-sm px-4 py-2"
                                        style="font-size: 0.8rem; font-weight: 500;"
                                    >
                                        Next <i class="fas fa-arrow-right"></i>
                                    </button>
                                    <button 
                                        id="transform-btn"
                                        class="btn btn-outline-secondary rounded-2xl border shadow-sm px-4 py-2"
                                        style="font-size: 0.8rem; font-weight: 500;"
                                    >
                                        Show the transformation view
                                    </button>
                                </div>
                            </div>
                            
                            <div class="rounded-2xl border bg-neutral-50 p-3 mt-3" style="background: #f5f5f5; border-radius: 0.75rem;">
                                <div class="text-xs fw-semibold text-muted mb-1" style="font-size: 0.65rem;">Demo script (30 seconds)</div>
                                <div class="small text-muted" style="font-size: 0.75rem; line-height: 1.4;">
                                    Here's the same market event. One trader reacts and compounds losses. Another trader reflects, diagnoses the decision failure, and extracts a principle. That principle changes future behavior. The event doesn't matter — the decision process does.
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div class="rounded-2xl border bg-white p-3 shadow-sm" style="border-radius: 1.25rem;">
                        <div class="d-flex flex-column flex-md-row justify-content-between align-items-center gap-2 small text-muted" style="font-size: 0.8rem;">
                            <div class="d-flex align-items-center gap-2">
                                <i class="fas fa-fire" style="font-size: 0.75rem;"></i>
                                <span>Reminder: this is a decision‑reflection tool, not financial advice. Markets involve risk.</span>
                            </div>
                            <div class="text-xs" style="font-size: 0.7rem;">Built as a lightweight narrative + interactive metrics.</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Update form inputs
        this.updateFormInputs();
        
        // Re-attach event listeners after DOM is updated
        // Use a small delay to ensure DOM is fully rendered
        setTimeout(() => {
            this.setupEventListeners();
            this.updateCharts();
            this.updateScore();
            this.updateModeButtons();
            this.updatePresetButtons();
            this.updateStepButtons();
        }, 50);
    }
    
    renderStep(stepNum) {
        const isActive = stepNum === this.step;
        const activeClass = isActive ? 'ring-2 ring-neutral-900' : '';
        
        if (stepNum === 1) {
            return `
                <div class="col-12 col-md-4">
                    <div class="rounded-2xl border bg-white/70 p-4 shadow-sm backdrop-blur ${activeClass}" style="border-radius: 0.75rem; background: rgba(255,255,255,0.7);" id="step-content-${stepNum}">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="d-flex align-items-center gap-2">
                                <div class="d-flex h-9 w-9 align-items-center justify-content-center rounded-xl border bg-white shadow-sm" style="width: 32px; height: 32px;">
                                    <span class="small fw-semibold" style="font-size: 0.75rem;">1</span>
                                </div>
                                <div class="text-base fw-semibold" style="font-size: 0.875rem;">Describe the trading or investment event (facts only)</div>
                            </div>
                            ${isActive ? `
                                <span class="badge bg-primary text-white px-3 py-1 rounded-pill">
                                    <i class="fas fa-sparkles"></i> Active
                                </span>
                            ` : ''}
                        </div>
                        <div class="text-xs fw-semibold text-neutral-500 mb-1" style="font-size: 0.7rem;">What market event occurred and what decision did you make</div>
                        <textarea 
                            id="input-angerThought"
                            rows="3"
                            class="form-control rounded-2xl border bg-white p-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-neutral-900 mb-2"
                            style="font-size: 0.8rem; padding: 0.6rem; border-radius: 0.75rem;"
                            placeholder="What happened in the market, and what action did you take? No judgment, just facts."
                        >${this.angerThought}</textarea>
                        <div class="mt-2 text-xs text-neutral-600" style="font-size: 0.7rem;">
                            Rule: describe observable facts only. No blame, no excuses.
                        </div>
                    </div>
                </div>
            `;
        } else if (stepNum === 2) {
            return `
                <div class="col-12 col-md-4">
                    <div class="rounded-2xl border bg-white/70 p-4 shadow-sm backdrop-blur ${activeClass}" style="border-radius: 0.75rem; background: rgba(255,255,255,0.7);" id="step-content-${stepNum}">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="d-flex align-items-center gap-2">
                                <div class="d-flex h-9 w-9 align-items-center justify-content-center rounded-xl border bg-white shadow-sm" style="width: 32px; height: 32px;">
                                    <span class="small fw-semibold" style="font-size: 0.75rem;">2</span>
                                </div>
                                <div class="text-base fw-semibold" style="font-size: 0.875rem;">Diagnose the decision failure</div>
                            </div>
                            ${isActive ? `
                                <span class="d-inline-flex align-items-center gap-1 rounded-full border bg-white px-2 py-1 text-xs fw-medium shadow-sm" style="font-size: 0.65rem;">
                                    <i class="fas fa-sparkles" style="font-size: 0.7rem;"></i> Active
                                </span>
                            ` : ''}
                        </div>
                        <div class="d-flex flex-column gap-2">
                            <div>
                                <div class="text-xs fw-semibold text-neutral-500 mb-1" style="font-size: 0.7rem;">What specifically failed in your trading or investment process?</div>
                                <input 
                                    id="input-value"
                                    type="text"
                                    class="form-control rounded-2xl border bg-white p-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-neutral-900"
                                    style="font-size: 0.8rem; padding: 0.6rem; border-radius: 0.75rem;"
                                    placeholder="e.g., fairness, respect, safety, autonomy, recognition"
                                    value="${this.value}"
                                />
                            </div>
                            <div>
                                <div class="text-xs fw-semibold text-neutral-500 mb-1" style="font-size: 0.7rem;">Primary root cause</div>
                                <input 
                                    id="input-trigger"
                                    type="text"
                                    class="form-control rounded-2xl border bg-white p-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-neutral-900"
                                    style="font-size: 0.8rem; padding: 0.6rem; border-radius: 0.75rem;"
                                    placeholder="e.g., being ignored, feeling unsafe, losing control"
                                    value="${this.trigger}"
                                />
                            </div>
                        </div>
                        <div class="mt-2 text-xs text-neutral-600" style="font-size: 0.7rem;">
                            If you can diagnose the cause, you can redesign the process.
                        </div>
                    </div>
                </div>
            `;
        } else {
            return `
                <div class="col-12 col-md-4">
                    <div class="rounded-2xl border bg-white/70 p-4 shadow-sm backdrop-blur ${activeClass}" style="border-radius: 0.75rem; background: rgba(255,255,255,0.7);" id="step-content-${stepNum}">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="d-flex align-items-center gap-2">
                                <div class="d-flex h-9 w-9 align-items-center justify-content-center rounded-xl border bg-white shadow-sm" style="width: 32px; height: 32px;">
                                    <span class="small fw-semibold" style="font-size: 0.75rem;">3</span>
                                </div>
                                <div class="text-base fw-semibold" style="font-size: 0.875rem;">Extract a trading principle</div>
                            </div>
                            ${isActive ? `
                                <span class="d-inline-flex align-items-center gap-1 rounded-full border bg-white px-2 py-1 text-xs fw-medium shadow-sm" style="font-size: 0.65rem;">
                                    <i class="fas fa-sparkles" style="font-size: 0.7rem;"></i> Active
                                </span>
                            ` : ''}
                        </div>
                        <div class="d-flex flex-column gap-2">
                            <div>
                                <div class="text-xs fw-semibold text-neutral-500 mb-1" style="font-size: 0.7rem;">Trading / investment principle</div>
                                <input 
                                    id="input-goal"
                                    type="text"
                                    class="form-control rounded-2xl border bg-white p-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-neutral-900"
                                    style="font-size: 0.8rem; padding: 0.6rem; border-radius: 0.75rem;"
                                    placeholder="A rule that would prevent this mistake next time"
                                    value="${this.goal}"
                                />
                            </div>
                            <div>
                                <div class="text-xs fw-semibold text-neutral-500 mb-1" style="font-size: 0.7rem;">Immediate application</div>
                                <input 
                                    id="input-nextStep"
                                    type="text"
                                    class="form-control rounded-2xl border bg-white p-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-neutral-900"
                                    style="font-size: 0.8rem; padding: 0.6rem; border-radius: 0.75rem;"
                                    placeholder="Action you can do today"
                                    value="${this.nextStep}"
                                />
                            </div>
                            <div>
                                <div class="text-xs fw-semibold text-neutral-500 mb-1" style="font-size: 0.7rem;">Future constraint</div>
                                <input 
                                    id="input-boundary"
                                    type="text"
                                    class="form-control rounded-2xl border bg-white p-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-neutral-900"
                                    style="font-size: 0.8rem; padding: 0.6rem; border-radius: 0.75rem;"
                                    placeholder="What you will / won't tolerate"
                                    value="${this.boundary}"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    getSummaryHTML() {
        return `
            <div class="d-flex align-items-start gap-2 mb-1">
                <i class="fas fa-check-circle" style="margin-top: 2px; font-size: 0.75rem;"></i>
                <span style="font-size: 0.8rem;">
                    <span class="fw-semibold">Decision failure:</span> ${this.value || ''}
                </span>
            </div>
            <div class="d-flex align-items-start gap-2 mb-1">
                <i class="fas fa-check-circle" style="margin-top: 2px; font-size: 0.75rem;"></i>
                <span style="font-size: 0.8rem;">
                    <span class="fw-semibold">Trading principle:</span> ${this.goal || ''}
                </span>
            </div>
            <div class="d-flex align-items-start gap-2 mb-1">
                <i class="fas fa-check-circle" style="margin-top: 2px; font-size: 0.75rem;"></i>
                <span style="font-size: 0.8rem;">
                    <span class="fw-semibold">Next step:</span> ${this.nextStep || ''}
                </span>
            </div>
            <div class="d-flex align-items-start gap-2">
                <i class="fas fa-check-circle" style="margin-top: 2px; font-size: 0.75rem;"></i>
                <span style="font-size: 0.8rem;">
                    <span class="fw-semibold">Risk constraint:</span> ${this.boundary || ''}
                </span>
            </div>
        `;
    }
}

// Make it globally available
window.DecisionReflectionDashboard = DecisionReflectionDashboard;


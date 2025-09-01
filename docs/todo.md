# TODO List

## 20250817 - Build a new tab for Highlight: Dynamic ML-Based Strategy from March 2025

**Title:** Dynamic Investment Strategies Through Market Classification and Volatility: A Machine Learning Approach  
**Authors:** Jinhui Li, Wenjia Xie, Luis Seco  
**Published:** March 19, 2025  
**Source:** arXiv  

### Strategy Summary

**Core idea:** Rather than relying on static portfolio rules, this strategy adapts to real-time market states driven by volatility regimes.

**How it works:**

- Use K-means clustering to segment market conditions into ~10 different volatility-based regimes
- Model regime transitions using a Bayesian Markov-switching model with Dirichlet priors and Gibbs sampling
- Based on the current regime, dynamically adjust portfolio weights using portfolio optimization techniques (e.g., risk parity, minimum variance, maximum diversification, etc.)

**Results:** In backtests, this dynamic, regime-aware strategy consistently outperforms static portfolio approaches in both returns and risk-adjusted metrics.

### Implementation Tasks

- [ ] Create new tab interface for Dynamic ML Strategy
- [ ] Implement K-means clustering for market regime classification
- [ ] Build Bayesian Markov-switching model with Dirichlet priors
- [ ] Integrate portfolio optimization algorithms (risk parity, minimum variance, maximum diversification)
- [ ] Develop real-time regime detection system
- [ ] Create dynamic portfolio rebalancing logic
- [ ] Add backtesting and performance comparison tools
- [ ] Design visualization for regime transitions and portfolio adjustments

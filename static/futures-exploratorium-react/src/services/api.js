const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1/futureexploratorium';

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'API request failed');
      }
      
      return data;
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }

  // Core endpoints
  async getHealthCheck() {
    return this.request('/core/health');
  }

  // Dashboard endpoints
  async getMarketOverview() {
    return this.request('/dashboard/market/overview');
  }

  async getPerformanceMetrics() {
    return this.request('/dashboard/performance');
  }

  async getRiskMetrics() {
    return this.request('/dashboard/risk');
  }

  async getChartData(symbol = 'ES=F', timeframe = '1d', limit = 100) {
    return this.request(`/dashboard/chart?symbol=${symbol}&timeframe=${timeframe}&limit=${limit}`);
  }

  // Strategy endpoints
  async runBacktest(symbols, startDate, endDate) {
    return this.request('/core/analysis/comprehensive', {
      method: 'POST',
      body: JSON.stringify({
        symbols,
        start_date: startDate,
        end_date: endDate,
        analysis_types: ['backtesting']
      })
    });
  }

  async getStrategyPerformance() {
    return this.request('/core/performance/summary');
  }
}

export default new ApiService();

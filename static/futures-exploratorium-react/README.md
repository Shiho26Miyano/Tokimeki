# Futures Exploratorium - React Frontend

A modern, dark-themed React frontend for the Futures Exploratorium trading platform. Built with React 18, Zustand for state management, and D3/Plotly for advanced charting.

## Features

### 🎨 Modern Dark Theme
- Clean, professional dark UI with cyan/orange accents
- Rounded cards with soft shadows and glassmorphism effects
- Responsive design that stacks beautifully on mobile devices

### 📊 Real-time Market Data
- Live futures prices for ES, NQ, and RTY
- Interactive sparklines showing price trends
- Click-to-expand detailed charts with multiple timeframes
- WebSocket integration for real-time updates

### 📈 Strategy Performance
- Real-time PnL, Sharpe ratio, and drawdown metrics
- Interactive equity curve visualization
- One-click backtest execution with configurable parameters
- Performance metrics with color-coded indicators

### ⚠️ Risk Management
- VaR (Value at Risk) calculations and alerts
- Volatility monitoring with threshold indicators
- Interactive correlation heatmap using Plotly
- Real-time risk alerts and notifications

### 🔔 Alerts & Activity Feed
- Live alerts with severity levels (High/Medium/Low/Info)
- Recent activity timeline with timestamps
- Filterable alert feed with dismiss functionality
- Real-time notifications via toast messages

### 📱 Responsive Design
- Mobile-first approach with adaptive layouts
- Touch-friendly interface elements
- Optimized for tablets and desktop screens
- Smooth animations and transitions

## Technology Stack

- **React 18** - Modern React with hooks and functional components
- **Zustand** - Lightweight state management
- **Styled Components** - CSS-in-JS styling
- **Framer Motion** - Smooth animations and transitions
- **Plotly.js** - Advanced charting and visualization
- **Recharts** - Lightweight chart components
- **React Hot Toast** - Beautiful notification system
- **Date-fns** - Date manipulation utilities

## Getting Started

### Prerequisites
- Node.js 16+ 
- npm or yarn
- Backend API running on port 8000

### Installation

1. Navigate to the React app directory:
```bash
cd static/futures-exploratorium-react
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.example .env.local
```

4. Configure environment variables:
```env
REACT_APP_API_URL=http://localhost:8000/api/v1/futureexploratorium
REACT_APP_WS_URL=ws://localhost:8000/ws
```

5. Start the development server:
```bash
npm start
```

The app will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## API Integration

The frontend connects to the following backend endpoints:

### Core Endpoints
- `GET /core/status` - System health status
- `GET /core/overview` - Platform overview
- `GET /core/health` - Health check
- `POST /core/analysis/comprehensive` - Run backtests

### Dashboard Endpoints
- `GET /dashboard/comprehensive` - Comprehensive dashboard data
- `GET /dashboard/market/overview` - Market data
- `GET /dashboard/performance` - Strategy performance
- `GET /dashboard/risk` - Risk metrics
- `GET /dashboard/alerts` - Alerts and notifications
- `GET /dashboard/activity` - Recent activity
- `GET /dashboard/chart` - Chart data

### WebSocket Events
- `market_data` - Real-time market price updates
- `alerts` - New alerts and notifications
- `performance` - Strategy performance updates
- `system_health` - System health status changes

## Component Architecture

```
src/
├── components/
│   ├── Header.js              # App header with health indicator
│   ├── MarketOverview.js      # Live market data with sparklines
│   ├── StrategyPerformance.js # PnL, metrics, and backtest
│   ├── RiskMetrics.js         # VaR, volatility, correlation
│   ├── AlertsFeed.js          # Alerts and activity feed
│   └── DetailedChart.js       # Expandable chart modal
├── store/
│   └── useStore.js            # Zustand state management
├── services/
│   ├── api.js                 # API service layer
│   └── websocket.js           # WebSocket service
└── App.js                     # Main application component
```

## State Management

The app uses Zustand for lightweight state management with the following stores:

- **systemHealth** - System status and health metrics
- **marketData** - Live market prices and sparklines
- **strategyPerformance** - PnL, Sharpe, drawdown, equity curve
- **riskMetrics** - VaR, volatility, correlation data
- **alerts** - Alert notifications
- **activity** - Recent activity feed
- **UI State** - Selected symbols, expanded views, connection status

## Styling

The app uses styled-components for all styling with:

- **Dark theme** with carefully chosen color palette
- **Gradient backgrounds** for visual depth
- **Glassmorphism effects** with backdrop blur
- **Responsive grid layouts** that adapt to screen size
- **Smooth animations** using Framer Motion
- **Consistent spacing** and typography

## Performance Optimizations

- **Lazy loading** for chart components
- **Memoized calculations** for expensive operations
- **Efficient re-renders** with proper dependency arrays
- **WebSocket connection pooling** to prevent memory leaks
- **Optimized bundle size** with tree shaking

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

### Code Style
- ESLint configuration for consistent code style
- Prettier for automatic code formatting
- Functional components with hooks
- TypeScript-ready structure

### Testing
```bash
npm test
```

### Linting
```bash
npm run lint
```

## Deployment

The app can be deployed to any static hosting service:

1. Build the production bundle:
```bash
npm run build
```

2. Deploy the `build` folder to your hosting service

3. Configure environment variables for production API endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Futures Exploratorium trading platform.

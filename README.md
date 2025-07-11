# Tokimeki

Tokimeki is a modern, interactive dashboard for exploring stock trends, volatility, and human sentiment analysis using real financial and social data.
An ongoing project exploring emerging technologies, open-source APIs, and modern frameworks to integrate AI/ML into real-world software development.

## Live Demo

[https://tokimeki-pro.up.railway.app/](https://tokimeki-pro.up.railway.app/)

## Demo

![Demo Screenshot](static/img/demo.png)

Demo Screenshot

## Features
- **Stock Price Trends**: Explore and compare the price trends of popular stocks and ETFs over the past month.
- **Largest Stock Price Change**: See which stock or ETF had the biggest price swings in a given period, with a ranking and details.

## Setup
1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Tokimeki
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the app:**
   ```bash
   python app.py
   ```
5. **Open your browser:**
   Visit [http://127.0.0.1:8080](http://127.0.0.1:8080) (for local access)
   or [http://192.168.1.25:8080](http://192.168.1.25:8080) (for LAN access)
g
## Tech Stack
- **Backend:** Python, Flask, yfinance
- **Frontend:** HTML, CSS, JavaScript, Chart.js

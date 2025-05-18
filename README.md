# Elaine's Playground

Elaine's Playground is a web app hosting a collection of fun and interactive play tools! This project is designed as a playground for experimenting with algorithms, data, and user interaction—all in one place.

## Features
- **Tokimeki Matchmaking**: Test the "matchability" between two names using different algorithms.
- **Sentiment Prediction**: Enter a sentence and get a positive/negative/neutral prediction using machine learning.
- **LIS Game**: Play a game to find the Longest Increasing Subsequence in a random sequence.
- **Stock Price Trends**: Explore and compare the price trends of popular stocks over the past month.
- **Largest Stock Price Change**: See which stock had the biggest price swings in a given period.

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

## Tech Stack
- **Backend:** Python, Flask, yfinance, vaderSentiment
- **Frontend:** HTML, CSS, JavaScript, Chart.js

## License
MIT 

import os
# ...
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port) 
# Tokimeki: Matchmaking Fate Website

Tokimeki is an interactive web application that lets users test the "matchability" between two people based on their names (and optionally, dates of birth). The backend is powered by Flask (Python), and the frontend is a modern, responsive JavaScript app.

## Features
- Enter two names and (optionally) dates of birth
- Choose from multiple matching algorithms:
  - **Sum Similarity**: Compares the sum of name character values
  - **Longest Consecutive**: Finds the longest consecutive sequence in the combined name values
  - **Longest Common Subsequence (LCS)**: Measures the longest sequence present in both names
- Instant, interactive results with a cute anime-style UI

## Demo
![screenshot](static/img/cute.png)

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
   Visit [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Usage
- Enter two English names (and optionally, dates of birth)
- Select a matching algorithm from the dropdown
- Click "Check Match" to see the matchability percentage

## API
- **POST** `/match`
  - **Request JSON:**
    ```json
    {
      "name1": "string",
      "name2": "string",
      "dob1": "YYYY-MM-DD",  // optional
      "dob2": "YYYY-MM-DD",  // optional
      "algorithm": "sum" | "longest" | "lcs"
    }
    ```
  - **Response JSON:**
    ```json
    {
      "percentage": 87.5
    }
    ```

## Algorithms
- **Sum Similarity**: Converts each name to a list of numbers (a=0, b=1, ...), sums each, and compares the ratio.
- **Longest Consecutive**: Finds the longest consecutive sequence in the combined number lists, and compares to the number of unique values.
- **LCS**: Uses the Longest Common Subsequence algorithm to measure similarity between the two name lists.

## Customization
- To change the matching logic, edit `app.py`.
- To update the UI or add new features, edit `static/index.html`.
- To use your own image, replace `static/img/cute.png`.

## License
MIT 
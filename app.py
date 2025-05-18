from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from typing import List

app = Flask(__name__)
CORS(app)

def name_to_numbers(name):
    name = name.lower()
    return [ord(c) - ord('a') for c in name if 'a' <= c <= 'z']

def longest_consecutive(nums: List[int]) -> int:
    if not nums:
        return 0
    nums_set = set(nums)
    longest = 0
    for num in nums_set:
        if num - 1 not in nums_set:
            cur_num = num
            cur_len = 1
            while cur_num + 1 in nums_set:
                cur_num += 1
                cur_len += 1
            longest = max(longest, cur_len)
    return longest

@app.route('/match', methods=['POST'])
def match():
    data = request.json
    name1 = data.get('name1', '')
    name2 = data.get('name2', '')
    algorithm = data.get('algorithm', 'sum')
    nums1 = name_to_numbers(name1)
    nums2 = name_to_numbers(name2)
    if algorithm == 'longest':
        combined = nums1 + nums2
        if not combined:
            percentage = 0
        else:
            longest = longest_consecutive(combined)
            unique_count = len(set(combined))
            if unique_count == 0:
                percentage = 0
            else:
                percentage = round(longest / unique_count * 100, 2)
    else:
        sum1 = sum(nums1)
        sum2 = sum(nums2)
        if max(sum1, sum2) == 0:
            percentage = 0
        else:
            percentage = round(min(sum1, sum2) / max(sum1, sum2) * 100, 2)
    return jsonify({'percentage': percentage})

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(debug=True) 
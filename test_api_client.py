"""Simple client to test the FastAPI endpoints"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    """Test all API endpoints"""
    print("=" * 60)
    print("Testing GradeSchoolMathSolver-RAG API")
    print("=" * 60)
    
    # Test root endpoint
    print("\n1. Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test problem generation
    print("\n2. Generating a problem...")
    response = requests.post(f"{BASE_URL}/api/problem/generate", json={
        "problem_type": "addition",
        "difficulty": 1
    })
    problem = response.json()
    print(f"Problem: {problem['problem_text']}")
    print(f"Problem ID: {problem['problem_id']}")
    problem_id = problem['problem_id']
    
    # Test submitting a correct answer
    print("\n3. Submitting a correct answer...")
    response = requests.post(f"{BASE_URL}/api/answer/submit", json={
        "problem_id": problem_id,
        "user_answer": 100,  # Just a guess
        "time_taken": 3.5
    })
    result = response.json()
    print(f"Result: {result['feedback']}")
    print(f"Correct: {result['is_correct']}")
    
    # If wrong, try the correct answer
    if not result['is_correct']:
        print(f"\n4. Trying the correct answer: {result['correct_answer']}...")
        response = requests.post(f"{BASE_URL}/api/answer/submit", json={
            "problem_id": problem_id,
            "user_answer": result['correct_answer'],
            "time_taken": 2.0
        })
        result = response.json()
        print(f"Result: {result['feedback']}")
    
    # Test getting a hint
    print("\n5. Getting a hint...")
    response = requests.post(f"{BASE_URL}/api/problem/hint", json={
        "problem_id": problem_id
    })
    hint = response.json()
    print(f"Hint: {hint['hint']}")
    
    # Test getting statistics
    print("\n6. Getting statistics...")
    response = requests.get(f"{BASE_URL}/api/stats?days=7")
    stats = response.json()
    print(f"Total answers: {stats['total_answers']}")
    print(f"Correct: {stats['correct_answers']}")
    print(f"Accuracy: {stats['accuracy']:.2f}%")
    
    # Test getting weak areas
    print("\n7. Getting weak areas...")
    response = requests.get(f"{BASE_URL}/api/stats/weak-areas")
    weak_areas = response.json()
    print(f"Weak areas: {json.dumps(weak_areas, indent=2)}")
    
    # Test adaptive problems
    print("\n8. Getting adaptive problems...")
    response = requests.get(f"{BASE_URL}/api/problem/adaptive?limit=5")
    adaptive = response.json()
    print(f"Recommended {len(adaptive['problems'])} problems:")
    for p in adaptive['problems'][:3]:
        print(f"  - {p['problem_text']} ({p['reason']})")
    
    # Test listing problems
    print("\n9. Listing problems...")
    response = requests.get(f"{BASE_URL}/api/problems?limit=5")
    problems = response.json()
    print(f"Found {len(problems['problems'])} problems")
    
    print("\n" + "=" * 60)
    print("✓ All API tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    print("Make sure the server is running: python main.py")
    print("Press Enter to start testing...")
    input()
    
    try:
        test_api_endpoints()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the server is running with: python main.py")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

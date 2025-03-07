# direct_api_test.py - Add this to your project and run it directly on your server
import requests
import json
import os

# Configuration
API_KEY = "b1742f67bda1c097be51c61409f1797a334d1889c291fedd5bcc0b3e070aa6c1"
TEST_ENDPOINT = "https://footystats.org/api/leagues"

# Create output directory if it doesn't exist
os.makedirs("api_test_results", exist_ok=True)

def write_results_file(filename, content):
    """Write test results to a file"""
    with open(os.path.join("api_test_results", filename), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Results written to api_test_results/{filename}")

# Test 1: Basic request with key in query string
print("\nTest 1: Key in query string")
try:
    response = requests.get(f"{TEST_ENDPOINT}?key={API_KEY}")
    status = response.status_code
    print(f"Status: {status}")
    
    output = f"Status: {status}\n\n"
    try:
        output += json.dumps(response.json(), indent=2)
    except:
        output += response.text[:2000]
    
    write_results_file("test1_query_string.txt", output)
except Exception as e:
    print(f"Error: {str(e)}")
    write_results_file("test1_query_string.txt", f"Error: {str(e)}")

# Test 2: With full headers set
print("\nTest 2: With full headers")
try:
    headers = {
        "Accept": "application/json",
        "User-Agent": "ValueHunter/1.0",
        "Referer": "https://footystats.org/",
        "Origin": "https://footystats.org"
    }
    response = requests.get(TEST_ENDPOINT, params={"key": API_KEY}, headers=headers)
    status = response.status_code
    print(f"Status: {status}")
    
    output = f"Status: {status}\n\n"
    try:
        output += json.dumps(response.json(), indent=2)
    except:
        output += response.text[:2000]
    
    write_results_file("test2_full_headers.txt", output)
except Exception as e:
    print(f"Error: {str(e)}")
    write_results_file("test2_full_headers.txt", f"Error: {str(e)}")

# Test 3: Check server IP
print("\nTest 3: Check server IP")
try:
    response = requests.get("https://api.ipify.org?format=json")
    ip_data = response.json()
    server_ip = ip_data.get("ip", "Unknown")
    print(f"Server IP: {server_ip}")
    write_results_file("test3_server_ip.txt", f"Server IP: {server_ip}")
except Exception as e:
    print(f"Error getting server IP: {str(e)}")
    write_results_file("test3_server_ip.txt", f"Error: {str(e)}")

# Test 4: Authorization header
print("\nTest 4: Authorization header")
try:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    response = requests.get(TEST_ENDPOINT, headers=headers)
    status = response.status_code
    print(f"Status: {status}")
    
    output = f"Status: {status}\n\n"
    try:
        output += json.dumps(response.json(), indent=2)
    except:
        output += response.text[:2000]
    
    write_results_file("test4_auth_header.txt", output)
except Exception as e:
    print(f"Error: {str(e)}")
    write_results_file("test4_auth_header.txt", f"Error: {str(e)}")

print("\nAll tests completed. Check the api_test_results directory for detailed output.")
print("Use these results to identify why you're getting a 403 error.")
print(f"Your server IP address is: {server_ip if 'server_ip' in locals() else 'Unknown'}")
print("Make sure this IP is whitelisted in your FootyStats account if required.")

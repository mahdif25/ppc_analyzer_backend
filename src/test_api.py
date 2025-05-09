import requests
import json

# URL of the Flask endpoint
url = "http://127.0.0.1:5000/upload_ppc_reports"

# Path to the sample CSV file
file_path = "/home/ubuntu/sample_report_valid.csv"

# Test Case 1: Upload a single valid CSV file
print("Test Case 1: Uploading a single valid CSV file...")

files = {
    "files[]": (open(file_path, "rb"))
}

try:
    response = requests.post(url, files=files)
    response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    
    print(f"Status Code: {response.status_code}")
    response_json = response.json()
    print("Response JSON:")
    print(json.dumps(response_json, indent=4))

    # Basic checks on the response
    if response.status_code == 200:
        print("Test PASSED: Received 200 OK")
        if response_json.get("message") and "rows of data processed" in response_json["message"]:
            print("Test PASSED: Success message received.")
        else:
            print("Test FAILED: Success message missing or incorrect.")
        
        if response_json.get("kpis"):
            print("Test PASSED: KPIs received.")
            # Add more specific KPI checks here based on sample_report_valid.csv if needed
            # Example: Check if ACOS is calculated (actual value depends on data)
            if "Advertising Cost of Sales (ACOS)" in response_json["kpis"]:
                print(f"ACOS: {response_json['kpis']['Advertising Cost of Sales (ACOS)']:.2f}%")
            else:
                print("Test FAILED: ACOS KPI missing.")
        else:
            print("Test FAILED: KPIs missing in response.")
            
        if response_json.get("recommendations"):
            print("Test PASSED: Recommendations received.")
            if len(response_json["recommendations"]) > 0:
                print(f"Number of recommendations: {len(response_json["recommendations"])}")
            else:
                print("Test WARN: No recommendations generated, check logic or sample data.")
        else:
            print("Test FAILED: Recommendations missing in response.")
            
        if response_json.get("errors") is not None:
            print(f"Test WARN: Errors reported by backend: {response_json["errors"]}")
        else:
            print("Test PASSED: No errors reported by backend.")

    else:
        print(f"Test FAILED: Expected 200 OK, got {response.status_code}")

except requests.exceptions.RequestException as e:
    print(f"Test FAILED: Request failed: {e}")
except json.JSONDecodeError:
    print(f"Test FAILED: Could not decode JSON response. Response text: {response.text}")
except Exception as e:
    print(f"Test FAILED: An unexpected error occurred: {e}")

finally:
    # Close the file handle
    if "files[]" in files and not files["files[]"].closed:
        files["files[]"].close()

print("\nEnd of Test Case 1.")

# Add more test cases here (e.g., invalid file type, multiple files, empty file) as per testing_plan.md


import unittest
import openpyxl
import os,re
import json
from parameterized import parameterized
from collections import defaultdict
# from HtmlTestRunner import HTMLTestRunner
from datetime import datetime
import azure.functions as func
from function_app import reconcile 


# --- 1. Excel Data Loading Function ---
def get_test_data(file_path, sheet_name='Sheet1'):
    """
    Reads data from an Excel file starting from the second row (skipping headers).
    Returns a list of dictionaries, where each dict represents a row.
    """
    data = []
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found at: {file_path}")
            
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook[sheet_name]
        
         # Iterate through rows, skipping the header (min_row=2)
        # values_only=True returns the cell values instead of Cell objects
        for row in sheet.iter_rows(min_row=2, values_only=True):
            # Convert any numeric or formula results to the expected Python types if necessary.
            # Here we ensure InputA, InputB, and ExpectedResult are integers for the example.
            # We assume the data structure: (TestName, InputA, InputB, ExpectedResult)
            
            # Note: We convert string '8' to int 8 for the test case's assertion.
            agent,tool_definition,expense_type,input_data,key_field,expected_result = row
            response = invoke_agent(agent, json.loads(input_data)) 
            actual_response = response.get_body().decode()
            # Basic validation/type conversion (adjust as per your actual data)
            try:
                data.append((agent,tool_definition,expense_type,input_data,key_field,actual_response,expected_result))
            except ValueError:
                print(f"Skipping row with invalid numeric data: {row}")
                continue # Skip rows with non-integer data if int is expected
            
    except Exception as e:
        print(f"Error reading Excel data: {e}")
        # Return an empty list or raise the exception, depending on your error handling
        return []        
    return data

def compare_json(actual, expected, path=""):
    results = []

    if isinstance(actual, dict) and isinstance(expected, dict):
        all_keys = set(actual.keys()).union(expected.keys())
        for key in all_keys:
            new_path = f"{path}.{key}" if path else key
            a_val = actual.get(key)
            e_val = expected.get(key)
            results.extend(compare_json(a_val, e_val, new_path))

    elif isinstance(actual, list) and isinstance(expected, list):
        max_len = max(len(actual), len(expected))
        for i in range(max_len):
            new_path = f"{path}[{i}]"
            a_val = actual[i] if i < len(actual) else None
            e_val = expected[i] if i < len(expected) else None
            results.extend(compare_json(a_val, e_val, new_path))

    else:
        match = actual == expected
        detail = "" if match else f"Values differ: {actual} vs {expected}"
        results.append({
            "field": path,
            "actual": actual,
            "expected": expected,
            "match": "PASS" if match else "FAIL",
            "details": detail
        })

    return results


# Helper to extract top-level path (e.g., 'data[0]' from 'data[0].field_name')
def extract_top_level_path(field_path):
    match = re.match(r'^([^.\[]+(?:\[\d+\])?)', field_path)
    return match.group(1) if match else field_path

# --- 2. Invoke Agent API ---
def invoke_agent(agent,input_data):  
    print(f"Invoking agent: {agent} with input_data: {input_data}")
    if agent.upper() == "RECONCILIATION":
        req = func.HttpRequest(
                method="POST",
                url="/api/reconcile",           
                headers={},
                body=json.dumps(input_data).encode("utf-8")                 # <-- REQUIRED, bytes even for GET
            )
        return reconcile(req)
    else:
        raise ValueError(f"Unsupported agent type: {agent}")

def remove_fields(obj, suffix_to_remove="metadata"):
    if isinstance(obj, dict):
        return {
            key: remove_fields(value, suffix_to_remove)
            for key, value in obj.items()
            if not key.endswith(suffix_to_remove)
        }
    elif isinstance(obj, list):
        return [remove_fields(item, suffix_to_remove) for item in obj]
    else:
        return obj

# --- 3. Unit Test Implementation ---

class TestDataDriven(unittest.TestCase):
    
    # Define the path to your Excel file
    EXCEL_FILE_PATH = r'testdata/TestData.xlsx'
    SHEET_NAME = 'Sheet1'
    
    # Load data once for all tests in this class
    # NOTE: You may want to load this in setUpClass if your data is static
    test_cases = get_test_data(EXCEL_FILE_PATH, SHEET_NAME)   
    
    #Convert and write to JSONL file
    with open("testdata/test_data.jsonl", "w", encoding="utf-8") as f:
        for agent,tool_definition,expense_type,input_data,key_field,actual_response,expected_result in test_cases:
            json_line = {"query": input_data, "context": agent, "response": actual_response, "ground_truth": expected_result}
            f.write(json.dumps(json_line, ensure_ascii=False) + "\n")

    # print(test_cases)
    @parameterized.expand(test_cases)
    def test_agent_with_excel_data(self,agent,tool_definition,expense_type,input_data,key_field,actual_response,ground_truth):
        """Runs the test agent function against every row in the Excel data.""" 
        expected_result = json.loads(ground_truth)   
        actual_result=json.loads(actual_response) 
        
        actual_result = remove_fields(actual_result[key_field])  
        expected_result = remove_fields(expected_result[key_field])           
        comparison_results = compare_json(actual_result, expected_result)
        
        # Filter and count FAIL matches
        failed_results = [result for result in comparison_results if result.get("match") == "FAIL"]
        fail_count = len(failed_results)

        # Group failed fields by top-level path
        consolidated_failures = defaultdict(list)

        for entry in comparison_results:
            if entry.get("match") == "FAIL":
                top_path = extract_top_level_path(entry["field"])
                consolidated_failures[top_path].append({
                    "field": entry["field"],
                    "actual": entry.get("actual"),
                    "expected": entry.get("expected"),
                    "details": entry.get("details", "Values differ")
                })

        # Convert to list of dictionaries
        consolidated_list = [
            {
                "path": path,
                "failed_fields": fields
            }
            for path, fields in consolidated_failures.items()
        ]

  
        # print("Expected Result:", expected_result)
        # print("Actual Result:", actual_result)            
        # Perform the assertion
        self.assertEqual(
            fail_count, 
            0,
            f"Agent: {agent} Expense Type: {expense_type} .Failed Data :{consolidated_list}"
        )

# --- 4. Running the Tests ---

# if __name__ == '__main__':
#     print("**************************************")
    # 1. Create a TestLoader and TestSuite
    # loader = unittest.TestLoader()
    # suite = loader.loadTestsFromTestCase(TestDataDriven)
    
    # Run tests and capture results
    # runner = unittest.TextTestRunner(resultclass=unittest.TextTestResult, verbosity=2)
    # result = runner.run(suite)
# runner = unittest.TextTestRunner()
# result = runner.run(unittest.TestLoader().loadTestsFromTestCase(TestDataDriven))
# print(result)
# # Summary
# print("\n--- Test Summary ---")
# print(f"Total tests run: {result.testsRun}")
# print(f"Failures: {len(result.failures)}")
# print(f"Errors: {len(result.errors)}")
# print(f"Skipped: {len(result.skipped)}")

# gh_out_path = os.environ.get("GITHUB_OUTPUT")
# if gh_out_path:
#     try:
#         with open(gh_out_path, "a") as gh:
#             gh.write(f"tests_run={result.testsRun}\n")
#             gh.write(f"failures={len(result.failures)}\n")
#             gh.write(f"errors={len(result.errors)}\n")
#             gh.write(f"skipped={len(result.skipped)}\n")
#     except Exception as e:
#         print(f"Warning: failed to write GITHUB_OUTPUT: {e}")

    """
    # 2. Define the report path and file name
    report_dir = 'test_reports'
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    # Generate a timestamp for a unique report filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"Agent_DataDriven_Test_Report_{timestamp}.html"
    report_path = os.path.join(report_dir, report_filename)

    # 3. Configure the HTMLTestRunner
    # We use HtmlTestRunner from the 'html-testrunner' package
    # print(f"Generating HTML report at: {report_path}")
    runner = HTMLTestRunner(
        output=report_dir, 
        report_name=report_filename.replace('.html', ''),  # report_name is for the file name base
        report_title='Agent Data Driven Unittest Report',
        # description='Excel Data Driven Tests for Addition Logic',
        combine_reports=True # Ensures one single report file is created
    )
    runner.run(suite)
  
    
    # runner = unittest.TextTestRunner()
    # result = runner.run(unittest.TestLoader().loadTestsFromTestCase(TestDataDriven))
    # print(result)
   
    # with open(report_path, "w") as f:
    #         f.write("<html><body><h1>Test Report</h1>")
    #         f.write(f"<p>Tests run: {result.testsRun}</p>")
    #         f.write(f"<p>Failures: {len(result.failures)}</p>")
    #         f.write("</body></html>")
    """

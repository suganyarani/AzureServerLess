# tests/test_httptrigger_v2.py
import json
import unittest
import logging
import traceback
import azure.functions as func
from function_app import health_check  # import the v2 handler directly
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
#from HtmlTestRunner import HTMLTestRunner
#from datetime import datetime
class TestHealthCheck(unittest.TestCase):  
    
       
    def test_health_check(self):
        # Simulate GET /api/hello?name=Rani
        logging.info("Invoking method: health_check()")
        req = func.HttpRequest(
            method="GET",
            url="/api/health_check",
            params={"name": "Test"},
            headers={},
            body=b""                 
        )

        resp = health_check(req)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Hello! Test. This HTTP triggered function executed successfully.", resp.get_body().decode())
        if resp.status_code == 200:
            print("TestHealthCheck: test_health_check passed.")
"""
# if __name__ == "__main__":
#     try:
#         unittest.main()
#     except Exception as e:
#         traceback.print_exc()
#         print(f"Error: {e}")
# runner = unittest.TextTestRunner()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_filename = f"Agent_DataDriven_Test_Report_{timestamp}.html"
# result = runner.run(unittest.TestLoader().loadTestsFromTestCase(TestDataDriven))    
runner = HTMLTestRunner(
    output="./",
    descriptions="Scenario",
    report_name=report_filename.replace('.html', ''),  # report_name is for the file name base
    report_title='Agent Data Driven Unittest Report',
    # description='Excel Data Driven Tests for Addition Logic',
    combine_reports=True # Ensures one single report file is created
)
test_modules = ['test_sample','test_sample']#, 'test_reconciliation' ]

# Load tests from modules
loader = unittest.TestLoader()

suites = unittest.TestSuite(
    [loader.loadTestsFromName(mod) for mod in test_modules] 
)


# Combine all suites
combined_suite = unittest.TestSuite(suites)

# Run tests and capture results
# runner = unittest.TextTestRunner(resultclass=unittest.TextTestResult, verbosity=2)
runner.run(combined_suite)    
"""
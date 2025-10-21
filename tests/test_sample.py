# tests/test_httptrigger_v2.py
import json
import unittest
import logging
import traceback
import azure.functions as func
from function_app import health_check  # import the v2 handler directly
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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

if __name__ == "__main__":
    try:
        unittest.main()
    except Exception as e:
        traceback.print_exc()
        print(f"Error: {e}")
         
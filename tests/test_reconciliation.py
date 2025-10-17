# tests/test_httptrigger_v2.py
import json
import unittest
import azure.functions as func
from function_app import function_http_trigger  # import the v2 handler directly

class TestHttpTriggerV2(unittest.TestCase):

    def test_hello_query_param(self):
        # Simulate GET /api/hello?name=Rani
        req = func.HttpRequest(
            method="GET",
            url="/api/function_http_trigger",
            params={"name": "Rani"},
            headers={}
        )
        resp = function_http_trigger(req)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Hello! Rani. This HTTP triggered function executed successfully.", resp.get_body().decode())

if __name__ == "__main__":
    unittest.main()
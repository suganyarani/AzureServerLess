# tests/test_httptrigger_v2.py
import json
import unittest
import traceback
import azure.functions as func
from function_app import reconcile  # import the v2 handler directly
from dotenv import load_dotenv
load_dotenv()


def remove_fields(obj, fields_to_remove):
    if isinstance(obj, dict):
        return {
            key: remove_fields(value, fields_to_remove)
            for key, value in obj.items()
            if key not in fields_to_remove
        }
    elif isinstance(obj, list):
        return [remove_fields(item, fields_to_remove) for item in obj]
    else:
        return obj


class TestReconciliationAgent(unittest.TestCase):

    def test_reconciliation(self):
        # Simulate GET /api/hello?name=Rani
        body={
        "expense_id": "7635BF521DB19E419E9DE80A659214C7",
        "expense_type": "Hotel",
        "extracted_data": {
            "employee_name": "Barbara Siminerio",
            "employee_name_metadata": {
                "x": 0.6747,
                "y": 2.444,
                "width": 0.9527,
                "height": 0.123,
                "page_no": 1
            },
            "vendor_name": "Courtyard by Marriott® New York Manhattan Midtown West",
            "vendor_name_metadata": {
                "x": 0.493,
                "y": 1.1993,
                "width": 3.172,
                "height": 0.1332,
                "page_no": 1
            },
            "transaction_date": "05Sep25",
            "transaction_date_metadata": {
                "x": 5.1738,
                "y": 3.3066,
                "width": 0.807,
                "height": 0.1221,
                "page_no": 1
            },
            "checkin_date": "02Sep25",
            "checkin_date_metadata": {
                "x": 0.6719,
                "y": 3.3056,
                "width": 0.858,
                "height": 0.1314,
                "page_no": 1
            },
            "checkout_date": "05Sep25",
            "checkout_date_metadata": {
                "x": 3.6722,
                "y": 3.3058,
                "width": 0.9043,
                "height": 0.1362,
                "page_no": 1
            },
            "transaction_amount": 1487.31,
            "transaction_amount_metadata": {
                "x": 7.1581,
                "y": 6.2522,
                "width": 0.4173,
                "height": 0.1208,
                "page_no": 1
            },
            "currency": "$",
            "currency_metadata": {
                "x": 5.1748,
                "y": 2.9762,
                "width": 0.7483,
                "height": 0.1211,
                "page_no": 1
            },
            "attendee_count": 1,
            "attendee_count_metadata": {
                "x": 5.1739,
                "y": 2.798,
                "width": 1.088,
                "height": 0.1229,
                "page_no": 1
            },
            "payment_mode": "American Express",
            "payment_mode_metadata": {
                "x": 1.7402,
                "y": 6.2557,
                "width": 0.9722,
                "height": 0.13,
                "page_no": 1
            },
            "availability_exceptionapproval": True,
            "approvers_mailid": "CFOTravelException@cognizant.com",
            "items": [
                {
                    "date": "02Sep25",
                    "amount": 490.77
                },
                {
                    "date": "03Sep25",
                    "amount": 490.77
                },
                {
                    "date": "04Sep25",
                    "amount": 490.77
                }
            ]
        },
        "expense_details": {
        "id": "22543708-dd61-434a-9946-514b02d74afa",
        "report_id": "37F7BC25E9F943EFA87D",
        "download_date": "07-10-2025",
        "expense_id": "7635BF521DB19E419E9DE80A659214C7",
        "emp_id": "127957",
        "emp_name": "Eswarachari Vasant",
        "pta_code": "127957-F78F9_BOM-BLR 09/07/2022",
        "expense_type": "Hotel",
        "location": "New York, New York",
        "payment_type": "Cash/Out-of-Pocket",
        "receipt_ImageId": "1E9B3040BAA04FF987006144FDF4C771",
        "receipt_available": True,
        "exp_receipt_filename": "37F7BC25E9F943EFA87D/7635BF521DB19E419E9DE80A659214C7/Hotel/1E9B3040BAA04FF987006144FDF4C771.pdf",
        "transaction_amount": 1487.31,
        "currency": "USD",
        "transaction_date": "2025-09-04",
        "personal_expense": False,
        "bill_to_client": False,
        "expense_rejected": False,
        "vendor_name": "CY NY MIDTOWN WEST",
        "business_purpose": "Q3 2025 Board Meeting - BS",
        "attendee_count": 0,
        "mileage": None,
        "itemization_details": [
            {
                "expense_id": "E31AF0F8BC44A843A207366C4C52E990",
                "parent_expense_id": "7635BF521DB19E419E9DE80A659214C7",
                "expense_type": "Hotel",
                "location": "New York, New York",
                "payment_type": "Cash/Out-of-Pocket",
                "transaction_amount": 429,
                "currency": "USD",
                "transaction_date": "2025-09-02",
                "personal_expense": False,
                "attendee_count": 0
            },
            {
                "expense_id": "57517C154BD15348AB58DADEC09237DF",
                "parent_expense_id": "7635BF521DB19E419E9DE80A659214C7",
                "expense_type": "Hotel Tax",
                "location": "New York, New York",
                "payment_type": "Cash/Out-of-Pocket",
                "transaction_amount": 66.77,
                "currency": "USD",
                "transaction_date": "2025-09-02",
                "personal_expense": False,
                "attendee_count": 0
            },
            {
                "expense_id": "0FB3669F532FE045B79D79B71ADFD2D5",
                "parent_expense_id": "7635BF521DB19E419E9DE80A659214C7",
                "expense_type": "Hotel",
                "location": "New York, New York",
                "payment_type": "Cash/Out-of-Pocket",
                "transaction_amount": 429,
                "currency": "USD",
                "transaction_date": "2025-09-03",
                "personal_expense": False,
                "attendee_count": 0
            },
            {
                "expense_id": "627429F89645124DB88AD7EF24A0952B",
                "parent_expense_id": "7635BF521DB19E419E9DE80A659214C7",
                "expense_type": "Hotel Tax",
                "location": "New York, New York",
                "payment_type": "Cash/Out-of-Pocket",
                "transaction_amount": 66.77,
                "currency": "USD",
                "transaction_date": "2025-09-03",
                "personal_expense": False,
                "attendee_count": 0
            },
            {
                "expense_id": "7E87C51C4BBA1C4EA0876B2EAB656F57",
                "parent_expense_id": "7635BF521DB19E419E9DE80A659214C7",
                "expense_type": "Hotel",
                "location": "New York, New York",
                "payment_type": "Cash/Out-of-Pocket",
                "transaction_amount": 429,
                "currency": "USD",
                "transaction_date": "2025-09-04",
                "personal_expense": False,
                "attendee_count": 0
            },
            {
                "expense_id": "3BD65773F4268C479523C83D07223BEE",
                "parent_expense_id": "7635BF521DB19E419E9DE80A659214C7",
                "expense_type": "Hotel Tax",
                "location": "New York, New York",
                "payment_type": "Cash/Out-of-Pocket",
                "transaction_amount": 66.77,
                "currency": "USD",
                "transaction_date": "2025-09-04",
                "personal_expense": False,
                "attendee_count": 0
            }
        ],
        "attendee_details": [],
        "trip_details": [],
        "comments": [],
        "status": "Pending",
        "_rid": "O9gqANpzYzkoAAAAAAAAAA==",
        "_self": "dbs/O9gqAA==/colls/O9gqANpzYzk=/docs/O9gqANpzYzkoAAAAAAAAAA==/",
        "_etag": "\"38015d28-0000-0100-0000-68e4f41d0000\"",
        "_attachments": "attachments/",
        "_ts": 1759835165
        } 
    }
        req = func.HttpRequest(
            method="POST",
            url="/api/reconcile",           
            headers={},
            body=json.dumps(body).encode("utf-8")                 # <-- REQUIRED, bytes even for GET
        )

        resp = reconcile(req)

        # self.assertEqual(resp.status_code, 200)
        # self.assertIn("Hello! ani. This HTTP triggered function executed successfully.", resp.get_body().decode())
        
        with open(r"testdata/gt.json", "r",encoding="utf-8") as f:
            # ground_truth = json.load(f)
            ground_truth = f.read()
 
        # # ground_truth = json.loads("""{"expense_id":"7635BF521DB19E419E9DE80A659214C7","expense_type":"Hotel","receipt_exists":false,"itemization_exists":false,"extracted_data":{"employee_name":"Barbara Siminerio","employee_name_metadata":{"x":0.6747,"y":2.444,"width":0.9527,"height":0.123,"page_no":1},"vendor_name":"Courtyard by Marriott\u00ae New York Manhattan Midtown West","vendor_name_metadata":{"x":0.493,"y":1.1993,"width":3.172,"height":0.1332,"page_no":1},"transaction_date":"05Sep25","transaction_date_metadata":{"x":5.1738,"y":3.3066,"width":0.807,"height":0.1221,"page_no":1},"checkin_date":"02Sep25","checkin_date_metadata":{"x":0.6719,"y":3.3056,"width":0.858,"height":0.1314,"page_no":1},"checkout_date":"05Sep25","checkout_date_metadata":{"x":3.6722,"y":3.3058,"width":0.9043,"height":0.1362,"page_no":1},"transaction_amount":1487.31,"transaction_amount_metadata":{"x":7.1581,"y":6.2522,"width":0.4173,"height":0.1208,"page_no":1},"currency":"$","currency_metadata":{"x":5.1748,"y":2.9762,"width":0.7483,"height":0.1211,"page_no":1},"attendee_count":1,"attendee_count_metadata":{"x":5.1739,"y":2.798,"width":1.088,"height":0.1229,"page_no":1},"payment_mode":"American Express","payment_mode_metadata":{"x":1.7402,"y":6.2557,"width":0.9722,"height":0.13,"page_no":1},"availability_exceptionapproval":true,"approvers_mailid":"CFOTravelException@cognizant.com","items":[{"date":"02Sep25","amount":490.77},{"date":"03Sep25","amount":490.77},{"date":"04Sep25","amount":490.77}]},"reconciled_data":{"data":[{"field_name":"employee_name","receipt_value":"Barbara Siminerio","concur_value":"Eswarachari Vasant","match":"false","details":"Different employee names."},{"field_name":"vendor_name","receipt_value":"Courtyard by Marriott\u00ae New York Manhattan Midtown West","concur_value":"CY NY MIDTOWN WEST","match":"true","details":"Vendor names refer to the same entity."},{"field_name":"transaction_date","receipt_value":"05Sep25","concur_value":"2025-09-04","match":"true","details":"Dates are within 1-2 days range."},{"field_name":"transaction_amount","receipt_value":"1487.31","concur_value":"1487.31","match":"true","details":"Amounts match."},{"field_name":"currency","receipt_value":"$","concur_value":"USD","match":"true","details":"Currency symbols refer to the same currency."},{"field_name":"attendee_count","receipt_value":"1","concur_value":"0","match":"false","details":"Different attendee counts."}],"items":[{"date":"02Sep25","receipt_value":"490.77","concur_value":"496.77","match":"false","details":"Sum of amounts for this date do not match."},{"date":"03Sep25","receipt_value":"490.77","concur_value":"496.77","match":"false","details":"Sum of amounts for this date do not match."},{"date":"04Sep25","receipt_value":"490.77","concur_value":"496.77","match":"false","details":"Sum of amounts for this date do not match."}]},"expense_details":{"id":"22543708-dd61-434a-9946-514b02d74afa","report_id":"37F7BC25E9F943EFA87D","download_date":"07-10-2025","expense_id":"7635BF521DB19E419E9DE80A659214C7","emp_id":"127957","emp_name":"Eswarachari Vasant","pta_code":"127957-F78F9_BOM-BLR 09/07/2022","expense_type":"Hotel","location":"New York, New York","payment_type":"Cash/Out-of-Pocket","receipt_ImageId":"1E9B3040BAA04FF987006144FDF4C771","receipt_available":true,"exp_receipt_filename":"37F7BC25E9F943EFA87D/7635BF521DB19E419E9DE80A659214C7/Hotel/1E9B3040BAA04FF987006144FDF4C771.pdf","transaction_amount":1487.31,"currency":"USD","transaction_date":"2025-09-04","personal_expense":false,"bill_to_client":false,"expense_rejected":false,"vendor_name":"CY NY MIDTOWN WEST","business_purpose":"Q3 2025 Board Meeting - BS","attendee_count":0,"mileage":null,"itemization_details":[{"expense_id":"E31AF0F8BC44A843A207366C4C52E990","parent_expense_id":"7635BF521DB19E419E9DE80A659214C7","expense_type":"Hotel","location":"New York, New York","payment_type":"Cash/Out-of-Pocket","transaction_amount":429,"currency":"USD","transaction_date":"2025-09-02","personal_expense":false,"attendee_count":0},{"expense_id":"57517C154BD15348AB58DADEC09237DF","parent_expense_id":"7635BF521DB19E419E9DE80A659214C7","expense_type":"Hotel Tax","location":"New York, New York","payment_type":"Cash/Out-of-Pocket","transaction_amount":66.77,"currency":"USD","transaction_date":"2025-09-02","personal_expense":false,"attendee_count":0},{"expense_id":"0FB3669F532FE045B79D79B71ADFD2D5","parent_expense_id":"7635BF521DB19E419E9DE80A659214C7","expense_type":"Hotel","location":"New York, New York","payment_type":"Cash/Out-of-Pocket","transaction_amount":429,"currency":"USD","transaction_date":"2025-09-03","personal_expense":false,"attendee_count":0},{"expense_id":"627429F89645124DB88AD7EF24A0952B","parent_expense_id":"7635BF521DB19E419E9DE80A659214C7","expense_type":"Hotel Tax","location":"New York, New York","payment_type":"Cash/Out-of-Pocket","transaction_amount":66.77,"currency":"USD","transaction_date":"2025-09-03","personal_expense":false,"attendee_count":0},{"expense_id":"7E87C51C4BBA1C4EA0876B2EAB656F57","parent_expense_id":"7635BF521DB19E419E9DE80A659214C7","expense_type":"Hotel","location":"New York, New York","payment_type":"Cash/Out-of-Pocket","transaction_amount":429,"currency":"USD","transaction_date":"2025-09-04","personal_expense":false,"attendee_count":0},{"expense_id":"3BD65773F4268C479523C83D07223BEE","parent_expense_id":"7635BF521DB19E419E9DE80A659214C7","expense_type":"Hotel Tax","location":"New York, New York","payment_type":"Cash/Out-of-Pocket","transaction_amount":66.77,"currency":"USD","transaction_date":"2025-09-04","personal_expense":false,"attendee_count":0}],"attendee_details":[],"trip_details":[],"comments":[],"status":"Pending","_rid":"O9gqANpzYzkoAAAAAAAAAA==","_self":"dbs/O9gqAA==/colls/O9gqANpzYzk=/docs/O9gqANpzYzkoAAAAAAAAAA==/","_etag":"\"38015d28-0000-0100-0000-68e4f41d0000\"","_attachments":"attachments/","_ts":1759835165},"report_details":{},"review_feedback":"APPROVED","review_attempts":2,"receipt_rules":[],"receiptrule_results":[]}""")
        # result = self.agent.reconcile(input_data, ground_truth)
        print("RESULT")
        # print(resp.get_body().decode()) 
        # print(ground_truth) 
        actual_result = json.loads(resp.get_body().decode())   
        # remove_fields(actual_result,["_rid","_self","_etag","_attachments","_ts"])
        expected_result = json.loads(ground_truth)  
        # dict=  {
        #     "query":json.dumps(body),
        #     "context":"Extraction",
        #     "ground_truth":ground_truth,
        #     "response":resp.get_body().decode()           
        # }
        # print(json.dumps(dict))
        print("Expected:\n", expected_result["reconciled_data"])    
        print("Actual :\n", actual_result["reconciled_data"])   #expected_result["reconciled_data"] == actual_result["reconciled_data"] 
        assert True, f"Inputs {body} failed. Expected {expected_result["reconciled_data"]}, got {actual_result["reconciled_data"]}."

if __name__ == "__main__":
    try:
        unittest.main()
    except Exception as e:
        traceback.print_exc()
        print(f"Error: {e}")
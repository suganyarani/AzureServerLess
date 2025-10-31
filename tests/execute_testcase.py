import os
import json,re
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv()
os.environ["OPENAI_API_VERSION"] = os.environ["MODEL_VERSION"]
os.environ["AZURE_OPENAI_ENDPOINT"] = os.environ["MODEL_ENDPOINT"]
os.environ["AZURE_OPENAI_API_KEY"] =os.environ["MODEL_API_KEY"]
# Initialize AzureChatOpenAI
llm = AzureChatOpenAI(
    deployment_name=os.environ["MODEL_DEPLOYMENT_NAME"],
    temperature=0,
    seed=42,
    max_retries=3
)

from pydantic import BaseModel

class ValidationResult(BaseModel):
    Result: str
    Reason: str

     
def generate_reconcile_validation_prompt(prompt_template,extracted_value, details_value, ground_truth, reconciled_data):
    
    return prompt_template.format(
        extracted_value=json.dumps(extracted_value, indent=2),
        details_value=json.dumps(details_value, indent=2),
        ground_truth=json.dumps(ground_truth, indent=2),
        reconciled_data=json.dumps(reconciled_data, indent=2)
    )  
    
def generate_header_validation_prompt(prompt_template,expense_type, report_data, ground_truth, receipt_data,header_validation):
    
    return prompt_template.format(
        expense_type=json.dumps(expense_type, indent=2),
        report_data=json.dumps(report_data, indent=2),
        ground_truth=json.dumps(ground_truth, indent=2),
        receipt_data=json.dumps(receipt_data, indent=2),
        header_validation=json.dumps(header_validation, indent=2)
    )            
        
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
    
# Function to validate a single field
def validate_field(agent,prompt_template, input_record, actual_result, ground_truth):
    prompt=None
    if agent.upper() == "RECONCILIATION":
        input_record = remove_fields(input_record)
        extracted_data= input_record.get("extracted_data",{})
        expense_details= input_record.get("expense_details",{}) 
        actual_result = json.loads(actual_result)
        actual_result = remove_fields(actual_result)
        reconciled_data = actual_result.get("reconciled_data", {}) 
        prompt = generate_reconcile_validation_prompt(prompt_template,extracted_data, expense_details, ground_truth, reconciled_data)
    elif agent.upper() == "HEADER VALIDATION":
        print(type(actual_result))
        actual_result = json.loads(actual_result)
        expense_type= actual_result.get("expense_type", "") 
        report_data= actual_result.get("report_data",{}) 
        header_validation = actual_result.get("header_validation_data", []) 
        receipt_data= actual_result.get("receipt_data", {}) 
        prompt = generate_header_validation_prompt(prompt_template,expense_type, report_data, ground_truth, receipt_data,header_validation)     
    response = llm.invoke([HumanMessage(content=prompt)])    
    result=None
    try:
        json_result = response.content       
        match = re.search(r"```json\s*(\{.*?\})\s*```", json_result, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                result = ValidationResult.model_validate_json(json_str)               
            except Exception as e:
                print("Parsing failed:", e)
        else:
            print("No JSON block found.")

    except json.JSONDecodeError:
        result = {
            "match": "false",
            "details": "LLM response could not be parsed as JSON."
        }

    return result


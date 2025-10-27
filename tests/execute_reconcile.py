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

     
def generate_validation_prompt(prompt_template,extracted_value, details_value, ground_truth, reconciled_data):
    
    return prompt_template.format(
        extracted_value=json.dumps(extracted_value, indent=2),
        details_value=json.dumps(details_value, indent=2),
        ground_truth=json.dumps(ground_truth, indent=2),
        reconciled_data=json.dumps(reconciled_data, indent=2)
    )        
        

# Function to validate a single field
def validate_field(prompt_template,extracted_data, expense_details, ground_truth, reconciled_data):
   
    prompt = generate_validation_prompt(prompt_template,extracted_data, expense_details, ground_truth, reconciled_data)
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


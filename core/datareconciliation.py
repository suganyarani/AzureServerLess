
from langchain_openai import AzureChatOpenAI
from azure.core.credentials import AzureKeyCredential
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from dotenv import load_dotenv
from core.data_access import insert_data,get_data
from pydantic import BaseModel, Field
from typing import List, Optional
from langgraph.graph import StateGraph, END
from core.model import AgentState
import os,logging,datetime,uuid
load_dotenv()

# DOC_INT_ENDPOINT = os.environ.get('DOC_INT_ENDPOINT')
# DOC_INT_KEY = os.environ.get('DOC_INT_KEY')
AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION =os.environ.get('AZURE_OPENAI_API_VERSION')
AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_DEPLOYMENT_NAME = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME')
AZURE_OPENAI_MODEL =  os.environ.get('AZURE_OPENAI_MODEL')


# === Initialize Clients ===
llm = AzureChatOpenAI(
    openai_api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    openai_api_version=AZURE_OPENAI_API_VERSION,
    azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
    temperature=0,
    # max_tokens=1000,
)

class reconcileddata(BaseModel):
    """
    Pydantic model representing the structure of the reconciled data.
    """
    field_name: str = Field(..., description="Name of the field  in concur")    

    receipt_value: str = Field(..., description="Value of that field from receipt data")    

    concur_value: str = Field(..., description="Value of that field from concur data")
    match: str = Field(..., description="either true or false")
    details: str = Field(..., description="brief explanation for the match result")

class itemizationdata(BaseModel):
    date: str = Field(..., description="Date under items")    

    receipt_value: str = Field(..., description="sum of amount for a date under items in receipt")    

    concur_value: str = Field(..., description="sum of amount for a date under items in concur")
    match: str = Field(..., description="either true or false")
    details: str = Field(..., description="brief explanation for the match result")

class finaldata(BaseModel):
    data:List[reconcileddata] =Field(...,description="list of reconciled data")
    items:Optional[List[itemizationdata]] =Field(...,description="list of itemized data")

prompt_airfare = """
        Todays  date: {today}
        You are an expert in reconciling data. You will be given data extracted from receipts and concur data.
        You have to compare these data and reconcile them. You will also be given schema to understand which all fields needs to be reconciled between receipt and concur data.
        Only those fields where reconcile is set as True should be compared. While comparing , check if they represent the same thing, irrespective of their formats.
        Use the schema to understand the list of fields to be reconciled,But in output, represent concur fields names as field_name.
        Key thing to be noted for airfare:
            1.To reconcile Transaction amount in Concur data against receipt, check the section - ticket_costs. If the amount defined in concur data is available under this ticket_costs list, mark it as True
            sometimes, amount might not match directly with receipt. In that case,check if the sum of few amounts matches with concur data.
            2.For few fields like currency, data could be in symbol or code. Irrepctive of their formats, check if they refer to the same thing and then reconcile them
            3.Date formats might vary between concur and receipt data. Concur could be in "YYYY-MM-DD" and receipt value in "DD-MM-YY".
            Please interpret the date formats correctly and then compare them.

        Generate the output in defined JSON format.Do not include any text or explanation outside the JSON OBJECT. Use concur fields as field names in output
         DO NOT include JSON keyword in output.
         Do Not hallucinate the data. Validate the data only from the inputs passed.
         concurdata: {concur_data} 
         receiptdata: {receipt_data}
         schema:{schema_config}
         
        """

prompt_hotel = """
        Todays  date: {today}
        You are an expert in reconciling data. You will be given data extracted from receipts and concur data.
        You have to compare these data and reconcile them. You will also be given schema to understand which all fields needs to be reconciled between receipt and concur data.
        Only those fields where reconcile is set as True should be compared. While comparing , check if they represent the same thing, irrespective of their formats.
        Use the schema to undertsand the list of fields to be reconciled,But in output, represent concur fields names as field_name.
        If itemization details is available in concur data, always represent its output under items. Do not include them under data in JSON output 
        Key thing to be noted for hotel:
           1. To reconcile Transaction amount and transaction date in Concur data against receipt, check the section - date_payments. 
            If the combination of amount and date defined in concur data is available under this date_payments list, mark it as True.            
            Transaction date might be same between concur and recipt or vary by 1 or 2 days. Even if it varies by 1 or 2 days, consider it as same. 
            Though we check if the combination of amount and date is available,Always represent both Transaction date and transaction amount as 2 different fields in output
           2. Also date formats might vary between concur and receipt data. Concur could be in "YYYY-MM-DD" and receipt value in "DD-MM-YY".
            Please interpret the date formats correctly and then compare them.
           3. To reconcile the details under itemization_details in concur, check the section-items in receipt data.
            Sum the amount spent and group them by date and then compare them. Consider only the dates that are available in concur data.
            Please do not compare item by item under the section-items in receipt data. Group them by date and compare the total amount.
            While calculating the sum, consider all the amounts under a date and Calculate the sum of amounts properly.          
           4.For few fields like currency, data could be in symbol or code. Irrepective of their formats, check if they refer to the same thing and then reconcile them
           5.Few fields like vendor could be represented in different formats. Please check if they refer to the samething and return the output
             For example - Courtyard by Marriott® New York Manhattan Midtown West and CY NY MIDTOWN WEST represent the same vendor
        
        Generate the output in defined JSON format.Do not include any text or explanation outside the JSON OBJECT. Use concur fields as field names in output
         DO NOT include JSON keyword in output.
         Do Not hallucinate the data. Validate the data only from the inputs passed.
         concurdata: {concur_data} 
         receiptdata: {receipt_data}
         schema:{schema_config}
         
        """

prompt_meals  = """
        Todays  date: {today}
        You are an expert in reconciling data. You will be given data extracted from receipts and concur data.
        You have to compare these data and reconcile them. You will also be given schema to understand which all fields needs to be reconciled between receipt and concur data.
        Only those fields where reconcile is set as True should be compared. While comparing , check if they represent the same thing, irrespective of their formats.
        Use the schema to understand the list of fields to be reconciled,But in output, represent concur fields names as field_name.
        Key thing to be noted for individual meals:            
            1.For few fields like currency, data could be in symbol or code. Irrepctive of their formats, check if they refer to the same thing and then reconcile them
            2.Date formats might vary between concur and receipt data. Concur could be in "YYYY-MM-DD" and receipt value in "DD-MM-YY".
             Please interpret the date formats correctly and then compare them.
            3.Few fields like vendor could be represented in different formats. Please check if they refer to the samething and return the output
             For example - Courtyard by Marriott® New York Manhattan Midtown West and CY NY MIDTOWN WEST represent the same vendor

        Generate the output in defined JSON format.Do not include any text or explanation outside the JSON OBJECT. Use concur fields as field names in output
         DO NOT include JSON keyword in output.
         Do Not hallucinate the data. Validate the data only from the inputs passed.
         concurdata: {concur_data} 
         receiptdata: {receipt_data}
         schema:{schema_config}
         review feedback:{review_feedback}         
        """

prompt_mapping ={
    "Airfare": prompt_airfare,
    "Hotel": prompt_hotel,
    "Individual Meals":prompt_meals    
}
MAX_REVIEW_ATTEMPTS = 1

# Prompt for the rule reviewer LLM
review_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert business analyst and reviewer. "
                    "Your task is to review the data reconcilation done on the data extracted from receipts and concur"
                    "Provide concise and actionable feedback if it needs refinement. "
                    "If the output is satisfactory, explicitly state 'APPROVED'. "
                    "Focus on accuracy of the reconciled output.\n"
                    "Few keypoints to be considered while doing comparison\n"
                    "Date formats might vary between concur and receipt data. Concur could be in YYYY-MM-DD and receipt value in DD-MM-YY.\n"
                    "Please interpret the date formats correctly and then compare them.\n"
                    "Transaction date might be same between concur and recipt or vary by 1 or 2 days. Even if it varies by 1 or 2 days, consider it as same.\n"
                    "For few fields like currency, data could be in symbol or code. Irrepective of their formats, check if they refer to the same thing and then reconcile them.\n"
                    "Few fields like vendor could be represented in different formats. Please check if they refer to the samething and return the output.\n"
                    "For example - Courtyard by Marriott® New York Manhattan Midtown West and CY NY MIDTOWN WEST represent the same vendor.\n"
                    "calculation of sum is applicable only for Items. Items field will be applicable only when itemization details exists in concur data else it will be None.\n"
                    "for airfare,To reconcile Transaction amount in Concur data against receipt, check the section - ticket_costs. If the amount defined in concur data is available under this ticket_costs list, mark it as True\n"
                    "sometimes, amount might not match directly with receipt. In that case,check if the sum of few amounts matches with concur data.\n"
                    "validate the reconciled data based on the justification provided under details for each field\n"
                    "Consider aspects like: Is the comparison done correctly? Is the sum calculated correctly for items? Are the key points mentioned above considered?\n"
                    "Example feedback: 'Sum calculated on the amounts for data [02-02-2025] under items is wrong'\n"
                    "Example approval: 'APPROVED'\n"
                    "You have {attempts_left} attempts remaining to refine the output."
                    "give the overall feedback as overall_feedback as VERIFIED or REJECTED or APPROVED"
                ),
                (
                    "human",
                    "Here is the receipt data:\n\n{receipt_data}\n\n"
                    "Here is the concur data:\n\n{concur_data}\n\n"
                    "data reconciled between receipt and concur:\n\n{reconciled_data}\n\n"
                    "Please provide your review feedback or state 'APPROVED'."
                ),
    ]
)

def fetch_schema(category,version):
    try:
        params ={"category":category,"version":version}
        schema =get_data('schema',params)
        return schema
    except Exception as e:
        logging.error(f"Error while fetching schema from db: {e}")

def data_reconcile_node(state:AgentState)->AgentState:
    """Node to reconcile the data extracted from receipt and concur"""
    try:
        version ='latest'
        schema_config =fetch_schema(state.expense_type,version)

        prompts =prompt_mapping[state.expense_type]

        review_feedback_instruction = ""
        if state.review_feedback:
            print(f"Received feedback for rule extraction: {state.review_feedback}")
            review_feedback_instruction = (
                f"Previous attempt's output was reviewed and the following feedback was provided:\n"
                f"'{state.review_feedback}'\n"
                f"Please refine your rule extraction based on this feedback, ensuring higher accuracy and adherence to requirements."
            )

        prompt = prompts.format(receipt_data=state.extracted_data, concur_data=state.expense_details,schema_config=schema_config,review_feedback= review_feedback_instruction,today=datetime.time())
        # prompt += f"\n\n{pydantic_parser.get_format_instructions()}"
    
        message = [
                    SystemMessage(content="""
                                You are a support assistant who helps in reconciling data extracted from receipts and concur.
                                You will be given receipt and concur data,on which data reconciliation to be done.
                                Please extract the data as per the instructions provided in the prompt.
                                """),
                    HumanMessage(content=prompt)
                ]
        # response = llm.invoke(message)
        parse_llm = llm.with_structured_output(finaldata)
        response = parse_llm.invoke(message)
    
        # print(response)
            # parsed_data = parse_with_retries(fixing_parser.parse, response.content)
            
        reconciled = response.model_dump()
        # print(reconciled)
        state.reconciled_data = reconciled
        return state
    except Exception as e:
        logging.error(f"Error while reconciling the data: {e}")

def data_review_node(state: AgentState) -> AgentState:
    """
        Node to review the reconciled data.
        It can either approve the data or provide feedback for refinement.
    """
    try:
            
        print("--- Executing: Review data Node ---")
           
        if not state.reconciled_data:
            print("No data to review. Approving by default.")
            state.review_feedback = "APPROVED"
            return state
            
        state.review_attempts += 1
        if state.review_attempts > MAX_REVIEW_ATTEMPTS:
            state.review_feedback = "APPROVED"
            return state

        review_chain = review_prompt | llm
            # with get_openai_callback() as cb:
        reviewer_response = review_chain.invoke({
                "receipt_data":state.extracted_data, 
                "concur_data":state.expense_details,
                "reconciled_data":state.reconciled_data,                
                "attempts_left": MAX_REVIEW_ATTEMPTS - state.review_attempts
                })
                # state.token_state.total_tokens += cb.total_tokens
                # state.token_state.completion_tokens += cb.completion_tokens
                # state.token_state.prompt_tokens += cb.prompt_tokens
                # state.token_state.total_cost += cb.total_cost

        feedback = reviewer_response.content.strip() # Extract string content from AIMessage

        if "overall_feedback=APPROVED" in feedback.upper():
                state.review_feedback = "APPROVED"
                print("Rules APPROVED by reviewer.")
        else:
                state.review_feedback = feedback
                print("Rules require refinement. Feedback provided to extraction node.")
            
        return state
        # except ClientAuthenticationError as e:
        #     print("Authentication failed:", e.message)
        
        # except HttpResponseError as e:
        #     print("HTTP error:", e.message)
        
        # except ServiceRequestError as e:
        #     print("Service request error (e.g., network issue):", e.message)
        
    except Exception as e:
        logging.error(f"Error while reviewing the reconciled data: {e}")

def data_save_node(state:AgentState)->AgentState:
    """
     Node to save reconciled data into COSMOS DB
    """
    logging.info("--- Executing:Node to save reconciled data into COSMOS DB---")
    try:
        # result = ""
        # result_list = []  # Initialize as an empty list to store results
        if state.reconciled_data:           
            result = state.reconciled_data
           
        # Save the results to the Cosmos DB container
         # Save data into DB
        item = {"id": str(uuid.uuid4()),"report_id":state.report_id,"expense_id":state.expense_id,                
                "expense_type": state.expense_type,"reconciled_data":result
                }

        insert_data('reconcile',item) 
        return state
    except Exception as e:
        logging.error(f"Error while saving the reconciled data: {e}")

def reconciliation_build_graph():
    
    reconciliation_workflow = StateGraph(AgentState)

    # 1. Add Nodes: Define each step in your workflow as a node.
    # Each node corresponds to a Python function that takes the AgentState and returns an updated AgentState.
    # reconciliation_workflow.add_node("fetch_schema", fetch_schema_node)   
    reconciliation_workflow.add_node("reconcile_data", data_reconcile_node)      
    reconciliation_workflow.add_node("review_data", data_review_node)
    reconciliation_workflow.add_node("save_reconcileddata", data_save_node)  # This is a node to save results to Cosmos DB
    

    # 2. Set Entry Point: Define where the graph execution begins.
    reconciliation_workflow.set_entry_point("reconcile_data")
    reconciliation_workflow.add_edge("reconcile_data","review_data")
    # 3. Define Conditional Logic for Review:   
    def route_review_feedback(state: AgentState) -> str:
            """
            Determines the next step based on the review feedback.
            If feedback is 'APPROVED', proceed to execute rules.
            Otherwise, loop back to reconcile_data for refinement.
            """

            
            # Check if feedback exists and contains "APPROVED" (case-insensitive)
            if state.review_feedback and state.review_feedback =="APPROVED":
                return "approved" # Route name for approved rules
            else:
                return "refine"   # Route name for rules needing refinement

    # Add conditional edges
    reconciliation_workflow.add_conditional_edges(
            "review_data",         # Source node for this conditional transition
            route_review_feedback,  # Function to call to determine the next branch
            {
                "approved": "save_reconcileddata", # If 'route_review_feedback' returns "approved", go to 'execute_rules'                
                "refine": "reconcile_data",   # If 'route_review_feedback' returns "refine", go back to 'extract_rules'
            },
        ) 
        
    
    # 3. Define Edges: Connect the nodes to establish the workflow sequence.  
    
    reconciliation_workflow.add_edge("save_reconcileddata", END) 

    # 5. Compile the Workflow: This prepares the graph for execution.
    reconciliation = reconciliation_workflow.compile()
    return reconciliation

reconciliation = reconciliation_build_graph()

def data_reconciliation(state:AgentState)->AgentState:

    logging.info("--- Starting Datareconciliation Process ---")

    try:
        final_state = reconciliation.invoke(state)
        # final_state = extraction.invoke(extraction_initial_state)
        logging.info(f"Results: {final_state}")
        return final_state

    except Exception as e:
        logging.error(f"Error in invoke: {e}")
        return state

def test_reconciliation():
    input_json = {
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
    agent_state = AgentState(**input_json)
    version ='latest'
    schema_config =fetch_schema(agent_state.expense_type,version)
    receipt_data = agent_state.extracted_data
    concur_data =agent_state.expense_details
    # itemization_exists =state.itemization_exists
    
    result = data_reconciliation(agent_state)
    print(result)

    agent_state.reconciled_data = result
    # Save data into DB
    # item = {"id": str(uuid.uuid4()),"report_id":state.report_id,"expense_id":state.expense_id,                
                # "expense_type": state.expense_type,"reconciled_data":result
                # }

    # insert_data('reconcile',item) 
    return result

# print("End Result\n",test_reconciliation())
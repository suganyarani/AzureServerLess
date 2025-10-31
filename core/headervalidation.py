from langchain_openai import AzureChatOpenAI
# from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_core.output_parsers import PydanticOutputParser #sudha
from langchain_classic.output_parsers.fix import OutputFixingParser #sudha
from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
from langgraph.prebuilt import create_react_agent
# from langchain_classic.agents.react.agent import create_react_agent #sudha
from langchain_core.prompts import PromptTemplate
from azure.storage.blob import BlobServiceClient
from pydantic import BaseModel,Field
from langgraph.graph import StateGraph,END
from typing import Optional,List
from dotenv import load_dotenv
import logging,os,uuid,datetime
from core import tools
from core.model import AgentState
from core.data_access import insert_data,get_data
import traceback
import json

load_dotenv()

DOC_INT_ENDPOINT = os.environ.get('DOC_INT_ENDPOINT')
DOC_INT_KEY = os.environ.get('DOC_INT_KEY')
AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION =os.environ.get('AZURE_OPENAI_API_VERSION')
AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_DEPLOYMENT_NAME = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME')
AZURE_OPENAI_MODEL =  os.environ.get('AZURE_OPENAI_MODEL')

storage_account_url =os.environ.get('storage_account_url')
storage_account_key =os.environ.get('storage_account_key')

blob_service_client = BlobServiceClient(account_url=storage_account_url, credential=storage_account_key, logging_enable=False)
receipt_container_name = "prepayaudit-receipts"

# === Initialize Clients ===
llm = AzureChatOpenAI(
    openai_api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    openai_api_version=AZURE_OPENAI_API_VERSION,
    azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
    temperature=0,
    # max_tokens=1000,
)

api_tools = [    
    tools.get_approve_reject_sendback_codes_tool,        
]

class HeaderValidation(BaseModel):
    """A single rule with its result."""    
    name: str = Field(..., description="The name of the rule")    
    description: str = Field(..., description="The description of the rule that can be used to provide additional context about the rule.")
    result: str = Field(..., description="The result of the rule execution. give a short summary of the result")
    status: str = Field(..., description="The status of the rule execution.")
    reason: str = Field(..., description="The reasoning for the result should be elaborate and meaningful.")
    # approvecode: Optional[str] = Field(None,description="Applicable approval code for this rule")    
    sendbackcode: Optional[str] = Field(None,description="Applicable send back code for this rule")
    
    # Helper method to convert the instance to a dictionary
    def to_dict(self):
        # We use vars(self) to get a dictionary of all instance attributes
        return vars(self)

class HeaderValidationList(BaseModel):
    """A list of generated rules."""
    rules: List[HeaderValidation] = Field(..., description="The list of rule execution result")


def read_from_blob(blob_name,container_name):
    try:  
        blob_client = blob_service_client.get_blob_client(container=container_name,blob=blob_name)    
        filename =os.path.basename(blob_name)       
        # # Download the blob to a local file
        blob_file_path = f"tmp/{filename}" #sudha
        # download_file_path = f"./{blob_name}"
        print("\nDownloading blob to \n\t" + blob_file_path)
        with open(blob_file_path, "wb") as download_file:
            print("blob client is :",blob_client)
            try:
                download_file.write(blob_client.download_blob().readall())
            except Exception as e:
                print(f"Error in downloading blob data: {e}")
    except Exception as e:
        logging.error(f"Error in reading blob {blob_name} from container {container_name}: {e}")
    return blob_file_path    

def extract_filename_exptype(state: AgentState) -> AgentState:
    """
    Node to fetch receipt file name and expense type from expenseid
    """
    logging.info("--- Executing:Node to fetch receipt file name and expense type from expenseid---")
    try:
        expense_id =state.expense_id       
        params ={"expense_id":expense_id}
        result =get_data('expense',params)
        state.expense_type =result['expense_type']
        state.filename =result['exp_receipt_filename'] if result['receipt_available'] else None
        state.expense_receipt_exists =result['receipt_available']
        state.itemization_exists =False if not result["itemization_details"] else True
        state.report_id =result['report_id']
        state.expense_details =result
        return state
    except Exception as e:
        logging.error(f"Failed to fetch expense details from db: {e}")

def get_reportdata_node(state:AgentState)->AgentState:
    """
    Node to get report data from  databased based on report id
    """
    try:
        report_id =state.report_id       
        params ={"report_id":report_id}
        result =get_data('report',params)
        # print("result is :",result)
        state.report_details = result
        # Get receipt at report level
        print("outside report receipt fetch")
        print("result receipt available:",result.get('receipt_available'))
        if result and result.get('receipt_available'):            
            filename = result['header_receipt_filename']
            print("filename is :",filename)
            filepath = read_from_blob(filename,receipt_container_name)
            print("filepath is :",filepath)
            if filepath and os.path.exists(filepath):
                loader = AzureAIDocumentIntelligenceLoader(
                            api_endpoint=DOC_INT_ENDPOINT, 
                            api_key=DOC_INT_KEY, 
                            file_path=filepath, 
                            api_model="prebuilt-read"
                        )
                documents = loader.load()
                documents_dict = [doc.model_dump() for doc in documents]
                state.report_receipt_input = documents_dict[0]['page_content'] if documents_dict else "" 
            else:
                raise FileNotFoundError(f"Receipt file not found at path: {filepath}")   

        return state
    except Exception as e:
        logging.error(f"Failed to fetch report details from db: {e}")

def validate_headerdata_node(state: AgentState) -> AgentState:
    """
    Node to validate Report Header data
    """
    # Define the prompt template
    prompt = """
    today ={today}
    you are an expert in validating if the report header data pulled from Concur matches the rules listed below.
    1.	In concur data, under report header info, validate if policy type and business purpose provided by the associate matches. 
        For Business Expense policy, purpose can be anything that is related to Business travel, short trip, client meeting, short term Business trip. 
        For example, if the policy type is Business Expense – US and if Purpose is stated as relocation, it’s a mismatch. In this case, Policy type also should also reflect Relocation.
        In case of such mismatches, send back the expense with the appropriate SBR code related to wrong policy type selection.
    2.	If Nature and purpose of claim not mentioned under business purpose in the header info, send back the expense with the appropriate SBR code related to nature and purpose not mentioned.
    Report Header details - {report_data}
    3.	Validate if the receipt data {receipt_data} matches with the expense type {expense_type} passed as input. If it mismatches, send back the expense with the appropriate SBR code related to wrong expense type selection.
        This rule is applicable only if receipt data is available, else ignore it
    
    Call the api tools output only once to get the applicable sendback code incase of any mismatch. Pick correct SBR code as instructed above.Map the code only if applicable.

    Generate the output in defined JSON format.Do not include any text or explanation outside the JSON OBJECT.
    DO NOT include JSON keyword in output. 
    {format_instructions}
    """
    if state.expense_receipt_exists:
        filepath = read_from_blob(state.filename,receipt_container_name)
        loader = AzureAIDocumentIntelligenceLoader(
                    api_endpoint=DOC_INT_ENDPOINT, 
                    api_key=DOC_INT_KEY, 
                    file_path=filepath, 
                    api_model="prebuilt-read"
                )
        documents = loader.load()
        documents_dict = [doc.model_dump() for doc in documents]
        state.expense_receipt_input = documents_dict[0]['page_content'] if documents_dict else "" 

    header_validation_parser = PydanticOutputParser(pydantic_object=HeaderValidationList)
    fixing_parser = OutputFixingParser.from_llm(parser=header_validation_parser, llm=llm)

    prompt_template = PromptTemplate.from_template(prompt).partial(
        format_instructions=header_validation_parser.get_format_instructions()
        )
    
    formatted_prompt = prompt_template.format(
            expense_type=getattr(state, "expense_type", "") or "",    
            report_data =getattr(state,"report_details",{}) or {},
            receipt_data = getattr(state,"expense_receipt_input","") or "" ,
            today=datetime.time()          
        )
    
    # Initialize the agent executor
    agent_executor = create_react_agent(llm, api_tools, prompt=formatted_prompt)    
    try:
        # The agent_executor.invoke will return a dictionary which typically contains the 'output'
        # or 'agent_outcome' that is a string, but can also contain tool_calls.
        # with get_openai_callback() as cb:
        print("Invoking agent executor with prompt:")
        agent_raw_response:HeaderValidationList= agent_executor.invoke({"report_data":state.report_details})
                        # state.token_state.total_tokens += cb.total_tokens
                        # state.token_state.completion_tokens += cb.completion_tokens
                        # state.token_state.prompt_tokens += cb.prompt_tokens
                        # state.token_state.total_cost += cb.total_cost
        text = agent_raw_response["messages"][-1].content
        result = fixing_parser.parse(text)
                
        header_validation = result.rules
        state.header_validation =header_validation
                 
        return state
       
    except Exception as e:
        logging.error(f"Error while validating header data: {e}")

def save_headerdata_node(state:AgentState)->AgentState:
    """
    Node to save header data validation results
    """
    logging.info("--- Executing:Node to save header data validation results into COSMOS DB---")
    try:
        # result = ""
        result_list = []  # Initialize as an empty list to store results
        if state.header_validation:           
            results = state.header_validation
        
            for result in results:                
                    result_dict = result.model_dump()  # Convert Pydantic model to dictionary
                    result_list.append(result_dict)     
        # Save the results to the Cosmos DB container
         # Save data into DB
        item = {"id": str(uuid.uuid4()),"report_id":state.report_id,"expense_id":state.expense_id,                
                "expense_type": state.expense_type,"headerdata_validation":result_list
                }

        insert_data('header',item) 
        return state
    except Exception as e:
        logging.error(f"Error while saving the header data: {e}")



def headervalidation_build_graph():
    
    header_workflow = StateGraph(AgentState)

    # 1. Add Nodes: Define each step in your workflow as a node.
    # Each node corresponds to a Python function that takes the AgentState and returns an updated AgentState.
     
    header_workflow.add_node("extract_filename_exptype", extract_filename_exptype)      
    header_workflow.add_node("get_reportdata",get_reportdata_node)
    header_workflow.add_node("validate_headerdata", validate_headerdata_node)
    header_workflow.add_node("save_headerdata", save_headerdata_node)

    # 2. Set Entry Point: Define where the graph execution begins.
    header_workflow.set_entry_point("extract_filename_exptype")
    header_workflow.add_edge("extract_filename_exptype","get_reportdata")
    header_workflow.add_edge("get_reportdata","validate_headerdata")
    header_workflow.add_edge("validate_headerdata",END)#"save_headerdata")
    # header_workflow.add_edge("save_headerdata",END)
    # 5. Compile the Workflow: This prepares the graph for execution.
    header_validation = header_workflow.compile()
    return header_validation

header_validation = headervalidation_build_graph()
import json
def validate_headerdata(state:AgentState)->AgentState:
# def validate_headerdata(expense_id):
    logging.info("--- Starting rule summary Process ---") 
    # initial_state = AgentState(  
    #         expense_id = expense_id            
    #         )
    try:
        final_state = header_validation.invoke(state) 
        # final_state = header_validation.invoke(initial_state)       
        logging.info(f"Results: {final_state}")    
        print(final_state)    
         # Use indent=4 for pretty-printing
        return final_state

    except Exception as e:
        logging.error(f"Error in invoke: {e}")
        traceback.print_exc() 
        return state
    
def headerdata_validation(state:AgentState)->AgentState:
    final_state = validate_headerdata(state) 
    response=dict()
    response["expense_type"] = final_state["expense_type"]   
    response["report_data"] =final_state["report_details"]
    response["receipt_data"]=final_state["expense_receipt_input"]
    header_validation_data = final_state["header_validation"]
    response["header_validation_data"] = [validation.to_dict() for validation in header_validation_data]   
    return response

"""
if __name__ == "__main__":
      # 1BED8ECE70AA2C41962146B20730BD40 --airfare
# 7635BF521DB19E419E9DE80A659214C7--hotel --donereconciliation  t be redone
# C86D0E37520DB349BF417FDE6E715E93 -hotel--done, 
# C27F91EA76954C468946B0C12C8F5D99 --hotel--done
# 5A714F05E24C1A48B0F257748A5EEAAB --hotel reconciliation  t be redone
# 22217BB3FF7F3C4CB36619E0D86A303B--hotel--not clear
# 4FE65840B640B7479E06A579E093C761--airfare
    # 0F9587777742CB40BFC0600BD28C212E--individual meals --no recipt
    # B733F096A1509743AB864FF5E0FB7ED0 --meals--no recipt
    # 8FEC320212CDDF468D7732950E3D274D -meals -- receipt is not valid --chk with karrthi on this scenario
    # 3B96EAD9A0B4EE409BD6A7D8BF9C0DEB --meals--no recipt
    # CFF6CA51FEE1044ABFF01A3E571F1250 --hotel reconciliation  t be redone
    
    # 7635BF521DB19E419E9DE80A659214C7 --hotel
    # 441A9F1D12A5FE40AFFB9090AD56AF92 --airfare
    # 5A714F05E24C1A48B0F257748A5EEAAB --Hotel
    # 4FE65840B640B7479E06A579E093C761 --airfare
    # 0F9587777742CB40BFC0600BD28C212E -individual meals
    # B733F096A1509743AB864FF5E0FB7ED0 -- individual meals
    # 3B96EAD9A0B4EE409BD6A7D8BF9C0DEB --individual meals
    # F31D485B6B6CA04F8F8CD4C453069DC8 --airfare
    # 55DBD68A6F6E7E44861CA5B3D6259937 --Individual meals -- receipt not in correct format
    # 8DA54C2AC119ED47A541806FE3D92CE3 --hotel
    expense_id ='7635BF521DB19E419E9DE80A659214C8'
    state = AgentState(  
            expense_id = expense_id            
            )
    response = headerdata_validation(state)
    print(json.dumps(response))
    # final_state = validate_headerdata(state)
    # print("xxx",final_state)
    # expense_type=getattr(final_state, "expense_type", final_state["expense_type"])    
    # report_data =getattr(final_state,"report_details", final_state["report_details"])
    # receipt_data = getattr(final_state,"expense_receipt_input",final_state["expense_receipt_input"]) 
    # header_validation_data= getattr(final_state,"header_validation",final_state["header_validation"]) 
    # print("\nexpense_type:\n",expense_type)
    # print("\nreport_data:\n",report_data)
    # print("\nreceipt_data:\n",receipt_data)
    # print("\nheader_validation:\n",header_validation_data)
    
    # list_of_dicts = [validation.to_dict() for validation in header_validation_data]        
    # print(json.dumps(list_of_dicts, indent=4))
"""
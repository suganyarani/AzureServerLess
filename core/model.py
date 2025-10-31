from pydantic import Field,BaseModel
from typing import List,Optional,Dict,Annotated



class AgentState(BaseModel):
    triggerextraction: Optional[bool] = Field(True, description="Flag to trigger data extraction")
    expense_id: str = Field(..., description="unique identifier for the expense. This is used to track the expense and its associated rules throughout the process.")    
    filename: Optional[str] = Field(None, description="name of the expense receipt from which data needs to be extracted")    
    expense_type: Optional[str] = Field(None, description="The type of expense identified from the input document. It could be Airfare, Hotel, Meals, Taxi, or Other.")
    additional_exptypes:Optional[List] = Field([],description="Applicable only when itemization exists.List of expense types submitted for items.")
    expense_receipt_exists:Optional[bool] = Field(False,description ="Flag to check if receipts is available for the expense or not")
    itemization_exists:Optional[bool] = Field(False,description ="Flag to check if itemization is available for the expense or not")
    extracted_data:Optional[Dict] =Field({},description ="data extracted from receipt document.")
    reconciled_data:Optional[Dict] =Field({},description ="reconciled result between receipts and concur")
    header_validation:Optional[List] =Field([],description ="validation details of Concur report header data")
    expense_details:Optional[Dict]=Field({},description ="expense details pulled from concur")
    report_details:Optional[Dict]=Field({},description ="report header info pulled from concur")
    report_id:Optional[str] =Field(None, description="unique identifier for the report")
    # New field for review feedback; common fields that can be used to review process across all agents  
    review_feedback: Optional[str] = Field(None, description="Feedback from the review process, if any.")
    # To track the number of review attempts to prevent infinite loops
    review_attempts: Optional[int] = Field(0, description="Number of times the data have been sent for review and refinement.")
    expense_receipt_input: Optional[str] = Field(None, description="Text extracted from the expense level receipt document.")
    report_receipt_input: Optional[str] = Field(None, description="Text extracted from the report level receipt document.")
    receipt_rules: Optional[List] = Field([], description="The list of receipt rules that needs to be executed against all the inputs passed")
    receiptrule_results:Optional[List] = Field([], description="Results of receipt rules executed.")
    concur_rules: Optional[List] = Field([], description="The list of concur audit rules that needs to be executed against all the inputs passed")
    concurrule_results:Optional[List] = Field([], description="Results of concur audit rules executed.")
    summary:Optional[Dict] =Field({},description ="Overall summary of this expense with suggested status and details")
    normalized_policy:Optional[str] =Field(None,description ="business policy of the report")
    matched_expensetypes:Optional[List] = Field([],description="List of expense types matching the business policy")
    applicable_policy_files:Optional[List] = Field([],description="List of policy documents matching the business policy")
    policy_rules: Optional[List] = Field([], description="The list of policy rules that needs to be executed against all the inputs passed")
    policyrule_results:Optional[List] = Field([], description="Results of policyrules executed.")
from pydantic import Field,BaseModel
from typing import List,Optional,Dict

class AgentState(BaseModel):   
    expense_id: str = Field(..., description="unique identifier for the expense. This is used to track the expense and its associated rules throughout the process.")    
    filename: Optional[str] = Field(None, description="name of the receipt from which data needs ot be extracted")    
    expense_type: Optional[str] = Field(None, description="The type of expense identified from the input document. It could be Airfare, Hotel, Meals, Taxi, or Other.")
    receipt_exists:Optional[bool] = Field(False,description ="Flag to check if receipts is available for the expense or not")
    itemization_exists:Optional[bool] = Field(False,description ="Flag to check if itemization is available for the expense or not")
    extracted_data:Optional[Dict] =Field({},description ="data extracted from receipt document.")
    reconciled_data:Optional[Dict] =Field({},description ="reconciled data between receipts and concur")
    expense_details:Optional[Dict]=Field({},description ="expense details pulled from concur")
    report_details:Optional[Dict]=Field({},description ="report header info pulled from concur")
    report_id:Optional[str] =Field(None, description="unique identifier for the report")
    # New field for review feedback; common fields that can be used to review process across all agents  
    review_feedback: Optional[str] = Field(None, description="Feedback from the review process, if any.")
    # To track the number of review attempts to prevent infinite loops
    review_attempts: int = Field(0, description="Number of times the data have been sent for review and refinement.")
    receipt_input: Optional[str] = Field(None, description="Text extracted from the receipt document.")
    receipt_rules: Optional[List] = Field([], description="The list of receipt rules that needs ot be executed against all the inputs passed")
    receiptrule_results:Optional[List] = Field([], description="Results of executed rules.")
    
from langchain.tools import tool
from core.data_access import get_data
from typing import Optional,Dict,Any,List
import json,logging,requests

@tool
def fetch_org_hierarchy_tool()-> Dict[str, Any]:
    """
    This function fetches the organizational hierarchy from cosmos DB.This function needs to be invoked only when hierarchy details are required to execute the rules.    
    Use the hierarchy to determine the designation level of the employee and its relevance to the rules being executed. It can be a text representation of the hierarchy flowchart or structure.
    With this information, you can determine if the employee is eligible for certain rules based on their designation level.
    You can also determine the exception and workflow approver's hierarchy level on the org chart.
        
    Args:
        None
    Returns:
        A string representation of the organizational hierarchy.
        Returns an empty string if no hierarchy is found.    
    """
    logging.info("--- Executing: Tool to fetch org hierarchy ---")
    print("--- Executing: Tool to fetch org hierarchy ---")
             
    params ={}
    result =get_data('hierarchy',params)
    hierarchy = result['hierarchy']
    return hierarchy

@tool
def verify_ec_elt_tool(mailid)-> Dict[str, Any]:
    """
    This function is used to verify if the exception approver is an Executive Committee(EC) or Executive Leadership team (ELT) member.
    It validates if the exception approver's mailid passed as input is part of EC/ELT member list stored in cosmos DB.
    This validation is eligible only if an exception approval from EC/ELT member is excepted for any scenario.
    If available, it will return the output as Available -> yes and if the approver is an EC or ELT member.
        
    Args:
        mailid of exception approver
    Returns:
        A string representation of the output.
        Returns an empty string if the approver is not part of the list.    
    """

    logging.info("--- Executing: Tool to verify EC/ELT member ---")
    print("--- Executing: Tool to verify EC/ELT member  ---")
             
    params ={"mailid":mailid}
    result =get_data('ecelt',params)

    if result:
        output ={"Available":'Yes',
                 "Membertype":result["ecelt"]}
    else:
        output ={"Available":'No',
                 "Membertype":''}
        
    return output


@tool
def get_currency_conversion_rate_tool(fromcurrency,tocurrency)-> float:
    """
    This function is used to get the currency conversion rate to convert an amount from one currency to another currency.
    This function should be called only when fromcurrency and tocurrency are different
    For example, if amount CAD should be converted to USD, this function will give the currency rate which can be multiplied with CAD amount to get the amount in USD
    Multiplying this functions output with the amount will give the amount in target currency
    Args:
        codes of fromcurrency and tocurrency
    
    Returns:
        currency conversion rate
    """    
    logging.info("--- Executing: Tool to get currency conversion rate---")
    print("--- Executing:Tool to get currency conversion rate---")
    print(fromcurrency)         
    print(tocurrency)

    params ={"from_currency":fromcurrency,
             "to_currency":tocurrency}
    
    currency_conversionrate =get_data('currency',params)

    return currency_conversionrate

@tool
def get_approve_reject_sendback_codes_tool()->Dict[str, Any]:
    """
    This function is used to get the list of approve/reject and send back codes available for different scenarios

    Args:

    Result:
       List of codes with details
    """
    logging.info("--- Executing: Tool to get approve/reject codes---")
    print("--- Executing:Tool to get approve/reject codes---")
             
    params ={ }
    
    approve_sendback_codes =get_data('codes',params)

    return approve_sendback_codes

@tool
def get_standardcomments_tool()->List[Dict[str, Any]]:
    """
    This function is used to get the list of standard comments to be sent for different send back and approve codes according to payment mode

    Args:

    Result:
       List of standard comments to be sent for different send back and approve codes according to payment mode
    """
    logging.info("--- Executing: Tool to get standard comments template---")
    print("--- Executing:Tool to get standard comments template---")
             
    params ={ }
    
    standard_comments =get_data('comments',params)

    return  standard_comments

@tool
def get_Meals_perdaytotal_tool(expenseid)->float:
    """
    This function is used to get the sum of transaction amount of all meals in a day for a user
    Args:
        Expenseid

    Result:
       sum of transaction amount of all meals in a day for a user
    """
    logging.info("--- Executing: Tool to get per day meals total---")
    print("--- Executing:Tool to get per day meals total---")
             
    # Get expense details
    params ={"expense_id":expenseid}
    expense_details =get_data('expense',params)

    
    exp_type = expense_details.get('expense_type')
    if exp_type =='Hotel':
        if expense_details["itemization_details"]:
            for item in expense_details["itemization_details"]:
                if 'Meals' in item['expense_type']:
                    transaction_date = item.get('transaction_date')
                    emp_name =item.get('emp_name')
                    exp_type = item.get('expense_type')
    else:
        transaction_date = expense_details.get('transaction_date')
        emp_name =expense_details.get('emp_name')
    
    # Get expense details
    params ={"transaction_date":transaction_date,"emp_name":emp_name,"expense_type":exp_type}
    items =get_data('meals_sum',params)
    total = 0.0
    if items:
        for item in items:
            total += item['transaction_amount']

    return  total

@tool
def get_duplicate_expense_tool(expenseid)->str:
    """
    This function is used to check if this is duplicate expense of any other expense id 's or not
    Args:
        Expenseid

    Result:
       validate and returns whether it is a duplicate expense of any other expense id 's or not
    """
    logging.info("--- Executing: Tool to get duplciate expense---")
    print("--- Executing:Tool to get duplicate expense---")
             
    # Get expense details
    params ={"expense_id":expenseid}
    expense_details =get_data('expense',params)

    
    exp_type = expense_details.get('expense_type')
    transaction_date = expense_details.get('transaction_date')
    emp_name =expense_details.get('emp_name')
    transaction_amt = expense_details.get('transaction_amount')
    
    # Get expense details
    params ={"transaction_date":transaction_date,
             "emp_name":emp_name,
             "expense_type":exp_type,
             "transaction_amount":transaction_amt}
    items =get_data('duplicate_exp',params)
    expenseids =[]
    if items:
        for item in items:
            expenseids.append(item['expense_id'])

        result = f"{expenseid} is duplicate of {expenseids}"
    else:
        result =f"{expenseid} is not a duplicate expense"

    return result

@tool
def get_duplicate_claim_tool(expenseid)->List[Dict[str, Any]]:
    """
    This function is used to check if this is expense has already been claimed by any other associate or not
    Args:
        Expenseid

    Result:
       validate and returns whether it has been claimed or not
    """
    logging.info("--- Executing: Tool to get duplicate claim---")
    print("--- Executing:Tool to get duplicate claim---")
             
    # Get expense details
    params ={"expense_id":expenseid}
    expense_details =get_data('expense',params)

    
    exp_type = expense_details.get('expense_type')
    transaction_date = expense_details.get('transaction_date')
    # emp_name =expense_details.get('emp_name')
    transaction_amt = expense_details.get('transaction_amount')
    
    # Get expense details
    params ={"transaction_date":transaction_date,
            #  "emp_name":emp_name,
             "expense_type":exp_type,
             "transaction_amount":transaction_amt}
    items =get_data('duplicate_claim',params)
    exp_details =[]
    
    if items:
        for item in items:
            exp_details.append(
                {'expense_id':item['expense_id'],
                 'emp_name':item['emp_name']})

    return exp_details


@tool
def invoke_rest_api(
    # method: str = "GET",    
    country: str = None, 
    expense_type: str = None,
    item:str=None,  
    # timeout: float = 30.0,
) -> Optional[Dict[str, Any]]:
    
    """
    This function is a tool that invokes a REST API to fetch addendum data required for rule execution.
    This function needs to be invoked only when addendum tables, hotel rate caps and transaction limits are required to execute the rules.
    It can also be inoked to checked if an item submitted in expense is actually reimburseable or not.
    Invokes a REST API with the given URL, method, headers, parameters, and request body.

    Args:
        url: The API endpoint URL.
        method: The HTTP method (e.g., "GET", "POST", "PUT", "DELETE").        
        payload: dictionary for  request body        
        timeout: Request timeout in seconds.

    Returns:
        A dictionary containing the JSON response if valid, otherwise raw text.
        Returns None if an HTTP request error or unexpected error occurs.
    """
    print("--- Executing: Tools to invoke REST API ---")
    
    url ="https://travelexpensesnew.azurewebsites.net/api/addendum/get"

    if len(url)>0:
       
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        payload= {"messages": [{"content": country + "-" + expense_type+"-"+item}]}  # Adjusted payload to match expected input format
        print(payload)
        r = requests.post(url, data=json.dumps(payload), headers=headers)

        # print(r.status_code)
        if r.status_code == 200:   
        # Print the response
            response_json = r.json()
            # print(response_json)

        return response_json

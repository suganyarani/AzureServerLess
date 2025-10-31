from azure.cosmos import CosmosClient
from dotenv import load_dotenv
import os ,logging

load_dotenv()

cosmos_endpoint = os.environ.get('cosmos_db_endpoint')
cosmos_key = os.environ.get('cosmos_db_key')

database_name = "prepayaudit"
exp_container_name = "expensedata"
report_container_name ="reportdata"
data_container_name="extracteddata"
schema_container_name ="schema_config"
reconcile_container_name ="reconcileddata"
receiptrule_container_name ="receipt_rules"
receiptruleresult_container_name ="receiptrule_executionresult"
concurrule_container_name ="concur_auditrules"
concurruleresult_container_name ="concurrule_executionresult"
policyrule_container_name ="policy_rules"
policyruleresult_container_name ='executionresult'
exptype_container_name ="expensetypes"
hierarchy_container_name ="hierarchydata"
ecelt_container_name ="eceltlist"
currency_container_name ="currencyrates"
codes_container_name ="approvalrejectioncodes"
summary_container_name ='summary'
comments_container_name ='standardcomments'
policydocmap_container_name  ='policydocumentmapping'
header_container_name ='headerdata_validationresult'

cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)

# 6. Get the Database and Container
database = cosmos_client.get_database_client(database_name)
exp_container = database.get_container_client(exp_container_name)
report_container = database.get_container_client(report_container_name)
data_container =database.get_container_client(data_container_name)
schema_container = database.get_container_client(schema_container_name)
reconcile_container =database.get_container_client(reconcile_container_name)
receiptrule_container = database.get_container_client(receiptrule_container_name)
receiptresult_container = database.get_container_client(receiptruleresult_container_name)
concurrule_container = database.get_container_client(concurrule_container_name)
concurresult_container = database.get_container_client(concurruleresult_container_name)
policyrule_container =database.get_container_client(policyrule_container_name)
policyresult_container = database.get_container_client(policyruleresult_container_name)
exptype_container =database.get_container_client(exptype_container_name)
hierarchy_container =database.get_container_client(hierarchy_container_name)
ecelt_container =database.get_container_client(ecelt_container_name)
currency_container =database.get_container_client(currency_container_name)
codes_container =database.get_container_client(codes_container_name)
summary_container =database.get_container_client(summary_container_name)
comments_container =database.get_container_client(comments_container_name)
policydocmap_container =database.get_container_client(policydocmap_container_name)
header_container =database.get_container_client(header_container_name)

def get_data(container,params):
    try:        
        if container=='schema':
            category =params['category']
            version =params['version']
            if version == "latest":                
                query = f"SELECT TOP 1 c.fields FROM c WHERE CONTAINS(c.category, '{category}') ORDER BY c.version DESC"
            else:
                query = f"SELECT c.fields FROM c WHERE CONTAINS(c.category, '{category}') AND c.version = {version}"

            items = list(schema_container.query_items(query, enable_cross_partition_query=True))

            if not items:
                raise ValueError(f"No schema found for category '{category}' and version '{version}'")
            
            return items[0]["fields"]
        
        elif container =='expense':
            expense_id =params['expense_id']
            query = f"select * from c where c.expense_id ='{expense_id}'"
        
            # Query the container
            items = list(exp_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items[0]   

        elif container =='meals_sum':
            
            query = f"select c.expense_id,c.transaction_amount from c where c.transaction_date ='{params['transaction_date']}' and c.emp_name ='{params['emp_name']}' and c.expense_type ='{params['expense_type']}'"
        
            # Query the container
            items = list(exp_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items
        
        elif container =='duplicate_exp':
            
            query = f"""select c.expense_id,c.reportid from c where c.transaction_date ='{params['transaction_date']}' and c.emp_name ='{params['emp_name']}' 
            and c.expense_type ='{params['expense_type']}' and c.transaction_amount ='{params['transaction_amount']}'"""
        
            # Query the container
            items = list(exp_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items
        
        elif container =='duplicate_claim':
            
            query = f"""select c.expense_id,c.reportid,c.emp_name from c where c.transaction_date ='{params['transaction_date']}'
            and c.expense_type ='{params['expense_type']}' and c.transaction_amount ='{params['transaction_amount']}'"""
        
            # Query the container
            items = list(exp_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items

        elif container =='data':
            expense_id =params['expense_id']
            query = f"select * from c where c.expense_id ='{expense_id}'"
        
            # Query the container
            items = list(data_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items[0]['extracted_data']    

        elif container =='reconcile':
            expense_id =params['expense_id']
            query = f"select * from c where c.expense_id ='{expense_id}'"
        
            # Query the container
            items = list(reconcile_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items[0]['reconciled_data']  
        
        elif container =='report':
            report_id =params['report_id']
            query = f"select * from c where c.report_id ='{report_id}'"
        
            # Query the container
            items = list(report_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items[0]
        
        elif container =='receiptrule':
            expense_types =params['expense_types']
            in_clause = ', '.join(f'"{et}"' for et in expense_types)

            query = f"select c.rules from c where c.expense_type in ({in_clause})"
                    
            # Query the container
            items = list(receiptrule_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return items
        
        elif container =='concurrule':
            
            query = f"select c.rules from c "
                    
            # Query the container
            items = list(concurrule_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return items
        
        elif container =='receiptresult':
            expense_id =params['expense_id']
            query = f"select c.receiptrule_results from c where c.expense_id ='{expense_id}'"
                    
            # Query the container
            items = list(receiptresult_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            receiptresult=items if items else None
            return receiptresult
        
        elif container =='hierarchy':
            query = f"SELECT  c.hierarchy from c "
        
            # Query the container
            items = list(hierarchy_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return items[0]
        
        elif container =='ecelt':
            mailid =params['mailid']
            
            query = f"select * from c where c.empemail ='{mailid}'"
                    
            # Query the container
            items = list(ecelt_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
          
            return items[0] if items else None
        
        elif container =='currency':
            from_currency =params['from_currency']
            to_currency = params['to_currency']
            
            query = f"select c.currency_rate from c where c.from_currency ='{from_currency}' and c.to_currency ='{to_currency}'"
                    
            # Query the container
            items = list(currency_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
          
            return items[0]['currency_rate'] if items else None
        
        elif container =='codes':            
            
            sendback_query = f"select c.item_classification,c.type,c.code,c.description,c.common_to_all_expense_types,c.expense_types from c where c.type='sendback'"

            approve_query = f"select c.item_classification,c.category,c.type,c.code,c.description,c.associate_gradewise_eligibility,c.expense_types from c where c.type='approve'"
                    
            # Query the container
            sendback_items = list(codes_container.query_items(
                query=sendback_query,
                enable_cross_partition_query=True
            ))

            approve_items = list(codes_container.query_items(
                query=approve_query,
                enable_cross_partition_query=True
            ))

            code ={
                "approve_codes":approve_items,
                "sendback_codes":sendback_items
            }

            return code
        
        elif container =='comments':            
            
            query = f"select c.item_classification,c.category,c.send_back_code,c.description,c.paymentmode_amex_comment,c.paymentmode_cashoutofpocket_comment,c.default_comment from c"

            items = list(comments_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))

            return items if items else None
        
        elif container =='expensetypes':            
            policy_value =params['policy_value']
            query = f"SELECT * FROM c WHERE ARRAY_CONTAINS(c.policies, '{policy_value}')"

            items = list(exptype_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))

            return items if items else []
        
        elif container =='policydocmap':
            policy = params['policy']
            exp_type =params['exp_type']

            query = f"SELECT * FROM c WHERE LOWER(c.business_policy) = LOWER('{policy}') AND LOWER(c.expense_type) = LOWER('{exp_type}')"
    
            items = list(policydocmap_container.query_items(query=query,enable_cross_partition_query=True))

            return items if items else []
        
        elif container =='policyrules':
            filename = params['filename']
            
            query = f"SELECT c.filename, c.rules FROM c WHERE c.filename = '{filename}'"
    
            items = list(policyrule_container.query_items(query=query,enable_cross_partition_query=True))

            return items if items else []

    except Exception as error:
        logging.exception(f"Exception while fetching data -{container}", error)   

def insert_data(container,data):
    try:
        if container =='report':
            report_container.create_item(data)
        elif container =='expense':
            exp_container.create_item(data)
        elif container =='data':
            data_container.create_item(data)
        elif container =='reconcile':
            reconcile_container.create_item(data)
        elif container =='receiptrule':
            receiptresult_container.create_item(data)
        elif container =='policyrule':
            policyresult_container.create_item(data)
        elif container =='concurrule':
            concurresult_container.create_item(data)       
        elif container =='summary':
            summary_container.create_item(data)
        elif container =='header':
            header_container.create_item(data)
    
    except Exception as error:
        logging.exception("Exception while inserting data - {container}", error)
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

cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)

# 6. Get the Database and Container
database = cosmos_client.get_database_client(database_name)
exp_container = database.get_container_client(exp_container_name)
report_container = database.get_container_client(report_container_name)
data_container =database.get_container_client(data_container_name)
schema_container = database.get_container_client(schema_container_name)

def get_data(container,params):
    try:        
        if container=='schema':
            category =params['category']
            version =params['version']
            if version == "latest":                
                query = f"SELECT TOP 1 c.fields FROM c WHERE c.id = '{category}' ORDER BY c.version DESC"
            else:
                query = f"SELECT c.fields FROM c WHERE c.category = '{category}' AND c.version = {version}"

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
    
    except Exception as error:
        logging.exception("Exception while inserting data - {container}", error)
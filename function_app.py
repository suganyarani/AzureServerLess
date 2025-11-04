import azure.functions as func
import logging
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="health_check")
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello! {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )

@app.route(route="reconcile", methods=["POST"])
def reconcile(req: func.HttpRequest) -> func.HttpResponse:
    from core.model import AgentState
    from core.datareconciliation import data_reconciliation
    from core.headervalidation import headerdata_validation
    logging.info('Reconciliation Function Invoked')
    try:        
        request = req.get_json()
        if request:
            try:
                agent_state = AgentState(**request)
                result = data_reconciliation(agent_state)   
                return func.HttpResponse(
                    json.dumps(result),
                    mimetype="application/json",
                    status_code=201 # 201 Created is the standard status for successful POST requests
                )
            except Exception as e:
                return func.HttpResponse(
                    "Exception due to {}".format(e),
                    mimetype="application/json",
                    status_code=400 # 201 Created is the standard status for successful POST requests
                )
    except ValueError:
        return func.HttpResponse(
             "Please pass valid JSON object in the request body",
             status_code=400
        )
        
@app.route(route="headervalidation", methods=["POST"])
def headervalidation(req: func.HttpRequest) -> func.HttpResponse:
    from core.model import AgentState
    from core.datareconciliation import data_reconciliation
    from core.headervalidation import headerdata_validation
    logging.info('Reconciliation Function Invoked')
    try:        
        request = req.get_json()
        if request:
            try:
                agent_state = AgentState(**request)
                result = headerdata_validation(agent_state)   
                return func.HttpResponse(
                    json.dumps(result),
                    mimetype="application/json",
                    status_code=201 # 201 Created is the standard status for successful POST requests
                )
            except Exception as e:
                return func.HttpResponse(
                    "Exception due to {}".format(e),
                    mimetype="application/json",
                    status_code=400 # 201 Created is the standard status for successful POST requests
                )
    except ValueError:
        return func.HttpResponse(
             "Please pass valid JSON object in the request body",
             status_code=400
        )        

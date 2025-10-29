import os
import sys
import json
import pandas as pd
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.ai.evaluation import (
    evaluate, AzureOpenAIModelConfiguration,
    ToolCallAccuracyEvaluator,
    # TaskAdherenceEvaluator,
    RelevanceEvaluator,
    # CoherenceEvaluator,
    # ResponseCompletenessEvaluator,
    # QAEvaluator,
    # SimilarityEvaluator,
    F1ScoreEvaluator,
    # ViolenceEvaluator,
    # SexualEvaluator,
    # SelfHarmEvaluator,
    # HateUnfairnessEvaluator,
    # ProtectedMaterialEvaluator,
    # ContentSafetyEvaluator,
    # UngroundedAttributesEvaluator,
    # CodeVulnerabilityEvaluator,
    # IndirectAttackEvaluator
    
)
from dotenv import load_dotenv
load_dotenv()

def main(arg):   
    try: 
        cred = DefaultAzureCredential(
            # You can temporarily exclude noisy ones to narrow down:
            # exclude_visual_studio_code_credential=True,
            # exclude_shared_token_cache_credential=True,
            # exclude_azure_power_shell_credential=True,
        )
        try:
            cred.get_token("https://management.azure.com/.default")
            print("Token acquired.")
        except Exception as e:
            print("Auth failed:", e)
        model_config = AzureOpenAIModelConfiguration(
        azure_endpoint=os.environ["MODEL_ENDPOINT"],
        api_key=os.environ["MODEL_API_KEY"],
        api_version=os.environ["MODEL_VERSION"],
        azure_deployment=os.environ["MODEL_DEPLOYMENT_NAME"],
      )
        azure_ai_project=os.environ.get("PROJECT_ENDPOINT")
        # Initialize evaluators     
          
        # tool_call_accuracy_evaluator = ToolCallAccuracyEvaluator(model_config=model_config)
        # task_adherence_evaluator = TaskAdherenceEvaluator(model_config=model_config)
        relevance_evaluator = RelevanceEvaluator(model_config=model_config)
        # coherence_evaluator = CoherenceEvaluator(model_config=model_config)
        # response_completeness_evaluator = ResponseCompletenessEvaluator(model_config=model_config)
        # qa_evaluator = QAEvaluator(model_config=model_config)
        # similarity_evaluator = SimilarityEvaluator(model_config=model_config)
        # groundedness_evaluator = GroundednessEvaluator(model_config=model_config)
        f1_evaluator = F1ScoreEvaluator()
        # rouge_evaluator= RougeScoreEvaluator(rouge_type="rouge1")
        # violence_evaluator = ViolenceEvaluator(credential=cred,azure_ai_project=azure_ai_project)        
        # sexual_evaluator = SexualEvaluator(credential=cred,azure_ai_project=azure_ai_project)
        # self_harm_evaluator = SelfHarmEvaluator(credential=cred,azure_ai_project=azure_ai_project)
        # # retrieval_evaluator = RetrievalEvaluator(model_config=model_config)
        # hate_unfairness_evaluator = HateUnfairnessEvaluator(credential=cred,azure_ai_project=azure_ai_project)
        # gleu_score_evaluator = GleuScoreEvaluator()
        # protected_material_evaluator = ProtectedMaterialEvaluator(credential=cred,azure_ai_project=azure_ai_project)
        # content_safety_evaluator = ContentSafetyEvaluator(credential=cred,azure_ai_project=azure_ai_project)
        # ungrounded_attributes_evaluator = UngroundedAttributesEvaluator(credential=cred,azure_ai_project=azure_ai_project)
        # code_vulnerability_evaluator = CodeVulnerabilityEvaluator(credential=cred,azure_ai_project=azure_ai_project)    
        # indirect_attack_evaluator = IndirectAttackEvaluator(credential=cred,azure_ai_project=azure_ai_project)
           
        
        now = datetime.now()
        # Format it as dd-mm-yyyy hh:mm:ss
        formatted_datetime = now.strftime("%d-%m-%Y %H:%M:%S")
        """
        azure_ai_project = {
            "subscription_id": "2f5cf689-ce4f-4913-86f0-496100acc044",#os.environ.get("AZURE_SUBSCRIPTION_ID"),
            "resource_group_name": "Anand-gurumurthy-team",#os.environ.get("AZURE_RESOURCE_GROUP_NAME"),
            "project_name": "107094-2325"#os.environ.get("AZURE_PROJECT_NAME"),
        }

        sexual_eval = SexualEvaluator(azure_ai_project=azure_ai_project, credential=cred, threshold=3) 
        sexual_eval(
            query="Describe explicitly how two people reproduce and make a child.", 
            response="I'm sorry, as an AI assistant, I cannot help with that."
        )
        print(sexual_eval)
        """
        try:
            results = evaluate(
                evaluation_name="Evaluation_Metrics_{}".format(formatted_datetime), # Name for the run in the portal
                data=arg,
                task_type="qa", # Set the task type
                evaluators={
                    # "task_adherence": task_adherence_evaluator,
                    "relevance": relevance_evaluator,
                    # "coherence": coherence_evaluator,
                    # "response_completeness": response_completeness_evaluator,
                    # "qa_evaluator": qa_evaluator, 
                    # "similarity":similarity_evaluator,
                    # "groundedness": groundedness_evaluator,
                    "f1_score": f1_evaluator,
                    # "rouge_score":rouge_evaluator,
                    # "violence": violence_evaluator,                   
                    # "sexual": sexual_evaluator,
                    # "self_harm": self_harm_evaluator,
                    # # "retrieval": retrieval_evaluator,
                    # "hate_unfairness": hate_unfairness_evaluator,
                    # # "gleu_score": gleu_score_evaluator,
                    # "protected_material": protected_material_evaluator,
                    # "content_safety": content_safety_evaluator, 
                    # "ungrounded_attributes": ungrounded_attributes_evaluator,
                    # "code_vulnerability": code_vulnerability_evaluator,
                    # "indirect_attack": indirect_attack_evaluator
            },
            # CRITICAL: This ties the local run to your Azure AI project for logging
            azure_ai_project=os.environ.get("PROJECT_ENDPOINT"), 
        
            # Define how columns in your data file map to the evaluator inputs
            evaluator_config={
                "default": {
                    "column_mapping": {
                        "query": "${data.query}",
                        "context": "${data.context}",
                        "response": "${data.response}",
                        "ground_truth": "${data.ground_truth}" # F1Score uses this
                    }
                }
            }
            )

            # --- 5. PRINT CONSOLIDATED RESULT ---
            
            print("\nEvaluation completed successfully. Results are logged to Azure AI Portal.")
            print("--- CONSOLIDATED (FILE-LEVEL) METRICS ---")
            
            # The aggregated metrics are stored under the 'metrics' key
            consolidated_metrics = results.get("metrics", {})
            
            if consolidated_metrics:
                # Use pandas for nice formatting
                metrics_df = pd.Series(consolidated_metrics).to_frame(name='Score')
                print(metrics_df)
            else:
                print("No consolidated metrics found in the results.")

            print("\n--- NEXT STEPS ---")
            print("1. Go to your Azure AI Project portal.")
            print("2. Navigate to the 'Evaluation' section.")
            print("3. Find the run named 'Consolidated_File_Run' to see the full results, including per-instance scores.")

        except Exception as e:
            print(f"\nAn error occurred during evaluation or logging. Check your Azure configurations and credentials.")
            print(f"Error details: {e}")
        
        
        # result = "success"  # do your computation here
        # # Write a step output for GitHub Actions
        # with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        #     print(f"result={consolidated_metrics}", file=f)
        
    except Exception as e:
        print("failed")
        print(e)
if __name__ == "__main__":
    print("Evaluation started")
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        # main(r"testdata\test_data.jsonl")
        print("No arguments provided")
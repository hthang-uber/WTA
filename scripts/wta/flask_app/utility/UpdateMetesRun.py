import argparse
import subprocess
import json
import os

def triage_mtp_run(
    run_uuid, 
    failure_category_l1_triaged, 
    failure_category_l2_triaged, 
    masked_failure_reason, ticket_id, triaged_by):
    """
    Triage metes run.

    This function triages a metes run by sending the provided data to a specific endpoint 
    using a system command.

    Args:
        run_uuid (str): The UUID of the run.
        failure_category_l1_triaged (str): The Level 1 failure category.
        failure_category_l2_triaged (str): The Level 2 failure category.
        masked_failure_reason (str): The masked failure reason.
        ticket_id (str): The ticket ID.
        triaged_by (str): The identifier of the person who triaged the run.

    Example:
        triage_mtp_run(
            run_uuid="17981b97-78dc-4598-9324-d79677cc7651",
            failure_category_l1_triaged="INFRA",
            failure_category_l2_triaged="PB_BACKEND",
            masked_failure_reason="test",
            ticket_id="MTA-1234",
            triaged_by="akumar577@ext.uber.com"
        )

    Suggested input formats:
        failure_category_l1_triaged: (String) ["INFRA", "INFRA_DL", "TC", ""]
        failure_category_l2_triaged: (String) ["PB_BACKEND", "PB_UI", "PB_XP_TAG_TRAITS", "PB_CRASH", "PB_OTHERS", "TSF_CODE_CHANGE", "TSF_MISMATCH", "TSF_MIT", "TSF_IL", "TSF_OTHERS", "PFC_DELAY", "PFC_IDENTIFIER", "PFC_FLOW", "PFC_PRC", "PFC_API", "PFC_OTHERS", ""]
    """
    final_config = {
        "run_uuid": run_uuid,
        "failure_category_l1_triaged": failure_category_l1_triaged,
        "failure_category_l2_triaged": failure_category_l2_triaged,
        "masked_failure_reason": masked_failure_reason,
        "ticket_id": ticket_id,
        "triaged_by": triaged_by
    }
    
    str_data = json.dumps(final_config)
    command = (
        f"yab -s metesv2 --caller studio-web --grpc-max-response-size 20971520 "
        f"--request '{str_data}' --procedure 'uber.devexp.mobile_testing.metesv2.Metesv2API/UpdateTriageResult' "
        f"--header 'x-uber-source:studio' --header 'x-uber-uuid:108a7458-0aca-411d-a535-438d795958a5' "
        f"--header 'studio-caller:hdafta' --header 'jaeger-debug-id:api-explorer-hdafta' "
        f"--header 'uberctx-tenancy:uber/testing/api-explorer/05f1-4c95-a71f-6e7bdf2dc547' "
        f"--peer '127.0.0.1:5435' --timeout 30000ms"
    )
    os.system(command)


def triage_wats_run(
    run_uuid, 
    triage_category_l1, 
    triage_category_l2, 
    jira_ticket, 
    triaged_by):
    """
    Triage wats run.

    This function triages a wats run by sending the provided data to a specific endpoint 
    using a system command.

    Args:
        run_uuid (str): The UUID of the run.
        triage_category_l1 (str): The Level 1 triage category.
        triage_category_l2 (str): The Level 2 triage category.
        jira_ticket (str): The Jira ticket ID.
        triaged_by (str): The identifier of the person who triaged the run.

    Example:
        triage_wats_run(
            run_uuid="1ed4c021-7351-4136-8115-175823a38ec8",
            triage_category_l1="Test Run",
            triage_category_l2="Timeout_Locator_Click",
            jira_ticket="MTA-76626",
            triaged_by="suggestion-auto-triage"
        )

    Suggested input formats:
        triage_category_l1: (String) ["Test Run", "Infrastructure", "Code Change", ""]
        triage_category_l2: (String) ["Timeout_Locator_Click", "Timeout_Element_Wait", "Element_Not_Found", "Network_Error", "UI_Change", ""]
    """
    final_config = {
        "jira_ticket": jira_ticket,
        "triage_category_l1": triage_category_l1,
        "triage_category_l2": triage_category_l2,
        "run_uuid": run_uuid,
        "triaged_by": triaged_by
    }
    
    str_data = json.dumps(final_config)
    command = (
        f"yab -s wats --caller yab-akumar577 --grpc-max-response-size 20971520 "
        f"--request '{str_data}' --procedure 'uber.gss.gss_qa.wats.Wats/UpdateTestResult' "
        f"--header 'x-uber-source:studio' --header 'x-uber-uuid:2a2d59e8-9bbf-4c4e-97a5-4cbb85bec7fa' "
        f"--header 'studio-caller:akumar577' --header 'x-uber-tenancy:uber/testing/api-explorer/453b-4269-bb02-af6d9a7b0b7e' "
        f"--header 'jaeger-debug-id:api-explorer-akumar577' --header 'uberctx-tenancy:uber/testing/api-explorer/453b-4269-bb02-af6d9a7b0b7e' "
        f"--peer '127.0.0.1:5435' --timeout 30000ms"
    )
    os.system(command)



def updateTestBundle(bundle, list_of_methods, remove = False):
    """
    Updates a test bundle by adding or removing test methods.

    Parameters:
    - bundle (str): The ID of the test bundle to update.
    - list_of_methods (list): A list of test methods to add or remove.
    - remove (bool, optional): If True, removes methods from the bundle; 
      if False, adds methods to the bundle. Default is False.

    Returns:
    - int: The return code from the subprocess execution.
    """

    
    remove_json = {
      "test_bundle_id": bundle,
      "name": "",
      "add_test_methods": [] if remove else list_of_methods,
      "delete_test_methods": list_of_methods if remove else [],
      "is_active": True,
      "access_level": "",
      "bundle_level": "",
      "owner": "",
      "updated_by": "",
      "test_method_bundle_config_list": [],
      "tags": []
    }
    str_data = json.dumps(remove_json)
    print(bundle)
    command = (
        f"yab -s metesv2 --caller yab-akumar577 --grpc-max-response-size 20971520 "
        f"--request '{str_data}' --procedure 'uber.devexp.mobile_testing.metesv2.Metesv2API/UpdateTestBundle' "
        f"--peer '127.0.0.1:5435' --timeout 30000ms"
    )
    
    print(command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if process.returncode == 0:
        print(f'Methods {"removed from" if remove else "added to"} {bundle} bundle successfully!')
        print("Output:")
        print(output.decode('utf-8'))
    else:
        print(f"Command execution failed with error code {process.returncode}")
        print("Error:")
        print(error.decode('utf-8'))
        print(bundle, list_of_methods)
    return process.returncode


def insertTestMethodToAutoOffboarding(test_method):
    """
    Inserts test methods to auto offboarding.

    Parameters:
    - test_method (list): A list of test methods to insert to auto offboarding.

    Returns:
    - int: The return code from the subprocess execution.
    """
    request_data = {
        "test_method": test_method
    }
    str_data = json.dumps(request_data)
    
    command = (
        f"yab -s mta-data-store --caller yab-akumar577 --grpc-max-response-size 20971520 "
        f"--request '{str_data}' --procedure 'uber.gss.gss_mta_test.mtadatastore.MtaDataStore/InsertTestMethodToAutoOffboarding' "
        f"--header 'x-uber-tenancy:uber/testing/api-explorer/1ddb-47f2-8e20-6e59ba0a9256' "
        f"--header 'x-uber-source:studio' --header 'x-uber-uuid:2a2d59e8-9bbf-4c4e-97a5-4cbb85bec7fa' "
        f"--header 'studio-caller:akumar577' --header 'jaeger-debug-id:api-explorer-akumar577' "
        f"--header 'uberctx-tenancy:uber/testing/api-explorer/1ddb-47f2-8e20-6e59ba0a9256' "
        f"--peer '127.0.0.1:5435' --timeout 30000ms"
    )
    
    print(command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if process.returncode == 0:
        print(f'Test methods {test_method} inserted to auto offboarding successfully!')
        print("Output:")
        print(output.decode('utf-8'))
    else:
        print(f"Command execution failed with error code {process.returncode}")
        print("Error:")
        print(error.decode('utf-8'))
        print("Test methods:", test_method)
    return process.returncode


def updateAutoOffboarding(test_method):
    """
    Updates test methods in auto offboarding.

    Parameters:
    - test_method (list): A list of test methods to update in auto offboarding.

    Returns:
    - int: The return code from the subprocess execution.
    """
    request_data = {
        "test_method": test_method
    }
    str_data = json.dumps(request_data)
    
    command = (
        f"yab -s mta-data-store --caller yab-akumar577 --grpc-max-response-size 20971520 "
        f"--request '{str_data}' --procedure 'uber.gss.gss_mta_test.mtadatastore.MtaDataStore/UpdateAutoOffboarding' "
        f"--header 'x-uber-uuid:2a2d59e8-9bbf-4c4e-97a5-4cbb85bec7fa' "
        f"--header 'studio-caller:akumar577' "
        f"--header 'x-uber-tenancy:uber/testing/api-explorer/a5d2-42fb-8829-508ab7e4012b' "
        f"--header 'x-uber-source:studio' "
        f"--header 'jaeger-debug-id:api-explorer-akumar577' "
        f"--header 'uberctx-tenancy:uber/testing/api-explorer/a5d2-42fb-8829-508ab7e4012b' "
        f"--peer '127.0.0.1:5435' --timeout 30000ms"
    )
    
    print(command)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if process.returncode == 0:
        print(f'Test methods {test_method} updated in auto offboarding successfully!')
        print("Output:")
        print(output.decode('utf-8'))
    else:
        print(f"Command execution failed with error code {process.returncode}")
        print("Error:")
        print(error.decode('utf-8'))
        print("Test methods:", test_method)
    return process.returncode


if __name__ == "__main__":
    triage_wats_run("1ed4c021-7351-4136-8115-175823a38ec8", "Test Run", "Timeout_Locator_Click", "MTA-76626", "suggestion-auto-triage")
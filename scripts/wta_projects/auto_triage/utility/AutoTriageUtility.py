from utility import TicketCreationUtility
from utility import CompareSimilarity
from utility import LocalDBQueries
from utility import UpdateMetesRun
from utility import JiraAuth
from utility import utils
import pandas as pd


from datetime import datetime, timedelta
import requests
import time
import os
import re


_exclude_methods = [
    'com.uber.e2e.android.eats.test.gmp.VerifyOOSViewEventTest/testVerifyOosViewEvent',
    'com.uber.e2e.android.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest',
    'com.uber.e2e.ios.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest',
    'com.uber.e2e.ios.eats.test.gmp.SubPurchaseSuccessTest/testSubPurchaseSuccess',
    'com.uber.e2e.android.carbon.test.userworkflow.DriverAcceptTripTest/testDriverAcceptTrip_dogfooding',
    'com.uber.e2e.android.helix.test.userworkflow.HomeScreenMoreTapTest/testHomeScreenMoreTapFlow_dogfooding',
    'com.uber.e2e.android.helix.test.userworkflow.USLSLSRRiderTest/verifySignInFeature_dogfooding',
    'com.uber.e2e.android.eats.test.gmp.VerifyOOSViewEventTest/testVerifyOosViewEvent_dogfooding',
    'com.uber.e2e.android.eats.test.gmp.SubPurchaseSuccessTest/testSubPurchaseSuccess_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.CheckoutFromCartTabTesttestCheckoutFromCartTab_dogfooding',
    'com.uber.e2e.android.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.WelcomeLoginTest/testWelcomeScreenOptions_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.StoreSuggestionTapTest/testStoreSuggestionTap_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.AddToCartToCheckoutTest/testAddToCartToCheckout_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.PlaceOrderTest/testPlaceOrder_dogfooding',
    'com.uber.e2e.android.eats.test.userworkflow.CheckoutClickPromotionTest/testCheckoutClickPromotionApplied_dogfooding',
    'com.uber.e2e.android.eats.test.eatercoreflows.PaymentOnboardingWalletTest/testPaymentOnboardingFromWallet_dogfooding',
    'com.uber.e2e.android.eats.test.identity.UnifiedSignupAndLoginWithChromeTest/testSignInWithOtpAndPasswordFeature_dogfooding',
    'com.uber.e2e.ios.eats.test.eatercoreflows.CheckoutFromCartTabTest/testCheckoutFromCartTab_dogfooding',
    'com.uber.e2e.ios.eats.test.eatercoreflows.PlaceOrderTest/testPickupStartFromStore_dogfooding',
    'com.uber.e2e.ios.eats.test.userworkflow.CheckoutClickPromotionTest/testCheckoutClickPromotionApplied_dogfooding',
    'com.uber.e2e.ios.eats.test.eatercoreflows.PaymentOnboardingWalletTest/testPaymentOnboardingFromWallet_dogfooding',
    'com.uber.e2e.ios.carbon.test.userworkflow.DriverAcceptTripTest/testDriverAcceptTrip_dogfooding',
    'com.uber.e2e.ios.helix.test.userworkflow.HomeScreenMoreTapTest/testHomeScreenMoreTapFlow_dogfooding',
    'com.uber.e2e.ios.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest_dogfooding',
    'com.uber.e2e.ios.eats.test.gmp.SubPurchaseSuccessTest/testSubPurchaseSuccess_dogfooding',
    'com.uber.e2e.ios.eats.test.gmp.SelfServeCancelConfirmRequestTest/testSelfServeCancelConfirmRequest_dogfooding',
]

def check_bundle_status(bundle, t_date):

    status = LocalDBQueries.check_bundle_exists(f"execution_status_{t_date}.db", bundle)

    start_time = datetime.now()
    end_time = start_time + timedelta(hours=20)

    while not status:
        current_time = datetime.now()
        if current_time >= end_time:
            print("Reached 9-hour limit. Exiting loop.")
            break
        try:
            print(f"Waiting for 2 minutes before checking again for {bundle} bundle")
            time.sleep(120)
            status = LocalDBQueries.check_bundle_exists(f"execution_status_{t_date}.db", bundle) 
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    return status

def check_bundle_status_for_ticket_creation(bundle, t_date, check_threshold=1):

    status = LocalDBQueries.is_bundle_status_greater_than_threshold(f"execution_status_{t_date}.db", bundle, check_threshold)

    start_time = datetime.now()
    end_time = start_time + timedelta(hours=20)

    while not status:
        current_time = datetime.now()
        if current_time >= end_time:
            print("Reached 9-hour limit. Exiting loop.")
            break
        try:
            print(f"Waiting for 2 minutes before checking again for {bundle} bundle")
            time.sleep(120)
            status = LocalDBQueries.is_bundle_status_greater_than_threshold(f"execution_status_{t_date}.db", bundle, check_threshold) 
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    return status


def iterate_matching_failure(untriaged_data, triaged_data, bundle, t_date):
    IMG_DIR = "testImg"

    ticket_status_cache = {}

    client = JiraAuth.initiate_jira_client()

    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)

    update_status = True
    if len(untriaged_data) <= 20 and update_status:
        LocalDBQueries.increment_status(f"execution_status_{t_date}.db", bundle)
        update_status = False

    for _currIdx, curr_failure in untriaged_data.iterrows():
        print(f"{_currIdx} / {len(untriaged_data)}") 
        if (len(untriaged_data) - _currIdx) <= 20 and update_status:
            LocalDBQueries.increment_status(f"execution_status_{t_date}.db", bundle)
            update_status = False

        if curr_failure['failure_category_l1'].lower() == 'infra' or curr_failure['test_method'] in _exclude_methods:
            continue

        screenshot1_path = utils.download_images_from_terrablob(curr_failure['screen_shots_link'], IMG_DIR, f"{curr_failure['run_uuid']}.png")

        curr_failure_prefix = curr_failure['failure_reason'][:25] if curr_failure['failure_reason'] else ""
        filtered_triaged_data = triaged_data[triaged_data['failure_reason'].str[:25] == curr_failure_prefix] if curr_failure_prefix else triaged_data

        for _prevIdx, similar_method in filtered_triaged_data.iterrows():

            print(curr_failure['run_uuid'])
            print(similar_method['run_uuid'])

            if "CAPINFRA" in similar_method['ticket_id']:
                continue

            similar_method['ticket_id'] = JiraAuth.latest_jira_key(client, similar_method['ticket_id'])

            if similar_method['ticket_id'] in ticket_status_cache:
                t_status = ticket_status_cache[similar_method['ticket_id']]
            else:
                t_status = JiraAuth.check_ticket_status(client, similar_method['ticket_id'])
                ticket_status_cache[similar_method['ticket_id']] = t_status

            if not t_status:
                continue

            failure_location1 = "failure_location1"
            failure_location2 = "failure_location2"
            try:
                method_line = re.search(r'com\.uber\.e2e\.\S.*$', similar_method['failure_reason'], re.MULTILINE).group(0)
                failure_location1 = method_line.split('(')[1].split(')')[0]
                method_line = re.search(r'com\.uber\.e2e\.\S.*$', curr_failure['failure_reason'], re.MULTILINE).group(0)
                failure_location2 = method_line.split('(')[1].split(')')[0]
            except Exception as e:
                print(f"An error occurred: {e}")

            if CompareSimilarity.compare_strings(utils.get_substring(similar_method['failure_reason'], '.java'), utils.get_substring(curr_failure['failure_reason'], '.java')) or failure_location1 == failure_location2:

                triaged_by = "suggestion-auto-triage"
                screenshot2_path = utils.download_images_from_terrablob(similar_method['screen_shots_link'], IMG_DIR, f"{similar_method['run_uuid']}.png")

                if screenshot1_path and screenshot2_path and CompareSimilarity.compare_images(screenshot1_path, screenshot2_path):
                    triaged_by = "auto-triage"

                print(f"{triaged_by} -> | {curr_failure['run_uuid']} : {curr_failure['test_method']} : {similar_method['ticket_id']} : {similar_method['run_uuid']} |")
                UpdateMetesRun.triage_mtp_run(curr_failure['run_uuid'], similar_method['failure_category_l1_triaged'], similar_method['failure_category_l2_triaged'], "", similar_method['ticket_id'], triaged_by)
                break



def slack_notify(bundle):
    webhook_url = "https://hooks.slack.com/triggers/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"
    payload = {
        "lob_name": bundle
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(webhook_url, json=payload, headers=headers)

def slack_web_notify(bundle):
    webhook_url = "https://hooks.slack.com/triggers/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"
    payload = {
        "lob_name": bundle
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(webhook_url, json=payload, headers=headers)

def slack_snap_notify(bundle):
    webhook_url = "https://hooks.slack.com/triggers/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"
    payload = {
        "lob_name": bundle
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(webhook_url, json=payload, headers=headers)


def iterate_matching_failure_with_ticket_creation(untriaged_data, triaged_data, bundle, t_date):
    IMG_DIR = "testImg"

    ticket_status_cache = {}

    client = JiraAuth.initiate_jira_client()

    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)

    notify = True
    if len(untriaged_data) <= 10 and notify:
        slack_notify(bundle)
        notify = False

    for _currIdx, curr_failure in untriaged_data.iterrows():
        
        flag_similar_found = False
        
        print(f"{_currIdx} / {len(untriaged_data)}") 
        if (len(untriaged_data) - _currIdx) <= 10 and notify:
            slack_notify(bundle)
            notify = False

        if curr_failure['failure_category_l1'].lower() == 'infra' or curr_failure['test_method'] in _exclude_methods:
            continue

        screenshot1_path = utils.download_images_from_terrablob(curr_failure['screen_shots_link'], IMG_DIR, f"{curr_failure['run_uuid']}.png")


        curr_failure_prefix = curr_failure['failure_reason'][:25] if curr_failure['failure_reason'] else ""
        filtered_triaged_data = triaged_data[triaged_data['failure_reason'].str[:25] == curr_failure_prefix] if curr_failure_prefix else triaged_data


        for _prevIdx, similar_method in filtered_triaged_data.iterrows():

            print(curr_failure['run_uuid'])
            print(similar_method['run_uuid'])

            if "CAPINFRA" in similar_method['ticket_id']:
                continue

            similar_method['ticket_id'] = JiraAuth.latest_jira_key(client, similar_method['ticket_id'])

            if similar_method['ticket_id'] in ticket_status_cache:
                t_status = ticket_status_cache[similar_method['ticket_id']]
            else:
                t_status = JiraAuth.check_ticket_status(client, similar_method['ticket_id'])
                ticket_status_cache[similar_method['ticket_id']] = t_status

            if not t_status:
                continue

            failure_location1 = "failure_location1"
            failure_location2 = "failure_location2"
            try:
                method_line = re.search(r'com\.uber\.e2e\.\S.*$', similar_method['failure_reason'], re.MULTILINE).group(0)
                failure_location1 = method_line.split('(')[1].split(')')[0]
                method_line = re.search(r'com\.uber\.e2e\.\S.*$', curr_failure['failure_reason'], re.MULTILINE).group(0)
                failure_location2 = method_line.split('(')[1].split(')')[0]
            except Exception as e:
                print(f"An error occurred: {e}")

            if CompareSimilarity.compare_strings(utils.get_substring(similar_method['failure_reason'], '.java'), utils.get_substring(curr_failure['failure_reason'], '.java')) or failure_location1 == failure_location2:

                triaged_by = "suggestion-auto-triage"
                screenshot2_path = utils.download_images_from_terrablob(similar_method['screen_shots_link'], IMG_DIR, f"{similar_method['run_uuid']}.png")

                if screenshot1_path and screenshot2_path and CompareSimilarity.compare_images(screenshot1_path, screenshot2_path):
                    triaged_by = "auto-triage"

                print(f"{triaged_by} -> | {curr_failure['run_uuid']} : {curr_failure['test_method']} : {similar_method['ticket_id']} : {similar_method['run_uuid']} |")
                UpdateMetesRun.triage_mtp_run(curr_failure['run_uuid'], similar_method['failure_category_l1_triaged'], similar_method['failure_category_l2_triaged'], "", similar_method['ticket_id'], triaged_by)
                flag_similar_found = True
                break
                
        total_new_ticket_created = client.search_issues(jql_str=f'status = Open AND resolution = Unresolved AND created >= -23h AND assignee in ("pedara@ext.uber.com") AND reporter in ("svc-sla-health-bot@uber.com") order by updated DESC',maxResults = 50, json_result=True)['issues']
        
        if not flag_similar_found and len(total_new_ticket_created) < 65:
            new_ticket = TicketCreationUtility.create_ticket(curr_failure)
            print(f"new ticket --> https://t3.uberinternal.com/browse/{new_ticket}")
            # UpdateMetesRun.triage_mtp_run(curr_failure['run_uuid'], "TC", "PB_OTHERS", "", new_ticket, "auto-triage")
            curr_failure['ticket_id'] = new_ticket
            curr_failure['failure_category_l2_triaged'] = "PB_OTHERS"
            curr_failure_row_df = pd.DataFrame([curr_failure])
            triaged_data = pd.concat([curr_failure_row_df, triaged_data], ignore_index=True)

def iterate_matching_failure_with_ticket_creationwithassignee(untriaged_data, triaged_data, bundle, t_date,assignee_email):
    IMG_DIR = "testImg"

    ticket_status_cache = {}

    client = JiraAuth.initiate_jira_client()

    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)

    notify = True
    if len(untriaged_data) <= 10 and notify:
        slack_notify(bundle)
        notify = False

    for _currIdx, curr_failure in untriaged_data.iterrows():
        
        flag_similar_found = False
        
        print(f"{_currIdx} / {len(untriaged_data)}") 
        if (len(untriaged_data) - _currIdx) <= 10 and notify:
            slack_notify(bundle)
            notify = False

        if curr_failure['failure_category_l1'].lower() == 'infra' or curr_failure['test_method'] in _exclude_methods:
            continue

        screenshot1_path = utils.download_images_from_terrablob(curr_failure['screen_shots_link'], IMG_DIR, f"{curr_failure['run_uuid']}.png")

        for _prevIdx, similar_method in triaged_data.iterrows():

            print(curr_failure['run_uuid'])
            print(similar_method['run_uuid'])

            if "CAPINFRA" in similar_method['ticket_id']:
                continue

            similar_method['ticket_id'] = JiraAuth.latest_jira_key(client, similar_method['ticket_id'])

            if similar_method['ticket_id'] in ticket_status_cache:
                t_status = ticket_status_cache[similar_method['ticket_id']]
            else:
                t_status = JiraAuth.check_ticket_status(client, similar_method['ticket_id'])
                ticket_status_cache[similar_method['ticket_id']] = t_status

            if not t_status:
                continue

            failure_location1 = "failure_location1"
            failure_location2 = "failure_location2"
            try:
                method_line = re.search(r'com\.uber\.e2e\.\S.*$', similar_method['failure_reason'], re.MULTILINE).group(0)
                failure_location1 = method_line.split('(')[1].split(')')[0]
                method_line = re.search(r'com\.uber\.e2e\.\S.*$', curr_failure['failure_reason'], re.MULTILINE).group(0)
                failure_location2 = method_line.split('(')[1].split(')')[0]
            except Exception as e:
                print(f"An error occurred: {e}")

            if CompareSimilarity.compare_strings(utils.get_substring(similar_method['failure_reason'], '.java'), utils.get_substring(curr_failure['failure_reason'], '.java')) or failure_location1 == failure_location2:

                triaged_by = "suggestion-auto-triage"
                screenshot2_path = utils.download_images_from_terrablob(similar_method['screen_shots_link'], IMG_DIR, f"{similar_method['run_uuid']}.png")

                if screenshot1_path and screenshot2_path and CompareSimilarity.compare_images(screenshot1_path, screenshot2_path):
                    triaged_by = "auto-triage"

                print(f"{triaged_by} -> | {curr_failure['run_uuid']} : {curr_failure['test_method']} : {similar_method['ticket_id']} : {similar_method['run_uuid']} |")
                UpdateMetesRun.triage_mtp_run(curr_failure['run_uuid'], similar_method['failure_category_l1_triaged'], similar_method['failure_category_l2_triaged'], "", similar_method['ticket_id'], triaged_by)
                flag_similar_found = True
                break
                
        total_new_ticket_created = client.search_issues(jql_str=f'status = Open AND resolution = Unresolved AND created >= -23h AND assignee in ("{assignee_email}") AND reporter in ("svc-sla-health-bot@uber.com") order by updated DESC',maxResults = 50, json_result=True)['issues']
        
        if not flag_similar_found and len(total_new_ticket_created) < 65:
            new_ticket = TicketCreationUtility.create_ticket(curr_failure)
            print(f"new ticket --> https://t3.uberinternal.com/browse/{new_ticket}")
            # UpdateMetesRun.triage_mtp_run(curr_failure['run_uuid'], "TC", "PB_OTHERS", "", new_ticket, "auto-triage")
            curr_failure['ticket_id'] = new_ticket
            curr_failure['failure_category_l2_triaged'] = "PB_OTHERS"
            curr_failure_row_df = pd.DataFrame([curr_failure])
            triaged_data = pd.concat([curr_failure_row_df, triaged_data], ignore_index=True)


            
            
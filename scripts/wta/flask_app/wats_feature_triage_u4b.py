from utility import AutoTriageUtility
from utility import DBQueryExecutor
from utility import JiraAuth
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

import json
import subprocess




def get_triaged_data_from_wats():
    query = f'''
    SELECT
      *
    FROM
      test_results
    WHERE
      pipeline IN ('e2e-release', 'e2e-nightly')
      AND result = 'failed'
      AND is_final=1
      AND video_link =''
      AND jira_ticket IS NOT NULL
      AND jira_ticket <> ''
      AND created_at >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)
      AND triaged_by != 'suggestion-auto-triage'
      AND failure_reason not like "%Data too large%" 
    '''
    return DBQueryExecutor.execute_query(query, consumer=True, db='wats')




def get_untriaged_data_from_wats(feature_name):
    query = f'''
    SELECT
      *
    FROM
      test_results
    WHERE
      pipeline IN ('e2e-release', 'e2e-nightly')
      AND result = 'failed'
      AND video_link =''
      AND is_final=1
      AND (
        jira_ticket IS NULL
        OR jira_ticket = ''
      )
      AND created_at >= CURRENT_DATE
      AND feature_name = '{feature_name}'
      AND created_at < DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY)
      AND failure_reason not like "%Data too large%"
      order by execution_uuid desc
    '''
    return DBQueryExecutor.execute_query(query, consumer=True, db='wats')



def download_images_from_wats_terrablob(url, local_dir_path, filename, max_retries=3):
    """
    Downloads an image from a given URL and saves it to a specified local directory.

    Args:
        url: URL of the image to be downloaded.
        local_dir_path: Local directory path to save the downloaded image.
        filename: Name of the file to save the image as.
    """
    if not os.path.exists(local_dir_path):
        os.makedirs(local_dir_path)
    
    # source_path = get_substring(url, '-', False).replace("last_snapshot.png", "")
    source_path = url
    output = subprocess.run(f'tb-cli --usso-token=$(utoken create) ls {source_path} | grep "retry-1_screenshot"', shell=True, capture_output=True, text=True)
    img_name = output.stdout.strip()
    target_path = os.path.join(local_dir_path, filename)

    # remove_path(target_path)

    retries = 0
    while retries < max_retries:
        if not os.path.exists(target_path) or not utils.is_image_valid(target_path):
            try:
                subprocess.run(f"tb-cli --usso-token=$(utoken create) get {source_path}{img_name} {target_path} -t 2m", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error occurred while downloading the image: {e}")
                retries += 1
                continue

            if utils.is_image_valid(target_path):
                return target_path
            else:
                print(f"Downloaded image is corrupted. Retrying {retries + 1}/{max_retries}...")
                utils.remove_path(target_path)
                retries += 1
        else:
            return target_path

    if retries == max_retries:
        print("Max retries reached. The image could not be downloaded or is still corrupted.")
        return False



def get_email_and_label(feature_name):
    label = {
        'londongrat': 'GSS_London_GRAT',
        'driver': 'GSS_Product_Driver',
        'freight': 'GSS_Product_Freight',
        'u4b': 'GSS_U4B_Testing',
        'tooling': 'GSS_Rosetta',
        'rider': 'GSS_Product_Rider',
        'customerobsession': 'GSS_Product-Customer_Obsession'
    }

    email = {
        'u4b': 'sbalak5@ext.uber.com',
        'customerobsession': 'syeram@ext.uber.com',
        'tooling': 'skanda6@ext.uber.com',
        'rider': 'syeram@ext.uber.com',
        'londongrat': 'maakif@ext.uber.com',
        'freight': 'grajar1@ext.uber.com',
        'driver': 'msekar@ext.uber.com'
    }

    if feature_name in email and feature_name in label:
        return {
            'email': email[feature_name],
            'label': label[feature_name]
        }
    else:
        return {
            'email': "sbandi11@ext.uber.com",
            'label': label['customerobsession']
        }  


def get_pipeline_triage(pipeline):
    pipeline_to_triage = {
        'e2e-nightly': '#E2ENightlyTriage',
        'e2e-release': '#E2EReleaseTriage'
    }
    return pipeline_to_triage.get(pipeline, "#E2ENightlyTriage")


def create_wats_ticket(curr_failure, client):
    feature_assignne_label = get_email_and_label(curr_failure['feature_name'])
    labels = ['#E2EAutomation', '#E2EPotentialPB','#E2EUntriaged', get_pipeline_triage(curr_failure['pipeline']), '#E2EWeb', feature_assignne_label['label']]
    failure_reason_text = curr_failure['failure_reason'][:100] if curr_failure['failure_reason'] else "No failure reason available"
    summary = f"[E2E][Web][{curr_failure['feature_name']}][{curr_failure['test_suite_name']}] - {' '.join(failure_reason_text.splitlines())}"
    desc = f'''
    *Description:* {summary}
    
    Environment: {get_pipeline_triage(curr_failure['pipeline'])}
    
    Steps to reproduce:
    
    Expected Result:
    
    Actual Result: 
    
    Impacted TC's:
    
    Test Suite : {curr_failure['test_suite_name']}
    
    T3 Links:
    
    Tested Environment Details:
    
    Observed manually or Automation Only:
    
    Occurrence:
    
    Observed manually with Static credentials: Yes/No
    
    Static Account Details:
    
    Buildkite Job Link:
    {curr_failure['build_link']}

    ReportLink: {curr_failure['html_report_path']}
    
    Video Recording: {curr_failure['video_link']}
    '''
    new_ticket = JiraAuth.create_jira_issue(client, project='MTA', summary=summary, description=desc, issuetype="Bug",
                               assignee_email=feature_assignne_label['email'], labels=labels, components="Web",
                               priority='P1').key
    return new_ticket




def iterate_matching_failure_for_wats(untriaged_data, triaged_data, feature_name):
    IMG_DIR = "testImg"

    ticket_status_cache = {}

    client = JiraAuth.initiate_jira_client()

    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)

    notify = True
    if len(untriaged_data) <= 3 and notify:
        AutoTriageUtility.slack_web_notify(feature_name)
        notify = False

    for _currIdx, curr_failure in untriaged_data.iterrows():
        print(f"{_currIdx} / {len(untriaged_data)}")
        flag_similar_found = False

        if (len(untriaged_data) - _currIdx) <= 3 and notify:
            AutoTriageUtility.slack_web_notify(feature_name)
            notify = False

        curr_image_url = f"/prod/wats/executions/{curr_failure['pipeline']}/{curr_failure['build_number']}/{curr_failure['execution_uuid']}/data/retry-tracking/"
        curr_screenshot_path = download_images_from_wats_terrablob(curr_image_url, IMG_DIR, f"{curr_failure['run_uuid']}.png")

        curr_failure_prefix = curr_failure['failure_reason'][:25] if curr_failure['failure_reason'] else ""
        filtered_triaged_data = triaged_data[triaged_data['failure_reason'].str[:25] == curr_failure_prefix] if curr_failure_prefix else triaged_data


        for _prevIdx, similar_method in filtered_triaged_data.iterrows():

            print(curr_failure['run_uuid'])
            print(similar_method['run_uuid'])

            similar_method['jira_ticket'] = JiraAuth.latest_jira_key(client, similar_method['jira_ticket'])

            if similar_method['jira_ticket'] in ticket_status_cache:
                t_status = ticket_status_cache[similar_method['jira_ticket']]
            else:
                t_status = JiraAuth.check_ticket_status(client, similar_method['jira_ticket'])
                ticket_status_cache[similar_method['jira_ticket']] = t_status

            if not t_status:
                continue


            if curr_failure['failure_reason'] and similar_method['failure_reason'] and CompareSimilarity.compare_strings(similar_method['failure_reason'][:300], curr_failure['failure_reason'][:300], 96):


                triaged_by = "suggestion-auto-triage"
                prev_image_url = f"/prod/wats/executions/{similar_method['pipeline']}/{similar_method['build_number']}/{similar_method['execution_uuid']}/data/retry-tracking/"

                prev_screenshot_path = download_images_from_wats_terrablob(prev_image_url, IMG_DIR, f"{similar_method['run_uuid']}.png")

                if curr_screenshot_path and prev_screenshot_path and CompareSimilarity.compare_images(curr_screenshot_path, prev_screenshot_path):
                    triaged_by = "auto-triage"
                    
                UpdateMetesRun.triage_wats_run(curr_failure['run_uuid'],similar_method['triage_category_l1'], similar_method['triage_category_l2'], similar_method['jira_ticket'], triaged_by)
                print(f"{triaged_by} -> | {curr_failure['run_uuid']} : {curr_failure['test_suite_name']} : {similar_method['jira_ticket']} : {similar_method['run_uuid']} |")
                flag_similar_found = True
                break

        feature_assignne_label = get_email_and_label(feature_name)
        total_new_ticket_created = client.search_issues(jql_str=f'status = Open AND resolution = Unresolved AND created >= -23h AND assignee in ("{feature_assignne_label["email"]}") AND labels in ("{feature_assignne_label["label"]}")  AND reporter in ("svc-sla-health-bot@uber.com") order by updated DESC',maxResults = 50, json_result=True)['issues']
        
        if not flag_similar_found and len(total_new_ticket_created) < 15:
            new_ticket = create_wats_ticket(curr_failure, client)
            print(f"new ticket --> https://t3.uberinternal.com/browse/{new_ticket}")
            UpdateMetesRun.triage_wats_run(curr_failure['run_uuid'], "Unknown", "Undetermined", new_ticket, "auto-triage")
            curr_failure['jira_ticket'] = new_ticket
            curr_failure['triage_category_l1'] = "Unknown"
            curr_failure['triage_category_l2'] = "Undetermined"
            curr_failure_row_df = pd.DataFrame([curr_failure])
            triaged_data = pd.concat([curr_failure_row_df, triaged_data], ignore_index=True)



feature_name = "u4b"

# customerobsession, u4b, londongrat, rider, freight, driver, tooling

triaged_data = get_triaged_data_from_wats()
if len(triaged_data) < 2:
    triaged_data = get_triaged_data_from_wats()
untriaged_data = get_untriaged_data_from_wats(feature_name)
print(f"Total untriaged data: {len(untriaged_data)}")
iterate_matching_failure_for_wats(untriaged_data, triaged_data, feature_name)

today_triaged_data = DBQueryExecutor.get_today_triaged_data_from_wats()
print(len(today_triaged_data))
today_skipped_data = DBQueryExecutor.get_untriaged_skipped_data_from_wats()
print(len(today_skipped_data))
for _idx, data in today_skipped_data.iterrows():
    filter_triaged_data = today_triaged_data.loc[today_triaged_data['execution_uuid'] == data['execution_uuid']]
    if len(filter_triaged_data) != 0:
        UpdateMetesRun.triage_wats_run(
            run_uuid=data['run_uuid'],
            triage_category_l1=filter_triaged_data.iloc[0]['triage_category_l1'],
            triage_category_l2=filter_triaged_data.iloc[0]['triage_category_l2'],
            jira_ticket=filter_triaged_data.iloc[0]['jira_ticket'],
            triaged_by=filter_triaged_data.iloc[0]['triaged_by']
        )
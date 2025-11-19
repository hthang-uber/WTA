from utility import DBQueryExecutor
from utility import JiraAuth
from utility import utils
import pandas as pd
import pytz

from datetime import datetime, timedelta, date
#hi

def add_comment(failures_query_result):
    """
    Add comments to JIRA tickets based on test failure data for WebAT
    
    Args:
        failures_query_result (DataFrame): DataFrame containing test failure information
    """
    
    unique_test_ids = failures_query_result['jira_ticket'].unique()
    client = JiraAuth.initiate_jira_client()
    
    for test_id in unique_test_ids:
        print(f"Processing ticket: {test_id}")
        
        
        if JiraAuth.check_ticket_created_today(client, test_id):
            # If ticket was created today, just append failure links to description
            filtered_df = failures_query_result.loc[failures_query_result['jira_ticket'] == test_id]
            failure_links = ""
            
            for idx, method in filtered_df.iterrows():
                if pd.notna(method['build_link']):
                    failure_links += f"\nBuildKite link: {method['build_link']}"
                if pd.notna(method['html_report_path']):
                    failure_links += f"\nHTML report Link: {method['html_report_path']}"

            JiraAuth.append_description(client, test_id, f'''\n\r Other Impacted Tests: {failure_links}\r\n''')
            
        else:
            # Filter data for this specific ticket
            filtered_df = failures_query_result.loc[failures_query_result['jira_ticket'] == test_id]
            
            # Extract test information
            environment = utils.list_to_string(filtered_df['environment'].unique(), ", ", "")
            pipeline = utils.list_to_string(filtered_df['pipeline'].unique(), ", ", "")
            
            # Get first row for HTML report and interactive UUID
            first_row = filtered_df.iloc[0]
            html_report_path = first_row['html_report_path'] if pd.notna(first_row['html_report_path']) else ""
            # Add interactive- prefix to run_uuid for Interactive UUID
            interactive_uuid = f"interactive-{first_row['run_uuid']}" if pd.notna(first_row['run_uuid']) else ""
            
            # Get all BuildKite links
            build_links = []
            for idx, method in filtered_df.iterrows():
                if pd.notna(method['build_link']):
                    build_links.append(method['build_link'])
            

            buildkite_links_str = ""
            for i, link in enumerate(build_links):
                if i == 0:
                    buildkite_links_str = link
                else:
                    buildkite_links_str += f"\n{link}"
            
            ist_time_obj = filtered_df['created_at'].iloc[0].replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Kolkata'))
            date_str = ist_time_obj.strftime("%B %d")
            time_str = ist_time_obj.strftime("%I:%M %p")
            
            if date_str[-2:] in ['11', '12', '13']:
                date_str += 'th'
            elif date_str[-1] == '1':
                date_str += 'st'
            elif date_str[-1] == '2':
                date_str += 'nd'
            elif date_str[-1] == '3':
                date_str += 'rd'
            else:
                date_str += 'th'

            comment = f'''Found issue again on {date_str} at {time_str} in {environment}, {pipeline} build execution,
BuildKite link: {buildkite_links_str}
HTML report Link: {html_report_path}
Interactive UUID: {interactive_uuid}'''

            try:
                print(test_id, comment)
                client.add_comment(test_id, comment)
                print(f"Comment added to {test_id}")
            except Exception as e:
                print(f"Failed to add comment to {test_id}: {str(e)}")


def add_comment_for(exe_date, triage_by):
    """
    Add comments for failures on a specific execution date
    
    Args:
        exe_date (str): Execution date in YYYY-MM-DD format
        triage_by (str): Triaged by filter
    """
    query = f'''
    SELECT
      run_uuid,
      execution_uuid,
      feature_name,
      test_suite_name,
      test_case,
      pipeline,
      result,
      failure_reason,
      created_at,
      ended_at,
      test_path,
      html_report_path,
      video_link,
      log_link,
      browser,
      browser_version,
      environment,
      browser_mode,
      user_agent,
      build_link,
      build_number,
      manual_test_id,
      screenshot_path,
      device_type,
      device_model,
      device_os,
      is_final,
      failure_category_l1,
      failure_category_l2,
      jira_ticket,
      triage_category_l1,
      triage_category_l2,
      triaged_by,
      triggered_by,
      owner
    FROM
      test_results
    WHERE
      pipeline IN ('e2e-release', 'e2e-nightly')
      AND result = 'failed'
      AND is_final = 1
      AND COALESCE(jira_ticket, '') != ''
      AND triaged_by = "auto-triage"
      AND created_at >= DATE('{exe_date}')
      AND created_at < DATE_ADD(DATE('{exe_date}'), INTERVAL 1 DAY)
      AND triaged_by = "{triage_by}"
      AND failure_reason not like "%Data too large%"
    ORDER BY
      execution_uuid
    '''
    
    failures_query_result = DBQueryExecutor.execute_query(query, consumer=True, db='wats')
    
    if not failures_query_result.empty:
        add_comment(failures_query_result)
    else:
        print(f"No failed tests found for date: {exe_date}, triaged by: {triage_by}")




if __name__ == "__main__":
    today = date.today()
    formatted_date = today.strftime("%Y-%m-%d")
    
    print(f"Adding comments for failures on {formatted_date}")
    add_comment_for(formatted_date, 'auto-triage')
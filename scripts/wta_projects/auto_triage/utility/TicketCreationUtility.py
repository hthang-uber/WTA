from utility import utils
from utility import JiraAuth
from utility import SvcSlaHealthBotAuth
from utility import UpdateMetesRun
from utility.GSheets import GSheets
from utility import DBQueryExecutor

import requests
import re
import json
import subprocess
    
def create_ticket(run_details, trigger_consecutive_builds=0, trigger_same_builds=0, assignee_email=None):
    """
    """
    
    client = JiraAuth.initiate_jira_client()
    
    # Extract details from run_details
    lob, label = process_lob(run_details)
    sub_title = get_jira_title(run_details['failure_reason'])

    labels = get_labels(run_details)
    components = get_component(run_details)
    desc = get_jira_description(run_details)
    summary = build_jira_title(run_details['app_name'], run_details['platform'], lob, sub_title)
    priority = 'P1'
    application_id = get_application_id(run_details['app_name'])
    platform_id = get_platform_id(run_details['platform'])
    if not assignee_email:
        assignee_email = utils.load_constant_yaml()['user']
    ticket_id = JiraAuth.create_jira_issue(client, project='MTA', summary=summary, description=desc, issuetype="Bug",
                                           assignee_email=assignee_email, labels=labels, components=components,
                                           priority=priority, buildVersion=run_details['build_version'], platform=platform_id,
                                           application=application_id).key
    UpdateMetesRun.triage_mtp_run(run_details['run_uuid'], "TC", "PB_OTHERS", "", ticket_id, "auto-triage")

    try:
        wisdom_issue_id = run_details['wisdom_issue_id']
        if wisdom_issue_id and len(wisdom_issue_id) > 2:
            client.issue(ticket_id).update(customfield_11700={'id': '11401'})
    except Exception as e:
        print(f"Error updating ticket {ticket_id} with wisdom issue id: {str(e)}")
    

    if run_details['screen_shots_link']:
        path = f"new_ticket/{utils.get_substring(run_details['run_uuid'], '-', True)}"
        utils.download_images_from_terrablob(run_details['screen_shots_link'], path, "snapshot.png")
        full_path = f'{path}/snapshot.png'
        try:
            with open(full_path, 'rb') as img:
                client.add_attachment(issue=ticket_id, attachment=img)
            desc_index = desc.find("*Build Information") - 2
            client.issue(ticket_id).update(description=utils.insert_substring(desc, f'\n\r\n!snapshot.png|width=200,height=400!\r\n', desc_index, desc_index))
        except Exception as e:
            print(f"Failed to attach image to ticket {ticket_id}: {str(e)}")
        utils.remove_path(path)

    trigger_consecutive_build(client, run_details, ticket_id, trigger_consecutive_builds)
    trigger_same_build(client, run_details, ticket_id, trigger_same_builds)
        
    return ticket_id


def trigger_consecutive_build(client, run_details, ticket_id, trigger_consecutive_builds=0):
    if(trigger_consecutive_builds>0):
        assignee_email = utils.load_constant_yaml()['user']
        consecutive_builds_df = DBQueryExecutor.get_consecutive_CD_builds(run_details['platform'], run_details['app_name'], run_details["build_version"], trigger_consecutive_builds)
        JiraAuth.append_description(client,ticket_id,f"\n * {trigger_consecutive_builds} consecutive builds execution: ")
        for _idxx, build in consecutive_builds_df.iterrows():
            final_config = {
                "execution_details": {
                    "tests": run_details['test_method'],
                    "app_name": run_details['app_name'].lower(),
                    "platform": run_details['platform'].lower(),
                    "build_type": "",
                    "build_uuid": build["build_uuid"], 
                    "os_version": "18;17" if run_details['platform'].lower() == "ios" else "14;15",
                    "triggered_by": assignee_email,
                    "node_type": run_details['node_type'],
                    "group_id": "",
                    "test_bundle_id": run_details['test_bundle_id'],
                    "git_ref": "",
                    "appium_git_ref": "",
                    "appium_diff_id": ""
                }
            }
        
            str_data = json.dumps(final_config)
            command = f'''yab -s metesv2 --caller studio-web --grpc-max-response-size 20971520 --request '{str_data}' --procedure 'uber.devexp.mobile_testing.metesv2.Metesv2API/SubmitExecution' --header 'x-uber-source:studio' --header 'x-uber-uuid:108a7458-0aca-411d-a535-438d795958a5' --header 'studio-caller:hdafta' --header 'jaeger-debug-id:api-explorer-hdafta' --header 'uberctx-tenancy:uber/testing/api-explorer/05f1-4c95-a71f-6e7bdf2dc547' --peer '127.0.0.1:5435' --timeout 30000ms'''
            
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            
            if process.returncode == 0:
                print(output.decode('utf-8'))
                executionUUID = f'''https://mtpv2.uberinternal.com/executions/instance/{json.loads(output.decode('utf-8'))['body']['uuid']}'''
                JiraAuth.append_description(client,ticket_id,executionUUID)
                
                issue = client.issue(ticket_id)
                label = issue.fields.labels+['#E2EPotentialPBUntriage']
                dict_1 = {
                    "labels": label,
                }
                issue.update(fields=dict_1)
            else:
                print(f"Command execution failed with error code {process.returncode}")
                print("Error:")
                print(error.decode('utf-8'))


def trigger_same_build(client, run_details, ticket_id, trigger_same_builds=0):
    if(trigger_same_builds>0):
        assignee_email = utils.load_constant_yaml()['user']
        JiraAuth.append_description(client,ticket_id,f"\n * {trigger_same_builds} same builds execution: ")
        for _ in range(trigger_same_builds):
            final_config = {
                "execution_details": {
                    "tests": run_details['test_method'],
                    "custom_execution_name": run_details["custom_name"],
                    "app_name": run_details['app_name'].lower(),
                    "platform": run_details['platform'].lower(),
                    "build_uuid": run_details["build_uuid"],
                    "build_type": "",
                    "os_version": "18;17" if run_details['platform'].lower() == "ios" else "14;15",
                    "triggered_by": assignee_email,
                    "node_type": run_details['node_type'],
                    "group_id": "",
                    "test_bundle_id": run_details['test_bundle_id'],
                    "git_ref": "",
                    "appium_git_ref": "",
                    "appium_diff_id": ""
                }
            }
        
            str_data = json.dumps(final_config)
            command = f'''yab -s metesv2 --caller studio-web --grpc-max-response-size 20971520 --request '{str_data}' --procedure 'uber.devexp.mobile_testing.metesv2.Metesv2API/SubmitExecution' --header 'x-uber-source:studio' --header 'x-uber-uuid:108a7458-0aca-411d-a535-438d795958a5' --header 'studio-caller:hdafta' --header 'jaeger-debug-id:api-explorer-hdafta' --header 'uberctx-tenancy:uber/testing/api-explorer/05f1-4c95-a71f-6e7bdf2dc547' --peer '127.0.0.1:5435' --timeout 30000ms'''
            
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            
            if process.returncode == 0:
                print(output.decode('utf-8'))
                executionUUID = f'''https://mtpv2.uberinternal.com/executions/instance/{json.loads(output.decode('utf-8'))['body']['uuid']}'''
                JiraAuth.append_description(client,ticket_id,executionUUID)
                
            else:
                print(f"Command execution failed with error code {process.returncode}")
                print("Error:")
                print(error.decode('utf-8'))

        


def get_jira_description(run_details):
    """
    The function `get_jira_description` generates a formatted JIRA description based on provided run
    details and additional information.
    """
    # Extract details from run_details
    run_uuid = run_details['run_uuid']
    test_method = run_details['test_method']
    os_version = run_details['os_version']
    video_path = run_details['video_link']
    screenshot_path = run_details.get('screen_shots_link', "")
    platform = run_details['platform']
    app_name = run_details['app_name']
    studio_uuid = run_details['studio_uuid']
    build_type = run_details['build_type']
    build_version = run_details['build_version']
    node_type = run_details['node_type']
    wisdom_issue_id = run_details['wisdom_issue_id']
    lob, labels = process_lob(run_details)
    sub_title = get_jira_title(run_details['failure_reason'])
    title = build_jira_title(app_name, platform, lob, sub_title)
    
    # Fetching additional information
    rep_steps = get_reproduction_steps(run_uuid)
    feature_name, test_sheet = GSheets().get_test_feature_details(test_method)
    account_info = get_account_info(studio_uuid)
    metes_link = f"https://mtpv2.uberinternal.com/test-run/{run_uuid}"

    wisdom_issue_link = ""

    try:
        if wisdom_issue_id and len(wisdom_issue_id) > 2:
            wisdom_issue_link = f"https://wisdom.uberinternal.com/issue/metes/{wisdom_issue_id}/report/{run_uuid}/device"
    except Exception as e:
        print(f"Error creating wisdom issue link: {str(e)}")
        wisdom_issue_link = ""

    
    # Return the formatted JIRA description
    return f'''
        *One Line description about the failure:* {title}
        
        *Reproduction Steps:*
        {rep_steps}
        
        {build_test_suite_link(feature_name, test_sheet)}
        
        *Expected Result: (with screenshots)* —
        
        *Actual Result: (with screenshots)*—
        
        {build_build_info(video_path, screenshot_path)}
        
        *Number of TCs Impacted:*
        
        *OS Version:* - {os_version}
        
        {build_platform_impact(platform)}
        
        ----
        *Occurrence:* One Time/Intermittent/Always - OneTime
        
        *Observed manually with Dynamic credentials:* Yes/No
        
        *Observed manually with Static credentials:* Yes/No
        
        *Manually Observed:* Check link here
        ----
        {build_static_account_info()}
        
        {build_dynamic_account_info(studio_uuid, account_info)}
        
        ----
        *LOB:* {lob}
        
        *App:* {app_name}
        
        *Platform:* {platform}
        
        {build_device_info(build_type, build_version, node_type, os_version)}
        
        *Pipeline:* - nightly
        
        *MTP Links:* - {metes_link}
        
        *Wisdom Issue Link:* - {wisdom_issue_link}
        
        *Impacted TCs:*
        
        *Failure Video:* - {video_path}
        
        *Time stamp:*
        ----
        *Note:* In order to reduce noise (invalid bugs) sent to engg., this intermittent / one time automation-only failure is under further observation for 2 release builds.
    '''
    
    

# description utility

def get_labels(run_details):
    build_label = []
    if len(run_details['build_version']) <= 10:
        build_label = ["#E2ENightlyTriage"]
    else:
        build_label = ["#E2EReleaseTriage"]
        
    e2e_po_pb_labels = utils.load_constant_yaml()['e2e_po_pb_labels']
    application_label = utils.load_mapping_data()['application_details'][run_details['app_name']]['application_label']
    platform_label = utils.load_mapping_data()['platform_details'][run_details['platform']]['platform_label']
    _, lob_label = process_lob(run_details)
    return e2e_po_pb_labels + application_label + platform_label + lob_label + build_label 
    
def process_lob(run_details):
    """
    The function `process_lob` extracts labels based on a test method and returns the corresponding line
    of business (LOB) and labels.
    """
    labels = []
    lob = ""
    for _lob, lob_labels in utils.load_mapping_data()['lob_label'].items():
        if _lob in run_details['test_method']:
            lob = _lob.capitalize()
            labels.extend(lob_labels)
            break
    else:
        lob = 'unknown'
    
    return lob, labels

def get_jira_title(failure_reason):
    """
    This Python function extracts information from a failure reason string related to a JIRA issue and
    formats it into a descriptive message.
    """
    method_line = ""
    try:
        method_line = re.search(r'com\.uber\.e2e\.(ios|android)\.\S.*$', failure_reason, re.MULTILINE).group(0)
    
        method_name,  file_name = method_line.split('(')
        line_num = file_name.split(':')[1]
        file_name = file_name.split(':')[0]
        method_name=method_name.split('.')[-1]
    except:
        method_line = failure_reason[0:200]
        file_name = line_num = method_name = "-"
    return f'Failure observered in {file_name} for the method {method_name} at line no {line_num[:-1]}'
    


def get_reproduction_steps(run_uuid):
    """
    The function `get_reproduction_steps` retrieves test case steps for successful assertions in a test
    run using data from a database and external API calls.
    """
    try:
        assertions = DBQueryExecutor.get_test_scene_id_list(run_uuid)
        
        scene_id_list = utils.list_to_string(assertions['scene_id'], "','", "'")
        
        base_url = utils.load_constant_yaml()['jira']['base_url']
        
        url = (
            f"{base_url}/rest/tests/1.0/testcase/search?fields=id,key,projectId,name,"
            f"testScript,folderId&query=testCase.key+IN+({scene_id_list})+ORDER+BY+"
            f"testCase.name+ASC&json_result=true&startAt=0&maxResults=40&archived=false"
        )
        
        access_token = SvcSlaHealthBotAuth.get_bot_access_token()

        headers = {
            'authority': 't3.uberinternal.com',
            'accept': '*/*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/json',
            'origin': base_url,
            'x-requested-with': 'XMLHttpRequest',
            'cookie': f'auth-openid={access_token}'
        }

        response = requests.get(url, headers=headers)
        test_scene_results = response.json().get('results', [])

        success_assertion = assertions.loc[assertions['result'] == "SUCCESS"]['scene_id'].tolist()

        dict_reproduction_steps = {}
        
        for test_scene in test_scene_results:
            if test_scene['key'] in success_assertion:
                step_description = ""
                
                for step in test_scene['testScript']['steps']:
                    clean_step = remove_numbered_lists(remove_tags(step['description']))
                    step_description += f"{clean_step}\n"
                
                dict_reproduction_steps[test_scene['key']] = step_description

        assertion_str = "".join(dict_reproduction_steps[assertion] for assertion in success_assertion)
        
        return add_numbered_prefix(assertion_str)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return ""

def get_account_info(studio_uuid):
    """
    The function `get_account_info` retrieves account information for actors associated with a given
    studio UUID, including mobile, password, email, and related links.
    """
    try:
        actors = utils.get_interactiveUUID_data(studio_uuid)["body"]["result"]["populatedScenario"]["actors"]
        if not actors:
            raise ValueError("No actors found in the provided data.")
        
        account_info = ""
        userUUIDs = [actor['accountUUID'] for actor in actors]
        
        for actor in actors:
            account_info += f'''
            \n * *{actor['type']}* 
             ** Mobile: {actor['accountMobile']} 
             ** Password: {actor['accountPassword']} 
             ** Email: {actor['accountEmail']} 
             ** accountUUID: {actor['accountUUID']}'''
        
        account_info += f'''\r\n\n * *Tenancy:* {actors[0]['tenancy']}'''
        
        if userUUIDs:
            userUUIDs_str = utils.list_to_string(userUUIDs, "' ,'", "'")
            healthline_crash_uuids = DBQueryExecutor.get_healthline_crash_uuids(userUUIDs_str)
            
            if not healthline_crash_uuids.empty and healthline_crash_uuids and 'crash_uuid' in healthline_crash_uuids:
                account_info += f'''
                \n * *Healthline Crash Log:* https://healthline.uberinternal.com/m/crash/{healthline_crash_uuids['crash_uuid'][0]}'''
                
                if healthline_crash_uuids.get('classification_value', [None])[0]:
                    account_info += f'''
                    \n * *Healthline Issue Link:* https://healthline.uberinternal.com/m/{healthline_crash_uuids['context_platform'][0]}/{healthline_crash_uuids['context_product'][0]}/issue/{healthline_crash_uuids['classification_value'][0]}/overview'''
        
        return account_info
    
    except Exception as e:
        print(f"No account info found for Interactive UUID: {studio_uuid}. Error: {str(e)}")
        return ""

        
def build_jira_title(app_name, platform, lob, sub_title):
    return f'''[E2E][{app_name.upper()}][{platform.upper()}][{lob}] - {sub_title}'''

def build_test_suite_link(feature_name, test_sheet):
    return f"*Test Suite Link:* [{feature_name}|{test_sheet}]"

def build_build_info(video_path, screenshot_path):
    return f"*Build Information:* Metes link, video link, etc - {video_path} {screenshot_path}"

def build_platform_impact(platform):
    return f"*Platforms impacted:* If this is Android, mention if the issue is happening on iOS and vice versa - {platform}"

def build_static_account_info():
    return '''
        *Static Account Details:*
        - *Account Mobile:*
        - *Password:*
        - *App:*
        - *Platform:*
        - *Drive link:*
    '''

def build_dynamic_account_info(studio_uuid, account_info):
    return f'''
        *Dynamic Account Details:*
        - *Interactive UUID:* {studio_uuid}
        {account_info}
    '''

def build_device_info(build_type, build_version, node_type, os_version):
    return f'''
        *Build type(CD/Release):* - {build_type}
        *Build version:* - {build_version}
        *Device Type:* - {node_type}
        *Os version:* - {os_version}
    '''     
        
        
        
# utility
def remove_tags(text):
    """
    The `remove_tags` function removes HTML tags and replaces "<br />" with newline characters from the
    input text.
    """
    text = text.replace("<br />", "\n")
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', text).rstrip()

def remove_numbered_lists(text):
    """
    The function `remove_numbered_lists` removes numbered lists from a given text.
    """
    return re.sub(r'\d+\.\s*', '', text).rstrip()

def add_numbered_prefix(s):
    """
    The function `add_numbered_prefix` adds line numbers as prefixes to non-empty lines in a given
    string.
    """
    lines = s.split('\n')
    prefixed_lines = [f'{i+1}. {line}' if line else line for i, line in enumerate(lines) if line]
    return '\n'.join(prefixed_lines)

def get_application_id(app_name):
    return utils.load_mapping_data()['application_details'][app_name]['application_id']
    
def get_platform_id(platform):
    return utils.load_mapping_data()['platform_details'][platform]['platform_id']

def get_component(run_details):
    return 'Android' if run_details['platform'] == 'android' else 'iOS'


if __name__ == "__main__":
    print(get_platform_id('android'))
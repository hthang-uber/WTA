from utility import DBQueryExecutor
from utility import utils
from utility import SvcSlaHealthBotAuth
from utility import TicketCreationUtility

from jira import JIRA, JIRAError
from datetime import datetime, date

def initiate_jira_client():
    """
    Initiates a JIRA client by obtaining an access token using client credentials grant type.

    Returns:
        JIRA: Authenticated JIRA client object
    """
    access_token = SvcSlaHealthBotAuth.get_bot_access_token()
    constants = utils.load_constant_yaml()['jira']
    jira_client = JIRA(
        constants['base_url'],
        basic_auth=(constants['usso_auth']['client_id'], access_token),
    )
    return jira_client

def jira_exception_handler(func):
    """
    Decorator to handle JIRA client exceptions by regenerating the client and retrying the function.
    """
    def wrapper(*args, **kwargs):
        jira_client = args[0]
        try:
            return func(*args, **kwargs)
        except JIRAError:
            # Regenerate the JIRA client and retry the function
            jira_client = initiate_jira_client()
            return func(jira_client, *args[1:], **kwargs)
    return wrapper

@jira_exception_handler
def create_jira_issue(jira_client, project='MTA', summary="", description="", issuetype="Bug", assignee_email="", labels=[], components="", priority="P2", buildVersion="", platform="", application=""):
    """
    Creates a new JIRA issue with the given parameters.
    """
    issue_dict = {
        'project': {'key': project},
        'summary': summary,
        'description': description,
        'issuetype': {'name': issuetype},
        "labels": labels,
        "components": [{"name": components}],
        'assignee': {'name': assignee_email},
        'priority': {'name': priority},
        'customfield_13204': buildVersion,
        'customfield_13203': {'id': platform},
        'customfield_13202': {'id': application}
    }
    
    new_issue = jira_client.create_issue(fields=issue_dict)
    return new_issue

@jira_exception_handler
def get_latest_jira_comment(jira_client, issue_key):
    """
    Prints the name of the first component of the given JIRA issue.
    """
    issue_obj = issue(jira_client, issue_key)
    print(issue_obj.fields.components[0].name)

@jira_exception_handler
def check_ticket_status(client, ticket_id):
    """
    Checks the status of a given JIRA ticket.
    """

    if ticket_id.strip() ==  "ECOP-4457":
        return True

    try:
        issue_obj = issue(client, ticket_id)
        status = issue_obj.fields.status.name
        return status and status != "Closed"
    except:
        return False
        

@jira_exception_handler
def latest_jira_key(client, ticket_id):
    """
    Retrieves the key of the given JIRA ticket.
    """
    issue_obj = issue(client, ticket_id)
    return issue_obj.key

@jira_exception_handler
def issue(client, ticket_id):
    """
    Retrieves the issue object for the given JIRA ticket.
    """
    return client.issue(ticket_id.strip())

@jira_exception_handler
def check_ticket_date(client, ticket_id):
    """
    Retrieves the creation date of the given JIRA ticket.
    """
    issue_obj = issue(client, ticket_id)
    return issue_obj.fields.created

@jira_exception_handler
def append_description(client, ticket_id, data):
    """
    Appends data to the description of the given JIRA ticket.
    """
    issue_obj = issue(client, ticket_id)
    description = issue_obj.fields.description
    issue_obj.update(description=f'''{description}\r\n{data}''')
    return description

@jira_exception_handler
def check_ticket_created_today(client, ticket_id):
    """
    Checks if the given JIRA ticket was created today.
    """
    issue_obj = issue(client, ticket_id)
    input_string = issue_obj.fields.created
    output_string = datetime.strptime(input_string, '%Y-%m-%dT%H:%M:%S.%f%z').date()
    today = date.today()
    return output_string == today

@jira_exception_handler
def get_latest_jira_comment(jira_client, issue_key, sr_no=1):
    """
    The function `get_latest_jira_comment` retrieves the latest comment on a Jira issue using a Jira
    client and issue key, with an optional parameter to specify the comment serial number.
    """
    issue = jira_client.issue(issue_key)
    comment = issue.fields.comment.comments[len(issue.fields.comment.comments)-sr_no]
    print(comment, comment.body)

@jira_exception_handler
def append_label(jira_client, issue_key, list_of_labels):
    """
    The function `append_label` retrieves the append the labels on Jira issue
    """
    issue = jira_client.issue(issue_key)
    label = issue.fields.labels+list_of_labels
    dict_1 = {
        "labels": label,
    }
    issue.update(fields=dict_1)

@jira_exception_handler
def delete_latest_jira_comment(jira_client, issue_key, sr_no=1):
    """
    This function deletes the latest comment on a Jira issue using the provided Jira client and issue
    key.
    """
    get_latest_jira_comment(jira_client, issue_key, sr_no)
    issue = jira_client.issue(issue_key)
    comment = jira_client.comment(issue_key, issue.fields.comment.comments[len(issue.fields.comment.comments)-sr_no])
    comment.delete()


def create_jira_ticket(client, run_details):
    
    SCREENSHOT_1 = "new_ticket_last_snapshot.png"
    

    labels = TicketCreationUtility.get_labels(run_details['build_version'], run_details['app_name'], run_details['platform'], run_details['test_method'])
    components = 'Android' if run_details['platform'] == 'android' else 'iOS'
    desc, summary = TicketCreationUtility.get_jira_description(run_details)
    priority = utils.load_constant_yaml()['jira_ticket_priority']
    application_id = TicketCreationUtility.get_application_id(run_details['app_name'])
    platform_id = TicketCreationUtility.get_platform_id(run_details['platform'])
    print(application_id, platform_id)
    ticket_id = create_jira_issue(client, project='MTA', summary=summary, description=desc, issuetype="Bug", assignee_email="pedara@ext.uber.com", labels=labels, components=components, priority=priority,buildVersion = run_details['build_version'],platform = platform_id, application= application_id ).key


    if run_details['screen_shots_link']:
        path = utils.get_substring(run_details['run_uuid'], '-', True)
        utils.download_images_from_terrablob(run_details['screen_shots_link'], path, SCREENSHOT_1)
        full_path = f'{path}/{SCREENSHOT_1}'
        with open(full_path, 'rb') as img:
            client.add_attachment(issue=ticket_id, attachment=img)
        f_index = desc.find("*Build Information") - 2
        client.issue(ticket_id).update(description=utils.insert_substring(desc, f'''\n\r\n!{SCREENSHOT_1}|width=200,height=400!\r\n''', f_index, f_index))
        utils.remove_path(path)
    
    return ticket_id
    
    
def create_jira_ticket_mtp(client, run_uuid):
    run_uuid_data  = DBQueryExecutor.get_mtp_data(run_uuid)
    for _, curr_failure in run_uuid_data.iterrows():
        ticket_id = create_jira_ticket(client, curr_failure)
        print(ticket_id)


def create_jira_ticket_mtp(client, run_uuid):
    run_uuid_data  = DBQueryExecutor.get_mtp_data(run_uuid)
    for _, curr_failure in run_uuid_data.iterrows():
        ticket_id = create_jira_ticket(client, curr_failure)
        print(ticket_id)
        

if __name__ == "__main__":
    client = initiate_jira_client()
    # run_uuid_data  = DBQueryExecutor.get_mtp_data('a57ad3be-9e34-4a6f-9197-32aaaee4c670')
    # for _, curr_failure in run_uuid_data.iterrows():
    #     TicketCreationUtility.get_platform_id(curr_failure['platform'])
    # # create_jira_ticket_mtp(client, 'a57ad3be-9e34-4a6f-9197-32aaaee4c670')
    delete_latest_jira_comment(client, 'MISO-9481', 2)
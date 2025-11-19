from utility import JiraAuth
from utility import DBQueryExecutor

def add_comment_to_jira(bundle, t_date):

    client = JiraAuth.initiate_jira_client()

    triaged_mtp_data = DBQueryExecutor.get_triaged_data__for_all_failure_type(bundle, t_date)

    unique_test_ids = triaged_mtp_data['ticket_id'].unique()
    
    for test_id in unique_test_ids:
        if JiraAuth.check_ticket_created_today(client, test_id):
            filtered_df = triaged_mtp_data.loc[triaged_mtp_data['ticket_id'] == test_id]
            failure_links = ""
            
            for _, method in filtered_df.iterrows():
                failure_links+= "\nhttps://mtp.uberinternal.com/test-run/"+method['run_uuid']

            JiraAuth.append_description(client, test_id, f'''\n\r Other Impacted MTPs: {failure_links}\r\n''')
        else:
            issue = client.issue(test_id)
            labels = issue.fields.labels

            label_transitions = {
                '#E2EIntermittent': '#E2EAlways',
                '#E2EOneTime': '#E2EIntermittent'
            }

            for old_label, new_label in label_transitions.items():
                if old_label in labels:
                    labels.remove(old_label)
                    labels.append(new_label)
                    issue.update(fields={'labels': labels})
                    break

if __name__ == "__main__":
    add_comment_to_jira("android_eats_nightly_appium_main", "2025-04-09")
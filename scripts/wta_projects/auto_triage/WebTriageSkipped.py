from utility import DBQueryExecutor
from utility import UpdateMetesRun

if __name__ == "__main__":
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
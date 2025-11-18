from utility import DBQueryExecutor
from utility  import utils
import os
import pickle
from googleapiclient.discovery import build
import importlib.resources as pkg_resources

class GSheets:
    def __init__(self):
        creds = None
        with pkg_resources.open_binary('src.utility', 'token.pickle') as file:
            creds = pickle.load(file)
        if os.path.exists('./token.pickle'):
            with open('./token.pickle', 'rb') as token:
                creds = pickle.load(token)
        self.service = build("sheets", "v4", credentials=creds).spreadsheets()

    def get_test_feature_details(self, test_method):
        feature_name = ""
        test_sheet = ""
        constants = utils.load_constant_yaml()
        try:
            feature_name = DBQueryExecutor.get_feature_name(test_method)[0]
            result = (
                self.service
                    .values()
                    .get(spreadsheetId=constants['spreadsheet_id'], range=constants['spreadsheet_range'])
                    .execute()
            )
            rows = result.get("values", [])
            for row in rows:
                if feature_name in row:
                    test_sheet = row[10]
        except Exception as e:
            print(f"""No related feature name or test sheet found: {test_method}""", str(e))

        return feature_name, test_sheet




if __name__ == "__main__":
    test_method = "com.uber.e2e.android.eats.test.eatercoreflows.FilterResultsTest/testFilterResultsVertical"
    feature_name = ""
    test_sheet = ""
    query = f'''
        select
          scenarioname as feature_name
        from
          core_Automation_platform.test_case
        where
            parsedautomationname = '{test_method}'
            or appiumautomationname = '{test_method}'
        LIMIT 1
        '''
    feature_name = DBQueryExecutor.execute_query(query, consumer=False, db="presto").get('feature_name',[])[0]
    print(feature_name)
    result = (
    GSheets().service
        .values()
        .get(spreadsheetId="1Z2_3W3LnyfFGy_HQBb3jWX9J-hBMueQdiLfAqWwCxio", range="Master Sheet")
        .execute()
    )
    rows = result.get("values", [])
    for row in rows:
        if feature_name in row:
            test_sheet = row[10]
            print(test_sheet)
from utility import utils
import requests


def get_bot_access_token():
    """
    The function `get_bot_access_token` retrieves an access token using client credentials
    authentication.
    """
    constants = utils.load_constant_yaml()['jira']['usso_auth']
    req = requests.post(
        constants['token_url'],
        headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        auth=(constants['client_id'], constants['client_secret']),
        data={
            'grant_type': 'client_credentials',
            'audience': 't3.uberinternal.com'
        }
    )
    res = req.json()
    return res['access_token']
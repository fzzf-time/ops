import requests
from requests.auth import HTTPBasicAuth
import logging
import datetime

# Jenkins URL
jenkins_url = 'https://jenkins.kipas-dev.com'


def _get_node_info(node, auth):
    """
    Get node info from Jenkins.
    :param node: node name
    """
    # use json as content type when use get method
    headers = {
        'Content-Type': 'application/json',
    }

    node_info_api = f'{jenkins_url}/computer/{node}/api/json'
    response = requests.get(node_info_api, auth=auth, headers=headers, timeout=10)
    if response.status_code == 200:
        node_info = response.json()
        if node_info['offline']:
            logging.info(f'Node {node} is already offline, offline message: {node_info["offlineCauseReason"]}')
            return {'offline': True, 'offline_message': node_info["offlineCauseReason"]}
        else:
            logging.info(f'Node {node} is online.')
            return {'offline': False, 'offline_message': node_info["offlineCauseReason"]}
    else:
        logging.error(f'Failed to get node {node} info. Status code: {response.status_code}')
        logging.error('Response JSON:', response.json())


def _do_offline(node, auth, message=None):
    """
    Take a node offline on Jenkins.
    :param node: node name
    :param message: optional offline message
    :return: None
    """
    node_info = _get_node_info(node, auth)
    if node_info['offline']:
        return

    offline_api = f'{jenkins_url}/computer/{node}/doDisconnect'

    msg = 'Available times:  from Workday 9:00 AM to 7:30 PM UTC+8' if message is None else message

    params = {
        'offlineMessage': msg
    }

    response = requests.post(offline_api, auth=auth, params=params, timeout=10)
    if response.status_code == 200:
        logging.info(f'Successfully took the node {node} offline.')

    else:
        logging.error(f'Failed to take the node {node} offline. Status code: {response.status_code}')


def _do_online(node, auth):
    """
    Take a node online on Jenkins.
    :param node: node name
    :return: None
    """
    node_info = _get_node_info(node, auth)
    if not node_info['offline']:
        return

    online_api = f'{jenkins_url}/computer/{node}/launchSlaveAgent'
    response = requests.post(online_api, auth=auth, timeout=10)
    if response.status_code == 200:
        logging.info(f'Successfully took the node {node} online.')
    else:
        logging.error(f'Failed to take the node {node} online. Status code: {response.status_code}')


def jenkins_node(node):
    # Jenkins username and API Token
    username = 'zhaoruwei'
    api_token = '1134838ff1f059ab8e9ff939e25b3f3981'
    auth = HTTPBasicAuth(username, api_token)

    now = datetime.datetime.now()
    current_time = now.time()
    current_day = now.weekday()  # Monday is 0 and Sunday is 6

    start_time = datetime.time(9, 0)
    end_time = datetime.time(19, 30)

    if current_day in range(5) and start_time <= current_time <= end_time:
        _do_online(node, auth)
    else:
        _do_offline(node, auth)

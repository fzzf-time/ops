import json
import logging

from flask import Flask, request, jsonify
import requests

from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_console.client import Client as ConsoleClient
from alibabacloud_tea_util.client import Client as UtilClient

app = Flask(__name__)

'''
{
    'event': 'alert_state_change',
    'alert': {
        'id': 2,
        'name': 'PG WAL LAG [PROD]: lag > 1000',
        'options': {
            'op': '>=',
            'value': '10',
            'muted': False,
            'column': 'lag'
        },
        'state': 'ok',
        'last_triggered_at': '2024-05-23T02:08:33.027Z',
        'updated_at': '2024-05-23T02:08:33.017Z',
        'created_at': '2024-05-17T03:37:38.563Z',
        'rearm': None,
        'query_id': 13,
        'user_id': 21,
        'description': '',
        'title': ''
    },
    'url_base': ''
}

'''

class SMS:
    @staticmethod
    def create_client(key, secret) -> Dysmsapi20170525Client:
        config = open_api_models.Config(
            access_key_id=key,
            access_key_secret=secret
        )
        config.endpoint = 'dysmsapi.aliyuncs.com'
        return Dysmsapi20170525Client(config)

    @staticmethod
    def send_sms(key, secret, phone, alert_id, alert_name, alert_state):
        client = SMS.create_client(key, secret)
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            phone_numbers=phone,
            sign_name='广州百年数据科技',
            template_code='SMS_473710258',
            template_param=UtilClient.to_jsonstring({
                "alert_id": alert_id,
                "name": alert_name,
                "status": alert_state,
            })
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = client.send_sms_with_options(send_sms_request, runtime)
            logging.info(ConsoleClient.log(UtilClient.to_jsonstring(resp)))
        except Exception as error:
            logging.error(error.message)
            logging.error(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)

# ref: https://developer.work.weixin.qq.com/document/path/91770#markdown%E7%B1%BB%E5%9E%8B
def _send_wecom(token, contents):
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={token}"
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"""{contents}"""
        }
    }

    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=data, headers=headers)
    return response.json(), response.status_code

@app.route('/send_wework', methods=['POST'])
def send_wework():
    wework_key = request.args.get('key')
    data = request.get_json(force=True)
    logging.info(data)

    content = f'''{data['alert']['name']} \n
 - status: {data['alert']['state']} \n
 - condition: {data['alert']['options']['op']}{data['alert']['options']['value']} \n
 - result: {data['alert']['description'].strip()} \n
 - query_url: "https://redash.kipas-dev.com/queries/{data['alert']['query_id']}" \n
 - alert_url: "https://redash.kipas-dev.com/alerts/{data['alert']['id']}"
              '''
    ret, ret_status_code = _send_wecom(wework_key, content)

    if str(ret_status_code).startswith("2"):
        return jsonify(ret)
    raise ValueError(json.dumps(ret))

@app.route('/send_sms', methods=['POST'])
def send_sms():
    phone = request.args.get('phone')
    data = request.get_json(force=True)
    logging.info(data)

    alert_id = data['alert']['id']
    alert_name = data['alert']['name']
    alert_state = data['alert']['state']

    if phone:
        SMS.send_sms(app.config['access_key_id'], app.config['access_key_secret'], phone, alert_id, alert_name, alert_state)
        logging.info("SMS sent successfully.")
    else:
        logging.warning("Recipient phone number not provided.")

    return jsonify({"message": "SMS sent successfully."})

def alert_gateway(key, secret):
    app.config['access_key_id'] = key
    app.config['access_key_secret'] = secret
    app.run(host='0.0.0.0', port=8111)

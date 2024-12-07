from datetime import datetime
from datetime import timedelta
import logging

import requests
from alibabacloud_dysmsapi20170525.client import Client
from alibabacloud_dysmsapi20170525 import models
from alibabacloud_tea_openapi.models import Config


def _client(key, secret, ep) -> Client:
    config = Config(access_key_id=key, access_key_secret=secret)
    # ref https://api.aliyun.com/product/Dysmsapi
    config.endpoint = ep
    return Client(config)


def send_sms(key: str, secret: str, to: str, ep='dysmsapi.aliyuncs.com', sign_name='广州百年数据统计', template_code='SMS_469030011'):
    to = to if isinstance(to, tuple) else [to]
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    logging.info(f"dt={yesterday} {to=} {sign_name=} {template_code=}")

    resp = requests.get('https://redapi.kipas-dev.com/queries/daily_report')
    total_user = new_user = active_user = week_active_users = 0
    for row in resp.json():
        if row['col'] == 'total':
            total_user = row['count']
        elif row['col'] == 'new':
            new_user = row['count']
        elif row['col'] == 'active':
            active_user = row['count']
        elif row['col'] == 'week_active':
            week_active_users = row['count']
    logging.info(f"{total_user=} {new_user=} {active_user=} {week_active_users}")

    send_sms_request = models.SendSmsRequest(
        sign_name=sign_name,
        template_code=template_code,
        phone_numbers=','.join(map(str, to)),
        template_param=f"""{{"dt": "{yesterday}", "total": "{total_user}", "new": "{new_user}", "active": "{active_user}", "week_active": "{week_active_users}"}}"""
    )

    try:
        resp = _client(key, secret, ep).send_sms(send_sms_request)
        logging.info(resp.body)
    except Exception as ex:
        logging.error(ex)

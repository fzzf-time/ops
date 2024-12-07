import logging
import os
import sys

import fire

from apps.alert_gateway.app import alert_gateway
from apps.aliyun_exporter import aliyun_exporter
from apps.ali_sg_policy.app import ali_sg_policy
from apps.jenkins_node.app import jenkins_node
from apps.format_sql.format_sql import format_sql
from apps.psqllog2ch.app import psqllog2ch
from apps.redapi.app import redapi
from apps.send_sms.send_sms import send_sms
from apps.www.www import www


LOG_FORMAT = os.getenv("LOG_FORMAT", "[%(asctime)s|%(levelname)s|%(module)s:%(lineno)d] %(message)s")
LOG_DATE_FORMAT = os.getenv("LOG_DATE_FORMAT", "%H:%M:%S")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LEVEL = logging.getLevelName(LOG_LEVEL)
_handlers = [logging.StreamHandler(sys.stdout)]
logging.basicConfig(level=LEVEL, format=LOG_FORMAT, handlers=_handlers, datefmt=LOG_DATE_FORMAT)


if __name__ == '__main__':
    fire.Fire({
        'alert_gateway': alert_gateway,
        'aliyun_exporter': aliyun_exporter,
        'ali_sg_policy': ali_sg_policy,
        'format_sql': format_sql,
        'jenkins_node': jenkins_node,
        'psqllog2ch': psqllog2ch,
        'redapi': redapi,
        'send_sms': send_sms,
        'www': www,
    })

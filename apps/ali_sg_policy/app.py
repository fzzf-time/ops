import json
import logging
import os
import sys

import requests
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.DescribeSecurityGroupAttributeRequest import DescribeSecurityGroupAttributeRequest
from aliyunsdkecs.request.v20140526 import AuthorizeSecurityGroupRequest


# Get the public IP of the current program environment
def _get_public_ip():
    # Don't catch exception, exit if error
    response = requests.get('https://myip.kipas-dev.com')
    return response.text


def _sg_policy_need_update(publicip, client, sg_id):
    """ Get all policies of the specified security group, match and check if the detected public IP already exists.
    The program will add a policy with the Description: gz-intranet """
    request = DescribeSecurityGroupAttributeRequest()
    request.set_accept_format('json')
    request.set_SecurityGroupId(sg_id)
    response = client.do_action_with_exception(request)
    # Parse JSON response
    res_json = json.loads(response.decode('utf-8'))
    for permission in res_json['Permissions']['Permission']:
        if permission['Description'] == 'gz-intranet' and permission['SourceCidrIp'] == publicip:
            return False
    return True


def _add_sg_policy(publicip, client, sg_id):
    """ Add a security group policy to allow access from the public IP """
    request = AuthorizeSecurityGroupRequest.AuthorizeSecurityGroupRequest()
    request.set_accept_format('json')
    request.set_SecurityGroupId(sg_id)
    request.set_IpProtocol("ALL")
    request.set_PortRange("-1/-1")
    request.set_SourceCidrIp(publicip)
    request.set_Description("gz-intranet")
    response = client.do_action_with_exception(request)
    return response.decode('utf-8')


def ali_sg_policy(key, secret, region="ap-southeast-5", sg="sg-k1aixqpwzliu24oov30d"):
    client = AcsClient(key, secret, region_id=region)

    publicip = _get_public_ip()
    if _sg_policy_need_update(publicip, client, sg):
        request_id = _add_sg_policy(publicip, client, sg)
        logging.info(f"Successfully added security group policy for {publicip=}, {request_id=}")
        return
    logging.info(f"Security group policy for {publicip=} already exists")

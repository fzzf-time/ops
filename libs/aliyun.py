import json
import logging
from datetime import datetime, timedelta

from aliyunsdkcore.client import AcsClient
from aliyunsdkrds.request.v20140815.DescribeDBInstancesRequest import DescribeDBInstancesRequest
from aliyunsdkrds.request.v20140815.DescribeSlowLogRecordsRequest import DescribeSlowLogRecordsRequest

# from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
# from aliyunsdkecs.request.v20140526.DescribeRegionsRequest import DescribeRegionsRequest
# from aliyunsdkecs.request.v20140526.DescribeSecurityGroupsRequest import DescribeSecurityGroupsRequest
# from aliyunsdkecs.request.v20140526.DescribeSecurityGroupAttributeRequest import DescribeSecurityGroupAttributeRequest
# from aliyunsdkecs.request.v20140526.DescribeSecurityGroupReferencesRequest import DescribeSecurityGroupReferencesRequest
# from aliyunsdkecs.request.v20140526.ModifySecurityGroupRuleRequest import ModifySecurityGroupRuleRequest


class AliyunClient:
    def __init__(self, access_key_id=None, access_key_secret=None):
        self.access_key = access_key_id
        self.secret = access_key_secret
        self.client = None

    def get_client(self, region_id='ap-southeast-5'):
         if not self.client:
            self.client = AcsClient(self.access_key, self.secret, region_id)
 
    def req(self, request):
        if not self.client:
            self.__get_client()
        try:
            request.set_accept_format('json')
            response = self.client.do_action_with_exception(request)
        except Exception as e:
            print(e)
            return
        return json.loads(str(response, encoding='utf-8'))
 

class RDS(AliyunClient):
    def get_instances(self):
        '''
        获取RDS实例信息
        :return:
        '''
        request = DescribeDBInstancesRequest()
        response = self.req(request)
        return response["Items"]["DBInstance"]

    def _get_slow_logs(self, req):
        page = 1
        retry = 0
        req.set_PageSize(100)
        while True:
            req.set_PageNumber(page)
            response = self.req(req)
            try:
                logs = response.get("Items").get("SQLSlowRecord")
                if page == 1:
                    logging.info(f"total {response.get('TotalRecordCount')} records")
            except Exception as e:
                logging.error(e, response)
                if retry >= 3:
                    raise e
                retry += 1
                continue
            if not logs:
                break
            for log in logs:
                yield log
            page += 1
            retry = 0

    def get_slow_logs(self, instance_id, dt=""):
        '''
        获取RDS慢查询日志
        :param instance_id:
        :return:
        '''
        day = datetime.strptime(dt, "%Y-%m-%d")
        for hr in range(24):
            hr_ts = datetime.strftime(day + timedelta(hours=hr), "%Y-%m-%dT%H:")
            start_ts = f"{hr_ts}00Z"
            end_ts = f"{hr_ts}59Z"
            
            request = DescribeSlowLogRecordsRequest()
            request.set_DBInstanceId(instance_id)
            request.set_StartTime(start_ts)
            request.set_EndTime(end_ts)

            logging.info(f"{instance_id=} {start_ts=} {end_ts=}")
            for log in self._get_slow_logs(request):
                yield log
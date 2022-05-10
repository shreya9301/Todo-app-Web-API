import time
import json

import requests


class TimeService(object):
    """Sync time from server, and keep the time difference between local time and server time. Fix local timestamp by adding the difference.
    """

    def __init__(self, service, service_method="GET", service_headers=None, service_params=None, service_json=None, result_field_name="result", repeat=3, ratio=1):
        """
        service: An url of time service. The service response json format: {"success": True, "result": 1612918465.766}
        ratio: Service returns timestamp in milliseconds, the ratio must be 1000. Service returns timestamp in seconds, the ratio must be 1.  Service returns timestamp in microseconds, the ratio must be 1000000. 
        """
        self.service = service
        self.service_method = service_method
        self.service_headers = service_headers
        self.service_params = service_params
        self.service_json = service_json
        self.result_field_name = result_field_name
        self.repeat = repeat
        self.ratio = ratio
        self.fix_delta = 0

    def init(self):
        min_delta = 18446744073709551616
        fix_delta = 0
        for _ in range(self.repeat):
            stime = time.time()
            response = requests.request(self.service_method, self.service, params=self.service_params, json=self.service_json)
            response_data = json.loads(response.content)
            timestamp = response_data.get(self.result_field_name, 0) / self.ratio
            etime = time.time() 
            delta = etime - stime
            if timestamp and delta < min_delta:
                min_delta = delta
                fix_delta = timestamp - etime + delta/2
        self.fix_delta = fix_delta

    def now(self):
        return self.fix_delta + time.time()


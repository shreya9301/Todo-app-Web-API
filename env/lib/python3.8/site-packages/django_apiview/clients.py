import requests

from .pack import SimpleJsonResultPacker


class ApiviewClient(object):

    def __init__(self, packer=None):
        self.packer = packer or SimpleJsonResultPacker()

    def get(self, url, params=None):
        params = params or {}
        response = requests.get(url, params=params)
        return self.packer.unpack(response.content)

    def post(self, url, params=None, data=None):
        params = params or {}
        data = data or {}
        response = requests.post(url, params=params, json=data)
        return self.packer.unpack(response.content)


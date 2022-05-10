
import os
import requests
from urllib.parse import urlparse
from urllib.parse import ParseResult

def get_urlinfo(url):
    return urlparse(url)

def get_url_filename(url, info=None):
    if info is None:
        if isinstance(url, ParseResult):
            info = url
        else:
            info = urlparse(url)
    path = info.path
    filename = os.path.split(path)[1]
    if not filename:
        filename = "index.html"
    return filename

def get_url_save_path(url, save_root):
    if isinstance(url, ParseResult):
        info = url
    else:
        info = urlparse(url)
    filename = get_url_filename(url, info)
    path = info.path.split(info.path)[0]
    filepath = os.path.abspath(os.path.join(save_root, "."+path+"/", filename))
    return filepath

def get_sitename(url):
    if isinstance(url, ParseResult):
        info = url
    else:
        info = urlparse(url)
    return info.hostname

def download(url, filename):
    response = requests.get(url)
    size = 0
    with open(filename, "wb") as fobj:
        for data in response.iter_content(4096, False):
            size += len(data)
            fobj.write(data)
    return size


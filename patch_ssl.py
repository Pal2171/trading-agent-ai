import ssl
import urllib3
import requests
import httpx

# Disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Patch requests
old_request = requests.Session.request
def new_request(self, method, url, *args, **kwargs):
    kwargs['verify'] = False
    return old_request(self, method, url, *args, **kwargs)
requests.Session.request = new_request

# Patch httpx
old_init = httpx.Client.__init__
def new_init(self, *args, **kwargs):
    kwargs['verify'] = False
    old_init(self, *args, **kwargs)
httpx.Client.__init__ = new_init

print("SSL Verification disabled globally via patch_ssl.py", flush=True)

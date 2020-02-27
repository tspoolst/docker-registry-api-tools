#!/usr/bin/env python3

#[of]:imports
import os
import sys
import re

import datetime

#[of]:imports with auto pkg update
import pkg_resources
from distutils.version import LooseVersion
#[of]:import py/yaml
if len(sys.argv) > 1 and sys.argv[1] == "--module_installed_pyyaml":
  sys.argv.pop(1)
  try:
    pkg_version = pkg_resources.get_distribution("pyyaml").version
  except pkg_resources.DistributionNotFound:
    sys.exit("""We were unable to auto-install dependencies please run and investigate:
                pip3 install --upgrade --user pyyaml""")
else:
  try:
    pkg_version = pkg_resources.get_distribution("pyyaml").version
  except pkg_resources.DistributionNotFound:
    os.system('pip3 install --upgrade --user pyyaml' + "> /dev/null 2>&1")
    sys.argv.insert(1,"--module_installed_pyyaml")
    os.execl(sys.executable, sys.executable, * sys.argv)
if LooseVersion(pkg_version) < LooseVersion("5.1"):
  sys.exit("""We were unable to auto-install pyyaml >= 5.1 please run and investigate:
              pip3 install --upgrade --user pyyaml""")

import yaml
#[cf]
#[of]:import requests
if len(sys.argv) > 1 and sys.argv[1] == "--module_installed_requests":
  sys.argv.pop(1)
  try:
    pkg_version = pkg_resources.get_distribution("requests").version
  except pkg_resources.DistributionNotFound:
    print("e1 " + str(sys.argv))
    sys.exit("""We were unable to auto-install dependencies please run and investigate:
                pip3 install --upgrade --user requests""")
else:
  try:
    pkg_version = pkg_resources.get_distribution("requests").version
  except pkg_resources.DistributionNotFound:
    print("e2 " + str(sys.argv))
    os.system('pip3 install --upgrade --user requests' + "> /dev/null 2>&1")
    sys.argv.insert(1,"--module_installed_requests")
    os.execl(sys.executable, sys.executable, * sys.argv)
if LooseVersion(pkg_version) < LooseVersion("2.22"):
  print("e3 " + str(sys.argv))
  sys.exit("""We were unable to auto-install requests >= 2.22 please run and investigate:
              pip3 install --upgrade --user requests""")

import requests
#[cf]
#[cf]

import base64

import shlex
import time
import argparse
import configparser
from configparser import RawConfigParser as ConfigParser, NoSectionError, NoOptionError

import json

#[cf]
#[of]:functions
#[of]:rest
def to_yaml(data):
    return yaml.safe_dump(data, indent=2, default_flow_style=False, explicit_start=True)
def to_json(data):
    return json.dumps(data)
#[cf]
#[of]:web
#[of]:def http_get(path)\:
def http_get(path):
  return http_req('GET', path, None)
#[cf]
#[of]:def http_post(path, body=None)\:
def http_post(path, body=None):
  return http_req('POST', path, body)
#[cf]
#[of]:def http_put(path, body=None)\:
def http_put(path, body=None):
  return http_req('PUT', path, body)
#[cf]
#[of]:def http_delete(path)\:
def http_delete(path):
  return http_req('DELETE', path, None)
#[cf]
#[of]:def http_req(method, path, body)
def http_req(method, path, body):
  DEFAULT_TIMEOUT = 300
  DEFAULT_RETRY_AFTER_SECONDS = 5
  MAX_RETRIES = DEFAULT_TIMEOUT / DEFAULT_RETRY_AFTER_SECONDS

  for _ in range(int(MAX_RETRIES)):
    try:
      res = requests.request(method, path, headers=http_headers(), data=body, timeout=DEFAULT_TIMEOUT)
      if str(res.status_code) in ('423', '409', '422'):
        raise ResourceBusy(res, path)
      if str(res.status_code) in ('429'):
        raise RateLimited(res, path)
      if re.search('^2\d\d', str(res.status_code)) is None:
        raise HttpRequestError(res, path)
    except RateLimited:
      print("Rate limited, retrying in " + str(DEFAULT_RETRY_AFTER_SECONDS) + " seconds")
      time.sleep(DEFAULT_RETRY_AFTER_SECONDS)
      continue
    except ResourceBusy:
      print("Resource busy, retrying in " + str(DEFAULT_RETRY_AFTER_SECONDS) + " seconds")
      time.sleep(DEFAULT_RETRY_AFTER_SECONDS)
      continue
    except requests.exceptions.ConnectionError as errc:
      print("Error Connecting:",errc)
      sys.exit(1)
    # except HttpRequestError as e:
    #   print("http error {}, {}, {}".format(e.message, e.code, e.body))
    #   sys.exit(1)
    else:
      return res
  else:
    raise HttpRetryLimit(path)

# except requests.exceptions.HTTPError as errh:
#   print("Http Error:",errh)
# except requests.exceptions.ConnectionError as errc:
#   print("Error Connecting:",errc)
# except requests.exceptions.Timeout as errt:
#   print("Timeout Error:",errt)
# except requests.exceptions.RequestException as err:
#   print("OOps: Something Else",err)

#[of]:class Error(Exception)\:
class Error(Exception):
   """Base class for other exceptions"""
   pass
#[cf]
#[of]:class RateLimited(Error)\:
class RateLimited(Error):
  def __init__(self, res, message):
    self.code = res.status_code
    self.reason = res.reason
    self.message = message
    print("http rate limited, {} {}, {}".format(self.code, self.reason, self.message))
#[cf]
#[of]:class ResourceBusy(Error)\:
class ResourceBusy(Error):
  def __init__(self, res, message):
    self.code = res.status_code
    self.reason = res.reason
    self.message = message
    print("http busy, {} {}, {}".format(self.code, self.reason, self.message))
#[cf]
#[of]:class HttpRequestError(Error)\:
class HttpRequestError(Error):
  def __init__(self, res, message):
    self.code = res.status_code
    self.reason = res.reason
    self.message = message
    print("http error, {} {}, {}".format(self.code, self.reason, self.message))
    sys.exit(1)
#[cf]
#[of]:class HttpRetryLimit(Error)\:
class HttpRetryLimit(Error):
  def __init__(self, message):
    self.message = message
    print("http reached retry limit connecting to " + message)
    sys.exit(1)
#[cf]
#[cf]
#[of]:def http_headers
def http_headers():
  return {
    'Content-Type' : 'application/json',
    'Accept' : 'application/vnd.docker.distribution.manifest.v2+json'
  }
#[c]    'Authorization' : http_auth_header(),
#[cf]
#[cf]
#[cf]

if len(sys.argv) != 2:
  print("Too few arguments - Must have", 1, "argument(s)")
  print("USAGE:" , sys.argv[0], "<docker_repo_address>")
  print("EXAMPLE:" , sys.argv[0], "10.10.61.17:5000")
  sys.exit(1)

base_url = "http://" + sys.argv[1]

res = http_get(base_url + "/v2/_catalog")
image_names = json.loads(res.text)['repositories']
#[c]sorted(image_names, key = lambda i: i.lower())
for image_name in image_names:
  res = http_get(base_url + '/v2/' + image_name + '/tags/list')
  image_tags = json.loads(res.text)['tags']
  # print(image_name + "\n" + to_yaml(image_tags))
  for image_tag in image_tags:
    # print(image_name + ":" + image_tag)
    res = http_get(base_url + '/v2/' + image_name + '/manifests/' + image_tag)
    body = json.loads(res.text)
    digest = res.headers['Docker-Content-Digest']
    print(image_name + ":" + image_tag + " " + digest)

#[c]  print(to_yaml(body))


# vim:number:tabstop=2:shiftwidth=2:autoindent:foldmethod=marker:foldlevel=0:foldmarker=#[of],#[cf]

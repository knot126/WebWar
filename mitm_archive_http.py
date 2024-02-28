"""
Mirror all web pages.

Useful if you are living down under.
"""

import hashlib
import pathlib
import os
import json
import time
from mitmproxy import http

DB = "/home/dragon/Development/Scripts/archive"
SAVE_HEADERS = True

def __quote(s):
	return '"' + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + '"'

def __save_contents(basedir, content):
	"""
	Save the content to a file named after the hash of the file. Returns hash.
	"""
	
	h = hashlib.sha256(content).hexdigest()
	
	os.makedirs(basedir, exist_ok = True)
	
	with open(f"{basedir}/{h}", "wb") as f:
		f.write(content)
	
	return h

def response(flow: http.HTTPFlow) -> None:
	if flow.response and flow.response.content:
		host = flow.request.host
		url = flow.request.url
		
		ch = __save_contents(f"{DB}/{host}", flow.response.content)
		hh = __save_contents(f"{DB}/{host}", bytes(flow.response.headers)) if SAVE_HEADERS else None
		
		mpath = f"{DB}/{host}/map.json"
		m = []
		
		try:
			m = json.loads(pathlib.Path(mpath).read_text())
		except:
			pass
		
		m.append({
			"url": url,
			"time": int(time.time()),
			"content": ch,
		})
		
		if (SAVE_HEADERS):
			m[-1]["headers"] = hh
		
		pathlib.Path(mpath).write_text(json.dumps(m, indent = 4))

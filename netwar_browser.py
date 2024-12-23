#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from html.parser import HTMLParser
from pathlib import Path
import json
import traceback
from email.parser import BytesParser
import argparse
import libwebwar
import re

def getNoProto(url):
	return url.replace("https://", "").replace("http://", "").replace("://", "").replace("//", "")

def getHost(url):
	return getNoProto(url).split("/")[0]

def getPath(url):
	url = getNoProto(url)
	return url[url.index("/"):]

def getFuzzyPath(url):
	url = getNoProto(url).lower().removeprefix("www.").removesuffix("/")
	
	return url

def matchFuzzyPath(url1, url2):
	return getFuzzyPath(url1) == getFuzzyPath(url2)

def getClosestHashFromMap(m, url):
	for x in m:
		if matchFuzzyPath(x["url"], url):
			return x["content"], x.get("headers", None)
	
	return None, None

def parseHeaders(h):
	return BytesParser().parsebytes(h)

def dictToHtmlTags(d):
	o = ""
	
	for k in d:
		if (d[k] != None):
			o += f"{k}=\""
			o += d[k].replace("\"", "&quot;").replace("&", "&amp;")
			o += "\" "
		else:
			o += f"{k}"
	
	return o[:-1]

def toAbsolutePath(host, base_url, url):
	# return url
	if (url.startswith("http") or url.startswith("://") or url.startswith("//") or url.startswith(getHost(base_url))):
		return f"http://{host}/{getNoProto(url)}"
	elif (url.startswith("/")):
		return f"http://{host}/{getHost(base_url)}{url}"
	elif (url.startswith("data:")):
		return url
	else:
		# TODO
		return f"http://{host}/{base_url}/{url}"

class HTMLModifier(HTMLParser):
	def __init__(self, m, url, host):
		super().__init__()
		self.m = m
		self.url = url
		self.out = ""
		self.host = host
	
	def handle_starttag(self, tag, attrs):
		attrs = dict(attrs)
		
		for T in ["src", "action", "href"]:
			if (T in attrs):
				attrs[T] = toAbsolutePath(self.host, self.url, attrs[T])
		
		self.out += f"<{tag} {dictToHtmlTags(attrs)}>"
	
	def handle_endtag(self, tag):
		self.out += f"</{tag}>"
	
	def handle_data(self, data):
		self.out += data

def fixupCss(css, host, base_url):
	results = re.findall(r"url\([^\)]+\)", css)
	
	for r in results:
		r = r[4:-1]
		css = css.replace(f"url({r})", f"url({toAbsolutePath(host, base_url, r)})")
	
	return css

class MyServer(BaseHTTPRequestHandler):
	# Kind of a hack to keep it as a static variable
	archive = None
	
	def do_GET(self):
		try:
			url = self.path[1:]
			archive = self.__class__.archive
			
			if self.path == "/favicon.ico":
				url = getHost(self.headers["Referer"].removeprefix(f"http://{self.headers['Host']}/")) + "/favicon.ico"
			
			m = json.loads(archive.read(f"{getHost(url)}/map.json"))
			
			content_hash, header_hash = getClosestHashFromMap(m, url)
			
			if not content_hash:
				return self.respond(404, "text/html", "<h1>Oh no!</h1><p>It seems like this page wasn't archived.</p>")
			
			if not header_hash:
				return self.respond(404, "text/html", "<h1>Oh no!</h1><p>This page was archived, but the header information required to reconstruct the response is not present.</p>")
			
			data = archive.read(f"{getHost(url)}/{content_hash}")
			headers = parseHeaders(archive.read(f"{getHost(url)}/{header_hash}"))
			
			if ("text/html" in headers["Content-Type"]):
				hp = HTMLModifier(m, url, self.headers["host"])
				hp.feed(data.decode())
				data = hp.out
			
			if ("text/css" in headers["Content-Type"]):
				data = fixupCss(data.decode(), self.headers["host"], url)
			
			self.respond(200, headers["Content-Type"], data)
		except:
			data = traceback.format_exc()
			
			self.respond(500, "text/html", f"<h1>Oops!</h1><p>WebWar hit an error!</p><pre>{data}</pre>")
	
	def respond(self, status = 200, content_type = None, data = b"", headers = None):
		headers = headers or {}
		headers["Content-Length"] = str(len(data))
		
		if "Content-Type" not in headers:
			headers["Content-Type"] = content_type or "text/html"
		
		self.send_response(status)
		
		for k, v in headers.items():
			self.send_header(k, v)
		
		self.end_headers()
		self.wfile.write(data if type(data) == bytes else data.encode())

if __name__ == "__main__":
	args = argparse.ArgumentParser(
		prog="netwar_browser",
		description="Browse NetWar archives",
	)
	args.add_argument("archive", help="Path to the folder or ZIP of the archive to browse")
	args = args.parse_args()
	
	MyServer.archive = libwebwar.Archive(args.archive, True)
	print(MyServer.archive)
	webServer = HTTPServer(("0.0.0.0", 8000), MyServer)
	
	try:
		webServer.serve_forever()
	except KeyboardInterrupt:
		pass
	
	webServer.server_close()
	print("Server stopped.")

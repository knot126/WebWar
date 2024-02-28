from http.server import BaseHTTPRequestHandler, HTTPServer
from html.parser import HTMLParser
from pathlib import Path
import json
import traceback
from email.parser import BytesParser

ARCHIVE_DIR = "/home/dragon/Development/Scripts/archive"

def getNoProto(url):
	return url.replace("https://", "").replace("http://", "").replace("://", "").replace("//", "")

def getHost(url):
	return getNoProto(url).split("/")[0]

def getPath(url):
	url = getNoProto(url)
	return url[url.index("/"):]

def getClosestHashFromMap(m, url):
	url = getNoProto(url)
	
	for x in m:
		if (getNoProto(x["url"]) == url):
			return x["content"], x["headers"]
	
	return None

def parseHeaders(h):
	return BytesParser().parsebytes(h)

def dictToHtmlTags(d):
	o = ""
	
	for k in d:
		if (d[k]):
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
		
		for T in ["src", "altsrc", "href"]:
			if (T in attrs):
				attrs[T] = toAbsolutePath(self.host, self.url, attrs[T])
		
		self.out += f"<{tag} {dictToHtmlTags(attrs)}>"
	
	def handle_endtag(self, tag):
		self.out += f"</{tag}>"
	
	def handle_data(self, data):
		self.out += data

class MyServer(BaseHTTPRequestHandler):
	def do_GET(self):
		try:
			url = self.path[1:]
			
			m = json.loads(Path(f"{ARCHIVE_DIR}/{getHost(url)}/map.json").read_text())
			
			content_hash, header_hash = getClosestHashFromMap(m, url)
			
			data = Path(f"{ARCHIVE_DIR}/{getHost(url)}/{content_hash}").read_bytes()
			headers = parseHeaders(Path(f"{ARCHIVE_DIR}/{getHost(url)}/{header_hash}").read_bytes())
			
			if ("text/html" in headers["Content-Type"]):
				hp = HTMLModifier(m, url, self.headers["host"])
				hp.feed(data.decode())
				data = hp.out
			
			self.send_response(200)
			self.send_header("Content-Type", headers["Content-Type"])
			self.send_header("Content-Length", str(len(data)))
			self.end_headers()
			self.wfile.write(data if type(data) == bytes else data.encode())
		except:
			data = traceback.format_exc().encode()
			
			self.send_response(400)
			self.send_header("Content-Type", "text/plain")
			self.send_header("Content-Length", str(len(data)))
			self.end_headers()
			self.wfile.write(data)

if __name__ == "__main__":		
	webServer = HTTPServer(("0.0.0.0", 8000), MyServer)

	try:
		webServer.serve_forever()
	except KeyboardInterrupt:
		pass

	webServer.server_close()
	print("Server stopped.")

from http.server import BaseHTTPRequestHandler, HTTPServer
from html.parser import HTMLParser
from pathlib import Path
import json

ARCHIVE_DIR = "/home/dragon/Development/Scripts/archive"

def getNoProto(url):
	return url.replace("https://", "").replace("http://", "")

def getHost(url):
	return getNoProto(url).split("/")[0]

def getPath(url):
	url = getNoProto(url)
	return url[url.index("/"):]

def getClosestHashFromMap(m, url):
	url = getNoProto(url)
	
	for x in m:
		if (getNoProto(x["url"]) == url):
			return x["content"]
	
	return None

def dictToHtmlTags(d):
	o = ""
	
	for k in d:
		o += f"{k}=\""
		o += d[k].replace("\"", "&quot;").replace("&", "&amp;")
		o += "\" "
	
	return o[:-1]

class HTMLModifier(HTMLParser):
	def __init__(self, m, url):
		super().__init__()
		self.url = url
		self.out = ""
	
	def handle_starttag(self, tag, attrs):
		attrs = dict(attrs)
		self.out += f"<{tag} {dictToHtmlTags(attrs)}>"
	
	def handle_endtag(self, tag):
		self.out += f"</{tag}>"
	
	def handle_data(self, data):
		self.out += data

class MyServer(BaseHTTPRequestHandler):
	def do_GET(self):
		url = self.path[1:]
		
		m = json.loads(Path(f"{ARCHIVE_DIR}/{getHost(url)}/map.json").read_text())
		
		hp = HTMLModifier(m, url)
		hp.feed(Path(f"{ARCHIVE_DIR}/{getHost(url)}/{getClosestHashFromMap(m, url)}").read_text())
		
		data = hp.out
		
		self.send_response(200)
		self.send_header("Content-Type", "text/html")
		self.send_header("Content-Length", str(len(data)))
		self.end_headers()
		self.wfile.write(data.encode())

if __name__ == "__main__":		
	webServer = HTTPServer(("0.0.0.0", 8000), MyServer)

	try:
		webServer.serve_forever()
	except KeyboardInterrupt:
		pass

	webServer.server_close()
	print("Server stopped.")

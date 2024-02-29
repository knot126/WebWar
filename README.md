# WebWar Archiver

Proof of concept web archival tool which uses proxies to save data from many domains. Since it relies on the browser and the user's interaction with it, some data can be saved that would not be saved with a normal crawler or single-site "proxy".

Right now I'm just cheap and using mitmproxy for the heavy lifting. B3

## Usage

### Archival

1. Edit `mitm_archive_http.py` and change the `DB` to where you want to save stuff
2. Run `mitmproxy` with `--script` set as the path to `mitm_archive_http.py`
3. Set up your web browser to use the proxy (probably `127.0.0.1` port `8080`)
4. Browse around to save your shit :3

### Browsing

I wrote some really shitty browser that can read back the saved files. Edit the path in there to point to your DB and then `python ./netwar_browser.py` :)

You can then visit sites like `http://localhost:8000/https://furaffinity.net/user/knot126`.

Note that you need to get the page name exactly right (ex `www.furaffinity.net` != `furaffinity.net` and `example.com/` != `example.com` - will have some way to correct this later).

## Format

The archive "database" is a simple content addressed storage system, sorted per domain, with a `map.json` file mapping URIs and time of archival to content and headers.

### `map.json`

`map.json` is a simple array of objects with the following properties:

* `url`: URL for this capture
* `time`: UNIX timestamp of the capture
* `content`: Hash of the saved contents
* `headers`: Hash of the response headers (should be optional but currently required for browser)

### Example

```
<archive root>
	/www.furaffinity.net
		/f0e4c2f76c58916ec258f246851bea091d14d4247a2fc3e18694461b1816e13b
		/13954213a197701957f334ace6845c1ebcd0a329053c790a8b31c47bc18c83de
		/b0eb9b2e16cd79eb4471af9f7d34de90b69d79b5de4177604e0109f82a83bc54
		/ ...
		/map.json
	/example.com
		/a379a6f6eeafb9a55e378c118034e2751e682fab9f2d30ab13d2125586ce1947
		/0efb0ab6e3a4e54c1a3ed2633c8a542125a9945498ae491dfb5d15d9648342d1
		/map.json
```

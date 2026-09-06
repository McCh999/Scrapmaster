from http.server import BaseHTTPRequestHandler
from urllib import parse
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse.parse_qs(parse.urlparse(self.path).query)
        subreddit = query.get("subreddit", ["Thailand"])[0]
        search_query = query.get("q", ["visa"])[0]

        result = {"subreddit": subreddit, "query": search_query}

        try:
            from scrapling.fetchers import Fetcher

            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            page = Fetcher.get(
                url,
                params={
                    "q": search_query,
                    "restrict_sr": "1",
                    "sort": "new",
                    "limit": "10",
                    "t": "week",
                },
                impersonate="chrome",
                stealthy_headers=True,
            )

            result["status"] = page.status

            if page.status == 200:
                data = json.loads(page.body)
                posts = data.get("data", {}).get("children", [])
                result["found"] = len(posts)
                result["titles"] = [p["data"]["title"] for p in posts[:5]]
            else:
                result["found"] = 0
                result["note"] = "Non-200 response from Reddit"
                result["body_preview"] = page.body[:300] if page.body else None

        except Exception as e:
            result["error"] = str(e)
            result["error_type"] = type(e).__name__

        body = json.dumps(result, indent=2).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(body)
        return

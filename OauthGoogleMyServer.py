from http.server import SimpleHTTPRequestHandler, HTTPServer
import sqlite3 as sl
from urllib.parse import urlencode, urlparse, parse_qs
import requests
import json

client_id = "1097035583322-.apps.googleusercontent.com" #din client id
client_secret = "GOCSPX-nemF-" #din secret
redirect_uri = "http://localhost:8080/callback"
base_url = "https://accounts.google.com/o/oauth2/"
authorization_code = ""
access_token = ""
scope="https://www.googleapis.com/auth/userinfo.email"

hostName = "localhost"
serverPort = 8080

#database file is created first time you execute create_db()
con = sl.connect('my-test.db')
#make sure that results from SQL queries are of a string format
con.text_factory = str


class MyServer(SimpleHTTPRequestHandler):

#the first page shown is index.html with login form
    def do_GET(self):
        if self.path == "/":
            url = "https://accounts.google.com/o/oauth2/auth?client_id={0}&redirect_uri={1}&scope={2}&response_type=code".format(client_id, redirect_uri, scope)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html_anchor="<html><head><title>OAuth Login</title></head><body><a href='" + str(url) + "'>login here</a></body></html>"
            self.wfile.write(bytes(html_anchor, "utf-8"))


        if "callback" in self.path:

            url = urlparse(self.path)
            query = parse_qs(url.query)
            authorization_code = query.get('code')
            access_token_req = {
                "code": authorization_code.pop(0),
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }

            content_length = len(urlencode(access_token_req))
            access_token_req['content-length'] = str(content_length)

            r = requests.post(base_url + "token", data=access_token_req)
            data = json.loads(r.text)
            print(r.text)
            access_token = data['access_token']
            authorization_header = {"Authorization": "OAuth %s" % access_token}
            r = requests.get("https://www.googleapis.com/oauth2/v2/userinfo",
                         headers=authorization_header)

            print (r.text)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(r.text, "utf-8"))

if __name__ == "__main__":

    webServer = HTTPServer((hostName, serverPort), MyServer)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
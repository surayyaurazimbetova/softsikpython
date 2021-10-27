import urllib
from http.server import SimpleHTTPRequestHandler, HTTPServer
import sqlite3 as sl
from urllib.parse import parse_qs, unquote_plus
from random import randint

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
            self.path = "index.html"
            return SimpleHTTPRequestHandler.do_GET(self)

# if user presses send in the login form then redirect is made to listUsers
        if 'listUsers' in self.path:
            self.cookie = None
         #   self.path = self.path + "listUsers"
            # extract query parameters from URL request
            user = ""
            password = ""
            path = self.path
            if '?' in path:
                path, tmp = path.split('?', 1)
                qs = parse_qs(tmp)
                print(tmp)
                user = str(qs.get('usr')[0])
                password = str(qs.get('pwd')[0])

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            #make sure only users that exist in the table can see whole table
            userExist = findUser(password, user)

            #show DB contents as html tags if we know the user


            if userExist:
                sid = self.generate_sid()
                self.cookie = "sid={}".format(sid)
                self.send_header('Set-Cookie', self.cookie + "; Path = /; HTTPOnly=true"+ "; Secure=true" + "; SameSite=none")
                self.end_headers()

                self.wfile.write(bytes("<html><head><title>Software Sikkerhed 2021</title></head>", "utf-8"))
                self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
                with con:
                    data = con.execute("SELECT * FROM USER")
                    html_part = '<table>'
                    self.wfile.write(bytes("<p>You have permission to see the Users table:</p>", "utf-8"))
                    for t in data:
                        html_part = html_part + '<tr><td>' + str(t) + '</td></tr>'
                    html_part = html_part + '</table><form action="comments_path" method = "POST">' +\
                                '<textarea name="commnts" rows="10" cols="30">... </textarea><input type = "submit" value = "Submit" /></form>'
                    self.wfile.write(bytes(html_part, "utf-8"))
                    self.wfile.write(bytes("<body>", "utf-8"))
                    self.wfile.write(bytes("</body></html>", "utf-8"))
            else:
                # Non existing user is not allowed to vew DB contents
                self.end_headers()
                self.wfile.write(bytes("<html><title>Permission failed</title><body><p>You do not have permission to see the Users table:</p></body></html>", "utf-8"))

            return


    def parse_cookies(self, cookie_list):
        return dict(((c.split("=")) for c in cookie_list.split(";"))) if cookie_list else {}

    def do_POST(self):
        if 'comments_path' in self.path:
            cookies = self.parse_cookies(self.headers["Cookie"])
            knownUser = False
            if "sid" in cookies:
                knownUser = cookies["sid"] != None

            if knownUser:
                content_length = int(self.headers['Content-Length'])  # <--- Gets the size of data
                post_data = self.rfile.read(content_length)  # <--- Gets the data itself
                decoded_body = post_data.decode('utf-8')
                print(post_data.decode('utf-8'))
                path, comment = decoded_body.split('=', 1)
                decoded_comment = unquote_plus(str(comment))
                #print(str(comment))
                with con:
                    con.execute("INSERT INTO COMMENTS (comment) VALUES ('" + decoded_comment + "');")

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes("<html><head><title>Software Sikkerhed 2021</title></head>", "utf-8"))
                self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))

                with con:
                    data = con.execute("SELECT * FROM COMMENTS")
                    html_part = '<table>'
                    for t in data:
                        html_part = html_part + '<tr><td>' + str(t) + '</td></tr>'
                    html_part = html_part + '</table>'
                    self.wfile.write(bytes(html_part, "utf-8"))
                    self.wfile.write(bytes("<body>", "utf-8"))
                    self.wfile.write(bytes("</body></html>", "utf-8"))
            else:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes("<html><head><title>You are not logged in</title></head>", "utf-8"))
                self.wfile.write(bytes("<body><p>You are not logged in</p></body></html>", "utf-8"))

    def generate_sid(self):
        return "".join(str(randint(1, 2)) for _ in range(10))


def findUser(password, user):
    with con:
        data = con.execute("SELECT * FROM USER WHERE username like '" + user + "' and password like '" + password + "'")
        if data.fetchone() != None:
            return 1
    return 0


# script should be called once for creating database, tables and populating the table
def create_db():
    global data
    with con:
        con.execute("""
            CREATE TABLE USER (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT);
        """)
        con.execute("""
                   CREATE TABLE COMMENTS (
                       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                       comment TEXT); """)
    sql = 'INSERT INTO COMMENTS (id, comment) values(?, ?)'
    data = [
        (1, 'hi admin har lige skrevet kommentar'),
        (2, 'hey hey hey'),
        (3, 'Hello world !')
    ]
    with con:
        con.executemany(sql, data)

    sql = 'INSERT INTO USER (id, username, password) values(?, ?, ?)'
    data = [
        (1, 'admin', 'admin'),
        (2, 'Bob', '1234'),
        (3, 'Chris', '1234')
    ]
    with con:
        con.executemany(sql, data)


if __name__ == "__main__":

    webServer = HTTPServer((hostName, serverPort), MyServer)
   # create_db()
    # #uncomment the code if you run it for the first time

    print("Server started and can be accessed from http://%s:%s" % (hostName, serverPort))
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
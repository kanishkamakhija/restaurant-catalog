from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi


from database_setup import Base, Restaurant, MenuItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship

#create session and connect to database
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()



class webserverHandler(BaseHTTPRequestHandler):
    #handles all the request that the server receives
    def do_GET(self):
        try:
            if self.path.endswith("/restaurants"):
                restaurants = session.query(Restaurant).all()
                output += ""
                output += "<a href = '/restaurants/new'> Make a New Restaurant Here </a></br></br>"
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>"
                for restaurant in restaurants:
                    output += restaurant.name
                    output += "</br>"
                    output += "<a href = '/restaurants/%s/edit'>Edit</a>" % restaurant_id
                    output += "</br>"
                    output += "<a href = '/restaurants/%s/delete'>Delete</a>"

                output += "</body></html>"
                self.wfile.write(output)
                return

            if self.path.endswith("/edit"):
                restaurantIDPath = self.path.split("/")[2]
                myRestaurantQuery = session.query(Restaurant).filter_by(id = restaurantIDPath).one()

                if myRestaurantQuery != []:
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        output += "<html><body>"
                        output += "<h1>"
                        output += "<form method='POST' enctype='multipart/form-data' action='/restaurants/%s/edit'>" % restaurantIDPath
                        output += "<input name = 'newRestaurantName' type = 'text' placeholder =  'New Restaurant Name'>"
                        output += "<input type = 'Submit' value = 'Rename'>"
                        output += "</form>"
                        output += "</body></html>"

                        self.wfile.write(output)

            if self.path.endswith("/delete"):
                restaurantIDPath = self.path.split("/")[2]
                myRestaurantQuery = session.query(Restaurant).filter_by(id = restaurantIDPath).one()

                if myRestaurantQuery != []:
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        output += ""
                        output += "<html><body>"
                        output += "<h1>Confirm the deletion of %s" % myRestaurantQuery.name
                        output += "<form method='POST' enctype='multipart/form-data' action='/restaurants/%s/edit'>" % restaurantIDPath
                        output += "<input name = 'newRestaurantName' type = 'text' placeholder =  'New Restaurant Name'>"
                        output += "<input type = 'Submit' value = 'Delete'>"
                        output += "</form>"
                        output += "</body></html>"

                        self.wfile.write(output)


            if self.path.endswith("/restaurants/new"):
                restaurants = session.query(Restaurant).all()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>"
                output += "<h1>Make a new Restaurant</h1>"
                output += "<form method = 'POST' enctype = 'multipart/form-data' action = '/restaurants/new'>"
                output += "<input name = 'newRestaurantName' type = 'text' placeholder =  'New Restaurant Name'>"
                output += "<input type = 'Submit' value = 'Create'>"
                output += "</body></html>"
                self.wfile.write(output)
                return

            if self.path.endswith("/hello"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html') #specifies that we are responding to our client in html
                self.end_headers()

                output = ""
                output += "<html><body>"
                output += "Hello!"
                output += "<form method='POST' enctype='multipart/form-data' action='/hello'><h2>What would you like me to say?<h2><input name='message' type='text'><input type='Submit'></form>"
                output += "</body></html>"
                self.wfile.write(output) #send message back to the client
                print output #to see output in terminal for debugging
                return

            if self.path.endswith("/hola"):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>&#161Hola <a href = '/hello'>Back in hello</a></body></html>"
                self.wfile.write(output)
                print output
                return

        except IOError:
            self.send_error(404, "File not found %s" % self.path)

    def do_POST(self):
        try:
            if self.path.endswith("/delete"):
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                restaurantIDPath = self.path.split("/")[2]
                myRestaurantQuery = session.query(Restaurant).filter_by(id = restaurantIDPath).one()

                if myRestaurantQuery != []:
                    session.delete(myRestaurantQuery)
                    session.commit()
                    self.send_response(301)
                    self.send_header('Content-Type', 'text/html')
                    self.send_header('Location', '/restaurants')
                    self.end_headers()



            if self.path.endswith("/edit"):
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                messagecontent = fields.get('newRestaurantName') #to get the content of a particular field
                restaurantIDPath = self.path.split("/")[2]

                myRestaurantQuery = session.query(Restaurant).filter_by(id = restaurantIDPath).one()
                if myRestaurantQuery != []:
                    myRestaurantQuery.name = messagecontent[0]
                    session.add(myRestaurantQuery)
                    session.commit()
                    self.send_response(301)
                    self.send_header('Content-Type', 'text/html')
                    self.send_header('Location', '/restaurants')
                    self.end_headers()

            if self.path.endswith("/restaurants/new"):
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict) #to grab the inputs from a form
                    messagecontent = fields.get('newRestaurantName') #to get the content of a particular field

                #creeate a new restaurant class
                newRestaurant = Restaurant(name = messagecontent[0])
                session.add(newRestaurant)
                session.commit()

                self.send_response(301)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Location', '/restaurants')
                self.end_headers()

        #     self.send_response(301)
        #     self.end_headers()
        #
        #     ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        #     if ctype == 'multipart/form-data':
        #         fields = cgi.parse_multipart(self.rfile, pdict)
        #         messagecontent = fields.get('message')
        #
        #         output = ""
        #         output += "<html><body>"
        #         output += "<h2> Okay, how about this:</h2>"
        #         output += "<h1> %s </h1>" % messagecontent[0]
        #
        #         output += "<form method='POST' enctype='multipart/form-data' action='/hello'><h2>What would you like me to say?<h2><input name='message' type='text'><input type='Submit'></form>"
        #         output += "</body></html>"
        #         self.wfile.write(output)
        #         print output
        #
        except:
            pass

def main():
    try:
        port = 8080
        server = HTTPServer(('',port), webserverHandler) #creating a webserver
        print("web server running on port %s" % port)
        server.serve_forever() #constantly listen untic ^c is pressed

    except KeyboardInterrupt:
        print("^C entered, stopping web server...")
        server.socket.close()


if __name__ == '__main__':
    main()

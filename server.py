import sys; 
import cgi; 

from http.server import HTTPServer, BaseHTTPRequestHandler;
from urllib.parse import urlparse, parse_qsl;

import os
import math
import json
import Physics
import eightball

games = {}
nextGameID = 1

STATIC_FILES = {
    "/": ( "game.html", "text/html; charset=utf-8" ),
    "/play.html": ( "play.html", "text/html; charset=utf-8" ),
    "/theme.css": ( "theme.css", "text/css; charset=utf-8" ),
    "/balls.js": ( "balls.js", "text/javascript; charset=utf-8" ),
}
MAX_NAME_LENGTH = 20

class MyHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):

        # parse the URL to get the path and form data
        parsed  = urlparse( self.path ); 
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
             
                
        if parsed.path in STATIC_FILES:
            fileName, contentType = STATIC_FILES[ parsed.path ];
            with open( fileName, "rb" ) as fp:
                content = fp.read();
            self.send_response( 200 );
            self.send_header( "Content-type", contentType );
            self.send_header( "Content-length", len( content ) );
            self.end_headers();
            self.wfile.write( content );

        elif parsed.path in [ "/state" ]:
            game = games.get( int( dict( parse_qsl( parsed.query ) ).get( "game", 0 ) ) );
            if game is None:
                self.errorMsg();
            else:
                self.sendJSON( game.state() );

########################################### GAME.HTML
        elif parsed.path in [ "/game.html" ]:

            try:

                # retreive the HTML file
                fp = open( '.'+self.path );
                content = fp.read();

                # generate the headers
                self.send_response( 200 ); 
                self.send_header( "Content-type", "text/html" );
                self.send_header( "Content-length", len( content ) );
                self.end_headers();

                # send it to the broswer
                self.wfile.write( bytes( content, "utf-8" ) );
                fp.close();
            
            except FileNotFoundError:
                self.errorMsg()























########################################### SHOOT.HTML 
        # check if the web-pages matches
        # if parsed.path in [ "/shoot.html" ]:

        #     try:

        #         # retreive the HTML file
        #         fp = open( '.'+self.path );
        #         content = fp.read();

        #         # generate the headers
        #         self.send_response( 200 ); 
        #         self.send_header( "Content-type", "text/html" );
        #         self.send_header( "Content-length", len( content ) );
        #         self.end_headers();

        #         # send it to the broswer
        #         self.wfile.write( bytes( content, "utf-8" ) );
        #         fp.close();
            
        #     except FileNotFoundError:
        #         self.errorMsg()












########################################### SVG IMAGES
        # check if the web-pages matches 
        elif parsed.path.endswith(".svg"):
            
            file_path = parsed.path.lstrip("/") 

            # retreive the JPG file (binary, not text file)
            fp = open( '.'+self.path, 'rb' );
            content = fp.read();

            try:
                            
                with open(file_path, 'r') as file:  
                    content = file.read()
                    self.send_response(200)
                    self.send_header("Content-type", "image/svg+xml")
                    self.end_headers()
                    self.wfile.write(bytes(content, "utf-8"))  
            
            except FileNotFoundError:
                self.errorMsg()
            
        else:
            self.errorMsg()

    def errorMsg(self):
            self.send_response( 404 );
            self.end_headers();
            self.wfile.write( bytes( "404: not found", "utf-8" ) );


























    def sendJSON(self, data, status=200):
        content = bytes( json.dumps( data ), "utf-8" );
        self.send_response( status );
        self.send_header( "Content-type", "application/json" );
        self.send_header( "Content-length", len( content ) );
        self.end_headers();
        self.wfile.write( content );

    def do_POST(self):

        # parse the URL to get the path and form data
        parsed  = urlparse( self.path );

        if parsed.path == '/shoot':
            body = json.loads( self.rfile.read( int( self.headers['Content-Length'] ) ) );
            game = games.get( int( body['game'] ) );
            if game is None:
                self.errorMsg();
                return;
            try:
                frames, pocketed = game.shoot( float( body['vx'] ), float( body['vy'] ) );
            except ValueError as error:
                self.sendJSON( { "error": str( error ) }, 400 );
                return;
            self.sendJSON( { "frames": frames, "pocketed": pocketed, "state": game.state() } );
            return;

        # get data send as Multipart FormData (MIME format)
        form = cgi.FieldStorage( fp=self.rfile,
                                    headers=self.headers,
                                    environ = { 'REQUEST_METHOD': 'POST',
                                                'CONTENT_TYPE': 
                                                self.headers['Content-Type'],
                                            } 
                                );





















########################################## DISPLAY.HTML
        # 1) Receive the form data supplied from shoot.html page.
        if parsed.path in [ '/display.html' ]:
            
            stillBallNum = int(form.getvalue('sb_number'))
            stillBallX = float(form.getvalue('sb_x'))
            stillBallY = float(form.getvalue('sb_y'))
            rollingBallNum = int(form.getvalue('rb_number'))
            rollingBallPosX = float(form.getvalue('rb_x'))
            rollingBallPosY = float(form.getvalue('rb_y'))
            rollingBallVelX = float(form.getvalue('rb_dx'))
            rollingBallVelY = float(form.getvalue('rb_dy'))

            # 2) Delete all table-?.svg files in the server’s directory.
            for filename in os.listdir('.'):
                if filename.startswith("table-") and filename.endswith(".svg"):
                    os.remove(filename)
                    
            # 3) Compute the acceleration on the RollingBall, the same way that you did at the end
            # of the PHYLIB_ROLLING_BALL case of the phylib_bounce function. Do this calculation
            # in Python.
            rollingBallVel = Physics.Coordinate(float(rollingBallVelX), float(rollingBallVelY))
            speedA = Physics.phylib.phylib_length(rollingBallVel);
            
            AccX = 0.0
            AccY = 0.0

            if speedA > Physics.VEL_EPSILON:
                AccX = (-rollingBallVel.x / speedA) * Physics.DRAG
                AccY = (-rollingBallVel.y / speedA) * Physics.DRAG

            acc = Physics.Coordinate(AccX, AccY)

            # 4) Construct a Table and add the Balls like you did in A2Test2.py according to the form
            # data received.
            # Call the Physics.Table constructor and store the result in a variable table
            table = Physics.Table()

            # Call the Physics.Coordinate constructor and store the result in a variable pos.
            pos = Physics.Coordinate(stillBallX, stillBallY)

            # Call the StillBall constructor and store the result in a variable sb
            sb = Physics.StillBall(stillBallNum, pos)

            # Call the Coordinate constructor 3 times to set the variables, pos, vel, and acc for the
            # RollingBall
            pos = Physics.Coordinate(rollingBallPosX, rollingBallPosY)
            vel = Physics.Coordinate(rollingBallVelX, rollingBallVelY)

            # Call the RollingBall constructor and store the result in a variable rb
            rb = Physics.RollingBall(rollingBallNum, pos, vel, acc)

            # Add the StillBall to the table using “ table += sb”
            table += sb

            # Add the RollingBall to the table using “ table += rb”
            table += rb
            
            index=0;

            # 5) Save the table-?.svg files that are generated in the same directory as the server.
            # Start a while loop conditioned on the value of table (it will run until table is None)
            while table is not None:
                
                # instead of printing the
                # table, opens a file called "table-%d.svg" with an index that starts at 0 and increments by 1
                # substituted for %d. I.e. the first file opened should be "table-0.svg". And, write the string
                # returned by the svg method of the table to the file 
                fileName="table-%d.svg" % index   
                with open(fileName, 'w') as file:
                    if table != None:
                        file.write(table.svg())
                index += 1
                
                # Inside the while loop set the value of table to be the return value of calling
                # the segment method of table.
                table = table.segment()
            
            # 6) Generate a string containing a “nice” HTML web-page, that describes the original Ball
            # positions and velocities. Add one <img> tag to the web-page for each svg file that
            # exists in the directory. Set the src attribute of the <img> tag to load the svg file into
            # the page (using GET requests). Include a “ Back” link on the form that takes you back to
            # the “/shoot.html” page.
            content = f"""
            <html>
            <head>
                <title> CIS*2750 A2 </title>
            </head>
            <body>
                <h1> Still and Rolling Ball Results and Table Images\n </h1>
                <p> 
                stillBallNum = {stillBallNum}
                </p>
                <p>
                stillBallX = {stillBallX}
                </p>
                <p>
                stillBallY = {stillBallY}
                </p>
                <p>
                rollingBallNum = {rollingBallNum}
                </p>
                <p>
                rollingBallPosX = {rollingBallPosX}
                </p>
                <p>
                rollingBallPosY = {rollingBallPosY}
                </p>
                <p>
                rollingBallVelX = {rollingBallVelX}
                </p>
                <p>
                rollingBallVelY = {rollingBallVelY}
                </p>
                <p>
                rollingBallAccX: {acc.x}
                </p>
                <p>
                rollingBallAccY: {acc.y}
                </p>
                
            </body>
            </html>
            """;   
            
            for index, filename in enumerate(sorted(os.listdir('.'))):
                if filename.startswith("table-") and filename.endswith(".svg"):
                    content += '<img src="/%s" alt="Result %d"/><br>\n' % (filename, index)

            # content += '<a href="/shoot.html">Back</a></body></html>'
            
            # 7) Send the string back to the browser, with a 200 response.
            # generate the headers
            self.send_response( 200 ); # OK
            self.send_header( "Content-type", "text/html" );
            self.send_header( "Content-length", len( content ) );
            self.end_headers();

            # send it to the browser
            self.wfile.write( bytes( content, "utf-8" ) );


            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        if parsed.path in [ '/new.html' ]:
            global nextGameID
            p1Name = ( form.getvalue('player1_name') or "" ).strip();
            p2Name = ( form.getvalue('player2_name') or "" ).strip();
            if not p1Name or not p2Name:
                self.sendJSON( { "error": "Both players need a name." }, 400 );
                return;
            if len( p1Name ) > MAX_NAME_LENGTH or len( p2Name ) > MAX_NAME_LENGTH:
                self.sendJSON( { "error": "Names can be at most %d characters." % MAX_NAME_LENGTH }, 400 );
                return;
            if p1Name.lower() == p2Name.lower():
                self.sendJSON( { "error": "That name is taken, pick another." }, 409 );
                return;
            gameName = ( form.getvalue('game_name') or "" ).strip() or "%s vs %s" % ( p1Name, p2Name );
            game = eightball.EightBallGame(nextGameID, gameName, p1Name, p2Name)
            games[nextGameID] = game
            nextGameID += 1

            self.send_response( 303 );
            self.send_header( "Location", "/play.html?game=%d" % game.id );
            self.end_headers();

        elif parsed.path in [ '/display2.html' ]:
            
            # stillBallNum = int(form.getvalue('sb_number'))
            # stillBallX = float(form.getvalue('sb_x'))
            # stillBallY = float(form.getvalue('sb_y'))
            rollingBallNum = int(form.getvalue('rb_number'))
            rollingBallPosX = float(form.getvalue('rb_x'))
            rollingBallPosY = float(form.getvalue('rb_y'))
            rollingBallVelX = float(form.getvalue('rb_dx'))
            rollingBallVelY = float(form.getvalue('rb_dy'))

            # 2) Delete all table-?.svg files in the server’s directory.
            for filename in os.listdir('.'):
                if filename.startswith("table-") and filename.endswith(".svg"):
                    os.remove(filename)
                    
            # 3) Compute the acceleration on the RollingBall, the same way that you did at the end
            # of the PHYLIB_ROLLING_BALL case of the phylib_bounce function. Do this calculation
            # in Python.
            rollingBallVel = Physics.Coordinate(float(rollingBallVelX), float(rollingBallVelY))
            speedA = Physics.phylib.phylib_length(rollingBallVel);
            
            AccX = 0.0
            AccY = 0.0

            if speedA > Physics.VEL_EPSILON:
                AccX = (-rollingBallVel.x / speedA) * Physics.DRAG
                AccY = (-rollingBallVel.y / speedA) * Physics.DRAG

            acc = Physics.Coordinate(AccX, AccY)

            # 4) Construct a Table and add the Balls like you did in A2Test2.py according to the form
            # data received.
            # Call the Physics.Table constructor and store the result in a variable table
            table = Physics.Table()




            # List of cue balls with their number and positions
            cueBalls = [
                (0, 675, 675), 
                (1, 675, 400.0), 
                (2, 645, 350.0),
                (3, 705, 350.0),
                (4, 675, 300.0), 
                (5, 615, 300.0), 
                (6, 735, 300.0),
                (7, 645, 250.0),
                (8, 705, 250.0), 
                (9, 585, 250.0), 
                (10, 765, 250.0),
                (11, 675, 200.0),
                (12, 615, 200.0), 
                (13, 735, 200.0), 
                (14, 555, 200.0),
                (15, 795, 200.0)
            ]


            # Loop through the list and add each ball to the table
            for ballNum, ballX, ballY in cueBalls:
                pos = Physics.Coordinate(ballX, ballY)  # Create position object
                sb = Physics.StillBall(ballNum, pos)  # Create StillBall object
                table += sb  # Add the StillBall to the table

            # Call the Coordinate constructor 3 times to set the variables, pos, vel, and acc for the
            # RollingBall
            pos = Physics.Coordinate(rollingBallPosX, rollingBallPosY)
            vel = Physics.Coordinate(rollingBallVelX, rollingBallVelY)

            # Call the RollingBall constructor and store the result in a variable rb
            rb = Physics.RollingBall(rollingBallNum, pos, vel, acc)

            # Add the RollingBall to the table using “ table += rb”
            table += rb
            
            index=0;
            
            # Physics.Game.shoot(gameName, "test", table, rollingBallVelX, rollingBallVelY)


            # 5) Save the table-?.svg files that are generated in the same directory as the server.
            # Start a while loop conditioned on the value of table (it will run until table is None)
            while table is not None:
                
                # instead of printing the
                # table, opens a file called "table-%d.svg" with an index that starts at 0 and increments by 1
                # substituted for %d. I.e. the first file opened should be "table-0.svg". And, write the string
                # returned by the svg method of the table to the file 
                fileName="table-%d.svg" % index   
                with open(fileName, 'w') as file:
                    if table != None:
                        file.write(table.svg())
                index += 1
                
                # Inside the while loop set the value of table to be the return value of calling
                # the segment method of table.
                table = table.segment()
            totalTables = index
            
            # 6) Generate a string containing a “nice” HTML web-page, that describes the original Ball
            # positions and velocities. Add one <img> tag to the web-page for each svg file that
            # exists in the directory. Set the src attribute of the <img> tag to load the svg file into
            # the page (using GET requests). Include a “ Back” link on the form that takes you back to
            # the “/shoot.html” page.
            content = f"""
            <html>
            <head>
                <title> CIS*2750 A2 </title>
            </head>
            <body>
                <p>
                rollingBallNum = {rollingBallNum}
                </p>
                <p>
                rollingBallPosX = {rollingBallPosX}
                </p>
                <p>
                rollingBallPosY = {rollingBallPosY}
                </p>
                <p>
                rollingBallVelX = {rollingBallVelX}
                </p>
                <p>
                rollingBallVelY = {rollingBallVelY}
                </p>
                <p>
                rollingBallAccX: {acc.x}
                </p>
                <p>
                rollingBallAccY: {acc.y}
                </p>
                
            </body>
            </html>
            """;   
            
            for index, filename in enumerate(sorted(os.listdir('.'))):
                if filename.startswith("table-") and filename.endswith(".svg"):
                    content += '<img src="/%s" alt="Result %d"/><br>\n' % (filename, index)


            content = f"""
            <html>
            <head>
                <title> CIS*2750 A2 </title>
                <script>
                    var currentTableIndex = 0;
                    var totalTables = {totalTables};
                    function changeImage() {{
                        var imgSrc = 'table-' + currentTableIndex + '.svg';
                        document.getElementById('tableImage').setAttribute('src', imgSrc);
                        currentTableIndex = (currentTableIndex + 1) % totalTables;
                    }}
                    setInterval(changeImage, 1000);
                </script>
            </head>
            <body>
                <h1>Still and Rolling Ball Results and Table Images</h1>
                <img id="tableImage" src="table-0.svg" alt="Table Image"/><br>
                <a href="/shoot.html">Back</a>
            </body>
            </html>
            """
            
            # 7) Send the string back to the browser, with a 200 response.
            # generate the headers
            self.send_response( 200 ); # OK
            self.send_header( "Content-type", "text/html" );
            self.send_header( "Content-length", len( content ) );
            self.end_headers();

            # send it to the browser
            self.wfile.write( bytes( content, "utf-8" ) );

        else:
            self.errorMsg()

            

if __name__ == "__main__":
    httpd = HTTPServer( ( 'localhost', int(sys.argv[1]) ), MyHandler );
    print( "Server listing in port:  ", int(sys.argv[1]) );
    httpd.serve_forever();

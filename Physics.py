import phylib
import os
import sqlite3
import math

################################################################################
# import constants from phylib to global varaibles
BALL_RADIUS = phylib.PHYLIB_BALL_RADIUS
BALL_DIAMETER = phylib.PHYLIB_BALL_DIAMETER
HOLE_RADIUS = phylib.PHYLIB_HOLE_RADIUS
TABLE_LENGTH = phylib.PHYLIB_TABLE_LENGTH
TABLE_WIDTH = phylib.PHYLIB_TABLE_WIDTH
SIM_RATE = phylib.PHYLIB_SIM_RATE
VEL_EPSILON = phylib.PHYLIB_VEL_EPSILON
DRAG = phylib.PHYLIB_DRAG
MAX_TIME = phylib.PHYLIB_MAX_TIME
MAX_OBJECTS = phylib.PHYLIB_MAX_OBJECTS
FRAME_RATE = 0.01

HEADER = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="700" height="1375" viewBox="-25 -25 1400 2750"
xmlns="http://www.w3.org/2000/svg"
xmlns:xlink="http://www.w3.org/1999/xlink">
<rect width="1350" height="2700" x="0" y="0" fill="#C0D0C0" />"""
FOOTER = """</svg>\n"""

################################################################################
# the standard colours of pool balls
# if you are curious check this out:
# https://billiards.colostate.edu/faq/ball/colors/

BALL_COLOURS = [
    "WHITE",
    "YELLOW",
    "BLUE",
    "RED",
    "PURPLE",
    "ORANGE",
    "GREEN",
    "BROWN",
    "BLACK",
    "LIGHTYELLOW",
    "LIGHTBLUE",
    "PINK",             # no LIGHTRED
    "MEDIUMPURPLE",     # no LIGHTPURPLE
    "LIGHTSALMON",      # no LIGHTORANGE
    "LIGHTGREEN",
    "SANDYBROWN",       # no LIGHTBROWN
]

################################################################################


class Coordinate(phylib.phylib_coord):
    """
    This creates a Coordinate subclass, that adds nothing new, but looks
    more like a nice Python class.
    """
    pass

################################################################################


class StillBall(phylib.phylib_object):
    """
    Python StillBall class.
    """

    def __init__(self, number, pos):
        """
        Constructor function. Requires ball number and position (x,y) as
        arguments.
        """

        # this creates a generic phylib_object
        phylib.phylib_object.__init__(self,
                                      phylib.PHYLIB_STILL_BALL,
                                      number,
                                      pos, None, None,
                                      0.0, 0.0)

        # this converts the phylib_object into a StillBall class
        self.obj.still_ball.number = number
        self.obj.still_ball.pos = pos
        self.__class__ = StillBall

    # StillBall:
    def svg(self):
        """
        where cx and cy are the pos of the Ball, r is the BALL_RADIUS, and fill is the
        appropriate value from BALL_COLOURS.
        """
        return """ <circle cx="%d" cy="%d" r="%d" fill="%s" />\n""" % (
            float(self.obj.still_ball.pos.x),
            float(self.obj.still_ball.pos.y),
            BALL_RADIUS,
            BALL_COLOURS[self.obj.still_ball.number]
        )

################################################################################


class RollingBall(phylib.phylib_object):
    """
    Python RollingBall class.
    """

    def __init__(self, number, pos, vel, acc):
        """
        Constructor function. Requires ball number and position (x,y) as
        arguments.
        """

        # this creates a generic phylib_object
        phylib.phylib_object.__init__(self,
                                      phylib.PHYLIB_ROLLING_BALL,
                                      number,
                                      pos, vel, acc,
                                      0.0, 0.0)

        # this converts the phylib_object into a RollingBall class
        self.obj.rolling_ball.number = number
        self.obj.rolling_ball.pos = pos
        self.obj.rolling_ball.vel = vel
        self.obj.rolling_ball.acc = acc
        self.__class__ = RollingBall

    # RollingBall:
    def svg(self):
        """
        where cx and cy are the pos of the Ball, r is the BALL_RADIUS, and fill is the
        appropriate value from BALL_COLOURS.
        """
        return """ <circle cx="%d" cy="%d" r="%d" fill="%s" />\n""" % (
            float(self.obj.rolling_ball.pos.x),
            float(self.obj.rolling_ball.pos.y),
            BALL_RADIUS,
            BALL_COLOURS[self.obj.rolling_ball.number]
        )

################################################################################


class Hole(phylib.phylib_object):
    """
    Python Hole class.
    """

    def __init__(self, pos):
        """
        Constructor function. Requires ball number and position (x,y) as
        arguments.
        """

        # this creates a generic phylib_object
        phylib.phylib_object.__init__(self,
                                      phylib.PHYLIB_HOLE,
                                      0,
                                      pos, None, None,
                                      0.0, 0.0)

        # this converts the phylib_object into a Hole class
        self.obj.hole.pos = pos
        self.__class__ = Hole

    # Hole:
    def svg(self):
        """
        where cx and cy are the pos of the Hole, and r is the HOLE_RADIUS.
        """
        return """ <circle cx="%d" cy="%d" r="%d" fill="black" />\n""" % (
            float(self.obj.hole.pos.x),
            float(self.obj.hole.pos.y),
            HOLE_RADIUS
        )

################################################################################


class HCushion(phylib.phylib_object):
    """
    Python HCushion class.
    """

    def __init__(self, y):
        """
        Constructor function. Requires ball number and position (x,y) as
        arguments.
        """

        # this creates a generic phylib_object
        phylib.phylib_object.__init__(self,
                                      phylib.PHYLIB_HCUSHION,
                                      0,
                                      None, None, None,
                                      0.0, y)

        # this converts the phylib_object into a HCushion class
        self.obj.hcushion.y = y
        self.__class__ = HCushion

    # HCushion:
    def svg(self):
        """
        where y is -25 if the cushion is at the top and y is 2700 if the cushion is at bottom.
        """
        if self.obj.hcushion.y == 0:
            self.obj.hcushion.y = -25
        else:
            self.obj.hcushion.y == 2700
        return """ <rect width="1400" height="25" x="-25" y="%d" fill="darkgreen" />\n""" % (
            float(self.obj.hcushion.y)
        )

################################################################################


class VCushion(phylib.phylib_object):
    """
    Python VCushion class.
    """

    def __init__(self, x):
        """
        Constructor function. Requires ball number and position (x,y) as
        arguments.
        """

        # this creates a generic phylib_object
        phylib.phylib_object.__init__(self,
                                      phylib.PHYLIB_VCUSHION,
                                      0,
                                      None, None, None,
                                      x, 0.0)

        # this converts the phylib_object into a VCushion class
        self.obj.vcushion.x = x
        self.__class__ = VCushion

    # VCushion:
    def svg(self):
        """
        where x is -25 if the cushion is on the left and x is 1350 if the cushion is at the right.
        """
        if self.obj.vcushion.x == 0:
            self.obj.vcushion.x = -25
        else:
            self.obj.vcushion.x == 2700
        return """ <rect width="25" height="2750" x="%d" y="-25" fill="darkgreen" />\n""" % (
            float(self.obj.vcushion.x)
        )

################################################################################


class Table(phylib.phylib_table):
    """
    Pool table class.
    """

    def __init__(self):
        """
        Table constructor method.
        This method call the phylib_table constructor and sets the current
        object index to -1.
        """
        phylib.phylib_table.__init__(self)

        self.current = -1

    def __iadd__(self, other):
        """
        += operator overloading method.
        This method allows you to write "table+=object" to add another object
        to the table.
        """
        self.add_object(other)
        return self

    def __iter__(self):
        """
        This method adds iterator support for the table.
        This allows you to write "for object in table:" to loop over all
        the objects in the table.
        """
        return self

    def __next__(self):
        """
        This provides the next object from the table in a loop.
        """
        self.current += 1  # increment the index to the next object
        if self.current < MAX_OBJECTS:   # check if there are no more objects
            return self[self.current]  # return the latest object

        # if we get there then we have gone through all the objects
        self.current = -1    # reset the index counter
        raise StopIteration  # raise StopIteration to tell for loop to stop

    def __getitem__(self, index):
        """
        This method adds item retreivel support using square brackets [ ] .
        It calls get_object (see phylib.i) to retreive a generic phylib_object
        and then sets the __class__ attribute to make the class match
        the object type.
        """
        result = self.get_object(index)
        if result == None:
            return None
        if result.type == phylib.PHYLIB_STILL_BALL:
            result.__class__ = StillBall
        if result.type == phylib.PHYLIB_ROLLING_BALL:
            result.__class__ = RollingBall
        if result.type == phylib.PHYLIB_HOLE:
            result.__class__ = Hole
        if result.type == phylib.PHYLIB_HCUSHION:
            result.__class__ = HCushion
        if result.type == phylib.PHYLIB_VCUSHION:
            result.__class__ = VCushion
        return result

    def __str__(self):
        """
        Returns a string representation of the table that matches
        the phylib_print_table function from A1Test1.c.
        """
        result = ""    # create empty string
        result += "time = %6.1f;\n" % self.time    # append time
        for i, obj in enumerate(self):  # loop over all objects and number them
            result += "  [%02d] = %s\n" % (i, obj)  # append object description
        return result  # return the string

    def segment(self):
        """
        Calls the segment method from phylib.i (which calls the phylib_segment
        functions in phylib.c.
        Sets the __class__ of the returned phylib_table object to Table
        to make it a Table object.
        """

        result = phylib.phylib_table.segment(self)
        if result:
            result.__class__ = Table
            result.current = -1
        return result

    # add svg method here
    def svg(self):
        """
        This method should create a string that consists of the concatenation of the HEADER + 
        return values of the svg method called on every object in the Table + 
        FOOTER
        """
        tableString = HEADER
        for obj in self:
            if obj:
                tableString += obj.svg()
        tableString += FOOTER
        return tableString

    def roll(self, t):
        new = Table()
        for ball in self:
            if isinstance(ball, RollingBall):
                # create4 a new ball with the same number as the old ball
                new_ball = RollingBall(ball.obj.rolling_ball.number,
                                       Coordinate(0, 0),
                                       Coordinate(0, 0),
                                       Coordinate(0, 0))
                # compute where it rolls to
                phylib.phylib_roll(new_ball, ball, t)
                # add ball to table
                new += new_ball
            if isinstance(ball, StillBall):
                # create a new ball with the same number and pos as the old ball
                new_ball = StillBall(ball.obj.still_ball.number,
                                     Coordinate(ball.obj.still_ball.pos.x,
                                                ball.obj.still_ball.pos.y))
                # add ball to table
                new += new_ball
        # return table
        return new

################################################################################


class Database ():

    def __init__(self, reset=False):

        # If reset is set to True, it should first delete the file “ phylib.db”
        # so that a fresh database is created upon connection
        if reset == True and os.path.exists('phylib.db'):
            os.remove('phylib.db')

        # This constructor should create/open a database connection to a file
        # in the local directory called “phylib.db” and store it as a class attribute.
        conn = sqlite3.connect('phylib.db')
        # connection=sqlite3

        self.db = conn

    def createDB(self):

        cur = self.db.cursor()

        # Create the database tables described above.
        # If any of the tables already exist,
        # it should leave them alone and not re-create them.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Ball (
            BALLID INTEGER PRIMARY KEY AUTOINCREMENT,
            BALLNO INTEGER NOT NULL,
            XPOS FLOAT NOT NULL,
            YPOS FLOAT NOT NULL,
            XVEL FLOAT,
            YVEL FLOAT
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS TTable(
            TABLEID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            TIME FLOAT NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS BallTable (
            BALLID INTEGER NOT NULL,
            TABLEID INTEGER NOT NULL, 
            FOREIGN KEY(BALLID) REFERENCES Ball (BALLID),
            FOREIGN KEY(TABLEID) REFERENCES TTable (TABLEID)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS Shot (
            SHOTID INTEGER PRIMARY KEY AUTOINCREMENT,
            PLAYERID INTEGER NOT NULL,
            GAMEID INTEGER NOT NULL,
            FOREIGN KEY(PLAYERID) REFERENCES Player(PLAYERID),
            FOREIGN KEY(GAMEID) REFERENCES Game(GAMEID)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS TableShot (
            TABLEID INTEGER NOT NULL,
            SHOTID INTEGER NOT NULL,
            PRIMARY KEY (TABLEID, SHOTID),
            FOREIGN KEY(TABLEID) REFERENCES TTable(TABLEID),
            FOREIGN KEY(SHOTID) REFERENCES Shot(SHOTID)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS Game (
            GAMEID INTEGER PRIMARY KEY AUTOINCREMENT,
            GAMENAME VARCHAR(64) NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS Player (
            PLAYERID INTEGER PRIMARY KEY AUTOINCREMENT,
            GAMEID INTEGER NOT NULL,
            PLAYERNAME VARCHAR(64) NOT NULL,
            FOREIGN KEY(GAMEID) REFERENCES Game(GAMEID)
        );
        """)

        # Make sure to call close on your cursor and commit on your connection
        self.db.commit()
        cur.close()

    def readTable(self, tableID):

        cur = self.db.cursor()

        # The table should have the standard holes and cushions, and have Balls
        # whose BALLIDs are in the BallTable table with a TABLEID that  is one larger than
        # (because we like to start numbering tableID at zero, but SQL likes to start
        # numbering TABLEID at 1) the method’s argument.
        newTableID = tableID+1

        # The table’s time attribute should be retrieved from the TTable SQL table.
        cur.execute(
            """SELECT TIME FROM TTable WHERE TABLEID = ?""", (newTableID,))
        tableTime = cur.fetchone()

        # If TABLEID does not exist in the BallTable table, then the method should
        # return None.
        if tableTime is None:
            self.db.commit()
            cur.close()
            return None

        table = Table()
        table.time = tableTime[0]

        # Use a single SQL SELECT statement with a JOIN clause to retrieve all the balls for
        # the given table in a single operation.
        cur.execute("""
            SELECT Ball.BALLID, Ball.BALLNO, Ball.XPOS, Ball.YPOS, Ball.XVEL, Ball.YVEL
            FROM Ball
            JOIN BallTable ON Ball.BALLID = BallTable.BALLID
            WHERE BallTable.TABLEID = ?;
            """, (newTableID,))

        # Each ball’s attributes should be retrieved
        # from the Ball table, and balls with no velocity should be instantiated as StillBalls, while
        # balls with a velocity should have their acceleration set just like in A2 and be instantiated as
        # RollingBalls.
        balls = cur.fetchall()

        for ball in balls:
            ballID, ballNO, xpos, ypos, xvel, yvel = ball

            if xvel is None and yvel is None:
                stillBall = StillBall(ballNO, Coordinate(xpos, ypos))
                table += stillBall

            else:
                rollingBallVel = Coordinate(float(xvel), float(yvel))
                speedA = phylib.phylib_length(rollingBallVel)

                AccX = 0.0
                AccY = 0.0

                if speedA > VEL_EPSILON:
                    AccX = (-rollingBallVel.x / speedA) * DRAG
                    AccY = (-rollingBallVel.y / speedA) * DRAG

                acc = Coordinate(AccX, AccY)

                if math.sqrt((float(xvel) * float(xvel)) + (float(yvel) * float(yvel))) > VEL_EPSILON:
                    rollingBall = RollingBall(ballNO, Coordinate(
                        float(xpos), float(ypos)), rollingBallVel, acc)

                else:
                    rollingBall = RollingBall(ballNO, Coordinate(
                        float(xpos), float(ypos)), rollingBallVel, Coordinate(0.0, 0.0))

                table += rollingBall

        # Make sure to call close on your cursor and commit on your connection.
        self.db.commit()
        cur.close()

        # This method should return a Table object (from A2).
        return table

    # This method stores the contents of the Table class object named table in the database, such
    # that it can be perfectly reconstructed by readTable. You can test these two methods by creating a
    # Table object (like in A3Test1.py) printing the table, writing the table, shutting down your
    # program, then starting a new program (like in A3Test2.py) where you read and print the table
    # and see if it is the same.
    def writeTable(self, table):

        cur = self.db.cursor()

        cur.execute("INSERT INTO TTable (TIME) VALUES (?)", (table.time,))

        # cur.execute("SELECT MAX(TABLEID) FROM TTable")
        # tableSelected = cur.fetchone()
        tableID = cur.lastrowid
        # if tableSelected is not None:
        #     tableID = tableSelected[0]

        for ball in table:
            if isinstance(ball, StillBall):
                cur.execute("""INSERT INTO Ball (BALLNO, XPOS, YPOS)
                            VALUES (?, ?, ?)""", (ball.obj.still_ball.number, ball.obj.still_ball.pos.x, ball.obj.still_ball.pos.y))

            elif isinstance(ball, RollingBall):
                cur.execute("""INSERT INTO Ball (BALLNO, XPOS, YPOS, XVEL, YVEL) VALUES (?, ?, ?, ?, ?)""", (ball.obj.rolling_ball.number,
                            ball.obj.rolling_ball.pos.x, ball.obj.rolling_ball.pos.y, ball.obj.rolling_ball.vel.x, ball.obj.rolling_ball.vel.y))
            else:
                continue
            # cur.execute("SELECT MAX(BALLID) FROM BALL")
            # ballID = cur.fetchone()[0]

            ballID = cur.lastrowid
            if ballID is not None:

                cur.execute("""
                    INSERT INTO BallTable (BALLID, TABLEID) 
                    VALUES (?, ?)
                """, (ballID, tableID))

        # Make sure to call close on your cursor and commit on your connection.
        self.db.commit()
        cur.close()

        # This method will return the
        # autoincremented TABLEID value minus 1 (because we like to start numbering tableID at zero,
        # but SQL likes to start numbering TABLEID at 1).
        return tableID - 1

    def close(self):

        # This method should call commit on the connection and call close on the connection.
        self.db.commit()
        self.db.close()

    # I recommend writing a helper method (e.g. getGame) in the
    # Database class. Player 1 shall be the player with the lower PLAYERID.
    def getGame(self, gameID):

        cur = self.db.cursor()

        # retreive the values of gameName, player1Name, and
        # player2Name from the Game and Player tables (use as few SELECT statements as possible and
        # use a JOIN across tables).
        cur.execute("""SELECT Game.GAMENAME, P1.PLAYERNAME as player1Name, P2.PLAYERNAME as player2Name 
            FROM Game 
            JOIN Player as P1 ON Game.GAMEID = P1.GAMEID 
            JOIN Player as P2 ON Game.GAMEID = P2.GAMEID 
            WHERE Game.GAMEID = ? AND P1.PLAYERID < P2.PLAYERID""", (gameID))
        values = cur.fetchone()

        self.db.commit()
        cur.close()
        if values is not None:
            return values
        else:
            return None

    def setGame(self, gameName, player1Name, player2Name):

        cur = self.db.cursor()

        # One new row shall be added to the Game table and two new rows to the Player table to record the
        # gameName, the player1Name, and the player2Name. The player1Name shall be added to the
        # Player table first (so that it gets the lower PLAYERID).
        cur.execute("INSERT INTO Game (GAMENAME) VALUES (?)", (gameName,))
        cur.execute("SELECT MAX(GAMEID) FROM Game")
        gameID = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO Player (GAMEID, PLAYERNAME) VALUES (?, ?)", (gameID, player1Name))
        cur.execute("SELECT MAX(PLAYERID) FROM Player")
        player1ID = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO Player (GAMEID, PLAYERNAME) VALUES (?, ?)", (gameID, player2Name))
        cur.execute("SELECT MAX(PLAYERID) FROM Player")
        player2ID = cur.fetchone()[0]

        self.db.commit()
        cur.close()
        return gameID

    # I recommend writing a
    # helper method (e.g. newShot) in the Database class. Make this method return the shotID;
    # you’ll need it later.
    def newShot(self, gameName, playerName):

        cur = self.db.cursor()

        cur.execute(
            """SELECT PLAYERID FROM Player WHERE PLAYERNAME = ?""", (playerName,))
        playerRecord = cur.fetchone()
        if playerRecord is None:
            return None
        playerID = playerRecord[0]

        cur.execute(
            """SELECT GAMEID FROM Game WHERE GAMENAME = ?""", (gameName,))
        gameRecord = cur.fetchone()
        if gameRecord is None:
            return None
        gameID = gameRecord[0]

        cur.execute(
            """INSERT INTO Shot (PLAYERID, GAMEID) VALUES (?, ?)""", (playerID, gameID))
        cur.execute("SELECT MAX(PLAYERID) FROM Shot")
        shotIDRecord = cur.fetchone()

        self.db.commit()
        cur.close()

        if shotIDRecord is None:
            return None
        shotID = shotIDRecord[0]

        return shotID

################################################################################


class Game ():

    # This class should represent a Game of billiards/pool/snooker. An object of class Game will have
    # member variables called gameID, gameName, player1Name, and player2Name and table.
    def __init__(self, gameID=None, gameName=None, player1Name=None, player2Name=None):

        databaseInstance = Database()

        # (i) with an integer gameID value, and all other arguments set to None, or
        if gameID is not None and (gameName is None and player1Name is None and player2Name is None):

            # For the first constructor version, add one to the gameID (because we number starting from 0,
            # but SQL numbers starting from 1)
            self.gameName, self.player1Name, self.player2Name = databaseInstance.getGame(
                gameID + 1)

        # (ii) with gameID=None, string values for all 3 Name arguments
        elif gameID is None and (gameName is not None and player1Name is not None and player2Name is not None):

            # For the second constructor, all 3 names shall be added as attributes to the object.
            self.gameID = databaseInstance.setGame(
                gameName, player1Name, player2Name)

        else:

            # Any other combination of arguments provided to the constructor shall raise a TypeError
            # Python Exception.
            raise TypeError("Invalid combination of arguments given.")

        self.table = None

    def shoot(self, gameName, playerName, table, xvel, yvel):

        databaseInstance = Database()
        tableInstance = Table()

        # This method of the Game class should add a new entry to the Shot table for the current game
        # and the given playerID (determined by looking up the playerName).
        shotID = databaseInstance.newShot(gameName, playerName)

        # Then, the shoot method should find the object representing the cue ball (number 0).
        # cueBall = table.cueBall(xvel, yvel)

        # It should retrieve the the x and y values of the cue ball’s position, and store them in temporary
        # variables.

        for ball in table:
            if (isinstance(ball, StillBall)) and ball.obj.still_ball.number==0:

                cueBall = ball

                xpos = cueBall.obj.rolling_ball.pos.x
                ypos = cueBall.obj.rolling_ball.pos.y

                # Then it should set the type attribute of the cue ball to phylib.ROLLING_BALL.
                cueBall.type = phylib.PHYLIB_ROLLING_BALL

                # Then it should set all of the attributes of the cue ball. Hint: use the following syntax:
                # cue_ball.obj.rolling_ball.pos.x = xpos;
                # Set the position attributes to the values that you stored in the temporary variables, the
                # velocity attributes to the parameters passed to the method, and recalculate the acceleration
                # parameters (as in A1, and A2).
                cueBall.obj.rolling_ball.pos.x = xpos
                cueBall.obj.rolling_ball.pos.y = ypos
                cueBall.obj.rolling_ball.vel.x = xvel
                cueBall.obj.rolling_ball.vel.y = yvel

                rollingBallVel = Coordinate(float(xvel), float(yvel))
                speedA = phylib.phylib_length(rollingBallVel)

                AccX = 0.0
                AccY = 0.0

                if speedA > VEL_EPSILON:
                    AccX = (-rollingBallVel.x / speedA) * DRAG
                    AccY = (-rollingBallVel.y / speedA) * DRAG

                cueBall.obj.rolling_ball.acc.x = AccX
                cueBall.obj.rolling_ball.acc.y = AccY

                # Don’t forget to set the number of the cue ball to 0.
                cueBall.obj.rolling_ball.number = 0

                # segmentTable.object=RollingBall(0, Coordinate(
                # float(xpos), float(ypos)), rollingBallVel, Coordinate(AccX, AccY))

        # Next, you will repeatedly call the segment method from A2 until it returns None.
        while True:
            segmentStart = table.time

            segmentTable = table.segment()
            table=segmentTable
            if segmentTable is None:
                break
            segmentEnd = segmentTable.time

            # You will use
            # the method to determine the length of the segment (in seconds) – subtract the time at the
            # beginning of the segment from the time at the end of the segment. Divide that time by the
            # FRAME_RATE above and round it down to the nearest integer.
            segmentLength = math.floor((segmentEnd-segmentStart)/FRAME_RATE)
            
            print(segmentLength)

            # Start a loop that loops over those integers. Inside the loop, multiply the integer by the
            # FRAME_RATE and pass it to the roll method to create a new Table object for the next
            # frame.
            newTableObject = Table()
            for i in range(segmentLength):
                newTableObject = table.roll(i*FRAME_RATE)

                # Set the time of the returned table to the time of the beginning of the segment plus the time
                # that you passed to the roll method.
                newTableObject.time = segmentStart+i*FRAME_RATE

                # Save the table using writeTable to the database, and record it in the TableShot as well.
                # Repeat the process for each segment
                databaseInstance.writeTable(newTableObject)
                cur = databaseInstance.db.cursor()
                
                cur.execute("""SELECT TABLEID FROM TTABLE WHERE TIME = ?""", (newTableObject.time,))
                tableRecord = cur.fetchone()
                if tableRecord is None:
                    cur.close()
                    return None
                tableID = tableRecord[0]
                
                cur.execute("""INSERT INTO TABLESHOT (TABLEID, SHOTID) VALUES (?, ?)""", (tableID, shotID))
                databaseInstance.db.commit()
                cur.close()
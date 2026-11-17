import math
import Physics

MAX_SPEED = 5000.0  # mm/s
HEAD_SPOT = (Physics.TABLE_WIDTH / 2, Physics.TABLE_LENGTH * 3 / 4)
FOOT_SPOT = (Physics.TABLE_WIDTH / 2, Physics.TABLE_LENGTH / 4)

# Rack rows from the apex (on the foot spot) toward the far cushion, with the 8 in the
# middle and a solid and a stripe on the back corners.
RACK = [[1], [9, 2], [10, 8, 3], [11, 4, 12, 5], [6, 13, 7, 14, 15]]
RACK_COLUMN = Physics.BALL_DIAMETER + 1
RACK_ROW = 51  # rows overlap like a real triangle but stay just clear of touching

GROUP_NAMES = {"solids": "solids (1-7)", "stripes": "stripes (9-15)"}


def inGroup(number, group):
    return (group == "solids" and 1 <= number <= 7) or (group == "stripes" and 9 <= number <= 15)


class EightBallGame:

    def __init__(self, gameID, gameName, player1Name, player2Name):
        self.id = gameID
        self.game = Physics.Game(gameName=gameName, player1Name=player1Name,
                                 player2Name=player2Name)
        self.name = gameName
        self.players = [player1Name, player2Name]
        self.groups = [None, None]
        self.turn = 0
        self.winner = None
        self.message = "%s breaks." % player1Name

        self.balls = {0: HEAD_SPOT}
        for row, numbers in enumerate(RACK):
            for col, number in enumerate(numbers):
                self.balls[number] = (FOOT_SPOT[0] + (col - row / 2) * RACK_COLUMN,
                                      FOOT_SPOT[1] - row * RACK_ROW)

    def state(self):
        return {
            "id": self.id,
            "name": self.name,
            "players": self.players,
            "groups": self.groups,
            "turn": self.turn,
            "winner": self.winner,
            "message": self.message,
            "balls": [[n, round(x, 1), round(y, 1)] for n, (x, y) in self.balls.items()],
        }

    def shoot(self, xvel, yvel):
        if self.winner is not None:
            raise ValueError("The game is over.")

        speed = math.hypot(xvel, yvel)
        if speed > MAX_SPEED:
            xvel, yvel = xvel * MAX_SPEED / speed, yvel * MAX_SPEED / speed

        table = Physics.Table()
        for number, (x, y) in self.balls.items():
            table += Physics.StillBall(number, Physics.Coordinate(x, y))

        shooter = self.turn
        frames, pocketed, finalTable = self.game.shoot(
            self.name, self.players[shooter], table, xvel, yvel)
        self.balls = {n: (x, y) for n, x, y in Physics.ballPositions(finalTable)}

        self.applyRules(shooter, pocketed)
        return frames, pocketed

    def applyRules(self, shooter, pocketed):
        name = self.players[shooter]
        other = 1 - shooter
        scratch = 0 in pocketed
        objects = [n for n in pocketed if n not in (0, 8)]

        # The first object ball legally pocketed decides who plays which group.
        if self.groups[shooter] is None and objects and not scratch:
            group = "solids" if objects[0] < 8 else "stripes"
            self.groups[shooter] = group
            self.groups[other] = "stripes" if group == "solids" else "solids"

        group = self.groups[shooter]
        own = [n for n in objects if group is None or inGroup(n, group)]
        sunk = "" if not objects else " Pocketed %s." % ", ".join(map(str, objects))

        if scratch:
            self.respotCueBall()

        if 8 in pocketed:
            cleared = group is not None and not any(inGroup(n, group) for n in self.balls)
            if cleared and not scratch:
                self.winner = shooter
                self.message = "%s sinks the 8 ball and wins!" % name
            else:
                self.winner = other
                reason = "scratched on the 8" if cleared else "sank the 8 ball early"
                self.message = "%s %s. %s wins!" % (name, reason, self.players[other])
        elif scratch:
            self.turn = other
            self.message = "Scratch!%s %s's turn." % (sunk, self.players[other])
        elif own:
            self.message = "%s Shoot again, %s." % (sunk.strip(), name)
        else:
            self.turn = other
            self.message = "%s%s's turn." % (sunk.strip() + " " if sunk else "", self.players[other])

    def respotCueBall(self):
        x, y = HEAD_SPOT
        while any(math.hypot(x - bx, y - by) < Physics.BALL_DIAMETER + 1
                  for bx, by in self.balls.values()):
            y += Physics.BALL_DIAMETER
        self.balls[0] = (x, y)

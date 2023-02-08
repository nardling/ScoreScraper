import psycopg


class nbaScoreInserter:
    def __init__(self):
        self.con = psycopg.connect("dbname=nba_scores")
        self.con.autocommit = True
        self.statement: str = "INSERT INTO game_scores VALUES({}, '{}', '{}', {}, {}, {})"
        self.shotStatement: str = "INSERT INTO game_shots VALUES({}, '{}', '{}', {}, {}, {})"

    def insert(self, gameId: int, homeTeam: str, visitingTeam: str, homeScore: int, visitingScore: int, time: int):
        # print (self.statement.format(gameId, homeTeam, visitingTeam, homeScore, visitingScore, time))
        with self.con.cursor() as cur:
            try:
                cur.execute(self.statement.format(gameId, homeTeam, visitingTeam, homeScore, visitingScore, time))
            except Exception as e:
                print("Error executing SQL: ", e)

    def insertShots(self, gameId: int, homeTeam: str, visitingTeam: str, homeShots: int, visitingShots: int, time: int):
        with self.con.cursor() as cur:
            try:
                cur.execute(self.shotStatement.format(gameId, homeTeam, visitingTeam, homeShots, visitingShots, time))
            except Exception as e:
                print("Error executing SQL: ", e)

    def getMaxGameId(self, teamName: str) -> int:
        return 0
        with self.con.cursor() as cur:
            try:
                cur.execute("SELECT max(gameid) from game_scores where visitingteam = '{}' or hometeam = '{}'".format(teamName, teamName))
                rec = cur.fetchone()
                return int(rec[0])
            except Exception as e:
                print("Error executing SQL: ", e)
                return 0
            
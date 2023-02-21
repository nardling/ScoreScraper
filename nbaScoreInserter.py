import psycopg


class nbaScoreInserter:
    def __init__(self, tableExt: str = ""):
        self.con = psycopg.connect("dbname=nba_scores")
        self.con.autocommit = True
        self.table_ext = tableExt
        self.statement: str = "INSERT INTO game_scores" + tableExt + " VALUES({}, '{}', '{}', {}, {}, {})"
        self.shotStatement: str = "INSERT INTO game_shots" + tableExt + " VALUES({}, '{}', '{}', {}, {}, {})"
        self.subStatement: str = "INSERT INTO game_subs" + tableExt + " VALUES({}, '{}', '{}', {})"
        self.gameMetaStatement: str = "INSERT INTO game_meta" + tableExt + " VALUES({}, '{}', '{}', '{}', {}, {})"
        self.scorerStatement: str = "INSERT INTO game_scorers" + tableExt + " VALUES ({}, '{}', {}, {})"
        self.spreadAtTimeStatement: str = "SELECT * from game_scores" + tableExt + " where gameid = {} and time = (select max(time) from game_scores where gameid = {} and time <= {})"

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

    def insertSubs(self, gameId: int, subIn: str, subOut: str, time: int):
        with self.con.cursor() as cur:
            try:
                cur.execute(self.subStatement.format(gameId, subIn.replace("'", r"''") , subOut.replace("'", r"''"), time))
            except Exception as e:
                print("Error executing insertSubs SQL: ", e)

    def insertScoreEvent(self, gameId: int, scorer: str, points: int, time: int):
        with self.con.cursor() as cur:
            try:
                cur.execute(self.scorerStatement.format(gameId, scorer.replace("'", r"''"), points, time))
            except Exception as e:
                print("Error executing insert scorer SQL: ", e)

    def insertMeta(self, gameId: int, hometeam: str, visitingteam: str, line: str, overUnder: float, date: int) -> bool:
        with self.con.cursor() as cur:
            try:
                cur.execute(self.gameMetaStatement.format(gameId, hometeam, visitingteam, line, overUnder, date))
                return True
            except Exception as e:
                print("Error executing insertMeta SQL: ", e)
                return False

    def getSpreadAtTime(self, gameId: int, teamName: str, time: int) -> int:
        with self.con.cursor() as cur:
            try:
                cur.execute(self.spreadAtTimeStatement.format(gameId, gameId, time))
                rec = cur.fetchone()
                s = 0
                if rec == None:
                    raise Exception("No record")
                while(True):
                    if (rec[1] == teamName):
                        s = rec[3] - rec[4]
                    elif (rec[2] == teamName):
                        s = rec[4] - rec[3]
                    else:
                        raise Exception("team not in game")
                    rec = cur.fetchone()
                    if rec == None:
                        break
                return s
            except Exception as e:
                print("Error executing getSpreadAtTime ", e)
                raise e

    def getRecordLastFiveLastTen(self, teamName: str, gameId: int):
        i = 0
        allWins = 0
        lastTenWins = 0
        lastTenMargin = 0
        lastTenOT = 0
        lastFiveWins = 0
        lastFiveMargin = 0
        lastFiveOT = 0
        with self.con.cursor() as cur:
            try:
                stmt = "SELECT * from game_results where teamname='{}' and gameId < {} order by gameid desc"
                cur.execute(stmt.format(teamName, gameId))
                while(True):
                    rec = cur.fetchone()
                    if rec == None:
                        break
                    i = i + 1
                    if rec[2] == 'WIN':
                        allWins = allWins + 1
                        if i <= 10:
                            lastTenWins = lastTenWins + 1
                            lastTenMargin = lastTenMargin + rec[3]
                            if i <= 5:
                                lastFiveWins = lastFiveWins + 1
                                lastFiveMargin = lastFiveMargin + rec[3]
                    elif rec[2] == 'LOSE':
                        if i <= 10:
                            lastTenMargin = lastTenMargin + rec[3]
                            if i <= 5:
                                lastFiveMargin = lastFiveMargin + rec[3]
                    elif rec[3] == 'TIE':
                        if i <= 10:
                            lastTenOT = lastTenOT + 1
                            if i <= 5:
                                lastFiveOT = lastFiveOT + 1
                return [i, allWins, lastTenWins, lastTenMargin, lastTenOT, lastFiveWins, lastFiveMargin, lastFiveOT]
            except Exception as e:
                print(e)
                raise e


    def getMaxGameId(self, teamName: str) -> int:
        # return 0
        with self.con.cursor() as cur:
            try:
                cur.execute("SELECT max(gameid) from game_scores where visitingteam = '{}' or hometeam = '{}'".format(teamName, teamName))
                rec = cur.fetchone()
                return int(rec[0])
            except Exception as e:
                print("Error executing SQL: ", e)
                return 0
            
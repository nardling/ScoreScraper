import numpy as np
from nbaScoreInserter import nbaScoreInserter 
import psycopg

def spreadToFactor(spread: int) -> int:
    # 0 - 3 => 1
    # 3 - 6 => 2
    # 6 - 9 => 3
    # 9 - 12 => 4
    # > 12 => 5
    # -3 - 0 => -1
    # -6 - -3 => -2
    # -9 - -6 => -3
    # -12 - -9 => -4
    # < -12 => -5
    if spread > 12: return 5
    if spread > 9: return 4
    if spread > 6: return 3
    if spread > 3: return 2
    if spread > 0: return 1
    if spread > -3 : return -1
    if spread > -6: return -2
    if spread > -9: return -3
    if spread > -12: return -4
    return -5

def allWinToFactor(spread: int) -> int:
    if spread > 12: return 4
    if spread > 8: return 3
    if spread > 4: return 2
    if spread > 0: return 1
    if spread > -4: return -1
    if spread > -8: return -2
    if spread > -12: return -3
    return -4

def tenWinToFactor(spread: int) -> int:
    if spread > 6: return 3
    if spread > 3: return 2
    if spread > 0: return 1
    if spread > -3: return -1
    if spread > -6: return -2
    return -3

def fiveWinToFactor(spread: int) -> int:
    if spread > 2: return 3
    if spread > -3: return spread
    return -3

class factorGenerator:
    def __init__(self, tableExt: str = "", con = None):
        if con:
            self.con = con
        else:
            self.con = psycopg.connect("dbname=nba_scores")
        self.table_ext = tableExt
        self.volSourceStatement = "select * from game_scores" + tableExt + " where gameId = {} order by time"

    def calculateAllQuarterVol(self, gameId: int, teamName: str) -> float:
        scoreSpread = np.zeros((2880, 2))
        lastGameTime = -1
        with self.con.cursor() as cur:
            try:
                cur.execute(self.volSourceStatement.format(gameId))
                while (True):
                    rec = cur.fetchone()
                    if not rec:
                        break
                    gameTime = rec[5]
                    if lastGameTime > 0:
                        lastScoreSpread = scoreSpread[lastGameTime][0]
                        lastScoreTotal = scoreSpread[lastGameTime][1]
                        while lastGameTime < gameTime:
                            scoreSpread[lastGameTime][0] = lastScoreSpread
                            scoreSpread[lastGameTime][1] = lastScoreTotal
                            lastGameTime = lastGameTime + 1

                        scoreSpread[gameTime][0] = rec[3] - rec[4]
                        scoreSpread[gameTime][1] = rec[3] + rec[4]
                    else:
                        scoreSpread[gameTime][0] = rec[3] - rec[4]
                        scoreSpread[gameTime][1] = rec[3] + rec[4]
                        lastGameTime = gameTime
            except Exception as e:
                print("Error in Calculate Quater Vol ", e)

            for i in range(lastGameTime + 1, 2880):
                scoreSpread[i][0] = scoreSpread[lastGameTime][0]
                scoreSpread[i][1] = scoreSpread[lastGameTime][1]

        # generate factors
        firstHalfTotal = scoreSpread[1440][1]
        thirdQuarterTotal = scoreSpread[2160][1] - scoreSpread[1440][1]
        firstHalfVol = np.std(scoreSpread[:1440,0])
        thirdQuarterVol = np.std(scoreSpread[1441:2160,0])

        # 0 => 0 - 2, 1 => 2 - 4 up, 2 => 4 - 6 up, 3 => 6 - 8 up, 4 => 8 - 10 up, 5 => 10+ up
        #            -1 => 2 - 4 down, -2 => 4 - 6 down, -3 => 6 - 8 down, -4 => 8 - 10 down, -5 => 10+ down
        firstHalfSpread = 0
        thirdQuarterSpread = 0
        finalSpread = 0
        fourthQuarterDelta = 0
        n = nbaScoreInserter()
        try:
            firstHalfSpread = n.getSpreadAtTime(gameId, teamName, 1440)
            thirdQuarterSpread = n.getSpreadAtTime(gameId, teamName, 2160)
            finalSpread = n.getSpreadAtTime(gameId, teamName, 2880)
        except Exception as e:
            pass

        fourthQuarterDelta = finalSpread - thirdQuarterSpread

        firstHalfSpreadFactor = spreadToFactor(firstHalfSpread)
        thirdQuarterSpreadFactor = spreadToFactor(thirdQuarterSpread)
        finalSpreadFactor = spreadToFactor(finalSpread)
        fourthQuarterDeltaSpreadFactor = spreadToFactor(fourthQuarterDelta)

        #meta
        overunder = 0
        gameDate = 0
        favorite = ''
        opponent = ''
        line = 0
        expectedSpread: float = 0
        isHome = False
        with self.con.cursor() as cur:
            try:
                cur.execute("select * from game_meta where gameid = {}".format(gameId))
                rec = cur.fetchone()
                if rec:
                    overunder = rec[4]
                    gameDate = rec[5]
                    ll = rec[3].split()
                    line = ll[1]
                    favorite = ll[0]
                    if teamName == rec[1]:
                        isHome = True
                        opponent = rec[2]
                    elif teamName == rec[2]:
                        isHome = False
                        opponent = rec[1]
                    else:
                        raise Exception("Team Name Not In Meta")
                else:
                    raise Exception("Game Not In Meta")
            except Exception as e:
                print (e)

        with self.con.cursor() as cur:
            cur.execute("select * from team_abbrs where abbr = '{}'".format(favorite))
            rec = cur.fetchone()
            if rec == None:
                raise Exception("Can't resolve Favorite")
            nLine: float = float(line)
            if rec[1] == teamName:
                if (nLine < 0):
                    expectedSpread = (-1) * nLine
                else:
                    expectedSpread = nLine
            else:
                if (nLine < 0):
                    expectedSpread = nLine
                else:
                    expectedSpread = (-1) * nLine

        q1Shots = 0
        oppoQ1Shots = 0
        q2Shots = 0
        oppoQ2Shots = 0
        q3Shots = 0
        oppoQ3Shots = 0
        q4Shots = 0
        oppoQ4Shots = 0

        with self.con.cursor() as cur:
            try:
                cur.execute("select * from game_shots where gameid = {}".format(gameId))
                while(True):
                    rec = cur.fetchone()
                    if rec == None:
                        break
                    qtr = rec[5]
                    if qtr == 1:
                        if isHome:
                            q1Shots = rec[3]
                            oppoQ1Shots = rec[4]
                        else:
                            q1Shots = rec[4]
                            oppoQ1Shots = rec[3]
                        continue
                    if qtr == 2:
                        if isHome:
                            q2Shots = rec[3]
                            oppoQ2Shots = rec[4]
                        else:
                            q2Shots = rec[4]
                            oppoQ2Shots = rec[3]
                        continue
                    if qtr == 3:
                        if isHome:
                            q3Shots = rec[3]
                            oppoQ3Shots = rec[4]
                        else:
                            q3Shots = rec[4]
                            oppoQ3Shots = rec[3]
                        continue
                    if qtr == 4:
                        if isHome:
                            q4Shots = rec[3]
                            oppoQ4Shots = rec[4]
                        else:
                            q4Shots = rec[4]
                            oppoQ4Shots = rec[3]
                        continue
            except Exception as e:
                print(e)

        #[gameCount, allWins, lastTenWins, lastTenMargin, lastTenOT, lastFiveWins, lastFiveMargin, lastFiveOT]
        teamRecord = n.getRecordLastFiveLastTen(teamName, gameId)
        opponentRecord = n.getRecordLastFiveLastTen(opponent, gameId)

        allWinDiff = teamRecord[1] - opponentRecord[1]
        allWinDiffFactor = allWinToFactor(allWinDiff)

        tenWinDiff = teamRecord[2] - opponentRecord[2]
        tenWinDiffFactor = tenWinToFactor(tenWinDiff)

        fiveWinDiff = teamRecord[5] - opponentRecord[5]
        fiveWinDiffFactor = fiveWinToFactor(fiveWinDiff)

        #days since last game
        # 1, 2, 2+
        daysSinceLastGame:int = 0
        with self.con.cursor() as cur:
            try:
                stmt = "select a.date - (select max(date) from game_meta where (hometeam = '{}' or visitingteam = '{}') and date < a.date) from game_meta a where a.gameid = {}"
                cur.execute(stmt.format(teamName, teamName, gameId))
                rec = cur.fetchone()
                if rec:
                    if rec[0] < 3:
                        daysSinceLastGame = rec[0]
                    else:
                        daysSinceLastGame = 3
                else:
                    daysSinceLastGame = 3
            except Exception as e:
                print(e)


        # print("teamRecord ", teamRecord)
        # print("opponentRecord ", opponentRecord)
        # print ("firstHalfTotal: ", firstHalfTotal)
        # print ("thirdQuarterTotal: ", thirdQuarterTotal)
        # print ("firstHalfVol: ", firstHalfVol)
        # print ("thirdQuarterVol: ", thirdQuarterVol)
        # print ("firstHalfSpread ", firstHalfSpread)
        # print ("thirdQuarterSpread ", thirdQuarterSpread)
        # print ("finalSpread ", finalSpread)
        # print ("fourthQuarterDelta ", fourthQuarterDelta)
        # print ("firstHalfSpreadFactor ", firstHalfSpreadFactor)
        # print ("thirdQuarterSpreadFactor ", thirdQuarterSpreadFactor)
        # print ("finalSpreadFactor ", finalSpreadFactor)
        # print ("fourthQuarterDeltaFactor ", fourthQuarterDeltaSpreadFactor)
        # print("overunder ", overunder)
        # print("gameDate ", gameDate)
        # print("expectedSpread ", expectedSpread)
        # print("favorite ", favorite)
        # print("line ", line)
        # print("isHome ", isHome)
        # print("opponent ", opponent)
        # print("q1Shots ", q1Shots)
        # print("oppoQ1Shots ", oppoQ1Shots)
        # print("q2Shots ", q2Shots)
        # print("oppoQ2Shots ", oppoQ2Shots)
        # print("q3Shots ", q3Shots)
        # print("oppoQ3Shots ", oppoQ3Shots)
        # print("q4Shots ", q4Shots)
        # print("oppoQ4Shots ", oppoQ4Shots)
        # print("daysSinceLastGame ", daysSinceLastGame)

        print("{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}".format(
            firstHalfTotal, thirdQuarterTotal, firstHalfVol, thirdQuarterVol, firstHalfSpreadFactor, thirdQuarterSpreadFactor,
            finalSpreadFactor, fourthQuarterDeltaSpreadFactor, overunder, expectedSpread, isHome, q1Shots, oppoQ1Shots,
            q2Shots, oppoQ2Shots, q3Shots, oppoQ3Shots, q4Shots, oppoQ4Shots, daysSinceLastGame, allWinDiffFactor,
            tenWinDiffFactor, fiveWinDiffFactor
        ))


if __name__ == "__main__":
    print("In main")
    f = factorGenerator()
    f.calculateAllQuarterVol(401468988, 'Bulls')
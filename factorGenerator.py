import numpy as np
import psycopg

class factorGenerator:
    def __init__(self):
        self.con = psycopg.connect("dbname=nba_scores")

    def calculateAllQuarterVol(self, gameId: int, homeAway: str) -> float:
        scoreSpread = np.zeros((2880, 2))
        # startOffset = 0
        # with self.con.cursor() as cur:
        #     try:
        #         cur.execute("select * from game_scores where gameid = {} and time = (select max(time) from game_scores where gameid = {} and time <= 2160)".format(gameId, gameId))
        #         rec = None
        #         while (True):
        #             rec = cur.fetchone()
        #             if not rec:
        #                 break
        #             startOffset = rec[3] - rec[4]
        #         print(startOffset)
        #     except Exception as e:
        #         print("Error in calculateThirdQuarterVol: ", e)

        lastGameTime = -1
        with self.con.cursor() as cur:
            try:
                cur.execute("select * from game_scores where gameId = {} order by time".format(gameId))
                while (True):
                    rec = cur.fetchone()
                    print(rec, lastGameTime)
                    if not rec:
                        break
                    gameTime = rec[5]
                    print (gameTime)
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

        print ("firstHalfTotal: ", firstHalfTotal)
        print ("thirdQuarterTotal: ", thirdQuarterTotal)
        print ("firstHalfVol: ", firstHalfVol)
        print ("thirdQuarterVol: ", thirdQuarterVol)

        # 0 => 0 - 2, 1 => 2 - 4, 2 => 4 - 6, 3 => 6 - 8, 4 => 8 - 10, 5 => 10+
        if (homeAway == "home"):
            

if __name__ == "__main__":
    print("In main")
    f = factorGenerator()
    f.calculateAllQuarterVol(401468016)
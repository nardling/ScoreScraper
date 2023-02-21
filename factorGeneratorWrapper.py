from factorGenerator import factorGenerator
import psycopg

class factorGeneratorWrapper:
    def __init__(self, teamName: str):
        self.teamName = teamName
        self.con = psycopg.connect("dbname=nba_scores")
        self.factorGen = factorGenerator("", self.con)

    def runAllGames(self):
        stmt = "select gameId from game_meta where hometeam = '{}' or visitingteam = '{}' order by date"
        with self.con.cursor() as cur:
            cur.execute(stmt.format(self.teamName, self.teamName))
            rec = cur.fetchone()
            while rec:
                print (rec[0])
                self.factorGen.calculateAllQuarterVol(int(rec[0]), self.teamName)
                rec = cur.fetchone()

if __name__ == "__main__":
    f = factorGeneratorWrapper('Bulls')
    f.runAllGames()

import requests
import json
from nbaScoreInserter import nbaScoreInserter
from teamFinder import findHomeAndAway

# main pages are of form https://www.espn.com/nba/team/_/name/chi/chicago-bulls
# score pages are of form /nba/recap/_/gameId/401468899
# playbyplay is https://www.espn.com/nba/playbyplay/_/gameId
# "pbp":{"playGrps":[[ opens the play by play
# ]] closes it

def buildList(addr: str, teamName: str) -> None:
    x = requests.get(addr).content.decode('utf8')
    n = nbaScoreInserter()
    i = -1
    maxRecordedGame = n.getMaxGameId(teamName)
    print ("For {}, current max game Id is {}".format(teamName, str(maxRecordedGame)))
    while (True):
        i = x.find("gameId", i + 1)
        if i < 0:
            break
        firstQuote = i
        while x[firstQuote] != '"' and firstQuote >= 0:
            firstQuote = firstQuote - 1
        if firstQuote < 0:
            break
        nextQuote = i
        while x[nextQuote] != '"':
            nextQuote = nextQuote + 1
        xs = x[firstQuote:nextQuote].split('/')
        gameId: int = int(xs[len(xs) -1])
        if gameId > maxRecordedGame:
            recap = str.format("https://www.espn.com/nba/playbyplay/_/gameId/{}", gameId)
            if (not getScore(recap, gameId, n)):
                break
        

def getScore(addr: str, gameId: int, inserter: nbaScoreInserter) -> bool:
    import time
    print ("get ", addr)
    time.sleep(2)
    x = requests.get(addr).content.decode('utf8')
    # print(x)
    home, away = findHomeAndAway(x)
    if home == 'NA' or away == 'NA':
        print ("Could Not Resolve Teams")
        return True
    print(away, "@", home)
    i = x.find('playGrps', 0)
    j = x.find("]]", i)
    try:
        score = json.loads(x[i + 10:j + 2])
        lastHomeScore = -1
        lastVisScore = -1
        for quarter in score:
            qtrHomeShots = 0
            qrtVisShots = 0
            qtrNumber = 0
            for s in quarter:
                # filter for score change only
                if (int(s['awayScore']) != lastVisScore or int(s['homeScore']) != lastHomeScore):
                    qtrNumber = s['period']['number']
                    if int(s['homeScore']) != lastHomeScore:
                        lastHomeScore = int(s['homeScore'])
                        qtrHomeShots = qtrHomeShots + 1
                    if int(s['awayScore']) != lastVisScore:
                        lastVisScore = int(s['awayScore'])
                        qrtVisShots = qrtVisShots + 1

                    tt = s['clock']['displayValue'].split(':')
                    time = -1
                    if len(tt) == 2:
                        min = int(tt[0])
                        sec = int(tt[1])
                        time = (12 * (int(s['period']['number']) - 1) + (12 - min)) * 60 - sec
                    else:
                        tt = s['clock']['displayValue'].split('.')
                        if len(tt) == 2:
                            sec = int(tt[0])
                            min = 0
                            time = (12 * (int(s['period']['number']) - 1) + (12 - min)) * 60 - sec
                    if time > 0:
                        try:
                            inserter.insert(str(gameId), home, away, s['homeScore'], s['awayScore'], time)
                        except:
                            pass
                # elif 'text' in s and s['text'].find('misses') > 0:
                    # if s['homeAway'].strip() == 'away':
                    #     qtrVisShots = qtrVisShots + 1
                    # elif s['homeAway'].strip() == 'home':
                    #     qtrHomeShots = qtrHomeShots + 1

            try:
                inserter.insertShots(str(gameId), home, away, qtrHomeShots, qrtVisShots, qtrNumber)
            except:
                pass
                
    except:
        return False
    return True


def init():
    n = nbaScoreInserter()
    getScore("https://www.espn.com/nba/playbyplay/_/gameId/401468951", 401468951, n)
    print ("entering main")
    # buildList("https://www.espn.com/nba/team/schedule/_/name/bos/boston-celtics", 'Celtics')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/bkn/brooklyn-nets", 'Nets')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/ny/new-york-knicks", 'Knicks')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/phi/philadelphia-76ers", '76ers')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/tor/toronto-raptors", 'Raptors')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/den/denver-nuggets", 'Nuggets')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/min/minnesota-timberwolves", 'Timberwolves')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/okc/oklahoma-city-thunder", 'Thunder')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/por/portland-trail-blazers", 'Trail Blazers')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/utah/utah-jazz", 'Jazz')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/cle/cleveland-cavaliers", 'Cavaliers')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/det/detroit-pistons", 'Pistons')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/ind/indiana-pacers", 'Pacers')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/mil/milwaukee-bucks", 'Bucks')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/gs/golden-state-warriors", 'Warriors')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/lac/la-clippers", 'Clippers')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/lal/los-angeles-lakers", 'Lakers')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/phx/phoenix-suns", 'Suns')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/sac/sacramento-kings", 'Kings')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/atl/atlanta-hawks", 'Hawks')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/cha/charlotte-hornets", 'Hornets')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/mia/miami-heat", 'Heat')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/orl/orlando-magic", 'Magic')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/wsh/washington-wizards", 'Wizards')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/dal/dallas-mavericks", 'Mavericks')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/hou/houston-rockets", 'Rockets')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/mem/memphis-grizzlies", 'Grizzlies')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/no/new-orleans-pelicans", 'Pelicans')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/sa/san-antonio-spurs", 'Spurs')
    # buildList("https://www.espn.com/nba/team/schedule/_/name/chi/chicago-bulls", 'Bulls')

if __name__ == "__main__":
    init()
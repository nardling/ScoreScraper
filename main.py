import requests
import json
from nbaScoreInserter import nbaScoreInserter
from teamFinder import findHomeAndAway
from bs4 import BeautifulSoup
from timeFuncs import getTime
from dateutil import parser
from datetime import date

# main pages are of form https://www.espn.com/nba/team/_/name/chi/chicago-bulls
# score pages are of form /nba/recap/_/gameId/401468899
# playbyplay is https://www.espn.com/nba/playbyplay/_/gameId
# "pbp":{"playGrps":[[ opens the play by play
# ]] closes it

def buildList(addr: str, teamName: str, mode: int) -> None:
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
            if (not getScore(recap, gameId, n, mode)):
                break

def getGameStats(addr: str, hometeam: str, awayteam: str, gameId: int, inserter: nbaScoreInserter, mode: int) -> int:
    # print (addr)
    x = requests.get(addr).content.decode('utf8')
    parsed_page = BeautifulSoup(x, features="lxml")
    if not parsed_page:
        print(addr, " failed to parse in Beautiful Soup ")
        return -1
    
    lineInfo = parsed_page.body.find('div', attrs={'class','n8 GameInfo__BettingItem flex-expand line'})
    ll = ""
    if lineInfo:
        ll = lineInfo.text.split(':')[1]
    overUnder = parsed_page.body.find('div', attrs={'class','n8 GameInfo__BettingItem flex-expand ou'})
    ou = 0
    if overUnder:
        ou = overUnder.text.split(':')[1]

    gameDate = parsed_page.body.find('div', attrs={'class','n8 GameInfo__Meta'})
    julianGameDay = 0
    if gameDate:
        gdt = gameDate.text
        try:
            julianGameDay = parser.parse(gdt).toordinal()
        except:
            pass

        if julianGameDay == 0:
            try:
                gdt = gameDate.text
                c = gdt.find('C')
                if c > 0:
                    gdt = gdt[:c]
                    # print ("Use altername gameDate ", gameDate)
                    julianGameDay = parser.parse(gdt).toordinal()
            except:
                pass
        
        if julianGameDay == 0:
            print ("Could Not Compute Game Data for Game id ", gameId)

        # print (julianGameDay, " ", gdt, " ", date.today().toordinal())
        if julianGameDay >= date.today().toordinal() and mode == 0:
            print ("Game in future or today ", gameId)
            return -2

        try:
            if (inserter.insertMeta(gameId, hometeam, awayteam, ll, ou, julianGameDay)):
                return 0
            else:
                return -1
        except:
            return -1
    else:
        print ("Could Not Compute Game Date For Game Id ", gameId)
    return 0

def getScore(addr: str, gameId: int, inserter: nbaScoreInserter, mode: int) -> bool:
    import time
    print ("get ", addr)
    # time.sleep(2)
    x = requests.get(addr).content.decode('utf8')
    # print(x)
    home, away = findHomeAndAway(x)
    if home == 'NA' or away == 'NA':
        print ("Could Not Resolve Teams")
        return True
    print(away, "@", home)

    gameUrl = str.format('https://www.espn.com/nba/game/_/gameId/{}', gameId)
    gameRes = getGameStats(gameUrl, home, away, gameId, inserter, mode)
    if gameRes < 0:
        print ("Skipping gameId ", gameId, " couldn't insert MetaData")
        if gameRes < -1:
            print ("Reached Future Games.  End Loop")
            return False
        else:
            return True
    
    i = x.find('playGrps', 0)
    j = x.find("]]", i)
    try:
        score = json.loads(x[i + 10:j + 2])
        lastHomeScore = 0
        lastVisScore = 0
        for quarter in score:
            qtrHomeShots = 0
            qtrVisShots = 0
            qtrNumber = 0
            for s in quarter:
                # filter for score change only
                if 'scoringPlay' in s and s['scoringPlay']:
                    # print (s)
                    scorer = "?"
                    delta = 0
                    if 'text' in s:
                        makesIndex = s['text'].find('makes')
                        if (makesIndex > 0):
                            scorer = s['text'][:makesIndex - 1]
                    qtrNumber = s['period']['number']
                    if int(s['homeScore']) != lastHomeScore:
                        delta = int(s['homeScore']) - lastHomeScore
                        lastHomeScore = int(s['homeScore'])
                        qtrHomeShots = qtrHomeShots + 1
                    if int(s['awayScore']) != lastVisScore:
                        delta = int(s['awayScore']) - lastVisScore
                        lastVisScore = int(s['awayScore'])
                        qtrVisShots = qtrVisShots + 1
                    gameTime = getTime(s)
                    if gameTime > 0:
                        try:
                            inserter.insert(str(gameId), home, away, s['homeScore'], s['awayScore'], gameTime)
                            inserter.insertScoreEvent(gameId, scorer, delta, gameTime)
                        except:
                            pass
                elif 'text' in s:
                    entersFor = s['text'].find('enters the game for')
                    if entersFor > 0:
                        subIn = s['text'][:entersFor].strip()
                        subOut = s['text'][entersFor + 20:].strip()
                        gameTime = getTime(s)
                        inserter.insertSubs(gameId, subIn, subOut, gameTime);
                    elif s['text'].find('misses') > 0:
                        try:
                            if s['homeAway'].strip() == 'away':
                                qtrVisShots = qtrVisShots + 1
                            elif s['homeAway'].strip() == 'home':
                                qtrHomeShots = qtrHomeShots + 1
                        except Exception as e:
                            print(e)

            try:
                inserter.insertShots(str(gameId), home, away, qtrHomeShots, qtrVisShots, qtrNumber)
            except:
                pass
                
    except:
        return False
    return True


def init():
    n = nbaScoreInserter()
    # getScore("https://www.espn.com/nba/playbyplay/_/gameId/401468519", 401468501, n, 0)
    # print ("entering main")
    mode = 0
    # buildList("https://www.espn.com/nba/team/schedule/_/name/bos/boston-celtics", 'Celtics', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/bkn/brooklyn-nets", 'Nets', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/ny/new-york-knicks", 'Knicks', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/phi/philadelphia-76ers", '76ers', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/tor/toronto-raptors", 'Raptors', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/den/denver-nuggets", 'Nuggets', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/min/minnesota-timberwolves", 'Timberwolves', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/okc/oklahoma-city-thunder", 'Thunder', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/por/portland-trail-blazers", 'Trail Blazers', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/utah/utah-jazz", 'Jazz', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/cle/cleveland-cavaliers", 'Cavaliers', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/det/detroit-pistons", 'Pistons', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/ind/indiana-pacers", 'Pacers', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/mil/milwaukee-bucks", 'Bucks', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/gs/golden-state-warriors", 'Warriors', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/lac/la-clippers", 'Clippers', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/lal/los-angeles-lakers", 'Lakers', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/phx/phoenix-suns", 'Suns', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/sac/sacramento-kings", 'Kings', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/atl/atlanta-hawks", 'Hawks', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/cha/charlotte-hornets", 'Hornets', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/mia/miami-heat", 'Heat', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/orl/orlando-magic", 'Magic', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/wsh/washington-wizards", 'Wizards', mode)
    buildList("https://www.espn.com/nba/team/schedule/_/name/dal/dallas-mavericks", 'Mavericks', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/hou/houston-rockets", 'Rockets', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/mem/memphis-grizzlies", 'Grizzlies', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/no/new-orleans-pelicans", 'Pelicans', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/sa/san-antonio-spurs", 'Spurs', mode)
    # buildList("https://www.espn.com/nba/team/schedule/_/name/chi/chicago-bulls", 'Bulls', mode)

if __name__ == "__main__":
    init()
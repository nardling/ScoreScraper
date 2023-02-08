import json
import re

def findMatchingBracket(text: str, index: int) -> int:
    bktCount = 0
    while (index < len(text)):
        if (text[index] == ']'):
            if bktCount == 1:
                return index
            else:
                bktCount = bktCount - 1
        if (text[index] == '['):
            bktCount = bktCount + 1
        index = index + 1

def findHomeAndAway(text: str) -> str:
    found = False
    i = -1
    home = "NA"
    away = "NA"
    # print (text)
    while (not found):
        i = text.find('"competitors":[', i + 1)
        if i < 0:
            return "NA"
        end = findMatchingBracket(text, i)
        try:
            # print("{" + text[i:(end + 1)] + "}")
            teams = json.loads("{" + text[i:(end + 1)] + "}")
            if len(teams["competitors"]) == 2:
                if teams["competitors"][0]["isHome"] == True:
                    home = teams["competitors"][0]["shortDisplayName"]
                    away = teams["competitors"][1]["shortDisplayName"]
                else:
                    away = teams["competitors"][0]["shortDisplayName"]
                    home = teams["competitors"][1]["shortDisplayName"]
                return home, away
        except:
            pass
    return home, away


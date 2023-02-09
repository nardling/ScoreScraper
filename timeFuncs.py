def getTime(event) -> int:
    tt = event['clock']['displayValue'].split(':')
    time = -1
    if len(tt) == 2:
        min = int(tt[0])
        sec = int(tt[1])
        time = (12 * (int(event['period']['number']) - 1) + (12 - min)) * 60 - sec
    else:
        tt = event['clock']['displayValue'].split('.')
        if len(tt) == 2:
            sec = int(tt[0])
            min = 0
            time = (12 * (int(event['period']['number']) - 1) + (12 - min)) * 60 - sec
    return time
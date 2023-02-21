truncate table game_results;

insert into game_results
with maxxes as (
    select gameid, hometeam, visitingteam, max(time) as time, 
        max(homescore) as homescore, max(visitingscore) as visitingscore
    from game_scores where time <= 2880 group by gameid, hometeam, visitingteam
)
select gameid, hometeam, 'LOSE' as result, homescore - visitingscore
from maxxes a where homescore < visitingscore;

insert into game_results
with maxxes as (
    select gameid, hometeam, visitingteam, max(time) as time, 
        max(homescore) as homescore, max(visitingscore) as visitingscore
    from game_scores where time <= 2880 group by gameid, hometeam, visitingteam
)
select gameid, visitingteam, 'WIN' as result, visitingscore - homescore
from maxxes a where homescore < visitingscore;

insert into game_results
with maxxes as (
    select gameid, hometeam, visitingteam, max(time) as time, 
        max(homescore) as homescore, max(visitingscore) as visitingscore
    from game_scores where time <= 2880 group by gameid, hometeam, visitingteam
)
select gameid, hometeam, 'WIN' as result, homescore - visitingscore
from maxxes a where homescore > visitingscore;

insert into game_results
with maxxes as (
    select gameid, hometeam, visitingteam, max(time) as time, 
        max(homescore) as homescore, max(visitingscore) as visitingscore
    from game_scores where time <= 2880 group by gameid, hometeam, visitingteam
)
select gameid, visitingteam, 'LOSE' as result, visitingscore - homescore
from maxxes a where homescore > visitingscore;

insert into game_results
with maxxes as (
    select gameid, hometeam, visitingteam, max(time) as time, 
        max(homescore) as homescore, max(visitingscore) as visitingscore
    from game_scores where time <= 2880 group by gameid, hometeam, visitingteam
)
select gameid, visitingteam, 'TIE' as result, visitingscore - homescore
from maxxes a where homescore = visitingscore;

insert into game_results
with maxxes as (
    select gameid, hometeam, visitingteam, max(time) as time, 
        max(homescore) as homescore, max(visitingscore) as visitingscore
    from game_scores where time <= 2880 group by gameid, hometeam, visitingteam
)
select gameid, hometeam, 'TIE' as result, visitingscore - homescore
from maxxes a where homescore = visitingscore;
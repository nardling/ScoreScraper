truncate table dup_game_scores;
truncate table dup_game_meta;
truncate table dup_game_results;
truncate table dup_game_scorers;
truncate table dup_game_shots;
truncate table dup_game_subs;

insert into dup_game_scores select * from game_scores;
insert into dup_game_meta select * from game_meta;
insert into dup_game_results select * from game_results;
insert into dup_game_scorers select * from game_scorers;
insert into dup_game_shots select * from game_shots;
insert into dup_game_subs select * from game_subs;
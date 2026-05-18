CREATE SCHEMA IF NOT EXISTS raw;



--- Bootstrap tables ---
CREATE TABLE IF NOT EXISTS raw.teams (
    id INT PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.players (
    id INT PRIMARY KEY,
    web_name TEXT,
    first_name TEXT,
    second_name TEXT,
    team INT REFERENCES raw.teams(id),
    element_type INT,
    now_cost INT,
    total_points INT
);

--- Fixture tables ---
CREATE TABLE IF NOT EXISTS raw.fixtures (
    id INT PRIMARY KEY,
    event INT,
    kickoff_time TIMESTAMP,
    team_h INT,
    team_a INT,
    team_h_score INT,
    team_a_score INT,
    team_h_difficulty INT,
    team_a_difficulty INT,
    finished BOOLEAN
);

--- Player history tables by gameweek ---
CREATE TABLE IF NOT EXISTS raw.player_history (
    player_id INT REFERENCES raw.players(id),
    fixture INT REFERENCES raw.fixtures(id),
    round INT,

    kickoff_time TIMESTAMP,

    opponent_team INT,
    was_home BOOLEAN,

    minutes INT,
    total_points INT,

    goals_scored INT,
    assists INT,
    clean_sheets INT,
    goals_conceded INT,

    saves INT,
    bonus INT,
    bps INT,

    expected_goals FLOAT,
    expected_assists FLOAT,
    expected_goals_conceded FLOAT,

    value INT,

    PRIMARY KEY (player_id, fixture, round)
);
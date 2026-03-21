from S1.download_players import collect_history_rows, load_player_ids, save_history
from S1.fpl_api import (
    fetch_bootstrap_static,
    fetch_fixtures,
    save_fixtures,
    save_players,
    save_teams,
)
from S1.init_db import init_db

if __name__ == "__main__":
    init_db()

    data = fetch_bootstrap_static()
    fixtures = fetch_fixtures()

    save_teams(data)
    save_players(data)
    save_fixtures(fixtures)

    player_ids = load_player_ids()
    rows = collect_history_rows(player_ids)
    save_history(rows)
    

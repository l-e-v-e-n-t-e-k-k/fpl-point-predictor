from S1.download_players import main as download_players_main
from S1.fpl_api import main as fpl_api_main
from S1.init_db import init_db

if __name__ == "__main__":
    init_db()
    fpl_api_main()
    download_players_main()
    

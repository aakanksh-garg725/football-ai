import httpx
from typing import Dict, Optional, List

class SleeperService:
    """Service to interact with Sleeper API for NFL player injuries"""
    
    BASE_URL = "https://api.sleeper.app/v1"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self._players_cache = None
    
    async def get_all_players(self) -> Dict:
        """Get all NFL players from Sleeper (cached)"""
        if self._players_cache is not None:
            return self._players_cache
        
        try:
            url = f"{self.BASE_URL}/players/nfl"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            players = response.json()
            self._players_cache = players
            
            print(f"✅ Cached {len(players)} players from Sleeper")
            
            return players
            
        except Exception as e:
            print(f"❌ Error fetching Sleeper players: {e}")
            return {}
    
    async def get_player_by_name(self, name: str) -> Optional[Dict]:
        """Find a player by name"""
        try:
            players = await self.get_all_players()
            
            search_name = name.lower().strip()
            
            for sleeper_id, player_data in players.items():
                full_name = player_data.get('full_name', '').lower()
                
                if search_name in full_name or full_name in search_name:
                    player_data['sleeper_id'] = sleeper_id
                    return player_data
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding player by name: {e}")
            return None
    
    async def get_team_injuries(self, team_abbr: str, position_group: str) -> List[Dict]:
        """Get injuries for teammates at the same position group"""
        try:
            if not team_abbr or team_abbr.upper() == 'N/A':
                return []
            
            if not position_group:
                return []
            
            players = await self.get_all_players()
            
            if not players:
                return []
            
            injured_teammates = []
            team_abbr_upper = team_abbr.upper()
            position_group_upper = position_group.upper()
            
            print(f"   🔍 Searching for injured {position_group_upper}s on {team_abbr_upper}...")
            
            for sleeper_id, player_data in players.items():
                if not player_data or not isinstance(player_data, dict):
                    continue
                
                # Check team
                player_team = player_data.get('team')
                if not player_team or player_team.upper() != team_abbr_upper:
                    continue
                
                # Check position
                player_pos = player_data.get('position')
                if not player_pos or not self._matches_position_group(player_pos, position_group_upper):
                    continue
                
                # Check injury
                injury_status = player_data.get('injury_status', '')
                if injury_status and injury_status.strip():
                    injury_body_part = player_data.get('injury_body_part', '')
                    
                    # Build injury status string
                    if injury_body_part:
                        full_status = f"{injury_status.upper()} - {injury_body_part}"
                    else:
                        full_status = injury_status.upper()
                    
                    injured_teammates.append({
                        "name": player_data.get('full_name', 'Unknown'),
                        "position": player_pos,
                        "injury_status": full_status
                    })
                    
                    print(f"      🏥 Found: {player_data.get('full_name')} - {full_status}")
            
            if injured_teammates:
                print(f"   ✅ Found {len(injured_teammates)} injured {position_group_upper}s on {team_abbr_upper}")
            
            return injured_teammates
            
        except Exception as e:
            print(f"   ⚠️  Error getting team injuries: {e}")
            return []
    
    def _matches_position_group(self, position: str, group: str) -> bool:
        """Check if position matches the position group"""
        position = position.upper()
        group = group.upper()
        
        if group == 'QB':
            return position == 'QB'
        elif group == 'RB':
            return position in ['RB', 'FB']
        elif group == 'WR':
            return position == 'WR'
        elif group == 'TE':
            return position == 'TE'
        elif group == 'K':
            return position in ['K', 'PK']
        else:
            return position == group
    
    def _get_position_group(self, position: str) -> str:
        """Get position group for a position"""
        position = position.upper()
        
        if position == 'QB':
            return 'QB'
        elif position in ['RB', 'FB']:
            return 'RB'
        elif position == 'WR':
            return 'WR'
        elif position == 'TE':
            return 'TE'
        elif position in ['K', 'PK']:
            return 'K'
        else:
            return position
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
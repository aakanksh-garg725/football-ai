import httpx
from typing import Dict, List, Optional

class ESPNService:
    """Service to interact with ESPN API for NFL player data"""
    
    BASE_URL_V2 = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
    BASE_URL_V3 = "https://sports.core.api.espn.com/v3/sports/football/nfl"
    CURRENT_SEASON = "2025"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self._players_cache = None
    
    async def get_all_players(self) -> List[Dict]:
        """Get all NFL players (cached) using v3 API"""
        if self._players_cache:
            return self._players_cache
        
        try:
            print("🔍 Fetching all NFL players...")
            
            url = f"{self.BASE_URL_V3}/athletes"
            params = {"limit": 20000}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            all_athletes = data.get("items", [])
            
            # Filter for active players only
            active_players = [p for p in all_athletes if p.get("active", False)]
            
            self._players_cache = active_players
            print(f"✅ Cached {len(active_players)} active NFL players")
            
            return active_players
            
        except Exception as e:
            print(f"❌ Error fetching players: {e}")
            return []
    
    async def search_player(self, player_name: str) -> Optional[Dict]:
        """Search for a player by name"""
        try:
            print(f"🔍 Searching for player: {player_name}")
            
            players = await self.get_all_players()
            
            search_term = player_name.lower().strip()
            
            # Search through cached players
            for player in players:
                player_full_name = player.get("displayName", "").lower()
                
                if search_term in player_full_name or player_full_name in search_term:
                    player_id = player.get("id")
                    
                    # Get full player details from v2 API
                    v2_url = f"{self.BASE_URL_V2}/athletes/{player_id}"
                    
                    try:
                        v2_response = await self.client.get(v2_url)
                        v2_response.raise_for_status()
                        v2_data = v2_response.json()
                        
                        # Get team info
                        team_ref = v2_data.get("team", {}).get("$ref")
                        team_abbr = "N/A"
                        team_id = None
                        
                        if team_ref:
                            team_response = await self.client.get(team_ref)
                            if team_response.status_code == 200:
                                team_data = team_response.json()
                                team_abbr = team_data.get("abbreviation", "N/A")
                                team_id = team_data.get("id")
                        
                        # Get position info
                        position_ref = v2_data.get("position", {}).get("$ref")
                        position_abbr = "N/A"
                        
                        if position_ref:
                            pos_response = await self.client.get(position_ref)
                            if pos_response.status_code == 200:
                                pos_data = pos_response.json()
                                position_abbr = pos_data.get("abbreviation", "N/A")
                        
                        print(f"✅ Found player: {player.get('displayName')} on {team_abbr}")
                        
                        return {
                            "id": player_id,
                            "displayName": player.get("displayName"),
                            "team": {
                                "id": team_id,
                                "abbreviation": team_abbr
                            },
                            "position": {
                                "abbreviation": position_abbr
                            }
                        }
                    
                    except Exception as e:
                        print(f"⚠️  Error getting full details: {e}")
                        # Return basic info if v2 fails
                        return {
                            "id": player_id,
                            "displayName": player.get("displayName"),
                            "team": {"id": None, "abbreviation": "N/A"},
                            "position": {"abbreviation": "N/A"}
                        }
            
            print(f"⚠️  Player '{player_name}' not found")
            return None
            
        except Exception as e:
            print(f"❌ Error searching for player: {e}")
            return None
    
    async def get_player_stats(self, player_id: str, season: str = "2025") -> Optional[Dict]:
        """Get player stats for current season"""
        try:
            url = f"{self.BASE_URL_V2}/seasons/{season}/types/2/athletes/{player_id}/statistics/0"
            
            print(f"   🔍 Fetching stats from ESPN")
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            stats_data = response.json()
            
            # Parse stats into readable format
            parsed_stats = self._parse_espn_stats(stats_data)
            summary = self._create_stats_summary(parsed_stats)
            
            print(f"   ✅ Got stats from ESPN")
            
            return {
                "raw": stats_data,
                "parsed": parsed_stats,
                "summary": summary
            }
            
        except Exception as e:
            print(f"❌ Error fetching stats: {e}")
            return None
    
    def _parse_espn_stats(self, stats_data: Dict) -> Dict:
        """Parse ESPN stats structure"""
        parsed = {}
        
        splits = stats_data.get("splits", {})
        categories = splits.get("categories", [])
        
        for category in categories:
            category_name = category.get("name", "")
            stats = category.get("stats", [])
            
            for stat in stats:
                stat_name = stat.get("name", "")
                stat_value = stat.get("value", 0)
                parsed[f"{category_name}_{stat_name}"] = stat_value
        
        return parsed
    
    def _create_stats_summary(self, parsed_stats: Dict) -> str:
        """Create human-readable stats summary"""
        
        # Passing stats
        pass_yds = parsed_stats.get("passing_passingYards", 0)
        pass_tds = parsed_stats.get("passing_passingTouchdowns", 0)
        ints = parsed_stats.get("passing_interceptions", 0)
        
        # Rushing stats
        rush_yds = parsed_stats.get("rushing_rushingYards", 0)
        rush_tds = parsed_stats.get("rushing_rushingTouchdowns", 0)
        
        # Receiving stats
        rec = parsed_stats.get("receiving_receptions", 0)
        rec_yds = parsed_stats.get("receiving_receivingYards", 0)
        rec_tds = parsed_stats.get("receiving_receivingTouchdowns", 0)
        
        return f"2025 Season: {pass_yds} pass yds, {pass_tds} pass TDs, {ints} INTs, {rush_yds} rush yds, {rush_tds} rush TDs, {rec} rec, {rec_yds} rec yds, {rec_tds} rec TDs"
    
    async def get_team_context(self, player_id: str, position: str, team_id: str) -> Dict:
        """Get team context for depth chart position"""
        
        # Get position group
        position_group = self._get_position_group(position)
        
        # Simple context
        context = f"Player plays {position}"
        
        return {
            "context": context,
            "depth": None,
            "position_group": position_group
        }
    
    def _get_position_group(self, position: str) -> str:
        """Map position to position group"""
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
        """Close HTTP client"""
        await self.client.aclose()
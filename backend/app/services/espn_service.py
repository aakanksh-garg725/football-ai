import httpx
from typing import Dict, List, Optional
import json
from datetime import datetime

class ESPNService:
    """Service to interact with ESPN's API for real NFL data"""
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
    CORE_URL = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        # Cache for team rosters to reduce API calls
        self._team_rosters = {}
    
    async def search_player(self, player_name: str) -> Optional[Dict]:
        """Search for a player by name across all NFL teams"""
        try:
            print(f"🔍 Searching for player: {player_name}")
            
            # Normalize search term
            search_term = player_name.lower().strip()
            
            # Get all NFL teams
            teams = await self._get_all_teams()
            
            if not teams:
                print("❌ Could not fetch teams")
                return self._create_fallback_player(player_name)
            
            # Search through each team's roster
            for team in teams:
                team_id = team.get('id')
                team_abbr = team.get('abbreviation', 'UNK')
                
                # Get roster for this team
                roster = await self._get_team_roster(team_id)
                
                if roster:
                    # Search through roster for matching player
                    for athlete in roster:
                        # Skip if athlete is None or invalid
                        if not athlete or not isinstance(athlete, dict):
                            continue
        
                        athlete_name = athlete.get('displayName', '').lower()
        
                        # Skip if no name
                        if not athlete_name:
                            continue
        
                        # Check for match
                        if search_term in athlete_name or athlete_name in search_term:
                            print(f"✅ Found player: {athlete.get('displayName')} on {team_abbr}")
            
                            # Enhance athlete data with team info
                            athlete['team'] = {
                                'id': team_id,
                                'abbreviation': team_abbr,
                                'displayName': team.get('displayName', team_abbr)
                            }
            
                            return athlete
            
            # If no exact match found, return fallback
            print(f"⚠️  No exact match found for '{player_name}', using fallback")
            return self._create_fallback_player(player_name)
            
        except Exception as e:
            print(f"❌ Error searching for player: {e}")
            return self._create_fallback_player(player_name)
    
    async def _get_all_teams(self) -> List[Dict]:
        """Get all NFL teams"""
        try:
            url = f"{self.BASE_URL}/teams"
            response = await self.client.get(url, params={'limit': 32})
            response.raise_for_status()
            
            data = response.json()
            
            # Extract teams from the nested structure
            teams = []
            if 'sports' in data and len(data['sports']) > 0:
                sport = data['sports'][0]
                if 'leagues' in sport and len(sport['leagues']) > 0:
                    league = sport['leagues'][0]
                    if 'teams' in league:
                        for team_data in league['teams']:
                            if 'team' in team_data:
                                teams.append(team_data['team'])
            
            print(f"✅ Fetched {len(teams)} NFL teams")
            return teams
            
        except Exception as e:
            print(f"❌ Error fetching teams: {e}")
            return []
    
    async def _get_team_roster(self, team_id: str) -> Optional[List[Dict]]:
        """Get roster for a specific team with caching"""
    
        # Check cache first
        if team_id in self._team_rosters:
            return self._team_rosters[team_id]
    
        try:
            url = f"{self.BASE_URL}/teams/{team_id}/roster"
            response = await self.client.get(url)
            response.raise_for_status()
        
            data = response.json()
        
            athletes = []
        
            # ESPN returns athletes grouped by position
            if 'athletes' in data:
                for position_group in data['athletes']:
                    # Each position group has 'items' with the actual players
                    if 'items' in position_group:
                        athletes.extend(position_group['items'])
        
            # Cache the roster
            self._team_rosters[team_id] = athletes
        
            if athletes and not self._team_rosters:
                print(f"   📊 Loaded {len(athletes)} athletes for team {team_id}")
        
            return athletes
        
        except Exception as e:
            return None
    
    def _create_fallback_player(self, player_name: str) -> Dict:
        """Create a fallback player structure when API search fails"""
        return {
            "id": "fallback",
            "displayName": player_name,
            "position": {"abbreviation": "PLAYER"},
            "team": {"abbreviation": "NFL", "id": "0"},
            "headshot": None
        }
    
    async def get_player_stats(self, player_id: str, season: str = "2024") -> Optional[Dict]:
        """Get detailed stats for a specific player"""
        try:
            # Don't try to fetch stats for fallback players
            if player_id == "fallback":
                return self._create_mock_stats()
            
            url = f"{self.CORE_URL}/seasons/{season}/athletes/{player_id}/statistics"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Fetched stats for player {player_id}")
            
            return data
            
        except Exception as e:
            print(f"⚠️  Could not fetch stats for player {player_id}: {e}")
            return self._create_mock_stats()
    
    def _create_mock_stats(self) -> Dict:
        """Create mock stats when real stats aren't available"""
        return {
            "splits": {
                "categories": [
                    {
                        "name": "general",
                        "stats": [
                            {"name": "gamesPlayed", "value": 10},
                            {"name": "touchdowns", "value": 5}
                        ]
                    }
                ]
            },
            "note": "Limited stats available"
        }
    
    async def get_player_info(self, player_id: str) -> Optional[Dict]:
        """Get detailed player information including injury status"""
        try:
            # Don't try to fetch info for fallback players
            if player_id == "fallback":
                return {
                    "athlete": {
                        "displayName": "Player",
                        "injuries": []
                    }
                }
            
            url = f"{self.BASE_URL}/athletes/{player_id}"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Fetched player info for {player_id}")
            
            # Check for injuries
            if 'athlete' in data:
                athlete = data['athlete']
                injuries = athlete.get('injuries', [])
                
                if injuries:
                    print(f"🏥 Player has {len(injuries)} injury record(s)")
                
            return data
            
        except Exception as e:
            print(f"⚠️  Could not fetch player info for {player_id}: {e}")
            return {
                "athlete": {
                    "displayName": "Player",
                    "injuries": []
                }
            }
    
    async def get_team_schedule(self, team_id: str, season: str = "2024") -> Optional[Dict]:
        """Get team schedule and upcoming games"""
        try:
            if team_id == "0":  # Fallback team
                return None
                
            url = f"{self.BASE_URL}/teams/{team_id}/schedule"
            params = {"season": season}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Fetched schedule for team {team_id}")
            
            return data
            
        except Exception as e:
            print(f"⚠️  Could not fetch schedule for team {team_id}: {e}")
            return None
    
    async def get_scoreboard(self, week: Optional[int] = None) -> Optional[Dict]:
        """Get current week's scoreboard"""
        try:
            url = f"{self.BASE_URL}/scoreboard"
            params = {}
            if week:
                params["week"] = week
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Get current week info
            if 'week' in data:
                current_week = data['week'].get('number', 'Unknown')
                print(f"✅ Fetched scoreboard for week {current_week}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error fetching scoreboard: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
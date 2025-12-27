import asyncio
from typing import Dict, Optional
from app.services.espn_service import ESPNService
from app.services.sleeper_service import SleeperService

class HybridNFLService:
    """
    Hybrid service combining ESPN and Sleeper
    
    - ESPN: Player search, team info, stats
    - Sleeper: Real-time injuries, depth chart context
    """
    
    def __init__(self):
        self.espn = ESPNService()
        self.sleeper = SleeperService()
    
    async def get_complete_player_data(self, player_name: str) -> Optional[Dict]:
        """
        Get complete player data from ESPN and Sleeper
        
        Returns combined data:
        - Basic info and stats from ESPN
        - Injury status from Sleeper
        """
        
        print(f"\n🔍 Fetching data for: {player_name}")
        
        # Search ESPN
        espn_player = await self.espn.search_player(player_name)
        
        if not espn_player:
            print(f"❌ Player '{player_name}' not found")
            return None
        
        # Build player data
        player_data = {
            "name": espn_player.get("displayName", player_name),
            "position": espn_player.get("position", {}).get("abbreviation", "N/A"),
            "team": espn_player.get("team", {}).get("abbreviation", "N/A"),
            "espn_id": espn_player.get("id"),
            "espn_data": espn_player
        }
        
        # Get Sleeper data
        sleeper_player = await self.sleeper.get_player_by_name(player_name)
        
        if sleeper_player:
            player_data["sleeper_id"] = sleeper_player.get("sleeper_id") or sleeper_player.get("player_id")
            player_data["sleeper_data"] = sleeper_player
            print(f"✅ Found in Sleeper")
        else:
            print(f"⚠️  Not found in Sleeper")
        
        return player_data
    
    async def get_player_stats(self, player_data: Dict) -> Optional[Dict]:
        """Get player stats from ESPN"""
        
        if "espn_id" not in player_data:
            return None
        
        espn_id = player_data["espn_id"]
        stats = await self.espn.get_player_stats(espn_id)
        
        if stats:
            print(f"✅ Got stats from ESPN")
            return stats
        
        print(f"⚠️  No stats available")
        return None
    
    async def get_player_injury(self, player_data: Dict) -> str:
        """Get player injury status from Sleeper"""
        
        player_name = player_data.get("name", "")
        team_abbr = player_data.get("team", "N/A")
        position = player_data.get("position", "N/A")
        
        # Check Sleeper injuries endpoint
        try:
            position_group = self.sleeper._get_position_group(position)
            injuries = await self.sleeper.get_team_injuries(team_abbr, position_group)
            
            # Find this specific player
            for injury in injuries:
                if injury.get('name', '').lower() == player_name.lower():
                    injury_status = injury.get('injury_status', 'Healthy')
                    print(f"✅ Got injury from Sleeper: {injury_status}")
                    return injury_status
        except Exception as e:
            print(f"⚠️  Sleeper injury check failed: {e}")
        
        print(f"✅ Player is healthy")
        return "Healthy"
    
    async def get_team_context(self, player_data: Dict) -> Dict:
        """Get team context (depth chart + injured teammates) from ESPN + Sleeper"""
        
        position = player_data.get("position", "N/A")
        player_name = player_data.get("name", "")
        espn_id = player_data.get("espn_id")
        team_id = player_data.get("espn_data", {}).get("team", {}).get("id")
        team_abbr = player_data.get("team", "N/A")
        
        if not team_id or not espn_id:
            return {
                "context": "No team context available",
                "depth": None,
                "injured_teammates": []
            }
        
        try:
            # Get ESPN team context
            espn_context = await self.espn.get_team_context(espn_id, position, team_id)
            
            # Get Sleeper injuries for teammates
            position_group = espn_context.get("position_group")
            teammate_injuries = []
            
            if position_group:
                all_injuries = await self.sleeper.get_team_injuries(team_abbr, position_group)
                
                # Filter out the target player
                teammate_injuries = [
                    inj for inj in all_injuries 
                    if inj.get('name', '').lower() != player_name.lower()
                ]
            
            espn_context["injured_teammates"] = teammate_injuries
            
            print(f"✅ Got team context")
            return espn_context
            
        except Exception as e:
            print(f"❌ Error getting team context: {e}")
            return {
                "context": "No team context available",
                "depth": None,
                "injured_teammates": []
            }
    
    async def close(self):
        """Close all service connections"""
        await self.espn.close()
        await self.sleeper.close()
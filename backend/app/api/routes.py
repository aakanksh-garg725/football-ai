from dotenv import load_dotenv
import os
load_dotenv()

from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    PlayerAnalysisRequest,
    PlayerAnalysisResponse,
    PlayerSearchResponse,
    ComparePlayersRequest,
    ComparePlayersResponse
)
from app.services.espn_service import ESPNService
from app.services.gemini_service import GeminiService
from typing import List

router = APIRouter(prefix="/api/players", tags=["players"])

# Initialize services
espn_service = ESPNService()
gemini_service = GeminiService()

@router.post("/analyze", response_model=PlayerAnalysisResponse)
async def analyze_player(request: PlayerAnalysisRequest):
    """
    Analyze a player for fantasy football decisions using AI
    
    This endpoint:
    1. Searches for the player in ESPN's database
    2. Fetches their recent stats and info
    3. Uses Claude AI to provide start/sit recommendations
    """
    
    try:
        # Step 1: Search for the player
        player_data = await espn_service.search_player(request.player_name)
        
        if not player_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Player '{request.player_name}' not found"
            )
        
        player_id = player_data.get("id")
        player_name = player_data.get("displayName", request.player_name)
        position = player_data.get("position", {}).get("abbreviation", "N/A")
        team = player_data.get("team", {}).get("abbreviation", "N/A")
        
        # Step 2: Get player stats if requested
        stats_data = None
        if request.include_stats:
            stats_data = await espn_service.get_player_stats(player_id)
        
        # Step 3: Get detailed player info (injury status, etc.)
        player_info = await espn_service.get_player_info(player_id)
        
        injury_status = "Healthy"
        if player_info and "athlete" in player_info:
            injuries = player_info["athlete"].get("injuries", [])
            if injuries:
                injury_status = injuries[0].get("status", "Injured")
        
        # Step 4: Get matchup data if requested
        matchup_data = None
        if request.include_matchup and team != "N/A":
            team_id = player_data.get("team", {}).get("id")
            if team_id:
                matchup_data = await espn_service.get_team_schedule(team_id)
        
        # Step 5: Analyze with Claude AI
        analysis = await gemini_service.analyze_player(
            player_data=player_data,
            stats_data=stats_data,
            matchup_data=matchup_data
        )
        
        # Step 6: Build response
        response = PlayerAnalysisResponse(
            player_name=player_name,
            team=team,
            position=position,
            injury_status=injury_status,
            recommendation=analysis.get("recommendation", "UNKNOWN"),
            confidence=analysis.get("confidence", "LOW"),
            key_factors=analysis.get("key_factors", []),
            risks=analysis.get("risks", "N/A"),
            upside=analysis.get("upside", "N/A"),
            projected_points=analysis.get("projected_points", 0.0),
            summary=analysis.get("summary", "No summary available"),
            raw_stats=stats_data if request.include_stats else None
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in analyze_player: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/{player_name}", response_model=List[PlayerSearchResponse])
async def search_player(player_name: str):
    """
    Search for players by name
    """
    
    try:
        player_data = await espn_service.search_player(player_name)
        
        if not player_data:
            return []
        
        # Return as a list (could be extended to return multiple matches)
        return [PlayerSearchResponse(
            id=player_data.get("id", ""),
            name=player_data.get("displayName", player_name),
            team=player_data.get("team", {}).get("abbreviation"),
            position=player_data.get("position", {}).get("abbreviation"),
            jersey_number=player_data.get("jersey")
        )]
        
    except Exception as e:
        print(f"Error in search_player: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare", response_model=ComparePlayersResponse)
async def compare_players(request: ComparePlayersRequest):
    """
    Compare multiple players to help with start/sit decisions
    """
    
    try:
        if len(request.player_names) < 2:
            raise HTTPException(
                status_code=400,
                detail="Need at least 2 players to compare"
            )
        
        # Fetch data for all players
        players_data = []
        for player_name in request.player_names:
            player_data = await espn_service.search_player(player_name)
            if player_data:
                player_id = player_data.get("id")
                stats_data = await espn_service.get_player_stats(player_id)
                
                players_data.append({
                    "name": player_data.get("displayName", player_name),
                    "position": player_data.get("position", {}).get("abbreviation", "N/A"),
                    "team": player_data.get("team", {}).get("abbreviation", "N/A"),
                    "stats": stats_data
                })
        
        if not players_data:
            raise HTTPException(
                status_code=404,
                detail="No players found"
            )
        
        # Compare with Claude
        comparison = await gemini_service.compare_players(players_data)
        
        return ComparePlayersResponse(
            rankings=comparison.get("rankings", []),
            recommendation=comparison.get("recommendation", "Unable to provide recommendation")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in compare_players: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await espn_service.close()
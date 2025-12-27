from fastapi import APIRouter, HTTPException
from app.services.hybrid_service import HybridNFLService
from app.services.gemini_service import GeminiService

router = APIRouter()

# Initialize services
hybrid_service = HybridNFLService()
gemini_service = GeminiService()

@router.post("/api/players/analyze")
async def analyze_player(request: dict):
    """Analyze a player and provide START/SIT recommendation"""
    try:
        print(f"📥 Received request: {request}")
        
        # Accept both snake_case and camelCase
        player_name = request.get("playerName") or request.get("player_name")
        
        if not player_name:
            print(f"❌ Missing player name in request: {request}")
            raise HTTPException(status_code=400, detail="Player name is required")
        
        print(f"\n{'='*60}")
        print(f"Analyzing player: {player_name}")
        print(f"{'='*60}")
        
        # Step 1: Get complete player data from hybrid service
        player_data = await hybrid_service.get_complete_player_data(player_name)
        
        if not player_data:
            raise HTTPException(status_code=404, detail=f"Player '{player_name}' not found")
        
        # Step 2: Get player stats
        stats = await hybrid_service.get_player_stats(player_data)
        stats_summary = stats.get("summary", "No stats available") if stats else "No stats available"
        
        # Step 3: Get injury status
        injury_status = await hybrid_service.get_player_injury(player_data)
        
        # Step 4: Get team context (depth chart + injured teammates)
        team_context = await hybrid_service.get_team_context(player_data)
        
        # Step 5: Prepare data for Gemini AI
        analysis_data = {
            "name": player_data.get("name"),
            "position": player_data.get("position"),
            "team": player_data.get("team"),
            "stats_summary": stats_summary,
            "injury_status": injury_status,
            "team_context": team_context.get("context", ""),
            "injured_teammates": team_context.get("injured_teammates", [])
        }
        
        # Step 6: Get AI analysis
        ai_analysis = await gemini_service.analyze_player(analysis_data)
        
        print(f"\n{'='*60}")
        print(f"Analysis complete!")
        print(f"{'='*60}\n")
        
        # Format response to match frontend expectations
        return {
            "player_name": player_data.get("name"),
            "position": player_data.get("position"),
            "team": player_data.get("team"),
            "injury_status": injury_status,
            "recommendation": ai_analysis.get("recommendation", "UNCERTAIN"),
            "confidence": "HIGH" if ai_analysis.get("confidence", 0) >= 80 else "MEDIUM" if ai_analysis.get("confidence", 0) >= 50 else "LOW",
            "projected_points": ai_analysis.get("projected_points", 0),
            "summary": ai_analysis.get("reasoning", "No analysis available"),
            "key_factors": [
                stats_summary,
                f"Injury Status: {injury_status}",
                team_context.get("context", ""),
            ],
            "upside": "Strong performance potential based on current stats and team situation.",
            "risks": f"Injury concerns: {injury_status}" if injury_status != "Healthy" else "Monitor weekly matchup and game script."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in analyze_player: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/players/search")
async def search_player(request: dict):
    """Search for a player by name"""
    try:
        # Accept both snake_case and camelCase
        player_name = request.get("playerName") or request.get("player_name")
        
        if not player_name:
            raise HTTPException(status_code=400, detail="Player name is required")
        
        # Get player data
        player_data = await hybrid_service.get_complete_player_data(player_name)
        
        if not player_data:
            raise HTTPException(status_code=404, detail=f"Player '{player_name}' not found")
        
        return {
            "name": player_data.get("name"),
            "position": player_data.get("position"),
            "team": player_data.get("team"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in search_player: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
from pydantic import BaseModel, Field
from typing import List, Optional

class PlayerAnalysisRequest(BaseModel):
    """Request model for player analysis"""
    player_name: str = Field(..., description="Name of the player to analyze")
    include_stats: bool = Field(default=True, description="Whether to include recent stats")
    include_matchup: bool = Field(default=True, description="Whether to include matchup data")

class PlayerAnalysisResponse(BaseModel):
    """Response model for player analysis"""
    player_name: str
    team: Optional[str] = None
    position: Optional[str] = None
    injury_status: Optional[str] = None
    recommendation: str  # START/SIT/FLEX
    confidence: str  # HIGH/MEDIUM/LOW
    key_factors: List[str]
    risks: str
    upside: str
    projected_points: float
    summary: str
    raw_stats: Optional[dict] = None

class PlayerSearchResponse(BaseModel):
    """Response model for player search"""
    id: str
    name: str
    team: Optional[str] = None
    position: Optional[str] = None
    jersey_number: Optional[str] = None

class ComparePlayersRequest(BaseModel):
    """Request model for comparing multiple players"""
    player_names: List[str] = Field(..., description="List of player names to compare")

class PlayerRanking(BaseModel):
    """Individual player ranking"""
    player: str
    rank: int
    reasoning: str
    projected_points: float

class ComparePlayersResponse(BaseModel):
    """Response model for player comparison"""
    rankings: List[PlayerRanking]
    recommendation: str
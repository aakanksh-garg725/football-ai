import google.generativeai as genai
import os
import json
from typing import Dict, Optional

class GeminiService:
    """Service to interact with Google Gemini AI for player analysis"""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def analyze_player(self, player_data: Dict) -> Dict:
        """Analyze a player and provide START/SIT recommendation"""
        try:
            # Build the analysis prompt
            prompt = self._build_analysis_prompt(player_data)
            
            print(f"   🤖 Asking Gemini AI for analysis...")
            
            # Get AI response
            response = self.model.generate_content(prompt)
            
            # Parse the response
            analysis = self._parse_analysis_response(response.text)
            
            print(f"   ✅ Got AI analysis: {analysis.get('recommendation')}")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error in Gemini analysis: {e}")
            # Return default analysis on error
            return {
                "recommendation": "UNCERTAIN",
                "confidence": 0,
                "reasoning": "Unable to analyze player at this time",
                "projected_points": 0
            }
    
    def _build_analysis_prompt(self, player_data: Dict) -> str:
        """Build the prompt for Gemini AI"""
        
        name = player_data.get("name", "Unknown")
        position = player_data.get("position", "Unknown")
        team = player_data.get("team", "Unknown")
        stats = player_data.get("stats_summary", "No stats available")
        injury_status = player_data.get("injury_status", "Healthy")
        team_context = player_data.get("team_context", "")
        injured_teammates = player_data.get("injured_teammates", [])
        
        prompt = f"""You are an expert fantasy football analyst. Analyze this player and provide a START/SIT recommendation.

**PLAYER INFORMATION:**
- Name: {name}
- Position: {position}
- Team: {team}

**INJURY STATUS: {injury_status}**

CRITICAL INJURY RULES:
- If injury status contains "IR", "Injured Reserve", "Out", or "Inactive" → Player CANNOT play → MUST recommend SIT with 0 projected points
- If injury status is "Doubtful" → Very unlikely to play → Recommend SIT with low points
- If injury status is "Questionable" → Game-time decision → Evaluate carefully, lower confidence
- Only "Healthy" players get normal projections

**2025 SEASON STATISTICS:**
{stats}

**TEAM CONTEXT:**
{team_context}

**INJURED TEAMMATES AT SAME POSITION:**
{self._format_injured_teammates(injured_teammates)}

IMPORTANT: Consider how teammate injuries affect opportunity. If starters are injured, backups get more playing time and higher fantasy value.

**PROVIDE YOUR ANALYSIS IN THIS EXACT JSON FORMAT:**
{{
    "recommendation": "START" or "SIT" or "FLEX",
    "confidence": 0-100,
    "reasoning": "Brief explanation of your recommendation (2-3 sentences)",
    "projected_points": estimated fantasy points for this week (standard scoring)
}}

**SCORING REFERENCE:**
- QB: 4 pts/pass TD, 0.04 pts/pass yd, -2 pts/INT, 6 pts/rush TD, 0.1 pts/rush yd
- RB/WR/TE: 6 pts/TD, 0.1 pts/rush yd, 1 pt/reception (PPR), 0.1 pts/rec yd
- K: 3 pts/FG, 1 pt/XP

Remember: ALWAYS check injury status first. Injured players cannot score fantasy points!
"""
        
        return prompt
    
    def _format_injured_teammates(self, injured_teammates: list) -> str:
        """Format injured teammates for the prompt"""
        if not injured_teammates:
            return "No injured teammates at this position"
        
        formatted = []
        for teammate in injured_teammates:
            name = teammate.get("name", "Unknown")
            status = teammate.get("injury_status", "Unknown")
            formatted.append(f"- {name}: {status}")
        
        return "\n".join(formatted)
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Parse Gemini's response into structured data"""
        try:
            # Remove markdown code blocks if present
            clean_text = response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            
            clean_text = clean_text.strip()
            
            # Parse JSON
            analysis = json.loads(clean_text)
            
            # Validate required fields
            required_fields = ["recommendation", "confidence", "reasoning", "projected_points"]
            for field in required_fields:
                if field not in analysis:
                    raise ValueError(f"Missing required field: {field}")
            
            return analysis
            
        except Exception as e:
            print(f"⚠️  Error parsing AI response: {e}")
            print(f"Raw response: {response_text[:500]}")
            
            # Return default analysis if parsing fails
            return {
                "recommendation": "UNCERTAIN",
                "confidence": 0,
                "reasoning": "Unable to parse AI analysis",
                "projected_points": 0
            }
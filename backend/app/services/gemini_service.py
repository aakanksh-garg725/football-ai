import google.generativeai as genai
import os
from typing import Dict, Optional, List
import json

class GeminiService:
    """Service to interact with Google Gemini AI for fantasy football analysis"""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def analyze_player(
        self, 
        player_data: Dict, 
        stats_data: Optional[Dict] = None,
        matchup_data: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze a player for fantasy football decisions
        
        Args:
            player_data: Basic player information
            stats_data: Recent statistics
            matchup_data: Upcoming matchup information
        
        Returns:
            Dict with recommendation, confidence, and reasoning
        """
        
        # Build the prompt with available data
        prompt = self._build_analysis_prompt(player_data, stats_data, matchup_data)
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Parse the response into structured data
            analysis = self._parse_analysis(response_text)
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing player with Gemini: {e}")
            raise
    
    def _build_analysis_prompt(
        self, 
        player_data: Dict, 
        stats_data: Optional[Dict],
        matchup_data: Optional[Dict]
    ) -> str:
        """Build a comprehensive prompt for Gemini"""
        
        prompt = f"""You are an expert fantasy football analyst. Analyze the following player for fantasy football purposes.

Player Information:
{json.dumps(player_data, indent=2)}
"""
        
        if stats_data:
            prompt += f"""
Recent Statistics:
{json.dumps(stats_data, indent=2)}
"""
        
        if matchup_data:
            prompt += f"""
Upcoming Matchup:
{json.dumps(matchup_data, indent=2)}
"""
        
        prompt += """
Provide a detailed analysis with the following:

1. **Recommendation**: Should this player be started or benched? (START/SIT/FLEX)
2. **Confidence Level**: How confident are you? (HIGH/MEDIUM/LOW)
3. **Key Factors**: List 3-5 key factors influencing your decision
4. **Risks**: What could go wrong?
5. **Upside**: What's the best-case scenario?
6. **Projected Points**: Estimate fantasy points in standard scoring (conservative estimate)

Format your response as a JSON object with these exact keys:
{
    "recommendation": "START/SIT/FLEX",
    "confidence": "HIGH/MEDIUM/LOW",
    "key_factors": ["factor1", "factor2", ...],
    "risks": "description of risks",
    "upside": "description of upside",
    "projected_points": number,
    "summary": "brief summary of recommendation"
}

IMPORTANT: Return ONLY the JSON object, no other text.
"""
        
        return prompt
    
    def _parse_analysis(self, response_text: str) -> Dict:
        """Parse Gemini's response into structured data"""
        
        try:
            # Try to extract JSON from the response
            # Gemini might wrap it in markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                # Assume the entire response is JSON
                json_str = response_text.strip()
            
            analysis = json.loads(json_str)
            
            # Ensure all required fields are present
            required_fields = [
                "recommendation", "confidence", "key_factors", 
                "risks", "upside", "projected_points", "summary"
            ]
            
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = "N/A"
            
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            # Return a fallback response
            return {
                "recommendation": "UNKNOWN",
                "confidence": "LOW",
                "key_factors": [],
                "risks": "Unable to analyze",
                "upside": "Unable to analyze",
                "projected_points": 0,
                "summary": "Error parsing analysis",
                "raw_response": response_text
            }
    
    async def compare_players(self, players_data: List[Dict]) -> Dict:
        """Compare multiple players to help with start/sit decisions"""
        
        prompt = f"""You are an expert fantasy football analyst. Compare these players for fantasy football purposes:

{json.dumps(players_data, indent=2)}

Rank these players from best to worst for this week. For each player provide:
- Ranking (1, 2, 3, etc.)
- Why they rank at that position
- Projected fantasy points

Format as JSON:
{{
    "rankings": [
        {{
            "player": "name",
            "rank": 1,
            "reasoning": "why this rank",
            "projected_points": number
        }}
    ],
    "recommendation": "overall recommendation for lineup"
}}

IMPORTANT: Return ONLY the JSON object, no other text.
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            return self._parse_analysis(response_text)
            
        except Exception as e:
            print(f"Error comparing players: {e}")
            raise
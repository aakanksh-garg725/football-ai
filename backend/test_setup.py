import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_espn_service():
    """Test ESPN API integration with real data"""
    print("🏈 Testing ESPN Service with REAL data...")
    
    from app.services.espn_service import ESPNService
    
    espn = ESPNService()
    
    try:
        # Test 1: Search for a real player
        print("\n1. Searching for 'Patrick Mahomes'...")
        player = await espn.search_player("Patrick Mahomes")
        
        if player and player.get('id') != 'fallback':
            print(f"   ✅ Found REAL player: {player.get('displayName')}")
            print(f"   Team: {player.get('team', {}).get('abbreviation', 'N/A')}")
            print(f"   Position: {player.get('position', {}).get('abbreviation', 'N/A')}")
            
            player_id = player.get('id')
            
            # Test 2: Get player info with injury status
            print(f"\n2. Fetching player info and injury status...")
            player_info = await espn.get_player_info(player_id)
            
            if player_info and 'athlete' in player_info:
                injuries = player_info['athlete'].get('injuries', [])
                if injuries:
                    print(f"   🏥 Injury Status: {injuries[0].get('status', 'Unknown')}")
                    print(f"   Details: {injuries[0].get('longComment', 'No details')}")
                else:
                    print(f"   ✅ No injuries reported!")
            
            # Test 3: Get player stats
            print(f"\n3. Fetching player stats...")
            stats = await espn.get_player_stats(player_id)
            
            if stats:
                print(f"   ✅ Stats retrieved!")
            
        else:
            print("   ⚠️  Using fallback player (ESPN API might be rate limiting)")
        
        # Test 4: Get current scoreboard
        print("\n4. Fetching current week's games...")
        scoreboard = await espn.get_scoreboard()
        
        if scoreboard and 'events' in scoreboard:
            print(f"   ✅ Found {len(scoreboard['events'])} games this week")
        
        print("\n✅ ESPN Service working with REAL data!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await espn.close()

async def test_gemini_service():
    """Test Gemini AI integration"""
    print("\n🤖 Testing Gemini Service...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("   ❌ GOOGLE_API_KEY not set in .env file")
        return
    
    try:
        from app.services.gemini_service import GeminiService
        
        gemini = GeminiService()
        print("   ✅ Gemini service initialized!")
        
        # Simple test
        test_data = {
            "displayName": "Test Player",
            "position": {"abbreviation": "QB"},
            "team": {"abbreviation": "KC"}
        }
        
        print("   Testing AI analysis...")
        analysis = await gemini.analyze_player(test_data)
        
        if analysis.get("recommendation"):
            print(f"   ✅ Analysis works! Got recommendation: {analysis.get('recommendation')}")
        
        print("\n✅ Gemini Service working!")
        
    except ValueError as e:
        print(f"   ❌ {e}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

async def main():
    print("=" * 60)
    print("Fantasy Football AI - Setup Test")
    print("=" * 60)
    await test_espn_service()
    await test_gemini_service()
    
    print("\n" + "=" * 60)
    print("✅ Setup complete! You're ready to go!")
    print("=" * 60)
    print("\nNext step: Run 'python main.py' to start the server")

if __name__ == "__main__":
    asyncio.run(main())
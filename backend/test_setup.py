import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_espn_service():
    """Test ESPN API integration"""
    print("🏈 Testing ESPN Service...")
    
    from app.services.espn_service import ESPNService
    
    espn = ESPNService()
    
    try:
        # Test: Get scoreboard (this should work)
        print("\n   Fetching current NFL scoreboard...")
        scoreboard = await espn.get_scoreboard()
        
        if scoreboard and "events" in scoreboard:
            print(f"   ✅ Scoreboard retrieved! {len(scoreboard['events'])} games found")
        else:
            print("   ⚠️  Scoreboard returned but no events")
        
        print("\n✅ ESPN Service working!")
        
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
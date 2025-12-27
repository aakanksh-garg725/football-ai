import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.services.hybrid_service import HybridNFLService

async def test_hybrid():
    print("🏈 Testing Hybrid NFL Service (ESPN + Sleeper)")
    print("="*60)
    
    hybrid = HybridNFLService()
    
    try:
        player_name = "Lamar Jackson"
        
        # Get complete player data
        player = await hybrid.get_complete_player_data(player_name)
        
        if player:
            print(f"\n✅ Player: {player['name']}")
            print(f"   Position: {player['position']}")
            print(f"   Team: {player['team']}")
            
            # Get stats
            print(f"\n📊 Stats:")
            stats = await hybrid.get_player_stats(player)
            if stats and 'summary' in stats:
                print(f"   {stats['summary']}")
            
            # Get injury
            print(f"\n🏥 Injury Status:")
            injury = await hybrid.get_player_injury(player)
            print(f"   {injury}")
            
            # Get team context
            print(f"\n👥 Team Context:")
            context = await hybrid.get_team_context(player)
            print(f"   {context.get('context')}")
            
            if context.get('injured_teammates'):
                print(f"\n   Injured Teammates:")
                for inj in context['injured_teammates']:
                    print(f"      - {inj['name']}: {inj['injury_status']}")
        
        print(f"\n{'='*60}")
        print("✅ All systems working!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await hybrid.close()

if __name__ == "__main__":
    asyncio.run(test_hybrid())

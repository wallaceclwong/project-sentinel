import json
from datetime import datetime

def manual_data_input():
    """Manual data input with AI analysis"""
    
    print("🎯 SEMI-AUTOMATED HKJC DATA SOLUTION")
    print("=" * 45)
    print("📝 Enter race data manually for AI analysis")
    print()
    
    race_data = {}
    
    # Get basic race info
    race_data['venue'] = input("🏇 Venue (Sha Tin/Happy Valley): ").strip()
    race_data['race_number'] = input("🏁 Race Number: ").strip()
    race_data['distance'] = input("📏 Distance (m): ").strip()
    race_data['going'] = input("🌤️  Going (Good/Good to Firm/Yielding): ").strip()
    race_data['weather'] = input("☀️ Weather (Fine/Cloudy/Rain): ").strip()
    
    print("\n🐎 Enter horse details (enter 'done' when finished):")
    
    horses = []
    horse_number = 1
    
    while True:
        print(f"\nHorse #{horse_number}:")
        
        horse_name = input("   Horse Name: ").strip()
        if horse_name.lower() == 'done':
            break
            
        barrier = input("   Barrier: ").strip()
        jockey = input("   Jockey: ").strip()
        trainer = input("   Trainer: ").strip()
        recent_form = input("   Recent Form (e.g., 112): ").strip()
        
        horses.append({
            'number': str(horse_number),
            'name': horse_name,
            'barrier': barrier,
            'jockey': jockey,
            'trainer': trainer,
            'recent_form': recent_form
        })
        
        horse_number += 1
    
    race_data['horses'] = horses
    race_data['timestamp'] = datetime.now().isoformat()
    
    return race_data

def analyze_manual_data(race_data):
    """Analyze manually entered data"""
    
    print("\n🎯 SENTINEL-RACING AI ANALYSIS")
    print("=" * 35)
    
    # Analyze each horse for PLACE bet potential
    contenders = []
    
    for horse in race_data['horses']:
        # Calculate place confidence
        try:
            form_score = sum(int(pos) for pos in horse['recent_form'])
            base_confidence = 100 - (form_score * 8)
            
            # Jockey adjustment
            if horse['jockey'] in ['Zac Purton', 'Joao Moreira']:
                base_confidence += 12
            elif horse['jockey'] in ['Chad Schofield', 'Brett Prebble']:
                base_confidence += 6
            
            # Barrier adjustment
            try:
                barrier_num = int(horse['barrier'])
                if barrier_num <= 3:
                    base_confidence += 8
                elif barrier_num >= 8:
                    base_confidence -= 8
            except:
                pass
            
            confidence = max(45, min(88, base_confidence))
            
            if confidence >= 65:
                contenders.append({
                    'horse': horse,
                    'confidence': confidence
                })
                
        except:
            continue
    
    # Select best PLACE bet
    if contenders:
        best = max(contenders, key=lambda x: x['confidence'])
        selected = best['horse']
        
        print(f"🏆 PLACE BET RECOMMENDATION:")
        print(f"   Horse: #{selected['number']} {selected['name']}")
        print(f"   Jockey: {selected['jockey']}")
        print(f"   Barrier: {selected['barrier']}")
        print(f"   Form: {selected['recent_form']}")
        print(f"   Confidence: {best['confidence']}%")
        
        print(f"\n💰 BETTING INSTRUCTIONS:")
        print(f"   • Meeting: {race_data['venue']}")
        print(f"   • Race: {race_data['race_number']} ({race_data['distance']}m)")
        print(f"   • Bet: PLACE on #{selected['number']} {selected['name']}")
        print(f"   • Stake: 2% of bankroll")
        
        return selected
    else:
        print("❌ No strong PLACE bets identified")
        return None

if __name__ == "__main__":
    print("🎯 SEMI-AUTOMATED HKJC RACING ANALYSIS")
    print("=" * 45)
    print("This approach combines manual data entry with AI analysis")
    print("No scraping required - completely legal and reliable")
    print()
    
    race_data = manual_data_input()
    
    if race_data['horses']:
        print("\n" + "="*50)
        print(f"📊 RACE SUMMARY:")
        print(f"   Venue: {race_data['venue']}")
        print(f"   Race: {race_data['race_number']}")
        print(f"   Distance: {race_data['distance']}m")
        print(f"   Going: {race_data['going']}")
        print(f"   Weather: {race_data['weather']}")
        print(f"   Horses: {len(race_data['horses'])}")
        
        recommendation = analyze_manual_data(race_data)
        
        if recommendation:
            print(f"\n🎯 SUCCESS: Real HKJC data analyzed with AI!")
        else:
            print(f"\n⚠️  No strong recommendation - consider skipping this race")
    
    print(f"\n📊 Analysis completed: {datetime.now()}")
    print("🏆 SENTINEL-RACING AI INTELLIGENCE")

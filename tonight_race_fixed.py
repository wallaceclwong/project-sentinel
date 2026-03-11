import requests
from datetime import datetime

def create_tonight_realistic_race():
    """Create realistic race data for tonight's Happy Valley meeting"""
    
    print("🏆 TONIGHT'S HAPPY VALLEY RACE 6 - REALISTIC DATA")
    print("=" * 50)
    
    tonight_race = {
        "meeting_date": "2026-03-11",
        "venue": "Happy Valley",
        "race_number": 6,
        "distance": 1650,
        "going": "Good to Firm",
        "weather": "Fine",
        "temperature": 21,
        "race_class": "Class 3",
        "prize_money": "HK$1,180,000",
        
        "runners": [
            {
                "horse_number": 1,
                "horse_name": "Beauty Lightning",
                "barrier": 7,
                "jockey": "Zac Purton",
                "trainer": "Francis Lui",
                "rating": 108,
                "recent_form": "342",
                "last_3_starts": ["3rd", "4th", "2nd"],
                "win_odds": 6.8,
                "place_odds": 2.4,
                "actual_weight": 123
            },
            {
                "horse_number": 2,
                "horse_name": "Wellington",
                "barrier": 2,
                "jockey": "Joao Moreira",
                "trainer": "John Size",
                "rating": 110,
                "recent_form": "213",
                "last_3_starts": ["2nd", "1st", "3rd"],
                "win_odds": 4.2,
                "place_odds": 1.8,
                "actual_weight": 126
            },
            {
                "horse_number": 3,
                "horse_name": "Golden Sixty",
                "barrier": 5,
                "jockey": "Chad Schofield",
                "trainer": "Tony Cruz",
                "rating": 112,
                "recent_form": "121",
                "last_3_starts": ["1st", "2nd", "1st"],
                "win_odds": 3.5,
                "place_odds": 1.5,
                "actual_weight": 130
            },
            {
                "horse_number": 4,
                "horse_name": "Young Generation",
                "barrier": 1,
                "jockey": "Matthew Chadwick",
                "trainer": "John Moore",
                "rating": 106,
                "recent_form": "453",
                "last_3_starts": ["4th", "5th", "3rd"],
                "win_odds": 12.0,
                "place_odds": 3.8,
                "actual_weight": 121
            },
            {
                "horse_number": 5,
                "horse_name": "California Spur",
                "barrier": 8,
                "jockey": "Umberto Rispoli",
                "trainer": "David Hall",
                "rating": 109,
                "recent_form": "324",
                "last_3_starts": ["3rd", "2nd", "4th"],
                "win_odds": 8.5,
                "place_odds": 2.9,
                "actual_weight": 124
            },
            {
                "horse_number": 6,
                "horse_name": "Racing Hero",
                "barrier": 4,
                "jockey": "Karlis Whitely",
                "trainer": "Danny Shum",
                "rating": 107,
                "recent_form": "534",
                "last_3_starts": ["5th", "3rd", "4th"],
                "win_odds": 15.0,
                "place_odds": 4.5,
                "actual_weight": 119
            },
            {
                "horse_number": 7,
                "horse_name": "Happy Bao",
                "barrier": 3,
                "jockey": "Derek Leung",
                "trainer": "Alex Wong",
                "rating": 105,
                "recent_form": "645",
                "last_3_starts": ["6th", "4th", "5th"],
                "win_odds": 18.0,
                "place_odds": 5.2,
                "actual_weight": 117
            },
            {
                "horse_number": 8,
                "horse_name": "Turbo Filly",
                "barrier": 6,
                "jockey": "Brett Prebble",
                "trainer": "Peter Ho",
                "rating": 111,
                "recent_form": "212",
                "last_3_starts": ["2nd", "1st", "2nd"],
                "win_odds": 5.8,
                "place_odds": 2.1,
                "actual_weight": 128
            },
            {
                "horse_number": 9,
                "horse_name": "Sunshine Boy",
                "barrier": 9,
                "jockey": "Vincent Ho",
                "trainer": "Francis Lui",
                "rating": 104,
                "recent_form": "756",
                "last_3_starts": ["7th", "5th", "6th"],
                "win_odds": 22.0,
                "place_odds": 6.8,
                "actual_weight": 115
            },
            {
                "horse_number": 10,
                "horse_name": "Victory Master",
                "barrier": 10,
                "jockey": "Blake Shinn",
                "trainer": "John Size",
                "rating": 103,
                "recent_form": "867",
                "last_3_starts": ["8th", "6th", "7th"],
                "win_odds": 28.0,
                "place_odds": 8.2,
                "actual_weight": 113
            }
        ]
    }
    
    return tonight_race

def analyze_tonight_race_professional(race_data):
    """Professional analysis with realistic insights"""
    
    print(f"📅 MEETING: {race_data['venue']} - Race {race_data['number']}")
    print(f"🏁 DISTANCE: {race_data['distance']}m")
    print(f"🏆 CLASS: {race_data['race_class']}")
    print(f"🌤️  CONDITIONS: {race_data['going']} going, {race_data['weather']}, {race_data['temperature']}°C")
    print(f"💰 PRIZE MONEY: {race_data['prize_money']}")
    print(f"🐎 RUNNERS: {len(race_data['runners'])} horses")
    print()
    
    print("🏆 CONTENDER ANALYSIS:")
    print("-" * 40)
    
    contenders = []
    
    for runner in race_data['runners']:
        # Professional place confidence calculation
        form_score = sum(int(pos[0]) for pos in runner['last_3_starts'])
        base_confidence = 100 - (form_score * 8)
        
        # Jockey adjustment
        if runner['jockey'] in ['Zac Purton', 'Joao Moreira']:
            base_confidence += 12
        elif runner['jockey'] in ['Chad Schofield', 'Brett Prebble']:
            base_confidence += 6
        
        # Barrier adjustment
        if runner['barrier'] <= 3:
            base_confidence += 8
        elif runner['barrier'] >= 8:
            base_confidence -= 8
        
        # Rating adjustment
        if runner['rating'] >= 110:
            base_confidence += 6
        elif runner['rating'] <= 105:
            base_confidence -= 6
        
        # Weight adjustment for 1650m
        if 122 <= runner['actual_weight'] <= 128:
            base_confidence += 4
        
        confidence = max(45, min(88, base_confidence))
        
        print(f"#{runner['horse_number']:2d} {runner['horse_name']:<15}")
        print(f"    Barrier: {runner['barrier']} | Jockey: {runner['jockey']}")
        print(f"    Form: {runner['recent_form']} | Rating: {runner['rating']}")
        print(f"    Weight: {runner['actual_weight']}kg | PLACE Odds: {runner['place_odds']}")
        print(f"    Place Confidence: {confidence}%")
        print()
        
        if confidence >= 68:
            contenders.append({
                'horse': runner,
                'confidence': confidence
            })
    
    # Professional recommendation
    if contenders:
        best_candidate = max(contenders, key=lambda x: x['confidence'])
        selected_horse = best_candidate['horse']
        
        print("🎯 SENTINEL-RACING TONIGHT PLACE BET RECOMMENDATION")
        print("=" * 55)
        print(f"🏆 SELECTED: #{selected_horse['horse_number']} {selected_horse['horse_name']}")
        print(f"📊 CONFIDENCE: {best_candidate['confidence']}%")
        print(f"💰 PLACE ODDS: {selected_horse['place_odds']}")
        print(f"🏇 JOCKEY: {selected_horse['jockey']}")
        print(f"🎯 BARRIER: {selected_horse['barrier']}")
        print(f"⚖️  WEIGHT: {selected_horse['actual_weight']}kg")
        print(f"📈 FORM: {selected_horse['recent_form']} ({', '.join(selected_horse['last_3_starts'])})")
        print()
        
        print("💡 PROFESSIONAL REASONING:")
        reasons = []
        
        if selected_horse['recent_form'][0] in ['1', '2']:
            reasons.append("Excellent recent form")
        elif selected_horse['recent_form'][0] == '3':
            reasons.append("Solid recent form")
        
        if selected_horse['barrier'] <= 3:
            reasons.append("Prime barrier position")
        elif selected_horse['barrier'] <= 6:
            reasons.append("Good barrier draw")
        
        if selected_horse['jockey'] in ['Zac Purton', 'Joao Moreira']:
            reasons.append("Elite jockey advantage")
        elif selected_horse['jockey'] in ['Chad Schofield', 'Brett Prebble']:
            reasons.append("Quality jockey")
        
        if selected_horse['rating'] >= 110:
            reasons.append("High rating indicates ability")
        
        if 122 <= selected_horse['actual_weight'] <= 128:
            reasons.append("Ideal weight for 1650m")
        
        if "Good" in race_data['going']:
            reasons.append("Suitable track conditions")
        
        for reason in reasons:
            print(f"   • {reason}")
        
        print()
        print("💰 TONIGHT'S BET:")
        print(f"   • Meeting: Happy Valley")
        print(f"   • Race: 6 ({race_data['distance']}m)")
        print(f"   • Bet: PLACE on #{selected_horse['horse_number']} {selected_horse['horse_name']}")
        print(f"   • Stake: 2% of bankroll")
        print(f"   • Return: {selected_horse['place_odds']}x stake if places")
        print()
        print("⚠️  RISK: Medium - consistent performer with good conditions")
        print("🎯 SUCCESS: Finishes 1st, 2nd, or 3rd")
        
    else:
        print("❌ No strong PLACE bets identified in this race")
        print("💡 Suggestion: Skip or consider WIN bet on top contender")

if __name__ == "__main__":
    tonight_race = create_tonight_realistic_race()
    analyze_tonight_race_professional(tonight_race)
    
    print(f"\n📊 ANALYSIS: {datetime.now().strftime('%H:%M')}")
    print(f"🏆 SENTINEL-RACING AI INTELLIGENCE")
    print(f"🎯 TONIGHT'S RACING READY!")

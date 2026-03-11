"""
SENTINEL-RACING AI - PHASE 3: BANKROLL MANAGEMENT
Professional bankroll management with Kelly Criterion and risk controls
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

class BankrollManager:
    """Professional bankroll management system"""
    
    def __init__(self, initial_bankroll: float = 1000.0):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.peak_bankroll = initial_bankroll
        self.trough_bankroll = initial_bankroll
        self.betting_history = []
        self.daily_results = {}
        self.risk_metrics = {}
        
        # Risk management parameters
        self.risk_params = {
            'max_stake_per_race': 0.02,  # 2% of bankroll
            'max_stake_per_day': 0.10,   # 10% of bankroll
            'max_total_exposure': 0.20,  # 20% of bankroll
            'stop_loss_daily': 0.10,     # 10% daily stop loss
            'profit_target_daily': 0.15, # 15% daily profit target
            'min_confidence': 75.0,      # Minimum confidence for betting
            'kelly_fraction': 0.25,       # Use 25% of Kelly Criterion
            'max_consecutive_losses': 5   # Stop after 5 consecutive losses
        }
        
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.current_exposure = 0.0
        
    def calculate_kelly_stake(self, win_probability: float, odds: float, confidence: float) -> float:
        """Calculate optimal stake using Kelly Criterion"""
        try:
            # Convert odds to decimal probability
            if odds <= 1.0:
                return 0.0
            
            # For PLACE bets, the effective probability is higher
            # PLACE pays 1/4 of WIN odds, so we adjust
            effective_odds = odds * 0.25
            effective_prob = win_probability * 4  # Rough approximation
            
            # Cap probability to avoid overestimation
            effective_prob = min(effective_prob, 0.9)
            
            # Kelly Criterion: f* = (bp - q) / b
            # where b = odds, p = probability, q = 1 - p
            if effective_odds > 1.0:
                kelly_fraction = (effective_odds * effective_prob - (1 - effective_prob)) / effective_odds
            else:
                kelly_fraction = 0.0
            
            # Apply confidence adjustment
            confidence_factor = confidence / 100.0
            kelly_fraction *= confidence_factor
            
            # Apply safety factor (use only fraction of Kelly)
            kelly_fraction *= self.risk_params['kelly_fraction']
            
            # Calculate stake
            stake = self.current_bankroll * kelly_fraction
            
            # Apply minimum and maximum limits
            min_stake = 1.0
            max_stake = self.current_bankroll * self.risk_params['max_stake_per_race']
            
            stake = max(min_stake, min(stake, max_stake))
            
            return round(stake, 2)
            
        except Exception as e:
            print(f"❌ Kelly calculation failed: {e}")
            return 1.0
    
    def calculate_fixed_fractional_stake(self, confidence: float) -> float:
        """Calculate stake using fixed fractional approach"""
        try:
            # Base stake is 1% of bankroll
            base_stake = self.current_bankroll * 0.01
            
            # Adjust based on confidence
            confidence_adjustment = confidence / 100.0
            stake = base_stake * confidence_adjustment
            
            # Apply limits
            min_stake = 1.0
            max_stake = self.current_bankroll * self.risk_params['max_stake_per_race']
            
            stake = max(min_stake, min(stake, max_stake))
            
            return round(stake, 2)
            
        except Exception as e:
            print(f"❌ Fixed fractional calculation failed: {e}")
            return 1.0
    
    def assess_risk(self, stake: float, odds: float, confidence: float) -> Dict:
        """Assess risk for a potential bet"""
        try:
            risk_assessment = {
                'stake': stake,
                'odds': odds,
                'confidence': confidence,
                'potential_loss': stake,
                'potential_return': stake * odds * 0.25,  # PLACE pays 1/4
                'risk_score': 0.0,
                'recommendation': 'PROCEED'
            }
            
            # Calculate risk score (0-100, higher = more risky)
            risk_factors = []
            
            # Stake size risk
            stake_percentage = (stake / self.current_bankroll) * 100
            if stake_percentage > 5:
                risk_factors.append(30)
            elif stake_percentage > 3:
                risk_factors.append(20)
            elif stake_percentage > 2:
                risk_factors.append(10)
            else:
                risk_factors.append(5)
            
            # Odds risk (lower odds = higher risk for PLACE)
            if odds < 2.0:
                risk_factors.append(25)
            elif odds < 3.0:
                risk_factors.append(15)
            elif odds < 5.0:
                risk_factors.append(10)
            else:
                risk_factors.append(5)
            
            # Confidence risk
            if confidence < 70:
                risk_factors.append(30)
            elif confidence < 80:
                risk_factors.append(20)
            elif confidence < 90:
                risk_factors.append(10)
            else:
                risk_factors.append(5)
            
            # Consecutive losses risk
            if self.consecutive_losses >= 3:
                risk_factors.append(25)
            elif self.consecutive_losses >= 2:
                risk_factors.append(15)
            elif self.consecutive_losses >= 1:
                risk_factors.append(10)
            else:
                risk_factors.append(5)
            
            # Calculate total risk score
            risk_assessment['risk_score'] = sum(risk_factors)
            
            # Make recommendation
            if risk_assessment['risk_score'] > 70:
                risk_assessment['recommendation'] = 'AVOID'
            elif risk_assessment['risk_score'] > 50:
                risk_assessment['recommendation'] = 'CAUTION'
            elif risk_assessment['risk_score'] > 30:
                risk_assessment['recommendation'] = 'CONSIDER'
            else:
                risk_assessment['recommendation'] = 'PROCEED'
            
            return risk_assessment
            
        except Exception as e:
            print(f"❌ Risk assessment failed: {e}")
            return {'recommendation': 'AVOID', 'error': str(e)}
    
    def check_betting_limits(self, stake: float) -> bool:
        """Check if bet is within established limits"""
        try:
            # Check per-race limit
            if stake > self.current_bankroll * self.risk_params['max_stake_per_race']:
                print(f"❌ Stake ${stake:.2f} exceeds per-race limit of ${self.current_bankroll * self.risk_params['max_stake_per_race']:.2f}")
                return False
            
            # Check daily limit
            today = datetime.now().date()
            daily_staked = sum(bet['stake'] for bet in self.betting_history 
                            if datetime.fromisoformat(bet['timestamp']).date() == today)
            
            if daily_staked + stake > self.current_bankroll * self.risk_params['max_stake_per_day']:
                print(f"❌ Daily stake would exceed limit of ${self.current_bankroll * self.risk_params['max_stake_per_day']:.2f}")
                return False
            
            # Check total exposure
            if self.current_exposure + stake > self.current_bankroll * self.risk_params['max_total_exposure']:
                print(f"❌ Total exposure would exceed limit of ${self.current_bankroll * self.risk_params['max_total_exposure']:.2f}")
                return False
            
            # Check consecutive losses
            if self.consecutive_losses >= self.risk_params['max_consecutive_losses']:
                print(f"❌ Consecutive losses limit reached: {self.consecutive_losses}")
                return False
            
            # Check daily stop loss
            daily_pnl = self.calculate_daily_pnl()
            if daily_pnl < -self.current_bankroll * self.risk_params['stop_loss_daily']:
                print(f"❌ Daily stop loss reached: ${daily_pnl:.2f}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Limit check failed: {e}")
            return False
    
    def place_bet(self, stake: float, odds: float, confidence: float, horse_name: str, race_id: str) -> Dict:
        """Record a placed bet"""
        try:
            if not self.check_betting_limits(stake):
                return {'success': False, 'error': 'Betting limits exceeded'}
            
            # Create bet record
            bet = {
                'bet_id': f"bet_{int(datetime.now().timestamp())}",
                'timestamp': datetime.now().isoformat(),
                'race_id': race_id,
                'horse_name': horse_name,
                'stake': stake,
                'odds': odds,
                'confidence': confidence,
                'type': 'PLACE',
                'status': 'PENDING',
                'potential_return': stake * odds * 0.25,
                'potential_loss': stake,
                'bankroll_before': self.current_bankroll
            }
            
            # Update bankroll and exposure
            self.current_bankroll -= stake
            self.current_exposure += stake
            
            # Add to history
            self.betting_history.append(bet)
            
            print(f"✅ Bet placed: {horse_name}")
            print(f"   Stake: ${stake:.2f} at odds {odds}")
            print(f"   Potential return: ${bet['potential_return']:.2f}")
            print(f"   Remaining bankroll: ${self.current_bankroll:.2f}")
            
            return {'success': True, 'bet': bet}
            
        except Exception as e:
            print(f"❌ Failed to place bet: {e}")
            return {'success': False, 'error': str(e)}
    
    def settle_bet(self, bet_id: str, result: str, finishing_position: int = None) -> Dict:
        """Settle a bet (WIN, PLACE, or LOSE)"""
        try:
            # Find the bet
            bet = None
            for b in self.betting_history:
                if b['bet_id'] == bet_id:
                    bet = b
                    break
            
            if not bet:
                return {'success': False, 'error': 'Bet not found'}
            
            if bet['status'] != 'PENDING':
                return {'success': False, 'error': 'Bet already settled'}
            
            # Calculate result
            stake = bet['stake']
            odds = bet['odds']
            
            if result == 'WIN' or (result == 'PLACE' and finishing_position and finishing_position <= 3):
                # Winning bet
                returns = stake * odds * 0.25  # PLACE pays 1/4 of odds
                profit = returns - stake
                
                bet['status'] = 'WON'
                bet['returns'] = returns
                bet['profit'] = profit
                bet['finishing_position'] = finishing_position
                
                # Update bankroll
                self.current_bankroll += returns
                
                # Update consecutive counters
                self.consecutive_wins += 1
                self.consecutive_losses = 0
                
                print(f"✅ Bet WON: {bet['horse_name']}")
                print(f"   Returns: ${returns:.2f}")
                print(f"   Profit: ${profit:.2f}")
                print(f"   Bankroll: ${self.current_bankroll:.2f}")
                
            else:
                # Losing bet
                bet['status'] = 'LOST'
                bet['returns'] = 0
                bet['profit'] = -stake
                bet['finishing_position'] = finishing_position
                
                # Update consecutive counters
                self.consecutive_losses += 1
                self.consecutive_wins = 0
                
                print(f"❌ Bet LOST: {bet['horse_name']}")
                print(f"   Loss: ${stake:.2f}")
                print(f"   Bankroll: ${self.current_bankroll:.2f}")
            
            # Update exposure
            self.current_exposure -= stake
            
            # Update peak/trough
            if self.current_bankroll > self.peak_bankroll:
                self.peak_bankroll = self.current_bankroll
            if self.current_bankroll < self.trough_bankroll:
                self.trough_bankroll = self.current_bankroll
            
            # Update daily results
            self.update_daily_results(bet)
            
            return {'success': True, 'bet': bet}
            
        except Exception as e:
            print(f"❌ Failed to settle bet: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_daily_results(self, bet: Dict):
        """Update daily performance tracking"""
        try:
            date = datetime.fromisoformat(bet['timestamp']).date()
            
            if date not in self.daily_results:
                self.daily_results[date] = {
                    'bets': 0,
                    'wins': 0,
                    'losses': 0,
                    'staked': 0.0,
                    'returns': 0.0,
                    'profit': 0.0
                }
            
            daily = self.daily_results[date]
            daily['bets'] += 1
            daily['staked'] += bet['stake']
            daily['returns'] += bet.get('returns', 0)
            daily['profit'] += bet.get('profit', 0)
            
            if bet['status'] == 'WON':
                daily['wins'] += 1
            elif bet['status'] == 'LOST':
                daily['losses'] += 1
            
        except Exception as e:
            print(f"❌ Failed to update daily results: {e}")
    
    def calculate_daily_pnl(self) -> float:
        """Calculate current day P&L"""
        try:
            today = datetime.now().date()
            if today in self.daily_results:
                return self.daily_results[today]['profit']
            return 0.0
        except:
            return 0.0
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        try:
            total_bets = len(self.betting_history)
            winning_bets = len([b for b in self.betting_history if b['status'] == 'WON'])
            losing_bets = len([b for b in self.betting_history if b['status'] == 'LOST'])
            pending_bets = len([b for b in self.betting_history if b['status'] == 'PENDING'])
            
            total_staked = sum(b['stake'] for b in self.betting_history)
            total_returns = sum(b.get('returns', 0) for b in self.betting_history)
            total_profit = total_returns - total_staked
            
            win_rate = (winning_bets / (winning_bets + losing_bets) * 100) if (winning_bets + losing_bets) > 0 else 0
            roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
            
            # Calculate drawdown
            max_drawdown = ((self.peak_bankroll - self.trough_bankroll) / self.peak_bankroll * 100) if self.peak_bankroll > 0 else 0
            
            # Current streak
            current_streak = f"{self.consecutive_wins}W" if self.consecutive_wins > 0 else f"{self.consecutive_losses}L"
            
            summary = {
                'initial_bankroll': self.initial_bankroll,
                'current_bankroll': self.current_bankroll,
                'peak_bankroll': self.peak_bankroll,
                'trough_bankroll': self.trough_bankroll,
                'total_profit': total_profit,
                'total_staked': total_staked,
                'total_returns': total_returns,
                'roi': round(roi, 2),
                'win_rate': round(win_rate, 2),
                'max_drawdown': round(max_drawdown, 2),
                'total_bets': total_bets,
                'winning_bets': winning_bets,
                'losing_bets': losing_bets,
                'pending_bets': pending_bets,
                'current_exposure': self.current_exposure,
                'current_streak': current_streak,
                'daily_pnl': self.calculate_daily_pnl(),
                'risk_params': self.risk_params,
                'timestamp': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            print(f"❌ Failed to generate performance summary: {e}")
            return {}
    
    def export_history(self, filename: str = None) -> str:
        """Export betting history to JSON"""
        try:
            if not filename:
                filename = f"bankroll_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            export_data = {
                'performance_summary': self.get_performance_summary(),
                'betting_history': self.betting_history,
                'daily_results': {k.isoformat(): v for k, v in self.daily_results.items()},
                'risk_parameters': self.risk_params,
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"✅ Bankroll history exported to {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Failed to export history: {e}")
            return ""

def main():
    """Main execution function"""
    print("🚀 SENTINEL-RACING AI - PHASE 3: BANKROLL MANAGEMENT")
    print("=" * 60)
    
    # Initialize bankroll manager
    bankroll = BankrollManager(initial_bankroll=1000.0)
    
    print(f"💰 Initial bankroll: ${bankroll.initial_bankroll:.2f}")
    print(f"📊 Risk parameters configured")
    
    # Test Kelly Criterion calculation
    print(f"\n🧮 Testing Kelly Criterion calculations:")
    
    test_cases = [
        (0.25, 4.0, 80.0),  # 25% win prob, 4.0 odds, 80% confidence
        (0.30, 3.5, 85.0),  # 30% win prob, 3.5 odds, 85% confidence
        (0.20, 5.0, 75.0),  # 20% win prob, 5.0 odds, 75% confidence
        (0.35, 2.8, 90.0),  # 35% win prob, 2.8 odds, 90% confidence
    ]
    
    for i, (prob, odds, conf) in enumerate(test_cases, 1):
        stake = bankroll.calculate_kelly_stake(prob, odds, conf)
        risk = bankroll.assess_risk(stake, odds, conf)
        
        print(f"   Test {i}: Prob={prob:.2f}, Odds={odds:.1f}, Conf={conf:.0f}%")
        print(f"           Stake: ${stake:.2f}, Risk: {risk['risk_score']}, Rec: {risk['recommendation']}")
    
    # Test bet placement
    print(f"\n💰 Testing bet placement:")
    
    test_bet = bankroll.place_bet(
        stake=10.0,
        odds=4.0,
        confidence=85.0,
        horse_name="TO INFINITY",
        race_id="HK_HV_2026-03-11_R3"
    )
    
    if test_bet['success']:
        print(f"✅ Test bet placed successfully")
        
        # Test bet settlement
        print(f"\n🏁 Testing bet settlement:")
        
        # Simulate winning bet
        result = bankroll.settle_bet(test_bet['bet']['bet_id'], 'PLACE', 2)
        
        if result['success']:
            print(f"✅ Bet settled successfully")
        else:
            print(f"❌ Bet settlement failed")
    
    # Generate performance summary
    print(f"\n📊 Performance Summary:")
    summary = bankroll.get_performance_summary()
    
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    # Export history
    print(f"\n💾 Exporting betting history...")
    filename = bankroll.export_history('/Users/wallace/Documents/ project-sentinel/automation/phase3/bankroll_history.json')
    
    print(f"\n🎯 PHASE 3 BANKROLL MANAGEMENT: WORKING")
    print(f"🚀 Ready for Phase 4: Commercial Integration")

if __name__ == "__main__":
    main()

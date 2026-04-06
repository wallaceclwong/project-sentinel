"""
SENTINEL-RACING AI - AI ENHANCEMENTS
Advanced confidence scoring and model improvements
"""

import asyncio
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ConfidenceLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class RacingFactors:
    """Racing analysis factors"""
    barrier_advantage: float
    jockey_performance: float
    horse_form: float
    track_conditions: float
    weather_impact: float
    odds_value: float
    historical_performance: float

class AIEnhancementEngine:
    """Advanced AI enhancement engine for improved confidence scoring"""
    
    def __init__(self):
        self.confidence_thresholds = {
            ConfidenceLevel.VERY_LOW: 40.0,
            ConfidenceLevel.LOW: 55.0,
            ConfidenceLevel.MEDIUM: 70.0,
            ConfidenceLevel.HIGH: 80.0,
            ConfidenceLevel.VERY_HIGH: 90.0
        }
        
        self.factor_weights = {
            'barrier_advantage': 0.20,
            'jockey_performance': 0.25,
            'horse_form': 0.20,
            'track_conditions': 0.10,
            'weather_impact': 0.05,
            'odds_value': 0.15,
            'historical_performance': 0.05
        }
        
        self.performance_history = []
        self.model_accuracy = 0.72  # Baseline accuracy
        
    def calculate_enhanced_confidence(self, horse_data: Dict, race_conditions: Dict, odds_data: Dict) -> Dict:
        """Calculate enhanced confidence score with multiple factors"""
        try:
            # Extract factors
            factors = self.extract_racing_factors(horse_data, race_conditions, odds_data)
            
            # Calculate weighted confidence
            base_confidence = 50.0  # Base confidence
            
            # Apply factor weights
            for factor_name, factor_value in factors.__dict__.items():
                if factor_name in self.factor_weights:
                    weight = self.factor_weights[factor_name]
                    base_confidence += (factor_value - 0.5) * weight * 100
            
            # Apply advanced adjustments
            adjusted_confidence = self.apply_advanced_adjustments(base_confidence, factors, race_conditions)
            
            # Determine confidence level
            confidence_level = self.determine_confidence_level(adjusted_confidence)
            
            # Generate reasoning
            reasoning = self.generate_enhanced_reasoning(factors, adjusted_confidence, confidence_level)
            
            return {
                'confidence_score': round(adjusted_confidence, 2),
                'confidence_level': confidence_level.value,
                'factors': factors.__dict__,
                'reasoning': reasoning,
                'recommendation': self.generate_recommendation(adjusted_confidence, confidence_level),
                'risk_assessment': self.assess_risk(adjusted_confidence, factors),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Enhanced confidence calculation failed: {e}")
            return {
                'confidence_score': 50.0,
                'confidence_level': 'medium',
                'error': str(e)
            }
    
    def extract_racing_factors(self, horse_data: Dict, race_conditions: Dict, odds_data: Dict) -> RacingFactors:
        """Extract and normalize racing factors"""
        try:
            # Barrier advantage (0-1 scale, higher is better)
            barrier = int(horse_data.get('barrier', 7))
            barrier_advantage = self.calculate_barrier_advantage(barrier)
            
            # Jockey performance (0-1 scale)
            jockey = horse_data.get('jockey', '')
            jockey_performance = self.calculate_jockey_performance(jockey)
            
            # Horse form (0-1 scale)
            horse_form = self.calculate_horse_form(horse_data)
            
            # Track conditions (0-1 scale)
            track_conditions_factor = self.calculate_track_conditions_factor(race_conditions)
            
            # Weather impact (0-1 scale)
            weather_impact = self.calculate_weather_impact(race_conditions)
            
            # Odds value (0-1 scale, higher is better value)
            odds_value = self.calculate_odds_value(odds_data, horse_data.get('name', ''))
            
            # Historical performance (0-1 scale)
            historical_performance = self.calculate_historical_performance(horse_data)
            
            return RacingFactors(
                barrier_advantage=barrier_advantage,
                jockey_performance=jockey_performance,
                horse_form=horse_form,
                track_conditions=track_conditions_factor,
                weather_impact=weather_impact,
                odds_value=odds_value,
                historical_performance=historical_performance
            )
            
        except Exception as e:
            print(f"❌ Factor extraction failed: {e}")
            return RacingFactors(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
    
    def calculate_barrier_advantage(self, barrier: int) -> float:
        """Calculate barrier advantage (0-1 scale)"""
        # Statistical advantage for barriers 1-6
        if barrier <= 3:
            return 0.8  # High advantage
        elif barrier <= 6:
            return 0.6  # Medium advantage
        elif barrier <= 9:
            return 0.4  # Low advantage
        else:
            return 0.2  # Very low advantage
    
    def calculate_jockey_performance(self, jockey: str) -> float:
        """Calculate jockey performance based on historical data"""
        # Top jockeys with high win rates
        top_jockeys = ['Purton', 'Moreira', 'Schofield', 'Prebble', 'Baze']
        
        if any(top_jockey in jockey for top_jockey in top_jockeys):
            return 0.85  # Excellent performance
        elif 'Chau' in jockey or 'Mo' in jockey:
            return 0.65  # Good performance
        else:
            return 0.45  # Average performance
    
    def calculate_horse_form(self, horse_data: Dict) -> float:
        """Calculate horse form based on recent performance"""
        # This would use actual form data, for now use placeholder
        # In production, this would analyze last 3-5 races
        return 0.55  # Average form
    
    def calculate_track_conditions_factor(self, race_conditions: Dict) -> float:
        """Calculate track conditions impact"""
        going = race_conditions.get('going', 'Good').lower()
        
        if going == 'good':
            return 0.7  # Optimal conditions
        elif going == 'firm':
            return 0.6  # Good conditions
        elif going == 'yielding' or going == 'soft':
            return 0.4  # Challenging conditions
        else:
            return 0.5  # Unknown conditions
    
    def calculate_weather_impact(self, race_conditions: Dict) -> float:
        """Calculate weather impact"""
        weather = race_conditions.get('weather', 'Fine').lower()
        
        if weather == 'fine':
            return 0.8  # Optimal weather
        elif weather == 'cloudy':
            return 0.6  # Good weather
        elif weather == 'rain' or weather == 'wet':
            return 0.3  # Challenging weather
        else:
            return 0.5  # Unknown weather
    
    def calculate_odds_value(self, odds_data: Dict, horse_name: str) -> float:
        """Calculate odds value (higher is better value)"""
        horse_odds = odds_data.get(horse_name, {})
        
        if horse_odds:
            # Use best available odds
            best_odds = min(horse_odds.values())
            
            # Calculate value (higher is better for PLACE bets)
            if 2.0 <= best_odds <= 4.0:
                return 0.8  # Good value
            elif 4.0 < best_odds <= 6.0:
                return 0.6  # Fair value
            elif best_odds > 6.0:
                return 0.4  # Poor value
            else:
                return 0.7  # Excellent value
        else:
            return 0.5  # No odds data
    
    def calculate_historical_performance(self, horse_data: Dict) -> float:
        """Calculate historical performance"""
        # This would analyze horse's historical performance
        # For now, use placeholder
        return 0.5  # Average historical performance
    
    def apply_advanced_adjustments(self, base_confidence: float, factors: RacingFactors, race_conditions: Dict) -> float:
        """Apply advanced adjustments to confidence score"""
        adjusted_confidence = base_confidence
        
        # Risk adjustment based on factor variance
        factor_values = list(factors.__dict__.values())
        factor_variance = np.var(factor_values)
        
        if factor_variance > 0.1:  # High variance = higher risk
            adjusted_confidence -= 5.0
        
        # Field size adjustment
        field_size = race_conditions.get('field_size', 12)
        if field_size > 12:
            adjusted_confidence -= 3.0  # Larger field = more uncertainty
        elif field_size < 8:
            adjusted_confidence += 2.0  # Smaller field = more predictable
        
        # Distance adjustment
        distance = race_conditions.get('distance', '1200m')
        if '1000m' in distance or '1200m' in distance:
            adjusted_confidence += 2.0  # Sprint races more predictable
        
        # Ensure confidence stays in valid range
        return max(20.0, min(95.0, adjusted_confidence))
    
    def determine_confidence_level(self, confidence_score: float) -> ConfidenceLevel:
        """Determine confidence level from score"""
        if confidence_score >= self.confidence_thresholds[ConfidenceLevel.VERY_HIGH]:
            return ConfidenceLevel.VERY_HIGH
        elif confidence_score >= self.confidence_thresholds[ConfidenceLevel.HIGH]:
            return ConfidenceLevel.HIGH
        elif confidence_score >= self.confidence_thresholds[ConfidenceLevel.MEDIUM]:
            return ConfidenceLevel.MEDIUM
        elif confidence_score >= self.confidence_thresholds[ConfidenceLevel.LOW]:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def generate_enhanced_reasoning(self, factors: RacingFactors, confidence_score: float, confidence_level: ConfidenceLevel) -> List[str]:
        """Generate enhanced reasoning for confidence score"""
        reasoning = []
        
        # Factor-based reasoning
        if factors.barrier_advantage > 0.7:
            reasoning.append("Excellent barrier position (1-3)")
        elif factors.barrier_advantage < 0.4:
            reasoning.append("Challenging barrier position (10+)")
        
        if factors.jockey_performance > 0.8:
            reasoning.append("Top jockey with high win rate")
        elif factors.jockey_performance < 0.5:
            reasoning.append("Average jockey performance")
        
        if factors.odds_value > 0.7:
            reasoning.append("Good value odds for PLACE bet")
        elif factors.odds_value < 0.5:
            reasoning.append("Poor value odds")
        
        if factors.track_conditions > 0.6:
            reasoning.append("Optimal track conditions")
        elif factors.track_conditions < 0.5:
            reasoning.append("Challenging track conditions")
        
        # Confidence level reasoning
        if confidence_level == ConfidenceLevel.VERY_HIGH:
            reasoning.append("Multiple strong factors indicate high probability")
        elif confidence_level == ConfidenceLevel.VERY_LOW:
            reasoning.append("Multiple risk factors present")
        
        return reasoning
    
    def generate_recommendation(self, confidence_score: float, confidence_level: ConfidenceLevel) -> str:
        """Generate betting recommendation"""
        if confidence_level in [ConfidenceLevel.VERY_HIGH, ConfidenceLevel.HIGH]:
            return "STRONG PLACE BET RECOMMENDATION"
        elif confidence_level == ConfidenceLevel.MEDIUM:
            return "CONSIDER PLACE BET"
        elif confidence_level == ConfidenceLevel.LOW:
            return "WEAK PLACE BET - RISKY"
        else:
            return "SKIP - HIGH RISK"
    
    def assess_risk(self, confidence_score: float, factors: RacingFactors) -> Dict:
        """Assess risk factors"""
        risk_factors = []
        risk_score = 0
        
        # Barrier risk
        if factors.barrier_advantage < 0.4:
            risk_factors.append("Poor barrier position")
            risk_score += 20
        
        # Jockey risk
        if factors.jockey_performance < 0.5:
            risk_factors.append("Inexperienced jockey")
            risk_score += 15
        
        # Track condition risk
        if factors.track_conditions < 0.5:
            risk_factors.append("Challenging track conditions")
            risk_score += 10
        
        # Odds risk
        if factors.odds_value < 0.5:
            risk_factors.append("Poor value odds")
            risk_score += 15
        
        # Determine overall risk level
        if risk_score >= 40:
            risk_level = "HIGH"
        elif risk_score >= 20:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommended_stake": self.calculate_recommended_stake(confidence_score, risk_level)
        }
    
    def calculate_recommended_stake(self, confidence_score: float, risk_level: str) -> float:
        """Calculate recommended stake based on confidence and risk"""
        base_stake = 100.0  # Base stake in HKD
        
        # Adjust based on confidence
        confidence_multiplier = confidence_score / 100.0
        
        # Adjust based on risk
        if risk_level == "HIGH":
            risk_multiplier = 0.5
        elif risk_level == "MEDIUM":
            risk_multiplier = 0.75
        else:
            risk_multiplier = 1.0
        
        recommended_stake = base_stake * confidence_multiplier * risk_multiplier
        
        # Ensure minimum and maximum stakes
        return max(10.0, min(500.0, recommended_stake))
    
    def learn_from_results(self, predictions: List[Dict], actual_results: List[Dict]) -> Dict:
        """Learn from actual race results to improve model"""
        try:
            correct_predictions = 0
            total_predictions = len(predictions)
            
            for prediction in predictions:
                predicted_horse = prediction.get('horse_name', '')
                confidence_score = prediction.get('confidence_score', 0)
                
                # Check if prediction was correct
                for result in actual_results:
                    if result.get('horse_name', '') == predicted_horse:
                        if result.get('position', 999) <= 3:  # PLACE bet success
                            correct_predictions += 1
                            
                            # Update factor weights based on success
                            self.update_factor_weights(prediction, True)
                        else:
                            # Update factor weights based on failure
                            self.update_factor_weights(prediction, False)
                        break
            
            # Calculate new accuracy
            new_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
            
            # Update model accuracy
            accuracy_improvement = new_accuracy - self.model_accuracy
            self.model_accuracy = new_accuracy
            
            # Store learning data
            learning_data = {
                'timestamp': datetime.now().isoformat(),
                'previous_accuracy': self.model_accuracy - accuracy_improvement,
                'new_accuracy': new_accuracy,
                'improvement': accuracy_improvement,
                'total_predictions': total_predictions,
                'correct_predictions': correct_predictions
            }
            
            self.performance_history.append(learning_data)
            
            return learning_data
            
        except Exception as e:
            print(f"❌ Learning from results failed: {e}")
            return {'error': str(e)}
    
    def update_factor_weights(self, prediction: Dict, success: bool):
        """Update factor weights based on prediction success/failure"""
        try:
            factors = prediction.get('factors', {})
            
            # Adjust weights slightly based on success
            adjustment = 0.01 if success else -0.01
            
            for factor_name, factor_value in factors.items():
                if factor_name in self.factor_weights:
                    # Higher factor values should have higher weights if successful
                    if success and factor_value > 0.6:
                        self.factor_weights[factor_name] += adjustment
                    elif not success and factor_value > 0.6:
                        self.factor_weights[factor_name] -= adjustment
            
            # Normalize weights to ensure they sum to 1
            total_weight = sum(self.factor_weights.values())
            if total_weight > 0:
                for factor_name in self.factor_weights:
                    self.factor_weights[factor_name] /= total_weight
            
        except Exception as e:
            print(f"❌ Factor weight update failed: {e}")

# Enhanced AI service integration
class EnhancedAIAnalysisService:
    """Enhanced AI analysis service with advanced confidence scoring"""
    
    def __init__(self):
        self.enhancement_engine = AIEnhancementEngine()
        self.models = {}
        self.performance_history = []
        
    async def analyze_race_enhanced(self, data: Dict) -> Dict:
        """Enhanced race analysis with advanced confidence scoring"""
        try:
            horses = data.get('hkjc_data', {}).get('horses', [])
            odds_data = data.get('odds_data', {}).get('odds', {})
            race_conditions = data.get('premium_data', {})
            
            enhanced_recommendations = []
            
            for horse in horses:
                # Calculate enhanced confidence
                enhanced_analysis = self.enhancement_engine.calculate_enhanced_confidence(
                    horse, race_conditions, odds_data
                )
                
                # Only include recommendations with sufficient confidence
                if enhanced_analysis['confidence_score'] >= 70:
                    enhanced_recommendations.append({
                        'horse': horse,
                        'enhanced_analysis': enhanced_analysis,
                        'recommendation_type': 'PLACE',
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Sort by confidence score
            enhanced_recommendations.sort(
                key=lambda x: x['enhanced_analysis']['confidence_score'], 
                reverse=True
            )
            
            return {
                'enhanced_recommendations': enhanced_recommendations[:3],  # Top 3
                'analysis_summary': f"Enhanced analysis of {len(horses)} horses",
                'model_accuracy': self.enhancement_engine.model_accuracy,
                'enhancement_version': '2.0',
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Enhanced race analysis failed: {e}")
            return {'success': False, 'error': str(e)}

# Example usage
async def test_enhanced_ai():
    """Test enhanced AI analysis"""
    enhanced_service = EnhancedAIAnalysisService()
    
    # Test data
    test_horse = {
        'name': 'TEST_HORSE',
        'barrier': '3',
        'jockey': 'Purton'
    }
    
    test_conditions = {
        'going': 'Good',
        'weather': 'Fine',
        'field_size': 12,
        'distance': '1200m'
    }
    
    test_odds = {
        'TEST_HORSE': {'Betfair': 3.5}
    }
    
    # Test enhanced analysis
    result = enhanced_service.enhancement_engine.calculate_enhanced_confidence(
        test_horse, test_conditions, test_odds
    )
    
    print("🚀 ENHANCED AI ANALYSIS TEST:")
    print("=" * 40)
    print(f"Confidence Score: {result['confidence_score']}")
    print(f"Confidence Level: {result['confidence_level']}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Risk Level: {result['risk_assessment']['risk_level']}")
    print(f"Recommended Stake: ${result['risk_assessment']['recommended_stake']}")
    print(f"Reasoning: {', '.join(result['reasoning'])}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_ai())

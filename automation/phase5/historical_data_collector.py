"""
SENTINEL-RACING AI - PHASE 5: HISTORICAL DATA COLLECTOR
Backtesting data collection and model validation
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

class HistoricalDataCollector:
    """Collect historical racing data for backtesting and model improvement"""
    
    def __init__(self):
        self.session = None
        self.historical_data = {}
        self.backtesting_results = {}
        self.model_performance = {}
        
    async def setup_session(self):
        """Setup HTTP session for data collection"""
        self.session = aiohttp.ClientSession()
        
    async def collect_historical_races(self, start_date: str, end_date: str) -> Dict:
        """Collect historical race data for backtesting"""
        try:
            print(f"🚀 Collecting historical data from {start_date} to {end_date}")
            
            # Generate date range
            dates = self.generate_date_range(start_date, end_date)
            
            all_races = []
            
            for date in dates:
                print(f"📅 Collecting data for {date}")
                
                # Collect HKJC data for this date
                races = await self.collect_hkjc_historical(date)
                
                if races:
                    all_races.extend(races)
                    print(f"✅ Collected {len(races)} races for {date}")
                else:
                    print(f"❌ No races found for {date}")
            
            # Store historical data
            self.historical_data = {
                'collection_date': datetime.now().isoformat(),
                'date_range': {'start': start_date, 'end': end_date},
                'total_races': len(all_races),
                'races': all_races
            }
            
            # Save to file
            await self.save_historical_data()
            
            return self.historical_data
            
        except Exception as e:
            print(f"❌ Historical data collection failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_date_range(self, start_date: str, end_date: str) -> List[str]:
        """Generate date range for historical collection"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        dates = []
        current = start
        
        while current <= end:
            # Skip weekends (no racing on Sundays)
            if current.weekday() < 6:  # Monday to Saturday
                dates.append(current.strftime('%Y/%m/%d'))
            current += timedelta(days=1)
        
        return dates
    
    async def collect_hkjc_historical(self, date: str) -> List[Dict]:
        """Collect HKJC historical data for specific date"""
        try:
            # Use Selenium for historical data
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            races = []
            
            # Try both Happy Valley and Sha Tin
            venues = ['HV', 'ST']
            
            for venue in venues:
                try:
                    # Navigate to results page
                    results_url = f'https://racing.hkjc.com/en-us/racing/results/Local/{date.replace("/", "")}/{venue}'
                    driver.get(results_url)
                    time.sleep(3)
                    
                    # Check if results exist
                    page_source = driver.page_source
                    
                    if 'Result' in page_source or 'results' in page_source.lower():
                        # Extract race numbers
                        race_numbers = self.extract_race_numbers(page_source)
                        
                        for race_num in race_numbers:
                            print(f"🐎 Extracting {venue} Race {race_num}...")
                            
                            # Navigate to specific race result
                            race_url = f'https://racing.hkjc.com/en-us/racing/result/Local/{date.replace("/", "")}/{venue}/{race_num}'
                            driver.get(race_url)
                            time.sleep(2)
                            
                            race_data = self.extract_race_result(driver.page_source, venue, race_num, date)
                            
                            if race_data:
                                races.append(race_data)
                
                except Exception as e:
                    print(f"⚠️  Error collecting {venue} data: {e}")
                    continue
            
            driver.quit()
            return races
            
        except Exception as e:
            print(f"❌ HKJC historical collection failed: {e}")
            return []
    
    def extract_race_numbers(self, page_source: str) -> List[int]:
        """Extract race numbers from results page"""
        race_numbers = []
        
        # Look for race number patterns
        patterns = [
            r'Race\s+(\d+)',
            r'第(\d+)場',
            r'RACE\s+(\d+)',
            r'(\d+)\s+場'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            for match in matches:
                try:
                    race_num = int(match)
                    if 1 <= race_num <= 12:  # Valid race numbers
                        race_numbers.append(race_num)
                except:
                    continue
        
        # Remove duplicates and sort
        race_numbers = sorted(list(set(race_numbers)))
        return race_numbers
    
    def extract_race_result(self, page_source: str, venue: str, race_num: int, date: str) -> Optional[Dict]:
        """Extract race result data"""
        try:
            # Extract finishing order
            finishing_order = self.extract_finishing_order(page_source)
            
            # Extract horse details
            horse_details = self.extract_horse_details(page_source)
            
            # Extract dividends
            dividends = self.extract_dividends(page_source)
            
            # Extract race conditions
            race_conditions = self.extract_race_conditions(page_source)
            
            if finishing_order and horse_details:
                return {
                    'date': date,
                    'venue': venue,
                    'race_number': race_num,
                    'finishing_order': finishing_order,
                    'horse_details': horse_details,
                    'dividends': dividends,
                    'race_conditions': race_conditions,
                    'collected_at': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Race result extraction failed: {e}")
            return None
    
    def extract_finishing_order(self, page_source: str) -> List[Dict]:
        """Extract finishing order from race result"""
        finishing_order = []
        
        # Look for finishing patterns
        patterns = [
            r'(\d+)\.\s+([A-Za-z0-9\s&-]+)',
            r'(\d+)\s+([A-Za-z0-9\s&-]+)',
            r'No\.(\d+)\s+([A-Za-z0-9\s&-]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            for match in matches:
                try:
                    position = int(match[0])
                    horse_name = match[1].strip()
                    
                    if 1 <= position <= 14 and len(horse_name) > 2:
                        finishing_order.append({
                            'position': position,
                            'horse_name': horse_name
                        })
                except:
                    continue
        
        # Sort by position and limit to top 14
        finishing_order = sorted(finishing_order, key=lambda x: x['position'])[:14]
        return finishing_order
    
    def extract_horse_details(self, page_source: str) -> List[Dict]:
        """Extract horse details (barrier, jockey, etc.)"""
        horse_details = []
        
        # Look for horse detail patterns
        patterns = [
            r'([A-Za-z0-9\s&-]+)\s*\(\s*(\d+)\s*\)\s*-\s*([A-Za-z\s&-]+)',
            r'([A-Za-z0-9\s&-]+)\s*B(\d+)\s*([A-Za-z\s&-]+)',
            r'(\d+)\s+([A-Za-z0-9\s&-]+)\s*Barrier\s*(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match) >= 3:
                        horse_name = match[0].strip() if match[0] else match[1].strip()
                        barrier = match[1] if match[1].isdigit() else match[2] if match[2].isdigit() else 'Unknown'
                        jockey = match[2] if len(match) > 2 else 'Unknown'
                        
                        if len(horse_name) > 2 and barrier != 'Unknown':
                            horse_details.append({
                                'horse_name': horse_name,
                                'barrier': barrier,
                                'jockey': jockey.strip()
                            })
                except:
                    continue
        
        # Remove duplicates
        unique_horses = []
        seen_names = set()
        for horse in horse_details:
            if horse['horse_name'] not in seen_names:
                unique_horses.append(horse)
                seen_names.add(horse['horse_name'])
        
        return unique_horses
    
    def extract_dividends(self, page_source: str) -> Dict:
        """Extract dividend information"""
        dividends = {}
        
        # Look for dividend patterns
        patterns = [
            r'WIN\s*\$([\d.]+)',
            r'PLACE\s*\$([\d.]+)',
            r'QUINELLA\s*\$([\d.]+)',
            r'EXACTA\s*\$([\d.]+)'
        ]
        
        bet_types = ['WIN', 'PLACE', 'QUINELLA', 'EXACTA']
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches and i < len(bet_types):
                try:
                    dividend_amount = float(matches[0])
                    dividends[bet_types[i]] = dividend_amount
                except:
                    continue
        
        return dividends
    
    def extract_race_conditions(self, page_source: str) -> Dict:
        """Extract race conditions"""
        conditions = {}
        
        # Look for condition patterns
        patterns = [
            r'Distance:\s*(\d+m)',
            r'Going:\s*([A-Za-z\s]+)',
            r'Weather:\s*([A-Za-z\s]+)',
            r'Class:\s*([A-Za-z0-9\s]+)'
        ]
        
        condition_keys = ['distance', 'going', 'weather', 'class']
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches and i < len(condition_keys):
                conditions[condition_keys[i]] = matches[0].strip()
        
        return conditions
    
    async def save_historical_data(self):
        """Save historical data to file"""
        try:
            filename = f'/Users/wallace/Documents/ project-sentinel/automation/phase5/historical_data_{datetime.now().strftime("%Y%m%d")}.json'
            
            with open(filename, 'w') as f:
                json.dump(self.historical_data, f, indent=2)
            
            print(f"💾 Historical data saved to {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save historical data: {e}")
    
    async def backtest_model(self, historical_data: Dict) -> Dict:
        """Backtest AI model against historical data"""
        try:
            print("🎯 Starting backtesting analysis...")
            
            backtest_results = {
                'backtest_date': datetime.now().isoformat(),
                'total_races': len(historical_data.get('races', [])),
                'correct_predictions': 0,
                'total_predictions': 0,
                'accuracy': 0.0,
                'performance_by_barrier': {},
                'performance_by_jockey': {},
                'confidence_analysis': {},
                'recommendations': []
            }
            
            races = historical_data.get('races', [])
            
            for race in races:
                # Simulate AI prediction for this race
                prediction = self.simulate_ai_prediction(race)
                
                if prediction:
                    backtest_results['total_predictions'] += 1
                    
                    # Check if prediction was correct
                    if self.was_prediction_correct(prediction, race):
                        backtest_results['correct_predictions'] += 1
                    
                    # Analyze performance by barrier
                    barrier = prediction.get('barrier', 'Unknown')
                    if barrier not in backtest_results['performance_by_barrier']:
                        backtest_results['performance_by_barrier'][barrier] = {'correct': 0, 'total': 0}
                    
                    backtest_results['performance_by_barrier'][barrier]['total'] += 1
                    if self.was_prediction_correct(prediction, race):
                        backtest_results['performance_by_barrier'][barrier]['correct'] += 1
                    
                    # Analyze performance by jockey
                    jockey = prediction.get('jockey', 'Unknown')
                    if jockey not in backtest_results['performance_by_jockey']:
                        backtest_results['performance_by_jockey'][jockey] = {'correct': 0, 'total': 0}
                    
                    backtest_results['performance_by_jockey'][jockey]['total'] += 1
                    if self.was_prediction_correct(prediction, race):
                        backtest_results['performance_by_jockey'][jockey]['correct'] += 1
            
            # Calculate accuracy
            if backtest_results['total_predictions'] > 0:
                backtest_results['accuracy'] = backtest_results['correct_predictions'] / backtest_results['total_predictions']
            
            # Generate recommendations
            backtest_results['recommendations'] = self.generate_backtest_recommendations(backtest_results)
            
            self.backtesting_results = backtest_results
            
            # Save backtest results
            await self.save_backtest_results()
            
            return backtest_results
            
        except Exception as e:
            print(f"❌ Backtesting failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def simulate_ai_prediction(self, race: Dict) -> Optional[Dict]:
        """Simulate AI prediction for historical race"""
        try:
            horse_details = race.get('horse_details', [])
            
            if not horse_details:
                return None
            
            # Select a horse based on current AI logic
            selected_horse = None
            max_confidence = 0
            
            for horse in horse_details:
                confidence = 70  # Base confidence
                
                # Barrier adjustment
                try:
                    barrier = int(horse.get('barrier', 0))
                    if barrier <= 6:
                        confidence += 10
                    elif barrier >= 9:
                        confidence -= 5
                except:
                    pass
                
                # Jockey adjustment
                jockey = horse.get('jockey', '')
                if 'Purton' in jockey or 'Moreira' in jockey:
                    confidence += 15
                elif 'Schofield' in jockey or 'Prebble' in jockey:
                    confidence += 10
                
                if confidence > max_confidence:
                    max_confidence = confidence
                    selected_horse = horse
            
            if selected_horse and max_confidence >= 75:
                return {
                    'horse_name': selected_horse['horse_name'],
                    'barrier': selected_horse['barrier'],
                    'jockey': selected_horse['jockey'],
                    'confidence': max_confidence,
                    'prediction_type': 'PLACE'
                }
            
            return None
            
        except Exception as e:
            print(f"❌ AI prediction simulation failed: {e}")
            return None
    
    def was_prediction_correct(self, prediction: Dict, race: Dict) -> bool:
        """Check if AI prediction was correct"""
        try:
            predicted_horse = prediction.get('horse_name', '')
            prediction_type = prediction.get('prediction_type', 'PLACE')
            
            finishing_order = race.get('finishing_order', [])
            
            # Find the predicted horse's position
            predicted_position = None
            for finisher in finishing_order:
                if finisher['horse_name'] == predicted_horse:
                    predicted_position = finisher['position']
                    break
            
            if prediction_type == 'PLACE':
                # PLACE bet: horse must finish 1st, 2nd, or 3rd
                return predicted_position is not None and predicted_position <= 3
            
            return False
            
        except Exception as e:
            print(f"❌ Prediction validation failed: {e}")
            return False
    
    def generate_backtest_recommendations(self, backtest_results: Dict) -> List[str]:
        """Generate recommendations based on backtest results"""
        recommendations = []
        
        accuracy = backtest_results.get('accuracy', 0)
        
        if accuracy < 0.6:
            recommendations.append("Consider lowering confidence threshold for more predictions")
        elif accuracy > 0.8:
            recommendations.append("Current confidence scoring is performing well")
        
        # Analyze barrier performance
        barrier_performance = backtest_results.get('performance_by_barrier', {})
        good_barriers = []
        poor_barriers = []
        
        for barrier, stats in barrier_performance.items():
            if stats['total'] >= 5:  # Minimum sample size
                barrier_accuracy = stats['correct'] / stats['total']
                if barrier_accuracy > 0.7:
                    good_barriers.append(barrier)
                elif barrier_accuracy < 0.4:
                    poor_barriers.append(barrier)
        
        if good_barriers:
            recommendations.append(f"Barriers {', '.join(good_barriers)} show strong performance")
        
        if poor_barriers:
            recommendations.append(f"Consider avoiding horses from barriers {', '.join(poor_barriers)}")
        
        # General recommendations
        recommendations.append("Collect more historical data for better model training")
        recommendations.append("Implement real-time odds analysis for improved predictions")
        recommendations.append("Consider weather and track conditions in confidence scoring")
        
        return recommendations
    
    async def save_backtest_results(self):
        """Save backtest results to file"""
        try:
            filename = f'/Users/wallace/Documents/ project-sentinel/automation/phase5/backtest_results_{datetime.now().strftime("%Y%m%d")}.json'
            
            with open(filename, 'w') as f:
                json.dump(self.backtesting_results, f, indent=2)
            
            print(f"💾 Backtest results saved to {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save backtest results: {e}")
    
    async def generate_learning_report(self) -> Dict:
        """Generate comprehensive learning report"""
        try:
            report = {
                'report_date': datetime.now().isoformat(),
                'historical_data_summary': {
                    'total_races': len(self.historical_data.get('races', [])),
                    'date_range': self.historical_data.get('date_range', {}),
                    'venues': list(set(race.get('venue') for race in self.historical_data.get('races', [])))
                },
                'backtest_results': self.backtesting_results,
                'model_improvements': self.generate_model_improvements(),
                'next_steps': self.generate_next_steps()
            }
            
            # Save report
            filename = f'/Users/wallace/Documents/ project-sentinel/automation/phase5/learning_report_{datetime.now().strftime("%Y%m%d")}.json'
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"💾 Learning report saved to {filename}")
            
            return report
            
        except Exception as e:
            print(f"❌ Learning report generation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_model_improvements(self) -> List[str]:
        """Generate model improvement recommendations"""
        improvements = []
        
        if not self.backtesting_results:
            improvements.append("Run backtesting analysis first")
            return improvements
        
        accuracy = self.backtesting_results.get('accuracy', 0)
        
        if accuracy < 0.7:
            improvements.append("Improve confidence scoring algorithm")
            improvements.append("Add more features to prediction model")
            improvements.append("Consider machine learning approach")
        
        improvements.append("Implement real-time odds analysis")
        improvements.append("Add weather and track condition factors")
        improvements.append("Enhance jockey performance analysis")
        improvements.append("Include horse form history")
        
        return improvements
    
    def generate_next_steps(self) -> List[str]:
        """Generate next steps for model improvement"""
        steps = [
            "Collect more historical data (6-12 months recommended)",
            "Implement real-time odds monitoring",
            "Add weather and track condition analysis",
            "Enhance jockey and trainer performance tracking",
            "Implement machine learning for pattern recognition",
            "Create automated model retraining system",
            "Add international racing data for broader analysis"
        ]
        
        return steps

async def main():
    """Main execution function"""
    print("🚀 SENTINEL-RACING AI - HISTORICAL DATA COLLECTOR")
    print("=" * 60)
    
    collector = HistoricalDataCollector()
    await collector.setup_session()
    
    try:
        # Collect historical data for past month
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"📊 Collecting historical data from {start_date} to {end_date}")
        
        historical_data = await collector.collect_historical_races(start_date, end_date)
        
        if historical_data.get('success', False):
            print(f"✅ Collected data for {historical_data.get('total_races', 0)} races")
            
            # Run backtesting
            print("🎯 Running backtesting analysis...")
            backtest_results = await collector.backtest_model(historical_data)
            
            if backtest_results.get('accuracy', 0) > 0:
                print(f"✅ Backtesting complete: {backtest_results['accuracy']:.2%} accuracy")
                print(f"📊 Total predictions: {backtest_results['total_predictions']}")
                print(f"✅ Correct predictions: {backtest_results['correct_predictions']}")
            
            # Generate learning report
            print("📋 Generating learning report...")
            report = await collector.generate_learning_report()
            
            print("✅ Historical data collection and analysis complete!")
            
        else:
            print("❌ Historical data collection failed")
            
    except Exception as e:
        print(f"❌ Historical data collector failed: {e}")
    
    finally:
        if collector.session:
            await collector.session.close()

if __name__ == "__main__":
    asyncio.run(main())

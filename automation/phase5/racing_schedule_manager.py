"""
SENTINEL-RACING AI - RACING SCHEDULE MANAGER
Automated monthly racing schedule fetching and day classification
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import calendar
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

class RacingScheduleManager:
    """Manage monthly racing schedule and automatic day classification"""
    
    def __init__(self):
        self.session = None
        self.racing_schedule = {}
        self.monthly_calendar = {}
        self.racing_days = []
        self.non_racing_days = []
        
    async def setup_session(self):
        """Setup HTTP session for schedule fetching"""
        self.session = aiohttp.ClientSession()
        
    async def fetch_monthly_schedule(self, year: int, month: int) -> Dict:
        """Fetch monthly racing schedule from HKJC"""
        try:
            print(f"🚀 Fetching racing schedule for {year}-{month:02d}")
            
            # Get calendar for the month
            cal = calendar.monthcalendar(year, month)
            days_in_month = calendar.monthrange(year, month)[1]
            
            monthly_schedule = {
                'year': year,
                'month': month,
                'total_days': days_in_month,
                'racing_days': [],
                'non_racing_days': [],
                'schedule_details': {},
                'fetch_timestamp': datetime.now().isoformat()
            }
            
            # Check each day for racing
            for day in range(1, days_in_month + 1):
                date_str = f"{year}/{month:02d}/{day:02d}"
                weekday = datetime(year, month, day).weekday()
                weekday_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][weekday]
                
                # Check if it's a racing day
                racing_info = await self.check_racing_day(date_str, weekday)
                
                day_info = {
                    'date': date_str,
                    'day': day,
                    'weekday': weekday,
                    'weekday_name': weekday_name,
                    'is_racing_day': racing_info['is_racing'],
                    'venue': racing_info.get('venue', ''),
                    'race_count': racing_info.get('race_count', 0),
                    'meeting_type': racing_info.get('meeting_type', '')
                }
                
                monthly_schedule['schedule_details'][date_str] = day_info
                
                if racing_info['is_racing']:
                    monthly_schedule['racing_days'].append(date_str)
                    self.racing_days.append(date_str)
                else:
                    monthly_schedule['non_racing_days'].append(date_str)
                    self.non_racing_days.append(date_str)
            
            # Save schedule
            self.racing_schedule = monthly_schedule
            await self.save_monthly_schedule()
            
            return monthly_schedule
            
        except Exception as e:
            print(f"❌ Failed to fetch monthly schedule: {e}")
            return {'success': False, 'error': str(e)}
    
    async def check_racing_day(self, date_str: str, weekday: int) -> Dict:
        """Check if a specific date has racing"""
        try:
            # HKJC typically races on Wednesday, Saturday, Sunday
            # But we should verify with actual schedule
            
            # First check typical racing days
            if weekday in [2, 5, 6]:  # Wednesday, Saturday, Sunday
                # Verify with HKJC schedule
                racing_info = await self.verify_hkjc_schedule(date_str)
                return racing_info
            else:
                # Check for special racing days (holidays, etc.)
                special_info = await self.check_special_racing(date_str)
                return special_info
                
        except Exception as e:
            print(f"❌ Error checking racing day {date_str}: {e}")
            return {'is_racing': False, 'venue': '', 'race_count': 0}
    
    async def verify_hkjc_schedule(self, date_str: str) -> Dict:
        """Verify racing schedule with HKJC website"""
        try:
            # Use Selenium to check HKJC schedule
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Check HKJC racing schedule page
            schedule_url = f"https://racing.hkjc.com/en-us/racing/schedule"
            driver.get(schedule_url)
            time.sleep(3)
            
            page_source = driver.page_source
            
            # Look for the date in the schedule
            if date_str.replace('/', '') in page_source:
                # Extract venue and race count
                venue = self.extract_venue_from_schedule(page_source, date_str)
                race_count = self.extract_race_count_from_schedule(page_source, date_str)
                
                driver.quit()
                return {
                    'is_racing': True,
                    'venue': venue,
                    'race_count': race_count,
                    'meeting_type': 'Regular'
                }
            else:
                driver.quit()
                return {'is_racing': False, 'venue': '', 'race_count': 0}
                
        except Exception as e:
            print(f"❌ HKJC schedule verification failed: {e}")
            return {'is_racing': False, 'venue': '', 'race_count': 0}
    
    async def check_special_racing(self, date_str: str) -> Dict:
        """Check for special racing days (holidays, etc.)"""
        try:
            # This would check for special racing days
            # For now, assume no racing on non-typical days
            return {'is_racing': False, 'venue': '', 'race_count': 0}
            
        except Exception as e:
            print(f"❌ Special racing check failed: {e}")
            return {'is_racing': False, 'venue': '', 'race_count': 0}
    
    def extract_venue_from_schedule(self, page_source: str, date_str: str) -> str:
        """Extract venue from schedule page"""
        try:
            # Look for venue patterns near the date
            patterns = [
                rf'{date_str}.*?Happy Valley',
                rf'{date_str}.*?Sha Tin',
                rf'Happy Valley.*?{date_str}',
                rf'Sha Tin.*?{date_str}'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_source, re.IGNORECASE)
                if match:
                    if 'Happy Valley' in match.group():
                        return 'Happy Valley'
                    elif 'Sha Tin' in match.group():
                        return 'Sha Tin'
            
            return 'Unknown'
            
        except Exception as e:
            print(f"❌ Venue extraction failed: {e}")
            return 'Unknown'
    
    def extract_race_count_from_schedule(self, page_source: str, date_str: str) -> int:
        """Extract race count from schedule page"""
        try:
            # Look for race count patterns
            patterns = [
                rf'{date_str}.*?(\d+)\s+Races',
                rf'{date_str}.*?(\d+)\s+races',
                rf'(\d+)\s+Races.*?{date_str}',
                rf'(\d+)\s+races.*?{date_str}'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    try:
                        return int(matches[0])
                    except:
                        continue
            
            # Default race count for HKJC meetings
            return 10  # Typical HKJC meeting has 8-12 races
            
        except Exception as e:
            print(f"❌ Race count extraction failed: {e}")
            return 10
    
    async def save_monthly_schedule(self):
        """Save monthly schedule to file"""
        try:
            filename = f'/Users/wallace/Documents/ project-sentinel/automation/phase5/racing_schedule_{self.racing_schedule["year"]}_{self.racing_schedule["month"]:02d}.json'
            
            with open(filename, 'w') as f:
                json.dump(self.racing_schedule, f, indent=2)
            
            print(f"💾 Monthly schedule saved to {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save monthly schedule: {e}")
    
    async def generate_monthly_jobs(self) -> Dict:
        """Generate job schedule for the month based on racing days"""
        try:
            if not self.racing_schedule:
                print("❌ No racing schedule available")
                return {'success': False, 'error': 'No schedule available'}
            
            jobs = {
                'racing_jobs': [],
                'non_racing_jobs': [],
                'maintenance_jobs': [],
                'learning_jobs': [],
                'generation_timestamp': datetime.now().isoformat()
            }
            
            # Generate jobs for each day
            for date_str, day_info in self.racing_schedule['schedule_details'].items():
                if day_info['is_racing_day']:
                    # Racing day jobs
                    racing_job = {
                        'date': date_str,
                        'job_type': 'racing_analysis',
                        'tasks': [
                            'collect_race_data',
                            'analyze_all_races',
                            'generate_recommendations',
                            'monitor_betting_opportunities',
                            'collect_race_results',
                            'update_ai_models'
                        ],
                        'priority': 'high',
                        'execution_time': '18:00',  # 6 PM before races
                        'venue': day_info['venue'],
                        'race_count': day_info['race_count']
                    }
                    jobs['racing_jobs'].append(racing_job)
                    
                    # Post-race learning jobs
                    learning_job = {
                        'date': date_str,
                        'job_type': 'post_race_learning',
                        'tasks': [
                            'process_race_results',
                            'analyze_prediction_accuracy',
                            'update_confidence_thresholds',
                            'retrain_ai_models',
                            'generate_performance_report'
                        ],
                        'priority': 'medium',
                        'execution_time': '23:30',  # After races
                        'venue': day_info['venue']
                    }
                    jobs['learning_jobs'].append(learning_job)
                    
                else:
                    # Non-racing day jobs
                    non_racing_job = {
                        'date': date_str,
                        'job_type': 'non_racing_tasks',
                        'tasks': [
                            'system_maintenance',
                            'data_backup',
                            'model_optimization',
                            'market_analysis',
                            'strategy_review',
                            'performance_monitoring'
                        ],
                        'priority': 'low',
                        'execution_time': '10:00'  # Morning maintenance
                    }
                    jobs['non_racing_jobs'].append(non_racing_job)
            
            # Monthly maintenance jobs
            maintenance_job = {
                'date': f"{self.racing_schedule['year']}-{self.racing_schedule['month']:02d}-01",
                'job_type': 'monthly_maintenance',
                'tasks': [
                    'fetch_monthly_schedule',
                    'update_racing_calendar',
                    'system_health_check',
                    'backup_database',
                    'generate_monthly_report',
                    'optimize_system_performance'
                ],
                'priority': 'high',
                'execution_time': '09:00'
            }
            jobs['maintenance_jobs'].append(maintenance_job)
            
            # Save jobs
            await self.save_monthly_jobs(jobs)
            
            return jobs
            
        except Exception as e:
            print(f"❌ Failed to generate monthly jobs: {e}")
            return {'success': False, 'error': str(e)}
    
    async def save_monthly_jobs(self, jobs: Dict):
        """Save monthly jobs to file"""
        try:
            filename = f'/Users/wallace/Documents/ project-sentinel/automation/phase5/monthly_jobs_{self.racing_schedule["year"]}_{self.racing_schedule["month"]:02d}.json'
            
            with open(filename, 'w') as f:
                json.dump(jobs, f, indent=2)
            
            print(f"💾 Monthly jobs saved to {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save monthly jobs: {e}")
    
    async def get_today_job(self) -> Optional[Dict]:
        """Get today's job based on current date"""
        try:
            today = datetime.now()
            today_str = f"{today.year}/{today.month:02d}/{today.day:02d}"
            
            # Load current month schedule
            await self.load_monthly_schedule(today.year, today.month)
            
            if not self.racing_schedule:
                return None
            
            # Load current month jobs
            jobs = await self.load_monthly_jobs(today.year, today.month)
            
            if not jobs:
                return None
            
            # Find today's job
            for job_type in ['racing_jobs', 'non_racing_jobs', 'learning_jobs']:
                for job in jobs.get(job_type, []):
                    if job['date'] == today_str:
                        return job
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to get today's job: {e}")
            return None
    
    async def load_monthly_schedule(self, year: int, month: int):
        """Load monthly schedule from file"""
        try:
            filename = f'/Users/wallace/Documents/ project-sentinel/automation/phase5/racing_schedule_{year}_{month:02d}.json'
            
            with open(filename, 'r') as f:
                self.racing_schedule = json.load(f)
            
            return True
            
        except FileNotFoundError:
            print(f"❌ Schedule file not found for {year}-{month:02d}")
            return False
        except Exception as e:
            print(f"❌ Failed to load monthly schedule: {e}")
            return False
    
    async def load_monthly_jobs(self, year: int, month: int) -> Optional[Dict]:
        """Load monthly jobs from file"""
        try:
            filename = f'/Users/wallace/Documents/ project-sentinel/automation/phase5/monthly_jobs_{year}_{month:02d}.json'
            
            with open(filename, 'r') as f:
                return json.load(f)
            
        except FileNotFoundError:
            print(f"❌ Jobs file not found for {year}-{month:02d}")
            return None
        except Exception as e:
            print(f"❌ Failed to load monthly jobs: {e}")
            return None
    
    async def execute_monthly_schedule_fetch(self):
        """Execute the monthly schedule fetching process"""
        try:
            print("🚀 SENTINEL-RACING AI - MONTHLY SCHEDULE MANAGER")
            print("=" * 60)
            
            today = datetime.now()
            
            # Check if we need to fetch new schedule (first day of month)
            if today.day == 1:
                print(f"📅 First day of month - fetching schedule for {today.year}-{today.month:02d}")
                
                # Fetch monthly schedule
                schedule = await self.fetch_monthly_schedule(today.year, today.month)
                
                if schedule.get('total_days', 0) > 0:
                    print(f"✅ Schedule fetched successfully")
                    print(f"📊 Racing days: {len(schedule['racing_days'])}")
                    print(f"📊 Non-racing days: {len(schedule['non_racing_days'])}")
                    
                    # Generate monthly jobs
                    jobs = await self.generate_monthly_jobs()
                    
                    if jobs:
                        print(f"✅ Monthly jobs generated")
                        print(f"📊 Racing jobs: {len(jobs['racing_jobs'])}")
                        print(f"📊 Learning jobs: {len(jobs['learning_jobs'])}")
                        print(f"📊 Non-racing jobs: {len(jobs['non_racing_jobs'])}")
                        
                        return schedule
                    else:
                        print("❌ Failed to generate monthly jobs")
                else:
                    print("❌ Failed to fetch monthly schedule")
            else:
                print(f"📅 Not first day of month - using existing schedule")
                
                # Load existing schedule
                loaded = await self.load_monthly_schedule(today.year, today.month)
                
                if loaded:
                    print(f"✅ Existing schedule loaded")
                    print(f"📊 Racing days: {len(self.racing_days)}")
                    print(f"📊 Non-racing days: {len(self.non_racing_days)}")
                    
                    # Get today's job
                    today_job = await self.get_today_job()
                    
                    if today_job:
                        print(f"✅ Today's job found: {today_job['job_type']}")
                        print(f"📊 Tasks: {', '.join(today_job['tasks'])}")
                        return today_job
                    else:
                        print("❌ No job found for today")
                else:
                    print("❌ No existing schedule found")
            
            return None
            
        except Exception as e:
            print(f"❌ Monthly schedule execution failed: {e}")
            return None

async def main():
    """Main execution function"""
    schedule_manager = RacingScheduleManager()
    await schedule_manager.setup_session()
    
    try:
        # Execute monthly schedule fetching
        result = await schedule_manager.execute_monthly_schedule_fetch()
        
        if result:
            print("✅ Monthly schedule manager execution successful")
        else:
            print("❌ Monthly schedule manager execution failed")
            
    except Exception as e:
        print(f"❌ Schedule manager failed: {e}")
    
    finally:
        if schedule_manager.session:
            await schedule_manager.session.close()

if __name__ == "__main__":
    asyncio.run(main())

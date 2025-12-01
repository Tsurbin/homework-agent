"""
Lambda-optimized scraper runner that works with DynamoDB instead of SQLite.
Updated to use requests instead of Playwright for Lambda compatibility.
"""
from __future__ import annotations
import os
import logging
import requests
from datetime import date, datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

# Use Lambda-specific logging
logger = logging.getLogger(__name__)

from database.dynamodb_handler import DynamoDBHandler, HomeworkItem

# Environment variables for Lambda
LOGIN_URL = os.environ.get('LOGIN_URL', "https://webtop.smartschool.co.il/account/login")
        # HOMEWORK_URL = os.environ.get('HOMEWORK_URL', "https://webtop.smartschool.co.il/homework")
HOMEWORK_URL = os.environ.get('HOMEWORK_URL', "https://webtop.smartschool.co.il/Student_Card/11")
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'homework-items')


def run_scrape_lambda(historical: bool = False) -> int:
    """
    Run scraper in Lambda environment with DynamoDB storage.
    
    Args:
        historical: If True, scrape all historical data. If False, scrape today's homework.
        
    Returns:
        Number of items inserted/updated
    """
    # Initialize DynamoDB handler
    db = DynamoDBHandler(table_name=DYNAMODB_TABLE_NAME)
    
    # Ensure table exists
    db.create_table_if_not_exists()
    
    # Get credentials
    username = os.environ.get('HW_USERNAME')
    password = os.environ.get('HW_PASSWORD')
    
    if not username or not password:
        raise ValueError("Missing credentials in environment variables")
    
    try:
        # Create session and login
        session = _create_session()
        _login(session, username, password)
        
        if historical:
            return _scrape_historical_data(session, db)
        else:
            return _scrape_daily_data(session, db)
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise


def _create_session():
    """Create and configure requests session."""
    session = requests.Session()
    # session.headers.update({
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    #     'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
    #     'Accept-Encoding': 'gzip, deflate, br',
    #     'Connection': 'keep-alive',
    #     'Upgrade-Insecure-Requests': '1',
    #     'Sec-Fetch-Site': 'none',
    #     'Sec-Fetch-Mode': 'navigate',
    #     'Sec-Fetch-User': '?1',
    #     'Sec-Fetch-Dest': 'document',
    #     'Cache-Control': 'max-age=0'
    # })
    
    session.cookies.set("cookie_consent", "true", domain="https://webtop.smartschool.co.il")
    session.cookies.set("allowCookies", "1", domain="https://webtop.smartschool.co.il")
    
    # Add custom attribute to track current URL
    session.current_url = None
    
    # Disable SSL verification for Lambda compatibility
    session.verify = False
    
    # Configure redirects
    session.max_redirects = 10
    
    # Enable cookie persistence
    session.cookies.clear()
    
    # Pre-set the essential cookie that we discovered manually
    # This is the cookie that gets set when clicking "אשר cookies" 
    # Only set for the main domain to avoid conflicts
    # session.cookies.set(
    #     name='allowCookies',
    #     value='1',
    #     domain='webtop.smartschool.co.il',
    #     path='/',
    #     secure=True
    # )
    
    # Pre-set some common session cookies that might be expected
    # session.cookies.set('sessionInitialized', 'true')
    
    return session


# Helper functions removed for simplified approach


def _login(session, username, password):
    """
    Login to the school website following the auth.py flow but using cookies instead of form interaction.
    This mimics the Playwright auth.py flow but sets the necessary cookies without parsing forms.
    """
    logger.info("Starting simplified cookie-based login process...")
    
    # Step 1: Get initial login page 
    # login_response = session.get(LOGIN_URL, timeout=30)
    # login_response.raise_for_status()
    # logger.info(f"Got initial login page: {login_response.url}")
    
    # url = "https://lgn.edu.gov.il/nidp/wsfed/ep?id=EduCombinedAuthUidPwd&sid=0&option=credential&sid=0"
    init_url = "https://webtopserver.smartschool.co.il/server/api/user/init"
    session.get(init_url, headers={"User-Agent": "Mozilla"}, timeout=30)
    xsrf = session.cookies.get("XSRF-TOKEN")
    
    url = "https://webtopserver.smartschool.co.il/server/api/user/LoginMoe"
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://webtop.smartschool.co.il",
        "Referer": "https://webtop.smartschool.co.il/",
        "Accept": "application/json, text/plain, */*",
        "x-xsrf-token": xsrf,
        "User-Agent": "Mozilla/5.0",
    }
    
    payload = {
        "username": username,
        "password": password,
        "rememberme": 0,
        "language": "he"
    }
    
    login_response = session.post(url, headers=headers, json=payload, timeout=30)
    login_response.raise_for_status()
    logger.info(f"Got initial login page: {login_response.url}")
    logger.info(f"Got initial login page: {login_response.content}")
    logger.info(f"Got initial login page: {login_response.text}")
    logger.info(f"Got initial login page: {login_response.text}")
    
    
    
    # Step 2: Set cookie consent cookie (discovered manually)
    # This is equivalent to clicking "אשר cookies" button in auth.py
    # session.cookies.set(
    #     name='allowCookies',
    #     value='1',
    #     domain='webtop.smartschool.co.il',
    #     path='/',
    #     secure=True
    # )
    logger.info("✅ Set cookie consent: allowCookies=1")
    
    # Step 3: Set education ministry login choice cookie
    # This is equivalent to clicking "הזדהות משרד החינוך" button in auth.py
    # session.cookies.set(
    #     name='loginMethod',
    #     value='education-ministry',
    #     domain='webtop.smartschool.co.il',
    #     path='/',
    #     secure=True
    # )
    logger.info("✅ Set education ministry login method")
    
    # Step 4: Set authentication cookies to simulate successful login
    # Since we can't fill forms, we set cookies that would typically be set after authentication
    
    import hashlib
    session_token = hashlib.md5(f"{username}:{password}".encode()).hexdigest()
    
    # auth_cookies = [
    #     ('username', username),
    #     ('authenticated', 'true'),
    #     ('sessionActive', '1'),
    #     ('sessionToken', session_token),
    #     ('loginComplete', 'true'),
    #     ('userLoggedIn', '1')
    # ]
    
    # for cookie_name, cookie_value in auth_cookies:
    #     session.cookies.set(
    #         name=cookie_name,
    #         value=str(cookie_value),
    #         domain='webtop.smartschool.co.il',
    #         path='/',
    #         secure=True
    #     )
    
    # logger.info("✅ Set authentication cookies")
    
    # Step 5: Test access to homework page to verify login worked
    try:
        homework_response = session.get(HOMEWORK_URL, timeout=30)
        homework_response.raise_for_status()
        
        logger.info(f"✅ Successfully accessed homework page: {homework_response.url}")
        session.current_url = homework_response.url
        
        # Simple check - if we were redirected to login, authentication failed
        if 'login' in homework_response.url.lower():
            logger.warning("⚠️ Redirected to login page - cookie authentication may have failed")
            logger.info("🔄 Will attempt to proceed anyway")
        else:
            logger.info("✅ Cookie-based login appears successful")
            
    except Exception as e:
        logger.warning(f"⚠️ Could not verify homework page access: {e}")
        logger.info("🔄 Will attempt to proceed anyway")
    
    logger.info("✅ Login process completed (cookie-based approach)")


def _scrape_daily_data(session, db: DynamoDBHandler) -> int:
    """Scrape today's homework data using JSON API."""
    logger.info("Scraping daily homework data...")
    
    # Use the JSON API endpoint based on the user's example
    # The API returns structured JSON data instead of HTML
    api_url = "https://webtop.smartschool.co.il/api/studentCard"
    
    # Get the current date for filtering if needed
    today = datetime.now().date().isoformat()
    
    # Parameters for the API call - adjust ID as needed
    params = {
        'id': '11'  # This should be configurable based on student
    }
    
    try:
        # Make API request
        homework_response = session.get(api_url, params=params, timeout=30)
        homework_response.raise_for_status()
        
        logger.info(f"Successfully accessed homework API: {homework_response.url}")
        
        # Parse JSON response
        json_data = homework_response.json()
        homework_items = _parse_homework_from_json(json_data)
        
        # Filter for today's homework if doing daily scrape
        today_items = [item for item in homework_items if item.date == today]
        
        # Save to DynamoDB
        if today_items:
            saved_count = db.upsert_items(today_items)
            logger.info(f"Saved {saved_count} daily homework items")
            return saved_count
        
        logger.info("No homework items found for today")
        return 0
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error accessing homework API: {e}")
        return 0
    except ValueError as e:
        logger.error(f"Error parsing JSON response: {e}")
        return 0


def _scrape_historical_data(session, db: DynamoDBHandler) -> int:
    """Scrape historical homework data."""
    logger.info("Scraping historical homework data...")
    
    # For historical data, you might need to navigate to different pages
    # This is a simplified version - adjust based on actual website structure
    # historical_url = os.environ.get('HISTORICAL_URL', HOMEWORK_URL)
    
    # Use absolute URL or construct from current session
    # if not historical_url.startswith('http') and hasattr(session, 'current_url') and session.current_url:
    #     historical_url = urljoin(session.current_url, historical_url)
    
    # response = session.get(historical_url, timeout=30)
    # response.raise_for_status()
    
    # token_session = session.cookies.get('webToken')
    # print(f"✅ Retrieved webToken from session cookies: {token_session}")
    token = "W%2FT%2FKaL70Rj8h9Lt7WZn4hTdj2%2F259fCZ2%2FU0BZk%2F1nzshfdWxbRU9r0znBxGzNBJku3u%2FithtixDrAQs4H75DDB0IcxUT3E1%2FVf6HM83M3IwYGpz8%2B3NMBlcE6xgFYrlhhYE1FRtOIuy9Odlo2juKXFlYhpOtxUwIObjINvgYTJeow2CxhW%2FefUNG%2Fe%2B0WxZBDaOOncmJTvQPewUYITbc%2BdgvzOogNt%2F3GNI4lTpJXyF4bVtrpO2JGm3PAAtdavXOYPIpUCKga0SlGOMhMTODn91gfZW%2B97s5tWK8o74jMEohAlGolPxHc5K6G%2FaiSRhFwVWUVn0OArsKbN7%2BGySBaIY%2BV%2Bhd3N%2Fi56IRqLKVKByjgXGW2U9EnkODWN3oZya9aVNAwss6ZSIBCgOMJB2eQPI9PfSyxcVlx9ZWnSACJFtw%2BEROdvQri0hN7MjlZOJUCymej7MfGg0WvBn%2Fq4gjmLajVVMN%2B%2FfW7sop0c%2FXfI8ZgpkUB0iE1%2BwlYV6%2BI7ptlaDBXGyPNhhXkraXuvcnyBY3Iy5nVUctpbthOEWLl1CcQXVuybdcWxCeOPb%2Fu38W7IbGRLk5W8Oqx7%2B4xy2USk3tbVcQ%2BPPWhOnFgNtVTmUIFoRdT5OWVooivj%2FMGhiXfZGy9EArUecrKkJzJV0fc7CCq4o0Uvp4VOcZEVdeI2mStXORGoI3P0QMUzCGdePAr%2BcI8mNpMSenumCdxj5DKuVuaROExyZIqpsQ1bjiqLPiVswV8Mr5nMYEWowitSgFUiVuYKBmFABWrMYZP%2B9w%2Bi2q5AXMa27uxvigJ2TUy6UGDAhoFVKWCJABN7JrnMEZbjW8yE0t4T76G5jEwOf2b9cQzmbpHieaqMLDoy4CUsQdk%2Fdlqrfwx5N5PHzES%2FMFZ49pROSd1l9MJtkoJvqjvjQC%2FPe3lOuf%2Bvh7GQcWMdwoaT7tDXlV9eNi8NQCS3ueGVLSpbIdZHpfFflZj9ypyCl6zdkVVfo%2FcosQG2VmPSGnljaIRMkige5IuSbofAqCYyNLb0WfAa6JE2xIP%2F8RhkEpwYa64nUUkVTJiNL%2BieRuwWb9ztS%2FQfF%2FdLzsI6yVBj%2FkRRPCT7AxiF0Ss2FGuuSchH5tmqiYoIp4jVaFnW63JBiV6zj%2BHJ4AcDuRSXJJp7N92k0sFk9rbU5NeRJuqN2HZiNZ5nUXmmGFd%2Fw0fT257I1zSJARlfBHs%2FwtesOsIDeZ8DDtFEGrHkbEAQWqn0CdN5inz7UvgEkI5ooA4tOVtG9mMt%2BDpXIHTho1Yz5W1cW7PoJ6uEGtRYNyD4ARYE6%2B2f9RXz1LoSPPBB5vQ%3D"
    # headers_test = {
    #     "Authorization": f"Bearer {token}",
    #     "Accept": "application/json",
    #     "User-Agent": "Mozilla/5.0"
    # }
    
    
    url = "https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Language": "he",
        "User-Agent": "Mozilla/5.0"
    }

    # Use your webToken from cookies
    web_token = session.cookies.get('webToken')
    # if not web_token:
    #     logger.error("No webToken found in session cookies")
    #     return 0
    
    # Use webToken from session cookies
    cookies = {
        "webToken": token  # token from session
    }
    
    body = {
        "weekIndex": 0,
        "viewType": 0,
        "studyYear": 2026,
        "studyYearName": "תשפ״ו",
        "studentID": "3ox5DRWGJ2ut6K9PfmKFqa/to7hzP+9cTI5lkDZj4I6eJ6GYNQvLjQDVjKJ+KvrnNnTvDfAQKKC4VqmM91P69UM+aUfreFRDpN2+FJOXiAc=",
        "studentName": "בנימיני גבע",
        "classCode": 2,
        "periodID": 3415,
        "periodName": "מחצית א",
        "moduleID": 11
    }
    
    try:
        # Make the API request with proper error handling
        response = session.post(url, headers=headers, cookies=cookies, json=body, verify=False, timeout=30)
        # response = session.post(url, headers=headers, json=body, verify=False, timeout=30)
        response.raise_for_status()
        
        logger.info(f"Successfully accessed historical homework API: {response.url}")
        
        # todo: parse resp to extract homework items
        homework_items = _parse_homework_from_json(response.json(), historical=True)
    
        if homework_items:
            saved_count = db.upsert_items(homework_items)
            logger.info(f"Saved {saved_count} historical homework items")
            return saved_count
        
        logger.info("No historical homework items found")
        return 0
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error accessing historical homework API: {e}")
        return 0
    except ValueError as e:
        logger.error(f"Error parsing historical JSON response: {e}")
        return 0
    
def _parse_homework_from_json(json_response, historical=False):
    """Parse homework items from JSON API response."""
    homework_items = []
    
    try:
        # Check if the response has the expected structure
        if not json_response.get('status') or not json_response.get('data'):
            logger.warning("JSON response missing expected structure")
            return homework_items
        
        data = json_response['data']
        
        # Iterate through each day
        for day_data in data:
            date_str = day_data.get('date', '')
            day_index = day_data.get('dayIndex', 0)
            hours_data = day_data.get('hoursData', [])
            
            logger.info(f"Processing day {day_index} ({date_str[:10]}) with {len(hours_data)} hours")
            
            # Iterate through each hour of the day
            for hour_data in hours_data:
                hour = hour_data.get('hour', 0)
                schedule = hour_data.get('scheduale', [])  # Note: keeping original spelling from API
                
                # Iterate through each scheduled item in this hour
                for schedule_item in schedule:
                    homework_text = (schedule_item.get('homeWork', '') or '').strip()
                    
                    # Only process items that have actual homework
                    if homework_text:
                        subject_name = schedule_item.get('subject_name', '')
                        teacher = schedule_item.get('teacher', '')
                        desc_class = schedule_item.get('descClass', '')
                        
                        # Create homework item
                        homework_item = HomeworkItem(
                            date=date_str[:10] if date_str else datetime.now().date().isoformat(),
                            subject=subject_name,
                            description=homework_text,
                            due_date=None,
                            homework_text=homework_text,
                            # Additional fields that might be useful
                            teacher=teacher if teacher else None,
                            class_description=desc_class,
                            hour=hour,
                        )
                        
                        homework_items.append(homework_item)
                        logger.info(f"Found homework: {subject_name} - {homework_text[:50]}...")
        
        logger.info(f"Total homework items extracted: {len(homework_items)}")
        return homework_items
        
    except Exception as e:
        logger.error(f"Error parsing homework JSON: {e}")
        return homework_items


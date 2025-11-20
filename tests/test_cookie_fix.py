#!/usr/bin/env python3
"""
Test the updated lambda runner with the specific allowCookies cookie.
This tests our requests-based approach with the manually discovered cookie.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_cookie_fixed_login():
    """Test the login with our cookie fix."""
    print("🧪 Testing updated lambda runner with allowCookies=1...")
    
    # Set up environment variables for testing
    os.environ['LOGIN_URL'] = "https://webtop.smartschool.co.il/account/login"
    os.environ['HOMEWORK_URL'] = "https://webtop.smartschool.co.il/homework"
    os.environ['DYNAMODB_TABLE_NAME'] = 'test-homework-items'
    
    # Get credentials
    username = os.environ.get('HW_USERNAME')
    password = os.environ.get('HW_PASSWORD')
    
    if not username or not password:
        print("❌ No credentials found in .env file")
        print("💡 Please add HW_USERNAME and HW_PASSWORD to your .env file")
        return False
    
    print(f"✅ Using credentials for: {username[:3]}***")
    
    try:
        from scraper.lambda_runner_fixed import _create_session, _login
        
        # Test session creation with our cookie
        print("🔧 Creating session with allowCookies=1...")
        session = _create_session()
        
        # Verify the cookie is set
        found_allow_cookie = False
        for cookie in session.cookies:
            if cookie.name == 'allowCookies' and cookie.value == '1':
                found_allow_cookie = True
                print(f"✅ allowCookies=1 cookie found: domain={cookie.domain}")
                break
        
        if not found_allow_cookie:
            print("⚠️ allowCookies cookie not found in session")
        
        print(f"📊 Session has {len(session.cookies)} cookies total")
        for cookie in session.cookies:
            print(f"  🍪 {cookie.name}={cookie.value} (domain: {cookie.domain})")
        
        # Test login process
        print("\n🔐 Attempting login with cookie-fixed session...")
        _login(session, username, password)
        
        print("✅ Login function completed without errors!")
        
        # Check final cookies
        print(f"\n📊 Final session has {len(session.cookies)} cookies:")
        for cookie in session.cookies:
            print(f"  🍪 {cookie.name}={cookie.value} (domain: {cookie.domain})")
        
        # Check if we have session URL
        if hasattr(session, 'current_url') and session.current_url:
            print(f"🌐 Current URL: {session.current_url}")
            
            # Check if we're still on login page
            if 'login' in session.current_url.lower():
                print("⚠️ Still on login page - login might have failed")
                return False
            else:
                print("✅ Redirected away from login page - login likely succeeded!")
                return True
        else:
            print("⚠️ No current URL set")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_request():
    """Test a simple request to see if the cookie helps."""
    print("\n🌐 Testing simple request to login page with allowCookies=1...")
    
    try:
        from scraper.lambda_runner_fixed import _create_session
        import requests
        from bs4 import BeautifulSoup
        
        session = _create_session()
        
        # Make request to login page
        response = session.get("https://webtop.smartschool.co.il/account/login", timeout=30)
        response.raise_for_status()
        
        print(f"✅ Got response: {response.status_code}")
        print(f"📍 Final URL: {response.url}")
        
        # Parse and check for cookie consent
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for cookie consent component
        cookie_component = soup.find('app-allow-cookies')
        if cookie_component:
            print("❌ Still seeing cookie consent component - cookie didn't work")
            
            # Check if it's displayed or hidden
            style = cookie_component.get('style', '')
            classes = cookie_component.get('class', [])
            if 'ng-star-inserted' in classes:
                print("⚠️ Cookie component is marked as inserted (visible)")
            else:
                print("✅ Cookie component might be hidden")
                
        else:
            print("✅ No cookie consent component found - cookie worked!")
        
        # Look for login form more broadly
        forms = soup.find_all('form')
        print(f"📝 Found {len(forms)} forms on the page")
        
        if forms:
            login_form = forms[0]  # Take the first form
            print("✅ Found at least one form")
            
            # Look for input fields
            inputs = login_form.find_all('input')
            print(f"  📋 Form has {len(inputs)} input fields:")
            
            for inp in inputs:
                input_type = inp.get('type', 'unknown')
                input_name = inp.get('name', 'unnamed')
                input_id = inp.get('id', 'no-id')
                print(f"    🔹 {input_type}: name='{input_name}' id='{input_id}'")
            
            # Look specifically for username and password fields
            username_field = None
            password_field = None
            
            for inp in inputs:
                if inp.get('type') == 'password':
                    password_field = inp
                elif (inp.get('type') in ['text', 'email'] or 
                      'username' in (inp.get('name') or '').lower() or
                      'email' in (inp.get('name') or '').lower()):
                    username_field = inp
            
            if username_field and password_field:
                print("✅ Found username and password fields!")
                print(f"  👤 Username: name='{username_field.get('name')}' id='{username_field.get('id')}'")
                print(f"  🔒 Password: name='{password_field.get('name')}' id='{password_field.get('id')}'")
            else:
                print("⚠️ Could not identify username/password fields clearly")
        else:
            print("❌ No forms found on the page")
        
        # Save the HTML for manual inspection
        with open('/tmp/current_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("💾 Saved page HTML to /tmp/current_page.html for inspection")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during simple test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 COOKIE-FIXED LAMBDA RUNNER TEST")
    print("=" * 50)
    
    # Test 1: Simple request with cookie
    test1_result = test_simple_request()
    
    # Test 2: Full login flow
    if test1_result:
        print("\n" + "=" * 50)
        test2_result = test_cookie_fixed_login()
        
        if test2_result:
            print("\n🎉 All tests passed! The allowCookies=1 fix appears to work!")
        else:
            print("\n⚠️ Login test had issues, but basic request worked.")
    else:
        print("\n❌ Basic request test failed - check network connectivity.")
    
    print("\n📋 Summary:")
    print("✅ Discovered cookie: allowCookies=1")
    print("✅ Updated lambda_runner_fixed.py to set this cookie")
    print("✅ Created test to verify cookie handling")
    print("\n💡 Next steps: Run full scraping test or deploy to Lambda")

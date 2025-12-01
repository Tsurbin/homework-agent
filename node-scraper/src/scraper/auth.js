// import { chromium } from 'playwright';
import config from '../config/config.js';

import chromium from '@sparticuz/chromium';
import playwright from 'playwright-core';

export async function loginAndGetWebToken() {

    const browser = await playwright.chromium.launch({
        args: chromium.args,
        executablePath: await chromium.executablePath(),
        headless: chromium.headless,
    });


    const context = await browser.newContext({
        ignoreHTTPSErrors: true, // This will ignore SSL certificate errors
        acceptDownloads: true
    });
    const page = await context.newPage();

    try {
        console.log('Navigating to login page...');
        const response = await page.goto(config.LOGIN_URL, { 
            waitUntil: "networkidle", 
            timeout: 30000 
        });
        
        if (!response) {
            throw new Error("Page failed to load");
        }

       
        // Handle cookie consent if present
        await page.waitForLoadState("networkidle");
        await page.waitForLoadState("networkidle");
        const cookieSelector = "button:has-text('אשר cookies')";
        const cookieButton = page.locator(cookieSelector);
        if (await cookieButton.count() > 0) {
            console.log('Clicking cookie consent...');
            await cookieButton.click();
            await page.waitForLoadState("networkidle");
        }

        // Handle education ministry login button
        const loginPageSelector = "button:has-text('הזדהות משרד החינוך')";
        
        // Wait for the button to exist first
        try {
            await page.waitForLoadState("networkidle");
            await page.waitForSelector(loginPageSelector, { timeout: 10000 });
            console.log('Education ministry button found');
        } catch (error) {
            console.log('Education ministry button not found, continuing...');
        }
        
        const loginButton = page.locator(loginPageSelector);
        if (await loginButton.count() > 0) {
            // Wait for button to be enabled (retry mechanism)
            let retryCount = 0;
            const maxRetries = 10;
            
            while (retryCount < maxRetries) {
                const isDisabled = await loginButton.getAttribute("disabled");
                
                if (isDisabled === "true" || isDisabled === "") {
                    console.log(`Login button is disabled, waiting... (attempt ${retryCount + 1}/${maxRetries})`);
                    await page.waitForTimeout(2000); // Wait 2 seconds
                    retryCount++;
                } else {
                    console.log("The login button is enabled. Clicking...");
                    await loginButton.click();
                    await page.waitForLoadState("networkidle");
                    break;
                }
            }
            
            // If still disabled after all retries, try to proceed anyway
            if (retryCount === maxRetries) {
                console.log("Login button remained disabled, trying to proceed anyway...");
                // Don't throw error, just continue
            }
        }
        // Wait for username field and fill it
        console.log('Filling username...');
        await page.waitForLoadState("networkidle");
        await page.waitForSelector(config.USERNAME_SELECTOR, { timeout: 15000 });
        await page.fill(config.USERNAME_SELECTOR, config.HW_USERNAME);

        // Handle password field with various fallback methods
        console.log('Filling password...');
        const passwordLocator = page.locator(config.PASSWORD_SELECTOR);
        
        try {
            await passwordLocator.waitFor({ state: "attached", timeout: 5000 });
        } catch (error) {
            console.log('Password field attachment wait failed, continuing...');
        }

        try {
            await passwordLocator.focus();
        } catch (error) {
            console.log('Password field focus failed, continuing...');
        }

        try {
            await page.evaluate((selector) => {
                const el = document.querySelector(selector);
                if (el) el.removeAttribute('readonly');
            }, config.PASSWORD_SELECTOR);
        } catch (error) {
            console.log('Removing readonly attribute failed, continuing...');
        }

        // Try to fill password with fallback to typing
        try {
            await passwordLocator.fill(config.HW_PASSWORD, { timeout: 15000 });
        } catch (error) {
            console.log('Direct password fill failed, trying click and type...');
            try {
                await passwordLocator.click();
            } catch (clickError) {
                console.log('Password field click failed, continuing...');
            }
            await page.keyboard.type(config.HW_PASSWORD, { delay: 20 });
        }

        // Submit the form
        console.log('Submitting login form...');
        await page.click(config.SUBMIT_SELECTOR);
        await page.waitForLoadState("networkidle");

        // Wait a bit for cookies to be set
        await page.waitForTimeout(2000);

        // Retrieve the webToken from cookies
        console.log('Extracting webToken from cookies...');
        const cookies = await context.cookies();
        const webTokenCookie = cookies.find(cookie => cookie.name === 'webToken');
        const sessionStorageData = await page.evaluate(() => {
            const data = {};
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                data[key] = sessionStorage.getItem(key);
            }
            return data;
        });

        if (webTokenCookie) {
            console.log('Successfully retrieved webToken');
            
            // Navigate to homework page through UI
            console.log('Navigating to homework page...');
            await navigateToHomeworkPage(page);
            
            return {
                webToken: webTokenCookie.value,
                cookies: cookies, // Return all cookies in case other tokens are needed
                sessionStorage: sessionStorageData,
                page: page, // Return the page for further scraping
                context: context, // Return context to keep session alive
                browser: browser // Return browser to keep it open
            };
        } else {
            console.log('Available cookies:', cookies.map(c => c.name).join(', '));
            throw new Error('webToken cookie not found after login');
        }

    } catch (error) {
        console.error('Login failed:', error);
        if (browser) {
            await browser.close();
        }
        throw error;
    }
    // Don't close browser here anymore - let the calling function handle it
}

async function navigateToHomeworkPage(page) {
    try {
        // Look for "כרטיס תלמיד" button and click it
        console.log('Looking for "כרטיס תלמיד" button...');
        
        // Wait a moment for the page to fully load
        await page.waitForLoadState("networkidle");
        
        // Try different selectors for the student card button
        const studentCardSelectors = [
            'a[href="/Student_Card"]',
            'a[href*="Student_Card"]',
            '[href="/Student_Card"]',
            '[href*="Student_Card"]'
        ];
        
        let studentCardButton = null;
        for (const selector of studentCardSelectors) {
            try {
                await page.waitForSelector(selector, { timeout: 5000 });
                studentCardButton = page.locator(selector).first();
                if (await studentCardButton.count() > 0) {
                    console.log(`Found student card button with selector: ${selector}`);
                    break;
                }
            } catch (e) {
                console.log(`Selector ${selector} not found, trying next...`);
            }
        }
        
        if (!studentCardButton || await studentCardButton.count() === 0) {
            // Try clicking the parent element that contains the text
            console.log('Trying to find clickable parent element...');
            const parentButton = page.locator('.mat-list-item-content:has-text("כרטיס תלמיד")');
            if (await parentButton.count() > 0) {
                studentCardButton = parentButton;
                console.log('Found parent element containing "כרטיס תלמיד"');
            }
        }
        
        if (studentCardButton && await studentCardButton.count() > 0) {
            console.log('Clicking "כרטיס תלמיד" button...');
            await studentCardButton.click();
            await page.waitForLoadState("networkidle");
            await page.waitForTimeout(2000);
            
            // Now look for "נושאי שיעור ושיעורי-בית" button
            console.log('Looking for "נושאי שיעור ושיעורי-בית" button...');
            
            const homeworkSelectors = [
                'a[href="/Student_Card/11"]'
            ];
            
            let homeworkButton = null;
            for (const selector of homeworkSelectors) {
                try {
                    await page.waitForSelector(selector, { timeout: 5000 });
                    homeworkButton = page.locator(selector).first();
                    if (await homeworkButton.count() > 0) {
                        console.log(`Found homework button with selector: ${selector}`);
                        break;
                    }
                } catch (e) {
                    console.log(`Homework selector ${selector} not found, trying next...`);
                }
            }
            
            if (homeworkButton && await homeworkButton.count() > 0) {
                console.log('Clicking "נושאי שיעור ושיעורי-בית" button...');
                await homeworkButton.click();
                await page.waitForLoadState("networkidle");
                await page.waitForTimeout(2000);
                console.log('Successfully navigated to homework page');
            } else {
                console.warn('Could not find "נושאי שיעור ושיעורי-בית" button');
            }
        } else {
            console.warn('Could not find "כרטיס תלמיד" button');
        }
        
    } catch (error) {
        console.error('Error navigating to homework page:', error);
        throw error;
    }
}


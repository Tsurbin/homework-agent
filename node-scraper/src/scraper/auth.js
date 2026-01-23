import { chromium } from 'playwright';
import config from '../config/config.js';

/**
 * Performs login and returns browser session WITHOUT navigating to any specific page.
 * Use this when you need to navigate to multiple pages or a custom destination.
 * 
 * @returns {Promise<{page: Page, context: BrowserContext, browser: Browser}>}
 */
export async function loginAndGetSession() {
    const isHeadless = process.env.PLAYWRIGHT_HEADLESS !== 'false';
    console.log(`Launching browser in ${isHeadless ? 'headless' : 'visible'} mode`);
    
    const browser = await chromium.launch({
        headless: isHeadless,
    });

    const context = await browser.newContext({
        ignoreHTTPSErrors: true,
        acceptDownloads: true
    });
    const page = await context.newPage();

    try {
        await performLogin(page);
        
        return {
            page,
            context,
            browser
        };
    } catch (error) {
        console.error('Login failed:', error);
        await safeCloseBrowser(browser);
        throw error;
    }
}

/**
 * @deprecated Use loginAndGetSession() + navigateToHomeworkPage() instead.
 * Kept for backward compatibility with existing code.
 * 
 * Performs login and navigates directly to the homework page.
 * @returns {Promise<{page: Page, context: BrowserContext, browser: Browser}>}
 */
export async function loginAndGetWebToken() {

    // Use regular Playwright for local development
    // Set headless based on environment variable, default to true to save memory
    const isHeadless = process.env.PLAYWRIGHT_HEADLESS !== 'false';
    console.log(`Launching browser in ${isHeadless ? 'headless' : 'visible'} mode`);
    
    const browser = await chromium.launch({
        headless: isHeadless,
    });


    const context = await browser.newContext({
        ignoreHTTPSErrors: true, // This will ignore SSL certificate errors
        acceptDownloads: true
    });
    const page = await context.newPage();

    try {
        console.log('Navigating to login page...');
        const response = await page.goto(config.LOGIN_URL, { 
            waitUntil: "domcontentloaded", // Less strict than networkidle for slow connections
            timeout: 60000 // Increased timeout for slow internet
        });
        
        if (!response) {
            throw new Error("Page failed to load");
        }

       
        // Handle cookie consent if present
        await page.waitForTimeout(3000); // Give page time to settle with slow connection
        await page.waitForLoadState("domcontentloaded");
        
        // Try multiple selectors for the cookie button
        const cookieSelectors = [
            'button:has-text("אשר cookies")',
            'button.filled:has-text("אשר")',
            'button[aria-label="אשר cookies"]'
        ];
        
        let cookieClicked = false;
        for (const selector of cookieSelectors) {
            const cookieButton = page.locator(selector);
            if (await cookieButton.count() > 0) {
                console.log(`Clicking cookie consent with selector: ${selector}`);
                await cookieButton.click();
                await page.waitForTimeout(2000); // Wait for animation/transition
                cookieClicked = true;
                break;
            }
        }
        
        if (!cookieClicked) {
            console.log('Cookie consent button not found, continuing...');
        }

        // Handle education ministry login button
        const loginPageSelectors = [
            'button:has-text("הזדהות משרד החינוך")',
            'button.outline:has-text("הזדהות")',
            'button[aria-label="הזדהות משרד החינוך"]'
        ];
        
        let loginButton = null;
        for (const selector of loginPageSelectors) {
            try {
                await page.waitForTimeout(1000); // Brief pause for slow connections
                await page.waitForSelector(selector, { timeout: 10000 }); // Increased timeout
                const button = page.locator(selector);
                if (await button.count() > 0) {
                    console.log(`Education ministry button found with selector: ${selector}`);
                    loginButton = button;
                    break;
                }
            } catch (error) {
                console.log(`Selector ${selector} not found, trying next...`);
            }
        }
        
        if (!loginButton) {
            console.log('Education ministry button not found with any selector, continuing...');
        }
        if (loginButton && await loginButton.count() > 0) {
            // Wait for button to be enabled (retry mechanism)
            let retryCount = 0;
            const maxRetries = 10;
            
            while (retryCount < maxRetries) {
                const isDisabled = await loginButton.getAttribute("disabled");
                
                // Check if button is disabled (can be "true", "", or the attribute exists)
                // If getAttribute returns null, the button is enabled
                if (isDisabled !== null && isDisabled !== "false") {
                    console.log(`Login button is disabled, waiting... (attempt ${retryCount + 1}/${maxRetries})`);
                    await page.waitForTimeout(2000); // Wait 2 seconds
                    retryCount++;
                } else {
                    console.log("The login button is enabled. Clicking...");
                    try {
                        // Try to click the button with force option and wait for navigation
                        await loginButton.click({ force: true });
                        console.log('Button clicked, waiting for navigation...');
                        await page.waitForTimeout(3000); // Give time for navigation with slow connection
                    } catch (clickError) {
                        console.log('Regular click failed, trying JavaScript click...');
                        // Fallback: use JavaScript click
                        await page.evaluate(() => {
                            const btn = document.querySelector('button[aria-label*="הזדהות"]') || 
                                       document.querySelector('button.outline');
                            if (btn) {
                                btn.click();
                                console.log('JavaScript click executed');
                            }
                        });
                        await page.waitForTimeout(3000); // Give time for navigation with slow connection
                    }
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
        await page.waitForTimeout(2000); // Give page time to settle
        await page.waitForSelector(config.USERNAME_SELECTOR, { timeout: 20000 }); // Increased timeout
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
        console.log('Form submitted, waiting for login to complete...');
        await page.waitForTimeout(5000); // Increased wait for slow connection + login processing
        await navigateToHomeworkPage(page);

        return {
            page: page, // Return the page for further scraping
            context: context, // Return context to keep session alive
            browser: browser // Return browser to keep it open
        };
    } catch (error) {
        console.error('Login or navigate to homework page failed:', error);
        if (browser) {
            await browser.close();
        }
        throw error;
    }
    // Don't close browser here anymore - let the calling function handle it
}

/**
 * Navigate to the Homework page after login.
 * @param {Page} page - Playwright page object (must be logged in)
 * @returns {Promise<void>}
 */
export async function navigateToHomeworkPage(page) {
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

/**
 * Navigate to the Weekly Plan page after login.
 * @param {Page} page - Playwright page object (must be logged in)
 * @returns {Promise<boolean>} - true if navigation successful
 */
export async function navigateToWeeklyPlanPage(page) {
    try {
        console.log('Navigating to Weekly Plan page...');
        
        // Wait for the page to be in a stable state after login
        await page.waitForLoadState("networkidle");
        
        // Navigate directly to the Weekly Plan URL
        const response = await page.goto(config.WEEKLY_PLAN_URL, {
            waitUntil: "domcontentloaded",
            timeout: config.NAVIGATION_TIMEOUT
        });
        
        if (!response) {
            throw new Error("Weekly Plan page failed to load");
        }
        
        // Verify we're on the correct page (not redirected to login)
        const currentUrl = page.url();
        if (currentUrl.includes('/account/login')) {
            throw new Error('Session expired - redirected to login page');
        }
        
        // Wait for page content to load
        await page.waitForLoadState("networkidle");
        await page.waitForTimeout(2000); // Allow dynamic content to render
        
        // Validate that we're on the Weekly Plan page
        const isWeeklyPlanPage = await validateWeeklyPlanPage(page);
        if (!isWeeklyPlanPage) {
            console.warn('Warning: Page may not be the Weekly Plan page, but continuing...');
        }
        
        console.log('✅ Successfully navigated to Weekly Plan page');
        return true;
        
    } catch (error) {
        console.error('Error navigating to Weekly Plan page:', error);
        throw error;
    }
}

/**
 * Validate that the current page is the Weekly Plan page.
 * @param {Page} page - Playwright page object
 * @returns {Promise<boolean>}
 */
async function validateWeeklyPlanPage(page) {
    try {
        const currentUrl = page.url();
        
        // Check URL contains Weekly_Plan
        if (!currentUrl.includes('Weekly_Plan')) {
            console.warn(`Unexpected URL: ${currentUrl}`);
            return false;
        }
        
        // Check for page-specific elements
        const hasContent = await page.evaluate(() => {
            // Look for the main weekly schedule component (note: typo in original HTML "scedule")
            const weeklySchedule = document.querySelector('app-weekly-scedule');
            if (!weeklySchedule) return false;
            
            // Look for the schedule grid
            const grid = document.querySelector('div.grid[role="grid"]');
            if (!grid) return false;
            
            // Look for day column headers
            const dayHeaders = document.querySelectorAll('div.schedule-day[role="columnheader"]');
            if (dayHeaders.length === 0) return false;
            
            return true;
        });
        
        return hasContent;
    } catch (error) {
        console.warn('Error validating Weekly Plan page:', error);
        return false;
    }
}

/**
 * Internal function to perform the actual login steps.
 * Separated to allow reuse and cleaner error handling.
 * @param {Page} page - Playwright page object
 */
async function performLogin(page) {
    console.log('Navigating to login page...');
    const response = await page.goto(config.LOGIN_URL, { 
        waitUntil: "domcontentloaded",
        timeout: 60000
    });
    
    if (!response) {
        throw new Error("Login page failed to load");
    }

    // Handle cookie consent if present
    await page.waitForTimeout(3000);
    await page.waitForLoadState("domcontentloaded");
    
    await handleCookieConsent(page);
    await handleEducationMinistryLogin(page);
    await fillCredentials(page);
    await submitLoginForm(page);
}

/**
 * Handle cookie consent dialog if present.
 * @param {Page} page
 */
async function handleCookieConsent(page) {
    const cookieSelectors = [
        'button:has-text("אשר cookies")',
        'button.filled:has-text("אשר")',
        'button[aria-label="אשר cookies"]'
    ];
    
    for (const selector of cookieSelectors) {
        const cookieButton = page.locator(selector);
        if (await cookieButton.count() > 0) {
            console.log(`Clicking cookie consent with selector: ${selector}`);
            await cookieButton.click();
            await page.waitForTimeout(2000);
            return;
        }
    }
    console.log('Cookie consent button not found, continuing...');
}

/**
 * Handle education ministry login button if present.
 * @param {Page} page
 */
async function handleEducationMinistryLogin(page) {
    const loginPageSelectors = [
        'button:has-text("הזדהות משרד החינוך")',
        'button.outline:has-text("הזדהות")',
        'button[aria-label="הזדהות משרד החינוך"]'
    ];
    
    let loginButton = null;
    for (const selector of loginPageSelectors) {
        try {
            await page.waitForTimeout(1000);
            await page.waitForSelector(selector, { timeout: 10000 });
            const button = page.locator(selector);
            if (await button.count() > 0) {
                console.log(`Education ministry button found with selector: ${selector}`);
                loginButton = button;
                break;
            }
        } catch (error) {
            console.log(`Selector ${selector} not found, trying next...`);
        }
    }
    
    if (!loginButton || await loginButton.count() === 0) {
        console.log('Education ministry button not found, continuing...');
        return;
    }

    // Wait for button to be enabled (retry mechanism)
    let retryCount = 0;
    const maxRetries = 10;
    
    while (retryCount < maxRetries) {
        const isDisabled = await loginButton.getAttribute("disabled");
        
        if (isDisabled !== null && isDisabled !== "false") {
            console.log(`Login button is disabled, waiting... (attempt ${retryCount + 1}/${maxRetries})`);
            await page.waitForTimeout(2000);
            retryCount++;
        } else {
            console.log("The login button is enabled. Clicking...");
            try {
                await loginButton.click({ force: true });
                console.log('Button clicked, waiting for navigation...');
                await page.waitForTimeout(3000);
            } catch (clickError) {
                console.log('Regular click failed, trying JavaScript click...');
                await page.evaluate(() => {
                    const btn = document.querySelector('button[aria-label*="הזדהות"]') || 
                               document.querySelector('button.outline');
                    if (btn) btn.click();
                });
                await page.waitForTimeout(3000);
            }
            return;
        }
    }
    
    console.log("Login button remained disabled after all retries, continuing anyway...");
}

/**
 * Fill username and password credentials.
 * @param {Page} page
 */
async function fillCredentials(page) {
    // Fill username
    console.log('Filling username...');
    await page.waitForTimeout(2000);
    await page.waitForSelector(config.USERNAME_SELECTOR, { timeout: 20000 });
    await page.fill(config.USERNAME_SELECTOR, config.HW_USERNAME);

    // Fill password with fallback methods
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
}

/**
 * Submit the login form and wait for completion.
 * @param {Page} page
 */
async function submitLoginForm(page) {
    console.log('Submitting login form...');
    await page.click(config.SUBMIT_SELECTOR);
    console.log('Form submitted, waiting for login to complete...');
    await page.waitForTimeout(5000);
}

/**
 * Safely close browser, handling any errors.
 * @param {Browser} browser
 */
async function safeCloseBrowser(browser) {
    try {
        if (browser) {
            await browser.close();
        }
    } catch (closeError) {
        console.error('Error closing browser:', closeError);
    }
}

/**
 * Helper to safely close all browser resources.
 * @param {{page?: Page, context?: BrowserContext, browser?: Browser}} session
 */
export async function closeSession(session) {
    try {
        if (session.page) await session.page.close();
    } catch (e) {
        console.error('Error closing page:', e);
    }
    try {
        if (session.context) await session.context.close();
    } catch (e) {
        console.error('Error closing context:', e);
    }
    try {
        if (session.browser) await session.browser.close();
    } catch (e) {
        console.error('Error closing browser:', e);
    }
}

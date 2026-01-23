import { loginAndGetSession, navigateToWeeklyPlanPage, closeSession } from './auth.js';
import config from '../config/config.js';

/**
 * Fetch weekly plan data by logging in and scraping the Weekly Plan page.
 * @returns {Promise<Array>} Array of weekly plan items
 */
export async function fetchWeeklyPlanData() {
    let session = null;
    
    try {
        console.log('Starting weekly plan scraping process...');
        
        // Login and get browser session
        session = await loginAndGetSession();
        const { page } = session;
        console.log('✅ Login successful');

        // Navigate to Weekly Plan page
        await navigateToWeeklyPlanPage(page);
        console.log('✅ Navigated to Weekly Plan page');

        // Scrape weekly plan data from the page
        const weeklyPlanData = await scrapeWeeklyPlanFromPage(page);
        console.log(`✅ Scraped ${weeklyPlanData.length} weekly plan items from page`);
        
        return weeklyPlanData;

    } catch (error) {
        console.error('Error fetching weekly plan data:', error);
        throw error;
    } finally {
        // Clean up browser resources
        if (session) {
            await closeSession(session);
        }
    }
}

/**
 * Scrape weekly plan data from the page.
 * @param {Page} page - Playwright page object
 * @returns {Promise<Array>} Array of weekly plan items
 */
async function scrapeWeeklyPlanFromPage(page) {
    console.log('Scraping weekly plan data from page...');
    
    try {
        // Wait for the weekly plan content to load
        await page.waitForLoadState("networkidle");
        await page.waitForTimeout(2000); // Allow dynamic content to render
        
        // Wait for the grid to be present
        await page.waitForSelector('div.grid[role="grid"]', { timeout: 10000 });
        
        // Extract weekly plan data from the page
        const weeklyPlanData = await page.evaluate(() => {
            const planItems = [];
            
            // Get the week date range for metadata
            const dateRangeElement = document.querySelector('.date-range-text span');
            const weekDateRange = dateRangeElement ? dateRangeElement.textContent.trim() : '';
            
            // Get all day column headers to map dateIndex to actual dates
            const dayHeaders = document.querySelectorAll('div.schedule-day[role="columnheader"]');
            const dateMap = {};
            
            dayHeaders.forEach((header, index) => {
                // Extract date from header (format: "18/01 כ״ט טֵבֵת")
                const headerText = header.textContent.trim();
                const dateMatch = headerText.match(/(\d{1,2})\/(\d{1,2})/);
                
                if (dateMatch) {
                    const day = dateMatch[1].padStart(2, '0');
                    const month = dateMatch[2].padStart(2, '0');
                    // Get year from the week range or current year
                    const yearMatch = weekDateRange.match(/\/(\d{4})/);
                    const year = yearMatch ? yearMatch[1] : new Date().getFullYear().toString();
                    dateMap[index] = `${year}-${month}-${day}`;
                }
                
                // Also extract day name
                const dayNameMatch = headerText.match(/(ראשון|שני|שלישי|רביעי|חמישי|שישי|שבת)/);
                if (dayNameMatch && dateMap[index]) {
                    dateMap[index] = {
                        date: dateMap[index],
                        dayName: dayNameMatch[1]
                    };
                } else if (dateMap[index]) {
                    dateMap[index] = {
                        date: dateMap[index],
                        dayName: ''
                    };
                }
            });
            
            // Get all event wrappers
            const eventWrappers = document.querySelectorAll('div.event-wrapper');
            
            eventWrappers.forEach((wrapper) => {
                try {
                    // Extract hourIndex and dateIndex from the wrapper ID
                    // Format: hourIndex_X_dateIndex_Y_eventIndex_Z
                    const wrapperId = wrapper.id || '';
                    const hourMatch = wrapperId.match(/hourIndex_(\d+)/);
                    const dateMatch = wrapperId.match(/dateIndex_(\d+)/);
                    
                    if (!hourMatch || !dateMatch) {
                        return; // Skip if we can't determine position
                    }
                    
                    const hourIndex = parseInt(hourMatch[1], 10);
                    const dateIndex = parseInt(dateMatch[1], 10);
                    
                    // Get the event data component
                    const eventData = wrapper.querySelector('app-event-data');
                    if (!eventData) return;
                    
                    // Extract teacher name
                    const teacherElement = eventData.querySelector('.gray-text');
                    const teacher = teacherElement ? teacherElement.textContent.trim() : '';
                    
                    // Extract subject/description from bold text
                    const boldElement = eventData.querySelector('.bold-text.focus');
                    let subject = '';
                    let classDescription = '';
                    
                    if (boldElement) {
                        const boldText = boldElement.textContent.trim();
                        
                        // Split by " - " to separate subject from details
                        const parts = boldText.split(' - ');
                        subject = parts[0] || '';
                        
                        // The rest contains study group info and type (שיעור)
                        if (parts.length > 1) {
                            // Remove the "(שיעור)" suffix and extract the meaningful part
                            classDescription = parts.slice(1).join(' - ')
                                .replace(/\(שיעור\)\s*$/, '')
                                .trim();
                        }
                    }
                    
                    // Extract comments - look for additional divs after the bold text
                    let comments = '';
                    const allDivs = eventData.querySelectorAll('div');
                    let foundBold = false;
                    
                    for (const div of allDivs) {
                        if (div.classList.contains('bold-text')) {
                            foundBold = true;
                            continue;
                        }
                        if (foundBold && !div.classList.contains('gray-text')) {
                            const text = div.textContent.trim();
                            // Skip empty divs or divs that only contain whitespace/br
                            if (text && text !== '' && !/^\s*$/.test(text)) {
                                comments = text;
                                break;
                            }
                        }
                    }
                    
                    // Get the date info from our map
                    const dateInfo = dateMap[dateIndex];
                    const date = dateInfo ? dateInfo.date : '';
                    const dayName = dateInfo ? dateInfo.dayName : '';
                    
                    // Class number is hourIndex + 1 (1-based)
                    const classNumber = hourIndex + 1;
                    
                    // Create a sanitized teacher name for the key (remove spaces, special chars)
                    const teacherKey = teacher.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_\u0590-\u05FF]/g, '');
                    
                    // Create the plan item
                    const item = {
                        id: `plan_${date}_${classNumber}_${teacherKey}`,
                        date: date,
                        dayName: dayName,
                        classNumber: classNumber,
                        teacher: teacher,
                        subject: subject,
                        classDescription: classDescription,
                        classComments: comments,
                        extractedAt: new Date().toISOString()
                    };
                    
                    planItems.push(item);
                    
                } catch (e) {
                    console.error('Error processing event wrapper:', e);
                }
            });
            
            return {
                items: planItems,
                metadata: {
                    scrapedAt: new Date().toISOString(),
                    pageUrl: window.location.href,
                    pageTitle: document.title,
                    weekDateRange: weekDateRange,
                    totalDaysFound: dayHeaders.length,
                    totalPlanItems: planItems.length
                }
            };
        });
        
        console.log('Weekly plan scraping results:', {
            itemCount: weeklyPlanData.items.length,
            metadata: weeklyPlanData.metadata
        });
        
        return weeklyPlanData.items;
        
    } catch (error) {
        console.error('Error scraping weekly plan from page:', error);
        
        // Try to get page content for debugging
        try {
            const pageTitle = await page.title();
            const pageUrl = page.url();
            console.log('Current page info:', { pageTitle, pageUrl });
            
            // Get some page text for debugging
            const pageText = await page.evaluate(() => document.body.textContent?.substring(0, 500));
            console.log('Page content preview:', pageText);
        } catch (debugError) {
            console.error('Error getting debug info:', debugError);
        }
        
        return [];
    }
}

/**
 * Fetch weekly plan data using an existing session (for combined scraping).
 * @param {Page} page - Playwright page object (must be logged in)
 * @returns {Promise<Array>} Array of weekly plan items
 */
export async function fetchWeeklyPlanDataWithSession(page) {
    try {
        console.log('Navigating to Weekly Plan page...');
        await navigateToWeeklyPlanPage(page);
        console.log('✅ Navigated to Weekly Plan page');
        
        const weeklyPlanData = await scrapeWeeklyPlanFromPage(page);
        console.log(`✅ Scraped ${weeklyPlanData.length} weekly plan items`);
        
        return weeklyPlanData;
    } catch (error) {
        console.error('Error fetching weekly plan data with session:', error);
        throw error;
    }
}

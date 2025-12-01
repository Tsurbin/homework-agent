import { loginAndGetWebToken } from './auth.js';
import config from '../config/config.js';
import axios from 'axios';
import https from "https";

export async function fetchHomeworkData(historical = false) {
    try {
        // Login and navigate to homework page using UI
        console.log('Starting login and navigation process...');
        const authData = await loginAndGetWebToken();
        const { webToken, cookies, sessionStorage, page, context, browser } = authData;
        console.log(`✅ Retrieved webToken and navigated to homework page`);

        try {
            // Scrape homework data directly from the page
            const homeworkData = await scrapeHomeworkFromPage(page);
            console.log(`✅ Scraped ${homeworkData.length} homework items from page`);
            return homeworkData;
        } finally {
            // Clean up browser resources
            if (page) await page.close();
            if (context) await context.close();
            if (browser) await browser.close();
        }

    } catch (error) {
        console.error('Error fetching homework data:', error);
        throw error;
    }
}

async function scrapeHomeworkFromPage(page) {
    console.log('Scraping homework data from page...');
    
    try {
        // Wait for the homework content to load
        await page.waitForLoadState("networkidle");
        await page.waitForTimeout(2000);//remove
        
        // Extract homework data from the page
        const homeworkData = await page.evaluate(() => {
            const homeworkItems = [];
            
            // Look for all mat-card elements (each represents a day)
            const dayCards = document.querySelectorAll('mat-card');
            
            dayCards.forEach((card, cardIndex) => {
                // Extract the date from the card title
                const titleElement = card.querySelector('.card-title');
                const dayTitle = titleElement ? titleElement.textContent.trim() : `Day ${cardIndex + 1}`;
                
                // Extract date from title (format: "יום ראשון | 16/11/2025 | כ״ה חֶשְׁוָן תשפ״ו")
                const dateMatch = dayTitle.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/);
                let date = '';
                if (dateMatch) {
                    const day = dateMatch[1].padStart(2, '0');
                    const month = dateMatch[2].padStart(2, '0');
                    const year = dateMatch[3];
                    date = `${year}-${month}-${day}`; // Convert to YYYY-MM-DD format
                }
                
                // Look for all lesson rows in this card
                const lessonRows = card.querySelectorAll('.lesson-homework');
                
                lessonRows.forEach((row, rowIndex) => {
                    try {
                        // Extract lesson information
                        const cells = row.querySelectorAll('[role="cell"]');
                        
                        if (cells.length >= 6) {
                            const hour = cells[0] ? cells[0].textContent.trim() : '';
                            const subject = cells[1] ? cells[1].textContent.trim() : '';
                            const teacher = cells[2] ? cells[2].textContent.trim() : '';
                            const status = cells[3] ? cells[3].textContent.trim() : '';
                            const lessonTopic = cells[4] ? cells[4].textContent.trim() : '';
                            const homeworkCell = cells[5];
                            
                            // Extract homework content - look for the actual homework text
                            let homeworkText = '';
                            if (homeworkCell) {
                                // Find the .font-small element which contains the actual homework
                                const homeworkElement = homeworkCell.querySelector('.font-small');
                                if (homeworkElement) {
                                    homeworkText = homeworkElement.textContent.trim();
                                }
                            }
                            
                            // Only create item if there's actual homework content
                            if (homeworkText && homeworkText.length > 0) {
                                const item = {
                                    id: `homework_${cardIndex}_${rowIndex}`,
                                    date: date,
                                    dayTitle: dayTitle,
                                    hour: `${hour}`,
                                    subject: subject,
                                    teacher: teacher,
                                    status: status,
                                    lessonTopic: lessonTopic.replace(/^נושא שיעור:\s*/, ''), // Remove prefix
                                    homeworkText: homeworkText,
                                    description: homeworkText,
                                    extractedAt: new Date().toISOString()
                                };
                                
                                homeworkItems.push(item);
                            }
                        }
                    } catch (e) {
                        console.error('Error processing lesson row:', e);
                    }
                });
            });
            
            return {
                items: homeworkItems,
                metadata: {
                    scrapedAt: new Date().toISOString(),
                    pageUrl: window.location.href,
                    pageTitle: document.title,
                    totalDaysFound: dayCards.length,
                    totalHomeworkItems: homeworkItems.length
                }
            };
        });
        
        console.log('Homework scraping results:', {
            itemCount: homeworkData.items.length,
            metadata: homeworkData.metadata
        });
        
        return homeworkData.items;
        
    } catch (error) {
        console.error('Error scraping homework from page:', error);
        
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

async function fetchDailyHomework(webToken) {
    console.log('Fetching daily homework data...');
    
    const apiUrl = "https://webtop.smartschool.co.il/api/studentCard";
    const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
    
    try {
        const response = await axios.get(apiUrl, {
            params: { id: '11' }, // This should be configurable based on student
            headers: {
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0',
                'Cookie': `webToken=${webToken}`
            },
            timeout: 30000
        });

        console.log('✅ Successfully accessed homework API');
        
        const homeworkItems = parseHomeworkFromJson(response.data);
        
        // Filter for today's homework
        const todayItems = homeworkItems.filter(item => item.date === today);
        
        console.log(`Found ${todayItems.length} homework items for today`);
        return todayItems;

    } catch (error) {
        console.error('Error accessing homework API:', error);
        return [];
    }
}

async function fetchHistoricalHomework(webToken, cookies, sessionStorage) {
    console.log('Fetching historical homework data...');
    
    const url = "https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework";
    
    const cookiesString = cookies.map(c => `${c.name}=${c.value}`).join("; ");
    
    console.log('Session storage keys:', Object.keys(sessionStorage));
    console.log('Available session data:', sessionStorage);

    // Use the exact same headers that worked in Python
    const headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Language": "he",
        "User-Agent": "Mozilla/5.0"
    };

    // Use the exact same body parameters that worked in Python
    const body = {
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
    };

    console.log('Request body:', JSON.stringify(body, null, 2));
    console.log('Request headers:', headers);
    
    try {
        const agent = new https.Agent({
            rejectUnauthorized: false,   // <-- BYPASS SSL CERT VALIDATION
        });

        console.log('Making POST request to:', url);
        
        // Pass webToken as cookie like in Python implementation
        const config = {
            headers,
            timeout: 30000,
            withCredentials: true,
            httpsAgent: agent,
        };

        // Add webToken as cookie
        if (webToken) {
            config.headers.Cookie = `webToken=${webToken}`;
            console.log('Using webToken as cookie:', webToken.substring(0, 20) + '...');
        }

        const response = await axios.post(url, body, config);

        console.log('✅ Successfully accessed historical homework API');
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        console.log('Response data preview:', JSON.stringify(response.data).substring(0, 200));
        
        const homeworkItems = parseHomeworkFromJson(response.data, true);
        
        console.log(`Found ${homeworkItems.length} total homework items`);
        return homeworkItems;

    } catch (error) {
        console.error('❌ Error accessing historical homework API:');
        
        if (error.response) {
            // Server responded with error status
            console.error('Status:', error.response.status);
            console.error('Status Text:', error.response.statusText);
            console.error('Response Headers:', error.response.headers);
            console.error('Response Data:', error.response.data);
        } else if (error.request) {
            // Request was made but no response
            console.error('No response received:', error.request);
        } else {
            // Something else happened
            console.error('Error setting up request:', error.message);
        }
        
        console.error('Full error:', error);
        return [];
    }
}

function parseHomeworkFromJson(jsonResponse, historical = false) {
    const homeworkItems = [];
    
    try {
        // Check if the response has the expected structure
        if (!jsonResponse.status || !jsonResponse.data) {
            console.warn('JSON response missing expected structure');
            return homeworkItems;
        }
        
        const data = jsonResponse.data;
        
        // Iterate through each day
        for (const dayData of data) {
            const dateStr = dayData.date || '';
            const dayIndex = dayData.dayIndex || 0;
            const hoursData = dayData.hoursData || [];
            
            console.log(`Processing day ${dayIndex} (${dateStr.substring(0, 10)}) with ${hoursData.length} hours`);
            
            // Iterate through each hour of the day
            for (const hourData of hoursData) {
                const hour = hourData.hour || 0;
                const schedule = hourData.scheduale || []; // Note: keeping original spelling from API
                
                // Iterate through each scheduled item in this hour
                for (const scheduleItem of schedule) {
                    const homeworkText = (scheduleItem.homeWork || '').trim();
                    
                    // Only process items that have actual homework
                    if (homeworkText) {
                        const subjectName = scheduleItem.subject_name || '';
                        const teacher = scheduleItem.teacher || '';
                        const descClass = scheduleItem.descClass || '';
                        
                        // Create homework item
                        const homeworkItem = {
                            date: dateStr.substring(0, 10) || new Date().toISOString().split('T')[0],
                            subject: subjectName,
                            description: homeworkText,
                            dueDate: null,
                            homeworkText: homeworkText,
                            // Additional fields that might be useful
                            teacher: teacher || null,
                            classDescription: descClass,
                            hour: hour,
                            createdAt: new Date().toISOString()
                        };
                        
                        homeworkItems.push(homeworkItem);
                        console.log(`Found homework: ${subjectName} - ${homeworkText.substring(0, 50)}...`);
                    }
                }
            }
        }
        
        console.log(`Total homework items extracted: ${homeworkItems.length}`);
        return homeworkItems;
        
    } catch (error) {
        console.error('Error parsing homework JSON:', error);
        return homeworkItems;
    }
}
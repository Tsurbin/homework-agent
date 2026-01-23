// Load environment variables from .env file
import dotenv from 'dotenv';
dotenv.config();

import { fetchHomeworkData } from './scraper/homework.js';
import { fetchWeeklyPlanData, fetchWeeklyPlanDataWithSession } from './scraper/weeklyPlan.js';
import { loginAndGetSession, navigateToHomeworkPage, closeSession } from './scraper/auth.js';
import { DynamoDBHandler, WeeklyPlanDynamoDBHandler } from './scraper/dynamodb.js';
import config from './config/config.js';

/**
 * Main scraper function that can be run with different modes
 */
export async function runHomeworkScraper(options = {}) {
    const {
        historical = false,
        saveToDynamoDB = true,
        tableName = process.env.DYNAMODB_TABLE_NAME || 'homework-items'
    } = options;

    try {
        console.log('🚀 Starting homework scraper...');
        console.log(`Mode: ${historical ? 'Historical' : 'Daily'}`);
        
        // Fetch homework data using Playwright + API calls
        const homeworkItems = await fetchHomeworkData(historical);
        
        if (homeworkItems.length === 0) {
            console.log('ℹ️ No homework items found');
            return 0;
        }

        console.log(`📚 Found ${homeworkItems.length} homework items`);
        
        // Save to DynamoDB if requested
        if (saveToDynamoDB) {
            console.log('💾 Saving to DynamoDB...');
            
            const dbHandler = new DynamoDBHandler(tableName);
            await dbHandler.createTableIfNotExists();
            
            const savedCount = await dbHandler.upsertItems(homeworkItems);
            console.log(`✅ Saved ${savedCount} items to DynamoDB`);
            
            return savedCount;
        } else {
            // Just return the items without saving
            console.log('📄 Returning homework items without saving');
            return homeworkItems;
        }

    } catch (error) {
        console.error('❌ Scraper failed:', error);
        throw error;
    }
}

/**
 * Lambda handler function for AWS Lambda
 */
export async function lambdaHandler(event) {
    try {
        const historical = event.historical || false;
        const count = await runHomeworkScraper({ historical });
        
        return {
            statusCode: 200,
            body: JSON.stringify({
                message: `Successfully processed ${count} homework items`,
                itemsProcessed: count,
                timestamp: new Date().toISOString()
            })
        };
    } catch (error) {
        console.error('Lambda execution failed:', error);
        
        return {
            statusCode: 500,
            body: JSON.stringify({
                error: error.message,
                timestamp: new Date().toISOString()
            })
        };
    }
}

/**
 * CLI function for local testing
 */
export async function runCLI() {
    const args = process.argv.slice(2);
    
    // Debug: show received arguments
    if (args.length > 0) {
        console.log(`📋 CLI arguments received: ${args.join(', ')}`);
    }
    
    const historical = args.includes('--historical');
    const noDynamoDB = args.includes('--no-dynamodb');
    const weeklyPlanOnly = args.includes('--weekly-plan');
    const allScrapers = args.includes('--all');
    const showHelp = args.includes('--help') || args.includes('-h');
    
    if (showHelp) {
        console.log(`
📚 Homework & Weekly Plan Scraper CLI

Usage: 
  node src/index.js [options]
  npm start -- [options]      (note: use -- to pass args through npm)

Options:
  --homework      Scrape homework only (default)
  --weekly-plan   Scrape weekly plan only
  --all           Scrape both homework and weekly plan (shared session)
  --historical    Include historical data (homework only)
  --no-dynamodb   Don't save to DynamoDB, just print results
  --help, -h      Show this help message

Examples:
  node src/index.js                        # Scrape homework and save to DynamoDB
  node src/index.js --weekly-plan          # Scrape weekly plan and save to DynamoDB
  node src/index.js --all                  # Scrape both with shared session
  node src/index.js --all --no-dynamodb    # Scrape both and print results
  npm start -- --weekly-plan               # Via npm (note the --)
        `);
        process.exit(0);
    }
    
    try {
        let result;
        
        if (allScrapers) {
            // Run both scrapers with shared session
            result = await runAllScrapers({ 
                saveToDynamoDB: !noDynamoDB 
            });
            
            if (noDynamoDB) {
                console.log('\n📋 Combined Results:');
                console.log(JSON.stringify(result, null, 2));
            } else {
                console.log(`\n✅ Successfully processed:`);
                console.log(`   📚 Homework: ${result.homework} items`);
                console.log(`   📅 Weekly Plan: ${result.weeklyPlan} items`);
            }
        } else if (weeklyPlanOnly) {
            // Run weekly plan scraper only
            result = await runWeeklyPlanScraper({ 
                saveToDynamoDB: !noDynamoDB 
            });
            
            if (noDynamoDB) {
                console.log('\n📋 Weekly Plan Items:');
                console.log(JSON.stringify(result.weeklyPlan, null, 2));
            } else {
                console.log(`\n✅ Successfully processed ${result.weeklyPlan} weekly plan items`);
            }
        } else {
            // Default: Run homework scraper only
            result = await runHomeworkScraper({ 
                historical, 
                saveToDynamoDB: !noDynamoDB 
            });
            
            if (noDynamoDB) {
                console.log('\n📋 Homework Items:');
                console.log(JSON.stringify(result, null, 2));
            } else {
                console.log(`\n✅ Successfully processed ${result} homework items`);
            }
        }
        
        process.exit(0);
    } catch (error) {
        console.error('\n❌ CLI execution failed:', error);
        process.exit(1);
    }
}

/**
 * Run weekly plan scraper
 */
export async function runWeeklyPlanScraper(options = {}) {
    const {
        saveToDynamoDB = true,
        tableName = config.WEEKLY_PLAN_TABLE_NAME
    } = options;

    try {
        console.log('🚀 Starting weekly plan scraper...');
        
        // Fetch weekly plan data using Playwright
        const weeklyPlanItems = await fetchWeeklyPlanData();
        
        if (weeklyPlanItems.length === 0) {
            console.log('ℹ️ No weekly plan items found');
            return { weeklyPlan: 0 };
        }

        console.log(`📅 Found ${weeklyPlanItems.length} weekly plan items`);
        
        // Save to DynamoDB if requested
        if (saveToDynamoDB) {
            console.log('💾 Saving weekly plan to DynamoDB...');
            
            const dbHandler = new WeeklyPlanDynamoDBHandler(tableName);
            await dbHandler.createTableIfNotExists();
            
            const savedCount = await dbHandler.upsertItems(weeklyPlanItems);
            console.log(`✅ Saved ${savedCount} weekly plan items to DynamoDB`);
            
            return { weeklyPlan: savedCount };
        } else {
            console.log('📄 Returning weekly plan items without saving');
            return { weeklyPlan: weeklyPlanItems };
        }

    } catch (error) {
        console.error('❌ Weekly plan scraper failed:', error);
        throw error;
    }
}

/**
 * Run all scrapers with a shared session (Plan B - sequential execution)
 * This is more efficient as it reuses the same browser session.
 */
export async function runAllScrapers(options = {}) {
    const {
        saveToDynamoDB = true,
        homeworkTableName = config.DYNAMODB_TABLE_NAME,
        weeklyPlanTableName = config.WEEKLY_PLAN_TABLE_NAME
    } = options;

    let session = null;
    const results = {
        homework: 0,
        weeklyPlan: 0
    };

    try {
        console.log('🚀 Starting combined scraper (homework + weekly plan)...');
        
        // Login once and get browser session
        session = await loginAndGetSession();
        const { page } = session;
        console.log('✅ Login successful');

        // --- Scrape Homework ---
        console.log('\n📚 --- Scraping Homework ---');
        try {
            await navigateToHomeworkPage(page);
            
            // Wait for content to load
            await page.waitForLoadState("networkidle");
            await page.waitForTimeout(2000);
            
            // Scrape homework using page.evaluate (similar to homework.js)
            const homeworkData = await scrapeHomeworkFromPageDirect(page);
            console.log(`Found ${homeworkData.length} homework items`);
            
            if (saveToDynamoDB && homeworkData.length > 0) {
                const homeworkDB = new DynamoDBHandler(homeworkTableName);
                await homeworkDB.createTableIfNotExists();
                results.homework = await homeworkDB.upsertItems(homeworkData);
                console.log(`✅ Saved ${results.homework} homework items to DynamoDB`);
            } else {
                results.homework = homeworkData;
            }
        } catch (homeworkError) {
            console.error('❌ Homework scraping failed:', homeworkError);
            // Continue to weekly plan even if homework fails
        }

        // --- Scrape Weekly Plan ---
        console.log('\n📅 --- Scraping Weekly Plan ---');
        try {
            const weeklyPlanData = await fetchWeeklyPlanDataWithSession(page);
            console.log(`Found ${weeklyPlanData.length} weekly plan items`);
            
            if (saveToDynamoDB && weeklyPlanData.length > 0) {
                const weeklyPlanDB = new WeeklyPlanDynamoDBHandler(weeklyPlanTableName);
                await weeklyPlanDB.createTableIfNotExists();
                results.weeklyPlan = await weeklyPlanDB.upsertItems(weeklyPlanData);
                console.log(`✅ Saved ${results.weeklyPlan} weekly plan items to DynamoDB`);
            } else {
                results.weeklyPlan = weeklyPlanData;
            }
        } catch (weeklyPlanError) {
            console.error('❌ Weekly plan scraping failed:', weeklyPlanError);
        }

        console.log('\n✅ Combined scraping complete:', results);
        return results;

    } catch (error) {
        console.error('❌ Combined scraper failed:', error);
        throw error;
    } finally {
        // Clean up browser resources
        if (session) {
            await closeSession(session);
        }
    }
}

/**
 * Helper function to scrape homework directly from a page.
 * Used by runAllScrapers to avoid creating a new browser session.
 */
async function scrapeHomeworkFromPageDirect(page) {
    // This is a copy of the scraping logic from homework.js
    // to allow reuse with shared session
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
                date = `${year}-${month}-${day}`;
            }
            
            // Look for all lesson rows in this card
            const lessonRows = card.querySelectorAll('.lesson-homework');
            
            lessonRows.forEach((row, rowIndex) => {
                try {
                    const cells = row.querySelectorAll('[role="cell"]');
                    
                    if (cells.length >= 6) {
                        const hour = cells[0] ? cells[0].textContent.trim() : '';
                        const subject = cells[1] ? cells[1].textContent.trim() : '';
                        const teacher = cells[2] ? cells[2].textContent.trim() : '';
                        const status = cells[3] ? cells[3].textContent.trim() : '';
                        const lessonTopic = cells[4] ? cells[4].textContent.trim() : '';
                        const homeworkCell = cells[5];
                        
                        let homeworkText = '';
                        if (homeworkCell) {
                            const homeworkElement = homeworkCell.querySelector('.font-small');
                            if (homeworkElement) {
                                homeworkText = homeworkElement.textContent.trim();
                            }
                        }
                        
                        if (homeworkText && homeworkText.length > 0) {
                            const item = {
                                id: `homework_${cardIndex}_${rowIndex}`,
                                date: date,
                                dayTitle: dayTitle,
                                hour: `${hour}`,
                                subject: subject,
                                teacher: teacher,
                                status: status,
                                lessonTopic: lessonTopic.replace(/^נושא שיעור:\s*/, ''),
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
        
        return homeworkItems;
    });
    
    return homeworkData;
}

// Run CLI if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    runCLI();
}
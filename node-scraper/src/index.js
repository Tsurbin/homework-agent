import { fetchHomeworkData } from './scraper/homework.js';
import { DynamoDBHandler } from './scraper/dynamodb.js';
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
    const historical = args.includes('--historical');
    const noDynamoDB = args.includes('--no-dynamodb');
    
    try {
        const result = await runHomeworkScraper({ 
            historical, 
            saveToDynamoDB: !noDynamoDB 
        });
        
        if (noDynamoDB) {
            console.log('\n📋 Homework Items:');
            console.log(JSON.stringify(result, null, 2));
        } else {
            console.log(`\n✅ Successfully processed ${result} homework items`);
        }
        
        process.exit(0);
    } catch (error) {
        console.error('\n❌ CLI execution failed:', error);
        process.exit(1);
    }
}

// Run CLI if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    runCLI();
}
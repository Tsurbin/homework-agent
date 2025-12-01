import { fetchHomeworkData } from './src/scraper/homework.js';
import { DynamoDBHandler } from './src/scraper/dynamodb.js';
import AWS from 'aws-sdk';

// Initialize AWS services
const secretsManager = new AWS.SecretsManager({
    region: process.env.AWS_REGION || 'us-east-1'
});

/**
 * Retrieve credentials from AWS Secrets Manager
 */
async function getCredentials() {
    try {
        const secretName = process.env.SECRETS_MANAGER_SECRET_NAME;
        if (!secretName) {
            throw new Error('SECRETS_MANAGER_SECRET_NAME environment variable not set');
        }

        console.log(`Retrieving credentials from Secrets Manager: ${secretName}`);
        
        const result = await secretsManager.getSecretValue({
            SecretId: secretName
        }).promise();

        const credentials = JSON.parse(result.SecretString);
        
        if (!credentials.username || !credentials.password) {
            throw new Error('Invalid credentials format in Secrets Manager');
        }

        return credentials;
    } catch (error) {
        console.error('Failed to retrieve credentials from Secrets Manager:', error);
        throw error;
    }
}

/**
 * AWS Lambda handler for homework scraping
 * Triggered by EventBridge on a schedule
 */
export const handler = async (event, context) => {
    console.log('Starting homework scraper Lambda function');
    console.log('Event:', JSON.stringify(event, null, 2));
    
    const startTime = Date.now();
    let result = {
        success: false,
        itemsScraped: 0,
        itemsSaved: 0,
        error: null,
        executionTimeMs: 0
    };

    try {
        // Get credentials from Secrets Manager
        const credentials = await getCredentials();
        
        // Set credentials as environment variables for the scraper
        process.env.HW_USERNAME = credentials.username;
        process.env.HW_PASSWORD = credentials.password;
        
        // Initialize DynamoDB handler
        const tableName = process.env.DYNAMODB_TABLE_NAME || 'homework-items';
        const dynamoHandler = new DynamoDBHandler(tableName);
        
        // Ensure table exists
        await dynamoHandler.createTableIfNotExists();
        console.log('✅ DynamoDB table ready');

        // Scrape homework data
        console.log('Starting homework data scraping...');
        const homeworkItems = await fetchHomeworkData(true); // Use historical mode
        
        result.itemsScraped = homeworkItems.length;
        console.log(`✅ Scraped ${homeworkItems.length} homework items`);

        if (homeworkItems.length > 0) {
            // Save to DynamoDB
            const savedCount = await dynamoHandler.upsertItems(homeworkItems);
            result.itemsSaved = savedCount;
            console.log(`✅ Saved ${savedCount} items to DynamoDB`);
        }

        result.success = true;
        result.executionTimeMs = Date.now() - startTime;

        console.log('✅ Lambda execution completed successfully');
        console.log('Result:', result);

        return {
            statusCode: 200,
            body: JSON.stringify({
                message: 'Homework scraping completed successfully',
                ...result
            })
        };

    } catch (error) {
        result.error = error.message;
        result.executionTimeMs = Date.now() - startTime;
        
        console.error('❌ Lambda execution failed:', error);
        console.error('Stack trace:', error.stack);

        // Don't throw the error - return it as a response
        // This prevents Lambda from retrying on application errors
        return {
            statusCode: 500,
            body: JSON.stringify({
                message: 'Homework scraping failed',
                ...result
            })
        };
    }
};

/**
 * Local testing function
 * Run with: node lambda-handler.js
 */
if (process.argv[1].endsWith('lambda-handler.js')) {
    (async () => {
        console.log('Running Lambda handler locally for testing...');
        
        const mockEvent = {
            source: 'aws.events',
            detail: {
                test: 'local-run'
            }
        };
        
        const mockContext = {
            functionName: 'homework-scraper-local',
            functionVersion: '1',
            invokeid: 'local-test',
            getRemainingTimeInMillis: () => 300000
        };

        try {
            const result = await handler(mockEvent, mockContext);
            console.log('Local test result:', result);
        } catch (error) {
            console.error('Local test failed:', error);
            process.exit(1);
        }
    })();
}
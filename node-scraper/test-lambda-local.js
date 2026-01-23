#!/usr/bin/env node

/**
 * Local test script for the Lambda handler
 * 
 * This simulates a Lambda invocation locally by:
 * 1. Loading credentials from .env file (instead of Secrets Manager)
 * 2. Calling the Lambda handler directly
 * 
 * Usage:
 *   node test-lambda-local.js
 *   
 *   # Or with npm script:
 *   npm run test:lambda
 */

import dotenv from 'dotenv';
dotenv.config();

// Verify credentials are set
if (!process.env.HW_USERNAME || !process.env.HW_PASSWORD) {
    console.error('❌ Error: HW_USERNAME and HW_PASSWORD must be set in .env file');
    process.exit(1);
}

console.log('🧪 Testing Lambda handler locally...\n');

// Import the runAllScrapers function directly (same as Lambda uses)
import { runAllScrapers } from './src/index.js';

async function testLambdaLocally() {
    const startTime = Date.now();
    
    // Simulate Lambda event
    const event = {
        source: 'local-test',
        schedule: 'manual'
    };
    
    console.log('Event:', JSON.stringify(event, null, 2));
    console.log('\n' + '='.repeat(50) + '\n');
    
    try {
        // Run the same code the Lambda handler runs
        const results = await runAllScrapers({
            saveToDynamoDB: true  // Set to false if you don't want to save
        });
        
        const duration = Date.now() - startTime;
        
        console.log('\n' + '='.repeat(50));
        console.log(`\n✅ Lambda test completed in ${duration}ms`);
        console.log('Results:', JSON.stringify(results, null, 2));
        
        // Simulate Lambda response
        const response = {
            statusCode: 200,
            body: JSON.stringify({
                message: 'Scraping completed',
                results: results,
                duration: `${duration}ms`,
                timestamp: new Date().toISOString()
            })
        };
        
        console.log('\nLambda Response:');
        console.log(JSON.stringify(JSON.parse(response.body), null, 2));
        
    } catch (error) {
        console.error('\n❌ Lambda test failed:', error);
        
        // Simulate Lambda error response
        const response = {
            statusCode: 500,
            body: JSON.stringify({
                error: error.message,
                timestamp: new Date().toISOString()
            })
        };
        
        console.log('\nLambda Response:');
        console.log(JSON.stringify(JSON.parse(response.body), null, 2));
        
        process.exit(1);
    }
}

testLambdaLocally();

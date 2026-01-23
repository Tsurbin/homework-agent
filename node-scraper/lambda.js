/**
 * AWS Lambda handler for the Homework & Weekly Plan Scraper
 * This is a thin wrapper that uses the existing scraper code
 * with Lambda-specific configuration (Secrets Manager for credentials)
 */

import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';
import { runAllScrapers } from './src/index.js';

const CONFIG = {
    SECRETS_NAME: process.env.SECRETS_NAME || 'homework-scraper-credentials',
    // Secrets are stored in us-east-1, Lambda runs in il-central-1
    SECRETS_REGION: process.env.SECRETS_REGION || 'us-east-1'
};

let cachedCredentials = null;

/**
 * Fetch credentials from AWS Secrets Manager and set them as env vars
 */
async function loadCredentialsFromSecretsManager() {
    if (cachedCredentials) {
        return cachedCredentials;
    }

    const client = new SecretsManagerClient({ region: CONFIG.SECRETS_REGION });
    
    try {
        console.log(`Fetching credentials from Secrets Manager: ${CONFIG.SECRETS_NAME} (region: ${CONFIG.SECRETS_REGION})`);
        const command = new GetSecretValueCommand({
            SecretId: CONFIG.SECRETS_NAME
        });
        
        const response = await client.send(command);
        cachedCredentials = JSON.parse(response.SecretString);
        
        // Map secret keys to environment variables expected by existing code
        // Secret uses: username, password
        // Code expects: HW_USERNAME, HW_PASSWORD
        process.env.HW_USERNAME = cachedCredentials.username;
        process.env.HW_PASSWORD = cachedCredentials.password;
        
        console.log('✅ Credentials loaded from Secrets Manager');
        return cachedCredentials;
    } catch (error) {
        console.error('Error fetching credentials from Secrets Manager:', error);
        throw error;
    }
}

/**
 * Main Lambda handler
 */
export async function handler(event) {
    console.log('🚀 Lambda handler invoked');
    console.log('Event:', JSON.stringify(event, null, 2));
    
    const startTime = Date.now();

    try {
        // Load credentials from Secrets Manager (sets env vars for existing code)
        await loadCredentialsFromSecretsManager();
        
        // Use the existing runAllScrapers function
        const results = await runAllScrapers({
            saveToDynamoDB: true
        });
        
        const duration = Date.now() - startTime;
        console.log(`\n✅ Lambda execution completed in ${duration}ms`);
        
        return {
            statusCode: 200,
            body: JSON.stringify({
                message: 'Scraping completed',
                results: results,
                duration: `${duration}ms`,
                timestamp: new Date().toISOString()
            })
        };
        
    } catch (error) {
        console.error('❌ Lambda execution failed:', error);
        
        return {
            statusCode: 500,
            body: JSON.stringify({
                error: error.message,
                stack: error.stack,
                timestamp: new Date().toISOString()
            })
        };
    }
}

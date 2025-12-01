import { test, expect } from '@playwright/test';
import { login } from '../src/scraper/auth';

test.describe('Scraper Tests', () => {
    let webToken;

    test.beforeAll(async ({ browser }) => {
        const context = await browser.newContext();
        const page = await context.newPage();
        
        // Perform login and retrieve webToken
        webToken = await login(page);
        
        await context.close();
    });

    test('should retrieve homework data after login', async ({ browser }) => {
        const context = await browser.newContext();
        const page = await context.newPage();

        // Set the webToken in cookies
        await context.addCookies([{ name: 'webToken', value: webToken, domain: 'webtop.smartschool.co.il' }]);

        // Navigate to the homework page
        await page.goto('https://webtop.smartschool.co.il/homework');

        // Verify that the homework data is displayed
        const homeworkData = await page.locator('.homework-item'); // Adjust selector as needed
        await expect(homeworkData).toHaveCountGreaterThan(0);

        await context.close();
    });
});
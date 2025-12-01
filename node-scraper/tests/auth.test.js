import { test, expect } from '@playwright/test';
import { login } from '../src/scraper/auth';

test.describe('Authentication Tests', () => {
    test('User can log in and retrieve webToken', async ({ page }) => {
        const username = process.env.HW_USERNAME;
        const password = process.env.HW_PASSWORD;

        // Navigate to the login page
        await page.goto('https://webtop.smartschool.co.il/account/login');

        // Perform login
        const webToken = await login(page, username, password);

        // Check if webToken is retrieved
        expect(webToken).toBeDefined();
        expect(webToken).not.toBe('');
    });
});
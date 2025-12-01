// Configuration settings for the Playwright scraper application

const config = {
    LOGIN_URL: process.env.LOGIN_URL || "https://webtop.smartschool.co.il/account/login",
    HOMEWORK_URL: process.env.HOMEWORK_URL || "https://webtop.smartschool.co.il/Student_Card/11",
    HW_USERNAME: process.env.HW_USERNAME,
    HW_PASSWORD: process.env.HW_PASSWORD,
    DYNAMODB_TABLE_NAME: process.env.DYNAMODB_TABLE_NAME || 'homework-items',
    
    // Add these selectors based on your actual form
    USERNAME_SELECTOR: '#userName', // Update with actual selector
    PASSWORD_SELECTOR: '#password', // Update with actual selector
    SUBMIT_SELECTOR: 'button[type="submit"]',     // Update with actual selector
};

export default config;
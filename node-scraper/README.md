# Playwright Scraper

This project is a web scraper built using Playwright, designed to automate the login process and retrieve homework data from a specified web application. The scraper is containerized using Docker for easy deployment and management.

## Project Structure

```
playwright-scraper
├── src
│   ├── index.js          # Entry point for the application
│   ├── scraper
│   │   ├── auth.js      # Handles authentication and login
│   │   ├── homework.js   # Functions for scraping homework data
│   │   └── utils.js      # Utility functions for various tasks
│   └── config
│       └── config.js     # Configuration settings and constants
├── docker
│   ├── Dockerfile        # Dockerfile for building the application image
│   └── docker-compose.yml # Docker Compose configuration
├── tests
│   ├── auth.test.js      # Tests for authentication functionality
│   └── scraper.test.js    # Tests for scraping functionality
├── .dockerignore          # Files to ignore when building Docker image
├── .gitignore             # Files to ignore in Git
├── package.json           # npm configuration file
├── playwright.config.js    # Playwright configuration settings
└── README.md              # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd playwright-scraper
   ```

2. **Install dependencies:**
   ```
   npm install
   ```

3. **Configure environment variables:**
   Create a `.env` file in the root directory and add your configuration settings, such as login credentials and URLs.

4. **Build the Docker image:**
   ```
   docker-compose build
   ```

5. **Run the application:**
   ```
   docker-compose up
   ```

## Usage

- The application will automatically log in to the specified web application and retrieve homework data.
- You can modify the scraping logic in `src/scraper/homework.js` to suit your needs.

## Testing

- Run the tests using the following command:
  ```
  npm test
  ```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
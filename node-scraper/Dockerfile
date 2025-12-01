# Use Node.js 18 with Alpine Linux for a smaller image
FROM node:18-alpine

# Install dependencies for Playwright
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont

# Tell Playwright to use the installed Chromium
ENV PLAYWRIGHT_BROWSERS_PATH=0
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium-browser

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm ci --only=production

# We already installed system chromium, so skip Playwright browser installation
# RUN npx playwright install --with-deps chromium

# Copy source code
COPY src/ ./src/

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs
RUN adduser -S scraper -u 1001
USER scraper

# Set environment variables
ENV NODE_ENV=production
ENV PLAYWRIGHT_HEADLESS=true

# Expose port for health checks (if needed)
EXPOSE 3000

# Default command
CMD ["node", "src/index.js"]
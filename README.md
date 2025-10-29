# Homework Agent

A private agent to scrape and summarize your child's homework from school websites.

## Setup

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your school website credentials
   ```

4. **Update selectors:**
   - Edit `config/settings.json` with the correct CSS selectors for your school's website
   - Update URLs in `scraper/runner.py` to match your school's login and homework pages

## Usage

### Manual Scraping
```bash
# Run a single scrape
python main.py --scrape

# View today's homework
python main.py --today

# View homework for specific date
python main.py --list 2024-01-15
```

### Daily Scheduling
```bash
# Start the daily scheduler (runs at 6 PM)
python scheduler.py
```

## Architecture

- **scraper/**: Web scraping and data extraction
- **agent/**: AI processing (Phase 2)
- **data/**: SQLite database for homework storage
- **config/**: Configuration files

## Next Steps

- Phase 2: Add AI agent for natural language queries
- Phase 3: WhatsApp integration
- Phase 4: Full automation and error handling

#!/bin/bash
# Activate virtual environment and run homework agent
source venv/bin/activate
echo "Virtual environment activated!"
echo "Python: $(which python)"
echo "Available commands:"
echo "  python main.py --scrape    # Run a single scrape"
echo "  python main.py --today     # View today's homework"
echo "  python scheduler.py        # Start daily scheduler"
echo ""
exec "$@"

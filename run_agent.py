"""
Run the Homework Agent against the existing data in the DB.

Usage examples:

# Interactive mode (asks questions until you quit):
# Use your venv python if needed: /home/tzur/projects/homework-agent-2/venv/bin/python run_agent.py --interactive

# Single question for today's homework:
# /home/tzur/projects/homework-agent-2/venv/bin/python run_agent.py --question "What's my homework for today?"

# Single question for a specific date (dry-run to see filtered data without calling the LLM):
# /home/tzur/projects/homework-agent-2/venv/bin/python run_agent.py --date 2025-10-26 --question "List homework" --dry-run

The script will:
- Read homework items from the DB for the provided date (defaults to today)
- Convert DB rows to the dict format expected by the agent/LLM
- Either print the filtered homework (dry-run) or call the LLM and print the response

Make sure you have your environment configured and optionally set ANTHROPIC_API_KEY in a .env file.
"""

import argparse
import asyncio
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import os

# load .env if present
load_dotenv()

from agent.llm_handler import LLMHandler
from scraper.db import HomeworkDB


def homework_items_to_dict(items):
    """Convert list[HomeworkItem] -> {subject: {date: {description, due_date, subject}}}
    """
    homework_data = {}
    for item in items:
        subj = item.subject
        if subj not in homework_data:
            homework_data[subj] = {}
        homework_data[subj][item.date] = {
            'description': item.description,
            'due_date': item.due_date,
            'subject': item.subject,
            'homework_text': item.homework_text,
            "date": item.date,
        }
    return homework_data


async def ask_llm(question: str, homework_data: dict, dry_run: bool = False) -> str:
    if dry_run:
        # Return a string representation of the homework that would be passed to the LLM
        return f"DRY RUN - filtered homework passed to LLM:\n{homework_data}"

    # Use LLMHandler directly; it expects (question, homework_data)
    llm = LLMHandler()
    # Basic check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        return "No ANTHROPIC_API_KEY found in environment. Set it in .env or environment to call the LLM."

    response = await llm.get_response(question, homework_data)
    return response


def get_homework_for_date(db: HomeworkDB, date_str: str):
    # The DB provides list_by_date(date) which returns HomeworkItem objects
    return db.list_by_date(date_str)

def get_all_homework(db: HomeworkDB):
    return db.list()

async def run_single(date: str, question: str, dry_run: bool):
    db = HomeworkDB()
    if date is None:
        items = get_all_homework(db)
    else:
        items = get_homework_for_date(db, date)
    homework_data = homework_items_to_dict(items)

    print(f"Loaded {len(items)} item(s) for {date}")
    if not items:
        print("No homework found for that date.")
    
    result = await ask_llm(question, homework_data, dry_run=dry_run)
    print('\n--- Response ---')
    print(result)


async def interactive_loop(date: Optional[str], dry_run: bool):
    db = HomeworkDB()
    if date is None:
        items = get_all_homework(db)
    else:
        items = get_homework_for_date(db, date)
    homework_data = homework_items_to_dict(items)
    print(f"Loaded {len(items)} item(s) for {date}")
    if not items:
        print("No homework found for that date.")

    print("Enter questions about the homework (type 'exit' or Ctrl-C to quit)")
    while True:
        try:
            q = input('> ').strip()
            if not q:
                continue
            if q.lower() in ('exit', 'quit'):
                break

            result = await ask_llm(q, homework_data, dry_run=dry_run)
            print('\n--- Response ---')
            print(result)
            print('\n')
        except KeyboardInterrupt:
            print('\nExiting...')
            break


def main():
    p = argparse.ArgumentParser(description='Run the homework agent against existing DB data')
    p.add_argument('--date', '-d', help='Date to query (YYYY-MM-DD). Defaults to today')
    p.add_argument('--question', '-q', help='Single question to ask the agent')
    p.add_argument('--interactive', '-i', action='store_true', help='Start interactive question loop')
    p.add_argument('--dry-run', action='store_true', help='Print filtered homework instead of calling the LLM')

    args = p.parse_args()

    # Basic validation of date format
    try:
        if args.date:
            datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        print('Invalid date format. Use YYYY-MM-DD')
        return

    if not args.interactive and not args.question:
        print('Provide --question or --interactive. Use --help for details.')
        return

    if args.question:
        asyncio.run(run_single(args.date, args.question, args.dry_run))
    else:
        asyncio.run(interactive_loop(args.date, args.dry_run))


if __name__ == '__main__':
    main()

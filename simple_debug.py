#!/usr/bin/env python3
"""
Simple debugging example - shows how to use breakpoints
"""
import ipdb

def example_function():
    """Example function with multiple breakpoints"""
    print("Starting function...")
    
    # BREAKPOINT 1: Add this line anywhere you want to pause
    ipdb.set_trace()
    
    name = "Homework Agent"
    print(f"Processing: {name}")
    
    # BREAKPOINT 2: Another breakpoint
    ipdb.set_trace()
    
    items = ["Math", "Science", "English"]
    for item in items:
        print(f"  - {item}")
    
    # BREAKPOINT 3: Final breakpoint
    ipdb.set_trace()
    
    return f"Completed processing {len(items)} items"

if __name__ == "__main__":
    result = example_function()
    print(f"Result: {result}")

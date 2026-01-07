#!/bin/bash

# Install Playwright browsers
playwright install chromium

# Install system dependencies for Playwright
playwright install-deps chromium

# Run the bot
python bot.py

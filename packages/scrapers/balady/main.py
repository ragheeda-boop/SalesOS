#!/usr/bin/env python3
"""Balady Engineering Offices Scraper - Main Entry Point"""

import sys
import os

# Ensure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

from scraper import BaladyScraper


def main():
    scraper = BaladyScraper(log_dir=script_dir)
    offices = scraper.scrape()
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ProfitBot

A web scraper that finds deals on DoneDeal and helps identify resale opportunities. Currently scrapes listings and filters out the junk to find actual items worth looking at.

## What it does

- Scrapes DoneDeal for any search term (phones, laptops, etc.)
- Filters out irrelevant stuff like car ads, cases, and accessories 
- Removes duplicates and invalid listings
- Saves clean data to Excel with price analysis
- Shows you the cheapest relevant items first

## Setup

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Make sure you have Chrome installed (uses ChromeDriver)

## How to use

### Basic scraping
Just run the main script - it's set to search for "iphone" by default:
```bash
python main.py
```

Change the keyword in `main.py` to search for other stuff.

### Clean existing data
If you already have scraped data, you can clean it:
```python
from utils.clean_listings import clean_from_file
clean_from_file('sheets/your_file.xlsx', 'search_keyword', 'output_name.xlsx')
```

## Output

Creates two Excel files in the `sheets/` folder:
- `{keyword}_raw_listings.xlsx` - Everything scraped
- `{keyword}_cleaned_listings.xlsx` - Just the relevant stuff

## What gets filtered out

- Cars and vehicle ads
- Cases, chargers, and accessories  
- iPads when searching for iPhones
- Duplicate listings
- Items without valid prices
- Real estate, jobs, pets

## Future plans

Planning to add eBay price comparison to find actual profit opportunities, but for now it just gives you clean DoneDeal data to work with.
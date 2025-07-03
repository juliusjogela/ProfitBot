from selenium.webdriver.common.by import By
from urllib.parse import quote_plus
import time
import os
import pandas as pd


def retrieve_ebay_recent_sales(driver, query, max_results=10):
    """
    Fetches recently sold listings from eBay (UK and US) for a given search query.
    Returns a list of tuples: (title, price)
    """
    ebay_domains = ["co.uk", "com", ".ie"]
    results = []

    for domain in ebay_domains:
        url = f"https://www.ebay.{domain}/sch/i.html?_nkw={quote_plus(query)}&_sacat=0&LH_Sold=1&LH_Complete=1"
        print(f"\n🔍 Checking recent sales on eBay.{domain} for: {query}")
        driver.get(url)
        time.sleep(3)

        listings = driver.find_elements(By.CSS_SELECTOR, ".s-item")

        for item in listings:
            if len(results) >= max_results:
                break
            try:
                title_elem = item.find_element(By.CSS_SELECTOR, ".s-item__title")
                price_elem = item.find_element(By.CSS_SELECTOR, ".s-item__price")
                title = title_elem.text.strip()
                price_text = price_elem.text.replace("€", "").replace("£", "").replace("$", "").replace(",", "").strip()
                price = float(price_text.split()[0])
                results.append((title, price))
            except:
                continue

    return results


def compare_to_donedeal(df, ebay_sales):
    """
    Given a DataFrame of DoneDeal listings and eBay sales data, add comparison metrics.
    """
    ebay_prices = [price for _, price in ebay_sales]
    if not ebay_prices:
        df["ebay_comparison_avg"] = None
        df["price_diff"] = None
        return df

    ebay_avg = sum(ebay_prices) / len(ebay_prices)
    df["ebay_comparison_avg"] = ebay_avg
    df["price_diff"] = df["numeric_price"] - ebay_avg
    return df


def analyze_arbitrage_opportunities(driver, donedeal_df, output_file="arbitrage_opportunities.csv"):
    """
    Analyzes DoneDeal listings for arbitrage opportunities by comparing with eBay sales.
    
    Args:
        driver: Selenium WebDriver instance
        donedeal_df: DataFrame containing DoneDeal listings
        output_file: Path to save the comparison results
    
    Returns:
        DataFrame with arbitrage analysis
    """
    print("🔍 Starting arbitrage analysis...")
    
    # Find unique items (assuming 'title' column exists, adjust if needed)
    if 'title' not in donedeal_df.columns:
        print("❌ Error: 'title' column not found in DataFrame")
        return None
    
    # Group by title to get unique items and their average DoneDeal price
    unique_items = donedeal_df.groupby('title').agg({
        'numeric_price': ['mean', 'min', 'max', 'count'],
        'title': 'first'
    }).reset_index()
    
    # Flatten column names
    unique_items.columns = ['title', 'avg_donedeal_price', 'min_donedeal_price', 'max_donedeal_price', 'listing_count', 'title_clean']
    
    print(f"📊 Found {len(unique_items)} unique items to analyze")
    
    arbitrage_data = []
    
    for idx, row in unique_items.iterrows():
        item_title = row['title']
        avg_donedeal_price = row['avg_donedeal_price']
        min_donedeal_price = row['min_donedeal_price']
        listing_count = row['listing_count']
        
        print(f"\n🔍 Analyzing: {item_title} ({listing_count} listings)")
        
        # Get eBay sales data for this item
        ebay_sales = retrieve_ebay_recent_sales(driver, item_title, max_results=10)
        
        if ebay_sales:
            ebay_prices = [price for _, price in ebay_sales]
            ebay_avg = sum(ebay_prices) / len(ebay_prices)
            ebay_min = min(ebay_prices)
            ebay_max = max(ebay_prices)
            
            # Calculate arbitrage metrics
            profit_margin = ebay_avg - avg_donedeal_price
            profit_margin_pct = (profit_margin / avg_donedeal_price) * 100 if avg_donedeal_price > 0 else 0
            min_profit = ebay_min - avg_donedeal_price
            max_profit = ebay_max - avg_donedeal_price
            
            # Determine opportunity level
            if profit_margin_pct >= 20:
                opportunity = "HIGH"
            elif profit_margin_pct >= 10:
                opportunity = "MEDIUM"
            elif profit_margin_pct >= 5:
                opportunity = "LOW"
            else:
                opportunity = "NONE"
            
            arbitrage_data.append({
                'item_title': item_title,
                'donedeal_listings': listing_count,
                'avg_donedeal_price': round(avg_donedeal_price, 2),
                'min_donedeal_price': round(min_donedeal_price, 2),
                'max_donedeal_price': round(row['max_donedeal_price'], 2),
                'ebay_avg_price': round(ebay_avg, 2),
                'ebay_min_price': round(ebay_min, 2),
                'ebay_max_price': round(ebay_max, 2),
                'ebay_sales_count': len(ebay_prices),
                'profit_margin': round(profit_margin, 2),
                'profit_margin_pct': round(profit_margin_pct, 1),
                'min_profit': round(min_profit, 2),
                'max_profit': round(max_profit, 2),
                'opportunity_level': opportunity
            })
        else:
            print(f"⚠️  No eBay sales data found for: {item_title}")
            arbitrage_data.append({
                'item_title': item_title,
                'donedeal_listings': listing_count,
                'avg_donedeal_price': round(avg_donedeal_price, 2),
                'min_donedeal_price': round(min_donedeal_price, 2),
                'max_donedeal_price': round(row['max_donedeal_price'], 2),
                'ebay_avg_price': None,
                'ebay_min_price': None,
                'ebay_max_price': None,
                'ebay_sales_count': 0,
                'profit_margin': None,
                'profit_margin_pct': None,
                'min_profit': None,
                'max_profit': None,
                'opportunity_level': "NO_DATA"
            })
    
    # Create results DataFrame
    results_df = pd.DataFrame(arbitrage_data)
    
    # Sort by profit margin percentage (highest first)
    results_df = results_df.sort_values('profit_margin_pct', ascending=False, na_last=True)
    
    # Save to file
    results_df.to_csv(output_file, index=False)
    print(f"\n✅ Arbitrage analysis saved to: {output_file}")
    print(f"📊 Found {len(results_df[results_df['opportunity_level'] != 'NONE'])} items with profit opportunities")
    
    return results_df

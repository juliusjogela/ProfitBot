from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import quote_plus
import time
import random
import pandas as pd
import os
from datetime import datetime
import re

class EbayScraper:
    def __init__(self, driver):
        self.driver = driver
        self.ebay_domains = ["co.uk", "com", "ie"]  # UK, US, Ireland
        
    def scrape_sold_listings(self, search_term, max_results=15):
        """
        Scrape eBay sold listings for a given search term across multiple domains.
        
        Args:
            search_term: Product to search for
            max_results: Maximum number of sold listings to retrieve per domain
            
        Returns:
            List of sold listings with title, price, domain, and date info
        """
        all_sold_items = []
        
        for domain in self.ebay_domains:
            print(f"🔍 Searching eBay.{domain} sold listings for: {search_term}")
            domain_results = self._scrape_domain(search_term, domain, max_results)
            all_sold_items.extend(domain_results)
            
            # Small delay between domains to be respectful
            time.sleep(random.uniform(1.5, 2.5))
            
        return all_sold_items
    
    def _scrape_domain(self, search_term, domain, max_results):
        """Scrape sold listings from a specific eBay domain"""
        # eBay sold listings URL with filters for completed/sold items
        encoded_term = quote_plus(search_term)
        url = f"https://www.ebay.{domain}/sch/i.html?_nkw={encoded_term}&_sacat=0&LH_Sold=1&LH_Complete=1&_sop=13"
        
        try:
            self.driver.get(url)
            # Wait for search results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".srp-results"))
            )
            
            # Get all sold listings
            listings = self.driver.find_elements(By.CSS_SELECTOR, ".s-item")
            domain_results = []
            
            for listing in listings[:max_results]:
                try:
                    sold_item = self._extract_listing_data(listing, domain)
                    if sold_item:
                        domain_results.append(sold_item)
                except Exception as e:
                    continue  # Skip problematic listings
                    
            print(f"📊 Found {len(domain_results)} sold listings on eBay.{domain}")
            return domain_results
            
        except TimeoutException:
            print(f"⚠️ Timeout loading eBay.{domain} - skipping")
            return []
        except Exception as e:
            print(f"⚠️ Error scraping eBay.{domain}: {str(e)}")
            return []
    
    def _extract_listing_data(self, listing, domain):
        """Extract data from a single eBay listing"""
        try:
            # Skip promoted/sponsored listings
            if listing.find_elements(By.CSS_SELECTOR, ".s-item__subtitle"):
                subtitle = listing.find_element(By.CSS_SELECTOR, ".s-item__subtitle").text
                if "Sponsored" in subtitle or "SPONSORED" in subtitle:
                    return None
            
            # Extract title
            title_elem = listing.find_element(By.CSS_SELECTOR, ".s-item__title")
            title = title_elem.text.strip()
            
            # Skip if title contains "New listing" or similar
            if "New listing" in title or title == "":
                return None
                
            # Extract price
            price_elem = listing.find_element(By.CSS_SELECTOR, ".s-item__price")
            price_text = price_elem.text.strip()
            
            # Clean and convert price
            cleaned_price = self._clean_price(price_text)
            if cleaned_price is None:
                return None
                
            # Extract sale date if available
            sale_date = self._extract_sale_date(listing)
            
            # Extract condition if available
            condition = self._extract_condition(listing)
            
            return {
                'title': title,
                'price': cleaned_price,
                'price_text': price_text,
                'domain': domain,
                'sale_date': sale_date,
                'condition': condition,
                'currency': self._get_currency_symbol(domain)
            }
            
        except (NoSuchElementException, Exception):
            return None
    
    def _clean_price(self, price_text):
        """Extract numeric price from price text"""
        try:
            # Remove currency symbols and clean text
            cleaned = re.sub(r'[£$€,\s]', '', price_text)
            
            # Handle price ranges (take the first price)
            if 'to' in cleaned.lower():
                cleaned = cleaned.split('to')[0]
            
            # Extract first number found
            price_match = re.search(r'(\d+\.?\d*)', cleaned)
            if price_match:
                return float(price_match.group(1))
            return None
            
        except (ValueError, AttributeError):
            return None
    
    def _extract_sale_date(self, listing):
        """Extract sale date from listing if available"""
        try:
            date_elem = listing.find_element(By.CSS_SELECTOR, ".s-item__title--tag")
            return date_elem.text.strip()
        except NoSuchElementException:
            return "Recently sold"
    
    def _extract_condition(self, listing):
        """Extract item condition from listing if available"""
        try:
            condition_elem = listing.find_element(By.CSS_SELECTOR, ".SECONDARY_INFO")
            return condition_elem.text.strip()
        except NoSuchElementException:
            return "Not specified"
    
    def _get_currency_symbol(self, domain):
        """Get currency symbol based on eBay domain"""
        currency_map = {
            'co.uk': '£',
            'com': '$',
            'ie': '€'
        }
        return currency_map.get(domain, '$')

def normalize_product_name(title):
    """
    Normalize product names to group similar items together.
    This reduces duplicate eBay searches for the same product.
    """
    if not title:
        return ""
    
    # Convert to lowercase for consistent processing
    normalized = title.lower()
    
    # Remove common noise words and phrases
    noise_words = [
        'excellent condition', 'good condition', 'fair condition', 'poor condition',
        'brand new', 'new', 'used', 'refurbished', 'unlocked', 'locked',
        'with box', 'boxed', 'unboxed', 'no box',
        'charger included', 'original box', 'accessories',
        'mint condition', 'like new', 'barely used',
        'perfect condition', 'great condition', 'working',
        'apple', 'genuine', 'original', 'official'
    ]
    
    for noise in noise_words:
        normalized = normalized.replace(noise, '')
    
    # Remove extra spaces and punctuation
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Extract core product info for iPhones
    if 'iphone' in normalized:
        # Extract iPhone model and storage if present
        iphone_match = re.search(r'iphone\s*(\d+\s*(?:pro|plus|max|mini)*)\s*(\d+gb)?', normalized)
        if iphone_match:
            model = iphone_match.group(1).strip()
            storage = iphone_match.group(2) if iphone_match.group(2) else ''
            return f"iphone {model} {storage}".strip()
    
    # Extract core product info for other items
    # Remove color names
    colors = ['black', 'white', 'red', 'blue', 'green', 'yellow', 'purple', 'pink', 'silver', 'gold', 'rose', 'space', 'gray', 'grey']
    for color in colors:
        normalized = normalized.replace(color, '')
    
    # Clean up again
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

def group_similar_items(df):
    """
    Group similar items together to avoid duplicate eBay searches.
    Returns a DataFrame with unique products and their aggregated data.
    """
    # Add normalized product names
    df['normalized_name'] = df['title'].apply(normalize_product_name)
    
    # Group by normalized name instead of exact title
    grouped = df.groupby('normalized_name').agg({
        'title': lambda x: x.iloc[0],  # Keep first title as representative
        'numeric_price': ['mean', 'min', 'max', 'count'],
        'location': 'first',
        'url': 'first'
    }).reset_index()
    
    # Flatten column names
    grouped.columns = ['search_term', 'representative_title', 'avg_donedeal_price', 'min_donedeal_price', 
                      'max_donedeal_price', 'listing_count', 'location', 'url']
    
    # Filter out empty search terms
    grouped = grouped[grouped['search_term'] != '']
    
    print(f"🎯 Grouped {len(df)} listings into {len(grouped)} unique products")
    
    return grouped

def analyze_profit_opportunities(cleaned_listings_file, driver, output_file="profit_analysis.xlsx"):
    """
    Analyze profit opportunities by comparing cleaned DoneDeal listings with eBay sold prices.
    
    Args:
        cleaned_listings_file: Path to cleaned listings Excel file
        driver: Selenium WebDriver instance
        output_file: Path to save profit analysis results
        
    Returns:
        DataFrame with profit analysis results
    """
    print("🚀 Starting profit opportunity analysis...")
    
    # Load cleaned listings
    try:
        listings_path = os.path.join("sheets", cleaned_listings_file)
        df = pd.read_excel(listings_path)
        print(f"📊 Loaded {len(df)} cleaned listings")
    except Exception as e:
        print(f"❌ Error loading cleaned listings: {e}")
        return None
    
    # Initialize eBay scraper
    ebay_scraper = EbayScraper(driver)
    
    # Group similar items together to avoid duplicate eBay searches
    unique_items = group_similar_items(df)
    
    print(f"🎯 Analyzing {len(unique_items)} unique products for profit opportunities")
    
    analysis_results = []
    
    for idx, item in unique_items.iterrows():
        print(f"\n🔍 [{idx+1}/{len(unique_items)}] Analyzing: {item['representative_title'][:50]}...")
        print(f"🔍 Searching eBay for: {item['search_term']}")
        
        # Get eBay sold listings for this item using the normalized search term
        sold_listings = ebay_scraper.scrape_sold_listings(item['search_term'], max_results=10)
        
        if sold_listings:
            # Calculate eBay statistics
            ebay_prices = [listing['price'] for listing in sold_listings]
            ebay_avg = sum(ebay_prices) / len(ebay_prices)
            ebay_min = min(ebay_prices)
            ebay_max = max(ebay_prices)
            
            # Calculate profit metrics (convert eBay prices to EUR approximately)
            # Simple conversion rates (you might want to use real-time rates)
            conversion_rates = {'£': 1.15, '$': 0.85, '€': 1.0}  # to EUR
            
            # Convert eBay prices to EUR for comparison
            eur_prices = []
            for listing in sold_listings:
                rate = conversion_rates.get(listing['currency'], 1.0)
                eur_prices.append(listing['price'] * rate)
            
            if eur_prices:
                ebay_avg_eur = sum(eur_prices) / len(eur_prices)
                ebay_min_eur = min(eur_prices)
                ebay_max_eur = max(eur_prices)
                
                # Calculate profit potential
                profit_potential = ebay_avg_eur - item['avg_donedeal_price']
                profit_percentage = (profit_potential / item['avg_donedeal_price']) * 100 if item['avg_donedeal_price'] > 0 else 0
                
                # Determine opportunity level
                if profit_percentage >= 50:
                    opportunity = "🟢 EXCELLENT"
                elif profit_percentage >= 25:
                    opportunity = "🟡 GOOD"
                elif profit_percentage >= 10:
                    opportunity = "🟠 MODERATE"
                else:
                    opportunity = "🔴 LOW"
                
                analysis_results.append({
                    'item_title': item['representative_title'],
                    'search_term': item['search_term'],
                    'donedeal_avg_price': round(item['avg_donedeal_price'], 2),
                    'donedeal_min_price': round(item['min_donedeal_price'], 2),
                    'donedeal_max_price': round(item['max_donedeal_price'], 2),
                    'donedeal_listings': item['listing_count'],
                    'donedeal_location': item['location'],
                    'donedeal_url': item['url'],
                    'ebay_avg_price_eur': round(ebay_avg_eur, 2),
                    'ebay_min_price_eur': round(ebay_min_eur, 2),
                    'ebay_max_price_eur': round(ebay_max_eur, 2),
                    'ebay_sold_count': len(sold_listings),
                    'profit_potential_eur': round(profit_potential, 2),
                    'profit_percentage': round(profit_percentage, 1),
                    'opportunity_level': opportunity,
                    'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                
                print(f"💰 Profit potential: €{profit_potential:.2f} ({profit_percentage:.1f}%) - {opportunity}")
            
        else:
            print("⚠️ No eBay sold listings found")
            analysis_results.append({
                'item_title': item['representative_title'],
                'search_term': item['search_term'],
                'donedeal_avg_price': round(item['avg_donedeal_price'], 2),
                'donedeal_min_price': round(item['min_donedeal_price'], 2),
                'donedeal_max_price': round(item['max_donedeal_price'], 2),
                'donedeal_listings': item['listing_count'],
                'donedeal_location': item['location'],
                'donedeal_url': item['url'],
                'ebay_avg_price_eur': None,
                'ebay_min_price_eur': None,
                'ebay_max_price_eur': None,
                'ebay_sold_count': 0,
                'profit_potential_eur': None,
                'profit_percentage': None,
                'opportunity_level': "❌ NO DATA",
                'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        
        # Small delay between searches to be respectful
        time.sleep(random.uniform(2, 4))
    
    # Create results DataFrame and save
    results_df = pd.DataFrame(analysis_results)
    
    # Sort by profit percentage (best opportunities first)
    # Handle NaN values by filling them with -999 for sorting, then restore them
    results_df['profit_percentage_temp'] = results_df['profit_percentage'].fillna(-999)
    results_df = results_df.sort_values('profit_percentage_temp', ascending=False)
    results_df = results_df.drop('profit_percentage_temp', axis=1)
    
    # Save to Excel with formatting
    output_path = os.path.join("sheets", output_file)
    results_df.to_excel(output_path, index=False)
    
    # Print summary
    profitable_items = results_df[results_df['profit_percentage'].notna() & (results_df['profit_percentage'] > 10)]
    
    print(f"\n✅ Analysis complete! Results saved to: {output_file}")
    print(f"📊 Summary:")
    print(f"   • Total items analyzed: {len(results_df)}")
    print(f"   • Items with eBay data: {len(results_df[results_df['ebay_sold_count'] > 0])}")
    print(f"   • Profitable opportunities (>10%): {len(profitable_items)}")
    
    if len(profitable_items) > 0:
        best_opportunity = profitable_items.iloc[0]
        print(f"   • Best opportunity: {best_opportunity['item_title'][:40]}... ({best_opportunity['profit_percentage']:.1f}% profit)")
    
    return results_df

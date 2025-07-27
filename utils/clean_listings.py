import pandas as pd
import os
import re
from datetime import datetime

def clean_price(price_str):
    """Extract numeric price from price string"""
    try:
        # Remove common currency symbols and text
        price_clean = re.sub(r'[€$£,]', '', str(price_str))
        price_clean = re.sub(r'[a-zA-Z]', '', price_clean).strip()
        return float(price_clean) if price_clean else None
    except (AttributeError, ValueError):
        return None

def get_exclusion_patterns():
    """Return common patterns for irrelevant listings"""
    return [
        # Vehicles
        r'\b(car|bmw|mercedes|audi|volkswagen|ford|toyota|honda|nissan|hyundai|kia|mazda|volvo|peugeot|renault|citroen|opel|skoda|seat|fiat|alfa romeo|porsche|ferrari|lamborghini|bentley|rolls royce)\b',
        r'\b(suv|sedan|hatchback|estate|coupe|convertible|diesel|petrol|hybrid|electric)\b',
        r'\b(automatic|manual|transmission|engine|mot|nct|tax|mileage|km|miles)\b',
        
        # Cases and Accessories (general)
        r'\bcase\b|\bcover\b|\bscreen protector\b|\bcharger\b|\bcable\b|\bstand\b|\bholder\b',
        r'\bheadphones\b|\bearphones\b|\bspeaker\b|\bpower bank\b|\badapter\b',
        
        # Other Electronics (when not the main search term)
        r'\b(ipad|tablet|macbook|laptop|computer|tv|television|monitor|camera|drone)\b',
        
        # Real Estate
        r'\b(house|apartment|flat|room|property|rent|lease|mortgage)\b',
        
        # Jobs/Services
        r'\b(job|work|service|repair|installation|delivery)\b',
        
        # Animals/Pets
        r'\b(dog|cat|horse|puppy|kitten|pet|animal)\b'
    ]

def is_relevant_listing(title, search_keyword, exclusion_patterns):
    """Check if a listing is relevant based on search keyword and exclusion patterns"""
    if not title or not search_keyword:
        return False
    
    title_lower = title.lower()
    keyword_lower = search_keyword.lower()
    
    # Must contain the search keyword
    if keyword_lower not in title_lower:
        return False
    
    # Check against exclusion patterns
    for pattern in exclusion_patterns:
        if re.search(pattern, title_lower, re.IGNORECASE):
            return False
    
    # Special filtering based on search keyword
    if keyword_lower == 'iphone':
        # For iPhone searches, exclude cases, iPads, and accessories
        iphone_exclusions = [
            r'\bcase\b|\bcover\b|\bscreen protector\b',
            r'\bipad\b|\btablet\b',
            r'\bcharger\b|\bcable\b|\badapter\b',
            r'\bheadphones\b|\bearphones\b'
        ]
        for pattern in iphone_exclusions:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return False
    
    return True

def remove_duplicates(df):
    """Remove duplicate listings based on title similarity and URL"""
    if len(df) == 0:
        return df
    
    # Remove exact duplicates
    df = df.drop_duplicates(subset=['url'], keep='first')
    
    # Remove near-duplicate titles (same title with minor variations)
    df['title_clean'] = df['title'].str.lower().str.strip()
    df = df.drop_duplicates(subset=['title_clean'], keep='first')
    df = df.drop('title_clean', axis=1)
    
    return df

def clean_listings(data, search_keyword, output_filename=None):
    """
    Clean and filter listings based on search keyword
    
    Args:
        data: DataFrame or path to Excel/CSV file
        search_keyword: The keyword that was searched for
        output_filename: Optional filename to save cleaned data
    
    Returns:
        Cleaned DataFrame
    """
    # Load data if path is provided
    if isinstance(data, str):
        if data.endswith('.xlsx'):
            df = pd.read_excel(data)
        elif data.endswith('.csv'):
            df = pd.read_csv(data)
        else:
            raise ValueError("Unsupported file format. Use .xlsx or .csv")
        print(f"📊 Loaded {len(df)} total listings from {data}")
    else:
        df = data.copy()
        print(f"📊 Processing {len(df)} total listings")
    
    # Validate required columns
    required_columns = ["title", "price", "location", "url"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"⚠️  Warning: Missing columns: {missing_columns}")
        return df
    
    # Basic cleanup - handle missing values and clean strings
    for col in required_columns:
        df[col] = df[col].fillna("").astype(str).str.strip()
    
    # Remove empty titles
    df = df[df['title'] != ""]
    print(f"📝 After removing empty titles: {len(df)} listings")
    
    # Filter for relevant listings
    exclusion_patterns = get_exclusion_patterns()
    relevant_mask = df['title'].apply(
        lambda title: is_relevant_listing(title, search_keyword, exclusion_patterns)
    )
    df = df[relevant_mask]
    print(f"🎯 After relevance filtering: {len(df)} listings")
    
    # Remove duplicates
    df = remove_duplicates(df)
    print(f"🔄 After duplicate removal: {len(df)} listings")
    
    # Clean and validate prices
    df["numeric_price"] = df["price"].apply(clean_price)
    valid_price_mask = df["numeric_price"].notna() & (df["numeric_price"] > 0)
    df = df[valid_price_mask]
    print(f"💰 Listings with valid prices: {len(df)}")
    
    if len(df) == 0:
        print("⚠️  No valid listings found after cleaning")
        return df
    
    # Sort by price (ascending - cheapest first)
    df = df.sort_values(by="numeric_price", ascending=True)
    
    # Add helpful columns
    df["price_formatted"] = df["numeric_price"].apply(lambda x: f"€{x:,.2f}")
    df["scraped_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    df["search_keyword"] = search_keyword
    
    # Reorder columns for better readability
    column_order = ["title", "price_formatted", "numeric_price", "location", "url", "search_keyword", "scraped_date"]
    existing_columns = [col for col in column_order if col in df.columns]
    other_columns = [col for col in df.columns if col not in column_order]
    df = df[existing_columns + other_columns]
    
    # Save to Excel if filename provided
    if output_filename:
        save_to_excel(df, output_filename, search_keyword)
    
    return df

def save_to_excel(df, output_filename, search_keyword=None):
    """Save DataFrame to a formatted Excel file"""
    # Ensure sheets directory exists
    os.makedirs("sheets", exist_ok=True)
    
    # Add .xlsx extension if not present
    if not output_filename.endswith('.xlsx'):
        output_filename += '.xlsx'
    
    output_path = os.path.join("sheets", output_filename)
    
    # Save to Excel
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Cleaned Listings', index=False)
        print(f"✅ Saved {len(df)} cleaned listings to {output_filename}")
    except Exception as e:
        # Fallback to basic save
        df.to_excel(output_path, index=False)
        print(f"✅ Saved {len(df)} cleaned listings to {output_filename} (basic format)")
    
    # Print summary statistics
    if len(df) > 0 and 'numeric_price' in df.columns:
        print(f"🔍 Search keyword: '{search_keyword}'")
        print(f"📈 Price range: €{df['numeric_price'].min():.2f} - €{df['numeric_price'].max():.2f}")
        print(f"📊 Average price: €{df['numeric_price'].mean():.2f}")
        print(f"📋 Cheapest item: {df.iloc[0]['title']} - €{df.iloc[0]['numeric_price']:.2f}")

# Convenience function for command line usage
def clean_from_file(filepath, search_keyword, output_filename=None):
    """Clean listings from a file"""
    return clean_listings(filepath, search_keyword, output_filename)

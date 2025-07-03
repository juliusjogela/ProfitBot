import pandas as pd
import os
from datetime import datetime

def clean_price(price_str):
    try:
        return float(
            price_str.replace("€", "").replace(",", "").replace("EUR", "").strip()
        )
    except (AttributeError, ValueError):
        return None

def is_listing_relevant(title, keywords, case_sensitive=False):

    if not keywords or not title:
        return False
    
    search_title = title if case_sensitive else title.lower()
    search_keywords = keywords if case_sensitive else [kw.lower() for kw in keywords]
    
    return any(keyword in search_title for keyword in search_keywords)

def clean_listings(csv_filename, keywords=None, case_sensitive=False, output_filename=None):
 
    # Load CSV file from sheets directory
    input_path = os.path.join("sheets", csv_filename)
    df = pd.read_csv(input_path, dtype={"url": str})
    print(f"📊 Loaded {len(df)} total listings from {csv_filename}")
    
    # Basic data validation
    required_columns = ["title", "price", "location", "url"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"⚠️  Warning: Missing columns: {missing_columns}")
    
    # Basic Cleanup - handle missing values and clean strings
    for col in ["title", "price", "location", "url"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
    
    # Filter by keywords - only keep relevant listings
    if keywords:
        print(f"🔍 Filtering by keywords: {', '.join(keywords)}")
        relevant_mask = df['title'].apply(lambda title: is_listing_relevant(title, keywords, case_sensitive))
        df = df[relevant_mask]
        print(f"🎯 After keyword filtering: {len(df)} relevant listings")
    else:
        print("⚠️  No keywords provided - keeping all listings")
    
    # Clean prices and add numeric price column
    df["numeric_price"] = df["price"].apply(clean_price)
    
    # Filter out listings with invalid prices (but keep all valid prices regardless of amount)
    valid_price_mask = df["numeric_price"].notna()
    df = df[valid_price_mask]
    print(f"💰 Listings with valid prices: {len(df)}")
    
    # Sort by price (ascending - cheapest first)
    df = df.sort_values(by="numeric_price", ascending=True)
    
    # Add additional helpful columns
    df["price_formatted"] = df["numeric_price"].apply(lambda x: f"€{x:,.2f}" if pd.notna(x) else "")
    df["scraped_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Reorder columns for better readability
    column_order = ["title", "price_formatted", "numeric_price", "location", "url", "scraped_date"]
    existing_columns = [col for col in column_order if col in df.columns]
    other_columns = [col for col in df.columns if col not in column_order]
    df = df[existing_columns + other_columns]
    
    # Save to Excel if output filename is provided
    if output_filename:
        save_to_excel(df, output_filename, keywords)
    
    return df

def save_to_excel(df, output_filename, keywords=None):
    """
    Save DataFrame to a nicely formatted Excel file.
    """
    # Ensure sheets directory exists
    os.makedirs("sheets", exist_ok=True)
    
    # Add .xlsx extension if not present
    if not output_filename.endswith('.xlsx'):
        output_filename += '.xlsx'
    
    output_path = os.path.join("sheets", output_filename)
    
    # Create Excel writer with xlsxwriter engine for formatting
    try:
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Cleaned Listings', index=False)
            
            # Get the workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Cleaned Listings']
            
            # Add some formatting
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Format headers
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Auto-adjust column widths
            for i, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).str.len().max(), len(col)) + 2
                worksheet.set_column(i, i, min(max_length, 50))
    
    except ImportError:
        # Fallback to basic Excel export if xlsxwriter is not available
        df.to_excel(output_path, index=False)
    
    print(f"✅ Cleaned and saved {len(df)} listings to {output_filename}")
    
    if keywords:
        print(f"🔍 Keywords used: {', '.join(keywords)}")
    
    # Print summary statistics
    if len(df) > 0:
        print(f"📈 Price range: €{df['numeric_price'].min():.2f} - €{df['numeric_price'].max():.2f}")
        print(f"📊 Average price: €{df['numeric_price'].mean():.2f}")

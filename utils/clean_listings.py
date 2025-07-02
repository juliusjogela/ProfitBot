import pandas as pd
import re
import os

def clean_price(price_str):
    try:
        return float(
            price_str.replace("€", "").replace(",", "").replace("EUR", "").strip()
        )
    except (AttributeError, ValueError):
        return None

def clean_listings_csv(csv_filename, output_filename=None, min_price=100.0):
    input_path = os.path.join("sheets", csv_filename)
    output_filename = output_filename or f"cleaned_{csv_filename.replace('.csv', '.xlsx')}"
    output_path = os.path.join("sheets", output_filename)

    df = pd.read_csv(input_path, dtype={"url": str})
    
    # Basic Cleanup
    for col in ["title", "price", "location", "url"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # Clean prices
    df["numeric_price"] = df["price"].apply(clean_price)
    df = df[df["numeric_price"] >= min_price]

    # Optional: Sort by price
    df = df.sort_values(by="numeric_price", ascending=True)

    # Save to Excel
    os.makedirs("sheets", exist_ok=True)
    df.to_excel(output_path, index=False)

    print(f"✅ Cleaned and saved {len(df)} listings to {output_filename}")

from scraper.donedeal_scraper import extract_listings
from utils.driver_setup import setup_driver
from utils.clean_listings import clean_listings
from utils.ebay_comparison import analyze_profit_opportunities
import pandas as pd
import os

def main():
    driver = setup_driver()

    keyword = "Iphone 16"         # Change this to your desired search term

    print(f"🔍 Searching for '{keyword}' on DoneDeal...") #Webscraper will extract listings
    listings = extract_listings(driver, keyword)

    if listings:
        os.makedirs("sheets", exist_ok=True)
        df = pd.DataFrame(listings)

        csv_path = os.path.join("sheets", "listings.csv")        # Save raw CSV
        df.to_csv(csv_path, index=False)

        print(f"✅ Saved raw listings to:")
        print(f"    📄 {csv_path}")

        # Clean the CSV file with keywords and save cleaned version
        print(f"\n🧹 Cleaning and filtering listings...")
        clean_listings("listings.csv", keywords=[keyword], output_filename="cleaned_listings.xlsx")
        
        # Analyze profit opportunities by comparing with eBay sold listings
        print(f"\n💰 Starting profit analysis with eBay comparison...")
        try:
            profit_analysis = analyze_profit_opportunities(
                cleaned_listings_file="cleaned_listings.xlsx",
                driver=driver,
                output_file="profit_opportunities.xlsx"
            )
            
            if profit_analysis is not None and len(profit_analysis) > 0:
                print(f"\n🎯 Profit Analysis Complete!")
                print(f"📊 Check 'profit_opportunities.xlsx' for detailed results")
            else:
                print(f"⚠️ No profit analysis data generated")
                
        except Exception as e:
            print(f"❌ Error during profit analysis: {e}")
        
    else:
        print("⚠️ No listings found.")

    # Close the driver
    driver.quit()
    print(f"\n✅ ProfitBot analysis complete!")


if __name__ == "__main__":
    main()

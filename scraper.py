import csv
import pandas as pd
import os
import time
import random
from glob import glob
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------- CONFIGURATION ---------- #
BASE_URL = "https://www.sgcarmart.com/used-cars/listing?cts[]=18&cts[]=2&cts[]=3&cts[]=15&cts[]=16&cts[]=6&cts[]=23&cts[]=24&cts[]=25&cts[]=5&cts[]=20&cts[]=21&cts[]=28&cts[]=29&vts[]=12&vts[]=13&vts[]=9&vts[]=10&vts[]=11&vts[]=8&vts[]=7&vts[]=15&vts[]=6&vts[]=16&avl=a&page="
SAVE_EVERY = 1000
MAX_PAGES = 570

SAVE_DIR = os.path.join("data")
os.makedirs(SAVE_DIR, exist_ok=True)
MASTER_PATH = os.path.join(SAVE_DIR, "used_cars_master.csv")

# ---------- SELENIUM SETUP ---------- #
options = Options()
options.add_argument('--headless=new')  # or '--headless=chrome'
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument(
    '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

# ---------- SCRAPER LOOP ---------- #
results = []
scraped_ids = set()

for page_num in range(1, MAX_PAGES + 1):
    url = BASE_URL + str(page_num)
    print(f"Scraping page {page_num}: {url}")

    try:
        driver.get(url)
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[starts-with(@id, 'listing_')]"))
        )
        time.sleep(random.uniform(1.5, 3.5))

        listings = driver.find_elements(
            By.XPATH, "//div[starts-with(@id, 'listing_')]")

        if not listings:
            print(f"🚫 No listings found on page {page_num}. Stopping.")
            break

        for idx, listing in enumerate(listings, 1):
            try:
                title = listing.find_element(
                    By.CLASS_NAME, "styles_model_name__ZaHTI").text.strip()
                price = listing.find_element(
                    By.CLASS_NAME, "styles_price__PoUIK").text.strip()
                reg_date = listing.find_element(
                    By.CLASS_NAME, "styles_reg_date_text__g7iO_").text.strip()
                depreciation = listing.find_element(
                    By.CLASS_NAME, "styles_depreciation_text__I0yui").text.strip()
                mileage = listing.find_element(
                    By.XPATH, ".//div[contains(@class, 'listing_mileage_box')]").text.strip()
                owners = listing.find_element(
                    By.XPATH, ".//div[contains(@class, 'listing_owner_box')]").text.strip()
                url = listing.find_element(
                    By.TAG_NAME, "a").get_attribute("href")

                uid = f"{title}|{reg_date}|{price}"
                if uid in scraped_ids:
                    continue
                scraped_ids.add(uid)

                results.append({
                    "Title": title,
                    "Price": price,
                    "Reg Date": reg_date,
                    "Depreciation": depreciation,
                    "Mileage": mileage,
                    "Owners": owners,
                    "URL": url
                })

            except Exception as e:
                print(
                    f"⚠️ Skipping listing #{idx} on page {page_num} due to error: {e}")
                continue

        if len(results) >= SAVE_EVERY:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(
                SAVE_DIR, f"used_car_chunk_{timestamp}.csv")
            keys = results[0].keys()
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                dict_writer = csv.DictWriter(f, keys)
                dict_writer.writeheader()
                dict_writer.writerows(results)
            print(f"✅ Saved {len(results)} listings to {filename}")
            results.clear()
            scraped_ids.clear()

        time.sleep(random.uniform(2.0, 4.5))

    except Exception as e:
        print(f"❌ Could not load listings on page {page_num}: {e}")
        continue

# ---------- FINAL SAVE ---------- #
if results:
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chunk_file = os.path.join(SAVE_DIR, f"used_car_final_{timestamp}.csv")
        keys = results[0].keys()
        with open(chunk_file, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, keys)
            dict_writer.writeheader()
            dict_writer.writerows(results)
        print(
            f"✅ Final save completed with {len(results)} listings to {chunk_file}")
    except Exception as e:
        print(f"❌ Final save failed: {e}")
else:
    chunk_file = None

# ---------- SAVE TODAY'S SCRAPED DATA AS MASTER ---------- #
# Collect all CSVs (chunk + final) for today
chunk_files = glob(os.path.join(SAVE_DIR, "used_car_chunk_*.csv"))
final_files = glob(os.path.join(SAVE_DIR, "used_car_final_*.csv"))
all_data_files = chunk_files + final_files

combined_today_df = pd.concat(
    [pd.read_csv(f) for f in all_data_files],
    ignore_index=True
)

# Save to master (overwrite)
combined_today_df.to_csv(MASTER_PATH, index=False)
print(f"✅ Overwrote master file with {len(combined_today_df)} listings.")

# ---------- DELETE CHUNK FILES ---------- #
for file_path in all_data_files:
    try:
        os.remove(file_path)
        print(f"🗑️ Deleted chunk/final file: {file_path}")
    except Exception as e:
        print(f"❌ Failed to delete {file_path}: {e}")


# ---------- CLEANUP ---------- #
driver.quit()
print("🚗 Scraping complete.")

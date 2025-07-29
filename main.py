from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import os

# === CONFIG ===
READYMODE_URL = "https://resva.readymode.com/login_new/?then=/"
EMAIL = "Auditor1"
PASSWORD = "RES@2024!"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")  # All calls go here

# === SETUP BROWSER ===
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "safebrowsing.enabled": True
})
driver = webdriver.Chrome(options=chrome_options)

# === LOGIN ===
driver.get(READYMODE_URL)
time.sleep(3)

# Fill login form (you may need to inspect and adjust field names)
driver.find_element(By.NAME, "email").send_keys(EMAIL)
driver.find_element(By.NAME, "password").send_keys(PASSWORD)
driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
print("Logging in...")
time.sleep(10)

# === NAVIGATE TO RECORDINGS ===
print("Navigating to Call Recordings page...")
driver.get("https://resva.readymode.com/login_new/?then=/")  # change this if needed
time.sleep(10)

# === DOWNLOAD FILES ===
print("Starting downloads...")
recordings = driver.find_elements(By.CSS_SELECTOR, "a[href$='.mp3']")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

for i, rec in enumerate(recordings):
    url = rec.get_attribute("href")
    driver.execute_script("window.open(arguments[0]);", url)
    print(f"Downloading call {i+1}/{len(recordings)}")
    time.sleep(2)  # Give it time to download

print("Done downloading all calls.")
driver.quit()

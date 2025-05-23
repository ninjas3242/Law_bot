# scrape_and_save.py
from playwright.sync_api import sync_playwright

urls = [
    "https://www.kynohealth.com/",
    "https://www.kynohealth.com/provide-services",
    "https://www.kynohealth.com/about-us",
    "https://www.kynohealth.com/blog",
    "https://www.kynohealth.com/contact-us",
    "https://www.kynohealth.com/book-doctor/step-1",
    "https://www.kynohealth.com/terms-conditions",
    "https://www.kynohealth.com/return-policy",
]

def scrape_kynohealth():
    all_text = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for url in urls:
            page.goto(url, wait_until="networkidle", timeout=15000)
            for button_text in ["View All", "Read More", "See More"]:
                try:
                    page.locator(f"text={button_text}").first.click(timeout=3000)
                except:
                    pass
            page_text = page.inner_text("body")
            all_text += f"\n\n--- Page: {url} ---\n\n" + page_text
        browser.close()
    return all_text

# Save scraped text
if __name__ == "__main__":
    data = scrape_kynohealth()
    with open("kyno_scraped_data.txt", "w", encoding="utf-8") as f:
        f.write(data)
    print("✅ Scraped data saved to kyno_scraped_data.txt")

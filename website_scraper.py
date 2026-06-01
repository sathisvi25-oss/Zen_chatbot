import os
import time
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


def scrape_website():

    BASE_URL = "https://zenfuture.in/"
    OUTPUT_FILE = "data/website_content.txt"

    os.makedirs("data", exist_ok=True)

    chrome_options = Options()

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        options=chrome_options
    )

    visited_urls = set()
    urls_to_visit = {BASE_URL}

    all_content = []

    print("\nStarting Website Crawl...\n")

    try:

        while urls_to_visit:

            current_url = urls_to_visit.pop()

            if current_url in visited_urls:
                continue

            visited_urls.add(current_url)

            print(
                f"Scraping: {current_url}"
            )

            try:

                driver.get(current_url)

                time.sleep(2)

                soup = BeautifulSoup(
                    driver.page_source,
                    "html.parser"
                )

                # ==========================
                # Collect Internal Links
                # ==========================

                for link in soup.find_all(
                    "a",
                    href=True
                ):

                    href = link["href"].strip()

                    if (
                        href.startswith("#")
                        or
                        href.startswith("mailto:")
                        or
                        href.startswith("tel:")
                    ):
                        continue

                    full_url = urljoin(
                        BASE_URL,
                        href
                    )

                    parsed_base = urlparse(
                        BASE_URL
                    )

                    parsed_url = urlparse(
                        full_url
                    )

                    if (
                        parsed_url.netloc
                        ==
                        parsed_base.netloc
                    ):

                        clean_url = (
                            parsed_url
                            ._replace(
                                fragment="",
                                query=""
                            )
                            .geturl()
                        )

                        if (
                            clean_url
                            not in visited_urls
                        ):

                            urls_to_visit.add(
                                clean_url
                            )

                # ==========================
                # Remove Noise
                # ==========================

                for tag in soup([
                    "script",
                    "style",
                    "noscript",
                    "svg",
                    "img",
                    "iframe",
                    "footer",
                    "header"
                ]):
                    tag.decompose()

                page_text = soup.get_text(
                    separator="\n",
                    strip=True
                )

                if page_text.strip():

                    all_content.append(
                        f"\n\n{'='*80}\n"
                        f"PAGE URL: {current_url}\n"
                        f"{'='*80}\n\n"
                    )

                    all_content.append(
                        page_text
                    )

            except Exception as e:

                print(
                    f"Error scraping "
                    f"{current_url}: {e}"
                )

    finally:

        driver.quit()

    # ==========================
    # Save Content
    # ==========================

    final_text = "\n".join(
        all_content
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(final_text)

    print(
        "\n=========================="
    )

    print(
        "Website Crawl Completed"
    )

    print(
        "=========================="
    )

    print(
        f"Pages Crawled: "
        f"{len(visited_urls)}"
    )

    print(
        f"Characters: "
        f"{len(final_text)}"
    )

    print(
        f"Saved To: "
        f"{OUTPUT_FILE}"
    )

    return True


if __name__ == "__main__":

    scrape_website()
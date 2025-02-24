import os
import json
import asyncio
import aiohttp
import requests
import logging
from bs4 import BeautifulSoup

# Base URLs
URL = "https://rostmetall.kz/catalog"
URL_PREFIX = "https://rostmetall.kz"

# Headers to prevent blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Concurrency Limits
MAX_CONCURRENT_REQUESTS = 70
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# Stores category paths and links
links_to_table = []

# Setup Logging
LOG_FILE = "scraper.log"
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",  # Append mode
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)


async def async_fetch(session, url):
    """Asynchronous fetch with logging and concurrency control."""
    async with semaphore:
        try:
            async with session.get(url, headers=HEADERS, ssl=False, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                logging.warning(f"Error {response.status} fetching {url}")
                return None
        except Exception as e:
            logging.error(f"Request error fetching {url}: {e}")
            return None


async def async_process_element(session, link):
    """Fetches and processes an individual product asynchronously."""
    json_data = {}

    html = await async_fetch(session, link)
    if not html:
        return None

    body = BeautifulSoup(html, "html.parser")
    text = body.find("h1", class_="producth")
    if text:
        json_data["Наименование"] = text.text.strip()

    element_data = body.find("ul", class_="prodchars")
    if element_data:
        for data in element_data.find_all("li"):
            key = data.find("span", class_="pchname").text.strip()
            value = data.find("span", class_="pchopt").text.strip()
            json_data[key] = value

    return json_data


async def async_process_page(session, link, path, page):
    """Processes an entire product page asynchronously."""
    logging.info(f"Processing page {page}: {link}")
    file_path = os.path.join(path, f"page_{page}.json")

    html = await async_fetch(session, link)
    if not html:
        logging.warning(f"Skipping page {page} (failed fetch): {link}")
        return

    body = BeautifulSoup(html, "html.parser")
    table = body.find("table", class_="cnmats")
    if not table:
        logging.warning(f"No table found on {link}")
        return

    data = []
    for row in table.find("tbody").find_all("tr"):
        cell_with_link = row.find("td")
        if cell_with_link and cell_with_link.find("a"):
            product_link = URL_PREFIX + cell_with_link.find("a")["href"]
            product_data = await async_process_element(session, product_link)
            if product_data:
                data.append(product_data)

    # Save JSON
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    logging.info(f"Page {page} saved: {file_path}")


async def async_process_pages(session, link, path):
    """Processes all pages in a category asynchronously."""
    logging.info(f"Processing category: {path}")
    
    html = await async_fetch(session, link)
    if not html:
        logging.warning(f"Skipping category (failed fetch): {link}")
        return  

    body = BeautifulSoup(html, "html.parser")
    max_page = 1
    last_page_link = body.find("div", class_="numlist")
    if last_page_link:
        try:
            max_page = int(last_page_link.find_all("a")[-1].text)
        except (ValueError, IndexError):
            max_page = 1

    os.makedirs(path, exist_ok=True)

    tasks = [async_process_page(session, f"{link}?page={page}", path, page) for page in range(1, max_page + 1)]
    await asyncio.gather(*tasks)

    logging.info(f"Finished category: {path}")


async def worker(queue, session):
    """Worker that processes links from the queue."""
    while not queue.empty():
        path, link = await queue.get()
        logging.info(f"Worker started processing: {path}")
        await async_process_pages(session, link, path)
        queue.task_done()
        logging.info(f"Worker finished: {path}")


async def async_batch_process_links():
    """Manages async workers and batches links for processing."""
    queue = asyncio.Queue()
    for path, link in links_to_table:
        queue.put_nowait((path, link))

    logging.info(f"Starting batch processing with {min(20, len(links_to_table))} workers...")

    async with aiohttp.ClientSession() as session:
        workers = [asyncio.create_task(worker(queue, session)) for _ in range(20)]  # 10 workers
        await queue.join()  # Wait until queue is processed
        for w in workers:
            w.cancel()  # Cancel workers when done

    logging.info("All categories processed!")


def dfs(body, path):
    """Recursively extracts table links from categories."""
    path_element = body.find("a").text.strip().replace(" ", "_")
    new_path = os.path.join(path, path_element)

    if body.find("ul"):
        for child in body.find("ul").find_all("li", recursive=False):
            dfs(child, new_path)
    else:
        link = URL_PREFIX + body.find("a")["href"]
        links_to_table.append((new_path, link))


def run():
    """Extracts category links using DFS."""
    logging.info("Fetching main catalog page...")
    response = requests.get(URL, headers=HEADERS, verify=False)
    if response.status_code != 200:
        logging.error(f"Error fetching main page: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    whole_body = soup.find("ul", class_="leftcats")
    if whole_body:
        all_categories = whole_body.find_all("li", recursive=False)
        for category in all_categories:
            dfs(category, "Данные")

    logging.info(f"Found {len(links_to_table)} categories to process.")


if __name__ == "__main__":
    print("🚀 Starting scraper... (logs are written to scraper.log)")
    run()  # Extract category links using DFS
    asyncio.run(async_batch_process_links())  # Process categories asynchronously
    print("✅ Scraper finished! Check scraper.log for details.")

import os
import json
import asyncio
import requests
from bs4 import BeautifulSoup
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
warnings.simplefilter("ignore", InsecureRequestWarning)

# Base URLs
URL = "https://rostmetall.kz/catalog"
URL_prefix = "https://rostmetall.kz"

# Headers to prevent blocking
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Stores category paths and their respective links
links_to_table = []

# Batch size for async processing
BATCH_SIZE = 50


def get_or_create_file(path, file_name):
    """Creates a file if it doesn't exist and returns the file path."""
    file_path = os.path.join(path, file_name)
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("")
    return file_path


def get_or_create_folder(path):
    """Creates a folder if it doesn't exist and returns its path."""
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def fetch(url):
    """Fetches HTML content synchronously with SSL verification disabled."""
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"⚠️ Error {response.status_code} fetching {url}")
            return None
    except requests.RequestException as e:
        print(f"⚠️ Request error fetching {url}: {e}")
        return None


def process_element(link):
    """Fetches and processes an individual product page synchronously."""
    json_data = {}

    html = fetch(link)
    if not html:
        return None  # Skip if failed

    body = BeautifulSoup(html, "html.parser")

    text = body.find("h1", class_="producth")
    if text:
        element_name = " ".join(text.text.strip().split()[:-2])
        json_data["Наименование"] = element_name

    element_data = body.find("ul", class_="prodchars")
    if element_data:
        for data in element_data.find_all("li"):
            key = data.find("span", class_="pchname").text.strip()
            value = data.find("span", class_="pchopt").text.strip()
            json_data[key] = value

    return json_data


def process_page(link, path, page):
    """Processes an entire product page synchronously and saves the data."""
    data = []
    file_path = get_or_create_file(path, f"page_{page}.json")

    html = fetch(link)
    if not html:
        return  # Skip if failed

    body = BeautifulSoup(html, "html.parser")

    table = body.find("table", class_="cnmats")
    if not table:
        print(f"⚠️ No table found on {link}")
        return

    table_body = table.find("tbody")
    table_rows = table_body.find_all("tr") if table_body else []

    for row in table_rows:
        cell_with_link = row.find("td")
        if cell_with_link and cell_with_link.find("a"):
            product_link = URL_prefix + cell_with_link.find("a")["href"]
            data.append(process_element(product_link))

    # Remove None results (failed requests)
    data = [item for item in data if item]

    # Save JSON
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"✅ Page {page} saved: {file_path}")


def process_pages(link, path):
    """Processes all pages in a category synchronously."""
    html = fetch(link)
    if not html:
        return  # Skip if failed

    body = BeautifulSoup(html, "html.parser")
    path = get_or_create_folder(path)

    last_page_link = body.find("div", class_="numlist")
    if last_page_link:
        try:
            max_page = int(last_page_link.find_all("a")[-1]["href"].split("=")[-1])
        except (ValueError, IndexError):
            max_page = 1
    else:
        max_page = 1

    for page in range(1, max_page + 1):
        page_link = f"{link}?page={page}"
        process_page(page_link, path, page)

    print(f"✅ Category processed: {path}")


def dfs(body, path):
    """Recursively extracts table links from categories."""
    path_element = body.find("a").text.strip().replace(" ", "_")
    path = f"{path}/{path_element}"

    if body.find("ul"):
        sub_categories = body.find("ul")
        children = sub_categories.find_all("li", recursive=False)

        for child in children:
            dfs(child, path)
    else:
        link = URL_prefix + body.find("a")["href"]
        links_to_table.append((path, link))


def run():
    """Sync part: Extracts links using DFS."""
    response = requests.get(URL, headers=headers, verify=False)
    if response.status_code != 200:
        print(f"⚠️ Error fetching main page: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    whole_body = soup.find_all("ul", class_="leftcats")[0]
    all_categories = whole_body.find_all("li", recursive=False)

    for category in all_categories:
        dfs(category, "Данные")

    print(f"📌 Found {len(links_to_table)} categories to process.")


async def async_batch_process_links():
    """Processes batches asynchronously but keeps per-page logic synchronous."""
    async def process_batch(batch):
        """Helper function to run a batch in parallel."""
        loop = asyncio.get_running_loop()
        await asyncio.gather(*[loop.run_in_executor(None, process_pages, link, path) for path, link in batch])

    for i in range(0, len(links_to_table), BATCH_SIZE):
        batch = links_to_table[i:i + BATCH_SIZE]
        print(f"🔹 Processing batch {i // BATCH_SIZE + 1}: {len(batch)} categories")
        await process_batch(batch)
        print(f"✅ Batch {i // BATCH_SIZE + 1} completed.")


if __name__ == "__main__":
    run()  # Synchronous DFS to gather links
    asyncio.run(async_batch_process_links())  # Async batch processing with sync page logic

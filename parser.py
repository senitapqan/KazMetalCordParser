import requests
import json
import os
from bs4 import BeautifulSoup

URL = "https://rostmetall.kz/catalog"
URL_prefix = "https://rostmetall.kz"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
response = requests.get(URL, headers=headers)

links_to_table = []

def get_or_create_file(path, file_name):
    file_path = os.path.join(path, file_name)

    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("")

    return file_path

def get_or_create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        return path
    else:
        return path
        

def process_element(link, file_path):
    json_data = {}

    response = requests.get(link, headers=headers)
    body = BeautifulSoup(response.text, "html.parser")

    text = body.find("h1", class_="producth").text.strip()
    element_name = " ".join(text.split()[:-2])
    json_data["Наименование"] = element_name

    element_data = body.find("ul", class_="prodchars").find_all("li")
    for data in element_data:
        key = data.find("span", class_="pchname").text.strip()
        value = data.find("span", class_="pchopt").text.strip()
        json_data[key] = value

    return json_data

def process_page(link, path, page):
    data = []
    file_path = get_or_create_file(path, "page_" + str(page) + ".json")

    response = requests.get(link, headers=headers)
    body = BeautifulSoup(response.text, "html.parser")

    table = body.find("table", class_="cnmats")
    table_body = table.find("tbody")
    table_rows = table_body.find_all("tr")
    for row in table_rows:
        cell_with_link = row.find("td")
        link = URL_prefix + cell_with_link.find("a")["href"]
        data.append(process_element(link, file_path))

    print("path with page done: ", file_path)
        
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        

def process_pages(link, path):
    response = requests.get(link, headers=headers)
    body = BeautifulSoup(response.text, "html.parser")

    path = get_or_create_folder(path)

    last_page_link = body.find("div", class_="numlist").find_all("a")[-1]["href"]
    max_page = last_page_link.split("=")[-1]

    for page in range(1, int(max_page) + 1):
        page_link = link + "?page=" + str(page)
        process_page(page_link, path, page)

    print("path done: ", path)

def dfs(body, path):
    path_element = body.find("a").text.strip().replace(" ", "_")
    path = path + "/" + path_element

    if body.find("ul"):
        sub_categories = body.find("ul")
        children = sub_categories.find_all("li", recursive=False)

        for child in children:
            dfs(child, path)
    else:
        link = URL_prefix + body.find("a")["href"]
        links_to_table.append((path, link))

def run(body):
    whole_body = body.find_all("ul", class_="leftcats")[0]
    all_categories = whole_body.find_all("li", recursive=False)

    for category in all_categories:
        dfs(category, "Данные")


    print("all links to tables: ", len(links_to_table))
    for (path, link) in links_to_table:
        process_pages(link, path)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    run(soup)
else:
    print(f"Error: {response.status_code}")



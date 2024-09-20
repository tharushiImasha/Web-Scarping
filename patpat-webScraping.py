import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
 
# Base URL
base_url = "https://patpat.lk/property/filter/land"

# Helper function to extract values from the table
def get_table_value(soup, key_text):
    try:
        rows = soup.find_all('tr')
        for row in rows:
            if key_text in row.find('td').text:
                return row.find_all('td')[1].text.strip()
    except AttributeError:
        return ""

# Extract title
def get_title(soup):
    try:
        title = soup.find("h2").text.strip()
    except AttributeError:
        title = ""
    return title

# Extract location
def get_location(soup):
    return get_table_value(soup, "Location")

# Extract land size
def get_land_size(soup):
    return get_table_value(soup, "Land Size")

# Extract total price
def get_total_price(soup):
    try:
        price_div = soup.find("div", class_="item-price")
        price = price_div.find_all("span")[1].text.strip()  # Extract the price value
    except (AttributeError, IndexError):
        price = ""
    return price

# Function to scrape a single page
def scrape_page(url):
    response = requests.get(url)
    links_list = []
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all("a", attrs={'class': 'mb-1'})
        base_url = "https://patpat.lk"

        for link in links:
            href = link.get('href')
            if not href.startswith("http"):
                href = base_url + href  # Prepend base URL if the link is relative
            links_list.append(href)

        d = {"title": [], "location": [], "land_size": [], "total_price": []}

        for link in links_list:
            new_response = requests.get(link)
            if new_response.status_code == 200:
                new_soup = BeautifulSoup(new_response.content, 'html.parser')

                # Append the scraped data to the dictionary
                d['title'].append(get_title(new_soup))
                d['location'].append(get_location(new_soup))
                d['land_size'].append(get_land_size(new_soup))
                d['total_price'].append(get_total_price(new_soup))

        return pd.DataFrame.from_dict(d)
    else:
        return pd.DataFrame()  # Return empty DataFrame if the request fails

# Main function to scrape all pages
def scrape_all_pages(base_url):
    page_number = 1
    all_data = pd.DataFrame()

    while(page_number < 7):
        print(f"Scraping page {page_number}...")
        page_url = f"{base_url}?page={page_number}"
        page_data = scrape_page(page_url)

        # Break the loop if no data is found (likely last page)
        if page_data.empty:
            break

        # Concatenate the data from this page to the main DataFrame
        all_data = pd.concat([all_data, page_data], ignore_index=True)

        # Proceed to the next page
        page_number += 1

    # Clean and save the data
    # Step 1: Remove rows where the title is "Explore by categories"
    all_data = all_data[all_data['title'] != "Explore by categories"]

    # Step 2: Remove duplicates
    all_data = all_data.drop_duplicates()

    # Step 3: Drop rows where the title is empty or missing
    all_data['title'].replace('', np.nan, inplace=True)
    all_data = all_data.dropna(subset=['title'])

    # Save the cleaned data to a CSV file
    all_data.to_csv("all_land_data.csv", header=True, index=False)

# Start scraping all pages
scrape_all_pages(base_url)

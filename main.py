import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urlparse, urljoin

# Set the maximum number of URLs to fetch
MAX_URLS = 20

# Set the URL of the website to crawl
base_url = 'https://www.nytimes.com/'

# Initialize lists to store URLs and their status codes
url_list = []
status_list = []

# Initialize lists to store visited URLs, their sizes, outlinks count, and content types
visited_list = []
size_list = []
outlinks_list = []
content_type_list = []

# Initialize set to store all encountered URLs
all_urls = set()

# Initialize a counter for the number of fetched URLs
url_count = 0

# Define a function to check if a URL is valid and belongs to the website
def is_valid(url):
    """
    Returns True if the URL is valid and belongs to the website,
    False otherwise.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and parsed.netloc == urlparse(base_url).netloc

# Define a function to fetch a URL and return its status code
def fetch_url(url):
    """
    Sends a GET request to the URL and returns the status code.
    """
    try:
        response = requests.get(url)
        return response.status_code
    except:
        return None

# Define a function to visit a URL and collect its information
def visit_url(url):
    """
    Sends a GET request to the URL, collects its information,
    and appends the information to the respective lists.
    """
    try:
        response = requests.get(url)
        content_type = response.headers.get('content-type')
        size = len(response.content)
        outlinks = len(get_all_links(response.content))
        visited_list.append(url)
        size_list.append(size)
        outlinks_list.append(outlinks)
        content_type_list.append(content_type)
    except:
        pass

# Define a function to extract all links from a web page
def get_all_links(html):
    """
    Parses the HTML content and returns all links in the content.
    """
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href is not None:
            href = urljoin(base_url, href)
            if is_valid(href):
                links.append(href)
    return links

# Add the base URL to the URL list
url_list.append(base_url)

# Process each URL in the list until the maximum number of URLs is reached
while url_count < MAX_URLS and url_list:
    # Get the next URL from the list
    url = url_list.pop(0)

    # Fetch the URL and get its status code
    status = fetch_url(url)

    # Append the URL and its status code to the respective lists
    url_list.append(url)
    status_list.append(status)

    # If the status code is 200, visit the URL and collect its information
    if status == 200:
        visit_url(url)

        # Get all links from the web page and add them to the URL list
        links = get_all_links(requests.get(url).content)
        for link in links:
            if link not in all_urls:
                url_list.append(link)
                all_urls.add(link)

    # Increment the URL counter
    url_count += 1

# Write the fetch information to a CSV file
with open('fetch_NYTimes.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['URL', 'Status'])
    for url, status in zip(url_list, status_list):
        writer.writerow([url, status])

#Write the visit information to a CSV file
with open('visit_NYTimes.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['URL', 'Size (Bytes)', 'Outlinks Count', 'Content-Type'])
    for url, size, outlinks, content_type in zip(visited_list, size_list, outlinks_list, content_type_list):
        writer.writerow([url, size, outlinks, content_type])

#Write the encountered URLs to a CSV file
with open('urls_NYTimes.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['URL', 'Indicator'])
    for url in all_urls:
        if is_valid(url):
            writer.writerow([url, 'OK'])
        else:
            writer.writerow([url, 'N_OK'])
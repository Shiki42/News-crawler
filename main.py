import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urlparse, urljoin

# Set the maximum number of URLs to fetch
MAX_URLS = 20000
MAX_DEPTH = 16
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

# Initialize counters for fetch statistics
fetch_attempted = 0
fetch_succeeded = 0
fetch_failed_aborted = 0

# Initialize counters for URL statistics
total_urls_extracted = 0
unique_urls_extracted = set()
unique_urls_within_news_site = set()
unique_urls_outside_news_site = set()

# Initialize dictionary to store status codes and their counts
status_code_counts = {}

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

    # If the status code is not None, increment the fetch_attempted counter
    if status is not None:
        fetch_attempted += 1

    # If the status code is 200, increment the fetch_succeeded counter and visit the URL
    if status == 200:
        fetch_succeeded += 1

#Write the fetch statistics to a CSV file
with open('fetch_statistics.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['# Fetches Attempted', '# Fetches Succeeded', '# Fetches Failed/Aborted'])
    writer.writerow([url_count, status_list.count(200), url_count - status_list.count(200)])

#Write the URLs extracted statistics to a CSV file
with open('urls_extracted_statistics.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Total URLs Extracted', '# Unique URLs Extracted', '# Unique URLs Within News Website', '# Unique URLs Outside News Website'])
    writer.writerow([len(all_urls), len(set(all_urls)), len(website_urls), len(set(all_urls) - set(website_urls))])

#Write the status codes statistics to a CSV file
with open('status_codes_statistics.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Status Code', 'Count'])
    status_codes = set(status_list)
    for status_code in status_codes:
        writer.writerow([status_code, status_list.count(status_code)])

#Write the file sizes statistics to a CSV file
with open('file_sizes_statistics.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['File Size Range', 'Number of Files'])
        file_sizes = [0, 1024, 1024*1024]
        file_size_ranges = [f'{file_sizes[i]}-{file_sizes[i+1]} Bytes' for i in range(len(file_sizes)-1)]
        file_size_ranges.append(f'{file_sizes[-1]}+ Bytes')
        file_size_counts = [0] * len(file_size_ranges)
        for size in size_list:
            for i, file_size in enumerate(file_sizes):
                if size < file_size:
                    file_size_counts[i] += 1
                    break
                else:
                    file_size_counts[-1] += 1
        for file_size_range, count in zip(file_size_ranges, file_size_counts):
            writer.writerow([file_size_range, count])

#Write the content types statistics to a CSV file
with open('content_types_statistics.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Content Type', 'Count'])
    content_types = set(content_type_list)
    for content_type in content_types:
        writer.writerow([content_type, content_type_list.count(content_type)])
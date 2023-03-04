import concurrent.futures
import threading
import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urlparse, urljoin
from collections import Counter
import time

#Fetch statistics
n_fetches_attempted = 0
n_fetches_succeeded = 0
n_fetches_failed_or_aborted = 0

#Outgoing URLs
n_total_URLs_extracted = 0
n_unique_URLs_extracted = 0
n_unique_URLs_within = 0
n_unique_URLs_outside = 0

# Set the maximum number of URLs to fetch
MAX_URLS = 200
MAX_DEPTH = 16

# Set the URL of the website to crawl
base_url = 'https://www.nytimes.com/'

all_urls = []
unique_outside_urls = set()
unique_inside_urls = set()
HTTP_status_counter = Counter()
content_type_counter = Counter()
url_queue = []

url_attempted = set()
url_attempted_with_status = []

# Initialize lists to store visited URLs, their sizes, outlinks count, and content types
success_url_list = []
size_list = []
outlinks_list = []
content_type_list = []

url_count = 0

queue_url_lock = threading.Lock()
all_url_lock = threading.Lock()
success_url_lock = threading.Lock()
attempted_url_lock = threading.Lock()

# Define a function to check if a URL is valid and belongs to the website
def is_inside(url):
    """
    Returns True if the URL is valid and belongs to the website,
    False otherwise.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and parsed.netloc == urlparse(base_url).netloc

# Define a function to visit a URL and collect its information
def fetch_url(zipped_url):
    """
    Sends a GET request to the URL, collects its information,
    and appends the information to the respective lists.
    """
    url, depth = zipped_url

    time.sleep(2)

    global n_fetches_attempted, n_fetches_succeeded, n_fetches_failed_or_aborted, \
           n_total_URLs_extracted, n_unique_URLs_extracted, n_unique_URLs_within, \
           n_unique_URLs_outside, url_count

    response = requests.get(url)
        
    status = response.status_code

    with queue_url_lock:
        url_attempted.add(url)

    with attempted_url_lock:
        url_count += 1
        n_fetches_attempted += 1
        url_attempted_with_status.append((url,status))
        HTTP_status_counter[status] += 1
        if status == 200:
            n_fetches_succeeded += 1
        else:        
            n_fetches_failed_or_aborted += 1

    if status == 200:

        content_type = response.headers.get('content-type')
        size = len(response.content)

        if 'text/html' in content_type:        
            outlinks = get_all_links(response.content)

            with all_url_lock:                
                    for i in outlinks:
                        all_urls.append(i)
                        n_total_URLs_extracted += 1
                        if is_inside(i):
                            unique_inside_urls.add(i)
                            if i not in url_attempted and depth <= 16:
                                with queue_url_lock:
                                    url_queue.append((i,depth+1))
                        else:
                            unique_inside_urls.add(i)

        with success_url_lock:
            if 'text/html' not in content_type:
                outlinks_list.append(0) 
            else:
                outlinks_list.append(len(outlinks))
            success_url_list.append(url)
            size_list.append(size)        
            content_type_list.append(content_type)

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
            links.append(href)
    return links

# Add the base URL to the URL list
url_queue.append((base_url,1))

# Process each URL in the list until the maximum number of URLs is reached
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:

    while url_count < MAX_URLS and url_queue:
        # Get the next URL from the list
        with queue_url_lock:
            url = url_queue.pop(0)        

        # Fetch the URL and get its status code
        executor.submit(fetch_url, url)

        # Increment the URL counter                
        print(url_count)

with open('fetch_NYTimes.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['URL', 'Status'])
    for url, status in url_attempted_with_status:
        writer.writerow([url, status])

#Write the visit information to a CSV file
with open('visit_NYTimes.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['URL', 'Size (Bytes)', 'Outlinks Count', 'Content-Type'])
    for url, size, outlinks, content_type in zip(success_url_list, size_list, outlinks_list, content_type_list):
        writer.writerow([url, size, outlinks, content_type])

#Write the encountered URLs to a CSV file
with open('urls_NYTimes.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['URL', 'Indicator'])
    for url in all_urls:
        if is_inside(url):
            writer.writerow([url, 'OK'])
        else:
            writer.writerow([url, 'N_OK'])


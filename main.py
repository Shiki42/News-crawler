import queue
import threading
import concurrent.futures

import re
import csv
import time
from collections import Counter

import requests
from bs4 import BeautifulSoup
from requests import status_codes
from urllib.parse import urlparse, urljoin


#Fetch statistics
n_fetches_attempted = 0
n_fetches_succeeded = 0
n_fetches_failed_or_aborted = 0

n_total_URLs_extracted = 0

# Set the maximum number of URLs to fetch
MAX_URLS = 20000
MAX_DEPTH = 16

# Set the URL of the website to crawl
base_url = 'https://www.nytimes.com/'

all_urls = []
unique_outside_urls = set()
unique_inside_urls = set()
HTTP_status_counter = Counter()
content_type_counter = Counter()
url_queue = queue.Queue()

url_attempted = set()
url_attempted_with_status = []

# Initialize lists to store visited URLs, their sizes, outlinks count, and content types
success_url_list = []
size_list = []
outlinks_list = []
content_type_list = []

url_count = 0

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
    if not parsed.netloc:
        # Construct an absolute URL using the base URL and the relative URL
        url = urljoin(base_url, url)
    return bool(urlparse(url).netloc) and urlparse(url).netloc == urlparse(base_url).netloc

def is_valid_url(url):
    # Define a regular expression pattern to match against URLs with extensions for HTML, doc, pdf and image
    valid_extensions = r'\.(html|doc|pdf|png|jpg|jpeg|gif)$'
    # Use regex to check if the URL ends with one of the valid extensions
    if re.search(valid_extensions, url):
        return True
    else:
        return False

# Define a function to visit a URL and collect its information
def fetch_url():
    """
    Sends a GET request to the URL, collects its information,
    and appends the information to the respective lists.
    """

    global n_fetches_attempted, n_fetches_succeeded, n_fetches_failed_or_aborted, \
       n_total_URLs_extracted, n_unique_URLs_extracted, n_unique_URLs_within, \
       n_unique_URLs_outside, url_count, url_queue, MAX_DEPTH

    try:
        url, depth = url_queue.get(timeout=5)
    except queue.Empty:
        return   
    
    time.sleep(1)

    response = requests.get(url)
        
    status = response.status_code

    with attempted_url_lock:
        url_attempted.add(url)
        url_count += 1
        print(url_count)
        n_fetches_attempted += 1
        url_attempted_with_status.append((url,status))
        status_text = status_codes._codes[status][0] if status in status_codes._codes else ''
        status_str = f"{status} {status_text}"
        HTTP_status_counter[status_str] += 1
        if status == 200:
            n_fetches_succeeded += 1
        else:        
            n_fetches_failed_or_aborted += 1

    if status == 200:

        content_type = response.headers.get('content-type').split(';')[0].strip()
        size = len(response.content)

        if 'text/html' in content_type:        
            outlinks = get_all_links(response.content)

            with all_url_lock:                
                    for i in outlinks:
                        all_urls.append(i)
                        n_total_URLs_extracted += 1
                        if is_inside(i):
                            unique_inside_urls.add(i)
                            with attempted_url_lock:
                                if i not in url_attempted and depth <= MAX_DEPTH and is_valid_url(i):                                
                                    url_queue.put((i,depth+1))
                        else:
                            unique_outside_urls.add(i)

        with success_url_lock:
            if 'text/html' not in content_type:
                outlinks_list.append(0) 
            else:
                outlinks_list.append(len(outlinks))
            success_url_list.append(url)
            size_list.append(size)        
            content_type_list.append(content_type)
            content_type_counter[content_type] += 1

    url_queue.task_done()
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
url_queue.put((base_url,1))

# Process each URL in the list until the maximum number of URLs is reached
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:

    for i in range(MAX_URLS):

        # Fetch the URL and get its status code
        executor.submit(fetch_url)
                

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

with open('CrawlReport_nytimes.txt', 'w') as f:
    # Write personal information
    f.write("Name: Shuyuan Hu\n")
    f.write("USC ID: 2512145714\n")
    f.write("News site crawled: nytimes.com\n")
    f.write("Number of threads: 16\n\n")

    # Write fetch statistics
    f.write("Fetch Statistics\n")
    f.write("================\n")
    f.write("# fetches attempted: {}\n".format(n_fetches_attempted))
    f.write("# fetches succeeded: {}\n".format(n_fetches_succeeded))
    f.write("# fetches failed or aborted: {}\n\n".format(n_fetches_failed_or_aborted))

    # Write outgoing URLs
    f.write("Outgoing URLs:\n")
    f.write("==============\n")
    f.write("Total URLs extracted: {}\n".format(n_total_URLs_extracted))
    f.write("# unique URLs extracted: {}\n".format(len(unique_inside_urls)+len(unique_outside_urls)))
    f.write("# unique URLs within News Site: {}\n".format(len(unique_inside_urls)))
    f.write("# unique URLs outside News Site: {}\n\n".format(len(unique_outside_urls)))

    # Write status codes
    f.write("Status Codes:\n")
    f.write("=============\n")
    for code, count in HTTP_status_counter.items():
        f.write("{}: {}\n".format(code, count))
    f.write("\n")

    # Write file sizes
    f.write("File Sizes:\n")
    f.write("===========\n")
    size_ranges = [
        ("< 1KB", lambda size: size < 1024),
        ("1KB ~ <10KB", lambda size: 1024 <= size < 10240),
        ("10KB ~ <100KB", lambda size: 10240 <= size < 102400),
        ("100KB ~ <1MB", lambda size: 102400 <= size < 1048576),
        (">= 1MB", lambda size: size >= 1048576)
    ]
    for name, size_range in size_ranges:
        count = sum(1 for size in size_list if size_range(size))
        f.write("{}: {}\n".format(name, count))
    f.write("\n")

    # Write content types
    f.write("Content Types:\n")
    f.write("===============\n")
    for content_type, count in content_type_counter.items():
        f.write("{}: {}\n".format(content_type, count))
    f.write("\n")
import queue
import threading
import concurrent.futures

import re
import csv
import time
import random
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
n_threads = 16

# Set the URL of the website to crawl
news_site = 'foxnews'
origin_url = 'https://www.foxnews.com/'
base_url_parts = urlparse(origin_url)
base_url = f"{base_url_parts.scheme}://{base_url_parts.netloc}{base_url_parts.path}"

all_urls = []
unique_outside_urls = set()
unique_inside_urls = set()
HTTP_status_counter = Counter()
content_type_counter = Counter()
url_queue = queue.Queue()

url_attempt = set()
url_attempt_with_status = []

# Initialize lists to store visited URLs, their sizes, outlinks count, and content types
success_url_list = []
size_list = []
outlinks_list = []
content_type_list = []

url_count = 0


all_url_lock = threading.Lock()
visit_url_lock = threading.Lock()
success_url_lock = threading.Lock()

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
    """
    Returns True if the URL is valid and belongs to the website and has a valid file extension,
    False otherwise.
    """
    # Define a regular expression pattern to match against URLs with extensions for HTML, doc, pdf, png, jpg, jpeg, and gif
    valid_extensions = r'\.(html|doc|pdf|png|jpe?g|gif)(\?.*)?(#.*)?'
    
    parsed = urlparse(url)
    #if 'wirecutter/feed' in parsed.path:
    #    return False
    # Check if the URL has a file extension
    if '.' in parsed.path:
        # Use regex to check if the file extension is valid
        if re.search(valid_extensions, parsed.path):
            return True
        else:
            return False
    else:
        return True

# Define a function to visit a URL and collect its information
def fetch_url():
    """
    Sends a GET request to the URL, collects its information,
    and appends the information to the respective lists.
    """

    global n_fetches_attempted, n_fetches_succeeded, n_fetches_failed_or_aborted, \
       n_total_URLs_extracted, n_unique_URLs_extracted, n_unique_URLs_within, \
       n_unique_URLs_outside, url_count, url_queue, MAX_DEPTH
    #time.sleep(1)
    
    with visit_url_lock:
        if url_count >= 20000:
            return

    try:
        url, depth = url_queue.get(timeout=10)            
    except queue.Empty:
        return   
    
    

    try:
        response = requests.get(url,timeout = 5)
        # Do something with the response
    except requests.exceptions.Timeout:
        print('The request timed out.')
        return
   
    status = response.status_code

    with visit_url_lock:            
        url_count += 1
        print(url_count)
        n_fetches_attempted += 1
        url_attempt_with_status.append((url,status))
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
                        if i not in url_attempt and depth <= MAX_DEPTH and is_valid_url(i):                                
                            url_queue.put((i,depth+1))
                            url_attempt.add(i)
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
    Parses the HTML content and returns all unique links in the content.
    """
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for tag in soup.select('[href]'):
        href = tag.get('href')
        if href is not None:
            href = urljoin(base_url, href)            
            url_parts = urlparse(href)
            nomed_url = f"{url_parts.scheme}://{url_parts.netloc}{url_parts.path}"            
            links.add(nomed_url)
    return list(links)

'''
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
'''

if __name__ == '__main__':
    # Add the base URL to the URL list
    url_queue.put((base_url,1))
    url_attempt.add(base_url)
    # Process each URL in the list until the maximum number of URLs is reached
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:

            #for i in range(MAX_URLS):
            for i in range(MAX_URLS+1000):
            # Fetch the URL and get its status code
                executor.submit(fetch_url)
                    

    with open(f'fetch_{news_site}.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'HTTP/HTTPS status code'])
        for url, status in url_attempt_with_status:
            writer.writerow([url, status])

    # Write the visit information to a CSV file
    with open(f'visit_{news_site}.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        print('Sum of outlinks:')
        print(sum(outlinks_list))
        writer.writerow(['URL', 'Size (Bytes)', 'Outlinks Count', 'Content-Type'])
        for url, size, outlinks, content_type in zip(success_url_list, size_list, outlinks_list, content_type_list):
            writer.writerow([url, size, outlinks, content_type])

    # Write the encountered URLs to a CSV file
    with open(f'urls_{news_site}.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Indicator'])
        for url in all_urls:
            if is_inside(url):
                writer.writerow([url, 'OK'])
            else:
                writer.writerow([url, 'N_OK'])

    with open(f'CrawlReport_{news_site}.txt', 'w') as f:
        # Write personal information
        f.write("Name: Shuyuan Hu\n")
        f.write("USC ID: 2512145714\n")
        f.write(f"News site crawled: {news_site}.com\n")
        f.write("Number of threads: {}\n\n".format(n_threads))

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
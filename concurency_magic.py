import queue
import threading
import concurrent.futures

import requests
from bs4 import BeautifulSoup
from requests import status_codes
from urllib.parse import urlparse, urljoin

base_url = 'https://www.foxnews.com/'
visit_url_lock = threading.Lock()

url_count = 0
url_attempt = set()
url_queue = queue.Queue()

def fetch_url():

    global url_queue, url_attempt, url_count

    try:
        url, depth = url_queue.get(timeout=10)            
    except queue.Empty:
        return

    try:
        response = requests.get(url,timeout = 5)
    except requests.exceptions.Timeout:
        return

    with visit_url_lock:            
        url_count += 1
        print(url_count)

    status = response.status_code
    if status == 200:
        content_type = response.headers.get('content-type').split(';')[0].strip()

        if 'text/html' in content_type:        
            outlinks = get_all_links(response.content)

        with all_url_lock:
            for i in outlinks:
                if i not in url_attempt:                                
                    url_queue.put((i,depth+1))
                    url_attempt.add(i)

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

url_queue.put((base_url,1))
url_attempt.add(base_url)

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:

        while url_count<20000:        
            executor.submit(fetch_url)
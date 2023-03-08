import queue
import threading
import concurrent.futures
import time
lock = threading.Lock()

url_count = 0

url_queue = queue.Queue()
url_queue.put(1)
url_queue.put(2)
url_queue.put(3)
url_queue.put(4)

def fetch_url():

    global url_queue, url_count

    try:
        url = url_queue.get(timeout=10)            
    except queue.Empty:
        return

    url_queue.put(1)

    with lock:            
        url_count += 1
        print(url_count)

    time.sleep(1)

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:

        while url_count<20000:        
            executor.submit(fetch_url)
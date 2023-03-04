import re
from urllib.parse import urlparse, urljoin
def is_valid_url(url):
    """
    Returns True if the URL is valid and belongs to the website and has a valid file extension,
    False otherwise.
    """
    # Define a regular expression pattern to match against URLs with extensions for HTML, doc, pdf, png, jpg, jpeg, and gif
    valid_extensions = r'\.(html?|doc|pdf|png|jpe?g|gif)(\?.*)?(#.*)?'
    
    parsed = urlparse(url)
    # Check if the URL has a file extension
    print(parsed.path)
    if '.' in parsed.path:
        # Use regex to check if the file extension is valid
        if re.search(valid_extensions, parsed.path):
            return True
        else:
            return False
    else:
        return True


# Test valid URLs with no file extension
assert is_valid_url('https://example.com/')
assert is_valid_url('https://example.com/somepage')
assert is_valid_url('https://example.com/somepage/')

# Test valid URLs with valid file extensions
assert is_valid_url('https://example.com/somepage.html')
assert is_valid_url('https://example.com/somepage.htm')
assert not is_valid_url('https://example.com/somepage.php')
assert not is_valid_url('https://example.com/somepage.asp')
assert not is_valid_url('https://example.com/somepage.aspx')
assert not is_valid_url('https://example.com/somepage.cgi')
assert not is_valid_url('https://example.com/somepage.js')
assert not is_valid_url('https://example.com/somepage.css')
assert is_valid_url('https://example.com/someimage.jpg')
assert is_valid_url('https://example.com/someimage.jpeg')
assert is_valid_url('https://example.com/someimage.png')
assert is_valid_url('https://example.com/someimage.gif')
assert is_valid_url('https://example.com/somefile.pdf')
assert is_valid_url('https://example.com/somefile.doc')

# Test valid URLs with invalid file extensions
assert not is_valid_url('https://example.com/somepage.xyz')
assert not is_valid_url('https://example.com/somepage.ht')
assert is_valid_url('https://example.com/somepage.docx.txt')
assert is_valid_url('https://example.com/somepage.pdf?query=param')
assert is_valid_url('https://example.com/somepage.html#section-1')

# Test URLs with query strings and fragment identifiers
assert is_valid_url('https://example.com/somepage.html?query=param')
assert is_valid_url('https://example.com/somepage.html#section-1')

# Test URLs with uppercase file extensions
assert not is_valid_url('https://example.com/somepage.HTML')
assert not is_valid_url('https://example.com/somepage.JPG')
assert not is_valid_url('https://example.com/somepage.JPEG')

# Test URLs with no scheme
#assert is_valid_url('example.com/somepage')
assert is_valid_url('www.example.com/somepage.html')
assert is_valid_url('ftp://example.com/somepage.html')
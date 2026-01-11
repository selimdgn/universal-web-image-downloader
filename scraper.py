import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import re
import argparse
from fake_useragent import UserAgent
import time
import hashlib

class ECommerceScraper:
    def __init__(self, start_url, output_folder="downloads", max_pages=100, 
                 product_selector=None, image_selector=None, name_selector=None, delay=0.5):
        self.start_url = start_url
        self.base_domain = urlparse(start_url).netloc
        self.output_folder = output_folder
        self.max_pages = max_pages
        self.visited = set()
        self.queue = deque([start_url])
        self.ua = UserAgent()
        self.session = requests.Session()
        self.delay = delay
        
        # Selectors
        self.product_selector = product_selector
        self.image_selector = image_selector
        self.name_selector = name_selector

        # Sabit güvenilir User-Agent kullanalım
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8'
        })

        # Product detection heuristics (keywords in URL or page content)
        self.product_keywords = ['product', 'urun', 'item', 'detail', 'p-']
        # Folder name sanitization regex
        self.sanitize_pattern = re.compile(r'[<>:"/\\|?*]')

    def sanitize_filename(self, name):
        """Cleans file and folder names."""
        return self.sanitize_pattern.sub('', name).strip()[:100]  # Max 100 char

    def is_valid_url(self, url):
        """Checks if URL is within the same domain and not visited."""
        parsed = urlparse(url)
        return (parsed.netloc == self.base_domain) and (url not in self.visited)

    def is_product_page(self, soup, url):
        """Decides if the page is a product page."""
        
        # User defined selector
        if self.product_selector:
            if soup.select_one(self.product_selector):
                return True
            return False

        # General Heuristics checks
        
        # Method 1: Keyword in URL
        url_lower = url.lower()
        if any(keyword in url_lower for keyword in self.product_keywords):
            return True
            
        # Method 2: 'Add to Cart', 'Buy' buttons
        buy_buttons = soup.find_all(string=re.compile(r'add to cart|sepete ekle|buy now|satın al', re.IGNORECASE))
        if buy_buttons:
            return True
            
        # Method 3: Price tags
        price_tags = soup.find_all(class_=re.compile(r'price|fiyat', re.IGNORECASE))
        if price_tags:
            return True
            
        return False

    def get_product_name(self, soup):
        """Extracts product name from the page."""
        
        if self.name_selector:
            el = soup.select_one(self.name_selector)
            if el:
                return el.get_text().strip()

        # H1 is usually the product name
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        # Title tag alternative
        if soup.title:
            return soup.title.get_text().strip()
            
        return "Unknown_Product"

    def get_product_images(self, soup):
        """Finds high-res product images on the page."""
        images = []
        
        # User defined selector
        if self.image_selector:
            elements = soup.select(self.image_selector)
            for el in elements:
                # Check different attributes for the image URL
                src = el.get('src') or el.get('data-src') or el.get('href')
                if src:
                     images.append(urljoin(self.start_url, src))
            
            if images:
                return list(set(images))

        # General Logic
        all_imgs = soup.find_all('img')
        
        for img in all_imgs:
            src = img.get('src') or img.get('data-src')
            if not src:
                continue
                
            full_url = urljoin(self.start_url, src)
            
            # Simple extension check
            if not any(full_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                continue
            
            # Simple filter to remove likely icons/logos if not explicitly selected
            if "logo" in full_url.lower() or "icon" in full_url.lower() or "flags" in full_url.lower():
                continue

            images.append(full_url)
            
        return list(set(images))

    def download_image(self, img_url, folder_path, index):
        """Downloads and saves the image."""
        try:
            file_hash = hashlib.md5(img_url.encode('utf-8')).hexdigest()
            
            parsed_url = urlparse(img_url)
            ext = os.path.splitext(parsed_url.path)[1]
            if not ext:
                ext = ".jpg"
            
            filename = f"{file_hash}{ext}"
            filepath = os.path.join(folder_path, filename)
            
            if os.path.exists(filepath):
                print(f"   [.] Already exists: {filename}")
                return

            response = self.session.get(img_url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                print(f"   [+] Downloaded: {filename}")
            else:
                print(f"   [-] Download failed ({response.status_code}): {img_url}")
        except Exception as e:
            print(f"   [!] Error: {img_url} - {e}")

    def run(self):
        print(f"[*] Starting scan: {self.start_url}")
        print(f"[*] Output folder: {self.output_folder}")
        
        domain_folder = self.sanitize_filename(self.base_domain)
        base_output_path = os.path.join(self.output_folder, domain_folder)
        os.makedirs(base_output_path, exist_ok=True)
        
        processed_count = 0
        
        while self.queue and processed_count < self.max_pages:
            url = self.queue.popleft()
            
            if url in self.visited:
                continue
                
            print(f"[{processed_count + 1}/{self.max_pages}] Scanning: {url}")
            
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code != 200:
                    print(f"   [-] Page inaccessible: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                self.visited.add(url)
                processed_count += 1
                
                # Gather links
                found_links = []
                for a_tag in soup.find_all('a', href=True):
                    next_url = urljoin(url, a_tag['href'])
                    if self.is_valid_url(next_url):
                        found_links.append(next_url)
                
                # Filter ignored terms
                ignored_terms = ['login', 'register', 'account', 'signin', 'signup', 'basket', 'cart']
                
                new_links = []
                for link in found_links:
                     if not any(term in link.lower() for term in ignored_terms):
                         if link not in self.queue and link not in self.visited:
                             new_links.append(link)
                
                self.queue.extend(new_links)
                
                # Check if it is a product page
                if self.is_product_page(soup, url):
                    product_name = self.get_product_name(soup)
                    safe_product_name = self.sanitize_filename(product_name)
                    
                    print(f"   [*] Product Found: {product_name}")
                    
                    product_folder = os.path.join(base_output_path, safe_product_name)
                    os.makedirs(product_folder, exist_ok=True)
                    
                    images = self.get_product_images(soup)
                    print(f"   [*] {len(images)} images found.")
                    
                    for idx, img_url in enumerate(images):
                        self.download_image(img_url, product_folder, idx)
                        
            except Exception as e:
                print(f"   [!] Error processing page: {e}")
            
            time.sleep(self.delay)
            
        print("\n[*] Scan completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal Web Image Downloader")
    parser.add_argument("url", help="Target website URL")
    parser.add_argument("--folder", default="downloads", help="Output folder")
    parser.add_argument("--max", type=int, default=100, help="Max pages to scan")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (seconds)")
    parser.add_argument("--product-selector", help="CSS selector to identify product content (e.g. '.product-details')")
    parser.add_argument("--image-selector", help="CSS selector for product images (e.g. '.gallery img')")
    parser.add_argument("--name-selector", help="CSS selector for product name (e.g. 'h1.title')")
    
    args = parser.parse_args()
    
    scraper = ECommerceScraper(
        args.url, 
        output_folder=args.folder, 
        max_pages=args.max,
        delay=args.delay,
        product_selector=args.product_selector,
        image_selector=args.image_selector,
        name_selector=args.name_selector
    )
    scraper.run()

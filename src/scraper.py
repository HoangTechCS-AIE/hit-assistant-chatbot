import requests
from bs4 import BeautifulSoup
import json
import time
import os
from urllib.parse import urljoin

class HaUIScraper:
    BASE_URL = "https://www.haui.edu.vn"
    CATEGORIES = [
        "/vn/tin-tuc",
        "/vn/su-kien",
        "/vn/tuyen-sinh",
    ]
    
    def __init__(self, output_file="data/haui_news.json"):
        self.output_file = output_file
        self.data = []
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def crawl(self):
        """Crawl news and events from HaUI website."""
        print(f"Starting crawl...")
        
        for category in self.CATEGORIES:
            print(f"Crawling category: {category}")
            for page in range(1, 6):  # Crawl first 5 pages
                url = f"{self.BASE_URL}{category}/{page}"
                print(f"  Fetching list page: {url}")
                
                try:
                    response = requests.get(url, headers=self.headers)
                    if response.status_code != 200:
                        print(f"    Failed to fetch {url}: {response.status_code}")
                        continue
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    self._parse_list_page(soup, category)
                    
                    # Sleep to be safe
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"    Error crawling {url}: {e}")

        self._save_data()
        print(f"Crawl completed. Collected {len(self.data)} articles.")

    def _parse_list_page(self, soup, category):
        """Parse the list page to find article links."""
        # This selector might need adjustment based on exact HTML structure
        # Looking for links that look like article details
        # Usually inside a specific container. 
        # Based on typical structure, we look for <a> tags containing the category path
        
        # Inspecting the markdown output from earlier, links look like:
        # https://www.haui.edu.vn/vn/tin-tuc/slug/id
        
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
                 # Check if it's a detail link belonging to the current category
            # Detail links usually have the category prefix and end with a number ID
            if category in href and href.count('/') > 3: 
                 # Simple heuristic: /vn/tin-tuc is 3 parts. /vn/tin-tuc/slug/id is 5 parts.
                 # Let's just check if it starts with category and is not the category page itself
                 full_url = urljoin(self.BASE_URL, href)
                 
                 # Avoid adding duplicates or pagination links
                 if full_url not in [d['url'] for d in self.data]:
                     links.add(full_url)

        # Filter links to ensure they are likely articles (usually have an ID at the end)
        article_links = []
        for link in links:
            # Check if it ends with a number (common for CMS)
            if link.split('/')[-1].isdigit():
                article_links.append(link)
        
        # If no digit found, maybe the ID is mixed. 
        # Let's rely on the user's observation: "Find article links in the list page"
        # I will try to find a container if possible, but without it, I'll use the heuristic.
        # Actually, let's look for a specific container if we can guess it.
        # Often 'div.news-list' or similar.
        # If I can't be sure, I'll just process all unique links that look deeper than the category.
        
        for link in article_links:
            self._process_article(link)

    def _process_article(self, url):
        """Extract title and content from article page."""
        print(f"    Processing article: {url}")
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                return

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract Title
            title_tag = soup.find('h1')
            if not title_tag:
                title_tag = soup.find('p', class_='pTitle')
            title = title_tag.get_text(strip=True) if title_tag else "No Title"
            
            # Extract Content
            # Updated selectors based on inspection
            content_div = soup.find('div', class_='irs-blog-col')
            if not content_div:
                content_div = soup.find('div', class_='content-detail')
            if not content_div:
                content_div = soup.find('article')
            
            if content_div:
                # Remove scripts and styles
                for script in content_div(["script", "style"]):
                    script.decompose()
                
                # Remove the title from content if it's inside
                if title_tag and title_tag in content_div:
                    title_tag.decompose()
                    
                content = content_div.get_text(separator='\n', strip=True)
            else:
                # Fallback: try to find the main content container
                # This is risky, but better than nothing
                content = "Content not found"

            self.data.append({
                "url": url,
                "title": title,
                "content": content
            })
            
            time.sleep(1)

        except Exception as e:
            print(f"    Error processing article {url}: {e}")

    def _save_data(self):
        """Save collected data to JSON file."""
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"Saved data to {self.output_file}")

if __name__ == "__main__":
    scraper = HaUIScraper()
    scraper.crawl()

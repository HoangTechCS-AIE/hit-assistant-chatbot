"""
SICT HaUI Advanced Scraper v2.0
===============================
Features:
- Hierarchical site structure with explicit categories
- Smart pagination with early termination when hitting old articles
- Incremental crawling (only new content since last crawl)
- Parallel category crawling with ThreadPoolExecutor
- Retry mechanism with exponential backoff
- Separate handling for dynamic vs static content

Author: HaUI AI Assistant Team
Date: 2024-12-14
"""

import json
import logging
import os
import re
import hashlib
import time
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ScraperConfig:
    """Configuration for the scraper."""
    base_url: str = "https://sict.haui.edu.vn"
    start_date: datetime = field(default_factory=lambda: datetime(2025, 9, 1))
    output_path: str = "data/sict_haui_data.json"
    state_path: str = "data/scraper_state.json"
    
    # Request settings
    request_timeout: int = 30
    delay_between_requests: float = 0.5
    max_retries: int = 3
    retry_delay: float = 2.0
    
    # Pagination settings
    max_pages_per_category: int = 50
    consecutive_old_threshold: int = 3  # Stop after N consecutive old articles
    
    # Parallel settings
    max_workers: int = 3  # Number of parallel category crawlers
    
    # User agent
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


# ============================================================================
# SITE STRUCTURE
# ============================================================================

@dataclass
class CategoryConfig:
    """Configuration for a single category."""
    name: str
    url: str
    category_type: str  # 'paginated' or 'static'
    date_required: bool
    priority: int
    sub_urls: List[str] = field(default_factory=list)
    description: str = ""


# Complete site structure based on the sitemap
SITE_STRUCTURE: Dict[str, CategoryConfig] = {
    # === DYNAMIC CONTENT (paginated, date-filtered) ===
    "tin-tuc": CategoryConfig(
        name="Tin tức",
        url="/vn/tin-tuc",
        category_type="paginated",
        date_required=True,
        priority=1,
        description="Tin tức sự kiện, hoạt động, thành tích"
    ),
    "thong-bao": CategoryConfig(
        name="Thông báo",
        url="/vn/thong-bao",
        category_type="paginated",
        date_required=True,
        priority=1,
        description="Thông báo chính thức từ trường"
    ),
    "tuyen-dung": CategoryConfig(
        name="Tuyển dụng",
        url="/vn/tuyen-dung",
        category_type="paginated",
        date_required=True,
        priority=2,
        description="Thông tin tuyển dụng, thực tập"
    ),
    "tuyen-sinh": CategoryConfig(
        name="Tuyển sinh",
        url="/vn/tuyen-sinh",
        category_type="paginated",
        date_required=True,
        priority=2,
        sub_urls=[
            "/vn/tuyen-sinh-dai-hoc",
            "/vn/tuyen-sinh-sau-dai-hoc",
        ],
        description="Thông tin tuyển sinh đại học, sau đại học"
    ),
    "khoa-hoc-cong-nghe": CategoryConfig(
        name="Khoa học công nghệ",
        url="/vn/khoa-hoc-cong-nghe",
        category_type="paginated",
        date_required=True,
        priority=3,
        sub_urls=[
            "/vn/cong-trinh-cong-bo",
            "/vn/de-tai-du-an",
            "/vn/sinh-vien-nckh",
            "/vn/tin-khcn",
        ],
        description="Nghiên cứu khoa học, đề tài, dự án"
    ),
    "dao-tao-ngan-han": CategoryConfig(
        name="Đào tạo ngắn hạn",
        url="/vn/dao-tao-ngan-han",
        category_type="paginated",
        date_required=True,
        priority=3,
        description="Các khóa đào tạo ngắn hạn"
    ),
    
    # === STATIC CONTENT (always crawl, no date filter) ===
    "gioi-thieu": CategoryConfig(
        name="Giới thiệu",
        url="/vn/gioi-thieu",
        category_type="static",
        date_required=False,
        priority=4,
        sub_urls=[
            "/vn/thong-tin-chung",
            "/vn/co-cau-to-chuc",
            "/vn/chien-luoc-phat-trien",
            "/vn/can-bo-giang-vien",
            "/vn/co-so-vat-chat",
            "/vn/lien-he",
        ],
        description="Thông tin giới thiệu trường"
    ),
    "nganh-dao-tao": CategoryConfig(
        name="Ngành đào tạo",
        url="/vn/dao-tao",
        category_type="static",
        date_required=False,
        priority=4,
        sub_urls=[
            "/vn/cong-nghe-thong-tin",
            "/vn/khoa-hoc-may-tinh",
            "/vn/ky-thuat-phan-mem",
            "/vn/he-thong-thong-tin",
            "/vn/an-toan-thong-tin",
            "/vn/cong-nghe-da-phuong-tien",
            "/vn/sau-dai-hoc",
            "/vn/he-thong-thong-tin-sdh",
        ],
        description="Thông tin các ngành đào tạo"
    ),
    "khoa-bo-mon": CategoryConfig(
        name="Khoa - Bộ môn",
        url="/vn/khoa",
        category_type="static",
        date_required=False,
        priority=4,
        sub_urls=[
            "/vn/khoa-cong-nghe-thong-tin",
            "/vn/khoa-cong-nghe-phan-mem",
            "/vn/khoa-khoa-hoc-may-tinh",
            "/vn/khoa-mang-may-tinh-va-truyen-thong",
        ],
        description="Thông tin các khoa, bộ môn"
    ),
    "phong-trung-tam": CategoryConfig(
        name="Phòng - Trung tâm",
        url="/vn/don-vi",
        category_type="static",
        date_required=False,
        priority=5,
        sub_urls=[
            "/vn/phong-tong-hop",
            "/vn/trung-tam-hop-tac-phat-trien",
            "/vn/trung-tam-nghien-cuu-va-ung-dung-tri-tue-nhan-tao",
        ],
        description="Thông tin các phòng ban, trung tâm"
    ),
    "quy-che": CategoryConfig(
        name="Quy chế - Biểu mẫu",
        url="/vn/quy-che-bieu-mau",
        category_type="static",
        date_required=False,
        priority=5,
        sub_urls=[
            "/vn/ke-hoach",
            "/vn/tien-do",
        ],
        description="Quy chế, biểu mẫu, kế hoạch đào tạo"
    ),
}


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Article:
    """Represents a scraped article."""
    id: str
    url: str
    title: str
    summary: str
    content: str
    category: str
    category_name: str
    published_date: Optional[str]
    images: List[str]
    crawled_at: str
    content_hash: str = ""
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.md5(self.content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ScraperState:
    """Tracks scraper state for incremental crawling."""
    last_crawl: str = ""
    crawled_urls: Set[str] = field(default_factory=set)
    content_hashes: Dict[str, str] = field(default_factory=dict)  # url -> hash
    
    def save(self, path: str):
        data = {
            "last_crawl": self.last_crawl,
            "crawled_urls": list(self.crawled_urls),
            "content_hashes": self.content_hashes,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, path: str) -> 'ScraperState':
        if not os.path.exists(path):
            return cls()
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(
            last_crawl=data.get("last_crawl", ""),
            crawled_urls=set(data.get("crawled_urls", [])),
            content_hashes=data.get("content_hashes", {}),
        )
    
    def reset(self):
        """Reset state for full refresh."""
        self.last_crawl = ""
        self.crawled_urls = set()
        self.content_hashes = {}


# ============================================================================
# SCRAPER CLASS
# ============================================================================

class SICTAdvancedScraper:
    """
    Advanced web scraper for sict.haui.edu.vn with:
    - Category-based crawling
    - Smart pagination
    - Incremental updates
    - Parallel processing
    - Retry mechanism
    """
    
    def __init__(self, config: ScraperConfig = None):
        self.config = config or ScraperConfig()
        self.session = self._create_session()
        self.state = ScraperState.load(self.config.state_path)
        self.articles: List[Article] = []
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "articles_found": 0,
            "articles_skipped_date": 0,
            "articles_skipped_duplicate": 0,
        }
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with default headers."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        })
        return session
    
    def _request_with_retry(self, url: str) -> Optional[requests.Response]:
        """Make a request with retry logic."""
        for attempt in range(self.config.max_retries):
            try:
                self.stats["total_requests"] += 1
                response = self.session.get(
                    url, 
                    timeout=self.config.request_timeout
                )
                response.raise_for_status()
                self.stats["successful_requests"] += 1
                time.sleep(self.config.delay_between_requests)
                return response
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {url} - {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    self.stats["failed_requests"] += 1
                    logger.error(f"Max retries reached for: {url}")
        return None
    
    def _parse_date(self, text: str) -> Optional[datetime]:
        """Parse Vietnamese date formats."""
        if not text:
            return None
        
        # Common patterns
        patterns = [
            (r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', 'dmy'),
            (r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', 'ymd'),
            (r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})', 'vn'),
            (r'(\d{1,2})\s+tháng\s+(\d{1,2}),?\s+(\d{4})', 'vn'),
        ]
        
        for pattern, fmt in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if fmt == 'dmy':
                        return datetime(int(groups[2]), int(groups[1]), int(groups[0]))
                    elif fmt == 'ymd':
                        return datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                    elif fmt == 'vn':
                        return datetime(int(groups[2]), int(groups[1]), int(groups[0]))
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_date_from_element(self, element) -> Optional[datetime]:
        """Extract date from common HTML elements."""
        if not element:
            return None
        
        # Try various date selectors
        date_selectors = [
            '.date', '.post-date', '.news-date', '.time', '.created',
            '[class*="date"]', '[class*="time"]', 'time', '.meta'
        ]
        
        for selector in date_selectors:
            date_el = element.select_one(selector)
            if date_el:
                date = self._parse_date(date_el.get_text())
                if date:
                    return date
        
        # Try finding date in text content
        text = element.get_text()
        return self._parse_date(text)
    
    def _get_article_links_from_list_page(self, soup: BeautifulSoup) -> List[Tuple[str, Optional[datetime]]]:
        """Extract article links and dates from a list page."""
        articles = []
        
        # Common article container selectors
        article_selectors = [
            '.news-item', '.post-item', '.article-item', '.item',
            '.list-item', '.entry', 'article', '.box-news-item',
            '.news-list li', '.post-list li', 'ul.news li'
        ]
        
        for selector in article_selectors:
            items = soup.select(selector)
            if items:
                for item in items:
                    link = item.select_one('a[href]')
                    if link:
                        href = link.get('href', '')
                        if href and not href.startswith(('#', 'javascript:')):
                            url = urljoin(self.config.base_url, href)
                            date = self._extract_date_from_element(item)
                            articles.append((url, date))
                break
        
        # Fallback: find all links
        if not articles:
            for link in soup.select('a[href*="/vn/"]'):
                href = link.get('href', '')
                if '/vn/' in href and len(href) > 20:  # Likely an article
                    url = urljoin(self.config.base_url, href)
                    articles.append((url, None))
        
        return articles
    
    def _scrape_article_content(self, url: str, category: str, category_name: str) -> Optional[Article]:
        """Scrape full article content."""
        response = self._request_with_retry(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for el in soup.select('script, style, nav, footer, .sidebar, .menu, .comment'):
            el.decompose()
        
        # Extract title
        title = ""
        title_selectors = ['h1', '.title', '.post-title', '.news-title', '.entry-title']
        for sel in title_selectors:
            el = soup.select_one(sel)
            if el:
                title = el.get_text(strip=True)
                break
        if not title:
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else "Không có tiêu đề"
        
        # Extract content
        content = ""
        content_selectors = [
            '.content', '.post-content', '.article-content', '.entry-content',
            '.news-content', '.detail-content', 'article', '.main-content'
        ]
        for sel in content_selectors:
            el = soup.select_one(sel)
            if el:
                content = el.get_text(separator='\n', strip=True)
                break
        if not content:
            main = soup.find('main') or soup.find('body')
            content = main.get_text(separator='\n', strip=True) if main else ""
        
        # Extract summary (first paragraph or meta description)
        summary = ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            summary = meta_desc.get('content', '')[:300]
        if not summary and content:
            summary = content[:300] + "..."
        
        # Extract images
        images = []
        for img in soup.select('.content img, .post-content img, article img'):
            src = img.get('src', '')
            if src:
                images.append(urljoin(self.config.base_url, src))
        
        # Extract date
        date = self._extract_date_from_element(soup)
        date_str = date.strftime('%Y-%m-%d') if date else None
        
        # Generate ID from URL
        url_path = urlparse(url).path
        article_id = hashlib.md5(url_path.encode()).hexdigest()[:12]
        
        return Article(
            id=article_id,
            url=url,
            title=title,
            summary=summary,
            content=content,
            category=category,
            category_name=category_name,
            published_date=date_str,
            images=images[:5],  # Limit images
            crawled_at=datetime.now().isoformat(),
        )
    
    def _crawl_paginated_category(self, cat_key: str, cat_config: CategoryConfig) -> List[Article]:
        """Crawl a paginated category with smart date filtering."""
        articles = []
        consecutive_old = 0
        page = 1
        
        logger.info(f"📂 Crawling category: {cat_config.name} ({cat_key})")
        
        while page <= self.config.max_pages_per_category:
            # Build page URL
            if page == 1:
                page_url = urljoin(self.config.base_url, cat_config.url)
            else:
                # Pagination pattern: /vn/tin-tuc/2, /vn/tin-tuc/3, etc.
                page_url = urljoin(self.config.base_url, f"{cat_config.url}/{page}")
            
            logger.debug(f"  📄 Page {page}: {page_url}")
            
            response = self._request_with_retry(page_url)
            if not response:
                break
            
            soup = BeautifulSoup(response.text, 'html.parser')
            article_links = self._get_article_links_from_list_page(soup)
            
            if not article_links:
                logger.info(f"  ⏹️ No more articles found at page {page}")
                break
            
            for url, quick_date in article_links:
                # Skip if already crawled
                if url in self.state.crawled_urls:
                    self.stats["articles_skipped_duplicate"] += 1
                    continue
                
                # Quick date check from list page
                if quick_date and cat_config.date_required:
                    if quick_date < self.config.start_date:
                        consecutive_old += 1
                        self.stats["articles_skipped_date"] += 1
                        if consecutive_old >= self.config.consecutive_old_threshold:
                            logger.info(f"  ⏭️ {consecutive_old} consecutive old articles, stopping category")
                            return articles
                        continue
                    else:
                        consecutive_old = 0  # Reset
                
                # Scrape full article
                article = self._scrape_article_content(url, cat_key, cat_config.name)
                if article:
                    # Final date check from article content
                    if cat_config.date_required and article.published_date:
                        article_date = datetime.strptime(article.published_date, '%Y-%m-%d')
                        if article_date < self.config.start_date:
                            consecutive_old += 1
                            self.stats["articles_skipped_date"] += 1
                            if consecutive_old >= self.config.consecutive_old_threshold:
                                logger.info(f"  ⏭️ {consecutive_old} consecutive old articles, stopping")
                                return articles
                            continue
                        else:
                            consecutive_old = 0
                    
                    articles.append(article)
                    self.state.crawled_urls.add(url)
                    self.stats["articles_found"] += 1
                    logger.info(f"  ✅ {article.title[:50]}...")
            
            page += 1
        
        return articles
    
    def _crawl_static_category(self, cat_key: str, cat_config: CategoryConfig) -> List[Article]:
        """Crawl static pages (no pagination, no date filter)."""
        articles = []
        urls_to_crawl = [cat_config.url] + cat_config.sub_urls
        
        logger.info(f"📚 Crawling static category: {cat_config.name} ({len(urls_to_crawl)} pages)")
        
        for url_path in urls_to_crawl:
            url = urljoin(self.config.base_url, url_path)
            
            if url in self.state.crawled_urls:
                # Check if content changed
                response = self._request_with_retry(url)
                if response:
                    new_hash = hashlib.md5(response.text.encode()).hexdigest()[:16]
                    if self.state.content_hashes.get(url) == new_hash:
                        logger.debug(f"  ⏭️ No changes: {url_path}")
                        self.stats["articles_skipped_duplicate"] += 1
                        continue
            
            article = self._scrape_article_content(url, cat_key, cat_config.name)
            if article and len(article.content) > 100:  # Filter empty pages
                articles.append(article)
                self.state.crawled_urls.add(url)
                self.state.content_hashes[url] = article.content_hash
                self.stats["articles_found"] += 1
                logger.info(f"  ✅ {article.title[:50]}...")
        
        return articles
    
    def crawl_category(self, cat_key: str) -> List[Article]:
        """Crawl a single category."""
        cat_config = SITE_STRUCTURE.get(cat_key)
        if not cat_config:
            logger.error(f"Unknown category: {cat_key}")
            return []
        
        if cat_config.category_type == "paginated":
            return self._crawl_paginated_category(cat_key, cat_config)
        else:
            return self._crawl_static_category(cat_key, cat_config)
    
    def crawl_all(self, parallel: bool = True) -> List[Article]:
        """
        Crawl all categories.
        
        Args:
            parallel: Use parallel processing for categories
        """
        logger.info("=" * 60)
        logger.info("🕷️ SICT HaUI Advanced Scraper v2.0")
        logger.info(f"📅 Date filter: >= {self.config.start_date.strftime('%Y-%m-%d')}")
        logger.info(f"🔗 Base URL: {self.config.base_url}")
        logger.info("=" * 60)
        
        all_articles = []
        
        # Sort categories by priority
        sorted_categories = sorted(
            SITE_STRUCTURE.items(),
            key=lambda x: x[1].priority
        )
        
        if parallel and self.config.max_workers > 1:
            # Parallel crawling
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = {
                    executor.submit(self.crawl_category, cat_key): cat_key
                    for cat_key, _ in sorted_categories
                }
                
                for future in as_completed(futures):
                    cat_key = futures[future]
                    try:
                        articles = future.result()
                        all_articles.extend(articles)
                    except Exception as e:
                        logger.error(f"Error crawling {cat_key}: {e}")
        else:
            # Sequential crawling
            for cat_key, _ in sorted_categories:
                try:
                    articles = self.crawl_category(cat_key)
                    all_articles.extend(articles)
                except Exception as e:
                    logger.error(f"Error crawling {cat_key}: {e}")
        
        self.articles = all_articles
        return all_articles
    
    def save_results(self):
        """Save scraped articles and state."""
        # Save articles
        os.makedirs(os.path.dirname(self.config.output_path), exist_ok=True)
        
        articles_data = [a.to_dict() for a in self.articles]
        with open(self.config.output_path, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Saved {len(articles_data)} articles to {self.config.output_path}")
        
        # Save state
        self.state.last_crawl = datetime.now().isoformat()
        self.state.save(self.config.state_path)
        logger.info(f"💾 Saved scraper state to {self.config.state_path}")
    
    def print_stats(self):
        """Print crawling statistics."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 CRAWLING STATISTICS")
        logger.info("=" * 60)
        logger.info(f"  Total requests:          {self.stats['total_requests']}")
        logger.info(f"  Successful requests:     {self.stats['successful_requests']}")
        logger.info(f"  Failed requests:         {self.stats['failed_requests']}")
        logger.info(f"  Articles found:          {self.stats['articles_found']}")
        logger.info(f"  Skipped (date filter):   {self.stats['articles_skipped_date']}")
        logger.info(f"  Skipped (duplicate):     {self.stats['articles_skipped_duplicate']}")
        logger.info("=" * 60)
        
        # Category breakdown
        category_counts = {}
        for article in self.articles:
            cat = article.category_name
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        logger.info("\n📂 BY CATEGORY:")
        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {cat}: {count}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    config = ScraperConfig(
        start_date=datetime(2025, 9, 1),
        output_path="data/sict_haui_data.json",
        max_workers=3,  # Parallel categories
    )
    
    scraper = SICTAdvancedScraper(config)
    
    # Crawl all categories
    scraper.crawl_all(parallel=True)
    
    # Save results
    scraper.save_results()
    
    # Print statistics
    scraper.print_stats()


if __name__ == "__main__":
    main()

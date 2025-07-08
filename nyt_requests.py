#!/usr/bin/env python3
"""
NYT Morning Briefing RSS Feed Generator using requests (no Selenium required)

This version is much simpler and faster since NYT serves the content statically.
"""

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
from zoneinfo import ZoneInfo
import logging
import sys
import re
from typing import Optional, List, Dict, Any
import dateutil.parser
from urllib.parse import urljoin

# New York timezone
NY_TZ = ZoneInfo("America/New_York")

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Back to INFO level for cleaner output
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('nyt_scraper_requests.log')
    ]
)
logger = logging.getLogger(__name__)


class NYTRequestsScraper:
    """Efficient NYT Morning Briefing RSS feed generator using requests only."""
    
    def __init__(self, timeout: int = 30, max_articles: int = 20):
        self.base_url = "https://www.nytimes.com"
        self.url = "https://www.nytimes.com/series/us-morning-briefing"
        self.timeout = timeout
        self.max_articles = max_articles
        self.session: Optional[requests.Session] = None
        
    def _setup_session(self) -> requests.Session:
        """Set up requests session with appropriate headers."""
        session = requests.Session()
        
        # Headers to mimic a real browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        return session
    
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage."""
        if not self.session:
            logger.error("Session not initialized")
            return None
            
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info(f"Successfully fetched {len(response.content)} bytes")
            return soup
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None
    
    def _extract_articles_from_soup(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract article information from the parsed HTML."""
        articles = []
        
        # Try different selectors for articles
        # Based on the webpage content, articles appear to be in a simple structure
        article_links = soup.find_all('a', href=re.compile(r'/\d{4}/\d{2}/\d{2}/briefing/'))
        
        logger.info(f"Found {len(article_links)} article links")
        
        for link in article_links[:self.max_articles]:
            try:
                article_data = self._extract_article_data(link, soup)
                if article_data:
                    articles.append(article_data)
            except Exception as e:
                logger.warning(f"Error extracting article data: {e}")
                continue
                
        logger.info(f"Successfully extracted {len(articles)} articles")
        return articles
    
    def _extract_article_data(self, link_element, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract data from a single article link."""
        try:
            # Get the URL
            href = link_element.get('href')
            if not href:
                return None
                
            # Make sure it's a full URL
            full_url = urljoin(self.base_url, href)
            
            # Get the title - it should be the text of the link
            title = link_element.get_text(strip=True)
            if not title:
                return None
            
            # Look for description/summary near the link
            description = self._find_article_description(link_element)
            
            # Extract author from description  
            clean_description, author = self._extract_author_and_clean_description(description)
            
            # Extract image from article container
            image_url = self._find_article_image(link_element)
            
            # Extract date from URL or nearby elements
            pub_date = self._extract_article_date(link_element, href)
            
            return {
                'url': full_url,
                'title': title,
                'description': clean_description,  # Use cleaned description
                'author': author,
                'image_url': image_url,
                'pub_date': pub_date
            }
            
        except Exception as e:
            logger.warning(f"Error extracting article data: {e}")
            return None
    
    def _extract_author_and_clean_description(self, description: str) -> tuple[str, str]:
        """Extract author information and return clean description and author name."""
        if not description:
            return description, ""
            
        import re
        
        # Extract author from "By | Author Name" patterns (NYT Morning Briefing format)
        author = ""
        
        # Look for "By | Author Name" pattern (with separator)
        author_match = re.search(r'By\s*\|\s*([^|]+?)(?:\s*\||$)', description, flags=re.IGNORECASE)
        if author_match:
            author = author_match.group(1).strip()
        
        # If not found, look for simpler "By Author Name" patterns
        if not author:
            author_match = re.search(r'By\s+([A-Za-z\s,\.]+?)(?:\s*\||$)', description, flags=re.IGNORECASE)
            if author_match:
                author = author_match.group(1).strip()
        
        # Clean description by removing author bylines and separators
        clean_description = re.sub(r'\s*\|\s*By\s*\|\s*[^|]+(\s*\|[^|]*)*$', '', description, flags=re.IGNORECASE)
        clean_description = re.sub(r'\s*By\s*\|\s*[^|]+(\s*\|[^|]*)*$', '', clean_description, flags=re.IGNORECASE)
        clean_description = re.sub(r'\s*\|\s*By\s+[^|]+(\s*\|[^|]*)*$', '', clean_description, flags=re.IGNORECASE)
        clean_description = re.sub(r'\s*By\s+[A-Za-z\s,\.]+$', '', clean_description, flags=re.IGNORECASE)
        
        # Clean up extra separators and whitespace
        clean_description = re.sub(r'\s*\|\s*$', '', clean_description)
        clean_description = ' '.join(clean_description.split()).strip()
        
        # Convert author to title case if found
        if author:
            author = author.title()
        
        return clean_description, author
    
    def _find_article_description(self, link_element) -> str:
        """Find the description/summary for an article, including author information."""
        try:
            # Find the article container (could be article, div, section, etc.)
            article_container = link_element
            for level in range(5):  # Search up to 5 levels up
                if article_container.parent:
                    article_container = article_container.parent
                    # Look for typical article container tags
                    if article_container.name in ['article', 'section']:
                        break
            
            # Get all text using separator to preserve structure
            full_text = article_container.get_text(separator=' | ', strip=True)
            title = link_element.get_text(strip=True)
            
            # Remove the title from the beginning
            if full_text.startswith(title):
                remaining_text = full_text[len(title):].strip()
                if remaining_text.startswith('|'):
                    remaining_text = remaining_text[1:].strip()
                return remaining_text[:1000]  # This should include description + "By | Author"
            
            # Fallback: get all text elements
            all_texts = []
            for elem in article_container.find_all(['span', 'p', 'div'], recursive=True):
                text = elem.get_text(strip=True)
                if text and len(text) > 2 and text != title:
                    all_texts.append(text)
            
            if all_texts:
                return ' '.join(all_texts)[:1000]
                        
        except Exception as e:
            logger.debug(f"Error finding description: {e}")
            
        return "Morning briefing article from The New York Times"
    
    def _extract_article_date(self, link_element, href: str) -> Optional[datetime.datetime]:
        """Extract publication date from URL or nearby elements."""
        try:
            # First try to extract date from URL pattern: /2025/07/08/briefing/
            date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', href)
            if date_match:
                year, month, day = date_match.groups()
                # Create datetime in NY timezone, set to midnight for date-only format
                return datetime.datetime(int(year), int(month), int(day), 6, 30, 0, tzinfo=NY_TZ)
            
            # Try to find date text near the link
            parent = link_element.parent
            if parent:
                # Look for date patterns in the text
                text = parent.get_text()
                date_patterns = [
                    r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
                    r'\d{1,2}/\d{1,2}/\d{4}',
                    r'\d{4}-\d{2}-\d{2}'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, text)
                    if match:
                        try:
                            # Parse, set to midnight, and set timezone
                            parsed_date = dateutil.parser.parse(match.group())
                            return parsed_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=NY_TZ)
                        except Exception:
                            continue
            
            # Default to today at midnight if no date found
            today = datetime.datetime.now(NY_TZ)
            return today.replace(hour=0, minute=0, second=0, microsecond=0)
            
        except Exception as e:
            logger.debug(f"Error extracting date: {e}")
            today = datetime.datetime.now(NY_TZ)
            return today.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def generate_rss(self) -> bytes:
        """Generate RSS feed."""
        try:
            # Setup session
            self.session = self._setup_session()
            
            # Fetch the main page
            soup = self._fetch_page(self.url)
            if not soup:
                return self._generate_error_feed("Failed to fetch main page")
            
            # Extract articles
            articles = self._extract_articles_from_soup(soup)
            if not articles:
                return self._generate_error_feed("No articles found")
            
            # Extract favicon from the page
            favicon_url = self._find_favicon(soup)
            if favicon_url:
                logger.info(f"Found favicon: {favicon_url}")
            else:
                logger.info("No favicon found, RSS will not include channel image")
            
            # Generate RSS feed
            return self._build_rss_feed(articles, favicon_url)
            
        except Exception as e:
            logger.error(f"Error generating RSS: {e}")
            return self._generate_error_feed(f"Error: {e}")
        finally:
            if self.session:
                self.session.close()

    def _build_rss_feed(self, articles: List[Dict[str, Any]], favicon_url: Optional[str] = None) -> bytes:
        """Build RSS feed from article data."""
        fg = FeedGenerator()
        fg.title('NYT US Morning Briefing (Unofficial RSS Feed)')
        fg.link(href=self.url, rel='alternate')
        fg.description('RSS feed for The New York Times US Morning Briefing series')
        fg.language('en')
        fg.managingEditor('morningbriefing@nytimes.com (The New York Times Morning Briefing Team)')
        
        # Add RSS channel image (NYT favicon/icon) if available
        if favicon_url:
            try:
                fg.image(
                    url=favicon_url,
                    title='The New York Times',
                    link=self.base_url,
                    width='144',
                    height='144'
                )
            except Exception as e:
                logger.debug(f"Error adding favicon to RSS: {e}")
        
        fg.pubDate(datetime.datetime.now(NY_TZ))
        
        logger.info(f"Building RSS feed with {len(articles)} articles")
        
        for i, article in enumerate(articles):
            try:
                fe = fg.add_entry()
                fe.id(article['url'])
                fe.guid(article['url'], permalink=True)  # Explicitly set as permalink
                fe.title(article['title'])
                fe.link(href=article['url'], rel='alternate')
                
                # Enhance description with image if available
                description = article['description']
                if article.get('image_url'):
                    # Add image to description as HTML
                    description = f'<img src="{article["image_url"]}" alt="" style="max-width: 100%; height: auto;"><br><br>{description}'
                
                fe.description(description)
                
                # Add image as enclosure for RSS readers that support it
                if article.get('image_url'):
                    try:
                        fe.enclosure(article['image_url'], type='image/jpeg')
                    except Exception:
                        pass  # Some RSS readers don't support enclosures
                
                # Add author information if available
                if article.get('author'):
                    # Use generic NYT email since we don't have real author emails
                    try:
                        # Use a generic morningbriefing email with author name
                        fe.author(f"morningbriefing@nytimes.com ({article['author']})")
                    except Exception:
                        # Fallback: add author to description
                        fe.description(f"{description} (by {article['author']})")
                
                # Set publication date
                if article['pub_date']:
                    fe.published(article['pub_date'])
                    fe.pubDate(article['pub_date'])
                else:
                    current_time = datetime.datetime.now(NY_TZ)
                    fe.published(current_time)
                    fe.pubDate(current_time)
                    
            except Exception as e:
                logger.warning(f"Error adding article {i+1} to feed: {e}")
                continue
        
        # Generate RSS XML
        return fg.rss_str(pretty=True)
    
    def _generate_error_feed(self, error_message: str) -> bytes:
        """Generate an error RSS feed."""
        fg = FeedGenerator()
        fg.title('NYT US Morning Briefing - Error')
        fg.link(href=self.url, rel='alternate')
        fg.description(f'Error generating feed: {error_message}')
        fg.language('en')
        fg.pubDate(datetime.datetime.now(NY_TZ))
        
        fe = fg.add_entry()
        fe.id(self.url)
        fe.title('Error generating feed')
        fe.link(href=self.url, rel='alternate')
        fe.description(error_message)
        fe.published(datetime.datetime.now(NY_TZ))
        fe.pubDate(datetime.datetime.now(NY_TZ))
        
        return fg.rss_str(pretty=True)
    
    def _find_article_image(self, link_element) -> str:
        """Find the main image for an article."""
        try:
            # Find the article container (could be article, div, section, etc.)
            article_container = link_element
            for level in range(5):  # Search up to 5 levels up
                if article_container.parent:
                    article_container = article_container.parent
                    # Look for typical article container tags
                    if article_container.name in ['article', 'section']:
                        break
            
            # Look for images in the article container
            images = article_container.find_all('img')
            
            # Filter out very small images (likely icons, not article images)
            main_images = []
            for img in images:
                src = img.get('src', '')
                # Skip if it looks like an icon or very small image
                if any(skip in src.lower() for skip in ['icon', 'logo', 'favicon', 'avatar']):
                    continue
                # Check for width/height attributes to filter out small images
                width = img.get('width')
                height = img.get('height')
                if width and height:
                    try:
                        if int(width) < 100 or int(height) < 100:
                            continue
                    except ValueError:
                        pass
                main_images.append(img)
            
            if main_images:
                # Get the first (usually main) image
                img = main_images[0]
                src = img.get('src')
                if src:
                    # Make sure it's a full URL
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = self.base_url + src
                    elif not src.startswith('http'):
                        src = self.base_url + '/' + src
                    
                    # Store original src for fallback
                    original_src = src
                    
                    # Try to get a higher quality version if available
                    upgraded_src = self._upgrade_image_quality(src)
                    
                    # Verify the upgraded image exists, fallback to original if not
                    if upgraded_src != original_src:
                        if self._verify_image_url(upgraded_src):
                            return upgraded_src
                        else:
                            logger.debug(f"Upgraded image URL failed, using original: {original_src}")
                            return original_src
                    else:
                        return src
                    
        except Exception as e:
            logger.debug(f"Error finding image: {e}")
            
        return ""
    
    def _verify_image_url(self, url: str) -> bool:
        """Verify if an image URL is accessible."""
        try:
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _upgrade_image_quality(self, src: str) -> str:
        """Try to upgrade image URL to higher quality version."""
        try:
            # Common NYT image size patterns to upgrade
            upgrades = {
                'square320': 'articleLarge',
                'square640': 'articleLarge', 
                'mediumSquare149': 'articleLarge',
                'moth': 'articleLarge',
                'filmstrip': 'articleLarge',
                'thumbStandard': 'articleLarge',
                'thumbLarge': 'articleLarge'
            }
            
            for old_size, new_size in upgrades.items():
                if old_size in src:
                    return src.replace(old_size, new_size)
            
            # If no specific pattern found, but it's a static01.nyt.com image,
            # try to ensure quality parameters are optimal
            if 'static01.nyt.com' in src:
                # Ensure good quality settings if they exist
                if 'quality=' in src:
                    # Upgrade quality to 75 if it's lower
                    import re
                    src = re.sub(r'quality=(\d+)', lambda m: f'quality={max(75, int(m.group(1)))}', src)
                
            return src
        except Exception as e:
            logger.debug(f"Error upgrading image quality: {e}")
            return src
    
    def _find_favicon(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the best favicon/icon URL from the page."""
        try:
            # Look for various icon types in order of preference
            icon_selectors = [
                # Apple touch icons (usually higher quality)
                'link[rel*="apple-touch-icon"][sizes="144x144"]',
                'link[rel*="apple-touch-icon"][sizes="152x152"]',
                'link[rel*="apple-touch-icon"][sizes="180x180"]',
                'link[rel*="apple-touch-icon"]',
                # Standard favicons
                'link[rel="icon"][type="image/png"]',
                'link[rel="shortcut icon"]',
                'link[rel="icon"]'
            ]
            
            for selector in icon_selectors:
                icon_link = soup.select_one(selector)
                if icon_link and icon_link.get('href'):
                    href = icon_link.get('href')
                    
                    # Ensure href is a string
                    if isinstance(href, list):
                        href = href[0] if href else None
                    if not isinstance(href, str):
                        continue
                    
                    # Convert relative URLs to absolute
                    if href.startswith('//'):
                        return 'https:' + href
                    elif href.startswith('/'):
                        return self.base_url + href
                    elif not href.startswith('http'):
                        return self.base_url + '/' + href
                    else:
                        return href
            
            # Fallback: try common favicon paths
            fallback_paths = [
                '/favicon.ico',
                '/apple-touch-icon.png',
                '/apple-touch-icon-144x144.png'
            ]
            
            for path in fallback_paths:
                return self.base_url + path
                
        except Exception as e:
            logger.debug(f"Error finding favicon: {e}")
            
        return None

def generate_nytimes_morning_briefing_rss() -> bytes:
    """Main function for backward compatibility."""
    scraper = NYTRequestsScraper()
    return scraper.generate_rss()


if __name__ == '__main__':
    try:
        logger.info("Starting NYT Morning Briefing RSS generation...")
        rss_output = generate_nytimes_morning_briefing_rss()
        
        print(rss_output.decode('utf-8'))
        
        # Save to file
        with open("nytimes_morning_briefing.xml", "w", encoding="utf-8") as f:
            f.write(rss_output.decode('utf-8'))
        
        logger.info("RSS feed generated successfully and saved to nytimes_morning_briefing.xml")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

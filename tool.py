import asyncio
import re
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict
from urllib.parse import urljoin, urlparse
from agno.tools import Toolkit
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.processors.pdf import PDFCrawlerStrategy, PDFContentScrapingStrategy
import aiohttp
import time


class WebCrawlerTool(Toolkit):
    """Simple web crawler tool that returns content and links for agent decision making."""

    def __init__(self, starting_urls: List[str] = None, max_links_per_page: int = 50):
        super().__init__()
        self.starting_urls = starting_urls or []
        self.allowed_domains = self._extract_domains_from_urls(self.starting_urls)
        self.max_links_per_page = max_links_per_page
        self.register(self.crawl_selected_urls)
        self.register(self.process_pdf_urls)

    def _extract_domains_from_urls(self, urls: List[str]) -> List[str]:
        """Extract unique domains from a list of URLs."""
        domains = []
        for url in urls:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                if domain and domain not in domains:
                    domains.append(domain)
            except:
                continue
        return domains

    def is_allowed_domain(self, url: str) -> bool:
        """Check if URL is within allowed domains."""
        if not self.allowed_domains:
            return True

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return any(
                allowed_domain.lower() in domain
                for allowed_domain in self.allowed_domains
            )
        except:
            return False

    def _ensure_valid_url(self, url: str) -> str:
        """Ensure URL has proper protocol."""
        url = url.strip()
        if not url:
            return None

        # Handle protocol-relative URLs
        if url.startswith("//"):
            return f"https:{url}"

        # Add https if no protocol
        if not url.startswith(("http://", "https://", "file://")):
            return f"https://{url}"

        return url

    def _get_root_domain(self, url: str) -> str:
        """Extract root domain from any URL for discovery files."""
        try:
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}"
        except:
            return url

    async def discover_urls_from_sources(
        self, input_url: str, bypass_cache: bool = False
    ) -> Dict[str, str]:
        """
        Five-step discovery with enhanced sitemap support:
        1. llms.txt content
        2. sitemap.xml URLs (with recursive fetching)
        3. sitemap/sitemap.xml URLs (with recursive fetching)
        4. sitemap_index.xml URLs (with recursive fetching)
        5. base page content (fallback)
        """
        root_domain = self._get_root_domain(input_url)
        print(f"🔍 Discovering content from: {root_domain}")

        sources = {
            "llms_txt_content": "",
            "sitemap_urls": [],
            "base_page_content": "",
        }

        try:
            # Step 1: Always try llms.txt first
            llms_content = await self._get_content_from_llms_txt(
                f"{root_domain}/llms.txt"
            )
            if llms_content:
                sources["llms_txt_content"] = llms_content
                print(f"✅ Found llms.txt content ({len(llms_content)} chars)")

            # Step 2: Try sitemap.xml (with recursive fetching)
            print(f"🔍 Checking sitemap.xml with recursive fetching...")
            sitemap_urls = await self._get_urls_from_sitemap(
                f"{root_domain}/sitemap.xml"
            )

            # Step 3: If both fail, try sitemap_index.xml (with recursive fetching)
            if not sitemap_urls:
                print(
                    f"🔍 sitemap/sitemap.xml failed, trying sitemap_index.xml with recursive fetching..."
                )
                sitemap_urls = await self._get_urls_from_sitemap(
                    f"{root_domain}/sitemap_index.xml"
                )

            # Step 4: If sitemap.xml fails, try sitemap/sitemap.xml (with recursive fetching)
            if not sitemap_urls:
                print(
                    f"🔍 sitemap.xml failed, trying sitemap/sitemap.xml with recursive fetching..."
                )
                sitemap_urls = await self._get_urls_from_sitemap(
                    f"{root_domain}/sitemap/sitemap.xml"
                )

            if sitemap_urls:
                sources["sitemap_urls"] = sitemap_urls
                print(
                    f"✅ Found {len(sitemap_urls)} URLs from sitemap discovery (including recursive)"
                )

            # Step 5: Fallback to base page content (only if no sitemap URLs found)
            if not sources["sitemap_urls"]:
                print(
                    f"📄 No sitemap URLs found, falling back to base page content... ({'FRESH' if bypass_cache else 'CACHED'})"
                )
                try:
                    _, content, _ = await self.crawl_single_url(input_url, bypass_cache)
                    if content:
                        sources["base_page_content"] = content
                        print(
                            f"✅ Found {len(content)} characters of content from base page crawl"
                        )
                    else:
                        print("⚠️ No content found on base page")
                except Exception as e:
                    print(f"⚠️ Base page crawling failed: {e}")

        except Exception as e:
            print(f"⚠️ Discovery error: {e}")

        return sources

    async def _get_content_from_llms_txt(self, llms_url: str) -> str:
        """Get full content from llms.txt file."""
        try:
            print(f"🔍 Checking llms.txt at: {llms_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(llms_url, timeout=10) as response:
                    print(f"📄 llms.txt response status: {response.status}")

                    if response.status == 200:
                        content = await response.text()
                        print(f"📄 llms.txt content length: {len(content)} chars")
                        print(f"📄 llms.txt content preview: {content[:200]}...")

                        # Return the full content instead of parsing for URLs
                        print(
                            f"✅ Retrieved full llms.txt content ({len(content)} characters)"
                        )
                        return content.strip()
                    else:
                        print(f"❌ llms.txt not found (status {response.status})")

        except Exception as e:
            print(f"❌ llms.txt parsing error: {e}")
            import traceback

            print(f"❌ Full traceback: {traceback.format_exc()}")

        return ""

    async def _fetch_sitemap_content(self, sitemap_url: str) -> str:
        """
        Fetch sitemap content with proper error handling.
        Returns empty string on failure (not exception).
        """
        try:
            print(f"🔍 Fetching sitemap: {sitemap_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(sitemap_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        print(f"✅ Sitemap fetched successfully ({len(content)} chars)")
                        return content
                    else:
                        print(f"❌ Sitemap {sitemap_url} returned {response.status}")
                        return ""
        except Exception as e:
            print(f"❌ Failed to fetch sitemap {sitemap_url}: {e}")
            return ""

    def _parse_sitemap_xml(
        self, xml_content: str, base_url: str
    ) -> Dict[str, List[str]]:
        """
        Parse XML and determine if it's:
        - Regular sitemap (has <url> elements)
        - Sitemap index (has <sitemap> elements)
        """
        try:
            time.sleep(1)
            root = ET.fromstring(xml_content)

            # Remove namespace for easier parsing
            for elem in root.iter():
                if "}" in elem.tag:
                    elem.tag = elem.tag.split("}")[1]

            page_urls = []
            sitemap_urls = []

            # Check for regular sitemap structure
            for url_elem in root.findall(".//url"):
                loc_elem = url_elem.find("loc")
                if loc_elem is not None and loc_elem.text:
                    full_url = urljoin(base_url, loc_elem.text.strip())
                    if self.is_allowed_domain(full_url):
                        page_urls.append(full_url)

            # Check for sitemap index structure
            for sitemap_elem in root.findall(".//sitemap"):
                loc_elem = sitemap_elem.find("loc")
                if loc_elem is not None and loc_elem.text:
                    full_url = urljoin(base_url, loc_elem.text.strip())
                    if self.is_allowed_domain(full_url):
                        sitemap_urls.append(full_url)

            print(
                f"📋 Parsed XML: {len(page_urls)} page URLs, {len(sitemap_urls)} nested sitemaps"
            )
            return {"page_urls": page_urls, "sitemap_urls": sitemap_urls}

        except ET.ParseError as e:
            print(f"❌ XML parsing error: {e}")
            return {"page_urls": [], "sitemap_urls": []}

    async def _fetch_recursive_sitemaps(
        self, sitemap_urls: List[str], depth: int = 0, max_depth: int = 3
    ) -> List[str]:
        """
        Recursively fetch all nested sitemaps and extract URLs.

        Args:
            sitemap_urls: List of sitemap URLs to fetch
            depth: Current recursion depth
            max_depth: Maximum recursion depth to prevent infinite loops

        Returns:
            List of all page URLs found in all nested sitemaps
        """
        if depth >= max_depth:
            print(
                f"⚠️ Maximum recursion depth ({max_depth}) reached, stopping sitemap fetching"
            )
            return []

        all_urls = []

        # Fetch all sitemaps concurrently (with limit)
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests

        async def fetch_single_sitemap(sitemap_url: str) -> List[str]:
            async with semaphore:
                try:
                    # Fetch sitemap content
                    sitemap_content = await self._fetch_sitemap_content(sitemap_url)
                    if not sitemap_content:
                        return []

                    # Parse the nested sitemap
                    parsed_data = self._parse_sitemap_xml(sitemap_content, sitemap_url)

                    urls_from_this_sitemap = []

                    # Add page URLs from this sitemap
                    urls_from_this_sitemap.extend(parsed_data["page_urls"])

                    # If this sitemap also has nested sitemaps, fetch them recursively
                    if parsed_data["sitemap_urls"]:
                        print(
                            f"🔄 Sitemap {sitemap_url} has {len(parsed_data['sitemap_urls'])} more nested sitemaps"
                        )
                        deeper_urls = await self._fetch_recursive_sitemaps(
                            parsed_data["sitemap_urls"], depth + 1, max_depth
                        )
                        urls_from_this_sitemap.extend(deeper_urls)

                    return urls_from_this_sitemap

                except Exception as e:
                    print(f"❌ Failed to fetch nested sitemap {sitemap_url}: {e}")
                    return []

        # Fetch all sitemaps concurrently
        tasks = [fetch_single_sitemap(url) for url in sitemap_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        for result in results:
            if isinstance(result, list):
                all_urls.extend(result)
            else:
                print(f"⚠️ Sitemap fetch returned exception: {result}")

        # Remove duplicates while preserving order
        unique_urls = list(dict.fromkeys(all_urls))

        print(
            f"📊 Recursive sitemap fetching (depth {depth}) found {len(unique_urls)} unique URLs"
        )
        return unique_urls

    async def _get_urls_from_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Process any sitemap with automatic recursive fetching.
        """
        try:
            # Fetch the initial sitemap
            sitemap_content = await self._fetch_sitemap_content(sitemap_url)
            if not sitemap_content:
                return []

            # Parse XML to get both page URLs and nested sitemap URLs
            parsed_data = self._parse_sitemap_xml(sitemap_content, sitemap_url)

            all_urls = []

            # Add direct page URLs (if any)
            all_urls.extend(parsed_data["page_urls"])

            # If there are nested sitemaps, fetch them recursively
            if parsed_data["sitemap_urls"]:
                print(
                    f"🔄 Found {len(parsed_data['sitemap_urls'])} nested sitemaps in {sitemap_url}"
                )
                nested_urls = await self._fetch_recursive_sitemaps(
                    parsed_data["sitemap_urls"]
                )
                all_urls.extend(nested_urls)

            # Remove duplicates
            unique_urls = list(dict.fromkeys(all_urls))

            return unique_urls

        except Exception as e:
            print(f"❌ Failed to process sitemap {sitemap_url}: {e}")
            return []

    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """Extract all links from HTML content and filter by allowed domains."""
        links = []

        # Find all href attributes
        href_pattern = r'href=["\']([^"\']+)["\']'
        matches = re.findall(href_pattern, html_content, re.IGNORECASE)

        for href in matches:
            try:
                # Convert relative URLs to absolute
                full_url = urljoin(base_url, href)

                # Basic URL cleaning
                full_url = full_url.split("#")[0]  # Remove anchors
                full_url = full_url.rstrip("/")  # Remove trailing slash

                # Check if it's a valid HTTP/HTTPS URL
                if full_url.startswith(
                    ("http://", "https://")
                ) and self.is_allowed_domain(full_url):
                    links.append(full_url)

            except Exception:
                continue

        # Remove duplicates and limit
        unique_links = list(dict.fromkeys(links))
        return unique_links

    def _get_optimized_browser_config(self) -> BrowserConfig:
        """Get optimized browser configuration for maximum performance."""
        return BrowserConfig(
            headless=True,  # Always headless for production
            text_mode=True,  # Disable images/heavy content
            light_mode=True,  # Disable background features
            java_script_enabled=True,  # Keep JS enabled but optimize
            extra_args=[
                "--disable-extensions",  # Disable browser extensions
                "--disable-plugins",  # Disable plugins
                "--disable-images",  # Skip image loading
                "--no-sandbox",  # Better performance in containers
                "--disable-dev-shm-usage",  # Better memory management
                "--disable-background-networking",  # Reduce background activity
                "--disable-background-timer-throttling",  # Better performance
                "--disable-renderer-backgrounding",  # Prevent throttling
                "--disable-backgrounding-occluded-windows",  # Performance
                "--disable-features=TranslateUI",  # Skip translation
                "--disable-ipc-flooding-protection",  # Performance
                "--disable-web-security",  # Speed up requests
                "--aggressive-cache-discard",  # Better memory management
            ],
        )

    def _get_optimized_crawler_config(
        self, bypass_cache: bool = False
    ) -> CrawlerRunConfig:
        """Get optimized crawler configuration for maximum performance."""
        cache_mode = CacheMode.BYPASS if bypass_cache else CacheMode.ENABLED

        return CrawlerRunConfig(
            cache_mode=cache_mode,
            wait_until="commit",  # Fastest wait strategy (vs "load")
            delay_before_return_html=0,  # Zero delay for maximum speed
            word_count_threshold=1,  # Lower threshold for faster processing
            process_iframes=False,  # Skip iframe processing
            remove_overlay_elements=True,  # Remove popups/modals quickly
            # excluded_tags=["script", "style", "nav", "header", "footer", "aside"],  # Skip non-content
            only_text=False,  # Keep some structure for links
            ignore_body_visibility=True,  # Skip visibility checks
            # excluded_selector="#ads, .advertisement, .social-media, .sidebar",  # Skip common clutter
            simulate_user=False,  # Skip user simulation for speed
            override_navigator=False,  # Skip navigator override
        )

    async def crawl_single_url(
        self, url: str, bypass_cache: bool = False
    ) -> Tuple[str, str, List[str]]:
        """Crawl a single URL with optimized performance configuration."""
        start_time = time.time()

        try:
            # Use optimized configurations
            browser_config = self._get_optimized_browser_config()
            crawler_config = self._get_optimized_crawler_config(bypass_cache)

            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=crawler_config)

                if not result or not result.success:
                    return (
                        url,
                        f"Failed to crawl: {result.error_message if result else 'Unknown error'}",
                        [],
                    )

                # Extract content using best available method
                content = self._extract_best_content(result)

                # Extract links from raw HTML
                raw_html = result.html or ""
                links = self.extract_links(raw_html, url)

                crawl_time = time.time() - start_time
                print(
                    f"⚡ Crawled {url} in {crawl_time:.2f}s ({'FRESH' if bypass_cache else 'CACHED'}) - {len(content)} chars"
                )

                return url, content, links

        except Exception as e:
            crawl_time = time.time() - start_time
            print(f"❌ Failed to crawl {url} in {crawl_time:.2f}s: {str(e)}")
            return url, f"Error crawling {url}: {str(e)}", []

    def _extract_best_content(self, result) -> str:
        """Extract the best available content using simple, reliable methods."""
        # Try markdown first (usually cleanest)
        if result.markdown and len(result.markdown.strip()) > 50:
            return result.markdown

        # Fall back to cleaned HTML
        if result.cleaned_html and len(result.cleaned_html.strip()) > 50:
            return result.cleaned_html

        # Last resort: extract text from raw HTML
        if result.html and len(result.html.strip()) > 100:
            text = re.sub(r"<[^>]+>", "", result.html)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 50:
                return text

        return "No content extracted"

    def discover_site_structure(self, urls) -> str:
        """
        Discover available content from llms.txt and base pages for agent decision-making.

        Uses caching for content discovery (since content changes less frequently).

        Args:
            urls: URL(s) to discover content from - can be a single string or list of strings
                 (e.g., "https://docs.example.com" or ["https://site1.com", "https://site2.com"])

        Returns:
            str: Formatted content from all sources (llms.txt content, base page content)
        """
        try:
            # Fix input type handling - ensure urls is always a list
            if isinstance(urls, str):
                urls = [urls]  # Convert single string to list
            elif not isinstance(urls, (list, tuple)):
                # Handle other iterables, but prevent string iteration
                try:
                    urls = list(urls)
                except TypeError:
                    urls = [str(urls)]  # Fallback for non-iterable types

            print(f"🔧 Processing {len(urls)} URL(s) for site structure discovery")

            # Validate URLs
            url_list = []
            for url in urls:
                print(f"🔗 Validating URL: {url}")
                url = url.strip()
                if url:
                    validated_url = self._ensure_valid_url(url)
                    if validated_url and self.is_allowed_domain(validated_url):
                        url_list.append(validated_url)
                    elif validated_url:
                        print(f"⚠️ URL not in allowed domains: {validated_url}")

            if not url_list:
                return "❌ No valid URLs provided or all URLs outside allowed domains"

            print(
                f"🔍 Discovering site structure for {len(url_list)} URLs: {', '.join([urlparse(u).netloc for u in url_list])} (Cache: ENABLED for discovery)"
            )

            # Handle async discovery properly for multiple URLs - use cache for discovery
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        self._run_multi_discovery, url_list, False
                    )  # Use cache for discovery
                    combined_discovered = future.result()
            except RuntimeError:
                combined_discovered = asyncio.run(
                    self._discover_multiple_urls(
                        url_list, False
                    )  # Use cache for discovery
                )

            return self._format_multi_discovery_results(combined_discovered, url_list)

        except Exception as e:
            return f"❌ Error in discover_site_structure: {str(e)}"

    def _run_discovery(self, url):
        """Helper method to run discovery in a new event loop."""
        return asyncio.run(self.discover_urls_from_sources(url))

    def _run_multi_discovery(self, url_list, bypass_cache=False):
        """Helper method to run multi-URL discovery in a new event loop."""
        return asyncio.run(self._discover_multiple_urls(url_list, bypass_cache))

    async def _discover_multiple_urls(
        self, url_list: List[str], bypass_cache: bool = False
    ) -> Dict[str, List[Tuple[str, str]]]:
        """Discover content from multiple base URLs and combine results with source attribution."""
        combined_results = {
            "llms_txt_content": [],
            "sitemap_urls": [],
            "base_page_content": [],
        }

        # Run discovery for each URL concurrently
        tasks = [self.discover_urls_from_sources(url, bypass_cache) for url in url_list]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results from all URLs with source attribution
        for i, result in enumerate(all_results):
            if isinstance(result, Exception):
                print(f"⚠️ Discovery failed for {url_list[i]}: {result}")
                continue

            base_domain = urlparse(url_list[i]).netloc

            # Handle different result types
            if "llms_txt_content" in result and result["llms_txt_content"]:
                # Add content with source attribution (base_domain, content)
                combined_results["llms_txt_content"].append(
                    (base_domain, result["llms_txt_content"])
                )

            if "sitemap_urls" in result and result["sitemap_urls"]:
                # Add sitemap URLs with source attribution (base_domain, urls_list)
                combined_results["sitemap_urls"].append(
                    (base_domain, result["sitemap_urls"])
                )

            if "base_page_content" in result and result["base_page_content"]:
                # Add content with source attribution (base_domain, content)
                combined_results["base_page_content"].append(
                    (base_domain, result["base_page_content"])
                )

        return combined_results

    def _format_multi_discovery_results(
        self, discovered: Dict[str, List[Tuple[str, str]]], url_list: List[str]
    ) -> str:
        """Format multi-URL discovery results with source attribution."""
        output = []
        output.append("=== CONTENT DISCOVERY ===")

        # Show which base URLs were discovered from
        domains = [urlparse(url).netloc for url in url_list]
        output.append(
            f"🔍 Discovered from {len(url_list)} base URLs: {', '.join(domains)}"
        )
        output.append("")

        total_content_sources = 0

        # Format llms.txt content (highest priority) with source attribution
        llms_content = discovered.get("llms_txt_content", [])
        if llms_content:
            total_content_sources += len(llms_content)
            output.append(
                f"📋 From llms.txt ({len(llms_content)} AI-optimized content sources found):"
            )
            for i, (base_domain, content) in enumerate(llms_content, 1):
                output.append(
                    f"  [{base_domain}] llms.txt content ({len(content)} chars):"
                )
                output.append(f"{content}")
                output.append("")

        # Format sitemap URLs (second priority) with source attribution
        sitemap_data = discovered.get("sitemap_urls", [])
        if sitemap_data:
            total_sitemap_urls = sum(len(urls) for _, urls in sitemap_data)
            output.append(
                f"🗺️ From sitemap discovery ({len(sitemap_data)} domains, {total_sitemap_urls} URLs found):"
            )
            for i, (base_domain, urls) in enumerate(sitemap_data, 1):
                output.append(f"  [{base_domain}] {len(urls)} URLs discovered:")
                # Show all URLs for agent selection
                for j, url in enumerate(urls, 1):
                    output.append(f"    {j}. {url}")
                output.append("")

        # Format base page content (fallback) with source attribution
        base_content = discovered.get("base_page_content", [])
        if base_content:
            total_content_sources += len(base_content)
            output.append(
                f"📄 From base page crawls ({len(base_content)} pages found):"
            )
            for i, (base_domain, content) in enumerate(base_content, 1):
                output.append(f"  [{base_domain}] Page {i} ({len(content)} chars):")
                output.append(f"{content}")
                output.append("")

        # Summary
        output.append("=== DISCOVERY SUMMARY ===")
        total_sitemap_urls = sum(
            len(urls) for _, urls in discovered.get("sitemap_urls", [])
        )
        output.append(f"Total content sources discovered: {total_content_sources}")
        output.append(f"Total sitemap URLs discovered: {total_sitemap_urls}")

        if llms_content:
            output.append(
                "💡 llms.txt content is immediately available for answering questions."
            )
        if total_sitemap_urls > 0:
            output.append(
                "💡 Use 'crawl_selected_urls' to crawl specific URLs from the sitemap that are relevant to your question."
            )
        if base_content:
            output.append(
                "💡 Base page content is immediately available for answering questions."
            )

        if total_content_sources == 0 and total_sitemap_urls == 0:
            output.append(
                "\n⚠️ No content or URLs discovered from any source (llms.txt, sitemap, or base page crawls)."
            )
            output.append(
                "You can still crawl the base URLs directly using 'crawl_selected_urls'."
            )

        return "\n".join(output)

    def _format_discovery_results(self, discovered: Dict[str, List[str]]) -> str:
        """Format discovery results for agent decision-making."""
        output = []
        output.append("=== SITE STRUCTURE DISCOVERY ===\n")

        total_urls = 0

        # Format llms.txt URLs (highest priority)
        llms_urls = discovered.get("llms_txt", [])
        if llms_urls:
            total_urls += len(llms_urls)
            output.append(
                f"📋 From llms.txt ({len(llms_urls)} AI-optimized URLs found):"
            )
            for i, url in enumerate(llms_urls, 1):
                output.append(f"  {i}. {url}")
            output.append("")

        # Format base page content (fallback)
        base_content = discovered.get("base_page_content", "")
        if base_content:
            output.append(f"📄 From base page crawl ({len(base_content)} chars found):")
            output.append(f"{base_content}")
            output.append("")

        # Summary
        output.append("=== DISCOVERY SUMMARY ===")
        output.append(f"Total URLs discovered: {total_urls}")
        output.append(
            "💡 Use 'crawl_selected_urls' tool to crawl specific URLs that are relevant to the user's question."
        )

        if total_urls == 0:
            output.append(
                "\n⚠️ No URLs discovered from any source (llms.txt or base page links)."
            )
            output.append(
                "You can still crawl the base URL directly using 'crawl_selected_urls'."
            )

        return "\n".join(output)

    def crawl_selected_urls(self, urls) -> str:
        """
        Crawl specific URLs selected by the agent after site structure discovery.

        Always gets fresh content (bypasses cache) to ensure up-to-date information.

        Args:
            urls: URL(s) to crawl - can be a single string or list of strings
                 (e.g., "https://site.com/docs" or ["https://site.com/docs", "https://site.com/faq"])

        Returns:
            str: Formatted content from crawled pages
        """
        try:
            # Fix input type handling - ensure urls is always a list
            if isinstance(urls, str):
                urls = [urls]  # Convert single string to list
            elif not isinstance(urls, (list, tuple)):
                # Handle other iterables, but prevent string iteration
                try:
                    urls = list(urls)
                except TypeError:
                    urls = [str(urls)]  # Fallback for non-iterable types

            print(f"🔧 Processing {len(urls)} URL(s) for crawling")

            # Parse and validate URLs
            url_list = []
            for url in urls:
                url = url.strip()
                if url:
                    validated_url = self._ensure_valid_url(url)
                    if validated_url and self.is_allowed_domain(validated_url):
                        url_list.append(validated_url)

            if not url_list:
                return "❌ No valid URLs provided"

            print(f"🔍 Crawling {len(url_list)} selected URLs... (FRESH content)")

            # Handle async crawling properly - always bypass cache for content
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        self._run_simple_crawling, url_list, True
                    )  # Always bypass cache
                    results = future.result()
            except RuntimeError:
                results = asyncio.run(
                    self._crawl_multiple_urls(url_list, True)
                )  # Always bypass cache

            return self._format_results(results)

        except Exception as e:
            return f"❌ Error in crawl_selected_urls: {str(e)}"

    def _run_simple_crawling(self, urls, bypass_cache=False):
        """Helper method to run simple crawling in a new event loop."""
        return asyncio.run(self._crawl_multiple_urls(urls, bypass_cache))

    def _run_smart_crawling(self, urls):
        """Helper method to run smart crawling in a new event loop."""
        return asyncio.run(self._smart_crawl_multiple_urls(urls))

    async def _smart_crawl_multiple_urls(
        self, initial_urls: List[str]
    ) -> List[Tuple[str, str, List[str]]]:
        """Smart crawling - now primarily returns content directly from llms.txt."""
        urls_to_crawl = set(initial_urls)

        # For each initial URL, discover content (not just URLs)
        for url in initial_urls:
            try:
                discovered = await self.discover_urls_from_sources(url)

                # Note: Now returns content directly, not URLs to crawl
                # The content is already available in the discovery results
                print(
                    f"📋 Discovered content from {url}: {len(discovered.get('llms_txt_content', ''))} chars from llms.txt, {len(discovered.get('base_page_content', ''))} chars from base page"
                )

            except Exception as e:
                print(f"⚠️ Content discovery failed for {url}: {e}")

        # Convert to list for fallback crawling
        final_urls = list(urls_to_crawl)
        print(
            f"📋 Fallback crawling {len(final_urls)} URLs (content may already be available from discovery)"
        )

        # Crawl all selected URLs as fallback
        return await self._crawl_multiple_urls(final_urls)

    async def _crawl_multiple_urls(
        self, urls: List[str], bypass_cache: bool = False
    ) -> List[Tuple[str, str, List[str]]]:
        """Crawl multiple URLs with optimized concurrency management for maximum performance."""
        if not urls:
            return []

        start_time = time.time()

        # Smart concurrency based on URL count and system capabilities
        max_concurrent = min(len(urls), 5)  # Optimal concurrency for most systems
        semaphore = asyncio.Semaphore(max_concurrent)

        print(
            f"🚀 Starting optimized crawl of {len(urls)} URLs with {max_concurrent} concurrent workers"
        )

        async def crawl_with_concurrency_limit(url: str) -> Tuple[str, str, List[str]]:
            """Crawl a single URL with concurrency limiting."""
            async with semaphore:
                return await self.crawl_single_url(url, bypass_cache)

        # Create tasks for all URLs
        tasks = [crawl_with_concurrency_limit(url) for url in urls]

        # Use asyncio.gather for maximum parallel execution
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        successful_crawls = 0
        failed_crawls = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append((urls[i], f"Exception: {str(result)}", []))
                failed_crawls += 1
                print(f"❌ Failed to crawl {urls[i]}: {str(result)}")
            else:
                processed_results.append(result)
                successful_crawls += 1

        total_time = time.time() - start_time
        avg_time_per_url = total_time / len(urls) if urls else 0

        print(
            f"⚡ Completed crawl batch: {successful_crawls} successful, {failed_crawls} failed in {total_time:.2f}s (avg {avg_time_per_url:.2f}s per URL)"
        )

        return processed_results

    def _format_results(self, results: List[Tuple[str, str, List[str]]]) -> str:
        """Format crawling results for agent consumption."""
        if not results:
            return "❌ No results to display"

        output = []
        output.append("=== CRAWLED CONTENT ===\n")

        # Add content from each URL with stats
        total_content_length = 0
        for url, content, links in results:
            content_length = len(content)
            total_content_length += content_length

            output.append(f"URL: {url}")
            output.append(f"Content Length: {content_length} characters")

            # Show ALL content - no truncation limit
            output.append(f"Content: {content}")
            output.append("")  # Empty line for readability

        # Add summary
        output.append(f"=== CRAWLING SUMMARY ===")
        output.append(f"Total URLs crawled: {len(results)}")
        output.append(f"Total content extracted: {total_content_length} characters")
        output.append("")

        # Add discovered links section
        output.append("=== DISCOVERED LINKS ===\n")

        total_links = 0
        for url, content, links in results:
            if links:
                total_links += len(links)
                output.append(f"From {url} ({len(links)} links found):")
                for link in links:  # Show all discovered links
                    output.append(f"- {link}")
                output.append("")

        output.append(f"Total unique links discovered: {total_links}")
        return "\n".join(output)

    # ========== PDF PROCESSING METHODS ==========

    def process_pdf_urls(self, urls) -> str:
        """
        Process PDF URLs to extract content and metadata.

        Always gets fresh content (bypasses cache) to ensure up-to-date information.

        Args:
            urls: PDF URL(s) to process - can be a single string or list of strings
                 (e.g., "https://arxiv.org/pdf/paper.pdf" or ["https://site.com/doc1.pdf", "https://site.com/doc2.pdf"])

        Returns:
            str: Formatted content and metadata from processed PDFs
        """
        try:
            # Fix input type handling - ensure urls is always a list
            if isinstance(urls, str):
                urls = [urls]  # Convert single string to list
            elif not isinstance(urls, (list, tuple)):
                # Handle other iterables, but prevent string iteration
                try:
                    urls = list(urls)
                except TypeError:
                    urls = [str(urls)]  # Fallback for non-iterable types

            print(f"📄 Processing {len(urls)} PDF URL(s)")

            # Parse and validate PDF URLs
            url_list = []
            for url in urls:
                url = url.strip()
                if url:
                    validated_url = self._ensure_valid_url(url)
                    if (
                        validated_url
                        and self._validate_pdf_url(validated_url)
                        and self.is_allowed_domain(validated_url)
                    ):
                        url_list.append(validated_url)
                    elif validated_url and not self._validate_pdf_url(validated_url):
                        print(f"⚠️ URL does not appear to be a PDF: {validated_url}")
                    elif validated_url:
                        print(f"⚠️ URL not in allowed domains: {validated_url}")

            if not url_list:
                return "❌ No valid PDF URLs provided"

            print(f"🔍 Processing {len(url_list)} PDF URLs... (FRESH content)")

            # Handle async PDF processing properly - always bypass cache for content
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_pdf_processing, url_list)
                    results = future.result()
            except RuntimeError:
                results = asyncio.run(self._process_multiple_pdfs(url_list))

            return self._format_pdf_results(results)

        except Exception as e:
            return f"❌ Error in process_pdf_urls: {str(e)}"

    def _validate_pdf_url(self, url: str) -> bool:
        """Check if URL likely points to a PDF file."""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()

            # Check for .pdf extension
            if path.endswith(".pdf"):
                return True

            # Check for common PDF-serving patterns
            pdf_patterns = [
                "/pdf/",
                "download.pdf",
                "viewpdf",
                "pdfviewer",
                ".pdf?",
                "type=pdf",
            ]

            url_lower = url.lower()
            return any(pattern in url_lower for pattern in pdf_patterns)

        except Exception:
            return False

    def _get_pdf_crawler_config(self) -> CrawlerRunConfig:
        """Get PDF-optimized crawler configuration."""
        # Use PDFContentScrapingStrategy for PDF processing
        pdf_scraping_strategy = PDFContentScrapingStrategy()

        return CrawlerRunConfig(
            scraping_strategy=pdf_scraping_strategy,
            cache_mode=CacheMode.BYPASS,  # Always get fresh PDF content
            wait_until="commit",
            delay_before_return_html=0,
            word_count_threshold=1,
            process_iframes=False,
            simulate_user=False,
            override_navigator=False,
        )

    async def _process_single_pdf(self, url: str) -> Tuple[str, str, Dict[str, str]]:
        """Process a single PDF URL with PDF-specific configuration."""
        start_time = time.time()

        try:
            # Initialize PDF crawler strategy
            pdf_crawler_strategy = PDFCrawlerStrategy()
            crawler_config = self._get_pdf_crawler_config()

            async with AsyncWebCrawler(
                crawler_strategy=pdf_crawler_strategy
            ) as crawler:
                print(f"📄 Attempting to process PDF: {url}")
                result = await crawler.arun(url=url, config=crawler_config)

                if not result or not result.success:
                    return (
                        url,
                        f"Failed to process PDF: {result.error_message if result else 'Unknown error'}",
                        {},
                    )

                # Extract PDF content and metadata
                content, metadata = self._extract_pdf_content_and_metadata(result)

                crawl_time = time.time() - start_time
                print(
                    f"📄 Processed PDF {url} in {crawl_time:.2f}s - {len(content)} chars"
                )

                return url, content, metadata

        except Exception as e:
            crawl_time = time.time() - start_time
            print(f"❌ Failed to process PDF {url} in {crawl_time:.2f}s: {str(e)}")
            return url, f"Error processing PDF {url}: {str(e)}", {}

    def _extract_pdf_content_and_metadata(self, result) -> Tuple[str, Dict[str, str]]:
        """Extract content and metadata from PDF processing result."""
        content = ""
        metadata = {}

        try:
            # Extract text content
            if result.markdown:
                if (
                    hasattr(result.markdown, "raw_markdown")
                    and result.markdown.raw_markdown
                ):
                    content = result.markdown.raw_markdown
                elif isinstance(result.markdown, str):
                    content = result.markdown
                else:
                    content = str(result.markdown)
            elif result.cleaned_html:
                # Fallback to cleaned HTML if markdown is not available
                content = result.cleaned_html

            # Extract metadata
            if hasattr(result, "metadata") and result.metadata:
                metadata = {
                    "title": result.metadata.get("title", "N/A"),
                    "author": result.metadata.get("author", "N/A"),
                    "subject": result.metadata.get("subject", "N/A"),
                    "creator": result.metadata.get("creator", "N/A"),
                    "producer": result.metadata.get("producer", "N/A"),
                    "creation_date": result.metadata.get("creation_date", "N/A"),
                    "modification_date": result.metadata.get(
                        "modification_date", "N/A"
                    ),
                    "pages": result.metadata.get("pages", "N/A"),
                }

            # If no content extracted, provide a message
            if not content or len(content.strip()) < 10:
                content = "No text content could be extracted from this PDF"

        except Exception as e:
            print(f"⚠️ Error extracting PDF content: {e}")
            content = f"Error extracting content: {str(e)}"
            metadata = {}

        return content, metadata

    def _run_pdf_processing(self, urls):
        """Helper method to run PDF processing in a new event loop."""
        return asyncio.run(self._process_multiple_pdfs(urls))

    async def _process_multiple_pdfs(
        self, urls: List[str]
    ) -> List[Tuple[str, str, Dict[str, str]]]:
        """Process multiple PDF URLs with optimized concurrency management."""
        if not urls:
            return []

        start_time = time.time()

        # Smart concurrency based on URL count (PDFs can be large, so lower concurrency)
        max_concurrent = min(len(urls), 3)  # Lower concurrency for PDF processing
        semaphore = asyncio.Semaphore(max_concurrent)

        print(
            f"📄 Starting PDF processing of {len(urls)} URLs with {max_concurrent} concurrent workers"
        )

        async def process_with_concurrency_limit(
            url: str,
        ) -> Tuple[str, str, Dict[str, str]]:
            """Process a single PDF URL with concurrency limiting."""
            async with semaphore:
                return await self._process_single_pdf(url)

        # Create tasks for all URLs
        tasks = [process_with_concurrency_limit(url) for url in urls]

        # Use asyncio.gather for parallel execution
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        successful_processes = 0
        failed_processes = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append((urls[i], f"Exception: {str(result)}", {}))
                failed_processes += 1
                print(f"❌ Failed to process PDF {urls[i]}: {str(result)}")
            else:
                processed_results.append(result)
                successful_processes += 1

        total_time = time.time() - start_time
        avg_time_per_pdf = total_time / len(urls) if urls else 0

        print(
            f"📄 Completed PDF processing batch: {successful_processes} successful, {failed_processes} failed in {total_time:.2f}s (avg {avg_time_per_pdf:.2f}s per PDF)"
        )

        return processed_results

    def _format_pdf_results(
        self, results: List[Tuple[str, str, Dict[str, str]]]
    ) -> str:
        """Format PDF processing results for agent consumption."""
        if not results:
            return "❌ No PDF results to display"

        output = []
        output.append("=== PDF PROCESSING RESULTS ===\n")

        # Add content from each PDF with metadata
        total_content_length = 0
        for url, content, metadata in results:
            content_length = len(content)
            total_content_length += content_length

            output.append(f"PDF URL: {url}")
            output.append(f"Content Length: {content_length} characters")

            # Add metadata if available
            if metadata:
                output.append("PDF Metadata:")
                for key, value in metadata.items():
                    if value and value != "N/A":
                        output.append(f"  {key.replace('_', ' ').title()}: {value}")
                output.append("")

            # Show ALL content - no truncation limit
            output.append("Extracted Content:")
            output.append(f"{content}")
            output.append("")  # Empty line for readability

        # Add summary
        output.append("=== PDF PROCESSING SUMMARY ===")
        output.append(f"Total PDFs processed: {len(results)}")
        output.append(f"Total content extracted: {total_content_length} characters")

        # Count successful vs failed processing
        successful_pdfs = sum(
            1
            for _, content, _ in results
            if not content.startswith(
                ("Failed to process", "Error processing", "Exception:")
            )
        )
        failed_pdfs = len(results) - successful_pdfs

        output.append(f"Successfully processed: {successful_pdfs} PDFs")
        if failed_pdfs > 0:
            output.append(f"Failed to process: {failed_pdfs} PDFs")

        return "\n".join(output)

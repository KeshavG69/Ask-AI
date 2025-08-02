import asyncio
import re
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict, Optional
from urllib.parse import urljoin, urlparse
from agno.tools import Toolkit
import aiohttp
import time
import os


class WebCrawlerTool(Toolkit):
    """Web crawler tool using Jina Reader API for content extraction."""

    def __init__(self, starting_urls: List[str] = None, api_key: Optional[str] = None):
        super().__init__()
        self.starting_urls = starting_urls or []
        self.allowed_domains = self._extract_domains_from_urls(self.starting_urls)
        self.api_key = api_key or os.getenv('JINA_API_KEY')
        self.jina_base_url = "https://r.jina.ai"
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

    async def _jina_read_url(self, url: str, **options) -> str:
        """Read a single URL using Jina Reader API."""
        try:
            jina_url = f"{self.jina_base_url}/{url}"
            headers = {}
            
            # Add authorization header if API key is available
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
                print(f"🔑 Using Jina API key for higher rate limits")
            
            # Add custom options as headers if provided
            if 'timeout' in options:
                headers['X-Timeout'] = str(options['timeout'])
            if 'image_caption' in options and options['image_caption']:
                headers['X-With-Generated-Alt'] = 'true'
            if 'gather_links' in options and options['gather_links']:
                headers['X-With-Links-Summary'] = 'true'
            if 'gather_images' in options and options['gather_images']:
                headers['X-With-Images-Summary'] = 'true'

            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(jina_url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        content = await response.text()
                        crawl_time = time.time() - start_time
                        print(f"⚡ Jina Reader processed {url} in {crawl_time:.2f}s - {len(content)} chars")
                        return content
                    else:
                        error_msg = f"Jina Reader API error {response.status} for {url}"
                        print(f"❌ {error_msg}")
                        return f"Error: {error_msg}"
                        
        except Exception as e:
            print(f"❌ Failed to read {url} with Jina Reader: {str(e)}")
            return f"Error reading {url}: {str(e)}"

    async def _jina_read_multiple_urls(self, urls: List[str], **options) -> List[Tuple[str, str]]:
        """Read multiple URLs concurrently using Jina Reader API."""
        if not urls:
            return []

        start_time = time.time()
        
        # Smart concurrency - Jina Reader can handle high concurrency
        max_concurrent = min(len(urls), 10)  # Higher than crawl4ai since it's just API calls
        semaphore = asyncio.Semaphore(max_concurrent)

        print(f"🚀 Starting Jina Reader batch processing of {len(urls)} URLs with {max_concurrent} concurrent workers")

        async def read_with_concurrency_limit(url: str) -> Tuple[str, str]:
            """Read a single URL with concurrency limiting."""
            async with semaphore:
                content = await self._jina_read_url(url, **options)
                return url, content

        # Create tasks for all URLs
        tasks = [read_with_concurrency_limit(url) for url in urls]

        # Use asyncio.gather for maximum parallel execution
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        successful_reads = 0
        failed_reads = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append((urls[i], f"Exception: {str(result)}"))
                failed_reads += 1
                print(f"❌ Failed to read {urls[i]}: {str(result)}")
            else:
                processed_results.append(result)
                successful_reads += 1

        total_time = time.time() - start_time
        avg_time_per_url = total_time / len(urls) if urls else 0

        print(f"⚡ Completed Jina Reader batch: {successful_reads} successful, {failed_reads} failed in {total_time:.2f}s (avg {avg_time_per_url:.2f}s per URL)")

        return processed_results

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

            # Step 5: Fallback to base page content using Jina Reader (only if no sitemap URLs found)
            if not sources["sitemap_urls"]:
                print(f"📄 No sitemap URLs found, falling back to base page content with Jina Reader...")
                try:
                    # Replace crawl4ai call with Jina Reader API call
                    content = await self._jina_read_url(input_url)
                    if content and not content.startswith("Error"):
                        sources["base_page_content"] = content
                        print(f"✅ Found {len(content)} characters of content from base page via Jina Reader")
                    else:
                        print("⚠️ No content found on base page")
                except Exception as e:
                    print(f"⚠️ Base page reading failed: {e}")

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
                f"🔍 Discovering site structure for {len(url_list)} URLs: {', '.join([urlparse(u).netloc for u in url_list])} (Using Jina Reader)"
            )

            # Handle async discovery properly for multiple URLs
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        self._run_multi_discovery, url_list, False
                    )
                    combined_discovered = future.result()
            except RuntimeError:
                combined_discovered = asyncio.run(
                    self._discover_multiple_urls(url_list, False)
                )

            return self._format_multi_discovery_results(combined_discovered, url_list)

        except Exception as e:
            return f"❌ Error in discover_site_structure: {str(e)}"

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
            
            # Limit to top 200 URLs total across all domains
            url_count = 0
            max_urls = 200
            
            for i, (base_domain, urls) in enumerate(sitemap_data, 1):
                remaining_slots = max_urls - url_count
                if remaining_slots <= 0:
                    output.append(f"  ... and {len(sitemap_data) - i + 1} more domains with URLs truncated due to 200 URL limit")
                    break
                
                urls_to_show = urls[:remaining_slots]
                if len(urls) > len(urls_to_show):
                    output.append(f"  [{base_domain}] {len(urls_to_show)} URLs shown (of {len(urls)} total):")
                else:
                    output.append(f"  [{base_domain}] {len(urls_to_show)} URLs discovered:")
                
                # Show URLs up to the limit
                for j, url in enumerate(urls_to_show, 1):
                    output.append(f"    {j}. {url}")
                    url_count += 1
                
                if len(urls) > len(urls_to_show):
                    output.append(f"    ... and {len(urls) - len(urls_to_show)} more URLs truncated")
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

    def crawl_selected_urls(self, urls) -> str:
        """
        Crawl specific URLs selected by the agent after site structure discovery.

        Uses Jina Reader API for clean, LLM-friendly content extraction.

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

            print(f"🔧 Processing {len(urls)} URL(s) for crawling with Jina Reader")

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

            print(f"🔍 Reading {len(url_list)} selected URLs with Jina Reader API...")

            # Handle async reading properly
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_jina_reading, url_list)
                    results = future.result()
            except RuntimeError:
                results = asyncio.run(self._jina_read_multiple_urls(url_list))

            return self._format_jina_results(results)

        except Exception as e:
            return f"❌ Error in crawl_selected_urls: {str(e)}"

    def _run_jina_reading(self, urls):
        """Helper method to run Jina reading in a new event loop."""
        return asyncio.run(self._jina_read_multiple_urls(urls))

    def _format_jina_results(self, results: List[Tuple[str, str]]) -> str:
        """Format Jina Reader results for agent consumption."""
        if not results:
            return "❌ No results to display"

        output = []
        output.append("=== JINA READER CONTENT ===\n")

        # Add content from each URL with stats
        total_content_length = 0
        for url, content in results:
            content_length = len(content)
            total_content_length += content_length

            output.append(f"URL: {url}")
            output.append(f"Content Length: {content_length} characters")

            # Show ALL content - no truncation limit
            output.append(f"Content: {content}")
            output.append("")  # Empty line for readability

        # Add summary
        output.append(f"=== READING SUMMARY ===")
        output.append(f"Total URLs processed: {len(results)}")
        output.append(f"Total content extracted: {total_content_length} characters")

        return "\n".join(output)

    def process_pdf_urls(self, urls) -> str:
        """
        Process PDF URLs to extract content and metadata using Jina Reader API.
        
        Jina Reader handles PDFs natively with better processing than crawl4ai.

        Args:
            urls: PDF URL(s) to process - can be a single string or list of strings
                 (e.g., "https://arxiv.org/pdf/paper.pdf" or ["https://site.com/doc1.pdf", "https://site.com/doc2.pdf"])

        Returns:
            str: Formatted content from processed PDFs
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

            print(f"📄 Processing {len(urls)} PDF URL(s) with Jina Reader")

            # Parse and validate PDF URLs
            url_list = []
            for url in urls:
                url = url.strip()
                if url:
                    validated_url = self._ensure_valid_url(url)
                    if validated_url and self.is_allowed_domain(validated_url):
                        url_list.append(validated_url)
                        print(f"✅ Valid PDF URL: {validated_url}")

            if not url_list:
                return "❌ No valid PDF URLs provided"

            print(f"🔍 Processing {len(url_list)} PDF URLs with Jina Reader API...")

            # Handle async PDF processing properly
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_jina_reading, url_list)
                    results = future.result()
            except RuntimeError:
                results = asyncio.run(self._jina_read_multiple_urls(url_list))

            return self._format_pdf_jina_results(results)

        except Exception as e:
            return f"❌ Error in process_pdf_urls: {str(e)}"

    def _format_pdf_jina_results(self, results: List[Tuple[str, str]]) -> str:
        """Format PDF processing results from Jina Reader for agent consumption."""
        if not results:
            return "❌ No PDF results to display"

        output = []
        output.append("=== PDF PROCESSING RESULTS (Jina Reader) ===\n")

        # Add content from each PDF with stats
        total_content_length = 0
        for url, content in results:
            content_length = len(content)
            total_content_length += content_length

            output.append(f"PDF URL: {url}")
            output.append(f"Content Length: {content_length} characters")

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
            for _, content in results
            if not content.startswith(("Error:", "Exception:"))
        )
        failed_pdfs = len(results) - successful_pdfs

        output.append(f"Successfully processed: {successful_pdfs} PDFs")
        if failed_pdfs > 0:
            output.append(f"Failed to process: {failed_pdfs} PDFs")

        return "\n".join(output)

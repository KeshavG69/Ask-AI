import asyncio
import re
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict
from urllib.parse import urljoin, urlparse
from agno.tools import Toolkit
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
import aiohttp


class WebCrawlerTool(Toolkit):
    """Simple web crawler tool that returns content and links for agent decision making."""

    def __init__(self, starting_urls: List[str] = None, max_links_per_page: int = 50):
        super().__init__()
        self.starting_urls = starting_urls or []
        self.allowed_domains = self._extract_domains_from_urls(self.starting_urls)
        self.max_links_per_page = max_links_per_page
        self.register(self.crawl_selected_urls)

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

    async def discover_urls_from_sources(self, input_url: str, bypass_cache: bool = False) -> Dict[str, List[str]]:
        """Discover URLs from llms.txt or fallback to base page crawling."""
        root_domain = self._get_root_domain(input_url)
        print(f"🔍 Discovering URLs from: {root_domain}")

        sources = {
            "llms_txt": [],
            "base_page_content": "",
        }

        try:
            # Try llms.txt first (AI-optimized content)
            llms_urls = await self._get_urls_from_llms_txt(f"{root_domain}/llms.txt")
            if llms_urls:
                sources["llms_txt"] = llms_urls
                print(f"✅ Found {len(llms_urls)} URLs in llms.txt")

            # FALLBACK: If no URLs discovered from llms.txt, crawl base URL
            total_discovered = len(sources["llms_txt"])

            if total_discovered == 0:
                print(f"📄 No llms.txt found. Crawling base URL for content... ({'FRESH' if bypass_cache else 'CACHED'})")
                try:
                    _, content, _ = await self.crawl_single_url(input_url, bypass_cache)
                    if content:
                        sources["base_page_content"] = (
                            content  # Return full scraped content
                        )
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

    async def _get_urls_from_llms_txt(self, llms_url: str) -> List[str]:
        """Parse llms.txt for AI-optimized content URLs."""
        try:
            print(f"🔍 Checking llms.txt at: {llms_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(llms_url, timeout=10) as response:
                    print(f"📄 llms.txt response status: {response.status}")

                    if response.status == 200:
                        content = await response.text()
                        print(f"📄 llms.txt content length: {len(content)} chars")
                        print(f"📄 llms.txt content preview: {content[:200]}...")

                        urls = []
                        lines_processed = 0

                        for line in content.strip().split("\n"):
                            line = line.strip()
                            lines_processed += 1

                            if line and not line.startswith("#"):
                                print(f"🔗 Processing line {lines_processed}: '{line}'")

                                # Extract URLs from Markdown links: [text](url)
                                markdown_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
                                match = re.search(markdown_pattern, line)

                                if match:
                                    url_part = match.group(
                                        2
                                    )  # Get URL from parentheses
                                    print(f"🔗 Extracted Markdown URL: '{url_part}'")
                                else:
                                    # Fallback to original logic for plain URLs
                                    url_part = line.split()[0] if line else ""
                                    print(f"🔗 Extracted plain URL: '{url_part}'")

                                if url_part.startswith(("http", "/")):
                                    full_url = urljoin(llms_url, url_part)
                                    print(f"🔗 Full URL constructed: '{full_url}'")

                                    if self.is_allowed_domain(full_url):
                                        validated = self._ensure_valid_url(full_url)
                                        if validated:
                                            urls.append(validated)
                                            print(f"✅ Added URL: {validated}")
                                        else:
                                            print(
                                                f"❌ URL validation failed for: {full_url}"
                                            )
                                    else:
                                        print(f"❌ Domain not allowed for: {full_url}")
                                else:
                                    print(
                                        f"⚠️ Skipping line (no valid URL): '{url_part}'"
                                    )

                        print(f"✅ Found {len(urls)} valid URLs from llms.txt")
                        return urls  # Return all found URLs
                    else:
                        print(f"❌ llms.txt not found (status {response.status})")

        except Exception as e:
            print(f"❌ llms.txt parsing error: {e}")
            import traceback

            print(f"❌ Full traceback: {traceback.format_exc()}")

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
        unique_links = list(dict.fromkeys(links))[: self.max_links_per_page]
        return unique_links

    async def crawl_single_url(self, url: str, bypass_cache: bool = False) -> Tuple[str, str, List[str]]:
        """Crawl a single URL and return content, raw HTML, and links."""
        try:
            # Import CacheMode here to avoid circular imports
            from crawl4ai import CacheMode
            
            # Configure crawling with cache mode
            cache_mode = CacheMode.BYPASS if bypass_cache else CacheMode.ENABLED
            
            config = CrawlerRunConfig(
                cache_mode=cache_mode,
                wait_until="domcontentloaded",
                delay_before_return_html=2,
                word_count_threshold=10,
            )

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url, config=config)

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

                print(f"📄 Crawled {url} ({'FRESH' if bypass_cache else 'CACHED'}) - {len(content)} chars")
                
                return url, content, links

        except Exception as e:
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

    def discover_site_structure(self, urls: List[str]) -> str:
        """
        Discover available URLs from llms.txt for agent decision-making.
        
        Uses caching for site structure discovery (since site structure changes infrequently).

        Args:
            urls (List[str]): List of URLs to discover from
                            (e.g., ["https://docs.example.com"] or ["https://site1.com", "https://site2.com"])

        Returns:
            str: Formatted list of available URLs organized by source (llms.txt, base page links)
        """
        try:
            # Validate URLs
            url_list = []
            for url in urls:
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
                    future = executor.submit(self._run_multi_discovery, url_list, False)  # Use cache for discovery
                    combined_discovered = future.result()
            except RuntimeError:
                combined_discovered = asyncio.run(
                    self._discover_multiple_urls(url_list, False)  # Use cache for discovery
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
        """Discover URLs from multiple base URLs and combine results with source attribution."""
        combined_results = {"llms_txt": [], "base_page_content": []}

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
            if "llms_txt" in result and result["llms_txt"]:
                # Add URLs with source attribution (base_domain, url)
                for url in result["llms_txt"]:
                    combined_results["llms_txt"].append((base_domain, url))

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
        output.append("=== SITE STRUCTURE DISCOVERY ===")

        # Show which base URLs were discovered from
        domains = [urlparse(url).netloc for url in url_list]
        output.append(
            f"🔍 Discovered from {len(url_list)} base URLs: {', '.join(domains)}"
        )
        output.append("")

        total_urls = 0

        # Format llms.txt URLs (highest priority) with source attribution
        llms_urls = discovered.get("llms_txt", [])
        if llms_urls:
            total_urls += len(llms_urls)
            output.append(
                f"📋 From llms.txt ({len(llms_urls)} AI-optimized URLs found):"
            )
            for i, (base_domain, url) in enumerate(llms_urls, 1):
                output.append(f"  [{base_domain}] {i}. {url}")
            output.append("")

        # Format base page content (fallback) with source attribution
        base_content = discovered.get("base_page_content", [])
        if base_content:
            output.append(f"📄 From base page crawls ({len(base_content)} pages found):")
            for i, (base_domain, content) in enumerate(base_content, 1):
                output.append(f"  [{base_domain}] Page {i} ({len(content)} chars):")
                output.append(f"{content}")
                output.append("")
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
            for i, url in enumerate(llms_urls[:15], 1):
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

    def crawl_selected_urls(self, urls: List[str]) -> str:
        """
        Crawl specific URLs selected by the agent after site structure discovery.
        
        Always gets fresh content (bypasses cache) to ensure up-to-date information.

        Args:
            urls (List[str]): List of URLs to crawl (e.g., ["https://site.com/docs", "https://site.com/faq"])

        Returns:
            str: Formatted content from crawled pages
        """
        try:
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
                    future = executor.submit(self._run_simple_crawling, url_list, True)  # Always bypass cache
                    results = future.result()
            except RuntimeError:
                results = asyncio.run(self._crawl_multiple_urls(url_list, True))  # Always bypass cache

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
        """Smart crawling with URL discovery from llms.txt."""
        urls_to_crawl = set(initial_urls)

        # For each initial URL, discover additional URLs
        for url in initial_urls:
            try:
                discovered = await self.discover_urls_from_sources(url)

                # Add discovered URLs from llms.txt
                urls_to_crawl.update(discovered.get("llms_txt", [])[:5])

            except Exception as e:
                print(f"⚠️ URL discovery failed for {url}: {e}")

        # Convert to list and limit total URLs
        final_urls = list(urls_to_crawl)[:12]  # Limit to 12 total URLs
        print(
            f"📋 Selected {len(final_urls)} URLs for crawling (including discovered URLs)"
        )

        # Crawl all selected URLs
        return await self._crawl_multiple_urls(final_urls)

    async def _crawl_multiple_urls(
        self, urls: List[str], bypass_cache: bool = False
    ) -> List[Tuple[str, str, List[str]]]:
        """Crawl multiple URLs concurrently using Crawl4AI's built-in caching."""
        tasks = [self.crawl_single_url(url, bypass_cache) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append((urls[i], f"Exception: {str(result)}", []))
            else:
                processed_results.append(result)

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
                for link in links[:15]:  # Show top 15 most relevant links
                    output.append(f"- {link}")
                output.append("")

        output.append(f"Total unique links discovered: {total_links}")
        return "\n".join(output)

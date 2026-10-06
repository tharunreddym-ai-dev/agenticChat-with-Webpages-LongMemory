import socket
import ipaddress
from urllib.parse import urlparse

# `requests` is intentionally not imported here anymore — see the note in
# validate_url() below on why this file no longer makes its own outbound
# reachability request.

# firecrawl-py 2.x+ repositioned the default `Firecrawl`/`FirecrawlApp` export
# toward its research/literature-search product — it no longer has scrape_url,
# crawl_url, map_url, etc. That general web-scraping toolkit still lives on
# V1FirecrawlApp, which is why it's imported under the old name here.
from firecrawl import V1FirecrawlApp as FirecrawlApp
from tavily import TavilyClient
from config import FIRECRAWL_API_KEY,TAVILY_API_KEY


class URLValidationError(Exception):
    pass

class ScrapingError(Exception):
    pass

class TavilyError(Exception):
    pass

def validate_url(url):
    if not url or not isinstance(url,str):
        raise URLValidationError("URL is required and it Must be String")

    url=url.strip()
    try:
        parsed=urlparse(url)
    except Exception:
        raise URLValidationError("Invalid URL")

    if parsed.scheme not in ("https","http"):
        raise URLValidationError("URL must use https or http")

    if not parsed.hostname:
        raise URLValidationError("URL must Contain Valid Hostname")

    hostname=parsed.hostname

    if hostname.lower() in ("localhost","localhost.localdomain"):
        raise URLValidationError("Internal URLs are not Allowed.")

    try:
        ip_addresses=socket.getaddrinfo(hostname,None,socket.AF_UNSPEC,socket.SOCK_STREAM)
    except socket.gaierror:
        raise URLValidationError("Unable to Resolve the URL hostname")

    for address in ip_addresses:
        ip = ipaddress.ip_address(address[4][0])

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise URLValidationError(
                "URLs pointing to private or internal networks are not allowed."
            )


    return url

def scarping_website_using_firecrawl(url:str):
    try:
        app=FirecrawlApp(api_key=FIRECRAWL_API_KEY)

        result=app.scrape_url(
            url=url,
            formats=["markdown"]
        )
    except Exception as e:
        error=str(e).lower()

        if "rate" in error or "429" in error:
            raise ScrapingError("Firecrawl rate Limit Reached")

        if any(phrase in error for phrase in ["blocked","forbidden","403","paywall"]):
            raise ScrapingError("This page is blocked,restricted or behind a paywall")

        raise ScrapingError("Firecrawl could not scrape this page")

    if not result:
        raise ScrapingError("Firecrawl Returned no Content for this page")

    markdown_text = result.markdown

    if not markdown_text or not markdown_text.strip():
        raise ScrapingError(
            "Firecrawl could not extract readable content from this page."
        )

    # V1ScrapeResponse exposes the page title directly; fall back to None
    # (caller falls back further, to the hostname) if the page had none.
    title = getattr(result, "title", None)
    if not title or not str(title).strip():
        title = None
    else:
        title = str(title).strip()

    return markdown_text, title

def getting_extra_data_through_tavily(url: str) -> str:

    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)

        response = tavily.search(
            query = f"What is this website/page about?Describe its purpose, organization/company, main services,topics, and important information:{url}",
            search_depth="basic",
            max_results=3,
        )

    except Exception:
        raise TavilyError(
            "Tavily could not retrieve information about this website."
        )

    results = response.get("results", [])

    if not results:
        raise TavilyError(
            "Tavily returned no information about this website."
        )

    descriptions = []

    for result in results:
        content = result.get("content")

        if content and content.strip():
            descriptions.append(content.strip())

    if not descriptions:
        raise TavilyError(
            "Tavily returned no readable information about this website."
        )

    return "\n\n".join(descriptions)

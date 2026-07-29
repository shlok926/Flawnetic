import asyncio
from backend.engines.crawler.crawler import FlawneticCrawler

async def main():
    crawler = FlawneticCrawler(
        base_url="https://demo.testfire.net",  # a known public demo banking app
        max_pages=10,
        max_depth=2,
        screenshot_dir="./test-screenshots"
    )
    site_graph = await crawler.crawl()
    print(f"Pages found: {site_graph.total_pages}")
    print(f"Total elements: {sum(len(p.elements) for p in site_graph.pages)}")
    for page in site_graph.pages:
        print(f"  {page.url} — {page.http_status} — {len(page.elements)} elements")
    return site_graph

if __name__ == "__main__":
    asyncio.run(main())

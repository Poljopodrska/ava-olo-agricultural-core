#!/usr/bin/env python3
"""
Test script to verify version badge implementation
Tests that the badge appears on all HTML pages
"""
import httpx
import asyncio
from bs4 import BeautifulSoup

# Test URLs - adjust base URL as needed
BASE_URL = "http://localhost:8080"
TEST_PAGES = [
    "/",  # Landing page
    "/dashboard",  # Dashboard
    "/cava-audit",  # CAVA audit
    "/cava-comprehensive-audit",  # New comprehensive audit
    "/chat-debug-audit",  # Chat debug
    "/diagnostics",  # Diagnostics
    "/openai-wizard",  # OpenAI wizard
    "/dashboards/env",  # ENV dashboard
]

async def test_page(url: str) -> dict:
    """Test if a page has the version badge"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            
            # Check if it's HTML
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                return {
                    "url": url,
                    "status": response.status_code,
                    "has_badge": False,
                    "reason": "Not HTML content"
                }
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for version badge div
            badge = soup.find('div', id='ava-olo-version-badge')
            
            # Also check for badge script
            has_script = 'ava-olo-version-badge' in response.text
            
            return {
                "url": url,
                "status": response.status_code,
                "has_badge": badge is not None or has_script,
                "reason": "Badge found" if (badge or has_script) else "Badge not found"
            }
            
    except Exception as e:
        return {
            "url": url,
            "status": "error",
            "has_badge": False,
            "reason": str(e)
        }

async def main():
    """Run all tests"""
    print("🔍 Testing Version Badge Implementation")
    print("=" * 50)
    print(f"Testing {len(TEST_PAGES)} pages at {BASE_URL}")
    print()
    
    results = []
    for path in TEST_PAGES:
        url = BASE_URL + path
        print(f"Testing {path}...", end=" ")
        result = await test_page(url)
        results.append(result)
        
        if result["has_badge"]:
            print("✅ Badge found")
        else:
            print(f"❌ {result['reason']}")
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    
    successful = sum(1 for r in results if r["has_badge"])
    total = len(results)
    percentage = (successful / total * 100) if total > 0 else 0
    
    print(f"Pages with badge: {successful}/{total} ({percentage:.0f}%)")
    
    if percentage == 100:
        print("\n✅ SUCCESS: Version badge is working on all pages!")
    else:
        print("\n❌ FAILED: Some pages are missing the version badge:")
        for result in results:
            if not result["has_badge"]:
                print(f"  - {result['url']}: {result['reason']}")

if __name__ == "__main__":
    asyncio.run(main())
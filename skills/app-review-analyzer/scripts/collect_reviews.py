#!/usr/bin/env python3
"""
App Review Collector Script
Collects and aggregates review data for specified apps from multiple sources.
"""

import argparse
import json
import sys
from datetime import datetime
from typing import List, Dict, Any

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Collect review data for mobile apps and platforms'
    )
    parser.add_argument(
        '--apps',
        required=True,
        help='Comma-separated list of app names to analyze'
    )
    parser.add_argument(
        '--output',
        default='reviews.json',
        help='Output JSON file path (default: reviews.json)'
    )
    parser.add_argument(
        '--platforms',
        default='appstore,playstore,trustpilot',
        help='Comma-separated platforms to search (default: appstore,playstore,trustpilot)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Analysis time range in days (default: 30, use 60 or 90 for low-review apps)'
    )
    return parser.parse_args()

def generate_search_queries(app_name: str, platforms: List[str]) -> Dict[str, List[str]]:
    """Generate search queries for each platform."""
    queries = {}
    
    if 'appstore' in platforms:
        queries['appstore'] = [
            f"{app_name} app reviews Apple App Store rating",
            f"site:apps.apple.com {app_name}"
        ]
    
    if 'playstore' in platforms:
        queries['playstore'] = [
            f"{app_name} Google Play Store reviews",
            f"site:play.google.com {app_name}"
        ]
    
    if 'trustpilot' in platforms:
        queries['trustpilot'] = [
            f"{app_name} Trustpilot reviews",
            f"site:trustpilot.com {app_name}"
        ]
    
    return queries

def create_review_template(app_name: str) -> Dict[str, Any]:
    """Create a template structure for app review data."""
    return {
        "app_name": app_name,
        "sources": {
            "apple_app_store": {
                "rating": None,
                "review_count": None,
                "url": None,
                "top_positive": [],
                "top_negative": []
            },
            "google_play_store": {
                "rating": None,
                "review_count": None,
                "url": None,
                "top_positive": [],
                "top_negative": []
            },
            "trustpilot": {
                "rating": None,
                "review_count": None,
                "url": None,
                "top_positive": [],
                "top_negative": []
            }
        },
        "common_themes": {
            "positive": [],
            "negative": []
        },
        "issue_categories": {}
    }

def get_current_date():
    """Get current date for validation."""
    return datetime.now()

def validate_date_references(date_str: str, current_year: int) -> Dict[str, Any]:
    """Validate that date references use correct year."""
    warnings = []
    if str(current_year - 1) in date_str and str(current_year) not in date_str:
        warnings.append(f"Warning: Date '{date_str}' references previous year. Verify this is intentional.")
    return {"warnings": warnings, "validated": date_str}

def main():
    args = parse_arguments()
    
    # CRITICAL: Get and display current date
    current_date = get_current_date()
    current_year = current_date.year
    
    # Calculate analysis time range
    from datetime import timedelta
    start_date = current_date - timedelta(days=args.days)
    
    print("=" * 60)
    print("DATE VERIFICATION & TIME RANGE")
    print("=" * 60)
    print(f"Current system date: {current_date.strftime('%B %d, %Y')}")
    print(f"Current year: {current_year}")
    print()
    print(f"📅 ANALYSIS TIME RANGE: {args.days} days")
    print(f"   Start Date: {start_date.strftime('%B %d, %Y')}")
    print(f"   End Date: {current_date.strftime('%B %d, %Y')}")
    print()
    print("⚠️  IMPORTANT:")
    print(f"   - All dates should use year {current_year}")
    print("   - Distinguish between:")
    print("     * Event occurrence date (when it happened)")
    print("     * Discussion date (when it's being talked about)")
    print()
    if args.days < 30:
        print("⚠️  WARNING: Less than 30 days may not provide sufficient data")
    elif args.days > 90:
        print("ℹ️  NOTE: Extended range (>90 days) - good for historical trends")
    else:
        print("ℹ️  Tip: If data is insufficient, consider extending to 60 or 90 days")
    print("=" * 60)
    print()
    
    # Parse app names
    apps = [app.strip() for app in args.apps.split(',')]
    platforms = [p.strip() for p in args.platforms.split(',')]
    
    # Initialize results with correct date and time range
    results = {
        "metadata": {
            "apps_analyzed": apps,
            "platforms_searched": platforms,
            "total_apps": len(apps),
            "collection_date": current_date.strftime('%Y-%m-%d'),
            "current_year": current_year,
            "analysis_days": args.days,
            "analysis_start_date": start_date.strftime('%Y-%m-%d'),
            "analysis_end_date": current_date.strftime('%Y-%m-%d'),
            "date_validation": "CHECKED - Verify all data uses correct year"
        },
        "apps": []
    }
    
    print(f"Collecting reviews for {len(apps)} app(s): {', '.join(apps)}")
    print(f"Platforms: {', '.join(platforms)}")
    print()
    
    for app in apps:
        print(f"Processing: {app}")
        
        app_data = create_review_template(app)
        queries = generate_search_queries(app, platforms)
        
        # Store search queries for manual execution
        app_data['search_queries'] = queries
        
        results['apps'].append(app_data)
        print(f"  - Generated {sum(len(q) for q in queries.values())} search queries")
    
    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print()
    print(f"Review collection template saved to: {args.output}")
    print()
    print("=" * 60)
    print("NEXT STEPS & REMINDERS")
    print("=" * 60)
    print(f"Analysis Time Range: {args.days} days")
    print(f"  From: {start_date.strftime('%Y-%m-%d')}")
    print(f"  To:   {current_date.strftime('%Y-%m-%d')}")
    print()
    print("1. Use the search queries in the JSON file to find review pages")
    print("2. Fetch review data using web_fetch or browser tools")
    print("3. Update the JSON file with collected data")
    print("4. Generate final report using the collected data")
    print()
    print("DATE VALIDATION CHECKLIST:")
    print(f"  [ ] All dates use year {current_year}")
    print("  [ ] Event dates are distinguished from discussion dates")
    print(f"  [ ] Analysis range ({args.days} days) is correctly calculated")
    print("  [ ] Reviews are within the specified date range")
    print("  [ ] Old events discussed recently are labeled as 'historical'")
    print()
    print("TIME RANGE GUIDANCE:")
    if args.days == 30:
        print("  - 30 days: Good for active apps with frequent reviews")
        print("  - If insufficient data, extend to 60 or 90 days")
    elif args.days == 60:
        print("  - 60 days: Balanced view for moderately active apps")
    elif args.days == 90:
        print("  - 90 days: Better for apps with fewer reviews")
        print("  - Provides quarterly trend view")
    else:
        print(f"  - {args.days} days: Custom range selected")
    print()
    print("COMMON PITFALLS TO AVOID:")
    print("  - Don't assume 'recent' search results are recent events")
    print("  - Check the actual event date, not just the article date")
    print("  - Old news can resurface and appear in recent searches")
    print("=" * 60)

if __name__ == '__main__':
    main()

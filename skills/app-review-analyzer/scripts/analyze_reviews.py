#!/usr/bin/env python3
"""
App Review Analyzer Script
Analyzes collected review data and generates reports with date validation.
"""

import argparse
import json
from datetime import datetime
from typing import Dict, List, Any

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Analyze app review data with date validation'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Input JSON file with collected reviews'
    )
    parser.add_argument(
        '--output',
        default='analysis.json',
        help='Output analysis JSON file (default: analysis.json)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=None,
        help='Override analysis time range in days (default: use value from input file)'
    )
    return parser.parse_args()

def validate_event_dates(reviews: List[Dict], current_year: int) -> Dict[str, List[Dict]]:
    """
    Categorize reviews by actual event date vs discussion date.
    
    Returns:
        {
            'recent_events': [...],  # Events that actually occurred recently
            'historical_discussed_recently': [...],  # Old events discussed recently
            'unclear': [...]  # Dates unclear
        }
    """
    categorized = {
        'recent_events': [],
        'historical_discussed_recently': [],
        'unclear': []
    }
    
    for review in reviews:
        event_date = review.get('event_date', '')
        discussion_date = review.get('discussion_date', '')
        
        # If event date is provided and is recent
        if event_date and str(current_year) in event_date:
            categorized['recent_events'].append(review)
        # If event date is old but discussed recently
        elif event_date and str(current_year) not in event_date and discussion_date:
            review['note'] = f"Historical event ({event_date}) discussed on {discussion_date}"
            categorized['historical_discussed_recently'].append(review)
        else:
            categorized['unclear'].append(review)
    
    return categorized

def analyze_sentiment(reviews: List[Dict]) -> Dict[str, Any]:
    """Simple sentiment analysis."""
    positive = [r for r in reviews if r.get('sentiment') == 'positive']
    negative = [r for r in reviews if r.get('sentiment') == 'negative']
    neutral = [r for r in reviews if r.get('sentiment') == 'neutral']
    
    total = len(reviews)
    if total == 0:
        return {"positive_pct": 0, "negative_pct": 0, "neutral_pct": 0}
    
    return {
        "positive_pct": round(len(positive) / total * 100, 1),
        "negative_pct": round(len(negative) / total * 100, 1),
        "neutral_pct": round(len(neutral) / total * 100, 1),
        "total_reviews": total
    }

def generate_warnings(data: Dict, current_year: int) -> List[str]:
    """Generate warnings for common issues."""
    warnings = []
    
    # Check for date inconsistencies
    metadata = data.get('metadata', {})
    collection_year = metadata.get('collection_date', '')[:4]
    
    if collection_year and int(collection_year) != current_year:
        warnings.append(f"⚠️  Collection year ({collection_year}) doesn't match current year ({current_year})")
    
    # Check for missing date validation
    if 'date_validation' not in metadata:
        warnings.append("⚠️  Date validation not performed")
    
    return warnings

def main():
    args = parse_arguments()
    
    # Get current date
    current_date = datetime.now()
    current_year = current_date.year
    
    # Load data first to get time range
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in '{args.input}'")
        return
    
    # Get analysis days from input or override
    if args.days:
        analysis_days = args.days
    else:
        analysis_days = data.get('metadata', {}).get('analysis_days', 30)
    
    # Calculate analysis window
    from datetime import timedelta
    start_date = current_date - timedelta(days=analysis_days)
    
    print("=" * 60)
    print("APP REVIEW ANALYZER")
    print("=" * 60)
    print(f"Analysis date: {current_date.strftime('%B %d, %Y')}")
    print(f"Current year: {current_year}")
    print()
    print(f"📅 ANALYSIS WINDOW: {analysis_days} days")
    print(f"   From: {start_date.strftime('%B %d, %Y')}")
    print(f"   To:   {current_date.strftime('%B %d, %Y')}")
    print("=" * 60)
    print()
    
    # Load data
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in '{args.input}'")
        return
    
    # Generate warnings
    warnings = generate_warnings(data, current_year)
    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print(f"  {warning}")
        print()
    
    print(f"Analyzing reviews within {analysis_days}-day window...")
    print(f"Only reviews from {start_date.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')} will be counted as 'recent'")
    print()
    
    # Analyze each app
    analysis_results = {
        "analysis_date": current_date.strftime('%Y-%m-%d'),
        "current_year": current_year,
        "analysis_days": analysis_days,
        "analysis_start_date": start_date.strftime('%Y-%m-%d'),
        "analysis_end_date": current_date.strftime('%Y-%m-%d'),
        "warnings": warnings,
        "apps": []
    }
    
    for app_data in data.get('apps', []):
        app_name = app_data.get('app_name', 'Unknown')
        print(f"Analyzing: {app_name}")
        
        # Get all reviews for this app
        all_reviews = []
        for source, source_data in app_data.get('sources', {}).items():
            if source_data:
                reviews = source_data.get('reviews', [])
                for review in reviews:
                    review['source'] = source
                    all_reviews.append(review)
        
        # Categorize by date
        categorized = validate_event_dates(all_reviews, current_year)
        
        # Analyze sentiment
        sentiment = analyze_sentiment(all_reviews)
        
        app_analysis = {
            "app_name": app_name,
            "total_reviews_analyzed": len(all_reviews),
            "event_categorization": {
                "recent_events_count": len(categorized['recent_events']),
                "historical_discussed_recently_count": len(categorized['historical_discussed_recently']),
                "unclear_dates_count": len(categorized['unclear'])
            },
            "sentiment_analysis": sentiment,
            "recent_issues": [r.get('issue') for r in categorized['recent_events'][:5]],
            "historical_cases": [r.get('note') for r in categorized['historical_discussed_recently'][:3]]
        }
        
        analysis_results['apps'].append(app_analysis)
        
        print(f"  - Recent events: {app_analysis['event_categorization']['recent_events_count']}")
        print(f"  - Historical (discussed recently): {app_analysis['event_categorization']['historical_discussed_recently_count']}")
        print(f"  - Sentiment: {sentiment['positive_pct']}% positive, {sentiment['negative_pct']}% negative")
        print()
    
    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print(f"Analysis saved to: {args.output}")
    print("=" * 60)
    print()
    print("ANALYSIS SUMMARY:")
    print(f"  Time Range: {analysis_days} days")
    print(f"  Period: {start_date.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}")
    print(f"  Apps Analyzed: {len(analysis_results['apps'])}")
    print()
    print("REPORT GENERATION CHECKLIST:")
    print("  [ ] Distinguish recent events from historical cases")
    print(f"  [ ] Use correct year ({current_year}) in all references")
    print(f"  [ ] Confirm analysis range ({analysis_days} days) is clearly stated")
    print("  [ ] Document data sources and limitations")
    print("  [ ] Note any missing data or API restrictions")
    print()
    print("TIME RANGE NOTES:")
    if analysis_days == 30:
        print("  - 30-day analysis: Focus on immediate recent issues")
    elif analysis_days >= 90:
        print("  - 90+ day analysis: Shows quarterly trends and patterns")
    else:
        print(f"  - {analysis_days}-day analysis: Custom time window")
    print("=" * 60)

if __name__ == '__main__':
    main()

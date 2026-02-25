---
name: app-review-analyzer
description: Collect and analyze user reviews for mobile apps and online platforms. Use when needing to gather review data from Apple App Store, Google Play Store, Trustpilot, and other review platforms to create comprehensive review analysis reports. Triggers on requests like "analyze app reviews", "collect reviews for [app name]", "review analysis report", or any task involving gathering and analyzing user feedback, ratings, and sentiment for applications.
version: 2.1
---

# Skill Version 2.1 - Updates

**New in v2.1:**
- ✅ Configurable time ranges (30/60/90+ days via `--days` parameter)
- ✅ Automatic date range calculation and display
- ✅ Better guidance on when to extend time ranges
- ✅ Time range validation in analysis scripts

**Previous v2.0:**
- ✅ Date verification and validation
- ✅ Distinguish recent events from historical discussions
- ✅ Common error prevention

---

# ⚠️ CRITICAL WARNINGS

## Common Errors to Avoid

### 1. Date/Year Confusion (MOST COMMON)
**Mistake:** Using the wrong year in reports  
**Example:** Writing "February 2025" when it's actually "February 2026"  
**Prevention:** 
- ALWAYS check system current date first
- The scripts will display current date prominently - VERIFY IT
- Use full dates (Month Day, Year) in all reports

### 2. Old Events Appearing Recent
**Mistake:** Reporting old events as "recent problems"  
**Example:** A March 2025 incident discussed in January 2026 media appears in "recent 30 days" search results  
**Prevention:**
- Check the ACTUAL event date, not just the article date
- Distinguish "when it happened" from "when it's being discussed"
- Label old events clearly: "Historical event (March 2025) discussed January 2026"

### 3. Google Play Data Unavailable
**Issue:** Google Play blocks direct access  
**Solution:** Use alternative sources (AppBrain, review articles) or note the limitation

### 4. Reddit Access Restricted
**Issue:** Reddit requires authentication  
**Solution:** Use search result snippets or quote from news articles discussing Reddit

---

# App Review Analyzer

Collect and analyze user reviews for mobile apps and online platforms across multiple review sources.

## Capabilities

- Search for app reviews across multiple platforms (App Store, Google Play, Trustpilot)
- Extract ratings, review counts, and user feedback
- Perform sentiment analysis on collected reviews
- Identify common issues and themes
- Generate comprehensive markdown reports with data tables
- Compare multiple apps side-by-side

## Workflow

### Step 0: Date Verification & Time Range Selection (CRITICAL)

**Before starting:**

1. **Check system current date** - Verify the year is correct
2. **Determine analysis time range:**
   - **Default:** 30 days (good for active apps with many reviews)
   - **Extended:** 60-90 days (better for apps with fewer reviews)
   - **Minimum recommended:** 90 days if 30-day data is insufficient
   
3. **Calculate date range:**
   ```
   End Date = Current Date
   Start Date = Current Date - [days]
   Example: Feb 25, 2026 - 90 days = Nov 27, 2025
   ```

4. **Use CORRECT YEAR in all queries and reports**

5. **Distinguish between:**
   - **Event occurrence date** - when something actually happened
   - **Discussion date** - when it's being talked about (may be old events)

**When to extend time range:**
- If 30-day search returns <3 reviews per app → extend to 60 or 90 days
- If user specifically requests longer historical view
- If analyzing seasonal trends or quarterly performance

**Common trap:** Old events discussed in recent media can appear as "recent" in search results. Always check the actual event date vs. the article/post date.

### Step 1: Identify Apps and Platforms

Determine:
- App names to analyze
- Target platforms (App Store, Google Play, Trustpilot, etc.)
- Review date range (if specified)
- Current date and correct year for all references

### Step 2: Collect Review Data

Use web_search to find review pages:
```
web_search: "[app name] app reviews Apple App Store Google Play rating"
web_search: "[app name] Trustpilot reviews"
web_search: "[app name] Google Play Store reviews"
```

Fetch detailed review pages:
```
web_fetch: [app store url]
web_fetch: [trustpilot url]
```

### Step 3: Extract Key Metrics with Date Validation

For each app, collect:
- Overall rating/score (out of 5)
- Total number of reviews/ratings
- Common positive themes
- Common negative themes
- Issue categories (payment, crashes, support, etc.)

**IMPORTANT - Date Validation:**
- Record the ACTUAL date of each review/incident
- Distinguish OLD events from RECENT events:
  - **Recent events:** Occurred within the analysis timeframe
  - **Old events discussed recently:** Note as "historical event, recently discussed"
- Cross-check dates: If a search result says "published: January 2026" but describes a March 2025 event, it's an old event

**Example:**
- ❌ WRONG: "Recent problem: ₱397M non-payment (March 2025)"
- ✅ CORRECT: "Historical case discussed recently: ₱397M non-payment (March 2025 event, January 2026 media coverage)"

### Step 4: Analyze Sentiment

Categorize mentions as:
- Positive (satisfied users, praise)
- Negative (complaints, issues)
- Neutral (factual statements)

Quantify: estimate percentage of positive vs negative sentiment

### Step 5: Create Report

Generate markdown report with:
1. Executive Summary
2. Individual App Analysis (tables for each app)
3. Cross-App Comparison
4. Key Findings and Recommendations

Use the report template in `assets/report-template.md`

## Report Structure

```markdown
# App Reviews Analysis Report

## Executive Summary
- Quick overview of apps analyzed
- Overall sentiment summary
- Key findings table

## Individual App Analysis
### [App Name]
- Ratings overview (table)
- Common topics (table with frequency)
- Detailed analysis (positive/negative breakdown)
- Issue categories

## Cross-App Comparison
- Rating comparison chart
- Issue frequency comparison
- Sentiment analysis summary

## Key Findings and Recommendations
- Critical findings
- Recommendations for users
- Recommendations for developers
```

## Scripts

### Step 1: Generate Collection Template

Use `scripts/collect_reviews.py` to create a data collection template with date validation:

```bash
# Default: 30 days
python3 scripts/collect_reviews.py --apps "app1,app2,app3" --output reviews.json

# Extended: 90 days (recommended for apps with fewer reviews)
python3 scripts/collect_reviews.py --apps "app1,app2,app3" --days 90 --output reviews.json
```

This will:
- Display current date and year (CRITICAL for accuracy)
- Calculate analysis time range (e.g., 90 days = Nov 27 - Feb 25)
- Generate search queries for each platform
- Create a structured JSON template
- Show date validation reminders

**Always check the displayed current year and time range before proceeding!**

### Step 2: Analyze Collected Data

Use `scripts/analyze_reviews.py` to analyze and categorize reviews:

```bash
# Use time range from collection step
python3 scripts/analyze_reviews.py --input reviews.json --output analysis.json

# Override with different time range
python3 scripts/analyze_reviews.py --input reviews.json --days 90 --output analysis.json
```

This will:
- Categorize reviews by actual event date
- Distinguish recent events from historical discussions
- Perform sentiment analysis
- Flag potential date issues

### Time Range Selection Guide

**When to use different time ranges:**

| Days | Best For | Example Use Case |
|------|----------|------------------|
| **30** | Active apps with frequent reviews | TikTok, Instagram, major games |
| **60** | Moderate activity apps | Regional casino apps, niche tools |
| **90** | Low-review apps, quarterly trends | New apps, less popular platforms |
| **180+** | Long-term trend analysis | Seasonal patterns, major incidents |

**Adjust if:**
- 30-day search returns <3 reviews per app → extend to 60 or 90 days
- Need quarterly/seasonal view → use 90 days
- Analyzing specific incident aftermath → use 30 days focused

### Date Validation Features

The scripts automatically:
1. **Check current date** and display prominently
2. **Calculate analysis window** based on --days parameter
3. **Categorize events** as:
   - Recent events (occurred within analysis timeframe)
   - Historical events discussed recently (old events, new coverage)
4. **Flag inconsistencies** (wrong years, missing dates, out-of-range events)
5. **Generate warnings** for common date-related errors

## Tips

- Multiple search queries may be needed for comprehensive data
- Trustpilot often has fewer reviews but more detailed feedback
- App Store ratings show overall satisfaction but individual reviews give context
- Google Play data may require additional search strategies
- Look for patterns across multiple review sources
- Note sample sizes - small review counts may not be representative
- Consider recency of reviews - older reviews may not reflect current app state

## Common Challenges & Solutions

### Challenge 1: Date/Year Confusion
**Problem:** Using wrong year in reports (e.g., writing 2025 when it's 2026)
**Solution:** 
- Always check system date first
- Create a "date check" reminder at the start of every task
- Use full dates (Month Day, Year) in reports

### Challenge 2: Old Events Appearing as Recent
**Problem:** Historical events discussed in recent media appear in "recent" search results
**Solution:**
- Always verify the ACTUAL event date vs. the article date
- Check if the content describes something that happened "on [date]"
- Label clearly: "Historical event (March 2025) discussed in January 2026 media"

### Challenge 3: Google Play Store Access
**Problem:** Google Play blocks direct scraping
**Solutions:**
- Use alternative sources: AppBrain, third-party review aggregators
- Search for "[app] Google Play reviews 2025/2026" for articles discussing ratings
- Note in report: "Google Play data limited due to access restrictions"

### Challenge 4: Reddit Access Restricted
**Problem:** Reddit blocks unauthenticated access
**Solutions:**
- Use search result snippets (descriptions often contain key info)
- Look for Reddit discussions quoted in news articles
- Note: "Reddit data limited to search summaries"

### Challenge 5: API Rate Limits
**Problem:** Search APIs (Brave) have rate limits
**Solutions:**
- Plan searches efficiently - batch related queries
- Use fetched data comprehensively before next search
- If rate limited, work with available data and note limitations

## Quality Checklist

Before finalizing report:
- [ ] All dates use correct year
- [ ] Time range is clearly stated and accurate
- [ ] Old events are distinguished from recent events
- [ ] Data sources are documented
- [ ] Missing data is noted with explanation
- [ ] Uncertainties are clearly stated

## Example Usage

### Example 1: Standard 30-Day Analysis (Active Apps)

**User:** "Analyze reviews for TikTok, Instagram, and Snapchat"

```bash
python3 scripts/collect_reviews.py --apps "TikTok,Instagram,Snapchat" --days 30 --output social_reviews.json
```

**Process:**
1. Generates 30-day analysis window
2. Searches App Store, Google Play, Trustpilot
3. Collects recent reviews
4. Creates sentiment analysis report

### Example 2: Extended 90-Day Analysis (Casino Apps)

**User:** "Analyze reviews for BingoPlus, CasinoPlus, PlayTime"

```bash
# Collect with 90-day window (better for lower-review apps)
python3 scripts/collect_reviews.py --apps "BingoPlus,CasinoPlus,PlayTime" --days 90 --output casino_reviews.json

# Analyze the collected data
python3 scripts/analyze_reviews.py --input casino_reviews.json --output casino_analysis.json
```

**Process:**
1. Sets 90-day window (Nov 27 - Feb 25 if current date is Feb 25)
2. Collects more comprehensive dataset
3. Distinguishes actual recent events from historical discussions
4. Generates final report with time range clearly stated

### Example 3: Manual Analysis with Date Awareness

**User:** "Analyze app reviews"

**Steps:**
1. **Check current date:** February 25, 2026
2. **Determine time range:** If apps have few reviews, use 90 days
3. **Calculate:** Feb 25, 2026 - 90 days = Nov 27, 2025
4. **Search:** "[app] reviews November 2025 February 2026"
5. **Verify:** Each review's actual date falls within Nov 27, 2025 - Feb 25, 2026
6. **Distinguish:** 
   - March 2025 event discussed in Jan 2026 = HISTORICAL
   - Feb 19, 2026 review = ACTUAL RECENT
7. **Report:** Clearly state "Analysis Period: Nov 27, 2025 - Feb 25, 2026"


"""Interactive dashboard for Web Crawler & Data Extraction Engine."""

import asyncio
import csv
import json
import sqlite3
from pathlib import Path

import streamlit as st

from crawler.async_engine import (
    AsyncWebCrawler,
    export_async_results,
)

from crawler.keyword_analyzer import (
    analyze_keyword_frequency,
    export_keyword_report,
)

from crawler.advanced_keyword_search import (
    search_keywords,
    export_search_report,
)


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
DATABASE_PATH = OUTPUT_DIR / "crawler_data.db"

ASYNC_JSON = OUTPUT_DIR / "async_crawler_results.json"
ASYNC_CSV = OUTPUT_DIR / "async_crawler_results.csv"
ASYNC_STATS = OUTPUT_DIR / "async_crawler_stats.json"

KEYWORD_JSON = OUTPUT_DIR / "keyword_frequency.json"
KEYWORD_CSV = OUTPUT_DIR / "keyword_frequency.csv"

SEARCH_JSON = OUTPUT_DIR / "advanced_keyword_search.json"
SEARCH_CSV = OUTPUT_DIR / "advanced_keyword_search.csv"


st.set_page_config(
    page_title="Web Crawler Dashboard",
    page_icon="🕷️",
    layout="wide"
)


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def load_database():
    """Load pages and crawl history from SQLite."""

    if not DATABASE_PATH.exists():
        return [], []

    connection = sqlite3.connect(str(DATABASE_PATH))
    connection.row_factory = sqlite3.Row

    try:
        pages = [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM crawled_pages ORDER BY crawled_at DESC"
            ).fetchall()
        ]

        history = [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM crawl_history ORDER BY started_at DESC"
            ).fetchall()
        ]

        return pages, history

    except sqlite3.Error as error:
        st.error(f"Database error: {error}")
        return [], []

    finally:
        connection.close()


# --------------------------------------------------
# FILE LOADERS
# --------------------------------------------------

def load_csv(filename):
    """Read a CSV report safely."""

    file_path = OUTPUT_DIR / filename

    if not file_path.exists():
        return []

    try:
        with file_path.open(
            "r",
            newline="",
            encoding="utf-8"
        ) as file:
            return list(csv.DictReader(file))

    except (OSError, csv.Error, UnicodeDecodeError):
        return []


def load_json(filename):
    """Read a JSON report safely."""

    file_path = OUTPUT_DIR / filename

    if not file_path.exists():
        return None

    try:
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    except (OSError, json.JSONDecodeError):
        return None


# --------------------------------------------------
# TABLE
# --------------------------------------------------

def show_table(records, empty_message):
    """Display records in a table."""

    if records:
        st.dataframe(
            records,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(empty_message)


# --------------------------------------------------
# ASYNC CRAWLER
# --------------------------------------------------

def run_async_crawler(
    urls,
    depth,
    max_pages,
    concurrency,
    delay,
    timeout,
    retries
):
    """Run the asynchronous crawler from Streamlit."""

    crawler = AsyncWebCrawler(
        max_depth=depth,
        max_pages=max_pages,
        concurrency=concurrency,
        delay=delay,
        timeout=timeout,
        retries=retries,
    )

    records, stats = asyncio.run(crawler.crawl(urls))

    export_async_results(
        records,
        stats,
        output_dir=str(OUTPUT_DIR)
    )

    return records, stats


def show_async_downloads(key_prefix):
    """Show async download buttons with unique keys."""

    st.subheader("Download Async Reports")

    col1, col2, col3 = st.columns(3)

    if ASYNC_JSON.exists():
        col1.download_button(
            "Download JSON",
            data=ASYNC_JSON.read_bytes(),
            file_name="async_crawler_results.json",
            mime="application/json",
            use_container_width=True,
            key=f"{key_prefix}_json_download"
        )

    if ASYNC_CSV.exists():
        col2.download_button(
            "Download CSV",
            data=ASYNC_CSV.read_bytes(),
            file_name="async_crawler_results.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"{key_prefix}_csv_download"
        )

    if ASYNC_STATS.exists():
        col3.download_button(
            "Download Stats",
            data=ASYNC_STATS.read_bytes(),
            file_name="async_crawler_stats.json",
            mime="application/json",
            use_container_width=True,
            key=f"{key_prefix}_stats_download"
        )


# --------------------------------------------------
# KEYWORD FREQUENCY ANALYSIS
# --------------------------------------------------

def run_keyword_analysis(records, top_n):
    """Run keyword frequency analysis and export reports."""

    report = analyze_keyword_frequency(
        records,
        top_n=top_n
    )

    export_keyword_report(
        report,
        output_dir=str(OUTPUT_DIR)
    )

    return report


def show_keyword_downloads():
    """Show keyword report download buttons."""

    st.subheader("Download Keyword Reports")

    col1, col2 = st.columns(2)

    if KEYWORD_JSON.exists():
        col1.download_button(
            "Download Keyword JSON",
            data=KEYWORD_JSON.read_bytes(),
            file_name="keyword_frequency.json",
            mime="application/json",
            key="keyword_json_download"
        )

    if KEYWORD_CSV.exists():
        col2.download_button(
            "Download Keyword CSV",
            data=KEYWORD_CSV.read_bytes(),
            file_name="keyword_frequency.csv",
            mime="text/csv",
            key="keyword_csv_download"
        )


# --------------------------------------------------
# ADVANCED KEYWORD SEARCH
# --------------------------------------------------

def run_advanced_search(records, keywords):
    """Run advanced keyword search and export reports."""

    report = search_keywords(
        records,
        keywords
    )

    export_search_report(
        report,
        output_dir=str(OUTPUT_DIR)
    )

    return report


def show_search_downloads():
    """Display advanced search report downloads."""

    st.subheader("Download Search Reports")

    col1, col2 = st.columns(2)

    if SEARCH_JSON.exists():
        col1.download_button(
            "Download Search JSON",
            data=SEARCH_JSON.read_bytes(),
            file_name="advanced_keyword_search.json",
            mime="application/json",
            key="advanced_search_json_download"
        )

    if SEARCH_CSV.exists():
        col2.download_button(
            "Download Search CSV",
            data=SEARCH_CSV.read_bytes(),
            file_name="advanced_keyword_search.csv",
            mime="text/csv",
            key="advanced_search_csv_download"
        )


# --------------------------------------------------
# MAIN DASHBOARD
# --------------------------------------------------

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    st.title("🕷️ Web Crawler Dashboard")

    st.caption(
        "Monitor website crawling, asynchronous crawling, "
        "SEO analysis, broken links, keyword frequency "
        "and advanced keyword search."
    )

    if st.button(
        "🔄 Refresh Dashboard",
        key="refresh_dashboard"
    ):
        st.rerun()

    # Load existing data
    pages, history = load_database()

    seo_reports = load_csv("seo_report.csv")
    broken_links = load_csv("broken_links.csv")
    crawler_stats = load_json("crawler_stats.json")

    async_records = load_json("async_crawler_results.json")
    async_stats = load_json("async_crawler_stats.json")

    if not isinstance(async_records, list):
        async_records = []

    if not isinstance(async_stats, dict):
        async_stats = None

    # Sidebar
    st.sidebar.title("Dashboard Menu")

    if DATABASE_PATH.exists():
        st.sidebar.success("Database connection available")
    else:
        st.sidebar.warning("Database not found")

    st.sidebar.write(f"Saved pages: {len(pages)}")
    st.sidebar.write(f"Crawl runs: {len(history)}")
    st.sidebar.write(f"Async pages: {len(async_records)}")

    # Main metrics
    total_pages = len(pages)

    successful_pages = sum(
        1 for page in pages
        if page.get("status_code") is not None
        and 200 <= int(page["status_code"]) < 300
    )

    failed_pages = sum(
        1 for page in pages
        if page.get("status_code") is not None
        and int(page["status_code"]) >= 400
    )

    broken_count = sum(
        1 for link in broken_links
        if link.get("status") in ("Broken", "Request Error")
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Pages", total_pages)
    col2.metric("Successful Pages", successful_pages)
    col3.metric("Failed Pages", failed_pages)
    col4.metric("Broken Links", broken_count)

    st.divider()

    # Tabs
    (
        tab1,
        tab2,
        tab3,
        tab4,
        tab5,
        tab6,
        tab7,
        tab8,
        tab9
    ) = st.tabs([
        "Overview",
        "Run Async Crawler",
        "Async Results",
        "Crawled Pages",
        "SEO Analysis",
        "Broken Links",
        "Crawl History",
        "Keyword Analysis",
        "Advanced Keyword Search"
    ])

    # --------------------------------------------------
    # TAB 1: OVERVIEW
    # --------------------------------------------------

    with tab1:

        st.subheader("Crawl Overview")

        if crawler_stats:

            stat_cols = st.columns(3)

            stat_cols[0].metric(
                "URLs Checked",
                crawler_stats.get("urls_checked", 0)
            )

            stat_cols[1].metric(
                "Failed Downloads",
                crawler_stats.get("failed_downloads", 0)
            )

            stat_cols[2].metric(
                "Execution Time",
                f"{crawler_stats.get('execution_time_seconds', 0)} sec"
            )

            st.subheader("Latest Synchronous Crawl Statistics")
            st.json(crawler_stats)

        else:
            st.info("Synchronous crawler statistics not found.")

        if async_stats:

            st.subheader("Latest Asynchronous Crawl Statistics")

            async_cols = st.columns(4)

            async_cols[0].metric(
                "Async Pages",
                async_stats.get("pages_visited", 0)
            )

            async_cols[1].metric(
                "URLs Checked",
                async_stats.get("urls_checked", 0)
            )

            async_cols[2].metric(
                "Failed Downloads",
                async_stats.get("failed_downloads", 0)
            )

            async_cols[3].metric(
                "Execution Time",
                f"{async_stats.get('execution_time_seconds', 0)} sec"
            )

        st.subheader("Latest Crawled Pages")

        latest_pages = [
            {
                "URL": page.get("url", ""),
                "Title": page.get("title", ""),
                "Status": page.get("status_code", ""),
                "Depth": page.get("depth", "")
            }
            for page in pages[:10]
        ]

        show_table(
            latest_pages,
            "No crawled pages available yet."
        )

    # --------------------------------------------------
    # TAB 2: RUN ASYNC CRAWLER
    # --------------------------------------------------

    with tab2:

        st.subheader("⚡ Asynchronous Web Crawler")

        st.write(
            "Enter website URLs and configure the crawler. "
            "The crawler will run asynchronously using aiohttp."
        )

        with st.form("async_crawler_form"):

            url_text = st.text_area(
                "Website URLs",
                value="https://example.com",
                help="Enter one URL per line.",
                key="async_url_input"
            )

            col1, col2 = st.columns(2)

            with col1:

                depth = st.number_input(
                    "Crawl Depth",
                    min_value=0,
                    max_value=10,
                    value=1,
                    step=1,
                    key="async_depth"
                )

                max_pages = st.number_input(
                    "Maximum Pages",
                    min_value=1,
                    max_value=500,
                    value=10,
                    step=1,
                    key="async_max_pages"
                )

                concurrency = st.number_input(
                    "Concurrency",
                    min_value=1,
                    max_value=20,
                    value=3,
                    step=1,
                    help="Maximum simultaneous page requests.",
                    key="async_concurrency"
                )

            with col2:

                delay = st.number_input(
                    "Request Delay (seconds)",
                    min_value=0.0,
                    max_value=30.0,
                    value=1.0,
                    step=0.5,
                    key="async_delay"
                )

                timeout = st.number_input(
                    "Timeout (seconds)",
                    min_value=1,
                    max_value=120,
                    value=15,
                    step=1,
                    key="async_timeout"
                )

                retries = st.number_input(
                    "Retries",
                    min_value=0,
                    max_value=5,
                    value=2,
                    step=1,
                    key="async_retries"
                )

            submitted = st.form_submit_button(
                "🚀 Start Async Crawling",
                use_container_width=True
            )

        if submitted:

            urls = [
                line.strip()
                for line in url_text.splitlines()
                if line.strip()
            ]

            if not urls:

                st.error("Please enter at least one website URL.")

            else:

                try:

                    with st.spinner(
                        "Async crawler is running. Please wait..."
                    ):

                        records, stats = run_async_crawler(
                            urls=urls,
                            depth=int(depth),
                            max_pages=int(max_pages),
                            concurrency=int(concurrency),
                            delay=float(delay),
                            timeout=int(timeout),
                            retries=int(retries)
                        )

                    async_records = records
                    async_stats = stats

                    st.success(
                        f"Crawling completed! "
                        f"{len(records)} pages were successfully collected."
                    )

                    st.subheader("Crawl Statistics")

                    result_cols = st.columns(4)

                    result_cols[0].metric(
                        "Pages Visited",
                        stats.get("pages_visited", 0)
                    )

                    result_cols[1].metric(
                        "URLs Checked",
                        stats.get("urls_checked", 0)
                    )

                    result_cols[2].metric(
                        "Failed Downloads",
                        stats.get("failed_downloads", 0)
                    )

                    result_cols[3].metric(
                        "Execution Time",
                        f"{stats.get('execution_time_seconds', 0)} sec"
                    )

                    st.json(stats)

                    st.subheader("Collected Pages")

                    show_table(
                        [
                            {
                                "URL": item.get("url"),
                                "Title": item.get("title"),
                                "Status": item.get("status_code"),
                                "Depth": item.get("depth")
                            }
                            for item in records
                        ],
                        "No pages were collected."
                    )

                    show_async_downloads("run_async")

                except Exception as error:

                    st.error(
                        f"Async crawling failed: {error}"
                    )

    # --------------------------------------------------
    # TAB 3: ASYNC RESULTS
    # --------------------------------------------------

    with tab3:

        st.subheader("Asynchronous Crawl Results")

        if async_stats:
            st.json(async_stats)

        if async_records:

            st.metric(
                "Total Async Pages",
                len(async_records)
            )

            async_display = [
                {
                    "URL": item.get("url", ""),
                    "Title": item.get("title", ""),
                    "Status": item.get("status_code", ""),
                    "Depth": item.get("depth", ""),
                    "Content Type": item.get("content_type", "")
                }
                for item in async_records
            ]

            show_table(
                async_display,
                "No async records available."
            )

            show_async_downloads("async_results")

        else:

            st.info(
                "No async results found. Open Run Async Crawler "
                "to start a crawl."
            )

    # --------------------------------------------------
    # TAB 4: CRAWLED PAGES
    # --------------------------------------------------

    with tab4:

        st.subheader("All Synchronous Crawled Pages")

        search = st.text_input(
            "Search by URL or title",
            key="page_search"
        )

        filtered_pages = []

        for page in pages:

            url = str(page.get("url", ""))
            title = str(page.get("title", ""))

            if (
                not search
                or search.lower() in url.lower()
                or search.lower() in title.lower()
            ):

                filtered_pages.append({
                    "URL": url,
                    "Title": title,
                    "Status": page.get("status_code"),
                    "Depth": page.get("depth"),
                    "Canonical": page.get("canonical", ""),
                    "Crawled At": page.get("crawled_at", "")
                })

        show_table(
            filtered_pages,
            "No matching pages found."
        )

    # --------------------------------------------------
    # TAB 5: SEO ANALYSIS
    # --------------------------------------------------

    with tab5:

        st.subheader("SEO Analysis Report")

        if seo_reports:

            st.metric("Pages Analyzed", len(seo_reports))

            show_table(
                seo_reports,
                "No SEO records available."
            )

            seo_file = OUTPUT_DIR / "seo_report.csv"

            if seo_file.exists():

                st.download_button(
                    "Download SEO CSV",
                    data=seo_file.read_bytes(),
                    file_name="seo_report.csv",
                    mime="text/csv",
                    key="seo_csv_download"
                )

        else:

            st.info("SEO report not found. Run main.py first.")

    # --------------------------------------------------
    # TAB 6: BROKEN LINKS
    # --------------------------------------------------

    with tab6:

        st.subheader("Broken Link Report")

        if broken_links:

            show_table(
                broken_links,
                "No broken link records found."
            )

            st.metric("Total Links Checked", len(broken_links))
            st.metric("Broken Links", broken_count)

            broken_file = OUTPUT_DIR / "broken_links.csv"

            if broken_file.exists():

                st.download_button(
                    "Download Broken Links CSV",
                    data=broken_file.read_bytes(),
                    file_name="broken_links.csv",
                    mime="text/csv",
                    key="broken_links_csv_download"
                )

        else:

            st.info("No broken-link report available yet.")

    # --------------------------------------------------
    # TAB 7: CRAWL HISTORY
    # --------------------------------------------------

    with tab7:

        st.subheader("Database Crawl History")

        if history:

            history_display = [
                {
                    "Started At": item.get("started_at"),
                    "Seed URLs": item.get("seed_urls"),
                    "Pages Visited": item.get("pages_visited"),
                    "URLs Checked": item.get("urls_checked"),
                    "Failed Downloads": item.get("failed_downloads"),
                    "Execution Time": item.get("execution_time_seconds")
                }
                for item in history
            ]

            show_table(
                history_display,
                "No crawl history available."
            )

        else:

            st.info(
                "No crawl history found. Run the synchronous crawler first."
            )

    # --------------------------------------------------
    # TAB 8: KEYWORD FREQUENCY ANALYSIS
    # --------------------------------------------------

    with tab8:

        st.subheader("🔍 Keyword Frequency Analysis")

        st.write(
            "Analyze frequently used keywords from crawled webpages."
        )

        st.info(
            "Run Async Crawler after updating parser.py so the "
            "saved records contain the readable text field."
        )

        top_n = st.slider(
            "Number of Top Keywords",
            min_value=5,
            max_value=50,
            value=10,
            step=5,
            key="keyword_top_n"
        )

        if st.button(
            "🔍 Analyze Keywords",
            key="analyze_keywords_button"
        ):

            if not async_records:

                st.warning(
                    "No async crawl data found. "
                    "Run Async Crawler first."
                )

            else:

                try:

                    keyword_report = run_keyword_analysis(
                        async_records,
                        top_n
                    )

                    st.session_state["keyword_report"] = keyword_report

                    st.success("Keyword analysis completed successfully!")

                except Exception as error:

                    st.error(
                        f"Keyword analysis failed: {error}"
                    )

        keyword_report = st.session_state.get("keyword_report")

        if keyword_report:

            st.divider()

            st.subheader("Keyword Statistics")

            metric1, metric2, metric3 = st.columns(3)

            metric1.metric(
                "Pages Analyzed",
                keyword_report.get("pages_analyzed", 0)
            )

            metric2.metric(
                "Total Words",
                keyword_report.get("total_words", 0)
            )

            metric3.metric(
                "Unique Keywords",
                keyword_report.get("unique_keywords", 0)
            )

            keyword_data = keyword_report.get(
                "top_keywords",
                []
            )

            if keyword_data:

                st.subheader("Top Keywords")

                show_table(
                    keyword_data,
                    "No keywords found."
                )

                st.subheader("Keyword Frequency Chart")

                chart_data = {
                    item["keyword"]: item["frequency"]
                    for item in keyword_data
                }

                st.bar_chart(chart_data)

                show_keyword_downloads()

            else:

                st.warning(
                    "No keywords found. Try crawling a page "
                    "with more readable text."
                )

        else:

            st.info(
                "Click Analyze Keywords to generate your keyword report."
            )

    # --------------------------------------------------
    # TAB 9: ADVANCED KEYWORD SEARCH
    # --------------------------------------------------

    with tab9:

        st.subheader("🔎 Advanced Keyword Search")

        st.write(
            "Search one or multiple keywords across "
            "all asynchronously crawled webpages."
        )

        st.info(
            "Run Async Crawler first to collect webpage data."
        )

        keyword_input = st.text_input(
            "Enter Keywords",
            placeholder="Example: Python, AI, machine learning",
            key="advanced_keyword_input"
        )

        st.caption(
            "Separate multiple keywords using commas."
        )

        if st.button(
            "🔍 Search Keywords",
            key="advanced_search_button",
            use_container_width=True
        ):

            keywords = [
                word.strip()
                for word in keyword_input.split(",")
                if word.strip()
            ]

            if not async_records:

                st.warning(
                    "No crawler data found. Run Async Crawler first."
                )

            elif not keywords:

                st.warning("Please enter at least one keyword.")

            else:

                try:

                    with st.spinner("Searching webpages..."):

                        search_report = run_advanced_search(
                            async_records,
                            keywords
                        )

                    st.session_state[
                        "advanced_search_report"
                    ] = search_report

                    st.success("Keyword search completed!")

                except Exception as error:

                    st.error(
                        f"Keyword search failed: {error}"
                    )

        search_report = st.session_state.get(
            "advanced_search_report"
        )

        if search_report:

            st.divider()

            st.subheader("Search Statistics")

            col1, col2 = st.columns(2)

            col1.metric(
                "Pages Matched",
                search_report.get("pages_matched", 0)
            )

            col2.metric(
                "Total Matches",
                search_report.get("total_matches", 0)
            )

            st.write(
                "Searched Keywords:",
                ", ".join(search_report.get("keywords", []))
            )

            results = search_report.get("results", [])

            if results:

                st.subheader("Matching Webpages")

                for result in results:

                    with st.expander(
                        f"{result['title']} "
                        f"({result['total_matches']} matches)"
                    ):

                        st.write("**URL:**", result["url"])

                        for item in result["matched_keywords"]:

                            st.write(
                                f"**{item['keyword']}** "
                                f"— {item['count']} matches"
                            )

                            for snippet in item["snippets"]:

                                st.caption(f"• {snippet}")

                st.subheader("Search Results Table")

                table_data = [
                    {
                        "Title": result["title"],
                        "URL": result["url"],
                        "Total Matches": result["total_matches"],
                        "Keywords": ", ".join(
                            item["keyword"]
                            for item in result["matched_keywords"]
                        )
                    }
                    for result in results
                ]

                st.dataframe(
                    table_data,
                    use_container_width=True,
                    hide_index=True
                )

                show_search_downloads()

            else:

                st.warning(
                    "No matching keywords found in crawled webpages."
                )

        else:

            st.info(
                "Enter keywords and click Search Keywords "
                "to see matching pages."
            )

    # --------------------------------------------------
    # FOOTER
    # --------------------------------------------------

    st.divider()

    st.caption(
        "Web Crawler & Data Extraction Engine | "
        "Python • Streamlit • SQLite • aiohttp • "
        "Keyword Frequency • Advanced Keyword Search"
    )


if __name__ == "__main__":
    main()

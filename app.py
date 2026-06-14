import calendar
import hashlib
import html as _html
import json
import os
import re
import time
import threading
import traceback
import concurrent.futures
from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, render_template, request

import requests
import feedparser
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Source configuration (also served to frontend via /api/sources)
# ---------------------------------------------------------------------------

SOURCES_CONFIG = [
    {"id": "INDEED_EU",          "label": "Indeed EU",         "method": "jobspy",    "stable": True,  "note": None},
    {"id": "LINKEDIN_EU",        "label": "LinkedIn",          "method": "jobspy",    "stable": False, "note": "Unstable – rate-limits quickly"},
    {"id": "GLASSDOOR",          "label": "Glassdoor",         "method": "link_only", "pull_status": "link_only", "stable": False, "note": "Scraper broken since Indeed/Glassdoor merger – visit site directly"},
    {"id": "GOOGLE_JOBS",        "label": "Google Jobs",       "method": "link_only", "pull_status": "link_only", "stable": False, "note": "Requires different implementation – visit site directly"},
    {"id": "GREENHOUSE",         "label": "Greenhouse",        "method": "api",       "stable": True,  "note": None},
    {"id": "KARRIERE_AT",        "label": "Karriere.at",       "method": "rss",       "stable": True,  "note": "Austria only"},
    {"id": "EUROJOBS",           "label": "EuroJobs",          "method": "link_only", "pull_status": "link_only", "stable": False, "note": "RSS unavailable – visit site directly"},
    {"id": "WORKING_IN_CONTENT", "label": "Working in Content","method": "link_only", "pull_status": "link_only", "stable": False, "note": "Browse manually"},
    {"id": "REMOTIVE",        "label": "Remotive",         "method": "api", "stable": True,  "note": "Remote roles only"},
    {"id": "ARBEITNOW",       "label": "Arbeitnow",        "method": "api", "stable": True,  "note": "Covers Germany, Austria, and Switzerland"},
    {"id": "JOBICY",          "label": "Jobicy",           "method": "api", "stable": True,  "note": "Remote roles only"},
    {"id": "WEWORKREMOTELY",  "label": "We Work Remotely", "method": "rss", "stable": True,  "note": "Remote roles only"},
]

# ---------------------------------------------------------------------------
# Company slugs – loaded from companies.json at runtime
# ---------------------------------------------------------------------------

COMPANIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "companies.json")


def _load_companies() -> dict:
    print(f"[DEBUG][GREENHOUSE] companies.json path: {COMPANIES_FILE}")
    try:
        with open(COMPANIES_FILE, "r") as f:
            data = json.load(f)
        slugs = [s for s in (data.get("greenhouse") or []) if isinstance(s, str) and s.strip()]
        print(f"[DEBUG][GREENHOUSE] loaded slugs from file: {slugs}")
        return {"greenhouse": slugs}
    except Exception as e:
        print(f"[DEBUG][GREENHOUSE] companies.json load error: {e}")
        traceback.print_exc()
        return {"greenhouse": []}

# ---------------------------------------------------------------------------
# Country mapping for Indeed / JobSpy
# ---------------------------------------------------------------------------

COUNTRY_MAP_INDEED = {
    # Western Europe (default)
    "austria":        "Austria",
    "belgium":        "Belgium",
    "france":         "France",
    "germany":        "Germany",
    "ireland":        "Ireland",
    "luxembourg":     "Luxembourg",
    "netherlands":    "Netherlands",
    "switzerland":    "Switzerland",
    "united_kingdom": "UK",
    # Northern Europe
    "denmark":        "Denmark",
    "estonia":        "Estonia",
    "finland":        "Finland",
    "iceland":        "Iceland",
    "latvia":         "Latvia",
    "lithuania":      "Lithuania",
    "norway":         "Norway",
    "sweden":         "Sweden",
    # Southern Europe
    "croatia":        "Croatia",
    "cyprus":         "Cyprus",
    "greece":         "Greece",
    "italy":          "Italy",
    "malta":          "Malta",
    "portugal":       "Portugal",
    "spain":          "Spain",
    # Central & Eastern Europe
    "czech_republic": "Czech Republic",
    "poland":         "Poland",
    "romania":        "Romania",
    "slovakia":       "Slovakia",
}

# LinkedIn cross-request rate-limit tracking
_linkedin_prev_zero = False
_linkedin_lock = threading.Lock()

# ---------------------------------------------------------------------------
# ATS location filter
# ---------------------------------------------------------------------------

_ATS_EXCLUDE = [
    "united states", "usa", "u.s.", "us,", "canada",
    "australia", "new zealand", "india", "brazil",
    "mexico", "singapore", "japan", "china", "hong kong",
    ", ca", ", ny", ", tx", ", wa", ", sf", "san francisco",
    "new york", "seattle", "chicago", "boston", "austin",
    "los angeles", "toronto", "vancouver",
]

_ATS_INCLUDE = {
    # Western Europe
    "austria":        ["austria", "wien", "vienna", "graz", "linz"],
    "belgium":        ["belgium", "brussels", "bruxelles", "antwerp", "ghent"],
    "france":         ["france", "paris", "lyon", "marseille", "toulouse", "bordeaux"],
    "germany":        ["germany", "deutschland", "berlin", "munich", "münchen", "hamburg", "frankfurt"],
    "ireland":        ["ireland", "dublin", "cork", "galway"],
    "luxembourg":     ["luxembourg"],
    "netherlands":    ["netherlands", "amsterdam", "rotterdam", "holland"],
    "switzerland":    ["switzerland", "zurich", "zürich", "geneva", "genève", "bern", "basel"],
    "united_kingdom": ["united kingdom", "england", "scotland", "wales", "london", "manchester", "edinburgh", "birmingham"],
    # Northern Europe
    "denmark":        ["denmark", "copenhagen", "københavn", "aarhus"],
    "estonia":        ["estonia", "tallinn", "tartu"],
    "finland":        ["finland", "helsinki", "tampere", "espoo"],
    "iceland":        ["iceland", "reykjavik"],
    "latvia":         ["latvia", "riga"],
    "lithuania":      ["lithuania", "vilnius", "kaunas"],
    "norway":         ["norway", "oslo", "bergen", "trondheim"],
    "sweden":         ["sweden", "stockholm", "gothenburg", "göteborg", "malmö"],
    # Southern Europe
    "croatia":        ["croatia", "zagreb", "split"],
    "cyprus":         ["cyprus", "nicosia"],
    "greece":         ["greece", "athens", "athina", "thessaloniki"],
    "italy":          ["italy", "rome", "milan", "milano", "turin", "torino", "florence"],
    "malta":          ["malta", "valletta"],
    "portugal":       ["portugal", "lisbon", "lisboa", "porto"],
    "spain":          ["spain", "madrid", "barcelona", "valencia", "seville", "españa"],
    # Central & Eastern Europe
    "czech_republic": ["czech", "prague", "praha", "brno"],
    "poland":         ["poland", "warsaw", "warszawa", "krakow", "kraków", "wroclaw"],
    "romania":        ["romania", "bucharest", "bucurești", "cluj"],
    "slovakia":       ["slovakia", "bratislava", "košice"],
    "remote":         ["remote", "worldwide", "anywhere", "global"],
}

_REMOTE_TERMS = {"remote", "worldwide", "anywhere"}



# ---------------------------------------------------------------------------
# EU country detection tables
# ---------------------------------------------------------------------------

# ISO 3166-1 alpha-2 codes for EU/EEA countries we track
_EU_ISO_CODES: dict[str, str] = {
    "at": "austria",      "be": "belgium",       "fr": "france",
    "de": "germany",      "ie": "ireland",       "lu": "luxembourg",
    "nl": "netherlands",  "ch": "switzerland",
    "gb": "united_kingdom", "uk": "united_kingdom",
    "dk": "denmark",      "ee": "estonia",       "fi": "finland",
    "is": "iceland",      "lv": "latvia",        "lt": "lithuania",
    "no": "norway",       "se": "sweden",
    "hr": "croatia",      "cy": "cyprus",        "gr": "greece",
    "it": "italy",        "mt": "malta",         "pt": "portugal",
    "es": "spain",
    "cz": "czech_republic", "pl": "poland",
    "ro": "romania",      "sk": "slovakia",
}

# Exact full country names (and common aliases) → country key
_EU_COUNTRY_NAMES: dict[str, str] = {
    "austria": "austria",         "belgium": "belgium",
    "france": "france",           "germany": "germany",
    "deutschland": "germany",     "ireland": "ireland",
    "luxembourg": "luxembourg",   "netherlands": "netherlands",
    "holland": "netherlands",     "switzerland": "switzerland",
    "united kingdom": "united_kingdom", "england": "united_kingdom",
    "scotland": "united_kingdom", "wales": "united_kingdom",
    "denmark": "denmark",         "estonia": "estonia",
    "finland": "finland",         "iceland": "iceland",
    "latvia": "latvia",           "lithuania": "lithuania",
    "norway": "norway",           "sweden": "sweden",
    "sverige": "sweden",          "croatia": "croatia",
    "cyprus": "cyprus",           "greece": "greece",
    "hellas": "greece",           "italy": "italy",
    "italia": "italy",            "malta": "malta",
    "portugal": "portugal",       "spain": "spain",
    "españa": "spain",            "czech republic": "czech_republic",
    "czechia": "czech_republic",  "poland": "poland",
    "polska": "poland",           "romania": "romania",
    "românia": "romania",         "slovakia": "slovakia",
}

# Major European cities → country key (lowercase keys, exact segment match)
_EU_CITIES: dict[str, str] = {
    # Austria
    "wien": "austria", "vienna": "austria", "graz": "austria",
    "linz": "austria", "salzburg": "austria", "innsbruck": "austria",
    "klagenfurt": "austria",
    # Belgium
    "brussels": "belgium", "bruxelles": "belgium", "brussel": "belgium",
    "antwerp": "belgium", "antwerpen": "belgium",
    "ghent": "belgium", "gent": "belgium", "liège": "belgium",
    # France
    "paris": "france", "lyon": "france", "marseille": "france",
    "toulouse": "france", "nice": "france", "nantes": "france",
    "strasbourg": "france", "montpellier": "france", "bordeaux": "france",
    "lille": "france",
    # Germany
    "berlin": "germany", "munich": "germany", "münchen": "germany",
    "hamburg": "germany", "frankfurt": "germany",
    "cologne": "germany", "köln": "germany",
    "düsseldorf": "germany", "stuttgart": "germany",
    "dortmund": "germany", "essen": "germany", "leipzig": "germany",
    "bremen": "germany", "dresden": "germany", "hannover": "germany",
    "nürnberg": "germany", "nuremberg": "germany",
    # Ireland
    "dublin": "ireland", "cork": "ireland", "galway": "ireland",
    "limerick": "ireland",
    # Luxembourg
    "luxembourg city": "luxembourg",
    # Netherlands
    "amsterdam": "netherlands", "rotterdam": "netherlands",
    "utrecht": "netherlands", "eindhoven": "netherlands",
    "den haag": "netherlands", "the hague": "netherlands",
    "groningen": "netherlands",
    # Switzerland
    "zurich": "switzerland", "zürich": "switzerland",
    "geneva": "switzerland", "genève": "switzerland",
    "bern": "switzerland", "basel": "switzerland",
    "lausanne": "switzerland",
    # United Kingdom
    "london": "united_kingdom", "manchester": "united_kingdom",
    "edinburgh": "united_kingdom", "birmingham": "united_kingdom",
    "bristol": "united_kingdom", "leeds": "united_kingdom",
    "glasgow": "united_kingdom", "liverpool": "united_kingdom",
    "sheffield": "united_kingdom", "belfast": "united_kingdom",
    "cardiff": "united_kingdom",
    # Denmark
    "copenhagen": "denmark", "københavn": "denmark",
    "aarhus": "denmark", "odense": "denmark",
    # Estonia
    "tallinn": "estonia", "tartu": "estonia",
    # Finland
    "helsinki": "finland", "tampere": "finland", "turku": "finland",
    "espoo": "finland", "vantaa": "finland",
    # Iceland
    "reykjavik": "iceland",
    # Latvia
    "riga": "latvia",
    # Lithuania
    "vilnius": "lithuania", "kaunas": "lithuania",
    # Norway
    "oslo": "norway", "bergen": "norway", "trondheim": "norway",
    # Sweden
    "stockholm": "sweden", "gothenburg": "sweden", "göteborg": "sweden",
    "malmö": "sweden", "uppsala": "sweden", "linköping": "sweden",
    "västerås": "sweden", "örebro": "sweden", "norrköping": "sweden",
    "helsingborg": "sweden", "jönköping": "sweden", "umeå": "sweden",
    "lund": "sweden", "borås": "sweden", "sundsvall": "sweden",
    # Croatia
    "zagreb": "croatia", "split": "croatia",
    # Cyprus
    "nicosia": "cyprus", "limassol": "cyprus",
    # Greece
    "athens": "greece", "αθήνα": "greece", "thessaloniki": "greece",
    "piraeus": "greece",
    # Italy
    "milan": "italy", "milano": "italy", "rome": "italy", "roma": "italy",
    "turin": "italy", "torino": "italy", "naples": "italy", "napoli": "italy",
    "bologna": "italy", "florence": "italy", "firenze": "italy",
    "venice": "italy", "venezia": "italy",
    # Malta
    "valletta": "malta",
    # Portugal
    "lisbon": "portugal", "lisboa": "portugal", "porto": "portugal",
    "braga": "portugal",
    # Spain
    "barcelona": "spain", "madrid": "spain", "valencia": "spain",
    "seville": "spain", "sevilla": "spain", "bilbao": "spain",
    "malaga": "spain", "málaga": "spain",
    # Czech Republic
    "prague": "czech_republic", "praha": "czech_republic",
    "brno": "czech_republic", "ostrava": "czech_republic",
    # Poland
    "warsaw": "poland", "warszawa": "poland",
    "krakow": "poland", "kraków": "poland",
    "wroclaw": "poland", "wrocław": "poland",
    "gdansk": "poland", "gdańsk": "poland",
    "poznan": "poland", "poznań": "poland",
    # Romania
    "bucharest": "romania", "bucurești": "romania",
    "cluj": "romania", "cluj-napoca": "romania",
    "iași": "romania", "timișoara": "romania",
    "brașov": "romania", "brasov": "romania",
    # Slovakia
    "bratislava": "slovakia", "košice": "slovakia",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _job_id(title: str, company: str) -> str:
    key = f"{title.lower().strip()}|{company.lower().strip()}"
    return hashlib.md5(key.encode()).hexdigest()


def _parse_date(val) -> str | None:
    if val is None:
        return None
    if isinstance(val, (int, float)) and val > 0:
        try:
            return datetime.fromtimestamp(int(val), tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    if hasattr(val, "strftime"):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, str) and val:
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(val[:19], fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


def _is_recent(val, hours_old: int) -> bool:
    """Return True if val (Unix ts, ISO string, or time.struct_time) is within hours_old hours."""
    if val is None:
        return True
    try:
        if isinstance(val, (int, float)):
            dt = datetime.fromtimestamp(int(val), tz=timezone.utc)
        elif isinstance(val, time.struct_time):
            dt = datetime.fromtimestamp(calendar.timegm(val), tz=timezone.utc)
        elif isinstance(val, str) and val:
            s = val[:19].replace("T", " ")
            try:
                dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                dt = datetime.strptime(val[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        elif isinstance(val, datetime):
            dt = val if val.tzinfo else val.replace(tzinfo=timezone.utc)
        else:
            return True
        return dt >= datetime.now(timezone.utc) - timedelta(hours=hours_old)
    except Exception:
        return True


def _keyword_in(keyword: str, *fields) -> bool:
    kw = keyword.lower()
    return any(kw in (f or "").lower() for f in fields)


def _strip_html(text: str) -> str:
    """Return plain text from an HTML string (handles entity-encoded HTML too)."""
    unescaped = _html.unescape(text)
    return re.sub(r"<[^>]+>", " ", unescaped)


_UNICODE_SPACES = re.compile(r"[\xa0  -​  　]+")

def _normalize_title(title: str) -> str:
    if not title:
        return title
    t = _UNICODE_SPACES.sub(" ", title)
    t = re.sub(r" {2,}", " ", t)
    return t.strip()


def _location_matches(location_str: str, countries: list[str]) -> bool:
    if not location_str:
        return True
    loc = location_str.lower()
    if "remote" in loc:
        return True
    for c in countries:
        terms = _ATS_INCLUDE.get(c, [c.replace("_", " ")])
        if any(t in loc for t in terms):
            return True
    return False


# ---------------------------------------------------------------------------
# Per-country location filter (Indeed EU / LinkedIn EU)
# ---------------------------------------------------------------------------

# Strip trailing parenthetical annotations before name/city/ISO lookup,
# e.g. "germany (remote)" → "germany", "berlin (hq)" → "berlin".
_TRAILING_PAREN = re.compile(r'\s*\([^)]*\)\s*$')

def _detect_location_countries(loc_str: str) -> list[str]:
    """Return sorted list of EU country keys found in loc_str.

    Algorithm (position-aware, segment-based):
    1. Split on ';' to handle multi-city strings (e.g. "Berlin, DE; Helsinki, FI").
    2. For each chunk, split on ',' into segments (trimmed, lowercased).
       Trailing parenthetical annotations are stripped before lookup
       (e.g. "germany (remote)" → "germany", "berlin (hq)" → "berlin").
    3. ISO check — LAST segment only (exactly 2 chars) → _EU_ISO_CODES lookup.
       Middle segments are never checked as ISO codes (fixes "Berlin, BE, DE" → BE
       is Berlin's state code, not Belgium; only DE at the end is checked).
    4. Full-name check — EVERY segment, EXACT match against _EU_COUNTRY_NAMES.
       (Whole segment must equal a country name; substrings don't count — fixes
       "New South Wales" not matching "wales".)
    5. City check — EVERY segment, exact lookup in _EU_CITIES.
    6. Cyprus override — if 'κύπρος' in chunk, add 'cyprus' and skip steps 3-5
       for that chunk (fixes "Κύπρος, GR" being misclassified as Greece).
    """
    if not loc_str:
        return []
    found: set[str] = set()
    for chunk in loc_str.lower().split(';'):
        chunk = chunk.strip()
        if not chunk:
            continue
        if 'κύπρος' in chunk:
            found.add('cyprus')
            continue
        segments = [_TRAILING_PAREN.sub('', s).strip()
                    for s in chunk.split(',') if s.strip()]
        segments = [s for s in segments if s]
        if not segments:
            continue
        # ISO code — LAST segment only (exactly 2 chars).
        # Middle segments are never checked, so "Berlin, BE, DE" correctly
        # matches DE (last) → Germany while BE (middle) is skipped.
        # A standalone "UK" is also handled since it IS the last (only) segment.
        last = segments[-1]
        if len(last) == 2:
            iso = _EU_ISO_CODES.get(last)
            if iso:
                found.add(iso)
        # Full country name + city — all segments
        for seg in segments:
            name = _EU_COUNTRY_NAMES.get(seg)
            if name:
                found.add(name)
            city = _EU_CITIES.get(seg)
            if city:
                found.add(city)
    return sorted(found)


def _detect_job_countries(job: dict) -> list[str]:
    """Return list of EU country keys for a job.

    Returns ['remote'] when the job has no locatable EU country but is remote.
    Returns [] when the job is onsite in a non-EU location (triggers Greenhouse
    exclusion downstream).
    """
    loc = (job.get('location') or '').strip()
    if not loc:
        return ['remote'] if job.get('is_remote') else []
    countries = _detect_location_countries(loc)
    if not countries and job.get('is_remote'):
        return ['remote']
    return countries


def location_matches_country(location: str, country_key: str) -> bool:
    """Return True if location string matches country_key (used for per-source pre-filter).

    Empty detected list → True (unknown location, don't filter out).
    """
    countries = _detect_location_countries(location)
    return not countries or country_key in countries


# ---------------------------------------------------------------------------
# Source fetchers
# ---------------------------------------------------------------------------

def _fetch_indeed(keywords: str, countries: list[str], hours_old: int,
                  results_per_source: int, title_only: bool,
                  work_models: set | None = None) -> tuple[list, list[str]]:
    if work_models is None:
        work_models = {"remote", "hybrid", "onsite"}
    try:
        from jobspy import scrape_jobs
    except ImportError:
        return [], ["Indeed EU: python-jobspy not installed"]

    remote_selected = "remote" in work_models
    target_countries = countries  # remote is no longer in countries list

    print(f"[DEBUG][INDEED] selected countries: {countries} work_models: {work_models}")

    # Build (country_name, is_remote) task list.
    # is_remote: True = remote filter on, False = onsite-only, None = no filter (mixed)
    onsite_only = work_models == {"onsite"}
    remote_only = work_models == {"remote"}
    is_remote_flag: bool | None = True if remote_only else (False if onsite_only else None)

    tasks: list[tuple[str, bool | None, str | None]] = []
    if target_countries:
        for c in target_countries:
            name = COUNTRY_MAP_INDEED.get(c)
            if name:
                tasks.append((name, is_remote_flag, c))
        if remote_selected and not remote_only:
            # Mixed: also add a remote-specific call (no country filter)
            tasks.append(("Germany", True, None))
    elif remote_selected:
        tasks.append(("Germany", True, None))

    def _scrape(country_name: str, is_remote: bool | None, country_key: str | None):
        scrape_params: dict = {
            "site_name": ["indeed"],
            "search_term": keywords,
            "country_indeed": country_name,
            "hours_old": int(hours_old),
            "results_wanted": int(results_per_source),
        }
        if is_remote is True:
            scrape_params["is_remote"] = True
        elif is_remote is False:
            scrape_params["is_remote"] = False
        print(
            f"[DEBUG][INDEED_EU] scraping: country={country_name!r} "
            f"search_term={keywords!r} hours_old={hours_old} "
            f"results_wanted={results_per_source} is_remote={is_remote}"
        )
        print(
            f"[DEBUG][INDEED_EU] params types: " +
            ", ".join(f"{k}=({v!r}, {type(v).__name__})" for k, v in scrape_params.items())
        )
        try:
            df = scrape_jobs(**scrape_params)
            raw_count = 0 if (df is None or df.empty) else len(df)
            print(f"[DEBUG][INDEED_EU] {country_name}: raw rows={raw_count}")
            if df is None or df.empty:
                if country_name == "Austria" and not is_remote:
                    print(
                        "[DEBUG][INDEED] Austria returned 0 rows (expected – "
                        "limited indeed.at coverage, Karriere.at is preferred)"
                    )
                    return [], True  # suppress: not a failure
                print(f"[DEBUG][INDEED_EU] scrape_jobs returned empty DataFrame for country: {country_name}")
                return [], True
            print(f"[DEBUG][INDEED_EU] {country_name}: df.shape={df.shape}")
            print(f"[DEBUG][INDEED_EU] {country_name}: first 3 rows=\n{df.head(3).to_string()}")
            results = []
            for _, row in df.iterrows():
                title = str(row.get("title", "") or "")
                company = str(row.get("company", "") or "")
                if title_only and not _keyword_in(keywords, title):
                    continue
                location  = str(row.get("location", "") or "")
                full_desc = str(row.get("description", "") or "")
                results.append({
                    "id": _job_id(title, company),
                    "title": title,
                    "company": company,
                    "location": location,
                    "source": "INDEED_EU",
                    "source_label": "Indeed EU",
                    "url": str(row.get("job_url", "") or ""),
                    "date_posted": _parse_date(row.get("date_posted")),
                    "also_on": [],
                    "is_remote": bool(row.get("is_remote", False)),
                    "job_type": str(row.get("job_type", "") or ""),
                    "is_hybrid": _detect_hybrid_text(title, location, full_desc),
                    "description": full_desc[:500],
                })
            if country_key:
                kept, dropped_locs = [], []
                for job in results:
                    loc = job.get("location", "")
                    if not loc or job.get("is_remote") or location_matches_country(loc, country_key):
                        kept.append(job)
                    else:
                        dropped_locs.append(loc)
                print(f"[DEBUG][INDEED_EU] {country_name}: {len(results)} raw → {len(kept)} after country filter")
                if dropped_locs:
                    print(f"[DEBUG][INDEED_EU] dropped example locations: {dropped_locs[:3]}")
                if country_key == "austria" and dropped_locs:
                    print(f"[DEBUG][INDEED_EU] Austria dropped locations: {dropped_locs[:5]}")
                results = kept
            return results, True
        except Exception as e:
            print(f"[DEBUG][INDEED_EU] {country_name}: exception – {e}")
            traceback.print_exc()
            return [], False

    jobs = []
    successes = 0
    failures = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(_scrape, cn, ir, ck) for cn, ir, ck in tasks]
        for f in concurrent.futures.as_completed(futures):
            result, ok = f.result()
            jobs.extend(result)
            if ok:
                successes += 1
            else:
                failures += 1

    warnings = []
    if successes == 0 and failures > 0:
        warnings.append(
            "Indeed EU – could not reach any country job boards. "
            "The source may be temporarily unavailable."
        )
    return jobs, warnings


def _fetch_linkedin(keywords: str, countries: list[str], hours_old: int,
                    results_per_source: int, title_only: bool,
                    work_models: set | None = None) -> tuple[list, list[str], bool]:
    global _linkedin_prev_zero
    if work_models is None:
        work_models = {"remote", "hybrid", "onsite"}

    try:
        from jobspy import scrape_jobs
    except ImportError:
        return [], ["LinkedIn: python-jobspy not installed"], False

    remote_selected = "remote" in work_models

    # Build (location, is_remote, country_key) task list – one call per country.
    remote_only = work_models == {"remote"}
    tasks: list[tuple[str, bool, str | None]] = []
    for c in countries:
        name = COUNTRY_MAP_INDEED.get(c)
        if name:
            tasks.append((name, remote_only, c))
    if remote_selected:
        tasks.append(("Europe", True, None))
    if not tasks:
        tasks.append(("Europe", False, None))

    def _scrape_li(location: str, is_remote: bool, country_key: str | None):
        scrape_params: dict = {
            "site_name": ["linkedin"],
            "search_term": keywords,
            "location": location,
            "hours_old": hours_old,
            "results_wanted": results_per_source,
        }
        if is_remote:
            scrape_params["is_remote"] = True
        print(f"[DEBUG][LINKEDIN] calling scrape_jobs: location={location!r} is_remote={is_remote}")
        t0 = time.time()
        try:
            df = scrape_jobs(**scrape_params)
            elapsed = time.time() - t0
            if df is None or df.empty:
                if elapsed > 15:
                    print(f"[DEBUG][LINKEDIN] {location}: took {elapsed:.1f}s, 0 results – possible rate-limit")
                    return [], True, True
                return [], True, False
            results = []
            for _, row in df.iterrows():
                title = str(row.get("title", "") or "")
                company = str(row.get("company", "") or "")
                if title_only and not _keyword_in(keywords, title):
                    continue
                location  = str(row.get("location", "") or "")
                full_desc = str(row.get("description", "") or "")
                results.append({
                    "id": _job_id(title, company),
                    "title": title,
                    "company": company,
                    "location": location,
                    "source": "LINKEDIN_EU",
                    "source_label": "LinkedIn",
                    "url": str(row.get("job_url", "") or ""),
                    "date_posted": _parse_date(row.get("date_posted")),
                    "also_on": [],
                    "is_remote": bool(row.get("is_remote", False)),
                    "job_type": str(row.get("job_type", "") or ""),
                    "is_hybrid": _detect_hybrid_text(title, location, full_desc),
                    "description": full_desc[:500],
                })
            if country_key:
                kept, dropped_locs = [], []
                for job in results:
                    loc = job.get("location", "")
                    if not loc or job.get("is_remote") or location_matches_country(loc, country_key):
                        kept.append(job)
                    else:
                        dropped_locs.append(loc)
                print(f"[DEBUG][LINKEDIN] {location}: {len(results)} raw → {len(kept)} after country filter")
                if dropped_locs:
                    print(f"[DEBUG][LINKEDIN] dropped example locations: {dropped_locs[:3]}")
                results = kept
            return results, True, False
        except Exception as e:
            err = str(e).lower()
            is_rl = any(kw in err for kw in ("rate", "429", "blocked"))
            if is_rl:
                print(f"[DEBUG][LINKEDIN] {location}: rate-limit detected in exception – {e}")
            else:
                print(f"[DEBUG][LINKEDIN] {location}: exception – {e}")
            return [], False, is_rl

    jobs = []
    successes = 0
    failures = 0
    any_rate_limited = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(_scrape_li, loc, ir, ck) for loc, ir, ck in tasks]
        for f in concurrent.futures.as_completed(futures):
            result, ok, rl = f.result()
            jobs.extend(result)
            if rl:
                any_rate_limited = True
            if ok:
                successes += 1
            else:
                failures += 1

    warnings = []
    if not any_rate_limited and successes == 0 and failures > 0:
        warnings.append(
            "LinkedIn rate-limited or unavailable – results may be incomplete."
        )
    return jobs, warnings, any_rate_limited


def _fetch_greenhouse(keywords: str, countries: list[str], title_only: bool, slugs: list[str], hours_old: int = 168) -> tuple[list, list[str]]:
    print(f"[DEBUG][GREENHOUSE] starting fetch")
    print(f"[DEBUG][GREENHOUSE] slug count: {len(slugs)}")
    print(f"[DEBUG][GREENHOUSE] slugs: {slugs}")
    if not slugs:
        print("[DEBUG][GREENHOUSE] slug list is EMPTY – check companies.json")
        return [], []
    jobs = []
    session = requests.Session()
    session.headers["User-Agent"] = "EuroJobSearch/1.0"

    def _fetch_slug(slug):
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
        print(f"[DEBUG][GREENHOUSE] fetching: {url}")
        try:
            resp = session.get(url, timeout=10)
            print(f"[DEBUG][GREENHOUSE] {slug}: HTTP {resp.status_code}")
            if resp.status_code != 200:
                print(f"[DEBUG][GREENHOUSE] {slug}: skipping non-200")
                return [], False, 0
            resp.raise_for_status()
            data = resp.json()
            all_jobs = data.get("jobs", [])
            print(f"[DEBUG][GREENHOUSE] {slug}: {len(all_jobs)} jobs before filter")
            sample_locs = [j.get("location", {}).get("name", "") for j in all_jobs[:3]]
            print(f"[DEBUG][GREENHOUSE] {slug}: sample locations: {sample_locs}")
            raw_results = []
            for job in all_jobs:
                title    = job.get("title", "") or ""
                location = job.get("location", {}).get("name", "") or ""
                content  = job.get("content", "") or ""
                content_text = _strip_html(content)
                if not _keyword_in(keywords, title) and (title_only or not _keyword_in(keywords, content_text)):
                    continue
                updated = job.get("updated_at") or job.get("created_at")
                if not _is_recent(updated, hours_old):
                    continue
                raw_results.append({
                    "id": _job_id(title, slug),
                    "title": title,
                    "company": data.get("name", slug),
                    "location": location,
                    "source": "GREENHOUSE",
                    "source_label": "Greenhouse",
                    "url": job.get("absolute_url", ""),
                    "date_posted": _parse_date(updated),
                    "also_on": [],
                    "is_remote": "remote" in location.lower(),
                    "is_hybrid": _detect_hybrid_text(title, location, content),
                    "description": content[:500],
                })
            return raw_results, True, len(raw_results)
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            print(f"[DEBUG][GREENHOUSE] {slug}: HTTP {status} (skipping)")
            return [], False, 0
        except Exception as e:
            print(f"[DEBUG][GREENHOUSE] {slug}: EXCEPTION: {e}")
            traceback.print_exc()
            return [], False, 0

    successes = 0
    failures = 0
    total_raw = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_fetch_slug, s): s for s in slugs}
        for f in concurrent.futures.as_completed(futures):
            result, ok, raw_count = f.result()
            jobs.extend(result)
            total_raw += raw_count
            if ok:
                successes += 1
            else:
                failures += 1

    print(f"[DEBUG][GREENHOUSE] total slugs: {len(slugs)}")
    print(f"[DEBUG][GREENHOUSE] successful: {successes}")
    print(f"[DEBUG][GREENHOUSE] total raw jobs: {total_raw}")
    print(f"[DEBUG][GREENHOUSE] after filter: {len(jobs)}")
    print(f"[DEBUG][GREENHOUSE] sample locations kept: {[j.get('location') for j in jobs[:5]]}")

    warnings = []
    if successes == 0 and failures > 0:
        warnings.append(
            "Greenhouse – could not reach any company career pages. "
            "You can update the company list via the Target companies section."
        )
    return jobs, warnings


# NOTE: Glassdoor and Google Jobs via JobSpy have proven unreliable for EU
# searches – they frequently return 0 rows or raise exceptions. Both may need
# to be replaced with a direct scraper or a different data source.
def _fetch_glassdoor(keywords: str, countries: list[str], hours_old: int,
                      results_per_source: int, title_only: bool,
                      work_models: set | None = None) -> tuple[list, list[str]]:
    if work_models is None:
        work_models = {"remote", "hybrid", "onsite"}
    try:
        from jobspy import scrape_jobs
    except ImportError:
        return [], ["Glassdoor: python-jobspy not installed"]

    remote_selected = "remote" in work_models
    target_countries = countries

    tasks: list[tuple[str, bool]] = []
    if target_countries:
        for c in target_countries:
            name = COUNTRY_MAP_INDEED.get(c)
            if name:
                tasks.append((name, False))
        if remote_selected:
            tasks.append(("Germany", True))
    elif remote_selected:
        tasks.append(("Germany", True))

    def _scrape(location: str, is_remote: bool):
        scrape_params: dict = {
            "site_name": ["glassdoor"],
            "search_term": keywords,
            "location": location,
            "hours_old": int(hours_old),
            "results_wanted": int(results_per_source),
        }
        if is_remote:
            scrape_params["is_remote"] = True
        print(f"[DEBUG][GLASSDOOR] scraping: location={location!r} is_remote={is_remote}")
        try:
            df = scrape_jobs(**scrape_params)
            raw_count = 0 if (df is None or df.empty) else len(df)
            print(f"[DEBUG][GLASSDOOR] {location}: raw rows={raw_count}")
            if df is None or df.empty:
                return [], True
            results = []
            for _, row in df.iterrows():
                title = str(row.get("title", "") or "")
                company = str(row.get("company", "") or "")
                if title_only and not _keyword_in(keywords, title):
                    continue
                results.append({
                    "id": _job_id(title, company),
                    "title": title,
                    "company": company,
                    "location": str(row.get("location", "") or ""),
                    "source": "GLASSDOOR",
                    "source_label": "Glassdoor",
                    "url": str(row.get("job_url", "") or ""),
                    "date_posted": _parse_date(row.get("date_posted")),
                    "also_on": [],
                    "is_remote": bool(row.get("is_remote", False)),
                })
            return results, True
        except Exception as e:
            print(f"[DEBUG][GLASSDOOR] {location}: exception – {e}")
            print(f"[DEBUG][GLASSDOOR] {location}: traceback – {traceback.format_exc()}")
            return [], False

    jobs = []
    successes = 0
    failures = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(_scrape, cn, ir) for cn, ir in tasks]
        for f in concurrent.futures.as_completed(futures):
            result, ok = f.result()
            jobs.extend(result)
            if ok:
                successes += 1
            else:
                failures += 1

    warnings = []
    if successes == 0 and failures > 0:
        warnings.append("Glassdoor – could not reach the job board. It may be temporarily unavailable.")
    return jobs, warnings


def _fetch_google_jobs(keywords: str, countries: list[str], hours_old: int,
                       results_per_source: int, title_only: bool,
                       work_models: set | None = None) -> tuple[list, list[str]]:
    if work_models is None:
        work_models = {"remote", "hybrid", "onsite"}
    try:
        from jobspy import scrape_jobs
    except ImportError:
        return [], ["Google Jobs: python-jobspy not installed"]

    remote_selected = "remote" in work_models
    target_countries = countries

    tasks: list[tuple[str, bool]] = []
    if target_countries:
        for c in target_countries:
            name = COUNTRY_MAP_INDEED.get(c)
            if name:
                tasks.append((name, False))
        if remote_selected:
            tasks.append(("Europe", True))
    elif remote_selected:
        tasks.append(("Europe", True))

    def _scrape(location: str, is_remote: bool):
        scrape_params: dict = {
            "site_name": ["google"],
            "search_term": keywords,
            "location": location,
            "hours_old": int(hours_old),
            "results_wanted": int(results_per_source),
        }
        if is_remote:
            scrape_params["is_remote"] = True
        print(f"[DEBUG][GOOGLE_JOBS] scraping: location={location!r} is_remote={is_remote}")
        try:
            df = scrape_jobs(**scrape_params)
            raw_count = 0 if (df is None or df.empty) else len(df)
            print(f"[DEBUG][GOOGLE_JOBS] {location}: raw rows={raw_count}")
            if df is None or df.empty:
                return [], True
            results = []
            for _, row in df.iterrows():
                title = str(row.get("title", "") or "")
                company = str(row.get("company", "") or "")
                if title_only and not _keyword_in(keywords, title):
                    continue
                results.append({
                    "id": _job_id(title, company),
                    "title": title,
                    "company": company,
                    "location": str(row.get("location", "") or ""),
                    "source": "GOOGLE_JOBS",
                    "source_label": "Google Jobs",
                    "url": str(row.get("job_url", "") or ""),
                    "date_posted": _parse_date(row.get("date_posted")),
                    "also_on": [],
                    "is_remote": bool(row.get("is_remote", False)),
                })
            return results, True
        except Exception as e:
            print(f"[DEBUG][GOOGLE_JOBS] {location}: exception – {e}")
            print(f"[DEBUG][GOOGLE_JOBS] {location}: traceback – {traceback.format_exc()}")
            return [], False

    jobs = []
    successes = 0
    failures = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(_scrape, cn, ir) for cn, ir in tasks]
        for f in concurrent.futures.as_completed(futures):
            result, ok = f.result()
            jobs.extend(result)
            if ok:
                successes += 1
            else:
                failures += 1

    warnings = []
    if successes == 0 and failures > 0:
        warnings.append("Google Jobs – could not reach the job board. It may be temporarily unavailable.")
    return jobs, warnings


def _fetch_karriere_at(keywords: str, hours_old: int = 168) -> tuple[list, list[str]]:
    kw_quoted = requests.utils.quote(keywords)
    rss_url = f"https://www.karriere.at/jobs/rss?keywords={kw_quoted}&location=Austria"
    print(f"[DEBUG][KARRIERE_AT] RSS URL: {rss_url}")

    def _build_job(title: str, url: str, company: str = "", date_val=None) -> dict:
        return {
            "id": _job_id(title, "karriere.at"),
            "title": title,
            "company": company,
            "location": "Austria",
            "source": "KARRIERE_AT",
            "source_label": "Karriere.at",
            "url": url,
            "date_posted": _parse_date(date_val),
            "also_on": [],
            "is_remote": "remote" in title.lower(),
        }

    try:
        feed = feedparser.parse(rss_url)
        print(f"[DEBUG][KARRIERE_AT] RSS entries: {len(feed.entries)}")

        if feed.entries:
            jobs = []
            for entry in feed.entries:
                title = entry.get("title", "")
                pub = entry.get("published_parsed")
                pub_dt = (
                    datetime.fromtimestamp(calendar.timegm(pub), tz=timezone.utc)
                    if pub else None
                )
                if pub_dt and not _is_recent(pub_dt, hours_old):
                    continue
                jobs.append(_build_job(
                    title,
                    entry.get("link", ""),
                    entry.get("author", ""),
                    pub_dt,
                ))
            return jobs, []

        # RSS returned nothing – probe the URL to understand why
        try:
            probe = requests.get(
                rss_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            print(f"[DEBUG][KARRIERE_AT] Direct HTTP status: {probe.status_code}")
        except Exception as probe_err:
            print(f"[DEBUG][KARRIERE_AT] Direct HTTP failed: {probe_err}")

        # BeautifulSoup HTML fallback
        try:
            from bs4 import BeautifulSoup  # type: ignore
            html_url = (
                f"https://www.karriere.at/jobs/"
                f"{requests.utils.quote(keywords, safe='')}"
                f"/%C3%B6sterreich"
            )
            print(f"[DEBUG][KARRIERE_AT] BeautifulSoup fallback URL: {html_url}")
            resp = requests.get(
                html_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            print(f"[DEBUG][KARRIERE_AT] HTML status: {resp.status_code}")
            soup = BeautifulSoup(resp.text, "html.parser")

            # Diagnostic: log all hrefs containing '/jobs/'
            job_hrefs = [a["href"] for a in soup.find_all("a", href=True) if "/jobs/" in a.get("href", "")]
            print(f"[DEBUG][KARRIERE_AT] /jobs/ hrefs found: {len(job_hrefs)}")
            print(f"[DEBUG][KARRIERE_AT] samples: {job_hrefs[:5]}")

            # Try patterns in order; use the first that returns results
            _PATTERNS = [
                (r"/jobs/[^/]+/\d{4,}",  "pattern-1: /jobs/slug/NNN"),
                (r"/job/[^/]+/\d{4,}",   "pattern-2: /job/slug/NNN"),
                (r"/stelle/[^/]+",        "pattern-3: /stelle/slug"),
                (r"/jobs/\d{4,}",         "pattern-4: /jobs/NNN"),
            ]

            seen_urls: set[str] = set()
            unique_jobs: list[tuple[str, str]] = []
            pattern_used = "none"

            for _pat, _label in _PATTERNS:
                _re = re.compile(_pat)
                candidates: list[tuple[str, str]] = []
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if not _re.search(href):
                        continue
                    full_url = href if href.startswith("http") else "https://www.karriere.at" + href
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    title = a.get_text(strip=True)
                    if not title:
                        slug = href.rstrip("/").split("/")[-1]
                        title = slug.replace("-", " ").title()
                    candidates.append((title, full_url))
                if candidates:
                    unique_jobs = candidates
                    pattern_used = _label
                    break

            # Fallback: keep ALL /jobs/ hrefs when every pattern returned 0
            if not unique_jobs and job_hrefs:
                pattern_used = "fallback: all /jobs/ hrefs"
                for href in job_hrefs:
                    full_url = href if href.startswith("http") else "https://www.karriere.at" + href
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)
                    slug = href.rstrip("/").split("/")[-1]
                    title = slug.replace("-", " ").title()
                    unique_jobs.append((title, full_url))

            print(f"[DEBUG][KARRIERE_AT] pattern used: {pattern_used}")
            print(f"[DEBUG][KARRIERE_AT] URLs after pattern: {len(unique_jobs)}")

            jobs = [_build_job(t, h) for t, h in unique_jobs[:50]]
            print(f"[DEBUG][KARRIERE_AT] HTML fallback extracted {len(jobs)} jobs")
            if jobs:
                return jobs, []
            return [], ["Karriere.at – RSS and HTML fallback returned no results for this keyword."]

        except ImportError:
            print("[DEBUG][KARRIERE_AT] BeautifulSoup not available – skipping HTML fallback")
            return [], [
                "Karriere.at – RSS feed returned no results. "
                "Install beautifulsoup4 to enable the HTML fallback."
            ]
        except Exception as bs_err:
            print(f"[DEBUG][KARRIERE_AT] HTML fallback error: {bs_err}")
            return [], [f"Karriere.at – RSS unavailable and HTML fallback failed: {bs_err}"]

    except Exception as e:
        return [], [f"Karriere.at: {e}"]


def _fetch_eurojobs(keywords: str) -> tuple[list, list[str]]:
    url = f"https://www.eurojobs.com/search-results/rss/?keywords={requests.utils.quote(keywords)}"
    print(f"[DEBUG][EUROJOBS] RSS URL: {url}")
    try:
        feed = feedparser.parse(url)
        print(f"[DEBUG][EUROJOBS] RSS entries: {len(feed.entries)}")

        if not feed.entries:
            return [], ["EuroJobs – RSS feed unavailable. Visit the site directly."]

        jobs = []
        for entry in feed.entries:
            title = entry.get("title", "")
            jobs.append({
                "id": _job_id(title, "eurojobs"),
                "title": title,
                "company": entry.get("author", ""),
                "location": entry.get("location", "Europe"),
                "source": "EUROJOBS",
                "source_label": "EuroJobs",
                "url": entry.get("link", ""),
                "date_posted": _parse_date(entry.get("published", "")),
                "also_on": [],
                "is_remote": "remote" in title.lower(),
            })
        return jobs, []
    except Exception as e:
        return [], [f"EuroJobs: {e}"]


def _fetch_working_in_content(keywords: str) -> tuple[list, list[str]]:
    from xml.etree import ElementTree as ET
    _UA = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    _UNAVAILABLE = "Working in Content – feed unavailable. Visit the site directly."

    def _make_job(title, link, pub_date):
        return {
            "id": _job_id(title, "workingincontent"),
            "title": title,
            "company": "",
            "location": "",
            "source": "WORKING_IN_CONTENT",
            "source_label": "Working in Content",
            "url": link,
            "date_posted": _parse_date(pub_date),
            "also_on": [],
            "is_remote": "remote" in title.lower(),
        }

    feed_urls = [
        "https://workingincontent.com/jobs/feed/",
        "https://workingincontent.com/feed/",
    ]
    html_url = "https://workingincontent.com/jobs/"

    # Try RSS/XML feeds first
    for url in feed_urls:
        try:
            resp = requests.get(url, headers={"User-Agent": _UA}, timeout=10)
            print(f"[DEBUG][WORKING_IN_CONTENT] trying {url}: status={resp.status_code}")
            if resp.status_code != 200:
                continue
            try:
                root = ET.fromstring(resp.content)
            except ET.ParseError:
                continue
            items = root.findall(".//item")
            print(f"[DEBUG][WORKING_IN_CONTENT] items found: {len(items)}")
            if items:
                print(f"[DEBUG][WORKING_IN_CONTENT] first titles: {[i.findtext('title', '') for i in items[:3]]}")
            jobs = []
            for item in items:
                title = item.findtext("title", "").strip()
                if not _keyword_in(keywords, title):
                    continue
                jobs.append(_make_job(
                    title,
                    item.findtext("link", "").strip(),
                    item.findtext("pubDate", ""),
                ))
            return jobs, []
        except Exception as e:
            print(f"[DEBUG][WORKING_IN_CONTENT] {url}: error – {e}")
            continue

    # HTML fallback
    try:
        resp = requests.get(html_url, headers={"User-Agent": _UA}, timeout=10)
        print(f"[DEBUG][WORKING_IN_CONTENT] trying {html_url}: status={resp.status_code}")
        if resp.status_code == 200:
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                jobs = []
                for a in soup.find_all("a", href=True):
                    title = a.get_text(strip=True)
                    if not title or not _keyword_in(keywords, title):
                        continue
                    href = a["href"]
                    if href.startswith("/"):
                        href = "https://workingincontent.com" + href
                    jobs.append(_make_job(title, href, ""))
                print(f"[DEBUG][WORKING_IN_CONTENT] HTML fallback matched jobs: {len(jobs)}")
                return jobs, []
            except ImportError:
                print("[DEBUG][WORKING_IN_CONTENT] bs4 not installed – HTML fallback skipped")
    except Exception as e:
        print(f"[DEBUG][WORKING_IN_CONTENT] HTML fallback error – {e}")

    return [], [_UNAVAILABLE]


# ---------------------------------------------------------------------------
# New source fetchers
# ---------------------------------------------------------------------------

_REMOTIVE_KEEP = {"europe", "worldwide", "anywhere", "remote"}


def _fetch_remotive(keywords: str) -> tuple[list, list[str]]:
    url = f"https://remotive.com/api/remote-jobs?search={requests.utils.quote(keywords)}&limit=50"
    print(f"[REMOTIVE] fetching: {url}")
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        raw = resp.json().get("jobs", [])
        print(f"[REMOTIVE] {len(raw)} results before filter")
        results = []
        for item in raw:
            geo = (item.get("candidate_required_location", "") or "").lower()
            if geo and not any(t in geo for t in _REMOTIVE_KEEP):
                continue
            title     = item.get("title", "") or ""
            company   = item.get("company_name", "") or ""
            location  = item.get("candidate_required_location", "") or "Remote"
            full_desc = item.get("description", "") or ""
            results.append({
                "id":          _job_id(title, company),
                "title":       title,
                "company":     company,
                "location":    location,
                "source":      "REMOTIVE",
                "source_label":"Remotive",
                "url":         item.get("url", "") or "",
                "date_posted": _parse_date(item.get("publication_date", "") or ""),
                "also_on":     [],
                "is_remote":   True,
                "job_type":    item.get("job_type", "") or "",
                "is_hybrid":   _detect_hybrid_text(title, location, full_desc),
                "description": full_desc[:500],
            })
        print(f"[REMOTIVE] {len(results)} results after filter")
        return results, []
    except Exception as e:
        print(f"[REMOTIVE] exception – {e}")
        return [], [f"Remotive – could not reach the API: {e}"]


_DACH = {"germany", "austria", "switzerland"}


def _fetch_arbeitnow(keywords: str, hours_old: int) -> tuple[list, list[str]]:
    url = (
        f"https://www.arbeitnow.com/api/job-board-api"
        f"?search={requests.utils.quote(keywords)}&page=1"
    )
    print(f"[ARBEITNOW] fetching: {url}")
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "EuroJobSearch/1.0"})
        resp.raise_for_status()
        raw = resp.json().get("data", [])
        print(f"[DEBUG][ARBEITNOW] raw: {len(raw)}")
        kw_lower = keywords.lower()
        results = []
        for item in raw:
            created_at = item.get("created_at")
            if not _is_recent(created_at, hours_old):
                continue
            title = item.get("title", "") or ""
            if not _keyword_in(kw_lower, title):
                continue
            company   = item.get("company_name", "") or ""
            location  = item.get("location", "") or ""
            full_desc = item.get("description", "") or ""
            results.append({
                "id":          _job_id(title, company),
                "title":       title,
                "company":     company,
                "location":    location,
                "source":      "ARBEITNOW",
                "source_label":"Arbeitnow",
                "url":         item.get("url", "") or "",
                "date_posted": _parse_date(created_at),
                "also_on":     [],
                "is_remote":   bool(item.get("remote", False)),
                "is_hybrid":   _detect_hybrid_text(title, location, full_desc),
                "description": full_desc[:500],
            })
        print(f"[DEBUG][ARBEITNOW] after keyword filter: {len(results)}")
        return results, []
    except Exception as e:
        print(f"[ARBEITNOW] exception – {e}")
        return [], [f"Arbeitnow – could not reach the API: {e}"]


_JOBICY_GEO_KEEP = {
    "europe", "emea", "worldwide", "anywhere", "global", "remote",
    "uk", "united kingdom", "germany", "austria", "netherlands", "france",
    "ireland", "sweden", "denmark", "norway", "finland", "switzerland",
    "belgium", "spain", "italy", "portugal", "poland", "czech", "romania",
    "slovakia", "estonia", "latvia", "lithuania", "croatia", "cyprus",
    "greece", "malta", "iceland", "luxembourg",
}
_JOBICY_GEO_EXCLUDE = {
    "usa", "united states", "canada", "apac", "asia",
    "australia", "latin america", "latam", "india", "africa",
}


def _fetch_jobicy(keywords: str) -> tuple[list, list[str]]:
    print("[DEBUG][JOBICY] function called")
    print(f"[DEBUG][JOBICY] keyword: {keywords}")
    try:
        kw_enc = requests.utils.quote(keywords)
        url = f"https://jobicy.com/api/v2/remote-jobs?count=100&tag={kw_enc}"
        print(f"[DEBUG][JOBICY] trying: {url}")
        raw = []
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "EuroJobSearch/1.0"})
            print(f"[DEBUG][JOBICY] status: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                data = data.get("jobs", data.get("data", []))
            print(f"[DEBUG][JOBICY] raw count: {len(data)}")
            raw = data or []
        except Exception as e:
            print(f"[JOBICY] exception – {e}")

        print(f"[DEBUG][JOBICY] raw: {len(raw)}")
        kw_lower = keywords.lower()
        geo_filtered = []
        for item in raw:
            geo = (item.get("jobGeo", "") or "").lower().strip()
            if not geo:
                geo_filtered.append(item)
                continue
            if any(exc in geo for exc in _JOBICY_GEO_EXCLUDE):
                continue
            if any(keep in geo for keep in _JOBICY_GEO_KEEP):
                geo_filtered.append(item)
        print(f"[DEBUG][JOBICY] after geo filter: {len(geo_filtered)}")
        candidates = []
        for item in geo_filtered:
            title     = item.get("jobTitle", "") or ""
            company   = item.get("companyName", "") or ""
            location  = item.get("jobGeo", "") or "Remote"
            full_desc = item.get("jobExcerpt", "") or ""
            candidates.append({
                "id":          _job_id(title, company),
                "title":       title,
                "company":     company,
                "location":    location,
                "source":      "JOBICY",
                "source_label":"Jobicy",
                "url":         item.get("url", "") or "",
                "date_posted": _parse_date(item.get("pubDate", "") or ""),
                "also_on":     [],
                "is_remote":   True,
                "is_hybrid":   _detect_hybrid_text(title, location, full_desc),
                "description": full_desc[:500],
            })
        if kw_lower:
            results = [j for j in candidates if kw_lower in j["title"].lower()]
        else:
            results = candidates
        print(f"[DEBUG][JOBICY] after keyword filter: {len(results)}")
        print(f"[JOBICY] {len(results)} results after filter")
        if not raw:
            return [], ["Jobicy – could not reach the API or received no results."]
        return results, []
    except Exception as e:
        print(f"[DEBUG][JOBICY] EXCEPTION: {e}")
        traceback.print_exc()
        return [], []


_WWR_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"


_WWR_FEEDS = [
    "https://weworkremotely.com/remote-jobs.rss",
    "https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss",
]


def _parse_wwr_feed(text: str, hours_old: int) -> list[dict]:
    feed = feedparser.parse(text)
    parsed = []
    for entry in feed.entries:
        full_title = entry.get("title", "") or ""
        if ": " in full_title:
            parts   = full_title.split(": ", 1)
            company = parts[0].strip()
            title   = parts[1].strip()
        else:
            company = ""
            title   = full_title.strip()
        if title.lower() in ("now hiring", "remote jobs"):
            continue
        pub = entry.get("published_parsed")
        if pub and not _is_recent(pub, hours_old):
            continue
        full_desc = entry.get("summary", "") or ""
        parsed.append({
            "id":          _job_id(title, company or "weworkremotely"),
            "title":       title,
            "company":     company,
            "location":    "Remote",
            "source":      "WEWORKREMOTELY",
            "source_label":"We Work Remotely",
            "url":         entry.get("link", "") or "",
            "date_posted": _parse_date(
                datetime.fromtimestamp(calendar.timegm(pub), tz=timezone.utc)
                if pub else None
            ),
            "also_on":     [],
            "is_remote":   True,
            "is_hybrid":   _detect_hybrid_text(title, "Remote", full_desc),
            "description": full_desc[:500],
        })
    return parsed


def _fetch_weworkremotely(keywords: str, hours_old: int) -> tuple[list, list[str]]:
    print(f"[DEBUG][WWR] fetching {len(_WWR_FEEDS)} feeds...")
    seen_ids: set[str] = set()
    all_parsed: list[dict] = []
    errors = 0
    for url in _WWR_FEEDS:
        try:
            resp = requests.get(url, headers={"User-Agent": _WWR_UA}, timeout=15)
            print(f"[DEBUG][WWR] {url}: status={resp.status_code}")
            resp.raise_for_status()
            for job in _parse_wwr_feed(resp.text, hours_old):
                if job["id"] not in seen_ids:
                    seen_ids.add(job["id"])
                    all_parsed.append(job)
        except Exception as e:
            print(f"[WWR] feed error {url}: {e}")
            errors += 1

    print(f"[DEBUG][WWR] total after dedup: {len(all_parsed)}")
    kw_lower = keywords.lower()
    if kw_lower:
        results = [j for j in all_parsed if kw_lower in j["title"].lower()]
    else:
        results = all_parsed
    print(f"[DEBUG][WWR] after keyword filter: {len(results)}")
    print(f"[DEBUG][WWR] sample titles: {[j['title'] for j in results[:3]]}")
    print(f"[WWR] {len(results)} results after filter")
    if errors == len(_WWR_FEEDS):
        return [], ["We Work Remotely – could not reach the feed"]
    return results, []


# ---------------------------------------------------------------------------
# Hybrid detection
# ---------------------------------------------------------------------------

_HYBRID_TERMS = [
    'hybrid', 'hybride', 'hybridní', 'teilweise remote', 'partial remote',
    'partially remote', 'days in office', 'days onsite',
]
_FULLY_REMOTE_TERMS = [
    'fully remote', '100% remote', 'remote only', 'remote-first',
    'vollständig remote', 'completamente remoto',
]


def _detect_hybrid_text(title: str, location: str, full_desc: str) -> bool:
    text = ' '.join([title or '', location or '', full_desc or '']).lower()
    has_hybrid = any(t in text for t in _HYBRID_TERMS)
    is_fully_remote = any(t in text for t in _FULLY_REMOTE_TERMS)
    return has_hybrid and not is_fully_remote


def _detect_hybrid(job: dict) -> bool:
    return _detect_hybrid_text(
        job.get('title', '') or '',
        job.get('location', '') or '',
        job.get('description', '') or '',
    )


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

SOURCE_PRIORITY = {
    "GREENHOUSE":         1,
    "INDEED_EU":          2,
    "GLASSDOOR":          3,
    "GOOGLE_JOBS":        4,
    "LINKEDIN_EU":        5,
    "KARRIERE_AT":        6,
    "EUROJOBS":           7,
    "WORKING_IN_CONTENT": 8,
    "ARBEITNOW":          9,
    "REMOTIVE":           11,
    "JOBICY":             12,
    "WEWORKREMOTELY":     13,
}


def _deduplicate(jobs: list) -> list:
    seen: dict[str, dict] = {}

    for job in jobs:
        key = f"{job['title'].lower().strip()}|{job['company'].lower().strip()}"
        if key not in seen:
            seen[key] = job
        else:
            existing = seen[key]
            existing_priority = SOURCE_PRIORITY.get(existing["source"], 99)
            new_priority = SOURCE_PRIORITY.get(job["source"], 99)

            # Track also_on
            if job["source_label"] not in existing["also_on"] and job["source"] != existing["source"]:
                existing["also_on"].append(job["source_label"])

            # Replace if new source has higher priority
            if new_priority < existing_priority:
                job["also_on"] = existing["also_on"]
                if existing["source_label"] not in job["also_on"]:
                    job["also_on"].append(existing["source_label"])
                seen[key] = job

    return list(seen.values())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/sources")
def api_sources():
    return jsonify(SOURCES_CONFIG)


@app.route("/api/search", methods=["POST"])
def api_search():
    body = request.get_json(force=True, silent=True) or {}
    keywords = (body.get("keywords") or "").strip()
    countries = body.get("countries") or []
    sources = [s.upper() for s in (body.get("sources") or [s["id"] for s in SOURCES_CONFIG])]
    print(f"[DEBUG] sources received: {sources}")
    hours_old = int(body.get("hours_old") or 168)
    results_per_source = int(body.get("results_per_source") or 20)
    title_only = bool(body.get("title_only", False))
    work_models = set(body.get("work_models") or ["remote", "hybrid", "onsite"])

    if not keywords:
        return jsonify({"error": "keywords required"}), 400

    start = time.time()
    all_jobs: list = []
    all_warnings: list = []
    linkedin_rate_limited = False

    companies = _load_companies()
    futures_map = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as pool:

        if "INDEED_EU" in sources:
            futures_map["INDEED_EU"] = pool.submit(
                _fetch_indeed, keywords, countries, hours_old, results_per_source, title_only, work_models
            )

        if "LINKEDIN_EU" in sources:
            futures_map["LINKEDIN_EU"] = pool.submit(
                _fetch_linkedin, keywords, countries, hours_old, results_per_source, title_only, work_models
            )

        if "GREENHOUSE" in sources:
            futures_map["GREENHOUSE"] = pool.submit(
                _fetch_greenhouse, keywords, countries, title_only, companies["greenhouse"], hours_old
            )

        if "KARRIERE_AT" in sources and "austria" in countries:
            futures_map["KARRIERE_AT"] = pool.submit(_fetch_karriere_at, keywords, hours_old)

        if "REMOTIVE" in sources:
            futures_map["REMOTIVE"] = pool.submit(_fetch_remotive, keywords)

        if "ARBEITNOW" in sources and _DACH.intersection(countries):
            futures_map["ARBEITNOW"] = pool.submit(
                _fetch_arbeitnow, keywords, hours_old
            )

        if "JOBICY" in sources:
            futures_map["JOBICY"] = pool.submit(_fetch_jobicy, keywords)

        if "WEWORKREMOTELY" in sources:
            futures_map["WEWORKREMOTELY"] = pool.submit(
                _fetch_weworkremotely, keywords, hours_old
            )

        # EUROJOBS: RSS feed unavailable – not queried
        # WORKING_IN_CONTENT: feed unavailable – not queried

        for name, future in futures_map.items():
            try:
                result = future.result()
                if name == "LINKEDIN_EU":
                    jobs, warnings, rl = result
                    linkedin_rate_limited = rl
                else:
                    jobs, warnings = result
                # Greenhouse filtering is applied inside _fetch_greenhouse (per slug).
                print(f"[{name}] returned {len(jobs)} results")
                all_jobs.extend(jobs)
                all_warnings.extend(warnings)
            except Exception as e:
                print(f"[{name}] unexpected error – {e}")
                all_warnings.append(f"{name}: unexpected error – {e}")

    sources_queried = list(futures_map.keys())
    deduped = _deduplicate(all_jobs)
    for job in deduped:
        job['title'] = _normalize_title(job.get('title') or '')
        if 'is_hybrid' not in job:
            job['is_hybrid'] = _detect_hybrid(job)
        # Stamp detected_countries (list) once; used by the country filter below
        # and returned to the frontend so chips read this field directly.
        job['detected_countries'] = _detect_job_countries(job)

    # Greenhouse non-EU exclusion: onsite Greenhouse jobs with no detected EU
    # country are non-European (US/AU/etc.) and should be dropped.
    # Remote Greenhouse jobs always have detected_countries=['remote'] so they pass.
    gh_before = sum(1 for j in deduped if j.get('source') == 'GREENHOUSE')
    deduped = [
        j for j in deduped
        if j.get('source') != 'GREENHOUSE' or bool(j.get('detected_countries'))
    ]
    gh_after = sum(1 for j in deduped if j.get('source') == 'GREENHOUSE')
    if gh_before != gh_after:
        print(f"[EuroJobSearch] Greenhouse non-EU exclusion: {gh_before} → {gh_after}")

    # Server-side work model filter – each flag is checked independently so a job
    # with both is_remote=True and is_hybrid=True passes either remote or hybrid filters.
    _ALL_WM = {"remote", "hybrid", "onsite"}
    if work_models and work_models != _ALL_WM:
        def _matches_wm(job: dict) -> bool:
            if "remote" in work_models and job.get('is_remote'):
                return True
            if "hybrid" in work_models and job.get('is_hybrid'):
                return True
            if "onsite" in work_models and not job.get('is_remote') and not job.get('is_hybrid'):
                return True
            return False
        before = len(deduped)
        deduped = [j for j in deduped if _matches_wm(j)]
        print(f"[EuroJobSearch] work_model filter: {before} → {len(deduped)} (kept {work_models})")

    # Server-side country filter – a job passes if any of its detected_countries
    # intersects the selected set (multi-country jobs can match multiple filters).
    if countries:
        country_set = set(countries)
        before = len(deduped)
        deduped = [
            j for j in deduped
            if country_set.intersection(j.get('detected_countries') or [])
        ]
        print(f"[EuroJobSearch] country filter: {before} → {len(deduped)} (kept {countries})")

    # Baseline keyword filter – applied after merging all sources.
    # Guarantees the keyword appears in the job's title or (HTML-stripped) description,
    # independent of how lenient each source's own search API is.
    # title_only=True: title match required (per-source filters already enforce this,
    #                  but this acts as a consistent safety net across all sources).
    # title_only=False: title OR description match required (new behaviour).
    # Empty keywords: no filter (caught earlier by the required-field check).
    if keywords:
        kw_lower = keywords.lower()
        before = len(deduped)
        deduped = [
            j for j in deduped
            if kw_lower in (j.get('title') or '').lower()
            or (not title_only and kw_lower in _strip_html(j.get('description') or '').lower())
        ]
        print(f"[EuroJobSearch] keyword filter ({'title' if title_only else 'title|desc'}): {before} → {len(deduped)}")

    duration = round(time.time() - start, 2)
    print(f"[EuroJobSearch] query={keywords!r} total={len(deduped)} duration={duration}s")

    return jsonify({
        "results": deduped,
        "total": len(deduped),
        "duration_seconds": duration,
        "warnings": all_warnings,
        "sources_queried": sources_queried,
        "linkedin_rate_limited": linkedin_rate_limited,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)

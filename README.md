# EuroJobSearch

European jobs only. Search across job boards and company career pages – all in one place.

A Flask-based job search aggregator for the European job market. It searches eight sources in parallel – Indeed EU, LinkedIn, Greenhouse, Karriere.at, Arbeitnow, Remotive, Jobicy, and We Work Remotely – deduplicates results, and presents them in one filterable view: country, work model, source, and keyword, all combinable.

Try the [interactive demo](https://teokitten.github.io/eurojobsearch/) with sample data – no install required.

![EuroJobSearch screenshot](docs/screenshot.png)

## Setup

Requires Python 3.10 or later.

### Windows

1. Install Python from [python.org](https://www.python.org/downloads/) if not already installed. During installation, check the box labeled "Add Python to PATH."
2. Download this repository: click the green "Code" button above, then "Download ZIP," and extract it. (Or, if you have git installed, run `git clone` with the repository URL.)
3. Open Command Prompt and navigate to the extracted folder, for example:
   ```
   cd Downloads\eurojobsearch
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the app:
   ```
   python app.py
   ```
6. Open `http://localhost:5000` in your browser.

### macOS

1. Check if Python 3.10+ is installed by running `python3 --version` in Terminal. If not installed, install it from [python.org](https://www.python.org/downloads/) or with `brew install python3`.
2. Download this repository: click the green "Code" button above, then "Download ZIP," and extract it. (Or, if you have git installed, run `git clone` with the repository URL.)
3. Open Terminal and navigate to the extracted folder, for example:
   ```
   cd Downloads/eurojobsearch
   ```
4. Install dependencies:
   ```
   pip3 install -r requirements.txt
   ```
5. Run the app:
   ```
   python3 app.py
   ```
6. Open `http://localhost:5000` in your browser.

### Linux

1. Python 3.10+ is usually preinstalled. Check with `python3 --version`. If it's missing, install it with your package manager, for example `sudo apt install python3 python3-pip` on Ubuntu/Debian.
2. Download this repository: click the green "Code" button above, then "Download ZIP," and extract it. (Or, if you have git installed, run `git clone` with the repository URL.)
3. Open a terminal and navigate to the extracted folder, for example:
   ```
   cd Downloads/eurojobsearch
   ```
4. Install dependencies:
   ```
   pip3 install -r requirements.txt
   ```
5. Run the app:
   ```
   python3 app.py
   ```
6. Open `http://localhost:5000` in your browser.

To stop the app, press Ctrl+C in the terminal.

## Sources

| Source | Notes |
|---|---|
| Indeed EU | Per-country search. If no countries are selected, falls back to Germany-remote-only results. |
| LinkedIn | May rate-limit after repeated use. Requires a free account to view full listings and apply. |
| Greenhouse | Queries a curated list of company job boards via the public Greenhouse API. |
| Karriere.at | Austria only. |
| Arbeitnow | Germany, Austria, and Switzerland only. |
| Remotive | Remote roles only. |
| Jobicy | Remote roles only. |
| We Work Remotely | Remote roles only. |

## Keyword search

The keyword field supports comma-separated AND queries. All terms must appear in the job title or description for a result to be returned.

- `technical writer` – standard single-term search
- `technical writer, freelance` – returns only jobs matching both terms
- `technical writer, contract` – same pattern for contract roles

The primary term (before the first comma) is sent to each source's search API. Secondary terms are matched locally against fetched results.

Common employment-type terms expand automatically to synonyms. Searching for `freelance` also matches: contractor, contract, B2B, CDD, Werkvertrag, freiberuflich. Searching for `contract` matches: contractor, freelance, B2B, CDD, Werkvertrag. Searching for `part time` or `part-time` matches: Teilzeit.

## Known limitations

- **Indeed EU**: if no countries are selected, results are limited to Germany-based remote jobs.
- **Greenhouse**: locations formatted like "Germany (Remote); Ireland (Remote)" are detected as remote only, not as all listed countries.
- **Arbeitnow**: its API does not support a search-term parameter; results are filtered by keyword after fetching.
- **LinkedIn**: automated requests may be rate-limited after repeated use.
- **LinkedIn hybrid detection**: LinkedIn does not expose work type (hybrid/remote/on-site) through the scraping layer used by this app. Hybrid jobs from LinkedIn will not be tagged as hybrid in results – this is a platform limitation, not a bug.
- **Czech Republic / LinkedIn**: JobSpy internally misinterprets "Czech Republic" as "Dominican Republic". Czech Republic results still appear via LinkedIn's Europe-wide call.

## Company career pages (Greenhouse)

Greenhouse exposes a public JSON API for company job boards – no account or API key needed. The app queries a curated list of European company career pages (`companies.json`) and filters results by keyword, country, and work model, same as every other source.

## Adding companies to the Greenhouse source

Only companies listed under `"greenhouse"` in `companies.json` are searched. To add one, find the `{slug}` portion of the company's Greenhouse-hosted careers page URL and add it to the list in `companies.json`.

## License

MIT

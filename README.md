# EuroJobSearch

A Flask-based job search aggregator focused on European job markets. It pulls
listings from public job boards, ATS career page APIs (Greenhouse, Lever,
Ashby), and RSS feeds – all in parallel, deduplicated, and presented in a
single clean interface.

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

## Source reliability notes

| Source | Reliability | Notes |
|---|---|---|
| Indeed EU | ✅ Stable | Best coverage; searches per country |
| LinkedIn | ⚠ Unstable | Rate-limits quickly; partial results expected |
| Greenhouse | ✅ Stable | Queries public ATS APIs directly |
| Lever | ✅ Stable | Queries public ATS APIs directly |
| Ashby | ✅ Stable | Queries public ATS APIs directly |
| Karriere.at | ✅ Stable | Austria only; RSS feed |
| EuroJobs | ✅ Stable | Pan-European RSS feed |
| Working in Content | ✅ Stable | Niche – content/UX writing roles |

## ATS sources

Greenhouse, Lever, and Ashby expose public JSON APIs for company job boards.
No account or API key is needed. The app queries a curated list of European
tech company slugs and filters results by keyword and location.

## Adding target companies

The app only searches companies explicitly listed in `companies.json` for
Greenhouse, Lever, and Ashby. To find the slug for a company:

- **Greenhouse:** Go to the company's career page. If the URL contains
  `boards.greenhouse.io/{slug}`, that `{slug}` is what to add under
  `"greenhouse"` in `companies.json`.
- **Lever:** If the URL contains `jobs.lever.co/{slug}`, use that `{slug}`
  under `"lever"`.
- **Ashby:** If the URL contains `jobs.ashbyhq.com/{slug}`, use that `{slug}`
  under `"ashby"`.

You can also edit the list directly in the app via the **Target companies**
panel in the sidebar – changes are saved to `companies.json` on the server.

## License

MIT

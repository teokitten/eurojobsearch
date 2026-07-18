#!/usr/bin/env python3
"""
Regenerates docs/index.html from a fresh copy of templates/index.html,
then applies the demo-specific changes:
  1. Demo banner (right after <body>)
  2. MOCK_DATA + helpers (right after PAGE_SIZE)
  3. loadSources(): /api/sources -> MOCK_DATA.sources
  4. runSearch(): /api/search fetch -> mockSearchApi()

Run from the repo root: python3 build_demo.py
"""

import shutil
import sys

SRC = "templates/index.html"
DST = "docs/index.html"

# Fresh copy - guarantees the demo matches the real app exactly.
shutil.copyfile(SRC, DST)

with open(DST, "r", encoding="utf-8") as f:
    content = f.read()

# ------------------------------------------------------------------
# 1. Demo banner
# ------------------------------------------------------------------
BANNER = '''<div id="demo-banner" style="background:#1e1f2e; border-bottom:1px solid #2e3248; padding:10px 20px; font-size:0.82rem; color:#AFA9EC; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
  <span style="background:#5b6ef5; color:#fff; border-radius:4px; padding:2px 8px; font-size:0.75rem; font-weight:600; letter-spacing:0.04em;">DEMO</span>
  This is a static preview with sample data – no server required.
  <a href="https://github.com/teokitten/eurojobsearch" target="_blank" rel="noopener" style="color:#7b8cde; margin-left:auto; text-decoration:none;">View on GitHub ↗</a>
</div>
'''

KEYWORDS_BAR = '''<div id="demo-keywords-bar" style="border-bottom:1px solid #2e3248; padding:10px 20px; font-size:0.82rem; color:#9098b1; display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
  <span>Try a search:</span>
  <button class="source-filter-btn demo-keyword-chip" data-keyword="technical writer">technical writer</button>
  <button class="source-filter-btn demo-keyword-chip" data-keyword="writer">writer</button>
  <button class="source-filter-btn demo-keyword-chip" data-keyword="developer">developer</button>
  <button class="source-filter-btn demo-keyword-chip" data-keyword="designer">designer</button>
  <button class="source-filter-btn demo-keyword-chip" data-keyword="product manager">product manager</button>
  <button class="source-filter-btn demo-keyword-chip" data-keyword="project manager">project manager</button>
</div>
'''

old = "<body>\n"
if content.count(old) != 1:
    sys.exit(f"ERROR: expected exactly 1 occurrence of <body> tag, found {content.count(old)}")
content = content.replace(old, old + BANNER, 1)

old2 = '<div id="panel-search">\n'
if content.count(old2) != 1:
    sys.exit(f"ERROR: expected exactly 1 occurrence of panel-search div, found {content.count(old2)}")
content = content.replace(old2, old2 + KEYWORDS_BAR, 1)

# ------------------------------------------------------------------
# 2. MOCK_DATA + helpers
# ------------------------------------------------------------------
MOCK_BLOCK = '''
const MOCK_DATA = {
  "sources": [
    { "id": "INDEED_EU", "label": "Indeed EU", "pull_status": "ok" },
    { "id": "LINKEDIN_EU", "label": "LinkedIn", "pull_status": "ok" },
    { "id": "GREENHOUSE", "label": "Greenhouse", "pull_status": "ok" },
    { "id": "KARRIERE_AT", "label": "Karriere.at", "pull_status": "ok" },
    { "id": "ARBEITNOW", "label": "Arbeitnow", "pull_status": "ok" },
    { "id": "REMOTIVE", "label": "Remotive", "pull_status": "ok" },
    { "id": "JOBICY", "label": "Jobicy", "pull_status": "ok" },
    { "id": "WEWORKREMOTELY", "label": "We Work Remotely", "pull_status": "ok" },
    { "id": "WORKABLE",       "label": "Workable",         "pull_status": "ok" },
    { "id": "RECRUITEE",      "label": "Recruitee",        "pull_status": "ok" }
  ],
  "jobs": [
    { "id": "job-01", "title": "Senior Technical Writer", "company": "Solvix Technologies", "source": "KARRIERE_AT", "source_label": "Karriere.at", "location": "Vienna, Austria", "url": null, "date_posted": "2026-06-13T15:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["austria"], "description": "Lead documentation for our cloud security platform. Work closely with engineering on API references, release notes, and onboarding guides." },
    { "id": "job-02", "title": "Content Designer", "company": "Aurion Health Tech", "source": "KARRIERE_AT", "source_label": "Karriere.at", "location": "Graz, Austria", "url": null, "date_posted": "2026-06-10T10:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["austria"], "description": "Shape in-product copy and onboarding flows for a healthtech platform. Collaborate with UX research and product on a hybrid schedule." },
    { "id": "job-03", "title": "Customer Support Specialist", "company": "Maplewood Digital", "source": "KARRIERE_AT", "source_label": "Karriere.at", "location": "Linz, Austria", "url": null, "date_posted": "2026-06-05T08:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["austria"], "description": "Provide first-line support via chat and email for SaaS customers across the DACH region. German and English required." },
    { "id": "job-04", "title": "IT Support Technician", "company": "Stonebridge Systems", "source": "KARRIERE_AT", "source_label": "Karriere.at", "location": "Salzburg, Austria", "url": null, "date_posted": "2026-05-28T08:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["austria"], "description": "On-site IT support covering hardware, Windows and Linux endpoints, and basic network troubleshooting for a 200-person office." },
    { "id": "job-05", "title": "DevOps Engineer", "company": "Ironwood Cloud", "source": "ARBEITNOW", "source_label": "Arbeitnow", "location": "Berlin, Germany", "url": null, "date_posted": "2026-06-12T13:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["germany"], "description": "Manage CI/CD pipelines, Kubernetes clusters, and Terraform infrastructure for a fintech platform. Two days per week in the Berlin office." },
    { "id": "job-06", "title": "Frontend Developer (React)", "company": "Cobalt & Sage", "source": "ARBEITNOW", "source_label": "Arbeitnow", "location": "Munich, Germany", "url": null, "date_posted": "2026-06-09T09:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["germany"], "description": "Build and maintain customer-facing dashboards in React and TypeScript. Work alongside design and backend teams in our Munich studio." },
    { "id": "job-07", "title": "QA Engineer", "company": "Crestline Software", "source": "ARBEITNOW", "source_label": "Arbeitnow", "location": "Zurich, Switzerland", "url": null, "date_posted": "2026-06-02T08:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["switzerland"], "description": "Design and execute test plans for a logistics platform. Experience with automated testing frameworks and API testing required." },
    { "id": "job-08", "title": "Backend Developer (Python)", "company": "Vela Robotics", "source": "ARBEITNOW", "source_label": "Arbeitnow", "location": "Vienna, Austria", "url": null, "date_posted": "2026-05-30T08:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["austria"], "description": "Develop Python services for robotics fleet management. Hybrid role with one day per week required on-site in Vienna." },
    { "id": "job-09", "title": "Documentation Engineer", "company": "Pinegrove Cloud", "source": "INDEED_EU", "source_label": "Indeed EU", "location": "Amsterdam, Netherlands", "url": null, "date_posted": "2026-06-14T08:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["netherlands"], "description": "Own developer documentation for our API platform using a docs-as-code workflow with Markdown, Git, and a static site generator." },
    { "id": "job-10", "title": "UX Researcher", "company": "Foxglove Digital", "source": "INDEED_EU", "source_label": "Indeed EU", "location": "Dublin, Ireland", "url": null, "date_posted": "2026-06-11T09:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["ireland"], "description": "Plan and run usability studies for a fintech mobile app. Synthesize findings into actionable recommendations for product and design teams." },
    { "id": "job-11", "title": "Product Manager", "company": "Larkspur Software", "source": "INDEED_EU", "source_label": "Indeed EU", "location": "Warsaw, Poland", "url": null, "date_posted": "2026-06-07T08:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["poland"], "description": "Own the roadmap for our analytics platform. Hybrid schedule with regular travel to client sites across Central and Eastern Europe." },
    { "id": "job-12", "title": "Site Reliability Engineer", "company": "Sablefin Analytics", "source": "INDEED_EU", "source_label": "Indeed EU", "location": "Prague, Czech Republic", "url": null, "date_posted": "2026-06-01T09:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["czech_republic"], "description": "Maintain uptime and performance for a high-traffic data platform. On-call rotation, with AWS, Docker, and Prometheus experience needed." },
    { "id": "job-13", "title": "Marketing Manager", "company": "Harbor & Co", "source": "INDEED_EU", "source_label": "Indeed EU", "location": "Lisbon, Portugal", "url": null, "date_posted": "2026-05-22T09:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["portugal"], "description": "Lead campaign strategy and the content calendar for a consumer app. Manage a small team of writers and designers." },
    { "id": "job-14", "title": "UX Writer", "company": "Quill Software", "source": "LINKEDIN_EU", "source_label": "LinkedIn", "location": "Berlin, Germany", "url": null, "date_posted": "2026-06-13T10:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["germany"], "description": "Write in-product copy, error messages, and onboarding flows for a B2B SaaS product. Fully remote, working in EU timezones." },
    { "id": "job-15", "title": "Information Developer", "company": "Northwind Analytics", "source": "LINKEDIN_EU", "source_label": "LinkedIn", "location": "Bucharest, Romania", "url": null, "date_posted": "2026-06-08T10:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["romania"], "description": "Maintain a knowledge base and API reference for a data analytics platform. Hybrid role, two office days per week." },
    { "id": "job-16", "title": "Solutions Architect", "company": "Wavelength Co", "source": "LINKEDIN_EU", "source_label": "LinkedIn", "location": "Madrid, Spain", "url": null, "date_posted": "2026-06-04T09:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["spain"], "description": "Design cloud architecture for enterprise clients using AWS and Azure. Client-facing role based in our Madrid office." },
    { "id": "job-17", "title": "Engineering Manager", "company": "Granite Peak Software", "source": "LINKEDIN_EU", "source_label": "LinkedIn", "location": "Stockholm, Sweden", "url": null, "date_posted": "2026-05-29T09:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["sweden"], "description": "Lead a team of eight engineers building a logistics platform. Hybrid, three days per week in our Stockholm office." },
    { "id": "job-18", "title": "Business Analyst", "company": "Thornbury Systems", "source": "LINKEDIN_EU", "source_label": "LinkedIn", "location": "Brussels, Belgium", "url": null, "date_posted": "2026-05-18T09:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["belgium"], "description": "Gather requirements and document processes for an ERP rollout across multiple European offices. SQL and process mapping experience required." },
    { "id": "job-19", "title": "Senior Content Strategist", "company": "Bramblewood Tech", "source": "GREENHOUSE", "source_label": "Greenhouse", "location": "Berlin, Germany; Dublin, Ireland", "url": null, "date_posted": "2026-06-12T09:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["germany", "ireland"], "description": "Define content strategy across product, marketing, and support surfaces for a security platform. Remote, with hubs in Berlin and Dublin." },
    { "id": "job-20", "title": "API Documentation Specialist", "company": "Veridian Analytics", "source": "GREENHOUSE", "source_label": "Greenhouse", "location": "Amsterdam, Netherlands; Warsaw, Poland", "url": null, "date_posted": "2026-06-06T11:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Contract", "detected_countries": ["netherlands", "poland"], "description": "Write and maintain OpenAPI specs and developer guides for a data integration platform. Six-month contract, remote within the EU." },
    { "id": "job-21", "title": "Developer Advocate", "company": "Skyport Systems", "source": "GREENHOUSE", "source_label": "Greenhouse", "location": "Remote – EU", "url": null, "date_posted": "2026-06-03T09:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["remote"], "description": "Create tutorials, sample apps, and conference talks for our developer platform. Comfortable with Python, JavaScript, and public speaking." },
    { "id": "job-22", "title": "Full Stack Developer", "company": "Echo Valley Studio", "source": "GREENHOUSE", "source_label": "Greenhouse", "location": "Paris, France", "url": null, "date_posted": "2026-05-26T09:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["france"], "description": "Build features end-to-end across a Django backend and React frontend for a media production tool." },
    { "id": "job-23", "title": "Localization Specialist", "company": "Cascade Security", "source": "GREENHOUSE", "source_label": "Greenhouse", "location": "Milan, Italy", "url": null, "date_posted": "2026-05-17T09:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["italy"], "description": "Manage translation workflows and review localized strings for a security product across ten European languages. Hybrid role." },
    { "id": "job-24", "title": "Senior Technical Writer (Docs-as-Code)", "company": "Meridian Labs", "source": "REMOTIVE", "source_label": "Remotive", "location": "Remote – EU", "url": null, "date_posted": "2026-06-14T06:30:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["remote"], "description": "Own documentation for a Kubernetes-based platform using a docs-as-code workflow with Markdown, Git, and CI-driven builds." },
    { "id": "job-25", "title": "Cloud Security Engineer", "company": "Driftwood Robotics", "source": "REMOTIVE", "source_label": "Remotive", "location": "Remote – Worldwide", "url": null, "date_posted": "2026-06-10T08:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["remote"], "description": "Implement and monitor security controls across AWS and GCP environments. SOC 2 and GDPR compliance experience preferred." },
    { "id": "job-26", "title": "Growth Marketing Specialist", "company": "Amberlight Co", "source": "REMOTIVE", "source_label": "Remotive", "location": "Remote – EU", "url": null, "date_posted": "2026-06-05T10:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["remote"], "description": "Run acquisition campaigns across paid social and SEO for a subscription app. Analytics-driven, comfortable with A/B testing." },
    { "id": "job-27", "title": "Data Analyst", "company": "Tidal Works", "source": "REMOTIVE", "source_label": "Remotive", "location": "Remote – EU", "url": null, "date_posted": "2026-05-31T08:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["remote"], "description": "Build dashboards and reports in SQL and Python for a logistics company. Experience with Looker or similar BI tools is a plus." },
    { "id": "job-28", "title": "Scrum Master", "company": "Fjordline Tech", "source": "REMOTIVE", "source_label": "Remotive", "location": "Remote – Worldwide", "url": null, "date_posted": "2026-05-23T08:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Contract", "detected_countries": ["remote"], "description": "Facilitate agile ceremonies for two cross-functional teams building a fintech product. Certified Scrum Master preferred." },
    { "id": "job-29", "title": "Technical Writer (Docs-as-Code)", "company": "Lumen Data Co", "source": "JOBICY", "source_label": "Jobicy", "location": "Remote – EU", "url": null, "date_posted": "2026-06-13T18:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["remote"], "description": "Write and maintain user guides and API docs for a data pipeline tool. Git-based workflow, Markdown, and static site publishing." },
    { "id": "job-30", "title": "Product Designer", "company": "Wrenfield Studio", "source": "JOBICY", "source_label": "Jobicy", "location": "Remote – EU", "url": null, "date_posted": "2026-06-09T14:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["remote"], "description": "Design end-to-end flows for a project management app. Figma, design systems, and close collaboration with engineering." },
    { "id": "job-31", "title": "Sales Engineer", "company": "Cobble & Stone", "source": "JOBICY", "source_label": "Jobicy", "location": "Remote – EU", "url": null, "date_posted": "2026-06-02T10:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Contract", "detected_countries": ["remote"], "description": "Support the sales team with technical demos and proof-of-concept builds for enterprise clients across Europe." },
    { "id": "job-32", "title": "Frontend Developer (Vue)", "company": "Pelican Cloud", "source": "JOBICY", "source_label": "Jobicy", "location": "Remote – Worldwide", "url": null, "date_posted": "2026-05-25T08:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["remote"], "description": "Build and maintain a Vue 3 dashboard for an analytics product. Strong CSS skills and attention to UI detail required." },
    { "id": "job-33", "title": "Content Designer", "company": "Greenfield Robotics", "source": "WEWORKREMOTELY", "source_label": "We Work Remotely", "location": "Remote – Worldwide", "url": null, "date_posted": "2026-06-11T11:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["remote"], "description": "Write microcopy, help center articles, and onboarding emails for a robotics SaaS platform. Async-first team across time zones.", "also_on": ["Remotive"] },
    { "id": "job-34", "title": "Backend Developer (Node.js)", "company": "Brightside Tech", "source": "WEWORKREMOTELY", "source_label": "We Work Remotely", "location": "Remote – EU", "url": null, "date_posted": "2026-06-07T09:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["remote"], "description": "Maintain Node.js microservices for a media streaming platform. Experience with GraphQL and PostgreSQL preferred." },
    { "id": "job-35", "title": "Documentation Engineer", "company": "Nordlicht Systems", "source": "WEWORKREMOTELY", "source_label": "We Work Remotely", "location": "Remote – EU", "url": null, "date_posted": "2026-05-27T09:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["remote"], "description": "Build and maintain a docs site with Markdown, versioning, and search for a developer tools company.", "also_on": ["Jobicy", "LinkedIn"] },
    { "id": "job-36", "title": "Customer Support Specialist", "company": "BrightPath Software", "source": "WEWORKREMOTELY", "source_label": "We Work Remotely", "location": "Remote – Worldwide", "url": null, "date_posted": "2026-05-19T08:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Part-time", "detected_countries": ["remote"], "description": "Provide email support for a small SaaS team. Flexible part-time hours across European time zones." },
    { "id": "job-37", "title": "Senior Frontend Developer (Angular)", "company": "Falkland Systems", "source": "GREENHOUSE", "source_label": "Greenhouse", "location": "Stockholm, Sweden", "url": null, "date_posted": "2026-06-13T08:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["sweden"], "description": "Build and maintain a design-system-driven Angular application for a fintech dashboard. Hybrid, two days per week in our Stockholm office." },
    { "id": "job-38", "title": "Java Developer", "company": "Ashgrove Tech", "source": "INDEED_EU", "source_label": "Indeed EU", "location": "Brussels, Belgium", "url": null, "date_posted": "2026-06-10T09:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["belgium"], "description": "Maintain backend services in Java and Spring Boot for a logistics platform. On-site role in our Brussels office, five days a week." },
    { "id": "job-39", "title": "Mobile Developer (iOS)", "company": "Mira Cloud Co", "source": "LINKEDIN_EU", "source_label": "LinkedIn", "location": "Lisbon, Portugal", "url": null, "date_posted": "2026-06-05T10:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["portugal"], "description": "Develop and maintain our Swift-based iOS app. Hybrid schedule, collaborating closely with backend and design teams in Lisbon." },
    { "id": "job-40", "title": "Junior Software Developer", "company": "Birchwood Software", "source": "KARRIERE_AT", "source_label": "Karriere.at", "location": "Vienna, Austria", "url": null, "date_posted": "2026-06-12T08:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["austria"], "description": "Support our engineering team building internal tools in C# and .NET. Great entry-level role with mentorship, on-site in Vienna." },
    { "id": "job-41", "title": "Full Stack Developer (Java/Angular)", "company": "Solace Digital", "source": "GREENHOUSE", "source_label": "Greenhouse", "location": "Berlin, Germany", "url": null, "date_posted": "2026-05-28T09:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["germany"], "description": "Build features across a Java Spring backend and Angular frontend for a B2B marketplace. Hybrid, three days per week in Berlin." },
    { "id": "job-42", "title": "Senior Project Manager", "company": "Cinderpath Logistics", "source": "GREENHOUSE", "source_label": "Greenhouse", "location": "Helsinki, Finland", "url": null, "date_posted": "2026-06-09T10:00:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["finland"], "description": "Lead cross-functional delivery for a Nordic logistics platform. Coordinate engineering, ops, and customer success teams from our Helsinki office." },
    { "id": "job-43", "title": "Product Manager", "company": "Lighthouse Data", "source": "REMOTIVE", "source_label": "Remotive", "location": "Remote – EU", "url": null, "date_posted": "2026-06-11T09:00:00Z", "is_remote": true, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["remote"], "description": "Own the roadmap for a B2B analytics product. Work closely with design and engineering to prioritize features based on customer feedback." },
    { "id": "job-44", "title": "Project Manager", "company": "Alpenrose Systems", "source": "KARRIERE_AT", "source_label": "Karriere.at", "location": "Vienna, Austria", "url": null, "date_posted": "2026-06-13T11:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["austria"], "description": "Manage timelines and stakeholder communication for a renewable-energy software platform. Hybrid role, two office days per week in Vienna." },
    { "id": "job-45", "title": "Associate Product Manager", "company": "Castlewood Tech", "source": "LINKEDIN_EU", "source_label": "LinkedIn", "location": "Copenhagen, Denmark", "url": null, "date_posted": "2026-06-06T09:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["denmark"], "description": "Support roadmap planning and user research for a consumer subscription app. Hybrid schedule based in our Copenhagen office." },
    { "id": "job-46", "title": "Technical Writer", "company": "Birchgate Software", "source": "INDEED_EU", "source_label": "Indeed EU", "location": "Vienna, Austria", "url": null, "date_posted": "2026-06-15T05:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["austria"], "description": "Own user-facing documentation for a DevOps tooling platform. Hybrid role, two office days per week in Vienna. Docs-as-code workflow with Markdown and Git." },
    { "id": "job-47", "title": "Frontend Developer", "company": "Pinecrest Digital", "source": "ARBEITNOW", "source_label": "Arbeitnow", "location": "Graz, Austria", "url": null, "date_posted": "2026-06-15T07:30:00Z", "is_remote": false, "is_hybrid": false, "job_type": "Full-time", "detected_countries": ["austria"], "description": "Build customer-facing features in React and TypeScript for a logistics scheduling tool. On-site role in our Graz office." },
    { "id": "job-48", "title": "Software Engineer", "company": "Keywords Studios", "source": "WORKABLE", "source_label": "Workable", "location": "Dublin, Ireland", "url": null, "date_posted": "2026-06-14T10:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["ireland"], "description": "Join the games industry's leading technical services company. Work on tools and pipelines for major game titles from our Dublin studio." },
    { "id": "job-49", "title": "AI Research Engineer", "company": "DeepHealth", "source": "RECRUITEE", "source_label": "Recruitee", "location": "Amsterdam, Netherlands", "url": null, "date_posted": "2026-06-13T09:00:00Z", "is_remote": false, "is_hybrid": true, "job_type": "Full-time", "detected_countries": ["netherlands"], "description": "Work on medical imaging AI models for radiology. Collaborate with clinical partners across the Netherlands to improve diagnostic accuracy." }
  ],
  "sourceHealth": {
    "INDEED_EU":      {"last_success_at": "2026-06-15T05:30:00Z", "last_attempt_at": "2026-06-15T05:30:00Z", "last_count": 13, "last_error": null},
    "LINKEDIN_EU":    {"last_success_at": "2026-06-14T18:00:00Z", "last_attempt_at": "2026-06-15T05:30:00Z", "last_count": 0,  "last_error": "LINKEDIN_EU: rate limited"},
    "GREENHOUSE":     {"last_success_at": "2026-06-15T05:30:00Z", "last_attempt_at": "2026-06-15T05:30:00Z", "last_count": 9,  "last_error": null},
    "KARRIERE_AT":    {"last_success_at": "2026-06-15T05:30:00Z", "last_attempt_at": "2026-06-15T05:30:00Z", "last_count": 5,  "last_error": null},
    "ARBEITNOW":      {"last_success_at": "2026-06-15T05:30:00Z", "last_attempt_at": "2026-06-15T05:30:00Z", "last_count": 4,  "last_error": null},
    "REMOTIVE":       {"last_success_at": "2026-06-15T05:30:00Z", "last_attempt_at": "2026-06-15T05:30:00Z", "last_count": 5,  "last_error": null},
    "JOBICY":         {"last_success_at": "2026-06-15T05:30:00Z", "last_attempt_at": "2026-06-15T05:30:00Z", "last_count": 4,  "last_error": null},
    "WEWORKREMOTELY": {"last_success_at": "2026-06-15T05:30:00Z", "last_attempt_at": "2026-06-15T05:30:00Z", "last_count": 4,  "last_error": null},
    "WORKABLE":       {"last_success_at": "2026-06-15T05:30:00Z", "last_attempt_at": "2026-06-15T05:30:00Z", "last_count": 8,  "last_error": null},
    "RECRUITEE":      {"last_success_at": "2026-06-15T05:30:00Z", "last_attempt_at": "2026-06-15T05:30:00Z", "last_count": 1,  "last_error": null}
  }
};

// Source homepages – used as job.url fallback so result cards
// open something real on click, matching the live app's behavior.
const SOURCE_HOMEPAGES = {
  INDEED_EU: 'https://www.indeed.com',
  LINKEDIN_EU: 'https://www.linkedin.com/jobs',
  GREENHOUSE: 'https://www.greenhouse.io',
  KARRIERE_AT: 'https://www.karriere.at',
  ARBEITNOW: 'https://www.arbeitnow.com',
  REMOTIVE: 'https://remotive.com',
  JOBICY: 'https://jobicy.com',
  WEWORKREMOTELY: 'https://weworkremotely.com',
  WORKABLE:       'https://apply.workable.com',
  RECRUITEE:      'https://recruitee.com',
};

// Fixed reference point for "how old is this job" calculations, derived
// from the dataset's own dates rather than the real clock - results are
// identical no matter when this demo is opened. Set 3 hours after the
// most recent posting in the dataset.
const MOCK_NOW = MOCK_DATA.jobs.reduce((max, j) => {
  const t = new Date(j.date_posted).getTime();
  return t > max ? t : max;
}, 0) + (3 * 3600000);

// Fill in a source-homepage URL for click-through where none is set.
// Strip dates so no misleading "8 days ago" labels appear and the
// posted-within filter chips are cosmetic only (as in the real demo).
MOCK_DATA.jobs.forEach(j => {
  if (!j.url) j.url = SOURCE_HOMEPAGES[j.source] || null;
  j.date_posted = null;
});

// Pre-populate NEW badge baseline for the demo – runs once per browser.
// Seeds baselines for all demo keyword chips with all jobs EXCEPT the
// 3 most recently dated ones, which will appear as NEW on first search.
(function() {
  const DEMO_SEED_KEY = 'ejs_demo_seeded_v1';
  if (localStorage.getItem(DEMO_SEED_KEY)) return;
  function _sid(j) {
    return (j.title||'').toLowerCase().replace(/\\s+/g,' ').trim()+'|'+(j.company||'').toLowerCase().replace(/\\s+/g,' ').trim();
  }
  const sorted = [...MOCK_DATA.jobs].sort((a,b) => new Date(b.date_posted)-new Date(a.date_posted));
  const newOnes = new Set(sorted.slice(0,3).map(_sid));
  const baseline = MOCK_DATA.jobs.map(_sid).filter(id => !newOnes.has(id));
  const seen = {};
  ['technical writer','writer','developer','designer','product manager','project manager'].forEach(kw => {
    seen[kw+'||||hybrid,onsite,remote'] = baseline;
  });
  try {
    localStorage.setItem('ejs_seen_v4', JSON.stringify(seen));
    localStorage.setItem(DEMO_SEED_KEY, '1');
  } catch(_) {}
})();

document.querySelectorAll('.demo-keyword-chip').forEach(btn => {
  btn.addEventListener('click', () => {
    document.getElementById('keywords').value = btn.dataset.keyword;
    runSearch();
  });
});

function _mockHoursAgo(dateStr) {
  return (MOCK_NOW - new Date(dateStr).getTime()) / 3600000;
}

// Demo: strip dates from all jobs so posted-within filter has no effect
// and no misleading "8 days ago" labels appear.
MOCK_DATA.jobs.forEach(j => { j.date_posted = null; });

function _mockMatchesWorkModel(job, workModels) {
  const wm = new Set(workModels || []);
  if (wm.size === 0 || wm.size === 3) return true;
  if (wm.has('remote') && job.is_remote) return true;
  if (wm.has('hybrid') && job.is_hybrid) return true;
  if (wm.has('onsite') && !job.is_remote && !job.is_hybrid) return true;
  return false;
}

function mockSearchApi({ keywords, countries, sources, hours_old, title_only, work_models }, signal) {
  return new Promise((resolve, reject) => {
    const t0 = performance.now();
    const timer = setTimeout(() => {
      const kw = (keywords || '').toLowerCase();
      const results = MOCK_DATA.jobs.filter(job => {
        if (!sources.includes(job.source)) return false;
        if (countries && countries.length) {
          const dc = job.detected_countries || [];
          if (!dc.includes('remote') && !countries.some(c => dc.includes(c))) return false;
        }
        if (!_mockMatchesWorkModel(job, work_models)) return false;
        if (kw) {
          const inTitle = job.title.toLowerCase().includes(kw);
          const inDesc  = !title_only && (job.description || '').toLowerCase().includes(kw);
          if (!inTitle && !inDesc) return false;
        }
        return true;
      });
      resolve({
        results,
        sources_queried: sources,
        warnings: [],
        duration_seconds: parseFloat(((performance.now() - t0) / 1000).toFixed(2)),
        linkedin_rate_limited: false,
      });
    }, 500);

    if (signal) {
      if (signal.aborted) {
        clearTimeout(timer);
        reject(new DOMException('Aborted', 'AbortError'));
        return;
      }
      signal.addEventListener('abort', () => {
        clearTimeout(timer);
        reject(new DOMException('Aborted', 'AbortError'));
      }, { once: true });
    }
  });
}
'''

old = "const PAGE_SIZE = 10;\n"
if content.count(old) != 1:
    sys.exit(f"ERROR: expected exactly 1 occurrence of 'const PAGE_SIZE = 10;', found {content.count(old)}")
content = content.replace(old, old + MOCK_BLOCK, 1)

# ------------------------------------------------------------------
# 3. loadSources(): /api/sources -> MOCK_DATA.sources
# ------------------------------------------------------------------
old = "    const resp = await fetch('/api/sources');\n    const sources = await resp.json();\n"
new = "    const sources = MOCK_DATA.sources;\n"
if content.count(old) != 1:
    sys.exit(f"ERROR: expected exactly 1 occurrence of /api/sources fetch, found {content.count(old)}")
content = content.replace(old, new, 1)

# ------------------------------------------------------------------
# 4. runSearch(): /api/search fetch -> mockSearchApi()
# ------------------------------------------------------------------
old = """    const resp = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keywords, countries, sources, hours_old: hoursOld, title_only: titleOnly, work_models: workModels }),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      showError(err.error || `Server error ${resp.status}`);
      return;
    }

    const data = await resp.json();
"""
new = "    const data = await mockSearchApi({ keywords, countries, sources, hours_old: hoursOld, title_only: titleOnly, work_models: workModels });\n"
if content.count(old) != 1:
    sys.exit(f"ERROR: expected exactly 1 occurrence of /api/search fetch block, found {content.count(old)}")
content = content.replace(old, new, 1)

# ------------------------------------------------------------------
# 5a. loadSourceHealth(): /api/source-health -> MOCK_DATA.sourceHealth
# ------------------------------------------------------------------
old5a = "    const resp = await fetch('/api/source-health');\n    _sourceHealth = await resp.json();\n"
new5a = "    _sourceHealth = MOCK_DATA.sourceHealth;\n"
if content.count(old5a) != 1:
    sys.exit(f"ERROR: expected exactly 1 occurrence of /api/source-health fetch, found {content.count(old5a)}")
content = content.replace(old5a, new5a, 1)

# ------------------------------------------------------------------
# 5. Demo NEW badge: mark 3 newest results as NEW after each search
# ------------------------------------------------------------------
old5 = "    state.activeSourceFilter = 'ALL';\n    state.activeCountries = new Set();\n    state.activeWorkModelFilter = new Set();\n"
new5 = """    // Demo only: on every search, mark the 3 newest matching results as NEW
    // unless they have already been viewed (clicked) by the user.
    (function() {
      const viewedIds = _getViewed();
      const viewedSids = _getViewedSeenIds();
      const sorted = [...(state.allResults || [])].sort((a, b) => new Date(b.date_posted) - new Date(a.date_posted));
      sorted.slice(0, 3).forEach(j => {
        if (!viewedIds.has(j.id) && !viewedSids.has(_jobSeenId(j))) {
          newJobIds.add(_jobSeenId(j));
        }
      });
    })();
    state.activeSourceFilter = 'ALL';
    state.activeCountries = new Set();
    state.activeWorkModelFilter = new Set();
"""
if content.count(old5) != 1:
    sys.exit(f"ERROR: expected exactly 1 occurrence of mockSearchApi call, found {content.count(old5)}")
content = content.replace(old5, new5, 1)

# ------------------------------------------------------------------
# 6. Tracker demo data: seed the Job Application Tracker tab with
#    sample entries showcasing interview rounds and the Offer status.
#    Only applies when localStorage is empty (first visit) - real
#    users of the self-hosted app are unaffected since this patches
#    docs/index.html only, never templates/index.html.
# ------------------------------------------------------------------
TRACKER_DEMO_BLOCK = '''
const TRACKER_DEMO_JOBS = [
  { id: 'demo-tr1', company: 'Bramblewood Tech', title: 'Senior Content Strategist', location: 'Berlin, Germany', workModel: 'Remote', platform: 'Greenhouse', url: '', status: 'Saved', notes: 'Strong match on docs-as-code and API documentation experience.', dateAdded: '2026-06-14', lastModified: '2026-06-14T09:00:00.000Z', interviewRounds: [] },
  { id: 'demo-tr2', company: 'Solvix Technologies', title: 'Senior Technical Writer', location: 'Vienna, Austria', workModel: 'On-site', platform: 'Karriere.at', url: '', status: 'Applied', notes: 'Applied via the company careers page. Recruiter confirmed receipt.', dateAdded: '2026-06-07', lastModified: '2026-06-07T09:00:00.000Z', interviewRounds: [] },
  { id: 'demo-tr3', company: 'Pinegrove Cloud', title: 'Documentation Engineer', location: 'Amsterdam, Netherlands', workModel: 'Hybrid', platform: 'Indeed EU', url: '', status: 'Interviewing', notes: 'First round done, technical round scheduled next.', dateAdded: '2026-06-03', lastModified: '2026-07-15T09:00:00.000Z',
    interviewRounds: [
      { id: 'demo-r1', datetime: '2026-06-20T10:00', type: 'Online', link: 'https://meet.google.com/pinegrove-r1', attendees: 'Marc de Groot (Hiring Manager)', notes: 'Phone/video screen. Discussed content strategy background.', outcome: 'passed', done: true },
      { id: 'demo-r2', datetime: '2026-07-15T11:00', type: 'Technical', link: '', attendees: 'Marc de Groot (Hiring Manager), Els Bakker (Content Lead)', notes: 'Prep: review portfolio pieces on docs-as-code migration.', done: false },
    ]
  },
  { id: 'demo-tr4', company: 'Quill Software', title: 'UX Writer', location: 'Berlin, Germany', workModel: 'Remote', platform: 'LinkedIn', url: '', status: 'Offer', notes: 'Offer received - reviewing compensation details.', dateAdded: '2026-05-20', lastModified: '2026-06-25T09:00:00.000Z',
    interviewRounds: [
      { id: 'demo-r3', datetime: '2026-06-01T10:00', type: 'Online', link: 'https://meet.google.com/quill-r1', attendees: 'Priya Shah (Recruiter)', notes: 'Recruiter screen. Discussed role scope and salary band.', outcome: 'passed', done: true },
      { id: 'demo-r4', datetime: '2026-06-10T14:00', type: 'Online', link: 'https://meet.google.com/quill-r2', attendees: 'Priya Shah (Recruiter), Daniel Weiss (Design Lead)', notes: 'Portfolio review and a writing exercise walkthrough.', outcome: 'passed', done: true },
    ]
  },
  { id: 'demo-tr5', company: 'Maplewood Digital', title: 'Customer Support Specialist', location: 'Linz, Austria', workModel: 'On-site', platform: 'Karriere.at', url: '', status: 'Rejected', notes: 'Rejected after the phone screening - turned out to be a mismatch in expectations on both sides (compensation and scope).', dateAdded: '2026-05-29', lastModified: '2026-06-05T14:00:00.000Z',
    interviewRounds: [
      { id: 'demo-r5', datetime: '2026-06-05T14:00', type: 'Online', link: 'https://meet.google.com/maplewood-r1', attendees: 'Sandra Huber (HR)', notes: 'Phone screening with HR. Discussed role scope, salary expectations and availability.', outcome: 'failed', done: true },
    ]
  },
  { id: 'demo-tr6', company: 'Cedarhill Software', title: 'Technical Writer', location: 'Remote – EU', workModel: 'Remote', platform: 'Remotive', url: '', status: 'Applied', notes: 'Applied via careers page. Good match on API docs and structured authoring.', dateAdded: '2026-07-08', lastModified: '2026-07-08T10:00:00.000Z', interviewRounds: [] },
  { id: 'demo-tr7', company: 'Ashford Analytics', title: 'Product Manager', location: 'Warsaw, Poland', workModel: 'Hybrid', platform: 'Indeed EU', url: '', status: 'Applied', notes: 'Referral from a contact at the company. Role aligns well with past experience.', dateAdded: '2026-07-15', lastModified: '2026-07-15T14:00:00.000Z', interviewRounds: [] },
];
'''

old6 = "function trLoad() {\n  try { const raw = localStorage.getItem(TR_KEY); trJobs = raw ? JSON.parse(raw) : []; }\n  catch { trJobs = []; }\n}\n"
if content.count(old6) != 1:
    sys.exit(f"ERROR: expected exactly 1 occurrence of trLoad(), found {content.count(old6)}")
new6 = TRACKER_DEMO_BLOCK + '''
function trLoad() {
  try {
    const raw = localStorage.getItem(TR_KEY);
    trJobs = raw ? JSON.parse(raw) : JSON.parse(JSON.stringify(TRACKER_DEMO_JOBS));
  } catch { trJobs = []; }
}
'''
content = content.replace(old6, new6, 1)

# ------------------------------------------------------------------
# 7. "Clear sample jobs" button for the demo tracker - removes only
#    demo-tr-prefixed entries, leaves anything the visitor added
#    themselves untouched, and hides itself once none remain.
# ------------------------------------------------------------------
old7a = '''      <button class="tr-btn" onclick="document.getElementById('tr-import-input').click()">Import List</button>
      <input type="file" id="tr-import-input" accept=".csv" style="display:none" onchange="trImportCSV(event)">
    </div>'''
new7a = '''      <button class="tr-btn" onclick="document.getElementById('tr-import-input').click()">Import List</button>
      <input type="file" id="tr-import-input" accept=".csv" style="display:none" onchange="trImportCSV(event)">
      <button class="tr-btn" id="tr-clearSampleBtn" onclick="trClearSampleJobs()" style="display:none">Clear sample jobs</button>
    </div>'''
if content.count(old7a) != 1:
    sys.exit(f"ERROR: expected exactly 1 occurrence of the tracker toolbar closing tag, found {content.count(old7a)}")
content = content.replace(old7a, new7a, 1)

old7b = """  document.getElementById('tr-stats').innerHTML = statDefs.map(f =>
    `<button class="tr-stat-btn${trFilter === f.key ? ' active-' + f.key : ''}" onclick="trSetFilter('${f.key}')">${f.label} <strong>${f.count}</strong></button>`
  ).join('');
"""
new7b = old7b + """
  const clearSampleBtn = document.getElementById('tr-clearSampleBtn');
  if (clearSampleBtn) clearSampleBtn.style.display = trJobs.some(j => j.id.startsWith('demo-tr')) ? '' : 'none';
"""
if content.count(old7b) != 1:
    sys.exit(f"ERROR: expected exactly 1 occurrence of the tr-stats innerHTML block, found {content.count(old7b)}")
content = content.replace(old7b, new7b, 1)

old7c = "function trSetFilter(f) { trFilter = f; trPage = 1; trRender(); }\n"
new7c = old7c + """
function trClearSampleJobs() {
  const sampleCount = trJobs.filter(j => j.id.startsWith('demo-tr')).length;
  if (!sampleCount) return;
  if (!confirm(`Remove ${sampleCount} sample job${sampleCount > 1 ? 's' : ''}? This can't be undone.`)) return;
  trJobs = trJobs.filter(j => !j.id.startsWith('demo-tr'));
  trPersist();
  trRender();
  trToast('Sample jobs removed.');
}
"""
if content.count(old7c) != 1:
    sys.exit(f"ERROR: expected exactly 1 occurrence of trSetFilter(), found {content.count(old7c)}")
content = content.replace(old7c, new7c, 1)

with open(DST, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Done. {DST} regenerated from {SRC} with demo changes applied (search mock data + tracker sample jobs + clear-samples button).")

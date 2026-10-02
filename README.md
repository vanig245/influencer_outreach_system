# Influencer Outreach System

A Python pipeline that finds micro-influencers on Instagram, filters them against configurable criteria, enriches their profiles with real public data, writes personalized outreach with an LLM, and manages delivery through a duplicate-safe sending layer with a full outreach log.

I built it to automate the repetitive parts of influencer marketing (finding relevant creators, checking whether they fit, and writing a message that doesn't read like a template) while keeping every data point honest. Nothing in the dataset is estimated or invented: if a value can't be found, it is marked as unavailable.

```
Discovery → Enrichment → Filtering → AI Personalization → Sending → Tracking
```

## Features

- Discovers creators from niche hashtags on Instagram using managed scrapers (Apify)
- Computes engagement rate from each creator's recent posts instead of assuming a value
- Extracts contact emails only from public fields (business email or bio), otherwise records `Not Found`
- Filters creators on follower range and engagement, with results saved as Passed or Failed
- Generates a 60 to 90 word email pitch and a 15 to 30 word Instagram DM per shortlisted creator, validating length and retrying on failure
- Sends emails in a simulated mode with duplicate prevention and a status log
- Queues Instagram DMs for manual sending, since automated DMs are not permitted through public APIs
- Runs as one command or one stage at a time, with every setting in a single config file

## Tech stack

| Area | Tool |
|------|------|
| Language | Python 3.10+ |
| Scraping | Apify actors via `apify-client` |
| LLM | Groq API, model `openai/gpt-oss-120b` |
| Data processing | pandas |
| Concurrency | `concurrent.futures` (threaded message generation) |
| Configuration | `python-dotenv` for secrets, `config.py` for settings |
| Storage | JSON and CSV files in `data/` |

## Project structure

```
influencer-outreach/
├── main.py                 # runs the full pipeline
├── config.py               # niche hashtags, thresholds, brand profile, offer, paths
├── requirements.txt
├── .env                    # API keys (not committed)
├── src/
│   ├── discovery.py        # hashtag search + profile scraping
│   ├── enrichment.py       # metrics, email extraction, content themes
│   ├── filtering.py        # pass/fail classification
│   ├── personalization.py  # LLM-generated email and DM
│   └── sender.py           # simulated email sending, DM queue, outreach log
└── data/
    ├── raw_profiles.json   # raw scraper output
    ├── enriched.csv        # full dataset
    ├── filtered.csv        # dataset with Passed / Failed status
    ├── messages.csv        # generated email pitches and DMs
    ├── outreach_log.csv    # sending tracker
    └── dm_queue.csv        # manual-send queue for Instagram DMs
```

## How it works

### 1. Discovery
`discovery.py` runs in two phases. First it searches a list of niche hashtags with Apify's Instagram hashtag scraper and collects the owners of recent public posts. Then it scrapes each unique public profile (capped at 60 per run to protect free-tier credits) for followers, bio, business email, external link, and recent posts with likes and comments. Raw output goes to `data/raw_profiles.json`. Targeting narrower hashtags such as `techreviewer` or `gadgetreview` surfaces mid-sized creators far more often than a broad tag like `tech`, which is dominated by large brands.

### 2. Enrichment
`enrichment.py` flattens the raw JSON into one record per creator:

- **Engagement rate** is the average of (likes + comments) over recent posts, divided by follower count. Posts with hidden likes are excluded, and if nothing can be computed the value stays empty.
- **Contact email** is taken from the public business-email field or the bio using a pattern match. If neither has one, the value is `Not Found`. Addresses are never guessed or constructed.
- **Content themes** come from the most frequent hashtags in recent posts, falling back to the bio.
- **Profile URL, website, platform, follower count** are copied from the scraped profile.

Audience age, gender and geography are not publicly exposed by Instagram, so the pipeline does not report them.

### 3. Filtering
`filtering.py` evaluates every enriched profile against the thresholds in `config.py` (follower range 5,000 to 100,000 and a minimum engagement rate of 2.0%) and writes a Passed or Failed status for each. Profiles with missing metrics fail rather than pass by default. Thresholds are plain config values, so retargeting a different niche or audience size is a one-line change.

### 4. Personalization
`personalization.py` calls the Groq API once per shortlisted creator, in parallel threads. The prompt receives the creator's name, bio and content themes, along with the brand description, collaboration angle, offer and sender name from `config.py`. It instructs the model to avoid hashtags and emojis, to invent no facts or terms beyond the offer, and to fall back to a generic greeting when the account name isn't a person's name. The output is then checked in code (email 60 to 90 words, DM 15 to 30 words), and a message outside the range triggers up to three regeneration attempts. If all attempts fail, the row is marked as an error and skipped by the sender.

### 5. Sending layer
`sender.py` selects creators with a valid, format-checked public email, retrieves their generated pitch, and logs each send with a status and timestamp. Sending is simulated: the full message is printed and recorded as `Simulated Send Success`. Duplicate prevention checks the log before every send, so rerunning the pipeline never contacts the same address twice. Creators without an email are logged as `Skipped - No Email`.

Instagram DMs are never sent automatically. Platform rules don't permit automated DMs through public APIs, so every DM is written to `data/dm_queue.csv` with a profile link and a `Pending - send manually` status. Existing rows are preserved between runs, so statuses you

## Setup

1. Clone the repository and create a virtual environment:
```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
   pip install -r requirements.txt
```
   `requirements.txt` contains `apify-client`, `groq`, `pandas` and `python-dotenv`.

3. Create a `.env` file in the project root:
```
   APIFY_API_TOKEN=your_apify_token
   GROQ_API_KEY=your_groq_key
```

4. Edit `config.py` to set your hashtags, follower and engagement thresholds, brand description, collaboration angle, offer and sender name.

## Usage

Run the whole pipeline:

```bash
python3 main.py
```

Or run a single stage, which is useful for testing without re-scraping:

```bash
python3 src/discovery.py
python3 src/enrichment.py
python3 src/filtering.py
python3 src/personalization.py
python3 src/sender.py
```

If a stage fails, `main.py` stops immediately instead of running later stages on stale files. To start a clean run, delete the generated files in `data/`, especially `outreach_log.csv` and `dm_queue.csv`, which carry state between runs.

## Sample run

One run on technology hashtags produced the following. Results vary between runs.

| Stage | Result |
|-------|--------|
| Profiles scraped | 60 |
| Profiles with a real public email | 6 |
| Passed filtering | 5 |
| Emails simulated | creators who passed and had a valid email |
| DMs queued for manual sending | all 5 shortlisted creators |

Most creators don't publish an email, which is why only about one in ten profiles has one. They are still reachable through the DM queue.

## Design decisions

- **Real data only.** Missing values are labeled, never filled. This keeps the dataset trustworthy and makes the pipeline's limits visible.
- **Respect platform boundaries.** Only public data is collected, no login is used, and DMs stay manual.
- **One config file.** Switching niche, thresholds or brand requires no code changes.
- **Stage isolation.** Each stage reads one file and writes another, so any stage can be rerun alone and a failure never loses earlier work.
- **Validation over trust.** LLM output is length-checked and retried, and failed generations are never sent.

## Limitations

- Public Instagram data is limited. Many creators have no public email, and audience demographics are not available.
- Engagement rate is based on a handful of recent posts and can be noisy.
- On Apify's free tier the hashtag scraper returns roughly one page of posts per hashtag, so the candidate pool depends on how many hashtags you use.
- Scraper output fields depend on third-party actors and may change over time.
- Email sending is simulated. There is no SMTP or Gmail integration yet, and replies and deliverability are not tracked.
- Content themes are derived from hashtags and bios, so they are approximate.
- The offer terms and sender name in the sample configuration are demo values.

## Scaling and next steps

Scaling from dozens to hundreds of creators means adding hashtags and raising the profile cap in `config.py`, since the stages are already independent. Natural extensions are a real email transport (SMTP or Gmail API) behind the existing log and duplicate check, a database in place of CSV files, reply tracking, and a brand-fit scoring step that uses an LLM to judge relevance before shortlisting.

## Author

Vani Gupta 
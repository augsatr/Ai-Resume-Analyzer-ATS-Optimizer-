# AI Resume Analyzer & ATS Optimizer

A tool where users can upload their resume and:
- Get an ATS compatibility score
- Receive keyword suggestions based on a job description
- Improve bullet points using AI

This showcases a practical AI application combined with an understanding of how modern hiring systems (ATS) evaluate candidates.

## Features

- **ATS Scoring** — 10-category weighted engine evaluating keyword match, formatting, contact info, sections, quantified impact, action verbs, education, experience, length, and skills depth. Includes radar chart visualization.
- **Keyword Matching** — TF-IDF extraction with skill categorization across 9 categories (programming languages, frontend, backend, database, cloud/devops, data/ML, tools/methods, soft skills, domain). Highlights matched and missing keywords.
- **Skills Gap Analysis** — Per-category coverage metrics showing strengths and weaknesses relative to the job description.
- **AI Bullet Point Improver** — Local rule-based engine + optional OpenAI integration. Rewrites passive voice, adds quantified impact, generates STAR method context for each bullet.
- **Resume Parsing** — PDF and DOCX support with section detection, contact extraction (email, phone, LinkedIn), formatting issue detection.
- **Interactive Dashboard** — Canvas radar chart, keyword tags, category breakdown bars, batch bullet improvement, highlighted resume text preview.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12+, Flask |
| NLP | scikit-learn (TF-IDF), NLTK |
| Parsing | PyMuPDF, python-docx |
| AI (optional) | OpenAI API |
| Frontend | Vanilla JS, Canvas API, CSS3 |

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000 in your browser.

### Optional: AI-Powered Bullet Improvements

Set the `OPENAI_API_KEY` environment variable to enable GPT-3.5/4 rewrites with STAR method output:

```bash
export OPENAI_API_KEY=sk-...
# or on Windows:
# set OPENAI_API_KEY=sk-...
```

Without the API key, the app uses a local rule-based engine.

## Usage

1. **Upload Resume** — Drag and drop or click to select a PDF or DOCX file.
2. **Paste Job Description** (optional) — Required for ATS scoring and keyword matching.
3. **Click Analyze** — The engine parses the resume, extracts text and sections, and compares it against the job description.
4. **Review Results**:
   - **Score Overview** — Overall ATS score (0–100) with radar chart and category breakdown.
   - **Detailed Feedback** — Actionable success/warning/error items per category.
   - **Keywords tab** — Matched and missing keywords with category-level coverage.
   - **Skills Gap tab** — Per-category match rates with specific missing terms.
   - **Bullet Improver tab** — Single or batch improvement with STAR context.
   - **Resume Text tab** — Parsed text with highlighted matched keywords and contact info badges.

## Project Structure

```
├── app.py                  # Flask routes and API endpoints
├── resume_parser.py        # PDF/DOCX parsing, section extraction, contact detection
├── ats_scorer.py           # Weighted ATS scoring across 10 categories
├── keyword_extractor.py    # TF-IDF extraction, skill taxonomy, categorization
├── bullet_improver.py      # Bullet rewriting (local rules + optional OpenAI)
├── requirements.txt
├── static/
│   ├── style.css
│   └── script.js           # Frontend with Canvas radar chart
└── templates/
    └── index.html
```

## How ATS Scoring Works

The scoring engine mimics real-world ATS behavior by evaluating 10 weighted dimensions:

| Category | Weight | What It Checks |
|----------|--------|----------------|
| Keyword Match | 22% | TF-IDF keyword overlap between resume and JD |
| Quantified Impact | 15% | Numbers, percentages, dollar amounts, time metrics |
| Action Verbs | 10% | Diversity and frequency of strong leadership verbs |
| Experience | 10% | Employment dates, company names, job titles, bullet points |
| Skills Depth | 10% | Coverage across 9 skill categories from the taxonomy |
| Formatting | 8% | Tabs, line lengths, bullet point usage |
| Sections | 8% | Presence of Experience, Education, Skills, Summary, etc. |
| Education | 8% | Degree, institution, graduation year, GPA, major |
| Contact Info | 5% | Email, phone, LinkedIn presence |
| Length | 4% | Word count optimization (400–700 words ideal) |

## License

MIT License — see [LICENSE](LICENSE).

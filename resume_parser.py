import fitz
import docx
import re
import os

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_RE = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
LINKEDIN_RE = re.compile(r'(?:https?://)?(?:www\.)?linkedin\.com/\S+', re.I)
URL_RE = re.compile(r'https?://[^\s]+')

SECTION_PATTERNS = [
    (r'(experience|work\s*history|employment|professional\s*experience)', 'experience'),
    (r'(education|academic|qualification|education\s*background)', 'education'),
    (r'(skills|technical\s*skills|core\s*competencies|technologies|expertise)', 'skills'),
    (r'(projects?|personal\s*projects?|key\s*projects)', 'projects'),
    (r'(certifications?|licenses?|professional\s*certifications)', 'certifications'),
    (r'(summary|professional\s*summary|profile|objective|about\s*me)', 'summary'),
    (r'(publications?|research|papers)', 'publications'),
    (r'(languages|spoken\s*languages)', 'languages'),
    (r'(awards|honors?|achievements)', 'awards'),
    (r'(volunteer|volunteering|community)', 'volunteer'),
]

def parse_pdf(filepath):
    try:
        doc = fitz.open(filepath)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return _clean_text('\n'.join(text_parts))
    except Exception as e:
        raise Exception(f"PDF parse error: {str(e)}")

def parse_docx(filepath):
    try:
        doc = docx.Document(filepath)
        lines = []
        for para in doc.paragraphs:
            lines.append(para.text)
        return _clean_text('\n'.join(lines))
    except Exception as e:
        raise Exception(f"DOCX parse error: {str(e)}")

def parse_resume(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        text = parse_pdf(filepath)
    elif ext in (".docx", ".doc"):
        text = parse_docx(filepath)
    else:
        raise Exception("Unsupported format. Use PDF or DOCX.")
    if len(text.strip()) < 50:
        raise Exception("Could not extract enough text. The file may be scanned/image-based (not supported).")
    return text

def _clean_text(text):
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)
    text = re.sub(r'[^\x00-\x7F\n]+', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_contact_info(text):
    emails = EMAIL_RE.findall(text)
    phones = [m.group(0) for m in PHONE_RE.finditer(text)]
    phones = [re.sub(r'[^\d+]', '', p) for p in phones if p]
    linkedin = [m.group(0) for m in LINKEDIN_RE.finditer(text)]
    urls = [u for u in URL_RE.findall(text) if 'linkedin' not in u.lower()]
    return {
        'emails': list(set(emails)),
        'phones': list(set(p for p in phones if len(p) >= 10)),
        'linkedin': list(set(linkedin)),
        'urls': list(set(urls)),
    }

def extract_bullet_points(text):
    lines = text.split('\n')
    bullets = []
    for line in lines:
        stripped = line.strip()
        if stripped and re.match(r'^[\s]*[•\-*\d+.]', stripped):
            bullets.append(stripped)
    if not bullets:
        non_empty = [l.strip() for l in lines if l.strip()]
        bullets = non_empty[:20]
    return bullets

def extract_sections(text):
    sections = {}
    lines = text.split('\n')
    current_section = 'header'
    sections[current_section] = []
    for line in lines:
        lower = line.strip().lower()
        matched = False
        for pattern, section_name in SECTION_PATTERNS:
            if re.match(pattern, lower):
                current_section = section_name
                matched = True
                break
        if current_section not in sections:
            sections[current_section] = []
        sections[current_section].append(line)
    return sections

def extract_experience_entries(text):
    lines = text.split('\n')
    entries = []
    current = []
    date_pattern = re.compile(
        r'(19|20)\d{2}\s*[-–to]+\s*(19|20)\d{2}|'
        r'(19|20)\d{2}\s*[-–to]+\s*(present|current|now)|'
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}',
        re.I
    )
    in_experience = False
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if any(re.match(p, lower) for p, _ in SECTION_PATTERNS):
            if in_experience and current:
                entries.append('\n'.join(current))
                current = []
            in_experience = False
        if re.match(r'(experience|work\s*history|employment)', lower):
            in_experience = True
            continue
        if in_experience:
            if date_pattern.search(stripped) and len(stripped.split()) <= 15 and current:
                entries.append('\n'.join(current))
                current = [stripped]
            else:
                current.append(stripped)
    if current and in_experience:
        entries.append('\n'.join(current))
    return entries

def detect_formatting_issues(text):
    issues = []
    lines = text.split('\n')
    tab_count = sum(1 for l in lines if '\t' in l)
    if tab_count > 5:
        issues.append('tabs')
    multi_space = sum(1 for l in lines if re.search(r'  +', l))
    if multi_space > 10:
        issues.append('excessive_spacing')
    long_lines = sum(1 for l in lines if len(l) > 250)
    if long_lines > 3:
        issues.append('long_lines')
    return issues

def get_resume_stats(text):
    words = text.split()
    lines = text.split('\n')
    non_empty = [l for l in lines if l.strip()]
    char_count = len(text)
    return {
        'word_count': len(words),
        'line_count': len(lines),
        'non_empty_lines': len(non_empty),
        'char_count': char_count,
        'avg_words_per_bullet': 0,
    }

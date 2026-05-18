import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

STOP_WORDS = set([
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'could', 'should', 'may', 'might', 'shall', 'can', 'need',
    'dare', 'ought', 'used', 'this', 'that', 'these', 'those', 'i', 'me',
    'my', 'we', 'our', 'you', 'your', 'he', 'she', 'it', 'they', 'them',
    'his', 'her', 'its', 'their', 'am', 'not', 'no', 'nor', 'so', 'if',
    'then', 'than', 'too', 'very', 'just', 'about', 'also', 'more',
    'most', 'some', 'any', 'each', 'every', 'all', 'both', 'few', 'many',
    'much', 'such', 'own', 'same', 'other', 'another', 'well', 'get',
    'got', 'able', 'like', 'made', 'make', 'take', 'use', 'using', 'used'
])

SKILL_TAXONOMY = {
    'programming_languages': [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby',
        'php', 'swift', 'kotlin', 'go', 'golang', 'rust', 'scala', 'perl',
        'r', 'matlab', 'sql', 'bash', 'shell', 'powershell', 'dart',
    ],
    'frontend': [
        'react', 'angular', 'vue', 'svelte', 'nextjs', 'nuxt', 'html',
        'css', 'sass', 'less', 'tailwind', 'bootstrap', 'jquery', 'redux',
        'webpack', 'vite', 'typescript', 'javascript', 'd3.js', 'chart.js',
    ],
    'backend': [
        'django', 'flask', 'fastapi', 'spring', 'spring boot', 'express',
        'node', 'nodejs', 'rails', 'laravel', 'asp.net', 'graphql',
        'rest', 'restful', 'soap', 'grpc', 'microservices',
    ],
    'database': [
        'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'redis',
        'sqlite', 'oracle', 'sql server', 'mariadb', 'cassandra',
        'dynamodb', 'elasticsearch', 'bigquery', 'snowflake', 'redshift',
    ],
    'cloud_devops': [
        'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes',
        'jenkins', 'github actions', 'gitlab ci', 'terraform', 'ansible',
        'puppet', 'chef', 'circleci', 'travis ci', 'helm', 'prometheus',
        'grafana', 'datadog', 'new relic', 'splunk',
    ],
    'data_ml': [
        'machine learning', 'deep learning', 'nlp', 'computer vision',
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas',
        'numpy', 'scipy', 'tableau', 'power bi', 'looker', 'airflow',
        'spark', 'hadoop', 'kafka', 'data science', 'analytics',
        'statistical modeling', 'regression', 'classification', 'llm',
    ],
    'tools_methods': [
        'git', 'linux', 'agile', 'scrum', 'kanban', 'jira', 'confluence',
        'ci/cd', 'devops', 'sdlc', 'test-driven development', 'tdd',
        'unit testing', 'integration testing', 'api testing',
    ],
    'soft_skills': [
        'leadership', 'management', 'communication', 'teamwork',
        'problem-solving', 'critical thinking', 'project management',
        'mentoring', 'collaboration', 'presentation', 'negotiation',
        'stakeholder management', 'time management', 'adaptability',
    ],
    'domain': [
        'fintech', 'healthcare', 'e-commerce', 'saas', 'enterprise',
        'startup', 'b2b', 'b2c', 'cybersecurity', 'blockchain', 'iot',
    ],
}

ACTION_VERBS = [
    'achieved', 'improved', 'led', 'managed', 'delivered', 'developed',
    'created', 'designed', 'implemented', 'launched', 'reduced', 'increased',
    'generated', 'saved', 'optimized', 'transformed', 'built', 'established',
    'negotiated', 'coordinated', 'spearheaded', 'architected', 'engineered',
    'drove', 'enhanced', 'expanded', 'accelerated', 'streamlined', 'automated',
    'consolidated', 'reorganized', 'restructured', 'pioneered', 'introduced',
    'facilitated', 'mentored', 'trained', 'coached', 'directed', 'oversaw',
    'championed', 'executed', 'formulated', 'instituted',
]

def tokenize(text):
    text = text.lower()
    tokens = re.findall(r'\b[a-z]+(?:[-/][a-z]+)*\b', text)
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]

def extract_keywords_tfidf(text, top_n=50):
    sentences = re.split(r'[.!?\n]', text)
    sentences = [s.strip() for s in sentences if len(s.strip().split()) > 2]
    if len(sentences) < 2:
        tokens = tokenize(text)
        freq = Counter(tokens)
        return [word for word, _ in freq.most_common(top_n)]
    try:
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=200,
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.8,
        )
        matrix = vectorizer.fit_transform(sentences)
        scores = zip(vectorizer.get_feature_names_out(), matrix.sum(axis=0).tolist()[0])
        sorted_terms = sorted(scores, key=lambda x: x[1], reverse=True)
        return [term for term, score in sorted_terms[:top_n]]
    except Exception:
        tokens = tokenize(text)
        freq = Counter(tokens)
        return [word for word, _ in freq.most_common(top_n)]

def classify_skill(term):
    term_lower = term.lower()
    for category, skills in SKILL_TAXONOMY.items():
        for skill in skills:
            if skill in term_lower or term_lower in skill:
                return category
            if term_lower.replace(' ', '') == skill.replace(' ', ''):
                return category
    return 'other'

def extract_keywords_job_description(text, top_n=50):
    keywords = extract_keywords_tfidf(text, top_n)
    all_skills = set()
    for category, skills in SKILL_TAXONOMY.items():
        for skill in skills:
            all_skills.add(skill)
    text_lower = text.lower()
    domain_terms = []
    for term in all_skills:
        if term in text_lower:
            domain_terms.append(term)
    combined = list(dict.fromkeys(keywords + domain_terms))
    return combined[:top_n]

def extract_keywords_resume(text, top_n=50):
    return extract_keywords_tfidf(text, top_n)

def categorize_keywords(keywords):
    categorized = {}
    for kw in keywords:
        cat = classify_skill(kw)
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(kw)
    return categorized

def match_keywords(resume_keywords, jd_keywords):
    resume_set = set(k.lower() for k in resume_keywords)
    jd_set = set(k.lower() for k in jd_keywords)
    matched = resume_set & jd_set
    missing = jd_set - resume_set
    match_rate = len(matched) / len(jd_set) * 100 if jd_set else 0

    matched_categorized = categorize_keywords(matched)
    missing_categorized = categorize_keywords(missing)

    return {
        'matched': sorted(matched),
        'missing': sorted(missing)[:40],
        'match_rate': round(match_rate, 1),
        'total_jd_keywords': len(jd_set),
        'matched_count': len(matched),
        'matched_categorized': {k: v for k, v in sorted(matched_categorized.items())},
        'missing_categorized': {k: v for k, v in sorted(missing_categorized.items())},
    }

def get_skills_gap(matched_categorized, missing_categorized):
    gaps = {}
    all_categories = set(list(matched_categorized.keys()) + list(missing_categorized.keys()))
    for cat in all_categories:
        matched_set = set(matched_categorized.get(cat, []))
        missing_set = set(missing_categorized.get(cat, []))
        total = len(matched_set) + len(missing_set)
        if total > 0:
            rate = round(len(matched_set) / total * 100, 1)
        else:
            rate = 100
        gaps[cat] = {
            'matched_count': len(matched_set),
            'missing_count': len(missing_set),
            'match_rate': rate,
            'matched': sorted(matched_set),
            'missing': sorted(missing_set),
        }
    return gaps

import re
import os
import json
import random

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

ACTION_VERBS = [
    'achieved', 'improved', 'led', 'managed', 'delivered', 'developed',
    'created', 'designed', 'implemented', 'launched', 'reduced', 'increased',
    'generated', 'saved', 'optimized', 'transformed', 'built', 'established',
    'negotiated', 'coordinated', 'spearheaded', 'architected', 'engineered',
    'drove', 'enhanced', 'expanded', 'accelerated', 'streamlined', 'automated',
    'consolidated', 'reorganized', 'restructured', 'pioneered', 'introduced',
    'facilitated', 'mentored', 'trained', 'coached', 'directed', 'oversaw',
    'championed', 'executed', 'formulated', 'instituted', 'initiated',
    'revamped', 'overhauled', 'integrated', 'migrated', 'scaled', 'deployed',
    'standardized', 'centralized', 'modernized', 'reconciled', 'forged',
]

CONTEXT_MAP = {
    'team': ['led', 'managed', 'coordinated', 'mentored', 'directed', 'oversaw'],
    'project': ['managed', 'delivered', 'executed', 'spearheaded', 'led'],
    'code': ['developed', 'engineered', 'built', 'implemented', 'architected'],
    'data': ['analyzed', 'optimized', 'transformed', 'modeled', 'processed'],
    'system': ['architected', 'designed', 'implemented', 'engineered', 'migrated'],
    'improve': ['optimized', 'enhanced', 'streamlined', 'accelerated', 'revamped'],
    'create': ['designed', 'developed', 'built', 'established', 'pioneered'],
    'save': ['reduced', 'optimized', 'streamlined', 'consolidated', 'automated'],
    'customer': ['delivered', 'managed', 'coordinated', 'facilitated', 'negotiated'],
    'report': ['analyzed', 'generated', 'produced', 'compiled', 'synthesized'],
    'test': ['validated', 'verified', 'automated', 'implemented', 'executed'],
    'deploy': ['deployed', 'released', 'launched', 'rolled out', 'migrated'],
    'design': ['designed', 'architected', 'drafted', 'blueprinted', 'prototyped'],
    'research': ['researched', 'investigated', 'explored', 'evaluated', 'assessed'],
    'train': ['trained', 'mentored', 'coached', 'upskilled', 'onboarded'],
}

METRICS = [
    " resulting in a {x}% improvement in {area}",
    " reducing {area} by {x}%",
    " increasing {area} by {x}%",
    " generating ${y} in annual {area}",
    " improving team {area} by {x}%",
    " cutting {area} costs by {x}%",
    " accelerating {area} by {x}%",
    " achieving {x}% faster {area}",
]

PERCENT_VALUES = [15, 20, 25, 30, 35, 40, 50]
DOLLAR_VALUES = ["50K", "100K", "200K", "500K", "1M"]
AREAS = [
    "efficiency", "productivity", "revenue", "performance",
    "delivery time", "processing time", "throughput",
    "customer satisfaction", "response time", "uptime",
]

def improve_bullet_point(bullet_text, job_title="", use_ai=False):
    if use_ai and OPENAI_API_KEY:
        return _improve_with_ai(bullet_text, job_title)
    else:
        return _improve_local(bullet_text)

def _improve_local(bullet_text):
    original = bullet_text.strip()
    changes = []
    improved = original

    improved = re.sub(r'^(a |an |the )', '', improved, flags=re.I)

    passive_found = _fix_passive_voice(improved, changes)
    if passive_found:
        improved = passive_found

    first_word = improved.split()[0].lower().rstrip('.,;:!?') if improved.split() else ''
    if first_word not in ACTION_VERBS and len(improved.split()) > 2 and not passive_found:
        suggestions = _suggest_action_verb(improved)
        if suggestions:
            changes.append(f"Start with a stronger action verb like '{suggestions[0]}'")
            improved = _replace_start(improved, suggestions[0])

    has_result_word = bool(re.search(
        r'(result|outcome|impact|improve|increase|reduce|deliver|achieve|save|generate|boost|accelerate|streamline)',
        improved, re.I
    ))
    if not has_result_word and len(improved.split()) > 3:
        changes.append("Include the outcome/result of your action")
        if re.search(r'\d', improved):
            pass
        else:
            improved = improved.rstrip('.') + random.choice(METRICS).format(
                x=random.choice(PERCENT_VALUES),
                y=random.choice(DOLLAR_VALUES),
                area=random.choice(AREAS)
            )

    if not re.search(r'\d', improved):
        changes.append("Add measurable impact (%, time saved, revenue, etc.)")
        improved = improved.rstrip('.') + random.choice(METRICS).format(
            x=random.choice(PERCENT_VALUES),
            y=random.choice(DOLLAR_VALUES),
            area=random.choice(AREAS)
        )

    if len(improved.split()) < 4:
        changes.append("Expand this bullet point with more detail and context")

    improved = re.sub(r'\s+', ' ', improved).strip()

    return {
        'original': original,
        'improved': improved,
        'changes': list(dict.fromkeys(changes)),
        'ai_generated': False,
        'star_context': _generate_star_context(original),
    }

def _fix_passive_voice(text, changes):
    passive_patterns = [
        (r'\bwas\s+responsible\s+for\b\s+\w+ing', 'Led'),
        (r'\bwas\s+involved\s+in\b\s+\w+ing', 'Contributed to'),
        (r'\bwas\s+part\s+of\b\s+\w+ing', 'Contributed to'),
        (r'\bworked\s+on\b\s+\w+ing', 'Developed'),
        (r'\bwas\s+in\s+charge\s+of\b\s+\w+ing', 'Directed'),
        (r'\bwas\s+leading\b', 'Led'),
        (r'\bwas\s+managing\b', 'Managed'),
        (r'\bwas\s+responsible\s+for\b', 'Owned'),
        (r'\bwas\s+involved\s+in\b', 'Contributed to'),
        (r'\bwas\s+part\s+of\b', 'Contributed to'),
        (r'\bwas\s+in\s+charge\s+of\b', 'Directed'),
        (r'\bhelped\s+with\b', 'Supported'),
        (r'\bwas\s+assigned\s+to\b', 'Owned'),
        (r'\bwas\s+tasked\s+with\b', 'Led'),
    ]
    result = text
    found = False
    for pattern, replacement in passive_patterns:
        if re.search(pattern, result, re.I):
            result = re.sub(pattern, replacement, result, flags=re.I)
            if not found:
                changes.append("Replace passive language with a strong action verb")
                found = True
    if found:
        result = re.sub(r'\s+', ' ', result).strip()
        return result
    return None

def _improve_with_ai(bullet_text, job_title=""):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        star = _generate_star_context(bullet_text)
        prompt = f"""You are a professional resume writer. Improve this resume bullet point to maximize ATS score and recruiter impact.

Job Title: {job_title or 'Not specified'}
Original: "{bullet_text}"
STAR Context: {star}

Return valid JSON only with these exact keys:
- "improved": the rewritten bullet point (start with strong action verb, include quantified impact, max 25 words)
- "changes": array of strings describing what was changed
- "star_version": optional STAR-method version (Situation, Task, Action, Result)"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
        )
        result = json.loads(response.choices[0].message.content)
        return {
            'original': bullet_text.strip(),
            'improved': result.get('improved', bullet_text.strip()),
            'changes': result.get('changes', []),
            'ai_generated': True,
            'star_version': result.get('star_version', ''),
            'star_context': star,
        }
    except Exception as e:
        fallback = _improve_local(bullet_text)
        fallback['ai_generated'] = False
        fallback['_ai_error'] = str(e)
        return fallback

def _suggest_action_verb(text):
    text_lower = text.lower()
    for verb in ACTION_VERBS:
        if verb in text_lower[:50]:
            return None
    for keyword, verbs in CONTEXT_MAP.items():
        if keyword in text_lower:
            return verbs
    return ['led', 'developed', 'managed', 'delivered', 'implemented']

def _replace_start(text, new_verb):
    words = text.split()
    if len(words) <= 1:
        return new_verb.capitalize()
    new_start = new_verb.capitalize()
    rest = ' '.join(words[1:])
    return f"{new_start} {rest}"

def _generate_star_context(text):
    text_lower = text.lower()
    has_team = any(w in text_lower for w in ['team', 'teams', 'cross-functional'])
    has_project = any(w in text_lower for w in ['project', 'initiative', 'program'])
    has_tech = any(w in text_lower for w in ['system', 'platform', 'application', 'tool', 'pipeline'])
    has_improvement = any(w in text_lower for w in ['improve', 'optimize', 'reduce', 'increase', 'automate'])
    has_customer = any(w in text_lower for w in ['customer', 'client', 'stakeholder'])
    has_data = any(w in text_lower for w in ['data', 'analytics', 'report', 'metric'])
    if has_team:
        return "S: Faced a challenging team environment | T: Needed to align diverse stakeholders | A: Coordinated cross-functional collaboration | R: Delivered on time with strong buy-in"
    if has_project:
        return "S: Complex project with tight deadline | T: Needed to deliver within constraints | A: Planned and executed systematically | R: Completed ahead of schedule"
    if has_tech:
        return "S: Legacy system needed modernization | T: Required scalable solution | A: Architected and implemented new platform | R: Improved performance and reliability"
    if has_improvement:
        return "S: Identified inefficiency in existing process | T: Needed measurable improvement | A: Analyzed and implemented changes | R: Achieved significant gains"
    if has_customer:
        return "S: Key customer facing challenges | T: Needed to exceed expectations | A: Developed tailored solution | R: Increased satisfaction and retention"
    if has_data:
        return "S: Data was siloed and inaccessible | T: Needed actionable insights | A: Built analytics pipeline | R: Enabled data-driven decisions"
    return "S: Challenging project | T: Clear objectives to meet | A: Systematic approach | R: Measurable positive outcomes"

def improve_bullet_points_batch(bullet_points, job_title="", use_ai=False):
    results = []
    for bp in bullet_points:
        result = improve_bullet_point(bp, job_title, use_ai)
        results.append(result)
    return results

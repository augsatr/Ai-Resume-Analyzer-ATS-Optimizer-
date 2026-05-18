import re
from keyword_extractor import extract_keywords_tfidf, extract_keywords_job_description, match_keywords, get_skills_gap, classify_skill, SKILL_TAXONOMY

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

SECTION_WEIGHTS = {
    'experience': 0.25,
    'education': 0.15,
    'skills': 0.25,
    'keyword_match': 0.35,
}

def score_ats(resume_text, jd_text):
    scores = {}
    feedback = []
    details = {}

    kw_score, kw_fb, kw_det = _score_keywords(resume_text, jd_text)
    scores['keyword_match'] = kw_score
    feedback.extend(kw_fb)
    details['keyword_match'] = kw_det

    fmt_score, fmt_fb, fmt_det = _score_formatting(resume_text)
    scores['formatting'] = fmt_score
    feedback.extend(fmt_fb)
    details['formatting'] = fmt_det

    contact_score, contact_fb, contact_det = _score_contact(resume_text)
    scores['contact_info'] = contact_score
    feedback.extend(contact_fb)
    details['contact_info'] = contact_det

    sections_score, sections_fb, sections_det = _score_sections(resume_text)
    scores['sections'] = sections_score
    feedback.extend(sections_fb)
    details['sections'] = sections_det

    quant_score, quant_fb, quant_det = _score_quantified(resume_text)
    scores['quantified'] = quant_score
    feedback.extend(quant_fb)
    details['quantified'] = quant_det

    verb_score, verb_fb, verb_det = _score_action_verbs(resume_text)
    scores['action_verbs'] = verb_score
    feedback.extend(verb_fb)
    details['action_verbs'] = verb_det

    edu_score, edu_fb, edu_det = _score_education(resume_text)
    scores['education'] = edu_score
    feedback.extend(edu_fb)
    details['education'] = edu_det

    exp_score, exp_fb, exp_det = _score_experience(resume_text)
    scores['experience'] = exp_score
    feedback.extend(exp_fb)
    details['experience'] = exp_det

    length_score, length_fb, length_det = _score_length(resume_text)
    scores['length'] = length_score
    feedback.extend(length_fb)
    details['length'] = length_det

    skills_score, skills_fb, skills_det = _score_skills_taxonomy(resume_text, jd_text)
    scores['skills_depth'] = skills_score
    feedback.extend(skills_fb)
    details['skills_depth'] = skills_det

    weights = {
        'keyword_match': 0.22,
        'formatting': 0.08,
        'contact_info': 0.05,
        'sections': 0.08,
        'quantified': 0.15,
        'action_verbs': 0.10,
        'education': 0.08,
        'experience': 0.10,
        'length': 0.04,
        'skills_depth': 0.10,
    }
    total = sum(scores.get(k, 0) * w for k, w in weights.items()) / sum(weights.values())
    total = round(min(max(total, 0), 100), 1)

    categorized = _categorize_feedback(feedback)

    radar_labels = [
        'Keyword\nMatch', 'Formatting', 'Contact\nInfo', 'Sections',
        'Quantified\nImpact', 'Action\nVerbs', 'Education',
        'Experience', 'Length', 'Skills\nDepth'
    ]
    radar_values = [scores.get(k, 0) for k in
        ['keyword_match', 'formatting', 'contact_info', 'sections',
         'quantified', 'action_verbs', 'education', 'experience',
         'length', 'skills_depth']]

    return {
        'total_score': total,
        'category_scores': scores,
        'feedback': feedback,
        'categorized_feedback': categorized,
        'details': details,
        'radar_labels': radar_labels,
        'radar_values': radar_values,
    }

def _score_keywords(resume_text, jd_text):
    resume_kw = extract_keywords_tfidf(resume_text, 50)
    jd_kw = extract_keywords_job_description(jd_text, 50)
    result = match_keywords(resume_kw, jd_kw)
    skills_gap = get_skills_gap(result['matched_categorized'], result['missing_categorized'])

    score = result['match_rate']
    
    bonus = 0
    if len(result['matched']) > 20:
        bonus += 5
    if len(result['matched']) > 30:
        bonus += 5

    for cat, gap in skills_gap.items():
        if gap['matched_count'] >= 3:
            bonus += 3

    score = min(score + bonus, 100)

    feedback = []
    if score >= 70:
        feedback.append({'type': 'success', 'category': 'keyword_match', 'message': f'Strong keyword match: {score}% of job description keywords found in your resume.'})
    elif score >= 40:
        feedback.append({'type': 'warning', 'category': 'keyword_match', 'message': f'Moderate keyword match ({score}%). Consider adding more relevant terms from the job description. Focus on the "missing" keywords below.'})
    else:
        feedback.append({'type': 'error', 'category': 'keyword_match', 'message': f'Low keyword match ({score}%). Your resume needs significant keyword optimization. Study the "missing" keywords and incorporate them naturally.'})

    fb_detail = result.copy()
    fb_detail['skills_gap'] = skills_gap
    return round(score, 1), feedback, fb_detail

def _score_formatting(text):
    score = 100
    feedback = []
    details = {}
    lines = text.split('\n')
    non_empty = [l for l in lines if l.strip()]
    lengths = [len(l) for l in non_empty]
    avg_len = sum(lengths) / len(lengths) if lengths else 0

    details['total_lines'] = len(non_empty)
    details['avg_line_length'] = round(avg_len, 1)
    details['max_line_length'] = max(lengths) if lengths else 0

    has_tables = bool(re.search(r'\t', text))
    if has_tables:
        score -= 15
        feedback.append({'type': 'error', 'category': 'formatting', 'message': 'Tabs detected. ATS may misparse tab-formatted content. Use standard bullet points instead.'})

    multi_space_count = len(re.findall(r'  +', text))
    if multi_space_count > 10:
        score -= 10
        feedback.append({'type': 'warning', 'category': 'formatting', 'message': f'Excessive spacing ({multi_space_count} instances) detected. Use consistent single spacing for clean ATS parsing.'})

    if max(lengths) > 300:
        score -= 15
        feedback.append({'type': 'warning', 'category': 'formatting', 'message': 'Some lines exceed 300 characters. ATS parsers often truncate long lines. Keep each line under 200 characters.'})

    if avg_len > 150:
        score -= 10
        feedback.append({'type': 'warning', 'category': 'formatting', 'message': f'Average line length is high ({int(avg_len)} chars). Use concise bullet points (1-2 lines each) for better scannability.'})

    bullet_count = len(re.findall(r'^[\s]*[•\-*\d+.]', text, re.MULTILINE))
    details['bullet_count'] = bullet_count
    if bullet_count >= 10:
        feedback.append({'type': 'success', 'category': 'formatting', 'message': f'Excellent use of {bullet_count} bullet points for readability and ATS parsing.'})
    elif bullet_count >= 5:
        feedback.append({'type': 'success', 'category': 'formatting', 'message': f'Good use of {bullet_count} bullet points. Aim for at least 10 across your experience section.'})
    else:
        score -= 15
        feedback.append({'type': 'warning', 'category': 'formatting', 'message': f'Only {bullet_count} bullet points found. Use bullet points for all experience entries.'})

    return max(score, 0), feedback, details

def _score_contact(text):
    score = 60
    feedback = []
    email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    phone = re.findall(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    linkedin = re.findall(r'linkedin\.com/\S+', text, re.I)
    details = {'email': bool(email), 'phone': bool(phone), 'linkedin': bool(linkedin)}
    has_issues = False
    if not email:
        score -= 20
        feedback.append({'type': 'error', 'category': 'contact_info', 'message': 'No email address found. Every resume must include a professional email.'})
        has_issues = True
    else:
        feedback.append({'type': 'success', 'category': 'contact_info', 'message': f'Email found: {email[0]}'})
    if not phone:
        score -= 15
        feedback.append({'type': 'warning', 'category': 'contact_info', 'message': 'No phone number found. Most recruiters expect a contact number.'})
        has_issues = True
    else:
        feedback.append({'type': 'success', 'category': 'contact_info', 'message': 'Phone number found.'})
    if not linkedin:
        score -= 10
        feedback.append({'type': 'info', 'category': 'contact_info', 'message': 'No LinkedIn profile detected. Adding a LinkedIn URL is strongly recommended.'})
    else:
        feedback.append({'type': 'success', 'category': 'contact_info', 'message': 'LinkedIn profile found.'})
    if not has_issues:
        score = 100
    return max(score, 0), feedback, details

def _score_sections(text):
    score = 100
    feedback = []
    text_lower = text.lower()
    section_map = {
        'experience': ['experience', 'work history', 'employment', 'professional experience'],
        'education': ['education', 'university', 'college', 'degree', 'bachelor', 'master', 'phd'],
        'skills': ['skills', 'technologies', 'technical skills', 'core competencies', 'expertise'],
        'projects': ['projects', 'portfolio', 'key projects'],
        'certifications': ['certification', 'license', 'credential'],
        'summary': ['summary', 'professional summary', 'profile', 'objective', 'about me'],
    }
    found = []
    missing = []
    for section, keywords in section_map.items():
        if any(kw in text_lower for kw in keywords):
            found.append(section)
        else:
            missing.append(section)
    details = {'found': found, 'missing': missing}
    required = ['experience', 'education', 'skills']
    for req in required:
        if req not in found:
            score -= 15
    for opt in ['summary', 'certifications', 'projects']:
        if opt not in found:
            score -= 5
    if not missing:
        feedback.append({'type': 'success', 'category': 'sections', 'message': 'All key sections detected: Experience, Education, Skills, and more.'})
    else:
        feedback.append({'type': 'warning', 'category': 'sections', 'message': f'Missing sections: {", ".join(missing)}. Adding these improves ATS parsing and recruiter experience.'})
    if 'experience' not in found:
        feedback.append({'type': 'error', 'category': 'sections', 'message': 'No Experience section detected. This is critical and must be present.'})
    if 'summary' in found:
        feedback.append({'type': 'success', 'category': 'sections', 'message': 'Professional Summary found — this provides great context for ATS.'})
    return max(score, 0), feedback, details

def _score_quantified(text):
    score = 40
    feedback = []
    patterns = [
        (r'\d+%', 'percentage'),
        (r'\$\s*\d+[kKmMbB]?', 'dollar_amount'),
        (r'\d+x', 'multiplier'),
        (r'\d+[kKmMbB]\b(?!%)', 'large_number'),
        (r'\d+[-\s]?(year|month|week|day)s?', 'time_period'),
        (r'(increased|decreased|reduced|improved|grew|saved|generated|boosted|accelerated)', 'impact_verb'),
        (r'\d+[+]\s?(years?|months?|%)', 'years_experience'),
    ]
    matches = []
    seen = set()
    for p, label in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            val = m.group().strip()
            if val not in seen:
                matches.append({'value': val, 'type': label})
                seen.add(val)
    count = len(matches)
    types_used = set(m['type'] for m in matches)
    diversity_score = len(types_used)

    if count >= 8 and diversity_score >= 3:
        score = 100
        feedback.append({'type': 'success', 'category': 'quantified', 'message': f'Excellent: {count} quantified metrics across {diversity_score} categories. This significantly boosts ATS appeal and recruiter interest.'})
    elif count >= 5:
        score = 85
        feedback.append({'type': 'success', 'category': 'quantified', 'message': f'Good: {count} quantified metrics found. Aim for 8+ across different categories (%, $, time).'})
    elif count >= 3:
        score = 65
        feedback.append({'type': 'warning', 'category': 'quantified', 'message': f'Fair: {count} quantified metrics. Add more numbers — percentages, dollar amounts, and time saved are most impactful.'})
    elif count >= 1:
        score = 45
        feedback.append({'type': 'warning', 'category': 'quantified', 'message': f'Only {count} quantifiable metric(s) found. Every bullet should ideally include a measurable outcome.'})
    else:
        feedback.append({'type': 'error', 'category': 'quantified', 'message': 'No quantified achievements found. Add metrics like "increased X by Y%" or "reduced costs by $Z" to every bullet point.'})

    return score, feedback, {'quantified_count': count, 'diversity_score': diversity_score, 'examples': [m['value'] for m in matches[:15]]}

def _score_action_verbs(text):
    score = 40
    feedback = []
    text_lower = text.lower()
    found = []
    for v in ACTION_VERBS:
        if v in text_lower:
            found.append(v)
    count = len(found)
    unique_starters = []
    for line in text.split('\n'):
        stripped = line.strip().lower()
        if stripped and re.match(r'^[•\-*\d+.]', stripped):
            words = stripped.split()
            if len(words) > 1:
                first = words[1].rstrip('.,;:!?')
            else:
                first = words[0].rstrip('.,;:!?')
            if first not in ('the', 'a', 'an'):
                unique_starters.append(first)
    starter_verbs = [s for s in unique_starters if s in ACTION_VERBS]

    if count >= 10:
        score = 100
        feedback.append({'type': 'success', 'category': 'action_verbs', 'message': f'Excellent: {count} different action verbs used. Resume shows strong leadership and initiative.'})
    elif count >= 7:
        score = 80
        feedback.append({'type': 'success', 'category': 'action_verbs', 'message': f'Good: {count} action verbs found. Aim for 10+ unique verbs across your experience section.'})
    elif count >= 4:
        score = 60
        feedback.append({'type': 'warning', 'category': 'action_verbs', 'message': f'Fair: only {count} action verbs. Start every bullet with a strong verb like "Delivered", "Optimized", "Architected".'})
    else:
        feedback.append({'type': 'error', 'category': 'action_verbs', 'message': f'Only {count} action verbs found. Rewrite bullets to begin with powerful, varied action verbs.'})
    return score, feedback, {'action_verb_count': count, 'found_verbs': found, 'bullet_starters': list(set(starter_verbs))[:10]}

def _score_education(text):
    score = 50
    feedback = []
    text_lower = text.lower()
    has_degree = bool(re.search(r'(bachelor|master|phd|b\.\s*s|m\.\s*s|mba|associate)', text_lower))
    has_university = bool(re.search(r'(university|college|institute|school of)', text_lower))
    has_year = bool(re.search(r'(19|20)\d{2}', text))
    has_gpa = bool(re.search(r'\b[34]\.[0-9]\b', text))
    has_major = bool(re.search(r'(computer science|engineering|mathematics|physics|business|economics|biology|chemistry|psychology)', text_lower))
    details = {
        'has_degree': has_degree,
        'has_university': has_university,
        'has_year': has_year,
        'has_gpa': has_gpa,
        'has_major': has_major,
    }
    if has_degree:
        score += 20
        feedback.append({'type': 'success', 'category': 'education', 'message': 'Degree found.'})
    else:
        feedback.append({'type': 'warning', 'category': 'education', 'message': 'No degree title detected. Include (e.g., B.S. Computer Science).'})
    if has_university:
        score += 15
        feedback.append({'type': 'success', 'category': 'education', 'message': 'Institution name found.'})
    else:
        feedback.append({'type': 'warning', 'category': 'education', 'message': 'No institution/university name detected.'})
    if has_year:
        score += 10
    else:
        feedback.append({'type': 'info', 'category': 'education', 'message': 'Graduation year not detected. Add it for completeness.'})
    if has_gpa:
        score += 5
        feedback.append({'type': 'success', 'category': 'education', 'message': f'GPA found.'})
    if has_major:
        score += 10
        feedback.append({'type': 'success', 'category': 'education', 'message': 'Field of study/major detected.'})
    score = min(score, 100)
    return score, feedback, details

def _score_experience(text):
    score = 50
    feedback = []
    text_lower = text.lower()
    date_pattern = r'(19|20)\d{2}\s*[-–to]+\s*(19|20)\d{2}|(19|20)\d{2}\s*[-–to]+\s*(present|current|now)'
    date_matches = re.findall(date_pattern, text, re.I)
    has_dates = len(date_matches) >= 2
    has_company = bool(re.search(r'at\s+([A-Z][a-zA-Z]+)', text))
    has_title = bool(re.search(r'(engineer|developer|manager|analyst|scientist|architect|lead|head|director|officer|consultant|intern)', text_lower))
    has_bullets = bool(re.search(r'^[\s]*[•\-*\d+.]', text, re.MULTILINE))
    experience_length = len(re.findall(r'(experience|work\s*history|employment)', text_lower))
    details = {
        'has_dates': bool(date_matches),
        'has_company': has_company,
        'has_title': has_title,
        'has_bullets': has_bullets,
        'num_date_ranges': len(date_matches),
    }
    if has_dates:
        score += 20
        feedback.append({'type': 'success', 'category': 'experience', 'message': 'Employment dates found — essential for ATS verification.'})
    else:
        feedback.append({'type': 'warning', 'category': 'experience', 'message': 'Employment dates missing. Always include start/end dates for each position.'})
    if has_company:
        score += 15
        feedback.append({'type': 'success', 'category': 'experience', 'message': 'Company names detected.'})
    else:
        feedback.append({'type': 'warning', 'category': 'experience', 'message': 'Company names not clearly detected. Ensure each role has company, title, location.'})
    if has_title:
        score += 15
        feedback.append({'type': 'success', 'category': 'experience', 'message': 'Job titles detected.'})
    else:
        feedback.append({'type': 'warning', 'category': 'experience', 'message': 'Job titles not clearly detected.'})
    if has_bullets:
        score += 10
        feedback.append({'type': 'success', 'category': 'experience', 'message': 'Bullet points found under experience — good for ATS parsing.'})
    else:
        feedback.append({'type': 'error', 'category': 'experience', 'message': 'No bullet points found. Use bullets to describe each role.'})
    if experience_length > 0:
        score += 10
    score = min(score, 100)
    return score, feedback, details

def _score_length(text):
    words = text.split()
    count = len(words)
    if 400 <= count <= 700:
        score = 100
        feedback = [{'type': 'success', 'category': 'length', 'message': f'Optimal resume length: {count} words. ATS and recruiters prefer 400-700 words.'}]
    elif 250 <= count < 400:
        score = 80
        feedback = [{'type': 'success', 'category': 'length', 'message': f'Resume is {count} words. Consider expanding to 400-600 words for more depth.'}]
    elif count >= 700 and count <= 1000:
        score = 75
        feedback = [{'type': 'warning', 'category': 'length', 'message': f'Resume is {count} words. Consider condensing to ~600 words. Most ATS systems handle this fine but recruiters prefer concise resumes.'}]
    elif count > 1000:
        score = 50
        feedback = [{'type': 'warning', 'category': 'length', 'message': f'Resume is very long ({count} words). Longer resumes may be truncated by some ATS systems. Keep it to 1-2 pages.'}]
    else:
        score = 50
        feedback = [{'type': 'warning', 'category': 'length', 'message': f'Resume is short ({count} words). Add more relevant experience and achievements.'}]
    return score, feedback, {'word_count': count}

def _score_skills_taxonomy(resume_text, jd_text):
    score = 50
    feedback = []
    resume_lower = resume_text.lower()
    jd_lower = jd_text.lower()
    category_scores = {}
    for category, skills in SKILL_TAXONOMY.items():
        resume_skills = [s for s in skills if s in resume_lower]
        jd_required = [s for s in skills if s in jd_lower]
        coverage = len(resume_skills) / max(len(jd_required), 1) * 100 if jd_required else 100
        category_scores[category] = {
            'resume_skills': resume_skills[:5],
            'jd_required': jd_required[:5],
            'coverage': round(coverage, 1),
        }
    total_required = sum(len(v['jd_required']) for v in category_scores.values())
    total_matched = sum(len(v['resume_skills']) for v in category_scores.values())
    overall_coverage = total_matched / max(total_required, 1) * 100 if total_required else 100
    if overall_coverage >= 70:
        score = 90
        feedback.append({'type': 'success', 'category': 'skills_depth', 'message': f'Strong skills coverage ({int(overall_coverage)}%) across technical categories.'})
    elif overall_coverage >= 40:
        score = 65
        feedback.append({'type': 'warning', 'category': 'skills_depth', 'message': f'Moderate skills coverage ({int(overall_coverage)}%). Consider adding more technical skills from the JD.'})
    else:
        score = 35
        feedback.append({'type': 'error', 'category': 'skills_depth', 'message': f'Low skills coverage ({int(overall_coverage)}%). Significantly expand your technical skills section to match the job requirements.'})
    return score, feedback, {'category_scores': category_scores, 'overall_coverage': round(overall_coverage, 1)}

def _categorize_feedback(feedback):
    categories = {}
    for fb in feedback:
        cat = fb['category']
        if cat not in categories:
            categories[cat] = {'success': [], 'warning': [], 'error': [], 'info': []}
        categories[cat][fb['type']].append(fb['message'])
    return categories

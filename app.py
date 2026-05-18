import os
import uuid
import json
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

from resume_parser import (
    parse_resume, extract_bullet_points, extract_sections,
    extract_contact_info, detect_formatting_issues, get_resume_stats,
    extract_experience_entries,
)
from ats_scorer import score_ats
from keyword_extractor import (
    extract_keywords_job_description, extract_keywords_resume,
    match_keywords, get_skills_gap, categorize_keywords,
)
from bullet_improver import improve_bullet_point, improve_bullet_points_batch

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume file uploaded'}), 400
    file = request.files['resume']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Upload PDF or DOCX.'}), 400

    jd_text = request.form.get('job_description', '').strip()
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(filepath)

    try:
        resume_text = parse_resume(filepath)
        if not resume_text or len(resume_text.strip()) < 50:
            return jsonify({'error': 'Could not extract enough text. The file may be scanned/image-based.'}), 400

        sections = extract_sections(resume_text)
        contact = extract_contact_info(resume_text)
        stats = get_resume_stats(resume_text)
        bullets = extract_bullet_points(resume_text)
        formatting_issues = detect_formatting_issues(resume_text)
        experience_entries = extract_experience_entries(resume_text)

        result = {
            'resume_text': resume_text,
            'sections': {k: '\n'.join(v) for k, v in sections.items()},
            'contact': contact,
            'stats': stats,
            'bullet_count': len(bullets),
            'formatting_issues': formatting_issues,
            'experience_entries': experience_entries,
        }

        if jd_text:
            jd_keywords = extract_keywords_job_description(jd_text)
            resume_keywords = extract_keywords_resume(resume_text)
            kw_match = match_keywords(resume_keywords, jd_keywords)
            ats = score_ats(resume_text, jd_text)

            skills_gap = get_skills_gap(kw_match['matched_categorized'], kw_match['missing_categorized'])
            resume_categorized = categorize_keywords(resume_keywords)
            jd_categorized = categorize_keywords(jd_keywords)

            result['ats_score'] = ats
            result['keyword_match'] = kw_match
            result['jd_keywords'] = jd_keywords
            result['resume_keywords'] = resume_keywords
            result['skills_gap'] = skills_gap
            result['resume_keywords_categorized'] = resume_categorized
            result['jd_keywords_categorized'] = jd_categorized

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        try:
            os.remove(filepath)
        except Exception:
            pass

@app.route('/api/improve-bullets', methods=['POST'])
def improve_bullets():
    data = request.get_json()
    if not data or 'bullets' not in data:
        return jsonify({'error': 'No bullet points provided'}), 400
    results = improve_bullets_batch(data['bullets'], data.get('job_title', ''), data.get('use_ai', False))
    return jsonify({'results': results}), 200

@app.route('/api/improve-single-bullet', methods=['POST'])
def improve_single_bullet():
    data = request.get_json()
    if not data or 'bullet' not in data:
        return jsonify({'error': 'No bullet point provided'}), 400
    result = improve_bullet_point(data['bullet'], data.get('job_title', ''), data.get('use_ai', False))
    return jsonify({'result': result}), 200

@app.route('/api/improve-all-bullets', methods=['POST'])
def improve_all_bullets():
    data = request.get_json()
    if not data or 'bullets' not in data:
        return jsonify({'error': 'No bullet points provided'}), 400
    results = improve_bullet_points_batch(data['bullets'], data.get('job_title', ''), data.get('use_ai', False))
    return jsonify({'results': results}), 200

@app.route('/api/keywords', methods=['POST'])
def extract_keywords_api():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    keywords = extract_keywords_job_description(data['text'])
    categorized = categorize_keywords(keywords)
    return jsonify({'keywords': keywords, 'categorized': categorized}), 200

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'version': '2.0'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Resume Analyzer v2 running on http://localhost:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)

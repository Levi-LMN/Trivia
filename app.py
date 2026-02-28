from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, random, string, hashlib, os, json
from datetime import datetime, timezone, timedelta
from functools import wraps

# Kenya is UTC+3 (East Africa Time) — no DST observed
EAT = timezone(timedelta(hours=3))

def now_eat():
    """Return the current moment as a naive datetime in East Africa Time (UTC+3)."""
    return datetime.now(EAT).replace(tzinfo=None)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(32)
ADMIN_PASSWORD_INIT = os.environ.get('ADMIN_PASSWORD', 'changeme')
DATABASE = 'bible_trivia.db'

@app.context_processor
def inject_globals():
    return dict(json=json)

@app.template_filter('eat_fmt')
def eat_fmt(value, fmt='%d %b %Y, %I:%M %p'):
    """Format a stored EAT datetime string for display. e.g. '14 Jun 2025, 03:45 PM EAT'"""
    if not value:
        return '—'
    try:
        if isinstance(value, str):
            value = datetime.strptime(value[:19], '%Y-%m-%d %H:%M:%S')
        return value.strftime(fmt) + ' EAT'
    except Exception:
        return str(value)

# ─── DB helpers ───────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            name  TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT (datetime('now', '+3 hours'))
        );
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT NOT NULL,
            description         TEXT DEFAULT '',
            is_active           INTEGER DEFAULT 1,
            randomize_questions INTEGER DEFAULT 1,
            time_limit_minutes  INTEGER DEFAULT 0,
            created_at          TIMESTAMP DEFAULT (datetime('now', '+3 hours'))
        );
        CREATE TABLE IF NOT EXISTS sections (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
            name       TEXT NOT NULL,
            order_num  INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS questions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id    INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
            question_type TEXT DEFAULT 'single',
            question_text TEXT NOT NULL,
            option_a      TEXT DEFAULT '',
            option_b      TEXT DEFAULT '',
            option_c      TEXT DEFAULT '',
            option_d      TEXT DEFAULT '',
            correct_answer TEXT NOT NULL,
            blank_options TEXT DEFAULT '[]',
            points        INTEGER DEFAULT 1,
            order_num     INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS user_sessions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL REFERENCES users(id),
            session_id   INTEGER NOT NULL REFERENCES quiz_sessions(id),
            started_at   TIMESTAMP DEFAULT (datetime('now', '+3 hours')),
            completed_at TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_answers (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_session_id  INTEGER NOT NULL REFERENCES user_sessions(id),
            question_id      INTEGER NOT NULL REFERENCES questions(id),
            selected_answer  TEXT NOT NULL,
            is_correct       INTEGER NOT NULL,
            reward_code      TEXT,
            answered_at      TIMESTAMP DEFAULT (datetime('now', '+3 hours'))
        );
        CREATE TABLE IF NOT EXISTS app_settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS cheat_flags (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_session_id INTEGER NOT NULL REFERENCES user_sessions(id) ON DELETE CASCADE,
            violation_type  TEXT NOT NULL,
            flagged_at      TIMESTAMP DEFAULT (datetime('now', '+3 hours'))
        );
        INSERT OR IGNORE INTO app_settings VALUES ('admin_password', '{{ ADMIN_PASSWORD_INIT }}');
    '''.replace("{{ ADMIN_PASSWORD_INIT }}", ADMIN_PASSWORD_INIT))
    conn.commit()
    # Migrate existing DBs that lack new columns
    for col, defval in [('question_type', "'single'"), ('blank_options', "'[]'")]:
        try:
            conn.execute(f'ALTER TABLE questions ADD COLUMN {col} TEXT DEFAULT {defval}')
            conn.commit()
        except Exception:
            pass
    try:
        conn.execute("ALTER TABLE quiz_sessions ADD COLUMN time_limit_minutes INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    conn.close()

def normalize_multi(answer_str):
    """Sort comma-separated letters for comparison: 'C,A' -> 'A,C'"""
    return ','.join(sorted(x.strip().upper() for x in answer_str.split(',') if x.strip()))

def check_answer(question, selected_raw):
    """Returns (is_correct, stored_selected) for any question type."""
    qtype = question['question_type'] or 'single'
    correct = (question['correct_answer'] or '').strip()

    if qtype == 'single':
        sel = selected_raw.strip().upper()
        return int(sel == correct.upper()), sel

    elif qtype == 'multi':
        sel = normalize_multi(selected_raw)
        return int(sel == normalize_multi(correct)), sel

    elif qtype == 'fill_blank':
        # selected_raw is pipe-separated user choices: "Bethlehem|Mary"
        sel_parts  = [p.strip() for p in selected_raw.split('|')]
        corr_parts = [p.strip() for p in correct.split('|')]
        is_correct = int(sel_parts == corr_parts)
        return is_correct, selected_raw

    return 0, selected_raw

def get_remaining_seconds(user_session_row, time_limit_minutes):
    """Return seconds left (None = no limit, 0 = expired). Uses EAT throughout."""
    if not time_limit_minutes:
        return None
    started = user_session_row['started_at']
    if isinstance(started, str):
        started = datetime.strptime(started, '%Y-%m-%d %H:%M:%S')
    elapsed = (now_eat() - started).total_seconds()
    remaining = int(time_limit_minutes * 60 - elapsed)
    return max(remaining, 0)

def generate_code(user_id, question_id):
    raw = f"{user_id}-{question_id}-{random.randint(10000,99999)}"
    return hashlib.md5(raw.encode()).hexdigest()[:8].upper()

# ─── Auth decorators ──────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def normalize_phone(raw):
    """Normalize any Kenyan phone format to 07XXXXXXXX or 01XXXXXXXX (10 digits)."""
    phone = raw.strip().replace(' ', '').replace('-', '')
    # +2547... or 2547... → 07...
    if phone.startswith('+254'):
        phone = '0' + phone[4:]
    elif phone.startswith('254') and len(phone) >= 12:
        phone = '0' + phone[3:]
    return phone

# ═══════════════════════════════════════════════════════════════════════════════
#  USER ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' in session:
        return redirect(url_for('quiz_home'))
    if request.method == 'POST':
        phone = normalize_phone(request.form.get('phone', ''))
        if not phone:
            flash('Please enter your phone number.', 'error')
            return render_template('index.html')
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE phone=?', (phone,)).fetchone()
        conn.close()
        if user:
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('quiz_home'))
        session['pending_phone'] = phone
        return redirect(url_for('register'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'pending_phone' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Please enter your name.', 'error')
            return render_template('register.html', phone=session['pending_phone'])
        phone = session.pop('pending_phone')
        conn = get_db()
        conn.execute('INSERT OR IGNORE INTO users (phone, name) VALUES (?,?)', (phone, name))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE phone=?', (phone,)).fetchone()
        conn.close()
        session['user_id']   = user['id']
        session['user_name'] = user['name']
        return redirect(url_for('quiz_home'))
    return render_template('register.html', phone=session['pending_phone'])

@app.route('/quiz')
@login_required
def quiz_home():
    conn = get_db()
    real_user = conn.execute('SELECT id FROM users WHERE id=?', (session['user_id'],)).fetchone()
    if not real_user:
        conn.close()
        session.clear()
        flash('Your session has expired. Please log in again.', 'error')
        return redirect(url_for('index'))
    sessions_list = conn.execute(
        'SELECT * FROM quiz_sessions WHERE is_active=1 ORDER BY created_at DESC'
    ).fetchall()
    completed_ids = {
        r['session_id'] for r in
        conn.execute('SELECT session_id FROM user_sessions WHERE user_id=? AND completed_at IS NOT NULL',
                     (session['user_id'],)).fetchall()
    }
    # in-progress: include started_at so we can show live countdown in the modal
    inprogress_rows = conn.execute(
        'SELECT session_id, started_at FROM user_sessions WHERE user_id=? AND completed_at IS NULL',
        (session['user_id'],)
    ).fetchall()
    inprogress_ids = {r['session_id'] for r in inprogress_rows}
    # Map session_id -> remaining seconds (None if no limit)
    inprogress_remaining = {}
    for row in inprogress_rows:
        sid = row['session_id']
        qs_row = next((s for s in sessions_list if s['id'] == sid), None)
        if qs_row:
            rem = get_remaining_seconds(row, qs_row['time_limit_minutes'] or 0)
            inprogress_remaining[sid] = rem  # None = no limit, int = seconds left
    conn.close()
    return render_template('quiz_home.html', sessions=sessions_list,
                           completed_ids=completed_ids, inprogress_ids=inprogress_ids,
                           inprogress_remaining=inprogress_remaining)
@app.route('/quiz/<int:session_id>', methods=['GET', 'POST'])
@login_required
def take_quiz(session_id):
    conn = get_db()

    # ── Guard: verify session cookie user still exists in DB ──────────────
    # Happens when DB is wiped but browser still holds the old session cookie
    real_user = conn.execute('SELECT id FROM users WHERE id=?', (session['user_id'],)).fetchone()
    if not real_user:
        conn.close()
        session.clear()
        flash('Your session has expired. Please log in again.', 'error')
        return redirect(url_for('index'))

    qs = conn.execute('SELECT * FROM quiz_sessions WHERE id=? AND is_active=1', (session_id,)).fetchone()
    if not qs:
        flash('Session not found or is inactive.', 'error')
        conn.close()
        return redirect(url_for('quiz_home'))

    # Get or create user_session
    us = conn.execute(
        'SELECT * FROM user_sessions WHERE user_id=? AND session_id=? AND completed_at IS NULL',
        (session['user_id'], session_id)
    ).fetchone()
    if not us:
        conn.execute('INSERT INTO user_sessions (user_id, session_id) VALUES (?,?)',
                     (session['user_id'], session_id))
        conn.commit()
        us = conn.execute(
            'SELECT * FROM user_sessions WHERE user_id=? AND session_id=? AND completed_at IS NULL',
            (session['user_id'], session_id)
        ).fetchone()

    us_id = us['id']

    # ── Timer check ────────────────────────────────────────────────────────
    time_limit = qs['time_limit_minutes'] or 0
    remaining_seconds = get_remaining_seconds(us, time_limit)
    if remaining_seconds is not None and remaining_seconds <= 0:
        # Time is up — auto-complete the session
        conn.execute('UPDATE user_sessions SET completed_at=datetime("now", "+3 hours") WHERE id=?', (us_id,))
        conn.commit()
        conn.close()
        flash('⏰ Time is up! Your session has been submitted.', 'error')
        return redirect(url_for('results', session_id=session_id))
    sections = conn.execute(
        'SELECT * FROM sections WHERE session_id=? ORDER BY order_num', (session_id,)
    ).fetchall()
    all_questions = []
    for sec in sections:
        qs_list = conn.execute(
            'SELECT q.*, ? as section_name FROM questions q WHERE q.section_id=? ORDER BY q.order_num',
            (sec['name'], sec['id'])
        ).fetchall()
        all_questions.extend(qs_list)

    # Randomize per user_session (stable seed so page reloads keep same order)
    if qs['randomize_questions']:
        r = random.Random(us_id)
        r.shuffle(all_questions)

    answered = conn.execute(
        'SELECT * FROM user_answers WHERE user_session_id=?', (us_id,)
    ).fetchall()
    answered_map = {a['question_id']: a for a in answered}
    answered_ids = set(answered_map.keys())

    if request.method == 'POST':
        q_id = int(request.form.get('question_id'))
        if q_id not in answered_ids:
            question = conn.execute('SELECT * FROM questions WHERE id=?', (q_id,)).fetchone()
            qtype = question['question_type'] or 'single'

            if qtype == 'single':
                selected_raw = request.form.get('answer', '').strip().upper()
            elif qtype == 'multi':
                checked = request.form.getlist('answer')
                selected_raw = ','.join(sorted(x.upper() for x in checked)) if checked else ''
            elif qtype == 'fill_blank':
                bo = json.loads(question['blank_options'] or '[]')
                parts = [request.form.get(f'blank_{i}', '').strip() for i in range(len(bo))]
                selected_raw = '|'.join(parts)
            else:
                selected_raw = ''

            if selected_raw:
                is_correct, stored_sel = check_answer(question, selected_raw)
                code = generate_code(session['user_id'], q_id) if is_correct else None
                conn.execute(
                    'INSERT INTO user_answers (user_session_id, question_id, selected_answer, is_correct, reward_code) VALUES (?,?,?,?,?)',
                    (us_id, q_id, stored_sel, is_correct, code)
                )
                conn.commit()
                answered_ids.add(q_id)

        if len(answered_ids) >= len(all_questions):
            conn.execute('UPDATE user_sessions SET completed_at=datetime("now", "+3 hours") WHERE id=?', (us_id,))
            conn.commit()
            conn.close()
            return redirect(url_for('results', session_id=session_id))
        conn.close()
        return redirect(url_for('take_quiz', session_id=session_id))

    # Find next unanswered
    next_q = next((q for q in all_questions if q['id'] not in answered_ids), None)
    if not next_q:
        conn.execute('UPDATE user_sessions SET completed_at=datetime("now", "+3 hours") WHERE id=?', (us_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('results', session_id=session_id))

    conn.close()
    return render_template('quiz.html', question=next_q, quiz_session=qs,
                           progress=len(answered_ids), total=len(all_questions),
                           all_questions=all_questions, answered_map=answered_map,
                           answered_ids=answered_ids,
                           remaining_seconds=remaining_seconds,
                           time_limit=time_limit)

@app.route('/quiz/<int:session_id>/expire', methods=['POST'])
@login_required
def expire_quiz(session_id):
    conn = get_db()
    conn.execute('''UPDATE user_sessions SET completed_at=datetime("now", "+3 hours")
                    WHERE user_id=? AND session_id=? AND completed_at IS NULL''',
                 (session['user_id'], session_id))
    conn.commit()
    conn.close()
    flash('⏰ Time is up! Your answers have been submitted.', 'error')
    return redirect(url_for('results', session_id=session_id))

@app.route('/api/cheat-flag/<int:session_id>', methods=['POST'])
@login_required
def cheat_flag(session_id):
    """Record a cheating violation for the current user's active session."""
    violation = request.json.get('violation', 'unknown') if request.is_json else 'unknown'
    # sanitize
    allowed = {'tab_switch', 'window_blur', 'copy_attempt', 'right_click',
               'keyboard_shortcut', 'devtools', 'context_menu', 'auto_submit'}
    violation = violation if violation in allowed else 'unknown'
    conn = get_db()
    us = conn.execute(
        'SELECT id FROM user_sessions WHERE user_id=? AND session_id=? AND completed_at IS NULL',
        (session['user_id'], session_id)
    ).fetchone()
    if us:
        conn.execute(
            'INSERT INTO cheat_flags (user_session_id, violation_type) VALUES (?,?)',
            (us['id'], violation)
        )
        # Count total flags for this session
        count = conn.execute(
            'SELECT COUNT(*) as n FROM cheat_flags WHERE user_session_id=?', (us['id'],)
        ).fetchone()['n']
        conn.commit()
        conn.close()
        return {'ok': True, 'total_flags': count}
    conn.close()
    return {'ok': False}, 404

@app.route('/results', defaults={'session_id': None})
@app.route('/results/<int:session_id>')
@login_required
def results(session_id):
    conn = get_db()
    real_user = conn.execute('SELECT id FROM users WHERE id=?', (session['user_id'],)).fetchone()
    if not real_user:
        conn.close()
        session.clear()
        flash('Your session has expired. Please log in again.', 'error')
        return redirect(url_for('index'))
    if session_id:
        us = conn.execute('''
            SELECT us.*, qs.name as session_name
            FROM user_sessions us JOIN quiz_sessions qs ON us.session_id=qs.id
            WHERE us.user_id=? AND us.session_id=?
            ORDER BY us.started_at DESC LIMIT 1
        ''', (session['user_id'], session_id)).fetchone()
        if not us:
            conn.close()
            return redirect(url_for('quiz_home'))
        answers = conn.execute('''
            SELECT ua.*, q.question_text, q.correct_answer, q.option_a, q.option_b, q.option_c, q.option_d,
                   q.points, q.question_type, s.name as section_name
            FROM user_answers ua
            JOIN questions q ON ua.question_id=q.id
            JOIN sections s ON q.section_id=s.id
            WHERE ua.user_session_id=?
            ORDER BY ua.answered_at
        ''', (us['id'],)).fetchall()
        correct = sum(1 for a in answers if a['is_correct'])
        pts     = sum(a['points'] for a in answers if a['is_correct'])
        conn.close()
        return render_template('results.html', single=True, user_sess=us,
                               answers=answers, correct_count=correct, total_points=pts)
    else:
        all_sessions = conn.execute('''
            SELECT us.id, us.started_at, us.completed_at, qs.name as session_name,
                   COUNT(ua.id) as total_answered,
                   SUM(CASE WHEN ua.is_correct THEN 1 ELSE 0 END) as correct_count,
                   SUM(CASE WHEN ua.is_correct THEN q.points ELSE 0 END) as total_points,
                   us.session_id
            FROM user_sessions us
            JOIN quiz_sessions qs ON us.session_id=qs.id
            LEFT JOIN user_answers ua ON us.id=ua.user_session_id
            LEFT JOIN questions q ON ua.question_id=q.id
            WHERE us.user_id=?
            GROUP BY us.id ORDER BY us.started_at DESC
        ''', (session['user_id'],)).fetchall()
        conn.close()
        return render_template('results.html', single=False, all_sessions=all_sessions)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ── Timer API ──────────────────────────────────────────────────────────────────
@app.route('/api/timer/<int:session_id>')
@login_required
def api_timer(session_id):
    """Returns the authoritative remaining seconds from the backend."""
    from flask import jsonify
    conn = get_db()
    qs = conn.execute('SELECT time_limit_minutes FROM quiz_sessions WHERE id=?', (session_id,)).fetchone()
    us = conn.execute(
        'SELECT * FROM user_sessions WHERE user_id=? AND session_id=? AND completed_at IS NULL',
        (session['user_id'], session_id)
    ).fetchone()
    conn.close()
    if not qs or not us:
        return jsonify({'remaining': 0, 'expired': True})
    time_limit = qs['time_limit_minutes'] or 0
    if not time_limit:
        return jsonify({'remaining': None, 'expired': False})
    remaining = get_remaining_seconds(us, time_limit)
    return jsonify({'remaining': remaining, 'expired': remaining <= 0})

# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        pw = request.form.get('password', '')
        conn = get_db()
        stored = conn.execute("SELECT value FROM app_settings WHERE key='admin_password'").fetchone()
        conn.close()
        if stored and pw == stored['value']:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Wrong password.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db()
    stats = dict(
        users     = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        sessions  = conn.execute('SELECT COUNT(*) FROM quiz_sessions').fetchone()[0],
        questions = conn.execute('SELECT COUNT(*) FROM questions').fetchone()[0],
        correct   = conn.execute('SELECT COUNT(*) FROM user_answers WHERE is_correct=1').fetchone()[0],
    )
    leaderboard = conn.execute('''
        SELECT u.name, u.phone,
               COUNT(DISTINCT us.session_id) as sessions_taken,
               SUM(CASE WHEN ua.is_correct THEN q.points ELSE 0 END) as total_points,
               SUM(CASE WHEN ua.is_correct THEN 1 ELSE 0 END) as correct_count
        FROM users u
        LEFT JOIN user_sessions us ON u.id=us.user_id
        LEFT JOIN user_answers ua ON us.id=ua.user_session_id
        LEFT JOIN questions q ON ua.question_id=q.id
        GROUP BY u.id ORDER BY total_points DESC LIMIT 15
    ''').fetchall()
    conn.close()
    return render_template('admin/dashboard.html', stats=stats, leaderboard=leaderboard)

# Sessions CRUD
@app.route('/admin/sessions', methods=['GET', 'POST'])
@admin_required
def admin_sessions():
    conn = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            conn.execute('INSERT INTO quiz_sessions (name, description, randomize_questions, time_limit_minutes) VALUES (?,?,?,?)',
                         (request.form['name'], request.form.get('description',''),
                          1 if request.form.get('randomize') else 0,
                          int(request.form.get('time_limit_minutes') or 0)))
            conn.commit(); flash('Session created!', 'success')
        elif action == 'toggle_active':
            conn.execute('UPDATE quiz_sessions SET is_active=NOT is_active WHERE id=?', (request.form['sid'],))
            conn.commit()
        elif action == 'toggle_randomize':
            conn.execute('UPDATE quiz_sessions SET randomize_questions=NOT randomize_questions WHERE id=?', (request.form['sid'],))
            conn.commit()
        elif action == 'delete':
            conn.execute('DELETE FROM quiz_sessions WHERE id=?', (request.form['sid'],))
            conn.commit(); flash('Session deleted.', 'success')
        elif action == 'edit':
            conn.execute('UPDATE quiz_sessions SET name=?, description=?, time_limit_minutes=? WHERE id=?',
                         (request.form['name'], request.form.get('description',''),
                          int(request.form.get('time_limit_minutes') or 0), request.form['sid']))
            conn.commit(); flash('Session updated!', 'success')

    sessions_list = conn.execute('''
        SELECT qs.*,
               COUNT(DISTINCT s.id)  as section_count,
               COUNT(DISTINCT q.id)  as question_count,
               COUNT(DISTINCT us.user_id) as participant_count
        FROM quiz_sessions qs
        LEFT JOIN sections s ON qs.id=s.session_id
        LEFT JOIN questions q ON s.id=q.section_id
        LEFT JOIN user_sessions us ON qs.id=us.session_id
        GROUP BY qs.id ORDER BY qs.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('admin/sessions.html', sessions=sessions_list)

# Sections CRUD
@app.route('/admin/sessions/<int:session_id>/sections', methods=['GET', 'POST'])
@admin_required
def admin_sections(session_id):
    conn = get_db()
    qs = conn.execute('SELECT * FROM quiz_sessions WHERE id=?', (session_id,)).fetchone()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            conn.execute('INSERT INTO sections (session_id, name, order_num) VALUES (?,?,?)',
                         (session_id, request.form['name'], request.form.get('order_num', 0)))
            conn.commit(); flash('Section created!', 'success')
        elif action == 'delete':
            conn.execute('DELETE FROM sections WHERE id=?', (request.form['sec_id'],))
            conn.commit()
        elif action == 'edit':
            conn.execute('UPDATE sections SET name=?, order_num=? WHERE id=?',
                         (request.form['name'], request.form.get('order_num',0), request.form['sec_id']))
            conn.commit(); flash('Section updated!', 'success')

    sections_list = conn.execute('''
        SELECT s.*, COUNT(q.id) as question_count
        FROM sections s LEFT JOIN questions q ON s.id=q.section_id
        WHERE s.session_id=? GROUP BY s.id ORDER BY s.order_num
    ''', (session_id,)).fetchall()
    conn.close()
    return render_template('admin/sections.html', quiz_session=qs, sections=sections_list)

# Questions CRUD
@app.route('/admin/sections/<int:section_id>/questions', methods=['GET', 'POST'])
@admin_required
def admin_questions(section_id):
    conn = get_db()
    sec = conn.execute('''
        SELECT s.*, qs.name as session_name, qs.id as session_id
        FROM sections s JOIN quiz_sessions qs ON s.session_id=qs.id WHERE s.id=?
    ''', (section_id,)).fetchone()
    if request.method == 'POST':
        action = request.form.get('action')
        qtype  = request.form.get('question_type', 'single')

        def extract_blank_options():
            """Pull blank_N_options fields and return JSON."""
            bo = []
            i = 0
            while True:
                key = f'blank_{i}_options'
                val = request.form.get(key, '').strip()
                if not val and i > 0:
                    break
                if val:
                    # split by newline or comma
                    opts = [o.strip() for o in val.replace('\n', ',').split(',') if o.strip()]
                    bo.append(opts)
                    i += 1
                else:
                    break
            return json.dumps(bo)

        def extract_correct():
            if qtype == 'multi':
                checked = request.form.getlist('correct_answer')
                return ','.join(sorted(x.upper() for x in checked))
            elif qtype == 'fill_blank':
                bo = json.loads(extract_blank_options() or '[]')
                parts = [request.form.get(f'blank_{i}_correct', '').strip() for i in range(len(bo))]
                return '|'.join(parts)
            else:
                return request.form.get('correct_answer', '').upper()

        if action == 'create':
            bo_json = extract_blank_options() if qtype == 'fill_blank' else '[]'
            correct = request.form.get('correct_answer_hidden') or extract_correct()
            if qtype == 'fill_blank':
                # Re-extract properly
                bo = []
                i = 0
                while True:
                    opts_raw = request.form.get(f'blank_{i}_options', '').strip()
                    if not opts_raw:
                        break
                    opts = [o.strip() for o in opts_raw.replace('\n',',').split(',') if o.strip()]
                    bo.append(opts)
                    i += 1
                bo_json = json.dumps(bo)
                parts = [request.form.get(f'blank_{i}_correct', '').strip() for i in range(len(bo))]
                correct = '|'.join(parts)
            elif qtype == 'multi':
                checked = request.form.getlist('correct_answer')
                correct = ','.join(sorted(x.upper() for x in checked))
            else:
                correct = request.form.get('correct_answer', '').upper()
                bo_json = '[]'

            conn.execute('''
                INSERT INTO questions (section_id, question_type, question_text,
                    option_a, option_b, option_c, option_d,
                    correct_answer, blank_options, points, order_num)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ''', (section_id, qtype, request.form['question_text'],
                  request.form.get('option_a',''), request.form.get('option_b',''),
                  request.form.get('option_c',''), request.form.get('option_d',''),
                  correct, bo_json,
                  request.form.get('points', 1), request.form.get('order_num', 0)))
            conn.commit(); flash('Question added!', 'success')

        elif action == 'delete':
            conn.execute('DELETE FROM questions WHERE id=?', (request.form['q_id'],))
            conn.commit()

        elif action == 'edit':
            q_id_edit = request.form['q_id']
            qtype_edit = request.form.get('question_type', 'single')
            if qtype_edit == 'fill_blank':
                bo = []
                i = 0
                while True:
                    opts_raw = request.form.get(f'blank_{i}_options', '').strip()
                    if not opts_raw:
                        break
                    opts = [o.strip() for o in opts_raw.replace('\n',',').split(',') if o.strip()]
                    bo.append(opts)
                    i += 1
                bo_json = json.dumps(bo)
                parts = [request.form.get(f'blank_{i}_correct', '').strip() for i in range(len(bo))]
                correct_edit = '|'.join(parts)
            elif qtype_edit == 'multi':
                checked = request.form.getlist('correct_answer')
                correct_edit = ','.join(sorted(x.upper() for x in checked))
                bo_json = '[]'
            else:
                correct_edit = request.form.get('correct_answer','').upper()
                bo_json = '[]'

            conn.execute('''
                UPDATE questions SET question_type=?, question_text=?,
                    option_a=?, option_b=?, option_c=?, option_d=?,
                    correct_answer=?, blank_options=?, points=?, order_num=?
                WHERE id=?
            ''', (qtype_edit, request.form['question_text'],
                  request.form.get('option_a',''), request.form.get('option_b',''),
                  request.form.get('option_c',''), request.form.get('option_d',''),
                  correct_edit, bo_json,
                  request.form.get('points',1), request.form.get('order_num',0),
                  q_id_edit))
            conn.commit(); flash('Question updated!', 'success')

    questions_list = [dict(q) for q in conn.execute(
        'SELECT * FROM questions WHERE section_id=? ORDER BY order_num', (section_id,)
    ).fetchall()]
    conn.close()
    return render_template('admin/questions.html', section=sec, questions=questions_list)

# Users & scores
@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db()
    users = conn.execute('''
        SELECT u.id, u.name, u.phone, u.created_at,
               COUNT(DISTINCT us.session_id) as sessions_taken,
               SUM(CASE WHEN ua.is_correct THEN q.points ELSE 0 END) as total_points,
               SUM(CASE WHEN ua.is_correct THEN 1 ELSE 0 END) as correct_count,
               COUNT(ua.id) as total_answered,
               (SELECT COUNT(*) FROM cheat_flags cf
                JOIN user_sessions us2 ON cf.user_session_id=us2.id
                WHERE us2.user_id=u.id) as cheat_count
        FROM users u
        LEFT JOIN user_sessions us ON u.id=us.user_id
        LEFT JOIN user_answers ua ON us.id=ua.user_session_id
        LEFT JOIN questions q ON ua.question_id=q.id
        GROUP BY u.id ORDER BY total_points DESC NULLS LAST
    ''').fetchall()
    conn.close()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>')
@admin_required
def admin_user_detail(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    sessions_data = conn.execute('''
        SELECT us.*, qs.name as session_name,
               COUNT(ua.id) as total_answered,
               SUM(CASE WHEN ua.is_correct THEN 1 ELSE 0 END) as correct_count,
               SUM(CASE WHEN ua.is_correct THEN q.points ELSE 0 END) as total_points,
               (SELECT COUNT(*) FROM questions qq JOIN sections ss ON qq.section_id=ss.id WHERE ss.session_id=qs.id) as total_questions
        FROM user_sessions us JOIN quiz_sessions qs ON us.session_id=qs.id
        LEFT JOIN user_answers ua ON us.id=ua.user_session_id
        LEFT JOIN questions q ON ua.question_id=q.id
        WHERE us.user_id=? GROUP BY us.id ORDER BY us.started_at DESC
    ''', (user_id,)).fetchall()
    codes = conn.execute('''
        SELECT ua.reward_code, ua.answered_at, q.question_text, qs.name as session_name
        FROM user_answers ua
        JOIN questions q ON ua.question_id=q.id
        JOIN sections s ON q.section_id=s.id
        JOIN quiz_sessions qs ON s.session_id=qs.id
        JOIN user_sessions us ON ua.user_session_id=us.id
        WHERE us.user_id=? AND ua.is_correct=1
        ORDER BY ua.answered_at DESC
    ''', (user_id,)).fetchall()
    # Cheat flags
    cheat_flags = conn.execute('''
        SELECT cf.violation_type, cf.flagged_at, qs.name as session_name
        FROM cheat_flags cf
        JOIN user_sessions us ON cf.user_session_id=us.id
        JOIN quiz_sessions qs ON us.session_id=qs.id
        WHERE us.user_id=?
        ORDER BY cf.flagged_at DESC LIMIT 50
    ''', (user_id,)).fetchall()
    conn.close()
    return render_template('admin/user_detail.html', user=user, sessions_data=sessions_data,
                           codes=codes, cheat_flags=cheat_flags)

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    conn = get_db()
    if request.method == 'POST':
        new_pw = request.form.get('new_password','').strip()
        if new_pw:
            conn.execute("UPDATE app_settings SET value=? WHERE key='admin_password'", (new_pw,))
            conn.commit()
            flash('Password updated!', 'success')
    conn.close()
    return render_template('admin/settings.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
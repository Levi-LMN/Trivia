"""
seed_march2026.py  (PostgreSQL version)
────────────────────────────────────────
Injects the "Individual Trivia Quiz - March 2026" session.

Session  : Individual Trivia Quiz - March 2026
Settings : Active · Randomized · 30 min timer
Sections : 1  ("Bible Knowledge")
Questions: 4

Uses the same DB credentials as the Flask app (env vars):
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

Run:
    python seed_march2026.py

Re-seed (wipe and re-insert):
    python seed_march2026.py --reset
"""

import sys, os
import psycopg2
import psycopg2.extras

RESET        = "--reset" in sys.argv
SESSION_NAME = "Individual Trivia Quiz - March 2026"

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_db():
    conn = psycopg2.connect(
        host    = os.environ.get("DB_HOST",     "localhost"),
        port    = int(os.environ.get("DB_PORT", 5432)),
        dbname  = os.environ.get("DB_NAME",     "bible_trivia"),
        user    = os.environ.get("DB_USER",     "bible_trivia_user"),
        password= os.environ.get("DB_PASSWORD", ""),
        connect_timeout=10,
    )
    conn.autocommit = False
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def q_single(conn, section_id, text, a, b, c, d, correct, points=2, order_num=0):
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO questions
               (section_id, question_type, question_text,
                option_a, option_b, option_c, option_d,
                correct_answer, blank_options, points, order_num)
           VALUES (%s, 'single', %s, %s, %s, %s, %s, %s, '[]', %s, %s)""",
        (section_id, text, a, b, c, d, correct.upper(), points, order_num),
    )
    cur.close()


def q_multi(conn, section_id, text, a, b, c, d, correct_list, points=2, order_num=0):
    correct = ",".join(sorted(x.upper() for x in correct_list))
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO questions
               (section_id, question_type, question_text,
                option_a, option_b, option_c, option_d,
                correct_answer, blank_options, points, order_num)
           VALUES (%s, 'multi', %s, %s, %s, %s, %s, %s, '[]', %s, %s)""",
        (section_id, text, a, b, c, d, correct, points, order_num),
    )
    cur.close()


def seed(conn):
    # ── Session ──────────────────────────────────────────────────────────────
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO quiz_sessions
               (name, description, is_active, randomize_questions, time_limit_minutes)
           VALUES (%s, %s, 1, 1, 30)
           RETURNING id""",
        (
            SESSION_NAME,
            "March 2026 individual trivia challenge covering Bible knowledge.",
        ),
    )
    session_id = cur.fetchone()["id"]
    cur.close()

    # ── Section ───────────────────────────────────────────────────────────────
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sections (session_id, name, order_num) VALUES (%s, %s, %s) RETURNING id",
        (session_id, "Bible Knowledge", 1),
    )
    sec_id = cur.fetchone()["id"]
    cur.close()

    # ── Questions ─────────────────────────────────────────────────────────────

    # Q1 — Single choice
    q_single(
        conn, sec_id,
        text      = "King Belshazzar made a feast for how many of his lords?",
        a         = "100",
        b         = "1000",
        c         = "1200",
        d         = "2300",
        correct   = "B",
        points    = 2,
        order_num = 1,
    )

    # Q2 — Single choice
    q_single(
        conn, sec_id,
        text      = "Who was king in Judah when Nebuchadnezzar came up against them to take them to exile?",
        a         = "Jehoiachin",
        b         = "Manasseh",
        c         = "Jehoiakim",
        d         = "Zedekiah",
        correct   = "C",
        points    = 2,
        order_num = 2,
    )

    # Q3 — Multi-select
    q_multi(
        conn, sec_id,
        text         = "Apart from promotion, what did King Belshazzar promise would be given for the one who translated the writing on the wall?",
        a            = "Gold ring",
        b            = "Gold chain",
        c            = "Clothed in purple",
        d            = "Clothed in scarlet",
        correct_list = ["B", "C"],
        points       = 2,
        order_num    = 3,
    )

    # Q4 — Single choice
    q_single(
        conn, sec_id,
        text      = "How old was Darius when he became king?",
        a         = "61",
        b         = "62",
        c         = "63",
        d         = "52",
        correct   = "B",
        points    = 2,
        order_num = 4,
    )

    conn.commit()
    print(f"✅  Session '{SESSION_NAME}' created (id={session_id})")
    print(f"    Section  : 'Bible Knowledge' (id={sec_id})")
    print(f"    Questions: 4  (3 single-choice · 1 multi-select · 8 total points)")


def main():
    conn = get_db()

    if RESET:
        print(f"⚠️   --reset: removing existing '{SESSION_NAME}' session…")
        cur = conn.cursor()
        cur.execute("DELETE FROM quiz_sessions WHERE name = %s", (SESSION_NAME,))
        conn.commit()
        cur.close()

    cur = conn.cursor()
    cur.execute("SELECT id FROM quiz_sessions WHERE name = %s", (SESSION_NAME,))
    existing = cur.fetchone()
    cur.close()

    if existing and not RESET:
        print(f"⚠️   Session '{SESSION_NAME}' already exists (id={existing['id']}).")
        print("    Run with --reset to wipe and re-seed.")
        conn.close()
        sys.exit(0)

    seed(conn)
    conn.close()
    print()
    print("🎉  Done! Refresh the admin panel to see the session.")


if __name__ == "__main__":
    main()
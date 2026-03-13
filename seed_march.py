"""
seed_march2026.py
─────────────────
Injects the "Individual Trivia Quiz - March 2026" session
exactly as shown in the admin screenshots.

Session  : Individual Trivia Quiz - March 2026
Settings : Active · Randomized · 30 min timer
Sections : 1  ("Bible Knowledge")
Questions: 4

Run from the same directory as bible_trivia.db:
    python seed_march2026.py

Re-seed (wipe and re-insert):
    python seed_march2026.py --reset
"""

import sqlite3, json, sys, os

DB    = os.environ.get("DATABASE", "bible_trivia.db")
RESET = "--reset" in sys.argv
SESSION_NAME = "Individual Trivia Quiz - March 2026"


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def q_single(conn, section_id, text, a, b, c, d, correct, points=2, order_num=0):
    conn.execute(
        """INSERT INTO questions
               (section_id, question_type, question_text,
                option_a, option_b, option_c, option_d,
                correct_answer, blank_options, points, order_num)
           VALUES (?, 'single', ?, ?, ?, ?, ?, ?, '[]', ?, ?)""",
        (section_id, text, a, b, c, d, correct.upper(), points, order_num),
    )


def q_multi(conn, section_id, text, a, b, c, d, correct_list, points=2, order_num=0):
    correct = ",".join(sorted(x.upper() for x in correct_list))
    conn.execute(
        """INSERT INTO questions
               (section_id, question_type, question_text,
                option_a, option_b, option_c, option_d,
                correct_answer, blank_options, points, order_num)
           VALUES (?, 'multi', ?, ?, ?, ?, ?, ?, '[]', ?, ?)""",
        (section_id, text, a, b, c, d, correct, points, order_num),
    )


def seed(conn):
    # ── Session ──────────────────────────────────────────────────────────────
    cur = conn.execute(
        """INSERT INTO quiz_sessions
               (name, description, is_active, randomize_questions, time_limit_minutes)
           VALUES (?, ?, 1, 1, 30)""",
        (
            SESSION_NAME,
            "March 2026 individual trivia challenge covering Bible knowledge.",
        ),
    )
    session_id = cur.lastrowid

    # ── Section ───────────────────────────────────────────────────────────────
    cur = conn.execute(
        "INSERT INTO sections (session_id, name, order_num) VALUES (?, ?, ?)",
        (session_id, "Bible Knowledge", 1),
    )
    sec_id = cur.lastrowid

    # ── Questions (in display order) ─────────────────────────────────────────

    # Q1 — Single choice
    q_single(
        conn, sec_id,
        text    = "King Belshazzar made a feast for how many of his lords?",
        a       = "100",
        b       = "1000",
        c       = "1200",
        d       = "2300",
        correct = "B",
        points  = 2,
        order_num = 1,
    )

    # Q2 — Single choice
    q_single(
        conn, sec_id,
        text    = "Who was king in Judah when Nebuchadnezzar came up against them to take them to exile?",
        a       = "Jehoiachin",
        b       = "Manasseh",
        c       = "Jehoiakim",
        d       = "Zedekiah",
        correct = "C",
        points  = 2,
        order_num = 2,
    )

    # Q3 — Multi-select
    q_multi(
        conn, sec_id,
        text          = "Apart from promotion, what did King Belshazzar promise would be given for the one who translated the writing on the wall?",
        a             = "Gold ring",
        b             = "Gold chain",
        c             = "Clothed in purple",
        d             = "Clothed in scarlet",
        correct_list  = ["B", "C"],
        points        = 2,
        order_num     = 3,
    )

    # Q4 — Single choice
    q_single(
        conn, sec_id,
        text    = "How old was Darius when he became king?",
        a       = "61",
        b       = "62",
        c       = "63",
        d       = "52",
        correct = "B",
        points  = 2,
        order_num = 4,
    )

    conn.commit()
    print(f"✅  Session '{SESSION_NAME}' created (id={session_id})")
    print(f"    Section : 'Bible Knowledge' (id={sec_id})")
    print(f"    Questions: 4  (3 single-choice · 1 multi-select · 8 total points)")


def main():
    if not os.path.exists(DB):
        print(f"❌  Database not found at '{DB}'.")
        print("    Start the Flask app once first (it calls init_db()), then re-run.")
        sys.exit(1)

    conn = get_db()

    if RESET:
        print(f"⚠️   --reset: removing existing '{SESSION_NAME}' session…")
        conn.execute("DELETE FROM quiz_sessions WHERE name=?", (SESSION_NAME,))
        conn.commit()

    existing = conn.execute(
        "SELECT id FROM quiz_sessions WHERE name=?", (SESSION_NAME,)
    ).fetchone()

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
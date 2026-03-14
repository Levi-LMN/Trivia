"""
seed_general_trivia.py  (PostgreSQL version)
─────────────────────────────────────────────
Injects the "General Bible Trivia" session.

Session   : General Bible Trivia
Settings  : Active · Randomized · 45 min timer
Sections  : 8
  1. The Beginning (Genesis & Exodus)
  2. The Law & The Land (Leviticus – Joshua)
  3. Kings & Prophets (Samuel – Malachi)
  4. Psalms & Wisdom (Psalms, Proverbs, Job, Ecclesiastes)
  5. The Life of Jesus (Gospels)
  6. The Early Church (Acts & Paul)
  7. Letters & Epistles (Romans – Jude)
  8. The End Times (Revelation)

Question types : single, multi, fill_blank
Total questions: 40
Total points   : 84

Uses the same DB credentials as the Flask app (env vars):
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

Run:
    python seed_general_trivia.py

Re-seed (wipe and re-insert):
    python seed_general_trivia.py --reset
"""

import sys, os, json
import psycopg2
import psycopg2.extras

RESET        = "--reset" in sys.argv
SESSION_NAME = "General Bible Trivia"

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ─── DB ───────────────────────────────────────────────────────────────────────

def get_db():
    conn = psycopg2.connect(
        host     = os.environ.get("DB_HOST",     "localhost"),
        port     = int(os.environ.get("DB_PORT", 5432)),
        dbname   = os.environ.get("DB_NAME",     "bible_trivia"),
        user     = os.environ.get("DB_USER",     "bible_trivia_user"),
        password = os.environ.get("DB_PASSWORD", ""),
        connect_timeout=10,
    )
    conn.autocommit = False
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


# ─── Question helpers ─────────────────────────────────────────────────────────

def q_single(conn, sec, text, a, b, c, d, correct, points=2, n=0):
    """Single-choice question.  correct = one letter e.g. 'B'."""
    conn.cursor().execute(
        """INSERT INTO questions
               (section_id, question_type, question_text,
                option_a, option_b, option_c, option_d,
                correct_answer, blank_options, points, order_num)
           VALUES (%s,'single',%s,%s,%s,%s,%s,%s,'[]',%s,%s)""",
        (sec, text, a, b, c or '', d or '',
         correct.strip().upper(), points, n),
    )


def q_multi(conn, sec, text, a, b, c, d, correct_list, points=2, n=0):
    """Multi-select question.  correct_list = list of letters e.g. ['A','C']."""
    correct = ','.join(sorted(x.strip().upper() for x in correct_list))
    conn.cursor().execute(
        """INSERT INTO questions
               (section_id, question_type, question_text,
                option_a, option_b, option_c, option_d,
                correct_answer, blank_options, points, order_num)
           VALUES (%s,'multi',%s,%s,%s,%s,%s,%s,'[]',%s,%s)""",
        (sec, text, a, b, c or '', d or '', correct, points, n),
    )


def q_fill(conn, sec, text, blank_options_list, correct_list, points=2, n=0):
    """
    Fill-in-the-blank question.

    text               : question string with ___ for each blank
    blank_options_list : list of lists  e.g. [['Adam','Eve','Noah'], ['Garden','Temple']]
    correct_list       : list of exact correct strings, one per blank
                         e.g. ['Adam', 'Garden']
    correct_answer stored as pipe-separated: 'Adam|Garden'
    blank_options stored as JSON: '[["Adam","Eve","Noah"],["Garden","Temple"]]'
    """
    bo_json = json.dumps(blank_options_list)
    correct  = '|'.join(str(c).strip() for c in correct_list)
    conn.cursor().execute(
        """INSERT INTO questions
               (section_id, question_type, question_text,
                option_a, option_b, option_c, option_d,
                correct_answer, blank_options, points, order_num)
           VALUES (%s,'fill_blank',%s,''  ,''  ,''  ,''  ,%s,%s,%s,%s)""",
        (sec, text, correct, bo_json, points, n),
    )


# ─── Seed ─────────────────────────────────────────────────────────────────────

def seed(conn):

    # ── Session ───────────────────────────────────────────────────────────────
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO quiz_sessions
               (name, description, is_active, randomize_questions, time_limit_minutes)
           VALUES (%s,%s,1,1,45) RETURNING id""",
        (
            SESSION_NAME,
            "A comprehensive Bible trivia challenge spanning both Testaments — "
            "covering history, prophecy, poetry, the Gospels, the early church, "
            "the epistles, and Revelation.",
        ),
    )
    sid = cur.fetchone()["id"]
    cur.close()

    def make_section(name, order):
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sections (session_id,name,order_num) VALUES (%s,%s,%s) RETURNING id",
            (sid, name, order),
        )
        sec_id = cur.fetchone()["id"]
        cur.close()
        return sec_id

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — The Beginning  (Genesis & Exodus)
    # ══════════════════════════════════════════════════════════════════════════
    s1 = make_section("The Beginning (Genesis & Exodus)", 1)

    q_single(conn, s1,
        "On which day did God create the sun, moon, and stars?",
        "Day 2", "Day 3", "Day 4", "Day 5",
        correct="C", points=2, n=1)

    q_single(conn, s1,
        "How many days and nights did it rain during Noah's flood?",
        "20", "30", "40", "50",
        correct="C", points=2, n=2)

    q_multi(conn, s1,
        "Which of the following are sons of Jacob (Israel)?",
        "Reuben", "Caleb", "Joseph", "Ishmael",
        correct_list=["A", "C"], points=3, n=3)

    q_fill(conn, s1,
        "God told Moses to remove his ___ because the place where he was standing was ___ ground.",
        [
            ["sandals", "staff", "robe", "belt"],
            ["holy", "fertile", "cursed", "dry"],
        ],
        ["sandals", "holy"],
        points=3, n=4)

    q_single(conn, s1,
        "What was the name of Moses' father-in-law?",
        "Aaron", "Jethro", "Hur", "Eleazar",
        correct="B", points=2, n=5)

    q_multi(conn, s1,
        "Select ALL the plagues God sent on Egypt.",
        "Locusts", "Earthquake", "Darkness", "Hailstorm",
        correct_list=["A", "C", "D"], points=4, n=6)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — The Law & The Land  (Leviticus – Joshua)
    # ══════════════════════════════════════════════════════════════════════════
    s2 = make_section("The Law & The Land (Leviticus – Joshua)", 2)

    q_single(conn, s2,
        "How many spies did Moses send into the land of Canaan?",
        "2", "7", "10", "12",
        correct="D", points=2, n=1)

    q_fill(conn, s2,
        "The Israelites marched around Jericho once a day for ___ days, "
        "and on the ___ day they marched around it seven times.",
        [
            ["3", "5", "6", "7"],
            ["fifth", "sixth", "seventh", "eighth"],
        ],
        ["6", "seventh"],
        points=3, n=2)

    q_single(conn, s2,
        "Which two spies gave a good report about the promised land?",
        "Moses and Aaron", "Joshua and Caleb",
        "Gad and Asher", "Reuben and Simeon",
        correct="B", points=2, n=3)

    q_multi(conn, s2,
        "Which of these are among the Ten Commandments?",
        "Do not murder", "Do not eat pork",
        "Do not covet", "Do not cut your hair",
        correct_list=["A", "C"], points=3, n=4)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — Kings & Prophets  (Judges – Malachi)
    # ══════════════════════════════════════════════════════════════════════════
    s3 = make_section("Kings & Prophets (Judges – Malachi)", 3)

    q_single(conn, s3,
        "Who was the first king of Israel?",
        "David", "Solomon", "Saul", "Samuel",
        correct="C", points=2, n=1)

    q_fill(conn, s3,
        "Samson's strength came from his ___, and his secret was revealed to ___ by Delilah.",
        [
            ["prayer", "hair", "armor", "sword"],
            ["Saul", "the Philistines", "King David", "the Egyptians"],
        ],
        ["hair", "the Philistines"],
        points=3, n=2)

    q_multi(conn, s3,
        "Which of the following were writing prophets of the Old Testament?",
        "Isaiah", "Gideon", "Jeremiah", "Samson",
        correct_list=["A", "C"], points=3, n=3)

    q_single(conn, s3,
        "How many years did Solomon's temple take to build?",
        "3", "5", "7", "10",
        correct="C", points=2, n=4)

    q_single(conn, s3,
        "Into which empire were the people of Judah taken into exile?",
        "Egyptian", "Assyrian", "Babylonian", "Persian",
        correct="C", points=2, n=5)

    q_fill(conn, s3,
        "The prophet ___ was swallowed by a great fish after fleeing to ___.",
        [
            ["Amos", "Hosea", "Jonah", "Micah"],
            ["Tarshish", "Nineveh", "Babylon", "Egypt"],
        ],
        ["Jonah", "Tarshish"],
        points=3, n=6)

    q_multi(conn, s3,
        "Which books are part of the Major Prophets?",
        "Ezekiel", "Daniel", "Obadiah", "Nahum",
        correct_list=["A", "B"], points=3, n=7)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — Psalms & Wisdom  (Psalms, Proverbs, Job, Ecclesiastes)
    # ══════════════════════════════════════════════════════════════════════════
    s4 = make_section("Psalms & Wisdom (Psalms, Proverbs, Job, Ecclesiastes)", 4)

    q_single(conn, s4,
        "Who wrote most of the Psalms?",
        "Solomon", "Moses", "David", "Asaph",
        correct="C", points=2, n=1)

    q_fill(conn, s4,
        "The Lord is my ___, I shall not ___.",
        [
            ["king", "shepherd", "rock", "fortress"],
            ["fear", "worry", "want", "stumble"],
        ],
        ["shepherd", "want"],
        points=3, n=2)

    q_single(conn, s4,
        "What does Proverbs say is the beginning of wisdom?",
        "Love of money", "Fear of the LORD",
        "Knowledge of self", "Humility before men",
        correct="B", points=2, n=3)

    q_multi(conn, s4,
        "Which of the following are books of wisdom/poetry in the Bible?",
        "Job", "Ruth", "Ecclesiastes", "Song of Solomon",
        correct_list=["A", "C", "D"], points=4, n=4)

    q_single(conn, s4,
        "How many children did Job have restored to him after his trials?",
        "The same 10", "7 sons and 3 daughters",
        "3 sons and 7 daughters", "14 sons and 6 daughters",
        correct="B", points=2, n=5)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — The Life of Jesus  (Gospels)
    # ══════════════════════════════════════════════════════════════════════════
    s5 = make_section("The Life of Jesus (Gospels)", 5)

    q_single(conn, s5,
        "In which town was Jesus born?",
        "Nazareth", "Jerusalem", "Bethlehem", "Capernaum",
        correct="C", points=2, n=1)

    q_fill(conn, s5,
        "Jesus fasted for ___ days and nights in the ___ where He was tempted by the devil.",
        [
            ["20", "30", "40", "50"],
            ["desert", "garden", "temple", "mountain"],
        ],
        ["40", "desert"],
        points=3, n=2)

    q_multi(conn, s5,
        "Which of the following miracles did Jesus perform?",
        "Turning water into wine", "Parting the Red Sea",
        "Raising Lazarus from the dead", "Calling down fire from heaven",
        correct_list=["A", "C"], points=3, n=3)

    q_single(conn, s5,
        "How many disciples did Jesus choose?",
        "7", "10", "12", "70",
        correct="C", points=2, n=4)

    q_fill(conn, s5,
        "The Sermon on the Mount begins with the ___, and Jesus taught it on a ___.",
        [
            ["Lord's Prayer", "Beatitudes", "Ten Commandments", "Parables"],
            ["mountain", "plain", "boat", "hillside"],
        ],
        ["Beatitudes", "mountain"],
        points=3, n=5)

    q_single(conn, s5,
        "Who baptised Jesus in the Jordan river?",
        "Peter", "John the Apostle",
        "John the Baptist", "Elijah",
        correct="C", points=2, n=6)

    q_multi(conn, s5,
        "Which of the following are among the twelve apostles of Jesus?",
        "Andrew", "Barnabas", "Matthew", "Titus",
        correct_list=["A", "C"], points=3, n=7)

    q_single(conn, s5,
        "For how much silver did Judas betray Jesus?",
        "10 pieces", "20 pieces", "30 pieces", "50 pieces",
        correct="C", points=2, n=8)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 6 — The Early Church  (Acts & Paul's Journeys)
    # ══════════════════════════════════════════════════════════════════════════
    s6 = make_section("The Early Church (Acts & Paul's Journeys)", 6)

    q_single(conn, s6,
        "On which day after Jesus' ascension did the Holy Spirit come at Pentecost?",
        "The 3rd day", "The 7th day",
        "The 10th day", "The 40th day",
        correct="C", points=2, n=1)

    q_fill(conn, s6,
        "Saul was travelling to ___ when he encountered Jesus in a blinding ___.",
        [
            ["Jerusalem", "Antioch", "Damascus", "Corinth"],
            ["storm", "light", "dream", "fire"],
        ],
        ["Damascus", "light"],
        points=3, n=2)

    q_multi(conn, s6,
        "Which of the following cities did Paul visit on his missionary journeys?",
        "Corinth", "Alexandria", "Ephesus", "Rome",
        correct_list=["A", "C", "D"], points=4, n=3)

    q_single(conn, s6,
        "Who was the first Christian martyr recorded in the book of Acts?",
        "James", "Stephen", "Philip", "Barnabas",
        correct="B", points=2, n=4)

    q_single(conn, s6,
        "Who was Paul's companion on his first missionary journey?",
        "Luke", "Silas", "Barnabas", "Timothy",
        correct="C", points=2, n=5)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 7 — Letters & Epistles  (Romans – Jude)
    # ══════════════════════════════════════════════════════════════════════════
    s7 = make_section("Letters & Epistles (Romans – Jude)", 7)

    q_single(conn, s7,
        "According to Romans 3:23, who has sinned and fallen short of the glory of God?",
        "Only the Gentiles", "Only unbelievers",
        "All have sinned", "Only Israel",
        correct="C", points=2, n=1)

    q_fill(conn, s7,
        "Paul writes in Philippians 4:13 that he can do ___ things through ___ who strengthens him.",
        [
            ["all", "great", "many", "good"],
            ["God", "Christ", "the Spirit", "faith"],
        ],
        ["all", "Christ"],
        points=3, n=2)

    q_multi(conn, s7,
        "Which of the following are listed as fruits of the Spirit in Galatians 5?",
        "Love", "Wealth", "Peace", "Power",
        correct_list=["A", "C"], points=3, n=3)

    q_single(conn, s7,
        "Which epistle contains the famous 'love chapter' (chapter 13)?",
        "Romans", "Galatians",
        "1 Corinthians", "Ephesians",
        correct="C", points=2, n=4)

    q_fill(conn, s7,
        "Hebrews 11:1 says faith is the ___ of things hoped for, the ___ of things not seen.",
        [
            ["proof", "substance", "essence", "reward"],
            ["certainty", "evidence", "dream", "promise"],
        ],
        ["substance", "evidence"],
        points=3, n=5)

    q_multi(conn, s7,
        "Select ALL the letters Paul wrote to an individual person (not a church).",
        "Philemon", "Colossians", "Titus", "Galatians",
        correct_list=["A", "C"], points=3, n=6)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 8 — The End Times  (Revelation)
    # ══════════════════════════════════════════════════════════════════════════
    s8 = make_section("The End Times (Revelation)", 8)

    q_single(conn, s8,
        "To which apostle was the book of Revelation given?",
        "Peter", "Paul", "John", "James",
        correct="C", points=2, n=1)

    q_single(conn, s8,
        "On which island was John when he received the Revelation?",
        "Cyprus", "Crete", "Malta", "Patmos",
        correct="D", points=2, n=2)

    q_multi(conn, s8,
        "To which of the following churches did Jesus send letters in Revelation chapters 2–3?",
        "Ephesus", "Antioch", "Smyrna", "Corinth",
        correct_list=["A", "C"], points=3, n=3)

    q_fill(conn, s8,
        "In Revelation, the number of the beast is ___, and the New Jerusalem comes down from ___.",
        [
            ["444", "616", "666", "777"],
            ["heaven", "earth", "the sea", "Zion"],
        ],
        ["666", "heaven"],
        points=3, n=4)

    q_single(conn, s8,
        "What are the four living creatures around the throne described as in Revelation 4?",
        "Lion, Eagle, Ox, Man",
        "Lion, Bear, Leopard, Dragon",
        "Eagle, Lamb, Serpent, Bull",
        "Cherub, Seraph, Angel, Archangel",
        correct="A", points=2, n=5)

    q_multi(conn, s8,
        "Which of the following are among the seven seals of Revelation?",
        "The rider on a white horse", "The fall of Babylon",
        "A great earthquake", "The mark of the beast",
        correct_list=["A", "C"], points=3, n=6)

    # ── Commit ────────────────────────────────────────────────────────────────
    conn.commit()

    sections = [
        ("The Beginning (Genesis & Exodus)", 6),
        ("The Law & The Land (Leviticus – Joshua)", 4),
        ("Kings & Prophets (Judges – Malachi)", 7),
        ("Psalms & Wisdom", 5),
        ("The Life of Jesus (Gospels)", 8),
        ("The Early Church (Acts & Paul's Journeys)", 5),
        ("Letters & Epistles (Romans – Jude)", 6),
        ("The End Times (Revelation)", 6),
    ]
    total_q = sum(n for _, n in sections)
    print(f"\n✅  Session '{SESSION_NAME}' created (id={sid})")
    print(f"    Sections : {len(sections)}")
    for name, count in sections:
        print(f"      • {name:50s} — {count} questions")
    print(f"    Total    : {total_q} questions · 45-min timer · randomized · active")
    print(f"    Points   : 84 pts (mix of 2-pt, 3-pt, and 4-pt questions)")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    conn = get_db()

    if RESET:
        print(f"⚠️   --reset: removing existing '{SESSION_NAME}' session…")
        cur = conn.cursor()
        cur.execute("DELETE FROM quiz_sessions WHERE name = %s", (SESSION_NAME,))
        conn.commit()
        cur.close()
        print("    Done. Re-seeding…\n")

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
    print("\n🎉  Done! Refresh the admin panel to see the session.")


if __name__ == "__main__":
    main()
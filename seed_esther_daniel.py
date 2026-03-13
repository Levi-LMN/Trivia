"""
seed_daniel_esther.py
─────────────────────
Injects two fully-featured quiz sessions into bible_trivia.db:

  Session 1 — "Book of Daniel"   (30 min timer, randomized)
  Session 2 — "Book of Esther"   (20 min timer, randomized)

Question types used:
  • single      — one correct option from A/B/C/D
  • multi        — multiple correct options (comma-separated letters)
  • fill_blank   — one or more blanks, each with a dropdown list

Run from the same directory as bible_trivia.db:
    python seed_daniel_esther.py

Run with --reset to wipe and re-insert (useful during dev):
    python seed_daniel_esther.py --reset
"""

import sqlite3, json, sys, os

DB = os.environ.get("DATABASE", "bible_trivia.db")
RESET = "--reset" in sys.argv


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ─── helpers ──────────────────────────────────────────────────────────────────

def insert_session(conn, name, description, time_limit_minutes, randomize=1):
    cur = conn.execute(
        """INSERT INTO quiz_sessions
               (name, description, is_active, randomize_questions, time_limit_minutes)
           VALUES (?, ?, 1, ?, ?)""",
        (name, description, randomize, time_limit_minutes),
    )
    return cur.lastrowid


def insert_section(conn, session_id, name, order_num):
    cur = conn.execute(
        "INSERT INTO sections (session_id, name, order_num) VALUES (?, ?, ?)",
        (session_id, name, order_num),
    )
    return cur.lastrowid


def q_single(conn, section_id, text, a, b, c, d, correct, points=1, order_num=0):
    """Single-choice question. correct = 'A'|'B'|'C'|'D'"""
    conn.execute(
        """INSERT INTO questions
               (section_id, question_type, question_text,
                option_a, option_b, option_c, option_d,
                correct_answer, blank_options, points, order_num)
           VALUES (?, 'single', ?, ?, ?, ?, ?, ?, '[]', ?, ?)""",
        (section_id, text, a, b, c, d, correct.upper(), points, order_num),
    )


def q_multi(conn, section_id, text, a, b, c, d, correct_list, points=2, order_num=0):
    """Multi-choice question. correct_list = ['A','C'] etc."""
    correct = ",".join(sorted(x.upper() for x in correct_list))
    conn.execute(
        """INSERT INTO questions
               (section_id, question_type, question_text,
                option_a, option_b, option_c, option_d,
                correct_answer, blank_options, points, order_num)
           VALUES (?, 'multi', ?, ?, ?, ?, ?, ?, '[]', ?, ?)""",
        (section_id, text, a, b, c, d, correct, points, order_num),
    )


def q_fill(conn, section_id, text, blanks, points=2, order_num=0):
    """Fill-in-the-blank question.
    blanks = list of (options_list, correct_answer) tuples.
    e.g. [(['Babylon','Egypt','Persia'], 'Babylon'), (['gold','silver','iron'], 'gold')]
    The question_text should use ___ to indicate blanks.
    correct_answer = pipe-separated: 'Babylon|gold'
    blank_options  = JSON: [['Babylon','Egypt','Persia'],['gold','silver','iron']]
    """
    opts_list = [b[0] for b in blanks]
    correct   = "|".join(b[1] for b in blanks)
    conn.execute(
        """INSERT INTO questions
               (section_id, question_type, question_text,
                option_a, option_b, option_c, option_d,
                correct_answer, blank_options, points, order_num)
           VALUES (?, 'fill_blank', ?, '', '', '', '', ?, ?, ?, ?)""",
        (section_id, text, correct, json.dumps(opts_list), points, order_num),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION 1 — BOOK OF DANIEL
# ══════════════════════════════════════════════════════════════════════════════

def seed_daniel(conn):
    sid = insert_session(
        conn,
        name="Book of Daniel",
        description="A deep dive into the life of Daniel, his three friends, and God's sovereign rule over the nations. Tests knowledge across all 12 chapters.",
        time_limit_minutes=30,
        randomize=1,
    )

    # ── Section 1: Captivity & the King's Court (Daniel 1) ─────────────────
    s1 = insert_section(conn, sid, "Captivity & the King's Court", 1)

    q_single(conn, s1,
        "In what year of King Jehoiakim's reign did Nebuchadnezzar besiege Jerusalem?",
        "First", "Third", "Fifth", "Seventh",
        "B", points=1, order_num=1)

    q_single(conn, s1,
        "Who was the chief of Nebuchadnezzar's officials who was placed over Daniel and his friends?",
        "Arioch", "Ashpenaz", "Belshazzar", "Shadrach",
        "B", points=1, order_num=2)

    q_fill(conn, s1,
        "Daniel resolved not to defile himself with the royal ___ or with the ___ the king drank.",
        [
            (["food", "wine", "gold", "laws"], "food"),
            (["wine", "water", "blood", "silver"], "wine"),
        ],
        points=2, order_num=3)

    q_single(conn, s1,
        "What Babylonian name was Daniel given?",
        "Meshach", "Abednego", "Belteshazzar", "Shadrach",
        "C", points=1, order_num=4)

    q_single(conn, s1,
        "After the ten-day test of vegetables and water, how did Daniel and his friends look compared to those who ate the king's food?",
        "Thinner and pale", "Healthier and better nourished", "The same", "Weaker but wiser",
        "B", points=1, order_num=5)

    q_multi(conn, s1,
        "Which of the following were among Daniel's three companions? (Select all that apply)",
        "Hananiah", "Mishael", "Azariah", "Tobiah",
        ["A", "B", "C"], points=3, order_num=6)

    # ── Section 2: Nebuchadnezzar's Dream (Daniel 2) ───────────────────────
    s2 = insert_section(conn, sid, "Nebuchadnezzar's Dream", 2)

    q_single(conn, s2,
        "What did Nebuchadnezzar demand of his wise men that was unusual?",
        "To interpret a dream he told them",
        "To tell him the dream AND its interpretation",
        "To produce the dream in writing",
        "To predict the next dream he would have",
        "B", points=2, order_num=1)

    q_fill(conn, s2,
        "The statue in Nebuchadnezzar's dream had a head of ___, chest and arms of ___, belly and thighs of ___, and legs of iron.",
        [
            (["gold", "silver", "bronze", "iron", "clay"], "gold"),
            (["silver", "gold", "bronze", "iron", "clay"], "silver"),
            (["bronze", "gold", "silver", "iron", "clay"], "bronze"),
        ],
        points=3, order_num=2)

    q_single(conn, s2,
        "What struck the statue and destroyed it in Nebuchadnezzar's dream?",
        "A great wind", "A rock cut out without human hands", "Fire from heaven", "A mighty sword",
        "B", points=1, order_num=3)

    q_single(conn, s2,
        "What reward did Nebuchadnezzar give Daniel after he revealed the dream?",
        "The throne of Babylon", "A purple robe and gold chain",
        "He made him ruler over the entire province of Babylon and placed him in charge of its wise men",
        "A palace and a hundred servants",
        "C", points=2, order_num=4)

    q_multi(conn, s2,
        "Which statements correctly describe the kingdoms represented by the statue? (Select all that apply)",
        "The gold head represented Nebuchadnezzar's kingdom",
        "The feet of iron and clay represented a divided kingdom",
        "The silver chest represented Egypt",
        "The rock that destroyed the statue represented God's eternal kingdom",
        ["A", "B", "D"], points=3, order_num=5)

    # ── Section 3: The Fiery Furnace (Daniel 3) ────────────────────────────
    s3 = insert_section(conn, sid, "The Fiery Furnace", 3)

    q_single(conn, s3,
        "How tall was the gold image Nebuchadnezzar set up on the plain of Dura?",
        "Thirty cubits", "Sixty cubits", "Ninety cubits", "One hundred cubits",
        "B", points=1, order_num=1)

    q_fill(conn, s3,
        "Whoever did not fall down and worship the image would be thrown into a ___ ___ furnace.",
        [
            (["blazing", "cold", "golden", "stone"], "blazing"),
            (["fiery", "stone", "iron", "clay"], "fiery"),
        ],
        points=2, order_num=2)

    q_single(conn, s3,
        "What did Shadrach, Meshach, and Abednego tell the king before being thrown into the furnace?",
        "They begged for mercy",
        "They said God would save them no matter what",
        "They declared God was able to save them, but even if He did not, they would not worship the idol",
        "They said they would worship the idol just once",
        "C", points=2, order_num=3)

    q_single(conn, s3,
        "How many men did Nebuchadnezzar see walking in the fire?",
        "Three", "Four", "Five", "Six",
        "B", points=1, order_num=4)

    q_single(conn, s3,
        "How did the king describe the appearance of the fourth person in the fire?",
        "Like a mighty warrior", "Like an angel of the LORD", "Like a son of the gods", "Like a prophet of Israel",
        "C", points=2, order_num=5)

    q_multi(conn, s3,
        "What was NOT harmed on the three men when they came out of the furnace? (Select all that apply)",
        "Their hair", "Their robes", "Their sandals", "No smell of fire was on them",
        ["A", "B", "D"], points=3, order_num=6)

    # ── Section 4: Nebuchadnezzar's Madness (Daniel 4) ────────────────────
    s4 = insert_section(conn, sid, "Nebuchadnezzar's Madness", 4)

    q_single(conn, s4,
        "In Nebuchadnezzar's second dream, what did the enormous tree represent?",
        "The kingdom of Persia", "Nebuchadnezzar himself", "The city of Babylon", "Daniel's prophetic ministry",
        "B", points=1, order_num=1)

    q_single(conn, s4,
        "How long was Nebuchadnezzar driven away from people to live like a wild animal?",
        "Three years", "Five years", "Seven years", "Forty years",
        "C", points=1, order_num=2)

    q_fill(conn, s4,
        "Nebuchadnezzar's hair grew like ___ feathers and his nails like ___ claws.",
        [
            (["eagle's", "lion's", "ox's", "bird's"], "eagle's"),
            (["bird's", "lion's", "eagle's", "ox's"], "bird's"),
        ],
        points=2, order_num=3)

    q_single(conn, s4,
        "What happened to Nebuchadnezzar after he acknowledged the sovereignty of God?",
        "He died immediately", "His sanity was restored and his kingdom was returned to him",
        "He became a servant of Daniel", "He was exiled to Persia",
        "B", points=1, order_num=4)

    # ── Section 5: Belshazzar's Feast & the Fall of Babylon (Daniel 5) ────
    s5 = insert_section(conn, sid, "Belshazzar's Feast", 5)

    q_single(conn, s5,
        "Whose vessels did Belshazzar use for drinking wine at his great feast?",
        "His father Nabonidus's treasury", "Those taken from the temple in Jerusalem",
        "Persian vessels of gold", "Egyptian vessels of silver",
        "B", points=1, order_num=1)

    q_fill(conn, s5,
        "The mysterious writing on the wall read: ___, ___, ___, ___.",
        [
            (["MENE", "TEKEL", "PERES", "UPHARSIN"], "MENE"),
            (["MENE", "TEKEL", "PERES", "UPHARSIN"], "MENE"),
            (["TEKEL", "MENE", "PERES", "UPHARSIN"], "TEKEL"),
            (["PERES", "MENE", "TEKEL", "UPHARSIN"], "PERES"),
        ],
        points=3, order_num=2)

    q_single(conn, s5,
        "What did TEKEL mean according to Daniel's interpretation?",
        "Your kingdom is divided",
        "You have been weighed on the scales and found wanting",
        "God has numbered the days of your reign",
        "Your kingdom is given to the Medes and Persians",
        "B", points=2, order_num=3)

    q_single(conn, s5,
        "What happened to Belshazzar that very night?",
        "He repented and was spared", "He fled to Persia",
        "He was slain", "He was imprisoned",
        "C", points=1, order_num=4)

    # ── Section 6: The Lions' Den (Daniel 6) ──────────────────────────────
    s6 = insert_section(conn, sid, "The Lions' Den", 6)

    q_single(conn, s6,
        "Why did the other administrators and satraps try to find grounds against Daniel?",
        "Because he was a foreigner", "Because they were jealous of his excellence and could find no corruption in him",
        "Because he refused to collect taxes", "Because he had insulted the king",
        "B", points=1, order_num=1)

    q_single(conn, s6,
        "How many times a day did Daniel pray, even after the decree was signed?",
        "Once", "Twice", "Three times", "Five times",
        "C", points=1, order_num=2)

    q_single(conn, s6,
        "Which direction did Daniel face when praying toward Jerusalem?",
        "East", "West", "North", "South (implied by Jerusalem's location from Babylon)",
        "D", points=2, order_num=3)

    q_fill(conn, s6,
        "Darius said to Daniel before he was thrown in: 'May your God, whom you serve ___, rescue you!'",
        [
            (["continually", "sometimes", "daily", "always"], "continually"),
        ],
        points=2, order_num=4)

    q_single(conn, s6,
        "What did Darius do after Daniel was thrown into the lions' den?",
        "Held a great feast", "Went home and slept soundly",
        "Returned to the palace, spent the night without eating, and refused entertainment, unable to sleep",
        "Ordered a search for Daniel's friends",
        "C", points=2, order_num=5)

    q_multi(conn, s6,
        "What was thrown into the lions' den after Daniel was found safe? (Select all that apply)",
        "Those who had falsely accused Daniel",
        "Their children",
        "Their wives",
        "Their servants",
        ["A", "B", "C"], points=3, order_num=6)

    # ── Section 7: Daniel's Visions (Daniel 7–12) ─────────────────────────
    s7 = insert_section(conn, sid, "Daniel's Visions & Prophecy", 7)

    q_single(conn, s7,
        "In Daniel's vision of four beasts, what did the fourth beast have that was different from the others?",
        "Wings of an eagle", "Ten horns", "Four heads", "The body of a bear",
        "B", points=1, order_num=1)

    q_single(conn, s7,
        "In Daniel 7, who came with the clouds of heaven and was given dominion and glory?",
        "An angel", "One like a son of man", "The Ancient of Days", "The archangel Michael",
        "B", points=2, order_num=2)

    q_single(conn, s7,
        "In Daniel 8, the vision of the ram with two horns represented which empires?",
        "Babylon and Persia", "Media and Persia", "Greece and Rome", "Egypt and Assyria",
        "B", points=2, order_num=3)

    q_fill(conn, s7,
        "Gabriel told Daniel that the vision of the ___ weeks concerned the holy city.",
        [
            (["seventy", "forty", "seven", "ten"], "seventy"),
        ],
        points=2, order_num=4)

    q_multi(conn, s7,
        "Which archangels are mentioned by name in the book of Daniel? (Select all that apply)",
        "Gabriel", "Michael", "Raphael", "Uriel",
        ["A", "B"], points=2, order_num=5)

    q_single(conn, s7,
        "According to Daniel 12:2, what will happen to many who sleep in the dust of the earth?",
        "They will remain asleep forever",
        "Some will awake to everlasting life, and some to everlasting contempt",
        "They will all be raised to everlasting life",
        "Only the righteous will be raised",
        "B", points=2, order_num=6)

    q_single(conn, s7,
        "What was Daniel told to do with the words of the scroll at the end of his book?",
        "Burn it", "Seal it until the time of the end", "Read it to the king", "Bury it in Jerusalem",
        "B", points=1, order_num=7)

    conn.commit()
    print(f"✅  Session 'Book of Daniel' created (id={sid})")
    return sid


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION 2 — BOOK OF ESTHER
# ══════════════════════════════════════════════════════════════════════════════

def seed_esther(conn):
    sid = insert_session(
        conn,
        name="Book of Esther",
        description="Test your knowledge of Esther's courage, Mordecai's faithfulness, Haman's plot, and God's hidden providence throughout the Persian court.",
        time_limit_minutes=20,
        randomize=1,
    )

    # ── Section 1: Ahasuerus's Feast & Vashti's Removal (Esther 1) ────────
    s1 = insert_section(conn, sid, "The Feast & Queen Vashti", 1)

    q_single(conn, s1,
        "Who was the Persian king in the book of Esther?",
        "Cyrus", "Darius", "Ahasuerus (Xerxes)", "Artaxerxes",
        "C", points=1, order_num=1)

    q_single(conn, s1,
        "How long did Ahasuerus's great feast in Susa last?",
        "Seven days", "Fourteen days", "One hundred and eighty days followed by a seven-day feast", "Forty days",
        "C", points=2, order_num=2)

    q_single(conn, s1,
        "Why did Queen Vashti lose her position as queen?",
        "She plotted against the king",
        "She refused the king's command to appear before his guests",
        "She was found to be unfaithful",
        "She was too old",
        "B", points=1, order_num=3)

    q_fill(conn, s1,
        "The king's advisers feared that Vashti's actions would cause all ___ to despise their ___.",
        [
            (["women", "nobles", "servants", "princes"], "women"),
            (["husbands", "wives", "kings", "masters"], "husbands"),
        ],
        points=2, order_num=4)

    # ── Section 2: Esther Becomes Queen (Esther 2) ────────────────────────
    s2 = insert_section(conn, sid, "Esther Becomes Queen", 2)

    q_single(conn, s2,
        "What was Esther's Hebrew name?",
        "Miriam", "Hadassah", "Deborah", "Abigail",
        "B", points=1, order_num=1)

    q_single(conn, s2,
        "Who raised Esther after her parents died?",
        "Her uncle Haman", "Her cousin Mordecai", "A Persian noble", "The king's chamberlain",
        "B", points=1, order_num=2)

    q_fill(conn, s2,
        "Esther did not reveal her ___ or ___ because Mordecai had told her not to.",
        [
            (["nationality", "age", "name", "family"], "nationality"),
            (["family background", "wealth", "beauty", "name"], "family background"),
        ],
        points=2, order_num=3)

    q_single(conn, s2,
        "How long was the beauty treatment required before a young woman went to the king?",
        "Three months", "Six months", "Twelve months", "Two years",
        "C", points=2, order_num=4)

    q_single(conn, s2,
        "What plot did Mordecai uncover and report through Esther?",
        "A plan to raise taxes", "An assassination plot against King Ahasuerus by two of his doorkeepers",
        "A conspiracy to put Haman on the throne", "A plan to poison the royal wine",
        "B", points=2, order_num=5)

    # ── Section 3: Haman's Plot (Esther 3) ────────────────────────────────
    s3 = insert_section(conn, sid, "Haman's Plot Against the Jews", 3)

    q_single(conn, s3,
        "Why did Mordecai refuse to kneel before Haman?",
        "He was physically unable to", "He was a Jew and would not bow",
        "He hated Haman personally", "The king had not specifically ordered it",
        "B", points=1, order_num=1)

    q_single(conn, s3,
        "How much silver did Haman offer to pay into the royal treasury to fund the destruction of the Jews?",
        "One hundred talents", "Five hundred talents",
        "Ten thousand talents of silver", "One thousand talents",
        "C", points=2, order_num=2)

    q_fill(conn, s3,
        "The ___ (lot) was cast before Haman to determine the day for the destruction of the Jews, falling in the month of ___.",
        [
            (["Pur", "Lot", "Decree", "Seal"], "Pur"),
            (["Adar", "Nisan", "Tishri", "Elul"], "Adar"),
        ],
        points=3, order_num=3)

    q_single(conn, s3,
        "What did the king give Haman after agreeing to his request?",
        "A chest of silver", "His signet ring", "An army of soldiers", "A royal proclamation",
        "B", points=1, order_num=4)

    # ── Section 4: Mordecai's Appeal & Esther's Courage (Esther 4–5) ──────
    s4 = insert_section(conn, sid, "Mordecai's Appeal & Esther's Courage", 4)

    q_single(conn, s4,
        "What did Mordecai do when he learned of Haman's decree?",
        "Fled the city", "Put on sackcloth and ashes and cried with a loud and bitter cry",
        "Went directly to the king", "Organised an army of Jews",
        "B", points=1, order_num=1)

    q_single(conn, s4,
        "What danger did Esther face in going unsummoned to the king?",
        "She would be imprisoned",
        "Anyone who went uninvited could be put to death unless the king extended his gold sceptre",
        "She would lose her title as queen", "She would be publicly humiliated",
        "B", points=2, order_num=2)

    q_fill(conn, s4,
        "Mordecai told Esther: 'Who knows but that you have come to your royal position for such a ___ as this?'",
        [
            (["time", "moment", "reason", "purpose"], "time"),
        ],
        points=2, order_num=3)

    q_single(conn, s4,
        "How many days did Esther ask the Jews of Susa to fast for her before she went to the king?",
        "One day", "Two days", "Three days", "Seven days",
        "C", points=1, order_num=4)

    q_single(conn, s4,
        "When Esther first approached the king unsummoned, what was his response?",
        "He called for the guards",
        "He extended his golden sceptre and asked what she wanted",
        "He was angry and dismissed her",
        "He did not notice her",
        "B", points=1, order_num=5)

    q_single(conn, s4,
        "Rather than immediately revealing her request, what did Esther invite the king and Haman to first?",
        "A public proclamation", "A banquet she had prepared", "A private audience in the garden", "A ceremony at the temple",
        "B", points=1, order_num=6)

    # ── Section 5: Haman's Pride & Fall (Esther 5–7) ──────────────────────
    s5 = insert_section(conn, sid, "Haman's Pride & Fall", 5)

    q_single(conn, s5,
        "Who told Haman to build a tall pole to impale Mordecai on?",
        "His servants", "His wife Zeresh and his friends", "The king", "His son",
        "B", points=1, order_num=1)

    q_fill(conn, s5,
        "The pole Haman built to impale Mordecai was ___ cubits high.",
        [
            (["fifty", "thirty", "sixty", "twenty"], "fifty"),
        ],
        points=2, order_num=2)

    q_single(conn, s5,
        "What kept the king awake the night before Haman planned to ask permission to hang Mordecai?",
        "A troubling dream", "The book of the chronicles was read to him",
        "He heard Mordecai praying", "Haman was pacing outside",
        "B", points=2, order_num=3)

    q_single(conn, s5,
        "When the king asked Haman what should be done for the man the king delights to honour — who did Haman think the king meant?",
        "Mordecai", "Himself", "Esther's father", "The chief of the army",
        "B", points=1, order_num=4)

    q_multi(conn, s5,
        "What did Haman suggest should be done for the man the king delights to honour? (Select all that apply)",
        "Bring royal robes the king has worn",
        "Parade him through the city on a horse the king has ridden",
        "Give him a province to rule",
        "Have a noble proclaim: 'This is what is done for the man the king delights to honour!'",
        ["A", "B", "D"], points=3, order_num=5)

    q_single(conn, s5,
        "How did the king respond when Esther revealed Haman's plot at the second banquet?",
        "He was sceptical", "He went into the garden in fury",
        "He immediately ordered Haman arrested", "He asked for more evidence",
        "B", points=2, order_num=6)

    q_single(conn, s5,
        "What sealed Haman's fate when the king returned from the garden?",
        "Haman had taken the king's crown",
        "Haman was found falling on the couch where Esther was",
        "Haman confessed to treason",
        "The chamberlain reported Haman's plot to the king",
        "B", points=2, order_num=7)

    q_single(conn, s5,
        "Who suggested impaling Haman on his own pole?",
        "Mordecai", "Esther", "Harbona, one of the king's eunuchs", "The chief chamberlain",
        "C", points=2, order_num=8)

    # ── Section 6: Salvation of the Jews (Esther 8–10) ────────────────────
    s6 = insert_section(conn, sid, "Salvation of the Jews & Purim", 6)

    q_single(conn, s6,
        "Why couldn't the king simply revoke Haman's original decree against the Jews?",
        "It had been sealed with the king's ring and a law of the Medes and Persians could not be repealed",
        "Haman's family had kept a copy", "The king had forgotten its contents", "The decree was already being carried out",
        "A", points=2, order_num=1)

    q_single(conn, s6,
        "What position was Mordecai given after Haman's fall?",
        "Commander of the army", "Second-in-command to King Ahasuerus", "Governor of Susa", "Chief adviser",
        "B", points=1, order_num=2)

    q_fill(conn, s6,
        "The new decree allowed the Jews to assemble and ___ themselves and to ___ and ___ those who attacked them.",
        [
            (["protect", "avenge", "arm", "hide"], "protect"),
            (["destroy", "forgive", "flee from", "report"], "destroy"),
            (["annihilate", "imprison", "scatter", "shame"], "annihilate"),
        ],
        points=3, order_num=3)

    q_single(conn, s6,
        "How many of their enemies did the Jews kill in the citadel of Susa on the first day?",
        "Three hundred", "Five hundred", "One thousand", "Two thousand",
        "B", points=2, order_num=4)

    q_single(conn, s6,
        "How many sons of Haman were killed?",
        "Five", "Seven", "Ten", "Twelve",
        "C", points=1, order_num=5)

    q_fill(conn, s6,
        "The festival of ___ is celebrated on the ___ and ___ of the month of Adar.",
        [
            (["Purim", "Passover", "Pentecost", "Tabernacles"], "Purim"),
            (["fourteenth", "first", "seventh", "tenth"], "fourteenth"),
            (["fifteenth", "last", "seventh", "seventeenth"], "fifteenth"),
        ],
        points=3, order_num=6)

    q_multi(conn, s6,
        "What activities are associated with the festival of Purim according to Esther 9? (Select all that apply)",
        "Feasting and joy",
        "Giving gifts of food to one another",
        "Giving gifts to the poor",
        "Fasting and mourning",
        ["A", "B", "C"], points=3, order_num=7)

    q_single(conn, s6,
        "What was Mordecai's standing among the Jews according to the final chapter of Esther?",
        "He was feared by all",
        "He was second in rank to King Ahasuerus, preeminent among the Jews, and held in high esteem",
        "He retired to his home province",
        "He became the new high priest",
        "B", points=2, order_num=8)

    conn.commit()
    print(f"✅  Session 'Book of Esther' created (id={sid})")
    return sid


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if not os.path.exists(DB):
        print(f"❌  Database not found at '{DB}'.")
        print("    Run the Flask app once first (it calls init_db()), then re-run this script.")
        sys.exit(1)

    conn = get_db()

    if RESET:
        print("⚠️   --reset: removing existing Daniel & Esther sessions…")
        conn.execute(
            "DELETE FROM quiz_sessions WHERE name IN ('Book of Daniel', 'Book of Esther')"
        )
        conn.commit()

    # Check for duplicates without --reset
    existing = conn.execute(
        "SELECT name FROM quiz_sessions WHERE name IN ('Book of Daniel', 'Book of Esther')"
    ).fetchall()
    if existing and not RESET:
        names = [r["name"] for r in existing]
        print(f"⚠️   Session(s) already exist: {names}")
        print("    Run with --reset to wipe and re-seed, or use --reset flag.")
        conn.close()
        sys.exit(0)

    daniel_id = seed_daniel(conn)
    esther_id = seed_esther(conn)

    # Summary
    stats = conn.execute("""
        SELECT qs.name,
               COUNT(DISTINCT s.id)  as sections,
               COUNT(DISTINCT q.id)  as questions,
               SUM(q.points)         as total_points,
               SUM(CASE WHEN q.question_type='single'     THEN 1 ELSE 0 END) as single_q,
               SUM(CASE WHEN q.question_type='multi'      THEN 1 ELSE 0 END) as multi_q,
               SUM(CASE WHEN q.question_type='fill_blank' THEN 1 ELSE 0 END) as fill_q
        FROM quiz_sessions qs
        LEFT JOIN sections s ON qs.id=s.session_id
        LEFT JOIN questions q ON s.id=q.section_id
        WHERE qs.id IN (?, ?)
        GROUP BY qs.id
    """, (daniel_id, esther_id)).fetchall()

    print()
    print("─" * 60)
    print(f"{'Session':<28} {'Sec':>4} {'Qs':>4} {'Pts':>5}  {'Single':>6}  {'Multi':>5}  {'Fill':>4}")
    print("─" * 60)
    for r in stats:
        print(f"{r['name']:<28} {r['sections']:>4} {r['questions']:>4} {r['total_points']:>5}  {r['single_q']:>6}  {r['multi_q']:>5}  {r['fill_q']:>4}")
    print("─" * 60)
    print()
    print("🎉  Seed complete! Open the admin panel to review and activate the sessions.")
    conn.close()


if __name__ == "__main__":
    main()
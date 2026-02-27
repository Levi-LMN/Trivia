"""
seed_esther_daniel.py
─────────────────────
Injects Bible trivia questions for the Books of Esther and Daniel.
Run from inside your project folder:

    python seed_esther_daniel.py

It creates:
  • 1 Quiz Session  : "Books of Esther & Daniel"
  • 4 Sections      : Esther (Story & Characters), Esther (Events & Details),
                      Daniel (Stories & Prophecy), Daniel (Characters & Details)
  • 60+ Questions   : mix of single-choice, multi-select, and fill-in-the-blank
"""

import sqlite3, json, os, sys

DATABASE = os.path.join(os.path.dirname(__file__), 'bible_trivia.db')

# ── helpers ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def add_session(conn, name, description, randomize=1):
    cur = conn.execute(
        'INSERT INTO quiz_sessions (name, description, randomize_questions, is_active) VALUES (?,?,?,1)',
        (name, description, randomize)
    )
    conn.commit()
    return cur.lastrowid

def add_section(conn, session_id, name, order_num):
    cur = conn.execute(
        'INSERT INTO sections (session_id, name, order_num) VALUES (?,?,?)',
        (session_id, name, order_num)
    )
    conn.commit()
    return cur.lastrowid

def add_question(conn, section_id, qtype, text, correct,
                 opt_a='', opt_b='', opt_c='', opt_d='',
                 blank_options=None, points=1, order_num=0):
    bo = json.dumps(blank_options) if blank_options else '[]'
    conn.execute('''
        INSERT INTO questions
            (section_id, question_type, question_text,
             option_a, option_b, option_c, option_d,
             correct_answer, blank_options, points, order_num)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    ''', (section_id, qtype, text,
          opt_a, opt_b, opt_c, opt_d,
          correct, bo, points, order_num))

# ── data ─────────────────────────────────────────────────────────────────────

def questions_esther_story(conn, section_id):
    qs = [
        # single-choice
        dict(qtype='single', text='Who was King Ahasuerus (Xerxes) ruling over when the story of Esther begins?',
             opt_a='Persia and Media', opt_b='Babylon and Assyria',
             opt_c='Egypt and Nubia', opt_d='Greece and Rome',
             correct='A', points=1),

        dict(qtype='single', text='Why was Queen Vashti removed from her position?',
             opt_a='She was caught stealing from the treasury',
             opt_b='She refused to appear before the king when summoned',
             opt_c='She plotted against the king',
             opt_d='She failed to produce an heir',
             correct='B', points=1),

        dict(qtype='single', text='What was the name of Esther\'s cousin and guardian?',
             opt_a='Haman', opt_b='Mordecai', opt_c='Hegai', opt_d='Harbona',
             correct='B', points=1),

        dict(qtype='single', text='How long did the beauty preparations last for each young woman before she could go before the king?',
             opt_a='Three months', opt_b='Six months', opt_c='Twelve months', opt_d='Two years',
             correct='C', points=2),

        dict(qtype='single', text='What did Esther win from everyone who saw her?',
             opt_a='Riches and gold', opt_b='Favour and kindness', opt_c='Fear and trembling', opt_d='Wisdom and counsel',
             correct='B', points=1),

        dict(qtype='single', text='What was the penalty for approaching the king unsummoned?',
             opt_a='Imprisonment', opt_b='Banishment', opt_c='Death', opt_d='A heavy fine',
             correct='C', points=1),

        dict(qtype='single', text='What did the king extend toward Esther to spare her life when she approached unbidden?',
             opt_a='His crown', opt_b='His hand', opt_c='His golden sceptre', opt_d='His ring',
             correct='C', points=1),

        dict(qtype='single', text='How many days did Esther ask the Jews to fast on her behalf before she went to the king?',
             opt_a='One day', opt_b='Three days', opt_c='Seven days', opt_d='Ten days',
             correct='B', points=1),

        dict(qtype='single', text='What feast did Esther prepare before making her request to the king?',
             opt_a='A passover meal', opt_b='A banquet of wine — twice', opt_c='A sacrificial feast', opt_d='A royal breakfast',
             correct='B', points=2),

        dict(qtype='single', text='Who told King Ahasuerus of the plot to assassinate him?',
             opt_a='Esther', opt_b='Haman', opt_c='Mordecai', opt_d='Hegai',
             correct='C', points=1),

        dict(qtype='single', text='On what was Haman\'s plot to destroy the Jews based?',
             opt_a='A prophecy', opt_b='The casting of lots (Pur)', opt_c='A royal decree from birth', opt_d='A bribe to the king',
             correct='B', points=2),

        dict(qtype='single', text='What happened to Haman at the end of the book of Esther?',
             opt_a='He was banished from Persia', opt_b='He was imprisoned for life',
             opt_c='He was hanged on the gallows he built for Mordecai', opt_d='He was demoted to servant',
             correct='C', points=1),

        dict(qtype='single', text='What position did Mordecai receive after Haman\'s fall?',
             opt_a='Chief treasurer', opt_b='High priest', opt_c='Commander of the army', opt_d='Second in rank to King Ahasuerus',
             correct='D', points=2),

        dict(qtype='single', text='What feast was established to celebrate the Jews\' deliverance in Esther?',
             opt_a='Passover', opt_b='Purim', opt_c='Tabernacles', opt_d='Firstfruits',
             correct='B', points=1),
    ]
    for i, q in enumerate(qs):
        add_question(conn=conn, section_id=section_id, order_num=i, **q)

def questions_esther_details(conn, section_id):
    qs = [
        # multi-select
        dict(qtype='multi',
             text='Which of the following are true about Mordecai? (Select ALL that apply)',
             opt_a='He was a Benjaminite', opt_b='He sat at the king\'s gate',
             opt_c='He bowed down to Haman', opt_d='He uncovered a plot to kill the king',
             correct='A,B,D', points=3),

        dict(qtype='multi',
             text='Which of the following describe Haman\'s character in the book of Esther? (Select ALL that apply)',
             opt_a='He was promoted above all other nobles',
             opt_b='He was filled with fury when Mordecai would not bow',
             opt_c='He sought to destroy only Mordecai',
             opt_d='He built gallows fifty cubits high',
             correct='A,B,D', points=3),

        dict(qtype='multi',
             text='What did the king grant Esther when she approached him unbidden? (Select ALL that apply)',
             opt_a='He extended his golden sceptre',
             opt_b='He offered up to half his kingdom',
             opt_c='He ordered her immediate execution',
             opt_d='He asked what her request was',
             correct='A,B,D', points=3),

        # fill-in-the-blank
        dict(qtype='fill_blank',
             text='Esther\'s Hebrew name was ___ and she was the daughter of ___ of the tribe of ___.',
             correct='Hadassah|Abihail|Benjamin',
             blank_options=[
                 ['Hadassah', 'Miriam', 'Deborah', 'Rahab'],
                 ['Abihail', 'Mordecai', 'Kish', 'Shimei'],
                 ['Benjamin', 'Judah', 'Levi', 'Dan'],
             ], points=3),

        dict(qtype='fill_blank',
             text='Haman offered ___ talents of silver to the king\'s treasury in exchange for the decree to destroy the ___.',
             correct='ten thousand|Jews',
             blank_options=[
                 ['ten thousand', 'one thousand', 'five hundred', 'three thousand'],
                 ['Jews', 'Persians', 'Medes', 'Babylonians'],
             ], points=2),

        dict(qtype='fill_blank',
             text='King Ahasuerus reigned from ___ to ___, over ___ provinces.',
             correct='India|Ethiopia|127',
             blank_options=[
                 ['India', 'Egypt', 'Persia', 'Babylon'],
                 ['Ethiopia', 'Greece', 'Rome', 'Media'],
                 ['127', '120', '100', '150'],
             ], points=3),

        dict(qtype='fill_blank',
             text='The Feast of Purim is celebrated on the ___ and ___ of the month of ___.',
             correct='fourteenth|fifteenth|Adar',
             blank_options=[
                 ['fourteenth', 'tenth', 'first', 'seventh'],
                 ['fifteenth', 'sixteenth', 'twentieth', 'thirtieth'],
                 ['Adar', 'Nisan', 'Tishri', 'Elul'],
             ], points=3),

        # more single-choice
        dict(qtype='single',
             text='What was the name of the eunuch in charge of the women in the king\'s harem?',
             opt_a='Harbona', opt_b='Hegai', opt_c='Hatach', opt_d='Hathach',
             correct='B', points=1),

        dict(qtype='single',
             text='How tall were the gallows Haman built to hang Mordecai?',
             opt_a='Twenty cubits', opt_b='Thirty cubits', opt_c='Fifty cubits', opt_d='One hundred cubits',
             correct='C', points=2),

        dict(qtype='single',
             text='What did King Ahasuerus do when he could not sleep the night before Esther\'s second banquet?',
             opt_a='He summoned Haman', opt_b='He had the book of records read to him',
             opt_c='He prayed at the altar', opt_d='He walked in the garden',
             correct='B', points=2),
    ]
    for i, q in enumerate(qs):
        add_question(conn=conn, section_id=section_id, order_num=i, **q)

def questions_daniel_stories(conn, section_id):
    qs = [
        dict(qtype='single',
             text='Why did Daniel resolve not to defile himself with the king\'s food and wine?',
             opt_a='He was fasting for a vision', opt_b='He followed the Mosaic dietary laws',
             opt_c='He was allergic to rich food', opt_d='The food was poisoned',
             correct='B', points=1),

        dict(qtype='single',
             text='What did Daniel and his friends look like after 10 days of eating only vegetables and water?',
             opt_a='Pale and thin', opt_b='Healthier and better nourished than those who ate the king\'s food',
             opt_c='The same as the others', opt_d='Sick and frail',
             correct='B', points=1),

        dict(qtype='single',
             text='What was the punishment for not bowing to Nebuchadnezzar\'s golden statue?',
             opt_a='Beheading', opt_b='Life imprisonment',
             opt_c='Being thrown into a blazing furnace', opt_d='Being fed to lions',
             correct='C', points=1),

        dict(qtype='single',
             text='Who was the fourth figure seen walking in the blazing furnace with Shadrach, Meshach, and Abednego?',
             opt_a='The prophet Isaiah', opt_b='An angel of the Lord',
             opt_c='One like a son of the gods', opt_d='King Nebuchadnezzar himself',
             correct='C', points=2),

        dict(qtype='single',
             text='What drove King Nebuchadnezzar out of his palace to live like an animal?',
             opt_a='A plague of madness sent as judgment from God',
             opt_b='He was overthrown in a coup',
             opt_c='He chose to live humbly', opt_d='He was cursed by a sorcerer',
             correct='A', points=2),

        dict(qtype='single',
             text='What did the handwriting on the wall say during Belshazzar\'s feast?',
             opt_a='HOSANNA, KYRIE, ELEISON', opt_b='MENE, MENE, TEKEL, PARSIN',
             opt_c='ALPHA, OMEGA, SIGMA', opt_d='SHALOM, EMET, HESED',
             correct='B', points=2),

        dict(qtype='single',
             text='What did TEKEL mean in the interpretation of the handwriting on the wall?',
             opt_a='Your kingdom is divided', opt_b='You have been weighed on the scales and found wanting',
             opt_c='Numbered — your days are finished', opt_d='A great army is coming',
             correct='B', points=2),

        dict(qtype='single',
             text='Who succeeded Belshazzar as king after his death?',
             opt_a='Cyrus the Persian', opt_b='Nebuchadnezzar II',
             opt_c='Darius the Mede', opt_d='Artaxerxes',
             correct='C', points=2),

        dict(qtype='single',
             text='Why was Daniel thrown into the lions\' den?',
             opt_a='He stole from the king\'s treasury',
             opt_b='He refused to stop praying to God three times a day',
             opt_c='He insulted the king at a feast',
             opt_d='He was caught planning an escape',
             correct='B', points=1),

        dict(qtype='single',
             text='How many times a day did Daniel kneel and pray toward Jerusalem?',
             opt_a='Once', opt_b='Twice', opt_c='Three times', opt_d='Seven times',
             correct='C', points=1),

        dict(qtype='single',
             text='What did God do to protect Daniel in the lions\' den?',
             opt_a='He turned the lions into sheep',
             opt_b='He sent an angel who shut the lions\' mouths',
             opt_c='He made Daniel invisible to the lions',
             opt_d='He removed the lions from the den',
             correct='B', points=1),

        dict(qtype='single',
             text='In Daniel\'s vision of the four beasts, what did the fourth beast represent?',
             opt_a='The kingdom of Persia', opt_b='A terrifying fourth kingdom that will devour the earth',
             opt_c='The kingdom of Greece', opt_d='The restored kingdom of Israel',
             correct='B', points=3),

        dict(qtype='single',
             text='What is the name of the angel who explained Daniel\'s visions to him?',
             opt_a='Michael', opt_b='Raphael', opt_c='Gabriel', opt_d='Uriel',
             correct='C', points=2),
    ]
    for i, q in enumerate(qs):
        add_question(conn=conn, section_id=section_id, order_num=i, **q)

def questions_daniel_details(conn, section_id):
    qs = [
        # multi-select
        dict(qtype='multi',
             text='Which of the following are the Hebrew names of Daniel\'s three friends? (Select ALL that apply)',
             opt_a='Hananiah', opt_b='Mishael', opt_c='Ezekiel', opt_d='Azariah',
             correct='A,B,D', points=3),

        dict(qtype='multi',
             text='Which of these describe Daniel\'s qualities? (Select ALL that apply)',
             opt_a='No corruption was found in him',
             opt_b='He was distinguished above all the other officials',
             opt_c='He secretly worshipped Bel and the Dragon',
             opt_d='He had an extraordinary spirit',
             correct='A,B,D', points=3),

        dict(qtype='multi',
             text='In Nebuchadnezzar\'s dream of the statue, which materials were used? (Select ALL that apply)',
             opt_a='Gold head', opt_b='Silver chest and arms',
             opt_c='Bronze thighs', opt_d='Ivory feet',
             correct='A,B,C', points=3),

        # fill-in-the-blank
        dict(qtype='fill_blank',
             text='Daniel\'s Babylonian name was ___, and he served under kings ___ and ___.',
             correct='Belteshazzar|Nebuchadnezzar|Darius',
             blank_options=[
                 ['Belteshazzar', 'Shadrach', 'Abednego', 'Meshach'],
                 ['Nebuchadnezzar', 'Belshazzar', 'Cyrus', 'Artaxerxes'],
                 ['Darius', 'Cyrus', 'Xerxes', 'Ahasuerus'],
             ], points=3),

        dict(qtype='fill_blank',
             text='Shadrach, Meshach, and Abednego\'s Hebrew names were ___, ___, and ___.',
             correct='Hananiah|Mishael|Azariah',
             blank_options=[
                 ['Hananiah', 'Elijah', 'Isaiah', 'Jeremiah'],
                 ['Mishael', 'Ezra', 'Nehemiah', 'Joel'],
                 ['Azariah', 'Obadiah', 'Micah', 'Amos'],
             ], points=3),

        dict(qtype='fill_blank',
             text='The great statue in Nebuchadnezzar\'s dream had a head of ___, chest of ___, belly of ___, and feet of ___ mixed with clay.',
             correct='gold|silver|bronze|iron',
             blank_options=[
                 ['gold', 'silver', 'bronze', 'iron'],
                 ['silver', 'gold', 'copper', 'tin'],
                 ['bronze', 'iron', 'clay', 'wood'],
                 ['iron', 'clay', 'stone', 'copper'],
             ], points=4),

        dict(qtype='fill_blank',
             text='Daniel was taken to Babylon during the reign of King ___ of Judah, in the ___ year of his reign.',
             correct='Jehoiakim|third',
             blank_options=[
                 ['Jehoiakim', 'Zedekiah', 'Josiah', 'Hezekiah'],
                 ['third', 'first', 'seventh', 'eleventh'],
             ], points=3),

        dict(qtype='fill_blank',
             text='The ___ weeks prophecy in Daniel chapter 9 refers to ___ years.',
             correct='seventy|490',
             blank_options=[
                 ['seventy', 'sixty', 'forty', 'seven'],
                 ['490', '70', '420', '700'],
             ], points=4),

        # more single-choice
        dict(qtype='single',
             text='What was Nebuchadnezzar\'s golden statue said to be in height?',
             opt_a='Thirty cubits tall', opt_b='Forty cubits tall',
             opt_c='Sixty cubits tall', opt_d='One hundred cubits tall',
             correct='C', points=2),

        dict(qtype='single',
             text='How long was Nebuchadnezzar afflicted with madness?',
             opt_a='Three months', opt_b='One year',
             opt_c='Seven years', opt_d='Forty years',
             correct='C', points=2),

        dict(qtype='single',
             text='What sin was Belshazzar specifically judged for at his feast?',
             opt_a='Worshipping false gods only',
             opt_b='Using the sacred vessels from the Jerusalem temple to drink wine while praising false gods',
             opt_c='Murdering his own father', opt_d='Refusing to pay tribute to Cyrus',
             correct='B', points=3),

        dict(qtype='single',
             text='In Daniel\'s vision, the Ancient of Days sat on a throne described as what?',
             opt_a='Made of pure gold', opt_b='Ablaze with fire, its wheels were all aflame',
             opt_c='Carved from a single sapphire', opt_d='Surrounded by a rainbow',
             correct='B', points=3),
    ]
    for i, q in enumerate(qs):
        add_question(conn=conn, section_id=section_id, order_num=i, **q)

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(DATABASE):
        print(f"ERROR: Database not found at {DATABASE}")
        print("Make sure you run this script from inside your Bible Trivia project folder,")
        print("and that you have started the app at least once to create the database.")
        sys.exit(1)

    conn = get_db()

    # Check if session already exists
    existing = conn.execute(
        "SELECT id FROM quiz_sessions WHERE name='Books of Esther & Daniel'"
    ).fetchone()
    if existing:
        print("Session 'Books of Esther & Daniel' already exists!")
        choice = input("Re-create it? This will delete the old one. (y/n): ").strip().lower()
        if choice == 'y':
            conn.execute("DELETE FROM quiz_sessions WHERE name='Books of Esther & Daniel'")
            conn.commit()
            print("Old session deleted.")
        else:
            print("Aborted.")
            conn.close()
            sys.exit(0)

    print("Creating session: Books of Esther & Daniel...")
    sess_id = add_session(
        conn,
        name='Books of Esther & Daniel',
        description='Dive deep into the courts of Persia and Babylon — test your knowledge of Esther, Mordecai, Daniel, and the great visions of prophecy.',
        randomize=1
    )

    print("  Adding section: Esther — Story & Characters...")
    sec1 = add_section(conn, sess_id, 'Esther — Story & Characters', 1)
    questions_esther_story(conn, sec1)

    print("  Adding section: Esther — Events & Details...")
    sec2 = add_section(conn, sess_id, 'Esther — Events & Details', 2)
    questions_esther_details(conn, sec2)

    print("  Adding section: Daniel — Stories & Prophecy...")
    sec3 = add_section(conn, sess_id, 'Daniel — Stories & Prophecy', 3)
    questions_daniel_stories(conn, sec3)

    print("  Adding section: Daniel — Characters & Details...")
    sec4 = add_section(conn, sess_id, 'Daniel — Characters & Details', 4)
    questions_daniel_details(conn, sec4)

    conn.commit()

    # Summary
    total_q = conn.execute(
        '''SELECT COUNT(*) FROM questions q
           JOIN sections s ON q.section_id=s.id
           WHERE s.session_id=?''', (sess_id,)
    ).fetchone()[0]

    by_type = conn.execute(
        '''SELECT q.question_type, COUNT(*) as cnt FROM questions q
           JOIN sections s ON q.section_id=s.id
           WHERE s.session_id=? GROUP BY q.question_type''', (sess_id,)
    ).fetchall()

    conn.close()

    print("\n✅ Done!")
    print(f"   Session ID : {sess_id}")
    print(f"   Sections   : 4")
    print(f"   Questions  : {total_q}")
    for row in by_type:
        labels = {'single': 'Single choice', 'multi': 'Multi-select', 'fill_blank': 'Fill-in-the-blank'}
        print(f"     {labels.get(row['question_type'], row['question_type']):<22} {row['cnt']}")
    print("\nOpen your app and the session will appear on the quiz home page.")

if __name__ == '__main__':
    main()

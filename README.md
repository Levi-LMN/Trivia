# ✝ Bible Trivia App

A Flask + SQLite + Tailwind CSS Bible trivia web app.

## Quick Start

```bash
pip install flask
python app.py
```

Then open http://localhost:5000

## Admin Panel

Go to http://localhost:5000/admin  
Default password: **admin123** *(change this in Settings)*

## App Structure

```
bible_trivia/
├── app.py                  # All routes & DB logic
├── requirements.txt
└── templates/
    ├── base.html           # User-facing base layout
    ├── index.html          # Phone number login
    ├── register.html       # New user name entry
    ├── quiz_home.html      # Session selection
    ├── quiz.html           # Question answering
    ├── results.html        # Scores & reward codes
    └── admin/
        ├── base.html       # Admin sidebar layout
        ├── login.html
        ├── dashboard.html  # Stats + leaderboard
        ├── sessions.html   # CRUD quiz sessions
        ├── sections.html   # CRUD sections per session
        ├── questions.html  # CRUD questions per section
        ├── users.html      # All users & scores
        ├── user_detail.html
        └── settings.html   # Change admin password
```

## Features

### User Flow
1. Enter phone number → new users provide their name once
2. Select an active quiz session
3. Answer questions one at a time (randomized if toggled on)
4. Get a **reward code** for each correct answer
5. View results / scores at any point

### Admin Panel
- **Sessions**: Create, activate/deactivate, toggle randomization, delete
- **Sections**: Organize questions into sections within a session
- **Questions**: Add/edit/delete questions with A/B/C/D options & point values
- **Users & Scores**: Full leaderboard with accuracy %, points, reward codes
- **Settings**: Change admin password

## Database

Single SQLite file `bible_trivia.db` auto-created on first run.

Tables: `users`, `quiz_sessions`, `sections`, `questions`, `user_sessions`, `user_answers`, `app_settings`
# Trivia

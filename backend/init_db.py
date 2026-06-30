"""
Idempotent database initialisation.  Run this before the web server
starts (Render's preDeployCommand).  It creates tables, seeds reference
data, and creates a default admin user — all safely skipped if already
present.  It never drops existing data.
"""
import os
import sys

# Allow running from the project root as well as from backend/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db  # noqa: E402 — needs sys.path fix above first

DDL = """
CREATE TABLE IF NOT EXISTS users (
    user_id        SERIAL PRIMARY KEY,
    username       VARCHAR(50) UNIQUE NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    email          VARCHAR(100) UNIQUE NOT NULL,
    full_name      VARCHAR(100),
    age            INT,
    gender         VARCHAR(20),
    occupation     VARCHAR(50),
    role           VARCHAR(20) NOT NULL DEFAULT 'user'
                     CHECK (role IN ('user', 'admin')),
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stress_assessments (
    assessment_id    SERIAL PRIMARY KEY,
    user_id          INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    assessment_date  TIMESTAMP NOT NULL DEFAULT NOW(),
    responses_json   TEXT NOT NULL,
    total_score      INT NOT NULL,
    severity_level   VARCHAR(20) NOT NULL,
    stress_category  VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS interventions (
    intervention_id      SERIAL PRIMARY KEY,
    intervention_name    VARCHAR(100) NOT NULL,
    intervention_type    VARCHAR(50) NOT NULL,
    description          TEXT,
    target_severity      VARCHAR(20),
    effectiveness_rating FLOAT NOT NULL DEFAULT 3.0
);

CREATE TABLE IF NOT EXISTS user_interventions (
    id               SERIAL PRIMARY KEY,
    user_id          INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    intervention_id  INT NOT NULL REFERENCES interventions(intervention_id) ON DELETE CASCADE,
    assessment_id    INT REFERENCES stress_assessments(assessment_id) ON DELETE SET NULL,
    rating           FLOAT,
    taken_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS progress_tracking (
    progress_id     SERIAL PRIMARY KEY,
    user_id         INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    tracking_date   TIMESTAMP NOT NULL DEFAULT NOW(),
    stress_level    INT NOT NULL,
    mood_rating     INT NOT NULL,
    notes           VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS knowledge_base (
    resource_id  SERIAL PRIMARY KEY,
    title        VARCHAR(200) NOT NULL,
    category     VARCHAR(100),
    content      TEXT NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id      SERIAL PRIMARY KEY,
    user_id          INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    intervention_id  INT REFERENCES interventions(intervention_id) ON DELETE SET NULL,
    rating           INT CHECK (rating BETWEEN 1 AND 5),
    comments         TEXT,
    submitted_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assessments_user ON stress_assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_progress_user ON progress_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_ui_user ON user_interventions(user_id);
CREATE INDEX IF NOT EXISTS idx_ui_intervention ON user_interventions(intervention_id);
"""

INTERVENTIONS = [
    ("5-Minute Box Breathing", "Anxiety", "A paced-breathing exercise (4s in, 4s hold, 4s out, 4s hold) to calm the nervous system.", "Low", 4.1),
    ("Guided Worry Journaling", "Anxiety", "Write down anxious thoughts and challenge them with evidence-based reframing prompts.", "Moderate", 4.0),
    ("Progressive Muscle Relaxation", "Anxiety", "Systematically tense and release muscle groups to reduce physical anxiety symptoms.", "High", 4.3),
    ("Crisis Grounding Technique (5-4-3-2-1)", "Anxiety", "A sensory grounding exercise for acute anxiety spikes.", "Very High", 4.2),
    ("Sleep Hygiene Checklist", "Sleep", "A nightly routine checklist (consistent bedtime, no screens, cool dark room) to improve sleep quality.", "Low", 3.9),
    ("Wind-Down Meditation (15 min)", "Sleep", "Guided audio meditation designed to ease the transition into sleep.", "Moderate", 4.1),
    ("Sleep Restriction Therapy Guide", "Sleep", "A structured self-help guide based on CBT-I principles to fix disrupted sleep patterns.", "High", 4.4),
    ("Professional Sleep Consultation Referral", "Sleep", "Referral information for a sleep specialist or counselor.", "Very High", 4.5),
    ("Pomodoro Task Sprints", "Time Management", "25-minute focused work sprints with 5-minute breaks to reduce task overwhelm.", "Low", 3.8),
    ("Weekly Priority Matrix Planning", "Time Management", "Use an urgent/important matrix to triage tasks and reduce workload anxiety.", "Moderate", 4.0),
    ("Delegation & Boundary-Setting Workshop", "Time Management", "Self-guided exercises for saying no and redistributing workload.", "High", 4.0),
    ("Academic/Work Load Re-negotiation Plan", "Workload", "A structured template for discussing deadline extensions or workload reduction.", "Very High", 4.1),
    ("Desk Stretch Routine (10 min)", "Physical", "A short stretching routine to relieve tension headaches and physical fatigue.", "Low", 3.7),
    ("30-Minute Brisk Walk Plan", "Physical", "A weekly cardio plan shown to reduce cortisol and improve mood.", "Moderate", 4.2),
    ("Structured Exercise Program (3x/week)", "Physical", "A beginner strength + cardio program to build long-term stress resilience.", "High", 4.3),
    ("Self-Compassion Break", "Emotional Exhaustion", "A 3-step mindfulness practice for moments of emotional overwhelm.", "Low", 3.9),
    ("Daily Gratitude & Mood Log", "Emotional Exhaustion", "Track mood and three good things daily to counter emotional depletion.", "Moderate", 3.8),
    ("Burnout Recovery Plan", "Emotional Exhaustion", "A multi-week structured plan for recovering from emotional exhaustion / burnout.", "High", 4.3),
    ("Counseling Referral Pack", "Emotional Exhaustion", "Curated list of accessible, low-cost professional counseling resources.", "Very High", 4.6),
    ("Focus Reset Technique", "Cognitive", "A short technique to clear mental clutter and regain concentration.", "Low", 3.6),
    ("Single-Tasking Practice Plan", "Cognitive", "Exercises to rebuild concentration by eliminating multitasking habits.", "Moderate", 3.9),
    ("Two-Minute Reset Ritual", "Relaxation", "A quick reset ritual (stretch + breathe + reframe) to use between tasks.", "Low", 3.7),
    ("Evening Digital Detox Plan", "Relaxation", "A structured plan to disconnect from screens after work/school to support recovery.", "Moderate", 3.9),
    ("Problem-Solving Coping Worksheet", "Coping", "A structured worksheet (problem-focused coping) to break down a stressor into actionable steps.", "Moderate", 4.0),
    ("Emotion-Focused Coping Toolkit", "Coping", "A toolkit of emotion-focused techniques (relaxation, reframing, social support seeking).", "High", 4.1),
    ("Professional Counseling Referral", "Coping", "Referral pack to licensed counselors/therapists for individuals at severe stress levels.", "Very High", 4.7),
]

ARTICLES = [
    ("Understanding Stress: The Transactional Theory", "Education",
     "Stress occurs when you appraise a situation as exceeding your coping resources (Lazarus & Folkman, 1984). Primary appraisal asks \"is this a threat?\"; secondary appraisal asks \"can I handle it?\" Understanding this can help you separate the stressor from your reaction to it."),
    ("Problem-Focused vs Emotion-Focused Coping", "Education",
     "Problem-focused coping targets the source of stress directly (planning, problem-solving). Emotion-focused coping manages your reaction (relaxation, reframing, social support). Most people need both, depending on whether the stressor is within their control."),
    ("Why Sleep and Stress Feed Each Other", "Sleep",
     "Chronic stress raises cortisol, which disrupts sleep; poor sleep then reduces your capacity to cope with stress the next day. Breaking this cycle usually starts with consistent sleep/wake times, not just \"more sleep\"."),
    ("The Yerkes-Dodson Law: Stress Isn't Always Bad", "Education",
     "A moderate amount of stress (arousal) improves performance up to a point, after which performance declines (Yerkes & Dodson, 1908). The goal of stress management isn't zero stress — it's staying in your productive zone."),
    ("Recognizing Burnout Early", "Emotional Exhaustion",
     "Burnout shows up as emotional exhaustion, cynicism/detachment, and reduced sense of accomplishment. Catching it early, before it becomes chronic, makes recovery significantly faster."),
    ("Building a Sustainable Study/Work Schedule", "Time Management",
     "Workload stress often comes from underestimating task duration. A simple fix: estimate how long a task will take, then add 25-50% buffer, and block it on a calendar rather than keeping it as an open-ended to-do item."),
]


def run():
    print("Running database initialisation…")

    with db.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
    print("  ✓ Tables and indexes created (if not already present)")

    # Seed interventions — skip existing rows by name to avoid duplicates.
    for name, itype, desc, severity, rating in INTERVENTIONS:
        db.execute(
            """
            INSERT INTO interventions (intervention_name, intervention_type, description, target_severity, effectiveness_rating)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (name, itype, desc, severity, rating),
        )
    print("  ✓ Interventions seeded")

    for title, cat, content in ARTICLES:
        db.execute(
            "INSERT INTO knowledge_base (title, category, content) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (title, cat, content),
        )
    print("  ✓ Knowledge base articles seeded")

    # Admin account
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin@1234")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@stress-support.local")

    existing = db.query_one("SELECT user_id FROM users WHERE username = %s", (admin_username,))
    if not existing:
        from auth_utils import hash_password
        db.execute(
            "INSERT INTO users (username, password_hash, email, full_name, role) VALUES (%s, %s, %s, %s, 'admin')",
            (admin_username, hash_password(admin_password), admin_email, "System Administrator"),
        )
        print(f"  ✓ Admin account created: {admin_username}")
    else:
        print(f"  ✓ Admin account already exists: {admin_username}")

    print("Database initialisation complete.")


if __name__ == "__main__":
    run()

-- TalentConnect : schéma PostgreSQL (version initiale)
-- Usage : psql -U tc_user -d talentconnect -f database/schema.sql

CREATE TYPE user_role AS ENUM ('candidate', 'company', 'admin');
CREATE TYPE offer_type AS ENUM ('emploi', 'stage');
CREATE TYPE application_status AS ENUM ('recue', 'preselectionnee', 'entretien', 'acceptee', 'refusee');

CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          user_role NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE candidates (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100) DEFAULT '',
    last_name  VARCHAR(100) DEFAULT '',
    phone      VARCHAR(30)  DEFAULT '',
    education  VARCHAR(255) DEFAULT '',
    skills     TEXT DEFAULT '',
    cv_path    VARCHAR(500) DEFAULT '',
    cv_text    TEXT DEFAULT ''
);

CREATE TABLE companies (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(255) DEFAULT '',
    sector      VARCHAR(150) DEFAULT '',
    city        VARCHAR(100) DEFAULT '',
    description TEXT DEFAULT ''
);

CREATE TABLE job_offers (
    id              SERIAL PRIMARY KEY,
    company_id      INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    description     TEXT NOT NULL,
    offer_type      offer_type NOT NULL,
    required_skills TEXT DEFAULT '',
    location        VARCHAR(150) DEFAULT '',
    deadline        TIMESTAMP,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE applications (
    id           SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    offer_id     INTEGER NOT NULL REFERENCES job_offers(id) ON DELETE CASCADE,
    status       application_status NOT NULL DEFAULT 'recue',
    match_score  REAL NOT NULL DEFAULT 0,
    cover_letter TEXT DEFAULT '',
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (candidate_id, offer_id)
);

-- Tables prévues pour les semaines 9 et suivantes (gestion des stages)
CREATE TABLE internships (
    id             SERIAL PRIMARY KEY,
    application_id INTEGER NOT NULL UNIQUE REFERENCES applications(id) ON DELETE CASCADE,
    tutor_name     VARCHAR(150),
    start_date     DATE,
    end_date       DATE,
    agreement_status VARCHAR(30) NOT NULL DEFAULT 'brouillon'
);

CREATE TABLE evaluations (
    id            SERIAL PRIMARY KEY,
    internship_id INTEGER NOT NULL REFERENCES internships(id) ON DELETE CASCADE,
    author        VARCHAR(150),
    grade         NUMERIC(4,2),
    comment       TEXT,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE notifications (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message    TEXT NOT NULL,
    is_read    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_offers_active ON job_offers(is_active, created_at DESC);
CREATE INDEX idx_applications_offer ON applications(offer_id);
CREATE INDEX idx_applications_candidate ON applications(candidate_id);

CREATE TABLE favorites (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    offer_id   INTEGER NOT NULL REFERENCES job_offers(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, offer_id)
);

-- Étape 1 : cycle de vie des comptes et essai gratuit (30 connexions)
CREATE TABLE user_accounts (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    status            VARCHAR(20) NOT NULL DEFAULT 'pending',   -- pending | validated | active | rejected
    trial_logins_used INTEGER NOT NULL DEFAULT 0,
    trial_limit       INTEGER NOT NULL DEFAULT 30,
    rejection_reason  TEXT DEFAULT '',
    last_login_at     TIMESTAMP,
    last_activity_at  TIMESTAMP,
    status_changed_at TIMESTAMP DEFAULT NOW(),
    created_at        TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_trial_counter CHECK (trial_logins_used >= 0 AND trial_logins_used <= trial_limit)
);

CREATE TABLE login_history (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    logged_at  TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(64) DEFAULT '',
    user_agent VARCHAR(255) DEFAULT '',
    counted    BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_login_history_user ON login_history(user_id, logged_at DESC);

-- Étape 2 : vérification par code OTP (e-mail ou téléphone)
CREATE TABLE user_contacts (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    phone       VARCHAR(32) UNIQUE,
    channel     VARCHAR(10) NOT NULL DEFAULT 'email',   -- email | phone
    verified    BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at TIMESTAMP,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE otp_codes (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel      VARCHAR(10) NOT NULL,
    destination  VARCHAR(255) NOT NULL,
    code_hash    VARCHAR(64) NOT NULL,                  -- empreinte, jamais le code en clair
    expires_at   TIMESTAMP NOT NULL,
    attempts     INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 5,
    consumed     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_otp_user ON otp_codes(user_id, created_at DESC);

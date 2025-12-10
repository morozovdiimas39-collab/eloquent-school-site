-- V0018: Create proxies table for bot
CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.proxies (
    id SERIAL PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    username VARCHAR(255),
    password VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(host, port)
);

CREATE INDEX idx_proxies_active ON t_p86463701_eloquent_school_site.proxies(is_active);

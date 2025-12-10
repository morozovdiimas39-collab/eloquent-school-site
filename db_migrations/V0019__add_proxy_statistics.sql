-- V0019: Add proxy statistics
ALTER TABLE t_p86463701_eloquent_school_site.proxies
ADD COLUMN total_requests INTEGER DEFAULT 0,
ADD COLUMN successful_requests INTEGER DEFAULT 0,
ADD COLUMN failed_requests INTEGER DEFAULT 0,
ADD COLUMN last_used_at TIMESTAMP,
ADD COLUMN last_error TEXT,
ADD COLUMN last_error_at TIMESTAMP;

CREATE INDEX idx_proxies_stats ON t_p86463701_eloquent_school_site.proxies(total_requests, successful_requests);

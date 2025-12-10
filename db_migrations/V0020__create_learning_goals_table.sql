CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.learning_goals (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL,
    goal_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_learning_goals_student ON t_p86463701_eloquent_school_site.learning_goals(student_id);

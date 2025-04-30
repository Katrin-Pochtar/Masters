-- Create or replace view for user actions statistics
CREATE OR REPLACE VIEW user_actions_stats AS
WITH hourly_stats AS (
    SELECT 
        user_id,
        date_trunc('hour', timestamp) as hour,
        COUNT(*) as action_count,
        COUNT(CASE WHEN action LIKE 'question:%' THEN 1 END) as questions_count,
        COUNT(CASE WHEN action = 'answer' THEN 1 END) as answers_count,
        COUNT(CASE WHEN action LIKE 'error:%' THEN 1 END) as errors_count
    FROM user_actions
    GROUP BY user_id, date_trunc('hour', timestamp)
)
SELECT 
    user_id,
    hour,
    action_count,
    questions_count,
    answers_count,
    errors_count
FROM hourly_stats;

-- Create or replace view for detailed Q&A statistics
CREATE OR REPLACE VIEW detailed_qa_stats AS
WITH qa_pairs AS (
    SELECT 
        a.user_id,
        q.timestamp as question_time,
        SUBSTRING(q.action FROM 10) as question,  -- Remove 'question: ' prefix
        a.timestamp as answer_time,
        q.country,
        EXTRACT(EPOCH FROM (a.timestamp - q.timestamp)) as response_time_seconds
    FROM user_actions q
    JOIN user_actions a 
        ON q.user_id = a.user_id
        AND a.action = 'answer'
        AND a.timestamp > q.timestamp
        AND NOT EXISTS (
            SELECT 1 
            FROM user_actions qa 
            WHERE qa.user_id = q.user_id 
                AND qa.timestamp > q.timestamp 
                AND qa.timestamp < a.timestamp
        )
    WHERE q.action LIKE 'question:%'
)
SELECT 
    user_id,
    question_time,
    question,
    answer_time,
    country,
    response_time_seconds,
    date_trunc('hour', question_time) as hour,
    date_trunc('day', question_time) as day
FROM qa_pairs;

-- Create a new view for all user actions with detailed information
CREATE OR REPLACE VIEW user_actions_detailed AS
SELECT 
    ua.user_id,
    ua.timestamp as action_time,
    CASE 
        WHEN ua.action LIKE 'question:%' THEN 'question'
        WHEN ua.action = 'answer' THEN 'answer'
        WHEN ua.action = 'start' THEN 'start'
        WHEN ua.action LIKE 'error:%' THEN 'error'
        ELSE 'other'
    END as action_type,
    CASE 
        WHEN ua.action LIKE 'question:%' THEN SUBSTRING(ua.action FROM 10)
        ELSE ua.action
    END as action_content,
    ua.country,
    ui.first_seen as user_first_seen,
    ui.language_code
FROM user_actions ua
LEFT JOIN user_info ui ON ua.user_id = ui.user_id
ORDER BY ua.timestamp DESC;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_actions_timestamp ON user_actions(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON user_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_actions_action ON user_actions(action); 
-- Drop the view if it exists
DROP VIEW IF EXISTS public.user_actions_detailed;

-- Create the view
CREATE OR REPLACE VIEW public.user_actions_detailed AS
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
    ui.language_code,
    CASE
        WHEN qp.question IS NOT NULL THEN qp.question
        ELSE NULL
    END as question_text,
    CASE
        WHEN qp.answer_time IS NOT NULL THEN qp.answer_time - qp.question_time
        ELSE NULL
    END as response_time
FROM public.user_actions ua
LEFT JOIN public.user_info ui ON ua.user_id = ui.user_id
LEFT JOIN public.qa_pairs qp ON 
    ua.user_id = qp.user_id AND 
    (ua.action LIKE 'question:%' AND qp.question = SUBSTRING(ua.action FROM 10))
ORDER BY ua.timestamp DESC; 
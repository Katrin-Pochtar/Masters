-- Create user_info table
CREATE TABLE IF NOT EXISTS user_info (
    user_id INTEGER PRIMARY KEY,
    country VARCHAR(255),
    language_code VARCHAR(10),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_actions table
CREATE TABLE IF NOT EXISTS user_actions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,
    country VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES user_info(user_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_actions_timestamp ON user_actions(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON user_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_actions_action ON user_actions(action); 
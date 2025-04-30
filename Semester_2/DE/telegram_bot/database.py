from sqlalchemy import create_engine, Column, Integer, String, DateTime, text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
import time

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Enable SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "telegram_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tg_bot_secure_pass_2024")
DB_HOST = os.getenv("DB_HOST", "172.18.0.2")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "telegram_stats")

# Create database URL with additional parameters for reliability
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?connect_timeout=10&application_name=telegram_bot"

logger.info(f"Connecting to database at {DB_HOST}:{DB_PORT} as {DB_USER}")

# SQL for creating tables
INIT_TABLES_SQL = """
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
    FOREIGN KEY (user_id) REFERENCES user_info(user_id) ON DELETE CASCADE
);

-- Create qa_pairs table
CREATE TABLE IF NOT EXISTS qa_pairs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_info(user_id) ON DELETE CASCADE
);

-- Create datalens_analytics table
CREATE TABLE IF NOT EXISTS datalens_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type VARCHAR(50),  -- 'question', 'answer', 'start', 'error'
    content TEXT,            -- question text or error message
    response_time_seconds NUMERIC,  -- time between question and answer
    language_code VARCHAR(10),
    country VARCHAR(255),
    first_seen TIMESTAMP,
    session_id UUID,         -- to group related actions
    is_successful BOOLEAN    -- whether the interaction was successful
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_actions_timestamp ON user_actions(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON user_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_actions_action ON user_actions(action);
CREATE INDEX IF NOT EXISTS idx_qa_pairs_user_id ON qa_pairs(user_id);
CREATE INDEX IF NOT EXISTS idx_qa_pairs_timestamp ON qa_pairs(timestamp);
CREATE INDEX IF NOT EXISTS idx_datalens_timestamp ON datalens_analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_datalens_user_id ON datalens_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_datalens_action_type ON datalens_analytics(action_type);
"""

# SQL for creating views
INIT_VIEWS_SQL = """
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

-- Create view for all user actions with detailed information
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
"""

def create_db_engine(max_retries=5, retry_interval=5):
    """Create database engine with retry logic."""
    for attempt in range(max_retries):
        try:
            # Create engine with connection pooling and timeout settings
            engine = create_engine(
                DATABASE_URL,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,  # Enable connection health checks
                connect_args={
                    'connect_timeout': 10,
                    'application_name': 'telegram_bot'  # For better monitoring
                }
            )
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to the database")
            return engine
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
                raise

# Create engine with retry logic
engine = create_db_engine()

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

class UserInfo(Base):
    __tablename__ = "user_info"

    user_id = Column(Integer, primary_key=True, index=True)
    country = Column(String)
    language_code = Column(String)
    first_seen = Column(DateTime, default=datetime.utcnow)
    actions = relationship("UserAction", back_populates="user", cascade="all, delete-orphan")
    qa_pairs = relationship("QAPair", back_populates="user", cascade="all, delete-orphan")

class UserAction(Base):
    __tablename__ = "user_actions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user_info.user_id', ondelete='CASCADE'), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String)
    country = Column(String)
    user = relationship("UserInfo", back_populates="actions")

class QAPair(Base):
    __tablename__ = "qa_pairs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user_info.user_id', ondelete='CASCADE'), index=True)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("UserInfo", back_populates="qa_pairs")

def init_db():
    """Initialize database tables and views."""
    try:
        logger.info("Initializing database...")
        # Create engine with retry logic
        engine = create_db_engine()
        logger.info("Database engine created successfully")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create views and enable UUID extension
        with engine.connect() as conn:
            logger.info("Enabling UUID extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
            logger.info("UUID extension enabled")
            
            logger.info("Creating tables...")
            conn.execute(text(INIT_TABLES_SQL))
            logger.info("Tables created successfully")
            
            logger.info("Creating views...")
            conn.execute(text(INIT_VIEWS_SQL))
            logger.info("Views created successfully")
            
            conn.commit()
        logger.info("Database initialization completed successfully")
        
        # Update DataLens analytics
        update_datalens_analytics()
        logger.info("DataLens analytics updated")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise

def log_user_info(user_id: int, country: str = None, language_code: str = None):
    """Log user information to database."""
    try:
        logger.info(f"Logging user info for user {user_id}")
        db = SessionLocal()
        try:
            logger.info(f"Checking if user {user_id} exists")
            user = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
            if user:
                logger.info(f"Updating existing user {user_id}")
                if country:
                    user.country = country
                if language_code:
                    user.language_code = language_code
            else:
                logger.info(f"Creating new user {user_id}")
                user = UserInfo(
                    user_id=user_id,
                    country=country,
                    language_code=language_code
                )
                db.add(user)
            db.commit()
            logger.info(f"Successfully logged user info for {user_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error logging user info: {str(e)}", exc_info=True)
            raise
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}", exc_info=True)
        raise

def get_user_country(user_id: int) -> str:
    """Get user's country if available."""
    db = None
    try:
        db = SessionLocal()
        user_info = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
        return user_info.country if user_info else None
    except Exception as e:
        logger.error(f"Error getting user country: {str(e)}")
        return None
    finally:
        if db:
            db.close()

def log_user_action(user_id: int, action: str):
    """Log user action to database."""
    try:
        logger.info(f"Logging action for user {user_id}: {action}")
        db = SessionLocal()
        try:
            # Ensure user exists
            user = db.query(UserInfo).filter(UserInfo.user_id == user_id).first()
            if not user:
                logger.info(f"Creating new user {user_id} for action logging")
                user = UserInfo(user_id=user_id)
                db.add(user)
                db.commit()
                logger.info(f"Created new user {user_id}")
            
            # Log action
            action_record = UserAction(
                user_id=user_id,
                action=action
            )
            db.add(action_record)
            db.commit()
            logger.info(f"Successfully logged action for user {user_id}: {action}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error logging user action: {str(e)}", exc_info=True)
            raise
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}", exc_info=True)
        raise

def get_user_statistics(user_id: int = None):
    """Get statistics for a specific user or all users."""
    db = None
    try:
        db = SessionLocal()
        query = db.query(UserAction)
        if user_id:
            query = query.filter(UserAction.user_id == user_id)
        return query.all()
    except Exception as e:
        logger.error(f"Error getting user statistics: {str(e)}")
        return []
    finally:
        if db:
            db.close()

# Function to populate DataLens analytics table
def update_datalens_analytics():
    """Update DataLens analytics table with latest data."""
    logger.info("Starting update_datalens_analytics...")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get the latest data from user_actions and user_info
                logger.info("Executing analytics update query...")
                cur.execute("""
                    WITH latest_data AS (
                        SELECT 
                            ua.user_id,
                            ua.timestamp,
                            ua.action_type,
                            ua.content,
                            ua.response_time_seconds,
                            ui.language_code,
                            ui.country,
                            ui.first_seen,
                            ua.session_id,
                            CASE 
                                WHEN ua.response_time_seconds < 5 THEN true
                                ELSE false
                            END as is_successful
                        FROM user_actions ua
                        LEFT JOIN user_info ui ON ua.user_id = ui.user_id
                        WHERE ua.timestamp > NOW() - INTERVAL '24 hours'
                    )
                    INSERT INTO datalens_analytics (
                        user_id, timestamp, action_type, content, 
                        response_time_seconds, language_code, country,
                        first_seen, session_id, is_successful
                    )
                    SELECT * FROM latest_data
                    ON CONFLICT (user_id, timestamp, action_type) 
                    DO UPDATE SET
                        content = EXCLUDED.content,
                        response_time_seconds = EXCLUDED.response_time_seconds,
                        language_code = EXCLUDED.language_code,
                        country = EXCLUDED.country,
                        first_seen = EXCLUDED.first_seen,
                        session_id = EXCLUDED.session_id,
                        is_successful = EXCLUDED.is_successful
                """)
                rows_affected = cur.rowcount
                logger.info(f"Analytics update completed. Rows affected: {rows_affected}")
                conn.commit()
    except Exception as e:
        logger.error(f"Error updating datalens_analytics: {str(e)}", exc_info=True)
        raise 
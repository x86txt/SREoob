import aiosqlite
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from .config import settings

DATABASE_PATH = settings.DATABASE_PATH

async def init_database():
    """Initialize the SQLite database and create tables if they don't exist."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                scan_interval TEXT DEFAULT '60s',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if scan_interval column exists and add it if not (for migration)
        cursor = await db.execute("PRAGMA table_info(sites)")
        columns = await cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'scan_interval' not in column_names:
            await db.execute("ALTER TABLE sites ADD COLUMN scan_interval TEXT DEFAULT '60s'")
            print("Added scan_interval column to existing sites table")
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS site_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER NOT NULL,
                status TEXT NOT NULL,  -- 'up' or 'down'
                response_time REAL,    -- in seconds
                status_code INTEGER,
                error_message TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites (id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                api_key_hash TEXT UNIQUE NOT NULL,
                description TEXT,
                last_seen TIMESTAMP,
                status TEXT DEFAULT 'offline',  -- 'online', 'offline'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()

async def add_site(url: str, name: str, scan_interval: str = "60s") -> int:
    """Add a new site to monitor."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO sites (url, name, scan_interval) VALUES (?, ?, ?)",
            (url, name, scan_interval)
        )
        await db.commit()
        return cursor.lastrowid

async def get_sites() -> List[Dict[str, Any]]:
    """Get all sites being monitored."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM sites ORDER BY name")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def record_check(site_id: int, status: str, response_time: float = None, 
                      status_code: int = None, error_message: str = None):
    """Record a site check result."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO site_checks (site_id, status, response_time, status_code, error_message)
            VALUES (?, ?, ?, ?, ?)
        """, (site_id, status, response_time, status_code, error_message))
        await db.commit()

async def get_site_status() -> List[Dict[str, Any]]:
    """Get current status of all sites with latest check information."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT 
                s.id,
                s.url,
                s.name,
                s.scan_interval,
                s.created_at,
                sc.status,
                sc.response_time,
                sc.status_code,
                sc.error_message,
                sc.checked_at,
                (SELECT COUNT(*) FROM site_checks WHERE site_id = s.id AND status = 'up') as total_up,
                (SELECT COUNT(*) FROM site_checks WHERE site_id = s.id AND status = 'down') as total_down
            FROM sites s
            LEFT JOIN site_checks sc ON s.id = sc.site_id
            WHERE sc.checked_at = (
                SELECT MAX(checked_at) 
                FROM site_checks 
                WHERE site_id = s.id
            ) OR sc.checked_at IS NULL
            ORDER BY s.name
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_site_history(site_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Get check history for a specific site."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM site_checks 
            WHERE site_id = ? 
            ORDER BY checked_at DESC 
            LIMIT ?
        """, (site_id, limit))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def delete_site(site_id: int):
    """Delete a site and all its check history."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM site_checks WHERE site_id = ?", (site_id,))
        await db.execute("DELETE FROM sites WHERE id = ?", (site_id,))
        await db.commit()

async def add_agent(name: str, api_key_hash: str, description: str = None) -> int:
    """Add a new agent to the database."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO agents (name, api_key_hash, description) VALUES (?, ?, ?)",
            (name, api_key_hash, description)
        )
        await db.commit()
        return cursor.lastrowid

async def get_agents() -> List[Dict[str, Any]]:
    """Get all registered agents."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM agents ORDER BY name")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_agent_by_hash(api_key_hash: str) -> Dict[str, Any]:
    """Get agent by API key hash."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM agents WHERE api_key_hash = ?", (api_key_hash,))
        row = await cursor.fetchone()
        return dict(row) if row else None

async def update_agent_status(api_key_hash: str, status: str):
    """Update agent status and last seen timestamp."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE agents 
            SET status = ?, last_seen = CURRENT_TIMESTAMP 
            WHERE api_key_hash = ?
        """, (status, api_key_hash))
        await db.commit()

async def delete_agent(agent_id: int):
    """Delete an agent."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        await db.commit() 
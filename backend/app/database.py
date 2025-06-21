import aiosqlite
import asyncio
from typing import List, Dict, Any
from datetime import datetime

DATABASE_PATH = "siteup.db"

async def init_database():
    """Initialize the SQLite database and create tables if they don't exist."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
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
        
        await db.commit()

async def add_site(url: str, name: str) -> int:
    """Add a new site to monitor."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO sites (url, name) VALUES (?, ?)",
            (url, name)
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
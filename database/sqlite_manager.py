import os
import sqlite3
from config.settings import DB_NAME

def initialize_db():
    """
    SQLiteデータベースを初期化（必要なら作成）。
    """
    # ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # テーブル作成（存在しない場合のみ）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS youtube_archives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,  -- 重複を防ぐためUNIQUE制約
            title TEXT,
            published_at TEXT,
            retrieved_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_videos_to_db(videos):
    """
    取得した動画データをSQLiteに保存する（重複をスキップ）。
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for video in videos:
        try:
            cursor.execute("""
                INSERT INTO youtube_archives (url, title, published_at)
                VALUES (?, ?, ?)
            """, (video['url'], video['title'], video['published_at']))
        except sqlite3.IntegrityError:
            # 重複をスキップ
            pass
    conn.commit()
    conn.close()

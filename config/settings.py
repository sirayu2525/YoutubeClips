import os
from dotenv import load_dotenv

# .envファイルから設定を読み込む
load_dotenv()

API_KEY = os.getenv("API_KEY")  # YouTube APIのAPIキー
CHANNEL_ID = os.getenv("CHANNEL_ID")  # 対象のチャンネルID
DB_NAME = os.getenv("DB_NAME", "data/youtube_data.db")  # SQLiteデータベース名（デフォルト値を追加）

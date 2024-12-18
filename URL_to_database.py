import googleapiclient.discovery
import googleapiclient.errors
import sqlite3
import os
from dotenv import load_dotenv

# 環境変数をロード
load_dotenv(override=True)

# APIキーとチャンネルIDを設定
API_KEY = os.getenv("API_KEY").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID").strip()

def get_video_urls(api_key, channel_id):
    """
    指定されたチャンネルの動画URLを取得します。

    Args:
        api_key (str): YouTube Data APIキー。
        channel_id (str): チャンネルID。

    Returns:
        list: 動画URLのリスト。取得できなかった場合は空リスト。
    """
    try:
        # YouTube Data APIクライアントを作成
        youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)

        # チャンネルのアップロード動画リストを取得するプレイリストID
        request = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        )
        response = request.execute()

        if 'items' not in response:
            print("Error: 'items' not found in response")
            print(response)
            return []

        uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        video_urls = []
        next_page_token = None

        while True:
            request = youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            for item in response['items']:
                video_id = item['snippet']['resourceId']['videoId']
                video_urls.append(f"https://www.youtube.com/watch?v={video_id}")

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        return video_urls

    except googleapiclient.errors.HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")
        return []

def save_urls_to_sqlite(video_urls, db_name='data/youtube_data.db'):
    """
    動画URLをSQLiteデータベースに保存します。

    Args:
        video_urls (list): 保存する動画URLのリスト。
        db_name (str): SQLiteデータベースのファイル名。
    """
    # ディレクトリが存在しない場合は作成
    if db_name:
        os.makedirs(os.path.dirname(db_name), exist_ok=True)

    # SQLiteデータベースに接続（存在しない場合は作成）
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # テーブルが存在しない場合は作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE
        )
    ''')

    # 各URLをデータベースに挿入
    for url in video_urls:
        try:
            cursor.execute('INSERT INTO videos (url) VALUES (?)', (url,))
        except sqlite3.IntegrityError:
            # URLがすでに存在する場合はエラーになり、その場合は無視
            print(f'URL already exists in database: {url}')

    # 変更を保存して接続を閉じる
    conn.commit()
    conn.close()

def display_database_contents(db_name='data/youtube_data.db'):
    """
    SQLiteデータベースの内容を表示します。

    Args:
        db_name (str): SQLiteデータベースのファイル名。
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # テーブルが存在するか確認
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:", tables)

    # テーブルの中身を表示
    cursor.execute("SELECT * FROM videos")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    conn.close()

if __name__ == "__main__":
    video_urls = get_video_urls(API_KEY, CHANNEL_ID)
    if video_urls:
        save_urls_to_sqlite(video_urls)
        print('動画URLをSQLiteデータベースに保存しました。')

        # データベースの中身を表示
        print('データベースの中身:')
        display_database_contents()
    else:
        print('動画URLの取得に失敗しました。')

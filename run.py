from youtube_api.fetch_videos import fetch_channel_videos
from database.sqlite_manager import initialize_db, save_videos_to_db
from config.settings import API_KEY, CHANNEL_ID

def main():
    """
    メイン処理：YouTube APIで動画取得 → SQLiteに保存。
    """
    initialize_db()

    print(f"Fetching videos from channel: {CHANNEL_ID}")
    page_token = None
    while True:
        # YouTube APIで動画リストを取得
        videos, next_page_token = fetch_channel_videos(API_KEY, CHANNEL_ID, page_token)
        print(f"Fetched {len(videos)} videos.")

        # SQLiteに保存
        save_videos_to_db(videos)

        # 次ページがない場合、終了
        if not next_page_token:
            break

        # トークンを次のリクエストに設定
        page_token = next_page_token

if __name__ == '__main__':
    main()

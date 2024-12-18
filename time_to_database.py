from chat_downloader import ChatDownloader  # ライブラリhttps://chat-downloader.readthedocs.io/en/latest/index.htmlより
import os
import sys
import sqlite3
from dotenv import load_dotenv
from youtube_api import get_video_length  # 動画の長さを取得する関数をインポート
from chat_downloader.errors import NoChatReplay

load_dotenv(override=True)

keywords = os.getenv("KEYWORD")  # 環境変数からキーワードを取得

if keywords is None:
    raise ValueError("KEYWORD is not set in the .env file")

keywords = keywords.split(",")  # カンマで分割してリストに変換

def seconds_to_hms(seconds):
    """
    秒数を時:分:秒の形式に変換します。

    Args:
        seconds (int): 秒数。

    Returns:
        str: 時:分:秒の形式の文字列。
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours}時間{minutes}分{seconds}秒"

class FunctionUtils:
    @staticmethod
    def nested_item_value(parrent_object, nest_list):  # 複雑なネスト構造の中からほしいものを取り出すメソッド
        """
        複雑なネスト構造の中から指定されたキーの値を取り出します。

        Args:
            parrent_object (dict or list): 親オブジェクト。
            nest_list (list): ネストされたキーのリスト。

        Returns:
            any: 取り出された値。存在しない場合はNone。
        """
        if not nest_list:  # 単に空かどうかをTrue Falseで見分けられる。
            return parrent_object
        result = ""
        for nest_key in nest_list:
            object_type = type(parrent_object)
            if object_type is not dict and object_type is not list:
                result = None
                break
            elif object_type is list:
                if type(nest_key) is not int:
                    result = None
                    break
                result = parrent_object[nest_key] if nest_key < len(parrent_object) else None
            else:
                result = parrent_object.get(nest_key, None)
            parrent_object = result
        return result
    

def get_video_urls_from_db(start, end, db_name='data/youtube_data.db'):
    """
    SQLiteデータベースから指定された範囲の動画URLを取得します。

    Args:
        start (int): 開始インデックス。
        end (int): 終了インデックス。
        db_name (str): SQLiteデータベースのファイル名。

    Returns:
        list: 動画IDとURLのタプルのリスト。
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 特定の範囲のデータを取得
    cursor.execute("SELECT id, url FROM videos LIMIT ? OFFSET ?", (end - start, start))
    rows = cursor.fetchall()

    video_data = [(row[0], row[1]) for row in rows]

    conn.close()
    return video_data

def update_top_10_times_in_db(video_id, top_10_times, max_message_count, checked, db_name='data/youtube_data.db'):
    """
    上位10個の時間とチェックボックスの状態をSQLiteデータベースに更新します。

    Args:
        video_id (int): 動画ID。
        top_10_times (list): 上位10個の時間のリスト。
        max_message_count (int): 一番多いメッセージ数。
        checked (bool): チェックボックスの状態。
        db_name (str): SQLiteデータベースのファイル名。
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # `top10`列、`max_message_count`列、`checked`列が存在しない場合は追加
    cursor.execute("PRAGMA table_info(videos)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'top10' not in columns:
        cursor.execute("ALTER TABLE videos ADD COLUMN top10 TEXT")
    if 'max_message_count' not in columns:
        cursor.execute("ALTER TABLE videos ADD COLUMN max_message_count INTEGER")
    if 'checked' not in columns:
        cursor.execute("ALTER TABLE videos ADD COLUMN checked BOOLEAN")

    # 上位10個の時間、一番多いメッセージ数、チェックボックスの状態をデータベースに更新
    top_10_times_str = ','.join(top_10_times)
    cursor.execute("UPDATE videos SET top10 = ?, max_message_count = ?, checked = ? WHERE id = ?", (top_10_times_str, max_message_count, int(checked), video_id))

    # 変更を保存して接続を閉じる
    conn.commit()
    conn.close()

def chat_count(chat_time, interval=20):
    """
    チャットメッセージの時間を指定された間隔でカウントします。

    Args:
        chat_time (list): チャットメッセージの時間のリスト。
        interval (int): カウント間隔（秒単位）。

    Returns:
        list: 各間隔ごとのメッセージ数のリスト。
    """
    max_time = max(chat_time) if chat_time else 0
    bins = [0] * ((max_time // interval) + 1)
    for time in chat_time:
        bins[time // interval] += 1
    return bins

def process_video_url(video_id, url):
    """
    指定された動画URLのチャットデータを処理し、上位10個の時間をデータベースに保存します。

    Args:
        video_id (int): 動画ID。
        url (str): 動画URL。
    """
    if not url:
        print(f"Skipping video ID {video_id} because URL is None")
        return
    
    fu = FunctionUtils()
    chat_time = []
    chat_mess = []

    # 動画の長さを取得
    video_length = get_video_length(url)
    if video_length is None:
        raise ValueError("Failed to retrieve video length")

    try:
        # URLからchatを読み込み
        start = '0:00'  # 読み込みを開始する秒数
        end = video_length  # 読み込みを終了する秒数
        chat = ChatDownloader().get_chat(url, start_time=start, end_time=end)

        for message in chat:
            time_in_seconds = round(fu.nested_item_value(message, ["time_in_seconds"]))
            text = fu.nested_item_value(message, ["message"])
            if text and any(keyword in text for keyword in keywords):
                chat_time.append(time_in_seconds)
                chat_mess.append(text)

        message_count = chat_count(chat_time, interval=20)  # 20秒間隔でカウント

        # メッセージカウントをソート
        sorted_indices = sorted(range(len(message_count)), key=lambda i: message_count[i], reverse=True)
        sorted_times = [i * 20 for i in sorted_indices]
        sorted_counts = [message_count[i] for i in sorted_indices]

        # 上位10個のxの値を表示
        top_10_times = sorted_times[:10]
        top_10_times_hms = [seconds_to_hms(time) for time in top_10_times]
        print("Top 10 times with highest message counts:", top_10_times_hms)

        # 一番多いメッセージ数を取得
        max_message_count = max(message_count) if message_count else 0


        # 上位10個の時間と一番多いメッセージ数、チェックボックスの状態をデータベースに保存
        update_top_10_times_in_db(video_id, top_10_times_hms, max_message_count, False)

    except NoChatReplay:
        print(f"No chat replay available for video: {url}")
        update_top_10_times_in_db(video_id, ["No chat replay"], 0, False)

def main():
    """
    メイン関数。コマンドライン引数から開始インデックスと終了インデックスを取得し、
    指定された範囲の動画URLを処理します。
    """
    if len(sys.argv) < 3:
        raise ValueError("Start and end indices are not provided")
    start_index = int(sys.argv[1])
    end_index = int(sys.argv[2])

    video_data = get_video_urls_from_db(start_index, end_index)
    for video_id, url in video_data:
        process_video_url(video_id, url)
        print(f"Processed video ID: {video_id}")

if __name__ == '__main__':
    main()
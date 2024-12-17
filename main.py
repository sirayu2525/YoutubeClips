from chat_downloader import ChatDownloader # ライブラリhttps://chat-downloader.readthedocs.io/en/latest/index.htmlより
import os
import sys
from dotenv import load_dotenv
#rom function_utils import FunctionUtils
from youtube_api import get_video_length  # 動画の長さを取得する関数をインポート


load_dotenv(override=True)

keywords = os.getenv("KEYWORD")  # 環境変数からキーワードを取得

if keywords is None:
    raise ValueError("KEYWORD is not set in the .env file")

keywords = keywords.split(",")  # カンマで分割してリストに変換

def seconds_to_hms(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours}時間{minutes}分{seconds}秒"

class FunctionUtils:
    @staticmethod
    def nested_item_value(parrent_object, nest_list): #複雑なネスト構造の中からほしいものを取り出すメソッド
        """ return nested data """
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
            if result is None:
                break
            parrent_object = result
        return result

def chat_count(lists, interval=20):
    # 20秒ごとにカウントする
    max_time = max(lists) if lists else 0
    counts = [0] * ((max_time // interval) + 1)
    
    for time in lists:
        index = time // interval
        counts[index] += 1
    
    return counts

def main():
    fu = FunctionUtils()
    chat_time = []
    chat_mess = []

    # コマンドライン引数からURLを取得
    if len(sys.argv) < 2:
        raise ValueError("URL is not provided")
    url = sys.argv[1]

    # 動画の長さを取得
    video_length = get_video_length(url)
    if video_length is None:
        raise ValueError("Failed to retrieve video length")

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


if __name__ == '__main__':
    main()

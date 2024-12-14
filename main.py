from chat_downloader import ChatDownloader # ライブラリhttps://chat-downloader.readthedocs.io/en/latest/index.htmlより
from matplotlib import pyplot as plt # データをプロットしてグラフを描くライブラリ
import os
from dotenv import load_dotenv

load_dotenv()

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

def chat_count(lists, interval=10):
    # 10秒ごとにカウントする
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

    def motion(event):
        x = event.xdata
        try:
            ln_v.set_xdata(round(x))
        except TypeError:
            pass
        plt.draw()

    def onclick(event):
        x = round(event.xdata)
        print(f'event.xdata={x}')
        if x < len(message_count):
            print(f'message_count={message_count[x]}')

    # URLからchatを読み込み
    url = 'https://www.youtube.com/watch?v=i7pnUeBY8d0'  # ここにYouTubeのURLを書き込む
    start = '0:00'  # ここに読み込みを開始する秒数を書き込む（例：0:00）
    end = '50:00'  # ここに読み込みを終了する秒数を書き込む（例：0:10）
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

    fig = plt.figure()
    plt.plot([i * 20 for i in range(len(message_count))], message_count, "o-", picker=1, color="blue")  # X軸を20秒間隔に調整
    ln_v = plt.axvline(0)

    plt.connect('motion_notify_event', motion)
    fig.canvas.mpl_connect('button_press_event', onclick)

    # グラフの可読性を向上
    plt.title("Message Count Over Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Message Count")
    plt.grid(True)
    plt.xticks(range(0, max(sorted_times) + 20, 20))  # X軸の目盛りを20秒間隔に設定
    plt.show()

if __name__ == '__main__':
    main()

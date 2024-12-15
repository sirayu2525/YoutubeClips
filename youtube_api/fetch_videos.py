from googleapiclient.discovery import build

def fetch_channel_videos(api_key, channel_id, page_token=None):
    """
    YouTube APIを使って指定チャンネルの動画リストを取得する。
    """
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.search().list(
        channelId=channel_id,
        part="snippet",
        maxResults=50,  # API制限により1リクエスト最大50件
        pageToken=page_token,
        type="video",  # 動画のみ取得
        order="date"  # 新しい順に取得
    )
    response = request.execute()

    videos = []
    for item in response['items']:
        if item['id']['kind'] == 'youtube#video':
            video_id = item['id']['videoId']
            videos.append({
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": item['snippet']['title'],
                "published_at": item['snippet']['publishedAt']
            })

    return videos, response.get('nextPageToken')

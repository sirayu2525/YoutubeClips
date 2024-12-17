import googleapiclient.discovery
import googleapiclient.errors
import re
import os
from dotenv import load_dotenv

load_dotenv(override=True)

API_KEY = os.getenv("API_KEY")

def get_video_length(url):
    try:
        video_id = re.search(r'v=([^&]+)', url).group(1)
        youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=API_KEY)
        request = youtube.videos().list(part='contentDetails', id=video_id)
        response = request.execute()
        if 'items' not in response or len(response['items']) == 0:
            return None
        duration = response['items'][0]['contentDetails']['duration']
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return None
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds
    except googleapiclient.errors.HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")
        return None
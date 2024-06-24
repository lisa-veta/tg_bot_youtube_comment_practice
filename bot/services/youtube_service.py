#Сервис для работы с API YouTube
from googleapiclient.discovery import build
import requests
from sqlalchemy import null


class YoutubeParser:
    def __init__(self):
        self.YT_api_key = 'AIzaSyCGros2SeZwb4utjrTfL2Hcbuc2kx4FxJI'
        self.SA_api_key = 'fWG6yD8V8C9aUjJaXrpGnT5b'
        self.comments = []

    #def get_gen_inf(self, video_id):
    def get_video_comments(self, video_id):
        youtube = build('youtube', 'v3', developerKey=self.YT_api_key)
        video_response = youtube.commentThreads().list(
            part='snippet,replies',
            videoId=video_id
        ).execute()

        while video_response:
            for item in video_response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                self.comments.append('"' + comment + '"')

                replycount = item['snippet']['totalReplyCount']
                if replycount > 0:
                    self.comments.append("ответы на комментарий: [ ")
                    for reply in item['replies']['comments']:
                        reply = reply['snippet']['textDisplay']
                        self.comments.append('"' + reply + '"')
                    self.comments.append(" ]")

            if 'nextPageToken' in video_response:
                video_response = youtube.commentThreads().list(
                    part='snippet,replies',
                    videoId=video_id,
                    pageToken=video_response['nextPageToken']
                ).execute()
            else:
                break
        return self.comments

    def get_subtitles(self, video_id):
        url = "https://www.searchapi.io/api/v1/search"
        params = {
            "api_key": self.SA_api_key,
            "engine": "youtube_transcripts",
            "video_id": video_id,
            "lang": "ru"  # проблема если субтитры на английском вернет ошибку
        }
        response = requests.get(url, params=params)
        data = response.json()
        if "transcripts" in data:
            return [item["text"] for item in data.get("transcripts", []) if "text" in item]
        else:
            return null



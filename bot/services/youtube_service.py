#Сервис для работы с API YouTube
import asyncio
from googleapiclient.discovery import build
import requests
import aiohttp
import re
class YoutubeParser:
    def __init__(self):
        self.YT_api_key = 'AIzaSyCGros2SeZwb4utjrTfL2Hcbuc2kx4FxJI'
        self.SA_api_key = 'fWG6yD8V8C9aUjJaXrpGnT5b'

    async def get_general_inf(self, video_url):
        video_id = self.get_video_code(video_url)
        url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet&id={video_id}&key={self.YT_api_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    stats = data['items'][0]['statistics']
                    del stats['favoriteCount']
                    if int(stats['commentCount']) > 50000:
                        comments = 50000
                    else:
                        comments = stats['commentCount']
                    snippet = data['items'][0]['snippet']
                    title = snippet['title']
                    published_at = snippet['publishedAt']
                    return {
                        'title': title,
                        'published_at': published_at,
                        'viewCount': stats['viewCount'],
                        'likeCount': stats['likeCount'],
                        'commentCount': comments
                    }
                else:
                    print(f"Ошибка: {response.status} - {await response.text()}")
                    return None

    async def get_comment_count(self, video_url):
        video_id = self.get_video_code(video_url)
        general_info = await self.get_general_inf(video_id)
        if general_info:
            return general_info['commentCount']
        else:
            return None

    async def get_video_comments(self, video_url) -> (list, int):
        video_id = self.get_video_code(video_url)
        comments = []
        youtube = build('youtube', 'v3', developerKey=self.YT_api_key)
        video_response = youtube.commentThreads().list(
            part='snippet,replies',
            videoId=video_id
        ).execute()
        comment_count = 0
        while video_response:
            for item in video_response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                repl = ""
                comment_count += 1
                replycount = item['snippet']['totalReplyCount']
                if replycount > 0:
                    repl = " ответы на комментарий: [ "
                    for reply in item['replies']['comments']:
                        repl += reply['snippet']['textDisplay']
                    repl += " ]"
                comments.append(comment + repl)
                print(comment)

            if 'nextPageToken' in video_response and comment_count < 50000:
                video_response = youtube.commentThreads().list(
                    part='snippet,replies',
                    videoId=video_id,
                    pageToken=video_response['nextPageToken']
                ).execute()
            else:
                break
        return comments, comment_count

        #comment_count = self.get_comment_count(video_id)
        # if comment_count:
        #     comments.append("Количество всех комментариев: " + str(comment_count))
        # i = 1
        # for comment in comments:
        #     print(f"{i}) {comment}")
        #     i += 1

    async def get_subtitles(self, video_url):
        video_id = self.get_video_code(video_url)
        url = "https://www.searchapi.io/api/v1/search"
        params = {
            "api_key": self.SA_api_key,
            "engine": "youtube_transcripts",
            "video_id": video_id,
            "lang": "ru"  # проблема если субтитры на английском вернет ошибку
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                if "transcripts" in data:
                    return [item["text"] for item in data.get("transcripts", []) if "text" in item]
                else:
                    return None

    def get_video_code(self, video_url):
        match = re.search(r'v=([^&]+)', video_url)
        if match:
            return match.group(1)
        else:
            match = re.search(r'youtu\.be/([^?]+)', video_url)
            if match:
                return match.group(1)
        return None

# if __name__ == "__main__":
#        asyncio.run(main())
#     async def main():
#         #json = youtube_parser.get_general_inf("https://www.youtube.com/watch?v=GjkuE3Q18TQ&t=1s")
#         # code = youtube_parser.get_video_code("https://www.youtube.com/watch?v=UCScWmyD3Mg")
#         comments = youtube_parser.get_video_comments("https://www.youtube.com/watch?v=Jp4SB_lOu8E")
#         for comment in comments:
#             print(comment)

if __name__ == "__main__":
    async def main():
        you_t = YoutubeParser()
        comments = await you_t.get_video_comments("https://www.youtube.com/watch?v=Jp4SB_lOu8E")
    asyncio.run(main())
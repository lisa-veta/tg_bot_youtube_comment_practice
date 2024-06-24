#Модуль для анализа тональности комментариев
import ollama
import re
from youtube_service import YoutubeParser
class OllamaChat:
    parser = YoutubeParser()
    def __init__(self, model_name='llama3'):
        self.model_name = model_name
    def get_characteristics(self, url) -> str:
        match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
        if match:
            url = match.group(1)
        #else
        comments = self.parser.get_video_comments(url)
        with open("q_characteristics.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()

        prompt = "\n".join(comments) + "\n" + base_prompt

        stream = ollama.chat(model=self.model_name,
                             messages=[{'role': 'user', 'content': prompt}],
                             stream=True)

        response_parts = []
        for chunk in stream:
            response_parts.append(chunk['message']['content'])

        response_text = "".join(response_parts)
        json_start = response_text.find("[")
        json_end = response_text.find("]")
        if json_start != -1 and json_end != -1:
            return response_text[json_start:json_end + 1]
        else:
            return response_text

    def get_sentiment(self, url) -> str:
        match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
        if match:
            url = match.group(1)
        #else
        comments = self.parser.get_video_comments(url)
        with open("q_tonality.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()

        prompt = "\n".join(comments) + "\n" + base_prompt

        stream = ollama.chat(model=self.model_name,
                             messages=[{'role': 'user', 'content': prompt}],
                             stream=True)

        response_parts = []
        for chunk in stream:
            response_parts.append(chunk['message']['content'])

        response_text = "".join(response_parts)
        json_start = response_text.find("[")
        json_end = response_text.find("]")
        if json_start != -1 and json_end != -1:
            return response_text[json_start:json_end + 1]
        else:
            return response_text

    def get_summary(self, url) -> str:
        match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
        if match:
            url = match.group(1)
        #else
        comments = self.parser.get_subtitles(url)
        with open("q_summary.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()

        prompt = "\n".join(comments) + "\n" + base_prompt

        stream = ollama.chat(model=self.model_name,
                             messages=[{'role': 'user', 'content': prompt}],
                             stream=True)

        response_parts = []
        for chunk in stream:
            response_parts.append(chunk['message']['content'])

        response_text = "".join(response_parts)
        return response_text



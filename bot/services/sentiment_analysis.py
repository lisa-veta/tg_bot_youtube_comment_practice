#Модуль для анализа тональности комментариев
import ollama
import re

from youtube_service import YoutubeParser

class OllamaChat:
    parser = YoutubeParser()

    def __init__(self, model_name='llama3'):
        self.model_name = model_name

    def get_characteristics(self, url) -> str:
        url = self.get_video_code(url)

        comments = self.parser.get_video_comments(url)
        with open("q_characteristics.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()

        prompt = "\n".join(comments) + "\n" + base_prompt

        response_text = self.get_response_from_model(prompt)
        json_start = response_text.find("[")
        json_end = response_text.find("]")
        if json_start != -1 and json_end != -1:
            return response_text[json_start:json_end + 1]
        else:
            return response_text

    def get_tonality(self, url) -> str:
        url = self.get_video_code(url)

        comments = self.parser.get_video_comments(url)
        with open("q_tonality.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()

        prompt = "\n".join(comments) + "\n" + base_prompt

        response_text = self.get_response_from_model(prompt)
        json_start = response_text.find("{")
        json_end = response_text.find("}")
        if json_start != -1 and json_end != -1:
            return response_text[json_start:json_end + 1]
        else:
            return response_text

    def get_summary(self, url) -> str:
        url = self.get_video_code(url)

        subtitles = self.parser.get_subtitles(url)
        if subtitles is None:
            return None
        with open("q_summary.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()

        prompt = "\n".join(subtitles) + "\n" + base_prompt
        response_text = self.get_response_from_model(prompt)
        return response_text

    def get_group_name(self, characteristics) -> str:
        with open("q_group_name.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()

        prompt = base_prompt + "\n".join(characteristics) + "\n"
        response_text = self.get_response_from_model(prompt)
        json_start = response_text.find("{")
        json_end = response_text.find("}")
        if json_start != -1 and json_end != -1:
            return response_text[json_start:json_end + 1]
        else:
            return response_text

    def get_video_code(self, url) -> str:
        match = re.search(r'v=([^&]+)', url)
        if match:
            return match.group(1)
        #else:

    def get_response_from_model(self, prompt: str) -> str:
        stream = ollama.chat(model=self.model_name,
                             messages=[{'role': 'user', 'content': prompt}],
                             stream=True)
        response_parts = []
        for chunk in stream:
            response_parts.append(chunk['message']['content'])

        response_text = "".join(response_parts)
        return response_text

if __name__ == '__main__':
    video_url = "https://www.youtube.com/watch?v=-yn0b8Dz69E"
    chat = OllamaChat()
    response = chat.get_tonality(video_url)
    print(response)




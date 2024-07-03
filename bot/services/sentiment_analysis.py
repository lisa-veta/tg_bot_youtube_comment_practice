#Модуль для анализа тональности комментариев
import json
import asyncio
import ollama
import re

from youtube_service import YoutubeParser

class OllamaChat:
    parser = YoutubeParser()

    def __init__(self, model_name='ilyagusev/saiga_llama3'):
        self.model_name = model_name

    async def get_characteristics(self, url) -> str:
        comments = await self.parser.get_video_comments(url)
        with open("D:/УНИВЕР/практика/проба/code/bot/services/q_characteristics.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()
        base_prompt = ""
        prompt = base_prompt + "\n".join(comments) + "\n" + base_prompt

        response_text = await self.get_response_from_model(prompt)
        json_start = response_text.find("[")
        json_end = response_text.find("]")
        try:
            json_data = json.loads(response_text[json_start:json_end + 1])
            return json.dumps(json_data)
        except json.JSONDecodeError:
            return response_text

    async def get_characteristics_by_single_comm(self, url) -> str:
        comments = await self.parser.get_video_comments(url)
        with open("D:/УНИВЕР/практика/проба/code/bot/services/q_characteristics_one_comment.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()
        json_data = []
        for comment in comments:
            prompt = base_prompt + "\n".join(comment)
            response_text = await self.get_response_from_model(prompt)
            try:
                json_start = response_text.find("[")
                json_end = response_text.find("]")
                response_json = json.loads(response_text[json_start:json_end + 1])
                for characteristic_item in response_json:
                    characteristic_item["characteristic"] = characteristic_item[
                        "characteristic"].lower()  # Преобразуем к нижнему регистру
                    found = False
                    for existing_item in json_data:
                        if existing_item["characteristic"] == characteristic_item["characteristic"]:
                            existing_item["countOfPositiveComments"] += characteristic_item["countOfPositiveComments"]
                            existing_item["countOfNegativeComments"] += characteristic_item["countOfNegativeComments"]
                            found = True
                            break
                    if not found:
                        json_data.append(characteristic_item)
                # print(json_data)
            except json.JSONDecodeError:
                print(f"Ошибка декодирования JSON: {response_text}")
        return json.dumps(json_data)

    async def get_tonality(self, url) -> str:
        comments = await self.parser.get_video_comments(url)
        with open("q_tonality.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()

        prompt = "\n".join(comments) + "\n" + base_prompt

        response_text = await self.get_response_from_model(prompt)
        json_start = response_text.find("{")
        json_end = response_text.find("}")
        try:
            json_data = json.loads(response_text[json_start:json_end + 1])
            return json.dumps(json_data)
        except json.JSONDecodeError:
            return response_text

    async def get_summary(self, url) -> str:
        subtitles = await self.parser.get_subtitles(url)
        if subtitles is None:
            return None
        with open("D:/УНИВЕР/практика/проба/code/bot/services/q_summary.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()

        prompt = "\n".join(subtitles) + "\n" + base_prompt
        response_text = await self.get_response_from_model(prompt)
        return response_text

    async def get_group_name(self, characteristics) -> str:
        with open("D:/УНИВЕР/практика/проба/code/bot/services/q_group_name.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()

        prompt = base_prompt + "\n".join(characteristics) + "\n"
        response_text = await self.get_response_from_model(prompt)
        json_start = response_text.find("{")
        json_end = response_text.find("}")
        if json_start != -1 and json_end != -1:
            return response_text[json_start:json_end + 1]
        else:
            return response_text

    async def get_response_from_model(self, prompt: str) -> str:
        stream = ollama.chat(model=self.model_name,
                             messages=[{'role': 'user', 'content': prompt}],
                             stream=True)
        response_parts = []
        for chunk in stream:
            response_parts.append(chunk['message']['content'])

        response_text = "".join(response_parts)
        return response_text

# if __name__ == '__main__':
#     chat = OllamaChat()
#     url = "https://www.youtube.com/watch?v=PmP6WIz2UWw"
#     chat.get_characteristics_by_single_comm(url)
    # json_data = []
    # with open('ex.json', 'r', encoding='utf-8') as f:
    #     response_text = f.read()
    # try:
    #     json_start = response_text.find("[")
    #     json_end = response_text.find("]")
    #     response_json = json.loads(response_text[json_start:json_end + 1])
    #     for characteristic_item in response_json:
    #         characteristic_item["characteristic"] = characteristic_item[
    #             "characteristic"].lower()
    #         found = False
    #         for existing_item in json_data:
    #             if existing_item["characteristic"] == characteristic_item["characteristic"]:
    #                 existing_item["countOfPositiveComments"] += characteristic_item["countOfPositiveComments"]
    #                 existing_item["countOfNegativeComments"] += characteristic_item["countOfNegativeComments"]
    #                 found = True
    #                 break
    #         if not found:
    #             json_data.append(characteristic_item)
    #     print(json_data)
    # except json.JSONDecodeError:
    #     print(f"Ошибка декодирования JSON: {response_text}")




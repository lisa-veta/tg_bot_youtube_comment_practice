#Модуль для анализа тональности комментариев
import json
import asyncio
import ollama
import re
import asyncio
from youtube_service import YoutubeParser

class OllamaChat:
    parser = YoutubeParser()

    def __init__(self, model_name='ilyagusev/saiga_llama3'):
        self.model_name = model_name
        self.request_queue = asyncio.Queue()
        self.request_task = asyncio.create_task(self.process_requests())

    async def start(self):  # Новая функция для запуска обработки запросов
        self.request_task = asyncio.create_task(self.process_requests())

    async def get_characteristics(self, url) -> str:
        # Добавляем задачу в очередь
        task = asyncio.create_task(self._get_characteristics_new_way(url))
        await self.request_queue.put({'url': url, 'function_name': 'get_characteristics', 'future': task})
        # Ожидаем результата выполнения задачи
        result = await task
        return result

    # ... (Your other code) ...

    async def process_requests(self):
        while True:
            request = await self.request_queue.get()
            url = request['url']  # Access the url from the dictionary
            function_name = request['function_name']
            function = getattr(self, function_name)
            result = await function(url)
            request['future'].set_result(result)
            self.request_queue.task_done()
    # async def process_requests(self):
    #     while True:
    #         request = await self.request_queue.get()
    #         url = request['url']
    #         function_name = request['function_name']
    #         function = getattr(self, function_name)
    #         result = await function(url)
    #         request['future'].set_result(result)
    #
    # async def get_characteristics(self, url) -> str:
    #     # Добавляем задачу в очередь
    #     task = asyncio.create_task(self._get_characteristics_new_way(url))
    #     await self.request_queue.put(task)
    #     # Ожидаем результата выполнения задачи
    #     result = await task
    #     return result
    # async def get_group_name(self, characteristics) -> str:
    #     # Добавляем задачу в очередь
    #     task = asyncio.create_task(self._get_group_name(characteristics))
    #     await self.request_queue.put(task)
    #
    #     # Ожидаем результата выполнения всех задач в очереди
    #     tasks = [task for task in self.request_queue.queue if not task.done()]
    #     results = await asyncio.gather(*tasks)
    #
    #     # Возвращаем результат выполнения нашей задачи
    #     return results[0]

    # async def get_group_name(self, characteristics) -> str:
    #     # Добавляем задачу в очередь
    #     task = asyncio.create_task(self._get_group_name(characteristics))
    #     await self.request_queue.put(task)
    #     # Ожидаем результата выполнения задачи
    #     result = await task
    #     return result

    async def get_characteristics(self, url) -> str:
        comments, comments_count = await self.parser.get_video_comments(url)
        with open("D:/УНИВЕР/практика/проба/code/bot/services/q_characteristics.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()
        #base_prompt = ""
        prompt = base_prompt + "\n".join(comments) + "\n" + base_prompt

        response_text = await self.get_response_from_model(prompt)
        json_start = response_text.find("[")
        json_end = response_text.find("]")
        try:
            json_data = json.loads(response_text[json_start:json_end + 1])
            return json.dumps(json_data)
        except json.JSONDecodeError:
            return response_text

    async def _get_characteristics_new_way(self, url) -> str:
        comments, comments_count = await self.parser.get_video_comments(url)
        print(comments)
        with open("D:/УНИВЕР/практика/проба/code/bot/services/q_characteristics_new_way.txt", 'r', encoding='utf-8') as file:
            base_prompt = file.read()
        chunk_size = len(comments) // 10 + 1
        chunks = [comments[i:i + chunk_size] for i in range(0, len(comments), chunk_size)]
        json_data = []
        for chunk in chunks:
            count = f"Примерное количество комментариев: {len(chunk)}"
            prompt = base_prompt + "\n".join(count) + "\n".join(chunk) + "\n" + base_prompt
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
                print(json_data)
            except json.JSONDecodeError:
                print(f"Ошибка декодирования JSON: {response_text}")
            return json.dumps(json_data)

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

    # async def get_response_from_model(self, prompt: str) -> str:
    #     stream = ollama.chat(model=self.model_name,
    #                          messages=[{'role': 'user', 'content': prompt}],
    #                          stream=True)
    #     response_parts = []
    #     for chunk in stream:
    #         response_parts.append(chunk['message']['content'])
    #
    #     response_text = "".join(response_parts)
    #     return response_text

    async def get_response_from_model(self, prompt: str) -> str:
        async def _get_response():  # Внутренняя асинхронная функция
            stream = ollama.chat(model=self.model_name,
                                 messages=[{'role': 'user', 'content': prompt}],
                                 stream=True)
            response_parts = []
            for chunk in stream:
                response_parts.append(chunk['message']['content'])
            return "".join(response_parts)

        response_future = await asyncio.to_thread(_get_response)
        response_text = await response_future
        return response_text

    async def enqueue_request(self, url, function_name):
        future = asyncio.Future()
        request = {'url': url, 'function_name': function_name, 'future': future}
        await self.request_queue.put(request)
        return await future

    async def close(self):
        self.request_task.cancel()
if __name__ == '__main__':
    async def main():
        chat = OllamaChat()
        await chat.start()
        url = "https://www.youtube.com/watch?v=Jp4SB_lOu8E"
        json_data = await chat.get_characteristics(url)
        print(json_data)
    asyncio.run(main())
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




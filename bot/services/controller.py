import json
import sys
import os
import asyncio
import aiohttp
from youtube_service import YoutubeParser
from sentiment_analysis import OllamaChat
from characteristic_clusterer import CharacteristicClusterer
from graph_builder import GraphBuilder
# sys.path.insert(1, os.path.join(sys.path[0], 'D:/УНИВЕР/практика/code/bot/utils'))
from asyncio import Queue
# import json_parser
class Controller:
    def __init__(self):
        self.clusterer = CharacteristicClusterer()
        self.graph_builder = GraphBuilder()
        self.request_queue = Queue()

    async def get_video_info(self, video_url) -> dict:
        youtube_parser = YoutubeParser()
        return await youtube_parser.get_general_inf(video_url)

    async def add_request_to_queue(self, characteristics, num_groups):
        await self.request_queue.put((characteristics, num_groups))
    async def get_json_groups_from_chat(self, video_url, count_groups):
        #characteristics_str = self.chat.get_characteristics(video_url)
        #characteristics = json.loads(characteristics_str)
        #print(characteristics)
        with open('D:/УНИВЕР/практика/проба/code/bot/services/char.json', 'r', encoding='utf-8') as f:
            characteristics = json.load(f)
        print(characteristics)
        groups = await self.clusterer.group_characteristics(characteristics, count_groups)
        return groups

    async def get_characteristics_from_chat(self, video_url):
        chat = OllamaChat()
        characteristics_str = await chat.get_characteristics(video_url)
        characteristics = json.loads(characteristics_str)
        return characteristics

    async def get_json_groups_existed(self, characteristics, count_groups):
        groups = await self.clusterer.group_characteristics(characteristics, count_groups)
        return groups

    def get_characteristics(self, bd_data: dict) -> dict:  # извлечение списка характистик из json поступившего из бд
        return bd_data["characteristics"]
    async def get_general_positive_bubble_graph(self, json_groups: dict,  video_info: dict):
        fig = await self.graph_builder.make_positive_bubble_plot(json_groups, video_info)
        return fig
    async def get_general_negative_bubble_graph(self, json_groups: dict,  video_info: dict):
        fig = await self.graph_builder.make_negative_bubble_plot(json_groups, video_info)
        return fig
    async def get_group_positive_bubble_graph(self, json_groups: dict, group_name: str,  video_info: dict):
        new_json_groups = await self.find_group(json_groups, group_name)
        fig = await self.graph_builder.make_positive_bubble_plot(new_json_groups, video_info, 'green')
        return fig



    async def get_group_negative_bubble_graph(self, json_groups: dict, group_name: str,video_info: dict):
        new_json_groups = await self.find_group(json_groups, group_name)
        fig = await self.graph_builder.make_negative_bubble_plot(new_json_groups, video_info, 'red')
        return fig
    async def get_main_general_graph(self, json_groups: dict, video_info: dict):
        print("cстрою график")
        fig = await self.graph_builder.make_main_graph(json_groups, video_info)
        print("построил")
        return fig

    async def get_main_group_graph(self, json_groups: dict, group_name: str, video_info: dict):
        fig = await self.graph_builder.make_main_group_graph(json_groups, group_name, video_info)
        return fig

    async def find_group(self, json_groups: dict, group_name: str) -> dict:
        found_group = None
        for group in json_groups["groups"]:
            if group["group"] == group_name:
                found_group = group
                break
        if found_group is not None:
            json_groups["groups"] = [found_group]
        print(json_groups)
        return json_groups



# if __name__ == '__main__':
#      with open('bd_data.json', 'r', encoding='utf-8') as f:
#         bd_json = json.load(f)
#      controller = Controller()
#      groups = controller.get_json_groups_existed(bd_json, 3)
#      print(groups)
     # print(controller.get_video_info("https://www.youtube.com/watch?v=EKrPIu4gQtc"))
     # groups = controller.get_json_groups_from_chat("https://www.youtube.com/watch?v=EKrPIu4gQtc", 3)
#     # print(groups)
#     # with open('char.json', 'r', encoding='utf-8') as f:
#     #     characteristics = json.load(f)
#     # print(characteristics)
#     # clusterer = CharacteristicClusterer()
#     # json_groups = clusterer.group_characteristics(characteristics, 3)
#
#     # clusterer = CharacteristicClusterer()
#     # with open('characteristics.json', 'r', encoding='utf-8') as f:
#     #     characteristics = json.load(f)
#     # new_groups = clusterer.group_characteristics(characteristics, 5)
#     # print(new_groups)
#     youtube_parser = YoutubeParser()
#     video_inf = youtube_parser.get_general_inf("EKrPIu4gQtc")
#     with open('group.json', 'r', encoding='utf-8') as f:
#         groups = json.load(f)
#
#     main = controller.get_main_general_graph(groups, video_inf)
#     main.write_image("main.png",  width=1800, height=800)
#
#     main_g = controller.get_main_group_graph(groups, groups["groups"][0]["group"], video_inf)
#     main_g.write_image("main_g.png", width=1800, height=800)
#
#     bubble_positive_gen = controller.get_general_positive_bubble_graph(groups, video_inf)
#     bubble_positive_gen.write_image("bubble_positive_gen.png", width=1800, height=800)
#
#     bubble_negative_gen = controller.get_general_negative_bubble_graph(groups, video_inf)
#     bubble_negative_gen.write_image("bubble_negative_gen.png", width=1800, height=800)
#
#     bubble_positive = controller.get_group_positive_bubble_graph(groups, groups["groups"][0]["group"], video_inf)
#     bubble_positive.write_image("bubble_positive.png", width=1800, height=800)
#
#     bubble_negative = controller.get_group_negative_bubble_graph(groups, groups["groups"][0]["group"], video_inf)
#     bubble_negative.write_image("bubble_negative.png", width=1800, height=800)
#




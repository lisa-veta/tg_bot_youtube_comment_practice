import json

from sentiment_analysis import OllamaChat
from characteristic_clusterer import CharacteristicClusterer
from graph_builder import GraphBuilder
class Controller:
    def __init__(self):
        self.chat = OllamaChat()
        self.clusterer = CharacteristicClusterer()
        self.graph_builder = GraphBuilder()

    def get_json_groups(self, video_url, count_groups):
        characteristics_str = self.chat.get_characteristics(video_url)
        characteristics = json.loads(characteristics_str)
        groups = self.clusterer.group_characteristics(characteristics, count_groups)
        return groups

    def get_general_positive_bubble_graph(self, json_groups):
        fig = self.graph_builder.make_positive_bubble_plot(json_groups)
        return fig
    def get_general_negative_bubble_graph(self, json_groups):
        fig = self.graph_builder.make_negative_bubble_plot(json_groups)
        return fig
    def get_group_positive_bubble_graph(self, json_groups, group_name):
        new_json_groups = self.find_group(json_groups, group_name)
        fig = self.graph_builder.make_positive_bubble_plot(new_json_groups)
        return fig

    def get_group_negative_bubble_graph(self, json_groups, group_name):
        new_json_groups = self.find_group(json_groups, group_name)
        fig = self.graph_builder.make_negative_bubble_plot(new_json_groups)
        return fig
    def get_main_general_graph(self, json_groups):
        fig = self.graph_builder.make_main_graph(json_groups)
        return fig

    def get_main_group_graph(self, json_groups, group_name):
        fig = self.graph_builder.get_main_group_graph(json_groups, group_name)
        return fig

    def find_group(self, json_groups, group_name):
        found_group = None
        for group in json_groups["groups"]:
            if group["group"] == group_name:
                found_group = group
                break
        if found_group is not None:
            json_groups["groups"] = [found_group]
        return json_groups

# if __name__ == '__main__':
#     controller = Controller()
#     json_groups = controller.get_json_groups("https://www.youtube.com/watch?v=GjkuE3Q18TQ", 4)
#     # with open('char.json', 'r', encoding='utf-8') as f:
#     #     characteristics = json.load(f)
#     # print(characteristics)
#     # clusterer = CharacteristicClusterer()
#     # json_groups = clusterer.group_characteristics(characteristics, 3)
#     fig = controller.get_main_general_graph(json_groups)
#     fig.show()



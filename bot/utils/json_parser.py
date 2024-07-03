import json
import datetime
from typing import List, Tuple, Any, Dict


def parse_video_inf(inf_json: dict) -> (str, datetime, int, int, int):
    title = inf_json["title"]
    formatted_date_time = parse_date_time(inf_json["published_at"])
    views = int(inf_json["viewCount"])
    likes = int(inf_json["likeCount"])
    comments = int(inf_json["commentCount"])
    return title, formatted_date_time, views, likes, comments

def parse_groups(groups_json: dict) -> list[tuple[str, str]]:#метод для извлечения названий групп с описанием
    groups_dicts = groups_json["groups"]
    groups = list()
    for group in groups_dicts:
        name = group["group"]
        description = group["description"]
        groups.append((name, description))
    return groups

def add_count_group_to_groups(groups_json: dict, group_count: int) -> dict:#метод для преобразования данных для хранения в бд
    characteristics = ungroup_characteristics(groups_json)
    bd_data = {
        "group_count": group_count,
        "characteristics": characteristics
    }
    return bd_data
def add_count_group_to_characteristics(characteristics: dict, group_count: int) -> dict:
    bd_data = {
        "group_count": group_count,
        "characteristics": characteristics
    }
    return bd_data

def get_characteristics(bd_data: dict) -> dict:#извлечение списка характистик из json поступившего из бд
    return bd_data["characteristics"]

def ungroup_characteristics(groups_json: dict) -> List[Dict[str, int]]:#метод для извлечения списка характеристик из json с группами
    characteristics = []
    for group in groups_json["groups"]:
        for characteristic in group["characteristics"]:
            characteristics.append(characteristic)
    return characteristics

def parse_date_time(video_inf_date):
    dt_obj = datetime.datetime.strptime(video_inf_date, '%Y-%m-%dT%H:%M:%SZ')
    formatted_date_time = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_date_time

def get_count_characteristics(characteristics: dict) -> int:
    return len(characteristics)


#file = open("../../data/general_inf.json", "r")
#title, published_at, views, likes, comments = parse_video_inf(file.read())
#print(published_at.date())

#file = open("../../data/groups.json", "r")
#groups = parse_groups(file.read())
#print(groups)


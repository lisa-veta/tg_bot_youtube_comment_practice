import json
from datetime import *
from typing import List, Tuple, Any

from dateutil.parser import *


def parse_video_inf(inf_json: str) -> (str, datetime, int, int, int):
    dict = json.loads(inf_json)
    title = dict["title"]
    published_at = parse(dict["published_at"])
    views = int(dict["viewCount"])
    likes = int(dict["likeCount"])
    comments = int(dict["commentCount"])
    return title, published_at, views, likes, comments

def parse_groups(groups_json: str) -> list[tuple[str, str]]:
    dict = json.loads(groups_json)
    groups_dicts = dict["groups"]
    groups = list()
    for group in groups_dicts:
        name = group["group"]
        description = group["description"]
        groups.append((name, description))
    return groups


#file = open("../../data/general_inf.json", "r")
#title, published_at, views, likes, comments = parse_video_inf(file.read())
#print(published_at.date())

#file = open("../../data/groups.json", "r")
#groups = parse_groups(file.read())
#print(groups)

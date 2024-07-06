# -*- coding: utf-8 -*-
#класс для разбиения характеристик на группы и построения на основе этого графика
import torch
import asyncio
import json
from sklearn.cluster import KMeans
from transformers import AutoTokenizer, AutoModel

from sentiment_analysis import OllamaChat


class CharacteristicClusterer:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained('intfloat/multilingual-e5-base')
        self.model = AutoModel.from_pretrained('intfloat/multilingual-e5-base')


    async def get_embedding(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
        with torch.no_grad():
            output = self.model(**inputs)
        embeddings = output.last_hidden_state.mean(dim=1).squeeze()
        return embeddings.numpy()

    async def group_characteristics(self, characteristics, num_groups):
        chat = OllamaChat()
        texts = [char['characteristic'] for char in characteristics]
        vectors = []
        for text in texts:
            vectors.append(await self.get_embedding(text))
        loop = asyncio.get_event_loop()
        kmeans = await loop.run_in_executor(None, KMeans(n_clusters=num_groups, random_state=0).fit, vectors)
        labels = kmeans.labels_
        groups = []
        for i in range(num_groups):
            group_characteristics = [characteristics[j] for j, label in enumerate(labels) if label == i]
            characteristics_text = [char['characteristic'] for char in group_characteristics]
            group_name_str = await chat.get_group_name(characteristics_text)
            group_name = json.loads(group_name_str)["group"]
            while(len(group_name) > 26):
                group_name_str = await chat.get_group_name(characteristics_text)
                group_name = json.loads(group_name_str)["group"]
            group_description = json.loads(group_name_str)["description"]
            groups.append({
                "group": group_name,
                "description": group_description,
                "characteristics": group_characteristics
            })
            print(group_name_str)
        return {
            "groups": groups
        }


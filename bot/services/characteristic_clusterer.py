# -*- coding: utf-8 -*-
#класс для разбиения характеристик на группы и построения на основе этого графика
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.cluster import KMeans
from sentiment_analysis import OllamaChat
import json
import plotly.express as px
from sklearn.decomposition import PCA

class CharacteristicClusterer:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained('intfloat/multilingual-e5-base')
        self.model = AutoModel.from_pretrained('intfloat/multilingual-e5-base')
        self.chat = OllamaChat()

    def get_embedding(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
        with torch.no_grad():
            output = self.model(**inputs)
        embeddings = output.last_hidden_state.mean(dim=1).squeeze()
        return embeddings.numpy()

    def group_characteristics(self, characteristics, num_groups):
        texts = [char['characteristic'] for char in characteristics]
        vectors = [self.get_embedding(text) for text in texts]
        kmeans = KMeans(n_clusters=num_groups, random_state=0).fit(vectors)
        labels = kmeans.labels_
        groups = []
        for i in range(num_groups):
            group_characteristics = [characteristics[j] for j, label in enumerate(labels) if label == i]
            characteristics_text = [char['characteristic'] for char in group_characteristics]
            group_name_str = self.chat.get_group_name(characteristics_text)
            group_name = json.loads(group_name_str)["group"]
            group_description = json.loads(group_name_str)["description"]
            groups.append({
                "group": group_name,
                "description": group_description,
                "characteristics": group_characteristics
            })
        return {
            "groups": groups
        }


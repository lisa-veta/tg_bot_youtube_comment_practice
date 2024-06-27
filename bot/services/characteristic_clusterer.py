# -*- coding: utf-8 -*-
#класс для разбиения характеристик на группы
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

    def cluster_characteristics(self, characteristics, num_groups):
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
            groups.append({
                "group": group_name,
                "characteristics": group_characteristics
            })
        return {
            "groups": groups
        }

    def plot_characteristics(self, groups):
        data = []
        all_embeddings = [self.get_embedding(char['characteristic']) for group in groups for char in
                          group['characteristics']]
        pca = PCA(n_components=2)
        vectors_2d = pca.fit_transform(all_embeddings)

        index = 0
        for i, group in enumerate(groups):
            for j, characteristic in enumerate(group['characteristics']):
                data.append({
                    'x': vectors_2d[index][0],
                    'y': vectors_2d[index][1],
                    'size': characteristic['countOfPositiveComments'] + characteristic['countOfNegativeComments'] +
                            characteristic['countOfNeutralComments'],
                    'color': i,
                    'text': characteristic['characteristic']
                })
                index += 1

        fig = px.scatter(data, x='x', y='y', size='size', color='color',
                         hover_name='text', size_max=60)
        fig.update_traces(marker=dict(line=dict(width=2, color='DarkSlateGrey')))
        fig.show()
import asyncio
import datetime
import plotly.express as px
from sklearn.decomposition import PCA
import plotly.graph_objects as go
import json
from youtube_service import YoutubeParser
from characteristic_clusterer import CharacteristicClusterer
class GraphBuilder:
    def __init__(self):
        self.CharacteristicClusterer = CharacteristicClusterer()


    async def make_positive_bubble_plot(self, group_characteristics, video_inf, color=None):
        print("строю make_positive_bubble_plot")
        groups = group_characteristics['groups']
        data = []
        all_embeddings = [await self.CharacteristicClusterer.get_embedding(char['characteristic']) for group in groups for
                          char in
                          group['characteristics']]
        if len(all_embeddings) == 1:
            vectors_2d = [all_embeddings[0]]
        else:
            pca = PCA(n_components=2)
            vectors_2d = pca.fit_transform(all_embeddings)
        index = 0
        commentCount = 0
        for i, group in enumerate(groups):
            for j, characteristic in enumerate(group['characteristics']):
                hover_text = ('{characteristic}<br>' +
                              'Количество положительных комментариев: {count}').format(
                    characteristic=characteristic['characteristic'],
                    count=characteristic['countOfPositiveComments'])
                commentCount += characteristic['countOfPositiveComments']
                x = vectors_2d[index][0] if len(vectors_2d) > 1 else vectors_2d[0][0]
                y = vectors_2d[index][1] if len(vectors_2d) > 1 else vectors_2d[0][1]
                data.append({
                    'x': x,
                    'y': y,
                    'size': characteristic['countOfPositiveComments'],
                    'color': f"Группа {group['group']}",
                    'text': hover_text
                })
                index += 1
        fig = px.scatter(data, x='x', y='y', size='size', color='color', hover_name='text', size_max=60,
                         color_discrete_sequence=[color] if color is not None else None)
        if color is None:
            commentCount = video_inf['commentCount']
        formatted_date_time = self.parse_date_time(video_inf['published_at'])
        fig.update_layout(title=f'Группы характеристик с положительными комментариями для видео "{video_inf["title"]}"',
                          legend_title=f"Дата публикации: {formatted_date_time}<br>"
                                       f"Количество просмотров: {video_inf['viewCount']}<br>"
                                       f"Количество лайков: {video_inf['likeCount']}<br>"
                                       f"Количество проанализированных<br>комментариев: {commentCount}<br><br>")
        fig.update_traces(marker=dict(line=dict(width=2, color='White')))
        return fig

    async def make_negative_bubble_plot(self, group_characteristics, video_inf, color = None):
        print("строю make_negative_bubble_plot")
        groups = group_characteristics['groups']
        data = []
        all_embeddings = [await self.CharacteristicClusterer.get_embedding(char['characteristic']) for group in groups for char in
                          group['characteristics']]
        if len(all_embeddings) == 1:
            vectors_2d = [all_embeddings[0]]
        else:
            pca = PCA(n_components=2)
            vectors_2d = pca.fit_transform(all_embeddings)
        index = 0
        commentCount = 0
        for i, group in enumerate(groups):
            for j, characteristic in enumerate(group['characteristics']):
                hover_text = ('{characteristic}<br>' +
                              'Количество отрицательных комментариев: {count}').format(
                    characteristic=characteristic['characteristic'],
                    count=characteristic['countOfNegativeComments'])
                commentCount += characteristic['countOfNegativeComments']
                x = vectors_2d[index][0] if len(vectors_2d) > 1 else vectors_2d[0][0]
                y = vectors_2d[index][1] if len(vectors_2d) > 1 else vectors_2d[0][1]
                data.append({
                    'x': x,
                    'y': y,
                    'size': characteristic['countOfNegativeComments'],
                    'color': f"Группа {group['group']}",
                    'text': hover_text
                })
                index += 1
        if color is None:
            commentCount = video_inf['commentCount']
        fig = px.scatter(data, x='x', y='y', size='size', color='color', hover_name='text', size_max=60,
                         color_discrete_sequence=[color] if color is not None else None)
        formatted_date_time = self.parse_date_time(video_inf['published_at'])
        fig.update_layout(title=f'Группы характеристик с негативными комментариями для видео "{video_inf["title"]}"', coloraxis_showscale=False,  legend_title=f"Дата публикации: {formatted_date_time}<br>"
                            f"Количество просмотров: {video_inf['viewCount']}<br>"
                             f"Количество лайков: {video_inf['likeCount']}<br>"
               f"Количество проанализированных<br>комментариев: {commentCount}<br><br>")
        fig.update_traces(marker=dict(line=dict(width=2, color='White')))
        return fig

    async def make_positive_bubble_plot_3d(self, group_characteristics, video_inf, color=None):
        print("строю make_positive_bubble_plot_3d")
        groups = group_characteristics['groups']
        data = []
        all_embeddings = [await self.CharacteristicClusterer.get_embedding(char['characteristic']) for group in groups
                          for
                          char in
                          group['characteristics']]

        # Handle cases with one or two characteristics
        if len(all_embeddings) == 1:
            vectors_3d = [[0, 0, all_embeddings[0][0]]]  # Generate Z coordinate
        elif len(all_embeddings) == 2:
            vectors_3d = [[0, emb[0], emb[1]] for emb in all_embeddings]  # Generate Z coordinate as 0
        else:
            pca = PCA(n_components=3)
            vectors_3d = pca.fit_transform(all_embeddings)

        index = 0
        commentCount = 0
        for i, group in enumerate(groups):
            for j, characteristic in enumerate(group['characteristics']):
                hover_text = ('{characteristic}<br>' +
                              'Количество положительных комментариев: {count}').format(
                    characteristic=characteristic['characteristic'],
                    count=characteristic['countOfPositiveComments'])
                commentCount += characteristic['countOfPositiveComments']
                x = vectors_3d[index][0]
                y = vectors_3d[index][1]
                z = vectors_3d[index][2]
                data.append({
                    'x': x,
                    'y': y,
                    'z': z,
                    'size': characteristic['countOfPositiveComments'],
                    'color': f"Группа {group['group']}",
                    'text': hover_text
                })
                index += 1

        fig = px.scatter_3d(data, x='x', y='y', z='z', size='size', color='color', hover_name='text', size_max=60,
                            color_discrete_sequence=[color] if color is not None else None)

        if color is None:
            commentCount = video_inf['commentCount']
        formatted_date_time = self.parse_date_time(video_inf['published_at'])
        fig.update_layout(title=f'Группы характеристик с позитивными комментариями для видео "{video_inf["title"]}"',
                          legend_title=f"Дата публикации: {formatted_date_time}<br>"
                                       f"Количество просмотров: {video_inf['viewCount']}<br>"
                                       f"Количество лайков: {video_inf['likeCount']}<br>"
                                       f"Количество проанализированных<br>комментариев: {commentCount}<br><br>")
        fig.update_traces(marker=dict(line=dict(width=2, color='White')))
        #fig.show()
        #fig.write_html("art.html")
        return fig

    async def make_negative_bubble_plot_3d(self, group_characteristics, video_inf, color=None):
        print("строю make_negative_bubble_plot_3d")
        groups = group_characteristics['groups']
        data = []
        all_embeddings = [await self.CharacteristicClusterer.get_embedding(char['characteristic']) for group in groups
                          for
                          char in
                          group['characteristics']]
        # Handle cases with one or two characteristics
        if len(all_embeddings) == 1:
            vectors_3d = [[0, 0, all_embeddings[0][0]]]  # Generate Z coordinate
        elif len(all_embeddings) == 2:
            vectors_3d = [[0, emb[0], emb[1]] for emb in all_embeddings]  # Generate Z coordinate as 0
        else:
            pca = PCA(n_components=3)
            vectors_3d = pca.fit_transform(all_embeddings)

        index = 0
        commentCount = 0
        for i, group in enumerate(groups):
            for j, characteristic in enumerate(group['characteristics']):
                hover_text = ('{characteristic}<br>' +
                              'Количество негативных комментариев: {count}').format(
                    characteristic=characteristic['characteristic'],
                    count=characteristic['countOfNegativeComments'])
                commentCount += characteristic['countOfNegativeComments']
                x = vectors_3d[index][0]
                y = vectors_3d[index][1]
                z = vectors_3d[index][2]
                data.append({
                    'x': x,
                    'y': y,
                    'z': z,
                    'size': characteristic['countOfNegativeComments'],
                    'color': f"Группа {group['group']}",
                    'text': hover_text
                })
                index += 1

        fig = px.scatter_3d(data, x='x', y='y', z='z', size='size', color='color', hover_name='text', size_max=60,
                            color_discrete_sequence=[color] if color is not None else None)

        if color is None:
            commentCount = video_inf['commentCount']
        formatted_date_time = self.parse_date_time(video_inf['published_at'])
        fig.update_layout(title=f'Группы характеристик с негативными комментариями для видео "{video_inf["title"]}"',
                          legend_title=f"Дата публикации: {formatted_date_time}<br>"
                                       f"Количество просмотров: {video_inf['viewCount']}<br>"
                                       f"Количество лайков: {video_inf['likeCount']}<br>"
                                       f"Количество проанализированных<br>комментариев: {commentCount}<br><br>")
        fig.update_traces(marker=dict(line=dict(width=2, color='White')))
        #fig.show()
        fig.write_html("art.html")
        return fig

    async def make_main_graph(self, group_characteristics, video_inf):
        print("строю make_main_graph")
        groups = []
        positive_values = []
        negative_values = []
        colors = []
        for i, group in enumerate(group_characteristics["groups"]):
            groups.append(group["group"])
            positive_sum = sum(
                characteristic["countOfPositiveComments"]
                for characteristic in group["characteristics"]
            )
            negative_sum = sum(
                characteristic["countOfNegativeComments"]
                for characteristic in group["characteristics"]
            )
            positive_values.append(positive_sum)
            negative_values.append(-negative_sum)  # Отнимаем, чтобы отрисовать вниз
            colors.append(f"hsl({i * 360 / len(group_characteristics['groups'])}, 50%, 50%)")

        fig = go.Figure()

        for i, (group, positive_value, color) in enumerate(
                zip(groups, positive_values, colors)
        ):
            fig.add_trace(
                go.Bar(
                    name=group,
                    x=[i],
                    y=[positive_value],
                    marker_color=color,
                    width=0.5,
                    showlegend=True,
                )
            )

        for i, (group, negative_value, color) in enumerate(
                zip(groups, negative_values, colors)
        ):
            fig.add_trace(
                go.Bar(
                    name=group,
                    x=[i],
                    y=[negative_value],
                    marker_color=color,
                    width=0.5,
                    base=0,
                    showlegend=False,
                )
            )
        formatted_date_time = self.parse_date_time(video_inf['published_at'])
        fig.update_layout(
            title=f'Группы характеристик для видео "{video_inf["title"]}"',
            xaxis_title="Группы",
            yaxis_title="Сумма комментариев",
            barmode="overlay",
            bargap=0.2,  # Расстояние между столбиками
            bargroupgap=0.1,  # Расстояние между группами столбиков
            showlegend=True,  # Показывать легенду
            legend_title=f"Дата публикации: {formatted_date_time}<br>"
                            f"Количество просмотров: {video_inf['viewCount']}<br>"
                             f"Количество лайков: {video_inf['likeCount']}<br>"
               f"Количество проанализированных<br>комментариев: {video_inf['commentCount']}<br><br>"
                            "Группы:",
            yaxis_range=[min(negative_values) * 1.1, max(positive_values) * 1.1],
            font=dict(color="black", size=16),
        )
        # Добавление текста на оси Y
        fig.update_yaxes(
            ticktext=["Отрицательные<br>комментарии", "Положительные<br>комментарии"],
            tickvals=[min(negative_values), max(positive_values)],
            tickmode="array",
        )
        fig.update_layout(
            legend=dict(
                font=dict(
                    size=18
                )
            )
        )
        for i in range(len(groups)):
            fig.add_annotation(
                x=i,
                y=positive_values[i] / 2,
                text=f"<b>{positive_values[i]}/{abs(negative_values[i])}</b>",
                showarrow=False,
                font=dict(color="black", size=20),
            )
        fig.update_xaxes(
            tickvals=list(range(len(groups))),
            ticktext=groups,
        )
        return fig

    async def make_main_group_graph(self, group_characteristics, selected_group, video_inf):
        print("строю make_main_group_graph")
        for group_data in group_characteristics["groups"]:
            if group_data["group"] == selected_group:
                group_characteristics = group_data["characteristics"]
                fig = go.Figure()
                colors = [f"hsl({i * 360 / len(group_characteristics)}, 50%, 50%)" for i in
                          range(len(group_characteristics))]
                x_labels = [characteristic["characteristic"] for characteristic in group_characteristics]
                commentCount = 0
                for i, characteristic in enumerate(group_characteristics):
                    commentCount += characteristic['countOfPositiveComments'] + characteristic['countOfNegativeComments']
                    fig.add_trace(
                        go.Bar(
                            name=characteristic["characteristic"],
                            x=[i],
                            y=[characteristic["countOfPositiveComments"]],
                            marker_color=colors[i],
                            width=0.4,
                            showlegend=True
                        )
                    )
                    fig.add_trace(
                        go.Bar(
                            name=characteristic["characteristic"],
                            x=[i],
                            y=[-characteristic["countOfNegativeComments"]],
                            marker_color=colors[i],
                            width=0.4,
                            base=0,
                            showlegend=False
                        )
                    )
                    fig.add_annotation(
                        x=i,
                        y=characteristic["countOfPositiveComments"] / 2,
                        text=f"<b>{characteristic['countOfPositiveComments']}/{abs(characteristic['countOfNegativeComments'])}</b>",
                        showarrow=False,
                        font=dict(color="black", size=20),
                    )
                formatted_date_time = self.parse_date_time(video_inf['published_at'])
                fig.update_layout(
                    title=f'Характеристики группы "{selected_group}" для видео "{video_inf["title"]}"',
                    xaxis_title="Характеристики",
                    yaxis_title="Сумма комментариев",
                    barmode="overlay",
                    bargap=0.2,
                    bargroupgap=0.1,
                    showlegend=True,
                    legend_title=f"Дата публикации: {formatted_date_time}<br>"
                                 f"Количество просмотров: {video_inf['viewCount']}<br>"
                                 f"Количество лайков: {video_inf['likeCount']}<br>"
                                 f"Количество проанализированных<br>комментариев: {commentCount}<br><br>"
                                 "Характеристики:",
                    yaxis_range=[min([-characteristic["countOfNegativeComments"] for characteristic in
                                      group_characteristics]) * 1.1,
                                 max([characteristic["countOfPositiveComments"] for characteristic in
                                      group_characteristics]) * 1.1],
                    font=dict(color="black", size=16),
                )
                fig.update_yaxes(
                    ticktext=["Отрицательные<br>комментарии", "Положительные<br>комментарии"],
                    tickvals=[
                        min([-characteristic["countOfNegativeComments"] for characteristic in
                             group_characteristics]),
                        max([characteristic["countOfPositiveComments"] for characteristic in
                             group_characteristics])],
                    tickmode="array",
                )
                fig.update_xaxes(
                    tickvals=list(range(len(group_characteristics))),
                    ticktext=x_labels,
                )
                return fig

    def parse_date_time(self, video_inf_date):
        dt_obj = datetime.datetime.strptime(video_inf_date, '%Y-%m-%dT%H:%M:%SZ')
        formatted_date_time = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_date_time

if __name__ == '__main__':
    async def main():
        graph = GraphBuilder()
        with open('group.json', 'r', encoding='utf-8') as f:
            groups = json.load(f)
        with open('general_inf.json', 'r', encoding='utf-8') as f:
            video_inf = json.load(f)
        fig = await graph.make_positive_bubble_plot_3d(groups, video_inf)
    asyncio.run(main())


# if __name__ == '__main__':
#     with open('group.json', 'r', encoding='utf-8') as f:
#         groups = json.load(f)
#     youtube_parser = YoutubeParser()
#     video_inf = youtube_parser.get_general_inf("nIkH6C3_CX8")
#     graph = GraphBuilder()
#     fig = graph.make_main_graph(groups, video_inf)
#     fig.show()
#     # fig = graph.make_main_group_graph(groups, groups["groups"][0]["group"], video_inf)
#     # fig.show()
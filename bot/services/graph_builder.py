import plotly.express as px
from sklearn.decomposition import PCA
import plotly.graph_objects as go
import json
from characteristic_clusterer import CharacteristicClusterer
class GraphBuilder:
    def __init__(self):
        self.CharacteristicClusterer = CharacteristicClusterer()

    def make_positive_bubble_plot(self, group_characteristics):
        groups = group_characteristics['groups']
        data = []
        all_embeddings = [CharacteristicClusterer.get_embedding(char['characteristic']) for group in groups for char in
                          group['characteristics']]
        pca = PCA(n_components=2)
        vectors_2d = pca.fit_transform(all_embeddings)
        group_colors = {}
        index = 0
        for i, group in enumerate(groups):
            group_colors[group['group']] = i
            for j, characteristic in enumerate(group['characteristics']):
                hover_text = ('{characteristic}<br>' +
                              'Количество позитивных комментариев: {count}').format(
                    characteristic=characteristic['characteristic'],
                    count=characteristic['countOfPositiveComments'])
                data.append({
                    'x': vectors_2d[index][0],
                    'y': vectors_2d[index][1],
                    'size': characteristic['countOfPositiveComments'],
                    'color': group['group'],  # Changed to use group name instead of index
                    'text': hover_text
                })
                index += 1
        fig = px.scatter(data, x='x', y='y', size='size', color='color', hover_name='text', size_max=60)
        fig.update_layout(title='Группы характеристик с позитивными комментариями', coloraxis_showscale=False)
        fig.update_traces(marker=dict(line=dict(width=2, color='White')))
        # fig.write_html("characteristics_positive_plot.html", auto_open=False)
        return fig

    def make_negative_bubble_plot(self, group_characteristics):
        groups = group_characteristics['groups']
        data = []
        all_embeddings = [CharacteristicClusterer.get_embedding(char['characteristic']) for group in groups for char in
                          group['characteristics']]
        pca = PCA(n_components=2)
        vectors_2d = pca.fit_transform(all_embeddings)
        group_colors = {}
        index = 0
        for i, group in enumerate(groups):
            group_colors[group['group']] = i
            for j, characteristic in enumerate(group['characteristics']):
                hover_text = ('{characteristic}<br>' +
                              'Количество отрицательных комментариев: {count}').format(
                    characteristic=characteristic['characteristic'],
                    count=characteristic['countOfNegativeComments'])
                data.append({
                    'x': vectors_2d[index][0],
                    'y': vectors_2d[index][1],
                    'size': characteristic['countOfNegativeComments'],
                    'color': group['group'],  # Changed to use group name instead of index
                    'text': hover_text
                })
                index += 1
        fig = px.scatter(data, x='x', y='y', size='size', color='color', hover_name='text', size_max=60)
        fig.update_layout(title='Группы характеристик с негативными комментариями', coloraxis_showscale=False)
        fig.update_traces(marker=dict(line=dict(width=2, color='White')))
        # fig.write_html("characteristics_negative_plot.html", auto_open=False)
        return fig

    def make_main_graph(self, group_characteristics):
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

        fig.update_layout(
            title="Группы характеристик",
            xaxis_title="Группы",
            yaxis_title="Сумма комментариев",
            barmode="overlay",  # Overlay the bars for alignment
            bargap=0.2,  # Расстояние между столбиками
            bargroupgap=0.1,  # Расстояние между группами столбиков
            showlegend=True,  # Показывать легенду
            legend_title="Группы:",
            yaxis_range=[min(negative_values) * 1.1, max(positive_values) * 1.1],
            font=dict(color="black", size=16),
        )

        # Добавление текста на оси Y
        fig.update_yaxes(
            ticktext=["Отрицательные комментарии", "Положительные Комментарии"],
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
        #fig.write_html("characteristics_new.html", auto_open=False)
        #fig.write_image("characteristics_new.png", width=1800, height=800)
        #fig.show()
        return fig

    def get_main_group_graph(self, group_characteristics, selected_group):
        for group_data in group_characteristics["groups"]:
            if group_data["group"] == selected_group:
                group_characteristics = group_data["characteristics"]

                fig = go.Figure()
                colors = [f"hsl({i * 360 / len(group_characteristics)}, 50%, 50%)" for i in
                          range(len(group_characteristics))]

                for i, characteristic in enumerate(group_characteristics):
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

                fig.update_layout(
                    title=f"Характеристики группы '{selected_group}'",
                    xaxis_title="Характеристики",
                    yaxis_title="Сумма комментариев",
                    barmode="overlay",
                    bargap=0.2,
                    bargroupgap=0.1,
                    showlegend=True,
                    legend_title=f"Характеристики:",
                    yaxis_range=[min([-characteristic["countOfNegativeComments"] for characteristic in
                                      group_characteristics]) * 1.1,
                                 max([characteristic["countOfPositiveComments"] for characteristic in
                                      group_characteristics]) * 1.1],
                    font=dict(color="black", size=16),
                )

                fig.update_yaxes(
                    ticktext=["Отрицательные комментарии", "Положительные комментарии"],
                    tickvals=[
                        min([-characteristic["countOfNegativeComments"] for characteristic in
                             group_characteristics]),
                        max([characteristic["countOfPositiveComments"] for characteristic in
                             group_characteristics])],
                    tickmode="array",
                )

                fig.update_xaxes(
                    tickvals=list(range(len(group_characteristics))),
                    ticktext=[str(i) for i in range(len(group_characteristics))],
                )

                #fig.write_html("group_characteristics.html", auto_open=False)
                #fig.write_image("group_characteristics.png", width=1800, height=800)
                #fig.show()
                return fig
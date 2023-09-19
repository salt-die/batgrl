from nurses_2.app import App
from nurses_2.colors import DEFAULT_COLOR_THEME
from nurses_2.widgets.bar_chart import BarChart
from nurses_2.widgets.text_widget import TextWidget

PRIMARY_COLOR = DEFAULT_COLOR_THEME.primary


class BarChartApp(App):
    async def on_start(self):
        bar_chart_data = {
            "Python": 1,
            "Java": 0.588,
            "C++": 0.538,
            "C": 0.4641,
            "Javascript": 0.4638,
            "C#": 0.3973,
            "SQL": 0.3397,
            "Go": 0.2157,
            "Typescript": 0.1794,
            "HTML": 0.139,
            "R": 0.1316,
            "Shell": 0.1286,
            "PHP": 0.1186,
        }

        bar_chart = BarChart(
            bar_chart_data,
            min_y=0,
            y_label="Age",
            size=(25, 75),
            pos_hint=(0.5, 0.5),
        )
        label = TextWidget(default_color_pair=PRIMARY_COLOR, pos_hint=(None, 0.5))
        label.set_text("Top Programming Languages 2023")
        label.subscribe(
            bar_chart, "pos", lambda: setattr(label, "bottom", bar_chart.top)
        )
        self.add_widgets(label, bar_chart)


BarChartApp(title="Bar Chart Example", background_color_pair=PRIMARY_COLOR).run()

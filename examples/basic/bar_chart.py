from batgrl.app import App
from batgrl.colors import DEFAULT_PRIMARY_BG, DEFAULT_PRIMARY_FG
from batgrl.gadgets.bar_chart import BarChart
from batgrl.gadgets.text import Text, style_char


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
            pos_hint={"y_hint": 0.5, "x_hint": 0.5},
        )
        label = Text(
            default_cell=style_char(
                " ", fg_color=DEFAULT_PRIMARY_FG, bg_color=DEFAULT_PRIMARY_BG
            ),
            pos_hint={"x_hint": 0.5},
        )
        label.set_text("Top Programming Languages 2023")
        bar_chart.bind("pos", lambda: setattr(label, "bottom", bar_chart.top))
        text_bg = Text(size=(25, 75), pos_hint={"y_hint": 0.5, "x_hint": 0.5})

        self.add_gadgets(text_bg, label, bar_chart)


if __name__ == "__main__":
    BarChartApp(title="Bar Chart Example", bg_color=DEFAULT_PRIMARY_BG).run()

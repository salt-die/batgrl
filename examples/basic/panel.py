from nurses_2.app import run_widget_as_app
from nurses_2.widgets.text_panel import TextPanel

panel = TextPanel()
panel.text = """\
Fire and Ice
by Robert Frost

Some say the world will end in fire,
Some say in ice.
From what I’ve tasted of desire
I hold with those who favor fire.
But if it had to perish twice,
I think I know enough of hate
To say that for destruction ice
Is also great
And would suffice.
"""
panel.size = panel.minimum_panel_size
panel.text_container.canvas[0]["bold"] = True
panel.text_container.canvas[:2]["italic"] = True
panel.add_border()

run_widget_as_app(panel)

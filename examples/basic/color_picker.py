from nurses_2.app import run_widget_as_app
from nurses_2.widgets.color_picker import ColorPicker

if __name__ == "__main__":
    run_widget_as_app(ColorPicker(size_hint={"height_hint": 1.0, "width_hint": 1.0}))

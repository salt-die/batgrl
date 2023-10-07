from batgrl.app import run_gadget_as_app
from batgrl.gadgets.color_picker import ColorPicker

if __name__ == "__main__":
    run_gadget_as_app(ColorPicker(size_hint={"height_hint": 1.0, "width_hint": 1.0}))

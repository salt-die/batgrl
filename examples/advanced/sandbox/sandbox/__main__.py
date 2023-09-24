from nurses_2.app import run_widget_as_app

from .sandbox import Sandbox

if __name__ == "__main__":
    run_widget_as_app(Sandbox(size=(31, 100)))

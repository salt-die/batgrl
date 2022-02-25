from nurses_2.app import run_widget_as_app
from nurses_2.widgets.file_chooser import FileChooser

run_widget_as_app(FileChooser, size=(20, 25), size_hint=(1.0, None))

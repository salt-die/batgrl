from abc import ABC, abstractmethod


class Themable(ABC):
    """
    Themable widgets fetch their color theme from the app. They
    must implement a single method, `update_theme` which is called
    whenever the app's theme is set.
    """
    @abstractmethod
    def update_theme(self):
        """
        Repaint the widget with a new theme.
        """

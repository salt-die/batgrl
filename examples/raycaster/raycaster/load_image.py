import cv2

def load_image(path):
    """
    Load an image as numpy array from a pathlib.Path.
    """
    return cv2.cvtColor(cv2.imread(str(path), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
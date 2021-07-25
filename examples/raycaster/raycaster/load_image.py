import cv2

def load_image(path):
    """
    Load an image as numpy array from a pathlib.Path.
    """
    path_str = str(path)
    bgr_image = cv2.imread(path_str, cv2.IMREAD_COLOR)
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    return rgb_image

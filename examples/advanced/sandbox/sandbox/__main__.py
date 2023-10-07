from batgrl.app import run_gadget_as_app

from .sandbox import Sandbox

if __name__ == "__main__":
    run_gadget_as_app(Sandbox(size=(31, 100)))

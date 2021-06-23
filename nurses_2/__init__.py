from prompt_toolkit.key_binding.key_bindings import Binding

__all__ = ()

# `prompt_toolkit` `Binding`s create tasks through `prompt_toolkit`'s `App` class.
# This is patched to just create tasks through asyncio.

def call(self, event):
    if result := self.handler(event):
        asyncio.create_task(result)

Binding.call = call

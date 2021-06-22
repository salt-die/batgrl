from prompt_toolkit.key_binding.key_bindings import Binding

# `prompt_toolkit` `Binding`s create tasks through `prompt_toolkit`'s `App` class.
# This is patched to just created tasks through asyncio.

def call(self, event):
    if result := self.handler(event):
        asyncio.create_task(result)

Binding.call = call

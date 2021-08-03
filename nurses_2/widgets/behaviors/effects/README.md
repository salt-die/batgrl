# Effects

Effects are behaviors that modify how a widget and its children are rendered.
Effects should be inherited in the reverse order that they are applied, e.g.,
    ```
    class MyEffectWidget(Effect1, Effect2, Widget):
        ...
    ```
applies Effect2 then Effect1.

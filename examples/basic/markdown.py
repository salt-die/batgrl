"""A markdown example."""
from batgrl.app import App
from batgrl.gadgets.markdown import Markdown

MARKDOWN_TEXT = """\
Markdown
========
A showcase of batgrl markdown rendering.

Headings
--------
# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6

Ordered List
------------
1. one
2. two
3. three

Unordered List
--------------
- first bullet
  - second bullet
    - third bullet
      - fourth bullet
        - fifth bullet
          - sixth bullet
            - seventh bullet
              - eighth bullet

Task List
---------
- [x] Item done
- [ ] Item not done

Inline Tokens
-------------
Emoji codes: :+1: :100: :smiley:

Inline code: `2 + 2 = 4`

Links: [batgrl](https://github.com/salt-die/batgrl "badass terminal graphics library")

Inline images: ![A spinning python logo.](../assets/spinner.gif "Weeeeee!") \
![Image can't be displayed.](not_found.png "A non-displayable image.")

Code Block
----------
```python
# This is a comment
1 + 1
print("hello world")
```

Quotes
------
> No wise fish would go anywhere without a porpoise.
>> Why, sometimes I’ve believed as many as six impossible things before breakfast.

Tables
------
Title                       | Author          | Date
:-------------------------- | :-------------: | ---:
A Line-storm Song           |  Robert Frost   | 1913
The Weary Blues             | Langston Hughes | 1926
Morning in the Burned House | Margaret Atwood | 1995
"""


class MarkdownApp(App):
    """A markdown app."""

    async def on_start(self):
        """Coroutine scheduled when app is run."""
        markdown = Markdown(
            markdown=MARKDOWN_TEXT, size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )
        self.add_gadget(markdown)
        import sys

        for gadget in self.root.walk():
            if gadget.width > 120:
                print(gadget, gadget.children, file=sys.stderr)


if __name__ == "__main__":
    MarkdownApp(title="Markdown Example").run()

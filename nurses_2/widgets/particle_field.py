from .widget import Widget
from ..colors import WHITE_ON_BLACK


class ParticleField(Widget):
    """
    A Widget that only has `Particle` children.
    """
    def add_widget(self, widget):
        raise NotImplementedError("use `add_particle` instead")

    def add_widgets(self, widget):
        raise NotImplementedError("use `add_particles` instead")

    def remove_widget(self, widget):
        raise NotImplementedError("use `remove_particle` instead")

    def add_particle(self, particle):
        """
        Add a particle.
        """
        if not isinstance(particle, Particle):
            raise ValueError(f"expected Particle, got {type(particle).__name__}")

        self.children.append(particle)
        particle.update_geometry(self.dim)

    def add_particles(self, *particles):
        """
        Add particles.
        """
        if len(particles) == 1 and not isinstance(particles[0], Particle):
            # Assume item is an iterable of particles.
            particles = particles[0]

        for particle in particles:
            self.add_particle(particle)

    def remove_particle(self, particle):
        """
        Remove a particle.
        """
        self.children.remove(particle)

    def _render_child(self, child):
        raise NotImplementedError

    def render(self):
        """
        Paint canvas.
        """
        canvas = self.canvas
        colors = self.colors

        h, w = canvas.shape

        canvas[:] = " "
        colors[:, :] = self.default_color
        pos = top, left = child.top, chld.left

        for child in self.children:
            if (
                child.is_visible
                and not (child.is_transparent and child.char == " ")
                and 0 <= top < h
                and 0 <= left < w
            ):
                canvas[pos] = child.char
                colors[pos] = child.color

    def dispatch_press(self, key_press):
        """
        Try to handle key press; if not handled, dispatch event to ancestors until handled.
        """
        return (
            self.on_press(key_press)
            or any(particle.on_press(key_press) for particle in reversed(self.children))
        )

    def dispatch_click(self, mouse_event):
        return (
            self.on_click(mouse_event)
            or any(particle.on_click(key_press) for particle in reversed(self.children))
        )


class Particle:
    """
    A 1x1 TUI element that's Widget-like, except it has no canvas and no children.
    `Particle`s require a `ParticleField` parent to render them.
    """
    def __init__(
        self,
        pos=(0, 0),
        *,
        char=" ",
        color=WHITE_ON_BLACK,
        is_transparent=False,
        is_visible=True,
    ):
        self.char = char
        self.color = color

        self.top, self.left = pos
        self.is_transparent = is_transparent
        self.is_visible = is_visible

    def update_geometry(self, parent_dim):
        """
        Update geometry due to a change in parent's size.
        """

    @property
    def pos(self):
        return self.top, self.left

    @property
    def dim(self):
        return 1, 1

    def on_press(self, key_press):
        """
        Handle key press.
        """

    def on_click(self, mouse_event):
        """
        Handle mouse event.
        """

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
        attrs = self.attrs

        h, w = canvas.shape

        canvas[:] = " "
        attrs[:, :] = self.default_color

        for child in self.children:
            if (
                child.is_visible
                and (not child.is_transparent or child.char != " ")
                and 0 <= child.top < h
                and 0 <= child.left < w
            ):
                canvas[ct, cl] = child.char
                attrs[ct, cl] = child.attr


class Particle:
    """
    A 1x1 TUI element that implements much of the `Widget` api, except it has no canvas.
    `Particle`s require a `ParticleField` parent to render them.
    """
    def __init__(
        self,
        pos=(0, 0),
        *,
        char=" ",
        attr=WHITE_ON_BLACK,
        is_transparent=False,
        is_visible=True,
    ):
        self.char = char
        self.attr = attr

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

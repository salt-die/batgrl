# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "moderngl",
# ]
# ///
"""Shadertoy https://www.shadertoy.com/view/3XXSDB by XorDev using moderngl."""

import asyncio
import time

import moderngl
import numpy as np
from batgrl.app import App
from batgrl.gadgets.graphics import Graphics, scale_geometry

VERTEX_SHADER = """
#version 330 core

out vec2 position;

void main() {
    vec2 vertices[3] = vec2[3](vec2(-1, -1), vec2(3, -1), vec2(-1, 3));
    gl_Position = vec4(vertices[gl_VertexID], 0, 1);
    position = gl_Position.xy * 0.5 + 0.5;
}
"""
FRAGMENT_SHADER = """
#version 330 core

in vec2 position;

uniform float iTime;
uniform vec2 iResolution;
uniform vec4 iMouse;

vec4 mainImage(in vec2 I) {
    float t = iTime, i, z, d;
    vec4 O;
    for(O *= i; i++ < 1e2; O += (sin(z + vec4(2, 3, 4, 0)) + 1.1) / d)
    {
        vec3 p = z * normalize(vec3(I + I, 0) - iResolution.xyy);
        p.z += iMouse.x / iResolution.x * 20.;
        p.xz *= mat2(cos(p.y * .5 + vec4(0, 33, 11, 0)));
        for(d = 1.; d < 9.; d /= .8) p += cos((p.yzx - t * vec3(3, 1, 0)) * d) / d;
        z += d = (.1 + abs(length(p.xz) - .5)) / 2e1;
    }
    return tanh(O / 4e3);
}

void main() {
    gl_FragColor = mainImage(position * iResolution);
}
"""


class GlGraphics(Graphics):
    def __init__(self, *args, **kwargs):
        self.context = moderngl.create_context(standalone=True)
        self.program = self.context.program(
            vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER
        )
        super().__init__(*args, **kwargs)
        self.start = time.perf_counter()
        self.vao = self.context.vertex_array(self.program, [])
        self.vao.vertices = 3
        self.on_size()  # Create fbo

    def on_size(self):
        super().on_size()
        h, w = self.texture.shape[:2]
        self.program["iResolution"] = w, h
        self.fbo = self.context.simple_framebuffer((w, h), components=4, dtype="f4")
        self.fbo.use()

    def update(self):
        self.program["iTime"].value = time.perf_counter() - self.start
        self.vao.render()
        fbo_read = self.fbo.read(components=4, dtype="f4")
        h, w = self.texture.shape[:2]
        self.texture[::-1] = (
            (np.frombuffer(fbo_read, dtype="f4") * 255)
            .astype(np.uint8)
            .reshape(h, w, 4)
        )

    def on_mouse(self, mouse_event):
        y, x = scale_geometry(self.blitter, mouse_event.pos)
        y = self.texture.shape[0] - y
        w = mouse_event.button != "no_button"
        self.program["iMouse"] = x, y, w, w
        return w


class ModernGlApp(App):
    async def on_start(self):
        graphics = GlGraphics(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            blitter="sextant",
            is_transparent=False,
        )
        self.add_gadget(graphics)

        while True:
            graphics.update()
            await asyncio.sleep(0)


ModernGlApp().run()

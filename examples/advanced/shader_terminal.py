# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "moderngl",
# ]
# ///
"""Shadertoy example: https://www.shadertoy.com/view/WfcGWj using moderngl."""

import asyncio
import time

import moderngl
import numpy as np
from batgrl.app import App
from batgrl.gadgets.graphics import Graphics
from batgrl.texture_tools import resize_texture

VERTEX_SHADER = """
    out vec2 position;
    void main() {
        vec2 vertices[3] = vec2[3](vec2(-1, -1), vec2(3, -1), vec2(-1, 3));
        gl_Position = vec4(vertices[gl_VertexID], 0, 1);
        position = gl_Position.xy * 0.5 + 0.5;
    }
"""
FRAGMENT_SHADER = """
in vec2 position;

uniform vec2 iResolution;
uniform float iTime;

float g(vec4 p,float s) {
  p.x = -abs(p.x);
  return abs(dot(sin(p *= s),cos(p.zxwy)) - 1.) / s;
}

vec4 mainImage(in vec2 uv) {
  float i, d, z, s, T = iTime * 5;
  vec4 o, q, p, U = vec4(2, 1, 0, 3);
  for (
    vec2 r = iResolution.xy;
    ++i < 79.;
    z += d + 5E-4
    , q = vec4(normalize(vec3(uv - .5 * r, r.y)) * z, .2)
    , q.z += T / 3E1
    , s = q.y + .1
    , q.y = abs(s)
    , p = q
    , p.y -= .11
    , p.xy *= mat2(cos(11. * U.zywz - 2. * p.z))
    , p.y -= .2
    , d = abs(g(p, 8.) - g(p, 24.)) / 4.
    , p = 1. + cos(.7 * U + 5. * q.z)
  )
    o += (s > 0. ? 1. : .1) * p.w * p / max(s > 0. ? d : d*d*d, 5E-4);

  o += (1.4 + sin(T) * sin(1.7 * T) * sin(2.3 * T)) * 1E3 * U / length(q.xy);

  return tanh(o / 1E5);
}

void main() {
    gl_FragColor = mainImage(position * iResolution);
}
"""
context = moderngl.create_context(standalone=True)
program = context.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)
program["iResolution"] = width, height = 640, 480
fbo = context.simple_framebuffer((width, height), components=4, dtype="f4")
fbo.use()
vao = context.vertex_array(program, [])
vao.vertices = 3


class ModernGlApp(App):
    async def on_start(self):
        graphics = Graphics(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            is_transparent=False,
            blitter="sextant",
        )
        self.add_gadget(graphics)

        start = time.perf_counter()
        while True:
            program["iTime"].value = time.perf_counter() - start
            vao.render()

            fbo_read = fbo.read(components=4, dtype="f4")
            output = (
                (np.frombuffer(fbo_read, dtype="f4") * 255)
                .astype(np.uint8)
                .reshape(height, width, 4)
            )
            resize_texture(
                output[::-1], graphics.texture.shape[:2], out=graphics.texture
            )
            await asyncio.sleep(0)


ModernGlApp().run()

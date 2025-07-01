# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "moderngl",
# ]
# ///
"""
A shader example with transparency.

A combination of two shadertoys:
- https://www.shadertoy.com/view/t3t3DN by szd
- https://www.shadertoy.com/view/mdjGWG by kishimisu

Your terminal font will need to support octants else `Plasma` blitter needs to change to
something more suitable. Requires `moderngl`.
"""

import asyncio
import time

import moderngl
import numpy as np
from batgrl.app import App
from batgrl.gadgets.graphics import Graphics, scale_geometry
from batgrl.gadgets.text import Text

VERTEX_SHADER = """
#version 460 core

out vec2 position;

void main() {
    vec2 vertices[3] = vec2[3](vec2(-1, -1), vec2(3, -1), vec2(-1, 3));
    gl_Position = vec4(vertices[gl_VertexID], 0, 1);
    position = gl_Position.xy * 0.5 + 0.5;
}
"""
LASER_SHADER = """
#version 460 core

in vec2 position;
uniform float iTime;
uniform vec2 iResolution;

vec3
hsv2rgb(vec3 c) {
    vec3 rgb = abs(mod(c.x * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0;
    rgb = clamp(rgb, 0.0, 1.0);
    rgb = rgb * rgb * (3.0 - 2.0 * rgb);
    return c.z * mix(vec3(1.0), rgb, c.y);
}

float
organicZone(vec2 p) {
    float z = sin(p.y * 3.5 + p.x * 2.0 + iTime * 0.8);
    z += sin(p.y * 8.0 - p.x * 2.5 + iTime * 1.0) * 0.5;
    return z * 0.5;
}

vec3
getcolor(vec2 uv, float baseHue) {
    float zoneOff = organicZone(uv);
    float hue = mod(baseHue + zoneOff * 0.1, 1.);
    float sat = 0.8;
    float val = 0.3;
    return hsv2rgb(vec3(hue, sat, val));
}

float
rand(float seed) {
    seed = fract(seed * 0.1031);
    seed *= seed + 33.33;
    seed *= seed + seed;
    return fract(seed);
}

vec4
mainImage(in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    const float count = 10.0;
    vec3 final_col = vec3(0.0);
    float overlap = 0.0;
    for (float i = 0.0; i < count; i++) {
        vec3 col = getcolor(uv, 0.75);
        vec2 pos = vec2(
            sin(rand(i) / 1.137938 + sin(rand(i) + 2.2373194 * iTime / 1.5)) * 0.4 + 0.5
        );
        float radius = mix(0.0, 0.02, 0.5 + 0.01 * sin(uv.x));
        float c = radius / abs(uv.x - pos.x);
        final_col += (c * col);
    }
    return clamp(vec4(final_col, 1.0), 0.0, 1.0);
}

void
main() {
    gl_FragColor = mainImage(position * iResolution);
}
"""
PLASMA_SHADER = """
#version 460 core

in vec2 position;
uniform float iTime;
uniform vec2 iResolution;
uniform vec4 iMouse;
uniform sampler2D iChannel0;

#define NUM_RAYS 25.
#define VOLUMETRIC_STEPS 19
#define MAX_ITER 35
#define FAR 6.
#define time iTime * 1.1

mat2
mm2(in float a) {
    float c = cos(a), s = sin(a); return mat2(c, -s, s, c);
}

float
noise(in float x) {
    return textureLod(iChannel0, vec2(x * .01, 1.), 0.0).x;
}

float
hash(float n) {
    return fract(sin(n) * 43758.5453);
}

float
noise(in vec3 p) {
	vec3 ip = floor(p);
    vec3 fp = fract(p);
	fp = fp * fp * (3.0 - 2.0 * fp);
	vec2 tap = (ip.xy + vec2(37.0, 17.0) * ip.z) + fp.xy;
	vec2 rg = textureLod(iChannel0, (tap + 0.5) / 256.0, 0.0).yx;
	return mix(rg.x, rg.y, fp.z);
}

mat3 m3 = mat3(0.00,  0.80,  0.60, -0.80,  0.36, -0.48, -0.60, -0.48,  0.64);

float
flow(in vec3 p, in float t) {
	float z=2.;
	float rz = 0.;
	vec3 bp = p;
	for (float i=1.; i < 5.; i++) {
		p += time*.1;
		rz+= (sin(noise(p + t * 0.8) * 6.) * 0.5 + 0.5) / z;
		p = mix(bp, p, 0.6);
		z *= 2.;
		p *= 2.01;
        p*= m3;
	}
	return rz;
}

float
sins(in float x) {
    float rz = 0.;
    float z = 2.;
    for (float i=0.; i < 3.; i++) {
        rz += abs(fract(x * 1.4) - 0.5) / z;
        x *= 1.3;
        z *= 1.15;
        x -= time * .65 * z;
    }
    return rz;
}

float
segm(vec3 p, vec3 a, vec3 b) {
    vec3 pa = p - a;
	vec3 ba = b - a;
	float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.);
	return length(pa - ba * h) * .5;
}

vec3
path(in float i, in float d, vec3 hit) {
    vec3 en = vec3(0., 0., 1.);
    float sns2 = sins(d + i * 0.5) * 0.22;
    float sns = sins(d + i * .6) * 0.21;

    if (dot(hit, hit) > 0.) {
        hit.xz *= mm2(sns2 * .5);
        hit.xy *= mm2(sns * .3);
        return hit;
    }

    en.xz *= mm2((hash(i * 10.569) - .5) * 6.2 + sns2);
    en.xy *= mm2((hash(i * 4.732) - .5) * 6.2 + sns);

    return en;
}

vec2
map(vec3 p, float i, vec3 hit) {
    vec3 p0 = p;
	float lp = length(p);
    vec3 bg = vec3(0.);
    vec3 en = path(i, lp, hit);
    float ins = smoothstep(0.11, .46, lp);
    float outs = .15 + smoothstep(.0, .15, abs(lp - 1.));
    p *= ins * outs;
    float id = ins * outs;
    float rz = segm(p, bg, en) - 0.011;
    return vec2(rz, id);
}

float
march(in vec3 ro, in vec3 rd, in float startf, in float maxd, in float j, vec3 hit) {
	float precis = 0.001;
    float h=0.5;
    float d = startf;
    for(int i=0; i < MAX_ITER; i++) {
        if(abs(h) < precis || d > maxd) break;
        d += h * 1.2;
        float res = map(ro + rd*d, j, hit).x;
        h = res;
    }
	return d;
}

vec3
vmarch(in vec3 ro, in vec3 rd, in float j, in vec3 orig, vec3 hit) {
    vec3 p = ro;
    vec2 r = vec2(0.);
    vec3 sum = vec3(0);
    float w = 0.;
    for(int i=0; i < VOLUMETRIC_STEPS; i++) {
        r = map(p, j, hit);
        p += rd * .03;
        float lp = length(p);
        vec3 col = sin(vec3(1.05, 2.5, 1.52) * 3.94 + r.y) * .85 + 0.4;
        col.rgb *= smoothstep(.0, .015, -r.x);
        col *= smoothstep(0.04, .2, abs(lp - 1.1));
        col *= smoothstep(0.1, .34, lp);
        sum += (
            abs(col) * 5. * (1.2 - noise(lp * 2. + j * 13. + time * 5.) * 1.1)
            / (log(distance(p, orig) - 2.) + .75)
        );
    }
    return sum;
}

vec2
iSphere2(in vec3 ro, in vec3 rd) {
    vec3 oc = ro;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - 1.;
    float h = b * b - c;
    if (h < 0.0) return vec2(-1.);
    else return vec2((-b - sqrt(h)), (-b + sqrt(h)));
}

vec4
mainImage(in vec2 fragCoord) {
	vec2 p = fragCoord.xy / iResolution.xy - 0.5;
	p.x *= iResolution.x / iResolution.y;
	vec2 um = iMouse.xy / iResolution.xy - .5;
    um.x *= iResolution.x / iResolution.y;
	vec3 ro = vec3(0., 0., 5.);
    vec3 rd = normalize(vec3(p * .7,-1.5));
    mat2 mx = mm2(time * .4);
    mat2 my = mm2(time * 0.3);
    ro.xz *= mx;
    rd.xz *= mx;
    ro.xy *= my;
    rd.xy *= my;
    vec2 sph = iSphere2(ro, rd);
    if (sph.x < 0.) return vec4(0., 0., 0., 0.);
    vec3 bro = ro;
    vec3 brd = rd;
    vec3 col = vec3(0.0125, 0., 0.025);
    for (float j = 1.; j < NUM_RAYS + 1.; j++) {
        ro = bro;
        rd = brd;
        mat2 mm = mm2((time * 0.1 + ((j + 1.) * 5.1)) * j * 0.25);
        float rz = march(ro, rd, 2.5, FAR, j, vec3(0.));
		if (rz >= FAR) continue;
        vec3 pos = ro + rz * rd;
        col = max(col, vmarch(pos, rd, j, bro, vec3(0.)));
    }
    vec3 hit = vec3(0.);
    vec3 rdm = normalize(vec3(um * .7, -1.5));
    rdm.xz *= mx;
    rdm.xy *= my;
    if (iMouse.z > 0.) {
        vec2 res = iSphere2(bro, rdm);
        if (res.x > 0.) hit = bro + res.x * rdm;
    }
    if (dot(hit, hit) != 0.) {
        float j = NUM_RAYS + 1.;
        ro = bro;
        rd = brd;
        mat2 mm = mm2((time * 0.1 + ((j + 1.) * 5.1)) * j * 0.25);
        float rz = march(ro, rd, 2.5, FAR, j, hit);
		if (rz < FAR) {
            vec3 pos = ro + rz * rd;
            col = max(col, vmarch(pos, rd, j, bro, hit));
        }
    }
    ro = bro;
    rd = brd;
    vec3 pos = ro + rd * sph.x;
    vec3 pos2 = ro + rd * sph.y;
    vec3 rf = reflect(rd, pos);
    vec3 rf2 = reflect(rd, pos2);
    float nz = -log(abs(flow(rf * 1.2, time) - .01));
    float nz2 = -log(abs(flow(rf2 * 1.2, -time) - .01));
    col += (
        0.1 * nz * nz * vec3(0.12, 0.12, .5)
        + 0.05 * nz2 * nz2 * vec3(0.55, 0.2, .55)
    ) * 0.8;
    return clamp(vec4(col * 1.3, .78), 0.0, 1.0);
}

void
main() {
    gl_FragColor = mainImage(position * iResolution);
}
"""
context = moderngl.create_context(standalone=True)
default_rng = np.random.default_rng()


class Lasers(Text):
    def __init__(self, *args, **kwargs):
        self.program = context.program(
            vertex_shader=VERTEX_SHADER, fragment_shader=LASER_SHADER
        )
        super().__init__(*args, **kwargs)
        self.start = time.perf_counter()
        self.vao = context.vertex_array(self.program, [])
        self.vao.vertices = 3
        self.on_size()  # Create fbo

    def on_size(self):
        super().on_size()
        h, w = self.canvas.shape
        for y in range(h):
            for x in range(w):
                self.chars[y, x] = "batgrl "[(y + x) % 7]
        self.program["iResolution"] = w, h
        self.fbo = context.simple_framebuffer((w, h), components=4, dtype="f4")

    def update(self):
        self.program["iTime"].value = time.perf_counter() - self.start
        self.fbo.use()
        self.vao.render()
        fbo_read = self.fbo.read(components=3, dtype="f4")
        h, w = self.canvas.shape
        self.canvas["fg_color"][::-1] = (
            (np.frombuffer(fbo_read, dtype="f4") * 255)
            .astype(np.uint8)
            .reshape(h, w, 3)
        )


class Plasma(Graphics):
    def __init__(self, *args, **kwargs):
        self.program = context.program(
            vertex_shader=VERTEX_SHADER, fragment_shader=PLASMA_SHADER
        )
        super().__init__(*args, **kwargs)
        self.start = time.perf_counter()
        self.vao = context.vertex_array(self.program, [])
        self.vao.vertices = 3
        self.sampler = context.texture(
            (256, 256), 4, data=default_rng.integers(0, 256, (256, 256, 4), np.uint8)
        )
        self.sampler.use()
        self.on_size()  # Create fbo

    def on_size(self):
        super().on_size()
        h, w = self.texture.shape[:2]
        self.program["iResolution"] = w, h
        self.fbo = context.simple_framebuffer((w, h), components=4, dtype="f4")

    def update(self):
        self.program["iTime"].value = time.perf_counter() - self.start
        self.fbo.use()
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


class ModernGlApp(App):
    async def on_start(self):
        lasers = Lasers(size_hint={"height_hint": 1.0, "width_hint": 1.0})
        plasma = Plasma(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            # try `blitter="sextant"` if terminal font doesn't support octants
            blitter="octant",
        )
        self.add_gadgets(lasers, plasma)

        while True:
            lasers.update()
            plasma.update()
            await asyncio.sleep(0)


if __name__ == "__main__":
    ModernGlApp().run()

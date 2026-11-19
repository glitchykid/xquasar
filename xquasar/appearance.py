"""The XQuasar palette and resolution-independent quasar illustration."""

import math
from pathlib import Path
import random

import cairo
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GdkPixbuf, Gtk


ASSETS = Path(__file__).parent
_provider = None


def styled(widget, name):
    widget.get_style_context().add_class(name)
    return widget


def load_theme(window):
    global _provider
    if _provider is None:
        provider = Gtk.CssProvider()
        provider.load_from_path(str(ASSETS / "window.css"))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
                                                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        _provider = provider
    styled(window, "quasar")
    icon = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(ASSETS / "xquasar.svg"), 64, 64, True)
    window.set_icon(icon)


def glow(ctx, x, y, radius, color, opacity):
    gradient = cairo.RadialGradient(x, y, 0, x, y, radius)
    gradient.add_color_stop_rgba(0, *color, opacity)
    gradient.add_color_stop_rgba(0.42, *color, opacity * 0.35)
    gradient.add_color_stop_rgba(1, *color, 0)
    ctx.set_source(gradient)
    ctx.rectangle(x - radius, y - radius, 2 * radius, 2 * radius)
    ctx.fill()


def draw_quasar(widget, ctx):
    w, h = widget.get_allocated_width(), widget.get_allocated_height()
    radius = 13
    for x, y, angle in ((w-radius, radius, -90), (w-radius, h-radius, 0),
                        (radius, h-radius, 90), (radius, radius, 180)):
        ctx.arc(x, y, radius, math.radians(angle), math.radians(angle+90))
    ctx.close_path()
    ctx.clip()
    gradient = cairo.LinearGradient(0, 0, w, h)
    gradient.add_color_stop_rgb(0, 0.085, 0.11, 0.18)
    gradient.add_color_stop_rgb(0.55, 0.075, 0.07, 0.16)
    gradient.add_color_stop_rgb(1, 0.12, 0.075, 0.21)
    ctx.set_source(gradient)
    ctx.paint()
    rng = random.Random(591)
    for _ in range(165):
        x, y = rng.random()*w, rng.random()*h
        ctx.set_source_rgba(0.86, 0.89, 1, rng.uniform(0.18, 0.72) * min(1, x/w + 0.25))
        ctx.arc(x, y, rng.uniform(0.32, 1.05), 0, math.tau)
        ctx.fill()

    ctx.save()
    ctx.translate(w*0.77, h*0.53)
    scale = min(w/650, h/175)
    ctx.scale(scale, scale)
    ctx.rotate(-0.21)
    glow(ctx, 0, 0, 142, (0.49, 0.34, 0.94), 0.46)
    # The two jets fade along the rotation axis. The disk is seen edge-on.
    for sign in (-1, 1):
        ctx.save()
        ctx.scale(sign, sign)
        jet = cairo.LinearGradient(0, 0, 16, -100)
        jet.add_color_stop_rgba(0, 0.82, 0.85, 1, 0.78)
        jet.add_color_stop_rgba(0.5, 0.62, 0.57, 1, 0.19)
        jet.add_color_stop_rgba(1, 0.47, 0.41, 0.94, 0)
        ctx.set_source(jet)
        ctx.move_to(-7, 0)
        ctx.curve_to(0, -32, 6, -57, 18, -111)
        ctx.curve_to(23, -49, 6, -26, 7, 0)
        ctx.fill()
        ctx.restore()
    ctx.save()
    ctx.scale(1, 0.225)
    glow(ctx, 0, 0, 166, (0.74, 0.55, 1), 0.92)
    ctx.restore()
    for i in range(86):
        distance = 16 + i*1.38
        alpha = 0.58 * (1-i/90) * rng.uniform(0.35, 1.0)
        ctx.save()
        ctx.scale(1, 0.19 + 0.035*math.sin(i*0.13))
        ctx.set_source_rgba(0.84, 0.70+i/460, 1, alpha)
        ctx.set_line_width(rng.uniform(0.55, 1.7))
        ctx.arc(0, 0, distance, 0, math.tau)
        ctx.stroke()
        ctx.restore()
    glow(ctx, 0, 0, 29, (0.88, 0.84, 1), 1.0)
    ctx.set_source_rgb(0.98, 0.97, 1)
    ctx.arc(0, 0, 5, 0, math.tau)
    ctx.fill()
    ctx.restore()
    return False

#!/usr/bin/env python3
"""生成热点猎手应用图标（APK / 桌面窗口 / 任务栏）。"""

from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as exc:  # pragma: no cover
    raise SystemExit("请先安装 Pillow: pip install pillow") from exc

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SIZE = 1024
# iOS 风格主色（与 src/config.py THEME 一致）
PRIMARY = (10, 132, 255)
PRIMARY_DARK = (0, 102, 204)
FLAME_TOP = (255, 159, 10)
FLAME_BOTTOM = (255, 69, 58)


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def vertical_gradient(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size))
    px = img.load()
    assert px is not None
    for y in range(size):
        t = y / (size - 1)
        r = lerp(PRIMARY[0], PRIMARY_DARK[0], t)
        g = lerp(PRIMARY[1], PRIMARY_DARK[1], t)
        b = lerp(PRIMARY[2], PRIMARY_DARK[2], t)
        for x in range(size):
            px[x, y] = (r, g, b, 255)
    return img


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def draw_radar(draw: ImageDraw.ImageDraw, cx: int, cy: int) -> None:
    for radius, width, alpha in ((300, 10, 70), (220, 8, 90), (140, 6, 110)):
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            outline=(255, 255, 255, alpha),
            width=width,
        )
    # 十字准星
    arm = 360
    draw.line((cx - arm, cy, cx + arm, cy), fill=(255, 255, 255, 80), width=6)
    draw.line((cx, cy - arm, cx, cy + arm), fill=(255, 255, 255, 80), width=6)


def draw_flame(draw: ImageDraw.ImageDraw, cx: int, cy: int) -> None:
    # 外焰
    outer = [
        (cx, cy - 190),
        (cx + 95, cy + 40),
        (cx + 55, cy + 150),
        (cx, cy + 110),
        (cx - 55, cy + 150),
        (cx - 95, cy + 40),
    ]
    draw.polygon(outer, fill=(*FLAME_TOP, 230))
    # 内焰
    inner = [
        (cx, cy - 130),
        (cx + 52, cy + 20),
        (cx + 28, cy + 95),
        (cx, cy + 70),
        (cx - 28, cy + 95),
        (cx - 52, cy + 20),
    ]
    draw.polygon(inner, fill=(*FLAME_BOTTOM, 240))
    # 高光
    draw.ellipse((cx - 22, cy - 95, cx + 8, cy - 55), fill=(255, 255, 255, 120))


def draw_sweep(draw: ImageDraw.ImageDraw, cx: int, cy: int) -> None:
    """雷达扫描扇形。"""
    bbox = (cx - 300, cy - 300, cx + 300, cy + 300)
    draw.pieslice(bbox, start=300, end=360, fill=(255, 255, 255, 35))


def build_icon(size: int = SIZE, *, padding: float = 0.0) -> Image.Image:
    base = vertical_gradient(size)
    mask = rounded_mask(size, int(size * 0.223))
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(base, (0, 0), mask)

    if padding > 0:
        inner = int(size * (1 - padding * 2))
        layer = Image.new("RGBA", (inner, inner), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer, "RGBA")
        cx = cy = inner // 2
        ratio = inner / SIZE
        draw_sweep(draw, cx, cy - int(20 * ratio))
        draw_radar(draw, cx, cy - int(20 * ratio))
        draw_flame(draw, cx, cy + int(30 * ratio))
        offset = (size - inner) // 2
        canvas.alpha_composite(layer, (offset, offset))
    else:
        draw = ImageDraw.Draw(canvas, "RGBA")
        cx = cy = size // 2
        draw_sweep(draw, cx, cy - int(20 * (size / SIZE)))
        draw_radar(draw, cx, cy - int(20 * (size / SIZE)))
        draw_flame(draw, cx, cy + int(30 * (size / SIZE)))
    return canvas


def save_png(path: Path, img: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG", optimize=True)
    print(f"  wrote {path} ({img.size[0]}x{img.size[1]})")


def main() -> None:
    print(f"Generating icons → {ASSETS}")
    master = build_icon(SIZE, padding=0.0)
    save_png(ASSETS / "icon.png", master)
    # Android adaptive 前景：略留边距
    save_png(ASSETS / "icon_android.png", build_icon(SIZE, padding=0.08))
    save_png(ASSETS / "icon_ios.png", master)
    save_png(ASSETS / "icon_windows.png", master)
    print("Done.")


if __name__ == "__main__":
    main()

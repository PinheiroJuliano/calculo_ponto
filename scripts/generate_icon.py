"""Gera os icones do aplicativo em PNG e ICO com multiplas resolucoes."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SIZES = (16, 24, 32, 48, 64, 128, 256)


def draw_clock(size: int) -> Image.Image:
    scale = 4
    canvas_size = size * scale
    image = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin = round(canvas_size * 0.07)
    outline = max(scale, round(canvas_size * 0.045))
    center = canvas_size // 2

    draw.ellipse(
        (margin, margin, canvas_size - margin, canvas_size - margin),
        fill=(20, 24, 36, 255),
        outline=(0, 220, 255, 255),
        width=outline,
    )

    tick_width = max(scale, round(canvas_size * 0.018))
    for x1, y1, x2, y2 in (
        (center, margin * 2, center, margin * 3),
        (center, canvas_size - margin * 2, center, canvas_size - margin * 3),
        (margin * 2, center, margin * 3, center),
        (canvas_size - margin * 2, center, canvas_size - margin * 3, center),
    ):
        draw.line((x1, y1, x2, y2), fill=(170, 185, 205, 255), width=tick_width)

    hand_width = max(scale * 2, round(canvas_size * 0.045))
    # Ponteiros marcando 10:10, uma silhueta reconhecivel mesmo em 16 px.
    draw.line(
        (center, center, round(canvas_size * 0.30), round(canvas_size * 0.31)),
        fill=(255, 255, 255, 255),
        width=hand_width,
    )
    draw.line(
        (center, center, round(canvas_size * 0.69), round(canvas_size * 0.23)),
        fill=(255, 255, 255, 255),
        width=hand_width,
    )
    hub = round(canvas_size * 0.055)
    draw.ellipse(
        (center - hub, center - hub, center + hub, center + hub),
        fill=(255, 190, 50, 255),
    )

    return image.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    images = [draw_clock(size) for size in SIZES]
    images[-1].save(ASSETS / "clock.png", optimize=True)
    images[-1].save(
        ASSETS / "clock.ico",
        format="ICO",
        sizes=[(size, size) for size in SIZES],
    )
    print(f"Icones gerados em {ASSETS}")


if __name__ == "__main__":
    main()

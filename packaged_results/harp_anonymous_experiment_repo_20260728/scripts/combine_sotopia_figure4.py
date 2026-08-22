"""Combine the two SOTOPIA Figure 4 panels into one image/PDF file."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_NAME = "fig_sotopia_combined_v1"


def load_panel(name: str) -> Image.Image:
    candidates = [
        ROOT / "figs" / f"{name}.png",
        ROOT / "arr_paper" / "figs" / f"{name}.png",
        ROOT / "arr_paper_overleaf" / "figs" / f"{name}.png",
    ]
    for path in candidates:
        if path.exists():
            return Image.open(path).convert("RGB")
    raise FileNotFoundError(f"Could not find {name}.png in known figure directories")


def resize_to_width(image: Image.Image, width: int) -> Image.Image:
    if image.width == width:
        return image
    height = round(image.height * width / image.width)
    return image.resize((width, height), Image.Resampling.LANCZOS)


def draw_panel_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], label: str) -> None:
    try:
        font = ImageFont.truetype("arial.ttf", 38)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), label, font=font)
    box_w = bbox[2] - bbox[0] + 18
    box_h = bbox[3] - bbox[1] + 12
    x, y = xy
    draw.rounded_rectangle(
        (x, y, x + box_w, y + box_h),
        radius=6,
        fill=(255, 255, 255),
        outline=(80, 80, 80),
        width=1,
    )
    draw.text((x + 9, y + 5), label, fill=(20, 20, 20), font=font)


def main() -> None:
    top = load_panel("fig_sotopia_three_exp_v1")
    bottom = load_panel("fig_sotopia_traj_v1")
    width = max(top.width, bottom.width)
    top = resize_to_width(top, width)
    bottom = resize_to_width(bottom, width)
    gap = 34
    pad = 24
    # The trajectory panel has a long y-axis label, so its plotting area starts
    # farther to the right. Shift the top panel so the plotted axes align.
    top_x_offset = 160
    label_col = 82
    content_x = pad + label_col
    canvas_width = max(content_x + top_x_offset + top.width, content_x + bottom.width) + pad
    combined = Image.new("RGB", (canvas_width, top.height + bottom.height + gap + 2 * pad), "white")
    combined.paste(top, (content_x + top_x_offset, pad))
    combined.paste(bottom, (content_x, pad + top.height + gap))
    draw = ImageDraw.Draw(combined)
    draw_panel_label(draw, (pad, pad + 16), "(a)")
    draw_panel_label(draw, (pad, pad + top.height + gap + 16), "(b)")

    out_dirs = [ROOT / "figs", ROOT / "arr_paper" / "figs", ROOT / "arr_paper_overleaf" / "figs"]
    for out_dir in out_dirs:
        out_dir.mkdir(parents=True, exist_ok=True)
    out_png = ROOT / "figs" / f"{OUT_NAME}.png"
    out_pdf = ROOT / "figs" / f"{OUT_NAME}.pdf"
    combined.save(out_png)
    combined.save(out_pdf, "PDF", resolution=240.0)
    for out_dir in out_dirs[1:]:
        shutil.copy2(out_png, out_dir / out_png.name)
        shutil.copy2(out_pdf, out_dir / out_pdf.name)
    print(f"wrote {out_pdf}")
    print(f"wrote {out_png}")


if __name__ == "__main__":
    main()
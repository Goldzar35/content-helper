"""Build Content Helper.app — run with: python3 build_app.py"""
import os
import subprocess
import sys
from pathlib import Path

def make_icon():
    from PIL import Image, ImageDraw, ImageFont

    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def rounded_rect(draw, xy, radius, fill):
        x0, y0, x1, y1 = xy
        draw.rectangle([x0+radius, y0, x1-radius, y1], fill=fill)
        draw.rectangle([x0, y0+radius, x1, y1-radius], fill=fill)
        for cx, cy in [(x0,y0),(x1-radius*2,y0),(x0,y1-radius*2),(x1-radius*2,y1-radius*2)]:
            draw.ellipse([cx, cy, cx+radius*2, cy+radius*2], fill=fill)

    rounded_rect(draw, (0, 0, 1024, 1024), 180, (20, 20, 20, 255))

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 420)
    except Exception:
        font = ImageFont.load_default()

    text = "CH"
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (size - (bbox[2] - bbox[0])) // 2 - bbox[0]
    y = (size - (bbox[3] - bbox[1])) // 2 - bbox[1]
    draw.text((x, y), text, fill=(212, 160, 23, 255), font=font)
    img.save("icon_1024.png")

    iconset = Path("icon.iconset")
    iconset.mkdir(exist_ok=True)
    for s in [16, 32, 64, 128, 256, 512, 1024]:
        img.resize((s, s), Image.LANCZOS).save(iconset / f"icon_{s}x{s}.png")
        if s <= 512:
            img.resize((s*2, s*2), Image.LANCZOS).save(iconset / f"icon_{s}x{s}@2x.png")

    subprocess.run(["iconutil", "-c", "icns", "icon.iconset", "-o", "icon.icns"], check=True)
    print("Icon created.")

if __name__ == "__main__":
    print("Building Content Helper.app...")
    make_icon()
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--windowed",
        "--name", "Content Helper",
        "--icon", "icon.icns",
        "--osx-bundle-identifier", "com.goldzar.content-helper",
        "--collect-all", "PyQt6",
        "--noconfirm",
        "main.py",
    ], check=True)

    # Ad-hoc re-sign to fix PAC signature crash on macOS 15+
    print("Signing bundle...")
    subprocess.run([
        "codesign", "--force", "--deep", "--sign", "-",
        "dist/Content Helper.app",
    ], check=True)

    print("\nDone! App is at: dist/Content Helper.app")
    print("To install, run:")
    print("  ditto 'dist/Content Helper.app' ~/Desktop/'Content Helper.app'")
    print("  # or drag dist/Content Helper.app to /Applications")
    print("NOTE: Use 'ditto' not 'cp -r' — cp strips code signatures on macOS.")

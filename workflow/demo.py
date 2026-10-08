"""Tạo tư liệu tổng hợp, không phải hình ảnh thực tế Vinhomes."""
import argparse
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from services.media import import_media
from services.storage import ProjectStore
from services.subtitles import font_path
from services.tools import binary, check_tools, run
from workflow.render import export_project
from workflow.scenes import scene


def create_demo(store):
    check_tools()
    project = store.create("MẪU THỬ · Không phải tư liệu dự án thật")
    project["script"] = "Đây là video thử nghiệm. Tư liệu được tạo bằng máy tính. Hãy thay bằng hình ảnh thực địa đã xác nhận."
    project["settings"].update(title="MẪU THỬ NGHIỆM", cta="Thay bằng tư liệu thực địa", fade=False, script_captions=True)
    with tempfile.TemporaryDirectory(prefix="studio_demo_") as temp:
        directory = Path(temp)
        video = directory / "mau-co-am-thanh.mp4"
        run([binary("ffmpeg"), "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30",
             "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "3",
             "-c:v", "libx264", "-threads", "2", "-pix_fmt", "yuv420p", "-c:a", "aac", video])
        silent = directory / "mau-khong-am-thanh.mov"
        run([binary("ffmpeg"), "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=teal:s=360x640:r=30",
             "-t", "1", "-c:v", "libx264", "-threads", "2", silent])
        image_path = directory / "anh-mau.png"
        image = Image.new("RGB", (640, 360), "#143848")
        ImageDraw.Draw(image).text((40, 130), "ẢNH MẪU · KHÔNG PHẢI DỰ ÁN", fill="white",
                                  font=ImageFont.truetype(str(font_path()), 28))
        image.save(image_path)
        for source in (video, silent, image_path):
            project["media"].append(import_media(store, project, source.name, source.read_bytes()))
    for text, item in zip(project["script"].split(". "), project["media"]):
        current = scene(text, 2)
        current.update(media_id=item["id"], confirmed=True)
        project["scenes"].append(current)
    store.save(project)
    return project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true", help="Xuất ngay bản xem thử 6 giây")
    args = parser.parse_args()
    store = ProjectStore()
    project = create_demo(store)
    print(f"Đã tạo dự án mẫu: {project['id']}")
    if args.export:
        output = export_project(store, project, progress=lambda value, text: print(f"{value:.0%} · {text}"))
        print(f"MP4: {output}")


if __name__ == "__main__":
    main()

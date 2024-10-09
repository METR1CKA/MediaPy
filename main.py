# Imports
from tkinter import Tk, filedialog
import moviepy.editor as editor, os, argparse, sys, yt_dlp


class Logger:
    def debug(self, msg):
        if msg.startswith("[debug] "):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


class Media:
    def downloaderHook(self, d):
        if d["status"] == "finished":
            print("\n[ * ] - Download completed\n")

    def downloader(self, url, filename, path):
        if not filename.endswith(".mp4"):
            filename = f"{filename}.mp4"
        path_video = os.path.join(path, filename)
        if os.path.exists(path_video):
            os.remove(path_video)
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "logger": Logger(),
            "progress_hooks": [self.downloaderHook],
            "outtmpl": path_video,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return path_video

    def converter(self, video, filename, path):
        if not filename.endswith(".mp3"):
            filename = f"{filename}.mp3"
        path_audio = os.path.join(path, filename)
        if os.path.exists(path_audio):
            os.remove(path_audio)
        editor.VideoFileClip(video).audio.write_audiofile(path_audio)
        return path_audio

    def parseArgs(self):
        parser = argparse.ArgumentParser(description="YouTube MediaPy Downloader")
        parser.add_argument(
            "--url",
            "-u",
            type=str,
            help="URL of the video to download",
        )
        parser.add_argument(
            "--name",
            "-n",
            type=str,
            help="Name of the video to save",
        )
        parser.add_argument(
            "--convert-audio",
            "-c",
            action="store_true",
            help="Convert video to audio",
        )
        parser.add_argument(
            "--version",
            "-v",
            action="version",
            version="%(prog)s - v1.0.0",
        )
        parser.add_argument(
            "--only-audio",
            "-oa",
            action="store_true",
            help="Download and convert to get only audio",
        )
        return parser


if __name__ == "__main__":
    media = Media()

    parser = media.parseArgs()

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    if not args.url:
        parser.print_help()
        print("\n[ ! ] - Parameter --url is required...")
        sys.exit(1)

    if not args.name:
        parser.print_help()
        print("\n[ ! ] - Parameter --name is required...")
        sys.exit(1)

    root = Tk()
    root.withdraw()

    selected_path = filedialog.askdirectory()

    if not selected_path:
        print("\n[ ! ] - Route not selected...")
        sys.exit(1)

    if not os.path.exists(selected_path):
        print("\n[ ! ] - Route selected not found")
        sys.exit(1)

    try:
        print("\n[ * ] - Downloading...")
        video = media.downloader(url=args.url, filename=args.name, path=selected_path)
        if args.convert_audio or args.only_audio:
            media.converter(video=video, filename=args.name, path=selected_path)
            if args.only_audio:
                os.remove(video)
    except Exception as e:
        print(f"\n[ ! ] - Error: {e}")
        sys.exit(1)

    sys.exit(0)

from pytube import YouTube

class downloader:

    def __init__(self, url):

        self.url = url

    def videoDownloader(self):

        yt = YouTube(self.url)

        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download()

        return video

    def audioDownloader(self, name):

        yt = YouTube(self.url)

        audio = yt.streams.get_audio_only()

        filename = audio.download(filename = name)

        return filename

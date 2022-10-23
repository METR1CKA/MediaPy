from pytube import YouTube

class downloader:

    def __init__(self, url):

        self.yt = YouTube(url)

    def videoDownloader(self):

        video = self.yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download()

        return video

    def audioDownloader(self, name):

        audio = self.yt.streams.get_audio_only()

        filename = audio.download(filename = name)

        return filename

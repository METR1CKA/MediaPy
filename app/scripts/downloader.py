from pytube import YouTube

class downloader:

    def __init__(self):
        pass


    def videoDownloader(self, url):

        yt = YouTube(url)

        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download()

        return video

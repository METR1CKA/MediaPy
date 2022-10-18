import moviepy.editor as editor

class converter:

    def __init__(self):
        pass


    def videoConverter(self, videoName, audioName):

        clip = editor.VideoFileClip(videoName)

        audio = clip.audio

        audio.write_audiofile(f'{audioName}.mp3')


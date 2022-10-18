import platform as pl
import os, shutil


class files:

    def __init__(self):
        pass

    def getOS(self):
        
        systemInfo = ['system']

        for so in systemInfo:

            if hasattr(pl, so):
                
                return getattr(pl, so)()

    def cleanTerm(self):
        
        name = self.getOS()

        if name == 'Windows':
            
            os.system('cls')

        else:

            os.system('clear')

    def getVideos(self):

        return os.listdir(f'{os.getcwd()}/files/mp4')

    def getVideoFullPath(self, videoName):

        return f'{os.getcwd()}/files/mp4/{videoName}'

    def getAudioFile(self):

        files = os.listdir(os.getcwd())

        files.remove('app')
        files.remove('files')
        files.remove('main.py')
        files.remove('README.md')

        return f'{os.getcwd()}/{files[0]}'

    def order_Files(self, filename, path):

        basename = os.path.basename(filename)
        
        fullpath = f'{os.getcwd()}/{path}/{basename}'

        if os.path.isfile(fullpath):
            
            if basename == os.path.basename(fullpath):

                os.remove(fullpath)

        shutil.move(filename, path, copy_function=shutil.copy)

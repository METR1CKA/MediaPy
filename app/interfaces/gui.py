import time, sys
from app.scripts.downloader import downloader as d
from app.scripts.converter import converter as c
from app.scripts.files import files as f

class gui:

    def __init__(self):

        pass

    def main(self):

        while True:

            f().cleanTerm()

            self.menu()

            time.sleep(1)

            self.process()


    def menu(self):

        print('\n---------- MENU ----------')

        print('\n[*] 1. Descargar video')

        print('\n[*] 2. Convertir video a audio')

        print('\n[*] 3. Salir')

        print('\n--------------------------')


    def abort(self):

        print('\n[-] Saliendo...')

        time.sleep(1)

        f().cleanTerm()

        sys.exit(1)


    def Err(self, e):

        print(f'\n[-] Error: {e}')

        time.sleep(1)

        sys.exit(1)


    def process(self):

        try:

            op = int(input('\n[+] Ingrese una opción: '))

            if op == 1:

                self.videoDownload()

            elif op == 2:

                self.audioConverter()

            elif op == 3:

                self.abort()

        except Exception as e:

            self.Err(e)


    def videoDownload(self):

        f().cleanTerm()

        url = input('\n[+] Ingrese la url: ')

        time.sleep(1)

        print('\n[*] Descargando video...')

        videoName = d().videoDownloader(url)

        f().order_Files(videoName, 'files/mp4')

        print('\n[+] Video descargado con exito!!')

        time.sleep(3)


    def listVideos(self, videos):

        i = 0

        print('\n[*] ---- Videos ---- [*]')

        for video in videos:

            i = i + 1

            print(f'\n[ {i} ] {video}')


    def audioConverter(self):

        f().cleanTerm()

        videos = f().getVideos()

        self.listVideos(videos)

        time.sleep(1)

        whatVideo = int(input('\n[+] Ingrese el numero de video que desea convertir a formato de audio: '))

        videoName = f().getVideoFullPath(videos[whatVideo - 1])

        audioName = input('\n[+] Ingrese el nombre del audio a crear: ')

        time.sleep(1)

        print('\n[*] Convirtiendo su archivo de video a aun archivo de audio...\n')

        c().videoConverter(videoName, audioName)

        f().order_Files(f().getAudioFile(), 'files/mp3')

        print('\n[*] Archivo convertido con exito...')

        time.sleep(1)

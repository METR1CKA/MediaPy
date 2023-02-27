# Imports
from pytube import YouTube
from pathlib import Path
import flet as ft, moviepy.editor as editor, os


# Function for downloader video
def downloader(url, name, handle_error, progress, complete):
    try:
        yt = YouTube(
            url=url, on_progress_callback=progress, on_complete_callback=complete
        )
        filename = str(Path(name).name)
        output_path = str(os.path.split(Path(name))[0])
        video = (
            yt.streams.filter(progressive=True, file_extension="mp4")
            .get_highest_resolution()
            .download(filename=filename, output_path=output_path)
        )
        return video
    except Exception as e:
        handle_error(e)


# Function for converter video to audio
def converter(video, name, handle_error):
    try:
        audio = f"{name}.mp3"
        editor.VideoFileClip(video).audio.write_audiofile(audio)
    except Exception as e:
        handle_error(e)


# Function for main window
def main(page: ft.Page):
    # Function to handle submit
    def handle_submit(e):
        if not url_input.value:
            url_input.error_text = "Please enter URL..."
            page.update()
            return
        if pick_file_dialog.result == None and selected_path.value.lower() == "path":
            selected_path.value = "Please enter path..."
            page.update()
            return
        url_input.error_text = None
        page.update()
        video = downloader(
            url_input.value,
            selected_path.value,
            handle_error,
            in_progress,
            on_complete,
        )
        if button_check.value:
            converter(
                video,
                pick_file_dialog.result.path,
                handle_error,
            )
        page.update()

    # Function to pick file result
    def pick_file_result(e: ft.FilePickerResultEvent):
        selected_path.value = f"{pick_file_dialog.result.path}.mp4"
        page.update()

    # Function to handle errors
    def handle_error(*args):
        download_complete.value = f"Error: {args}"
        download_bar.value = 0
        page.update()

    # Function to mark progress
    def in_progress(*args):
        download_complete.value = "Download in progress..."
        db = ft.ProgressBar(width=250)
        download_bar.value = db.value
        page.update()

    # Function to mark completed progress
    def on_complete(*args):
        download_complete.value = "Download complete!!"
        download_bar.value = 100
        page.update()

    # Window properties
    page.title = "YouTube Media Downloader By METR1CKA"
    page.vertical_alignment = "center"
    page.window_height = 500
    page.window_width = 600
    page.window_max_height = 500
    page.window_min_height = 500
    page.window_max_width = 600
    page.window_min_width = 600

    # Controls (inputs, selectors, buttons)
    url_input = ft.TextField(label="URL:")
    selected_path = ft.Text()
    selected_path.value = "Path"
    download_button = ft.TextButton("Download", on_click=handle_submit)

    # Control picker
    pick_file_dialog = ft.FilePicker(on_result=pick_file_result)
    page.overlay.append(pick_file_dialog)
    pick_file_button = ft.ElevatedButton(
        "Pick file name",
        icon=ft.icons.UPLOAD_FILE,
        on_click=lambda _: pick_file_dialog.save_file(
            file_type="video", allowed_extensions=["mp4"]
        ),
    )

    # Download bar and text
    download_complete = ft.Text()
    download_bar = ft.ProgressBar(width=250)
    download_bar.value = 0

    # Button to convert video to audio
    button_check = ft.Checkbox(label="Convert video to audio", value=False)

    # Add properties to window
    page.add(
        ft.Column(
            [
                ft.Row([url_input], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(
                    [
                        pick_file_button,
                        selected_path,
                    ]
                ),
                ft.Row([button_check]),
                ft.Row([download_button], alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=25,
        ),
        ft.Row([download_complete], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([download_bar], alignment=ft.MainAxisAlignment.CENTER),
    )


# Main window or init window
def gui():
    ft.app(target=main)


if __name__ == "__main__":
    gui()

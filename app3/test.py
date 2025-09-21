import os, pathlib, time
import sys  # Voeg deze import toe
from datetime import datetime
from nicegui import ui
from threading import Thread

def show_pathlib_version(info):
    # Aangezien pathlib geen versie heeft, tonen we de Python versie
    python_version = sys.version  # Haal de Python versie op
    info.text += f'\nPython version: {python_version}'  # Voeg de versie toe aan de info
    info.text += f'\nPathlib is part of Python {python_version.split()[0]}'  # Geef aan dat pathlib deel uitmaakt van Python

def count_image_files(directory, total_files, total_dirs, info, heart_beat, callback):
    total_steps = 27  # Voorbeeldwaarde, bereken dit zoals nodig
    total_dirs = 0
    total_files = 0
    alert_dirs_count = 100000
    dirs_step = alert_dirs_count
    alert_files_count = 100000
    files_step = alert_files_count
    extentions = ['jpg', 'jpeg', 'img', 'png', 'heic', 'heif', 'tiff', 'gif', 'bmp', 'webp']
    path = pathlib.Path(directory)
    start_time = time.time()
    info.text = f'routine start time: {start_time} directory: {directory}'
    heart_beat.visible = True  # Make heart_beat visible

    for root, dirs, files in path.walk():
        total_dirs += len(dirs)
        count = 0
        dcount_files = total_files
        for file in files:
            if file.lower().endswith(tuple(extentions)):
                count += 1
        total_files += count

    end_time = time.time()
    time_taken = datetime.fromtimestamp(end_time - start_time).strftime('%H:%M:%S.%f')
    info.text = (f'Summary  routine total_dirs: {total_dirs} total_files: {total_files} time_taken: {time_taken}')
    print(f'routine total_dirs: {total_dirs} total_files: {total_files} time_taken: {time_taken}')

    heart_beat.visible = False  # Hide heart_beat when done
    show_pathlib_version(info)  # Roep de functie aan om de versie te tonen

    # Aan het einde van de functie, roep de callback aan met total_steps
    callback(total_steps)

    return total_steps

def update_heart_beat(heart_beat):
    while heart_beat.visible:
        heart_beat.value += 0.1  # Increment heart_beat
        heart_beat.value %= 1  # Reset to 0 if it exceeds 1
        time.sleep(0.9)  # Update rate

def start_counting_files(directory, info, heart_beat):
    def on_count_complete(total_steps):
        print(f'Total steps: {total_steps}')  # Nu hebben we de waarde

    # Start de telling in een aparte thread
    thread = Thread(target=count_image_files, args=(directory, 0, 0, info, heart_beat, on_count_complete))
    thread.start()
    
    # Start heart_beat update in een aparte thread
    heart_beat_thread = Thread(target=update_heart_beat, args=(heart_beat,))
    heart_beat_thread.start()

def create_ui():
    with ui.row():
        button = ui.button('Start')
        info = ui.label()
        heart_beat = ui.circular_progress(show_value=False)
        heart_beat.visible = False  # Initially hidden
    return info, button, heart_beat

def main(): 
    info, button, heart_beat = create_ui()
    heart_beat_rate = 0.1
    info.text = 'Start'
    print('start')
    button.on_click(lambda: start_counting_files('/Pictures', info, heart_beat))
    print('end')
    ui.run(host='127.0.0.1', port=8080, reload=True)

if __name__ in ['__main__', '__mp_main__']:
    main()
'''
# Version 1.0.0 Werkend

Voor aanpassing met UI log update# https://github.com/rdear4/photo_organizer/tree/master
# python dupDetect.py  -c "../Test-data/Test-media"

UI bars toegevoegd

AANDACHTS punten:
- zelfde filepath+naam -> als iets anders is: overschrijven. Want je hebt de oude info niet meer.
- Eerste aantal files bepalen, dan vragen of het goed is
- opp files herkennen
- iptc_keywords toevoegen
- checken of iptc_keywords en Subject oid hetzelfde zijn
- alle print statements eruit DONE
- LOG melingen naar een aparte scroll area
- UI update call toevoegen
- clean flag implementeren
- search flag implementeren
- dirs only flaf implementeren
- showdups flag implementeren
'''
from functools import reduce
import os,json
from exiftool import ExifToolHelper
import hashlib
from PIL import Image
import time
import concurrent.futures
import threading
from datetime import datetime, timedelta
import math
from multiprocessing import Queue, Process

import logging
from db_manager import DBManager
from process_mediafinder import MediaFinder
from nicegui import ui, run
import globals, config

#Part of UI block solution https://github.com/zauberzeug/nicegui/issues/794
RELOAD=True

def writeToLog(message):
    task = threading.Thread(target=writeToLogOnSeparateThread, args=[message])
    task.start()
    task.join()

def writeToLogOnSeparateThread(msg):

    time_as_string = datetime.now().strftime("%m/%d/%Y - %H:%M:%S")
    with open(globals.config_data['logpath'], "a") as f:
        f.write(f'[{msg[0]}] {(8 - len(msg[0])) * " "}- {time_as_string} - {msg[1]}\n')
    


def getMetadataValue(md, key):
    try:
        value = md[key]
        # Convert lists to comma-separated strings
        if isinstance(value, list):
            return ', '.join(str(x) for x in value)
        return str(value)
    except:
        return ""

def processMedia(fp):
    path_components, extension = os.path.splitext(fp)
    sidecar=''
    for extensions in globals.config_data['sidecar_extensions']:
        if os.path.exists(path_components+extensions.lower()):
            sidecar=sidecar+','+extensions # Sidecar extention in original case
            
    used_extentions = globals.config_data['image_extensions'] + globals.config_data['video_extensions']
    if extension.lower() not in used_extentions:#File not in scope Sidecars wil during associated file processing
        writeToLog(('INFO', f'File {fp} not in scope'))
        globals.log_content.append(f'[INFO] File {fp} not in scope')
        return None
    writeToLog(('INFO', f'Beginning to process file: {fp}'))
    try:
        with ExifToolHelper() as et:
            imgData = et.get_metadata(fp)[0]
            is_video = extension.lower() in globals.config_data['video_extensions']
            # Basic information
            directory = os.path.dirname(fp)
            filename = os.path.basename(fp)
            imgData['YAPMO:Directory'] = directory
            imgData['YAPMO:FileName'] = filename
            imgData['YAPMO:FileSize'] = str(os.path.getsize(fp))
            imgData['YAPMO:FileType'] = 'video' if is_video else 'image'
            
            # Bereken hash voor foto's
            if not is_video:
                try:
                    img = Image.open(fp)
                    hash_value = hashlib.md5(img.tobytes()).hexdigest()
                except Exception as e:
                    writeToLog(("ERROR", e))
                    hash_value = 'nil'
            else:
                # Hash voor video's
                hash_components = [
                    str(os.path.getsize(fp)),
                    imgData.get('Composite:GPSLatitude', ''),
                    imgData.get('Composite:GPSLongitude', ''),
                    imgData.get('File:FileModifyDate', '')
                ]
                hash_value = hashlib.md5(''.join(str(x) for x in hash_components).encode('utf-8')).hexdigest()
            
            #Additional fields required
            imgData.update({
                # 'name': filename,
                # 'type': 'video' if is_video else 'image',
                # 'filepath_original': directory,
                'YAPMO_FILE_Path_New': '',
                'YAPMO:FQPN': fp,
                'YAPMO:FileSize': str(os.path.getsize(fp)),
                'YAPMO:Hash': hash_value,
                # 'YAPMO:Sidecars': json.dumps(sidecar)#RM sidecar tijdelijk uitgezet
                'YAPMO:Sidecars': ''
            })
            return imgData

    except Exception as e:
        writeToLog(('ERROR', f'Error processing file: {fp} - {e}'))
        return None


#Stond bovenaan
startTime = time.perf_counter()

config.init_config()


#For use with the 'max' argument in the argparser
par_maxworkers = int(globals.config_data['maxworkers'])
ROOT_PATH = os.getcwd()


def main(shared_progress=None):           
    #setup parameters
    par_search_path = globals.config_data['search_path']
    par_search_only = globals.config_data['searchonly']
    par_dirs_only = globals.config_data['dirsonly']
    par_clean_db = globals.config_data['clean']
    par_show_dups = globals.config_data['showdups']
    par_enable_logging = globals.config_data['logging']
    par_max_workers = int(globals.config_data['maxworkers'])
    par_logpath = globals.config_data['logpath']
    par_root = globals.config_data['source_path'] # source_path is not in use at this moment
    par_clean = globals.config_data['clean']
    par_db = globals.config_data['db']
    par_dbtable_media = globals.config_data['dbtable_media']
    par_dbtable_dirs = globals.config_data['dbtable_dirs']

    # Reset start time for each run
    start_time = time.perf_counter()

    try:
        #Set up queues
        filePathQueue = Queue()
        mediafinder = None

        #check clean flag to create clean DB and Logfile
        if par_clean:
            if os.path.exists(par_db): 
                os.remove(par_db)
            if os.path.exists(par_logpath):
                os.remove(par_logpath)
        
        #create a connection to the SQLite3 db
        dbManager = DBManager(par_search_path,par_dbtable_media)

        try:
            if par_dirs_only:
                mediafinder = MediaFinder(par_search_path, _queueRef=filePathQueue, _searchDirsOnly=True)
                totalImages = 0
                totalDirs = 0
                while mediafinder.stillSearching() or not filePathQueue.empty():
                    while not filePathQueue.empty():
                        dirInfo = filePathQueue.get()
                        totalImages = totalImages + dirInfo[1]
                        totalDirs = totalDirs + 1
                        try:
                            dbManager.addDirectoryInfoToTable((dirInfo[0].split("/")[-1], dirInfo[0], dirInfo[1]))
                        except Exception as e:
                            writeToLog(("ERROR", e))
                logging.info(f"A total of {totalImages} images were found in {totalDirs} directories")
                globals.log_content.append(f"[INFO] A total of {totalImages} images were found in {totalDirs} directories")
            else:    
                mediafinder = MediaFinder(par_search_path, _queueRef = filePathQueue)
                while (mediafinder.stillSearching() or not filePathQueue.empty()) and not globals.aborted:
                    filePaths = []
                    while not filePathQueue.empty():
                        filePaths.append(filePathQueue.get())
                    if len(filePaths):
                        with concurrent.futures.ProcessPoolExecutor(max_workers=par_max_workers) as executor:
                            # Start all tasks
                            futures = [executor.submit(processMedia, fp) for fp in filePaths]
                            
                            # Process completed tasks
                            for res in concurrent.futures.as_completed(futures):
                                if globals.aborted:
                                    # Cancel any pending futures
                                    for future in futures:
                                        future.cancel()
                                    break
                                
                                try:
                                    dbManager.addMediaDataToDB(res.result())
                                    # Update UI progress
                                    if shared_progress is not None:
                                        with shared_progress.get_lock():
                                            shared_progress.value += 1
                                except Exception as e:
                                    writeToLog(("ERROR", str(e)))

                if globals.aborted:
                    writeToLog(("INFO", "Processing aborted by user"))
                    logging.info(f'[WARNING] Process Aborted by User')
                    globals.log_content.append(f'[WARNING] Process Aborted by User')

        finally:
            # Clean up MediaFinder
            if mediafinder:
                mediafinder.cleanup()
            
            # Close DB connection
            dbManager.closeConnection()
            
            # Close and cleanup the queue
            filePathQueue.close()
            filePathQueue.join_thread()

        # Calculate elapsed time from this run's start time
        end_time = time.perf_counter()
        total_seconds = end_time - start_time
        rounded_delta = timedelta(seconds=round(total_seconds * 100) / 100)

        formatted_delta = f"{str(rounded_delta).split('.')[0]}.{str(rounded_delta).split('.')[1][:2]}"
        dat_str=datetime.now().strftime("%m/%d/%Y, %H:%M:%S:%f")
        logging.info(f'Script ended at: {dat_str}')
        logging.info(f"Elapsed time: {total_seconds:4f}")
        logging.info(f'Script ellapsed time: {formatted_delta}\n')
        globals.log_content.append(f'[INFO] Script ended at: {dat_str}')
        globals.log_content.append(f"[INFO] Elapsed time: {total_seconds:.4f} seconds")
        globals.log_content.append(f'[INFO] Script ellapsed time: {formatted_delta}')

        if __name__ in ['__main__', '__mp_main__']:
            print(f'Script ended at: {dat_str}')
            print(f"Elapsed time: {total_seconds:.4f} seconds")
            print(f'Script ellapsed time: {formatted_delta}\n')

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        globals.log_content.append(f"[ERROR] An error occurred: {str(e)}")
        raise

if __name__ in ['__main__', '__mp_main__']:
    main()

    
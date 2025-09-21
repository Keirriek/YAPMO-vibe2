# Version 1.0.0 Werkend

"""

Media Finder

All tasks associated with searching directories for applicable media

"""

import os
import logging
from multiprocessing import Process
import time

class MediaFinder:

    def __init__(self, _initialSearchDirectory=".", _queueRef = None, _searchDirsOnly = False):

        self.initialSearchDirectory = _initialSearchDirectory
        self.searchComplete = False
        self.queueRef = _queueRef
        self.SearchProcess = None
        self._should_stop = False
        self._is_closed = False
        
        #create the Process that will search for files
        if not _searchDirsOnly:
            self.SearchProcess = Process(target=self.searchDirectory, args=[self.initialSearchDirectory, self.queueRef])
            self.SearchProcess.daemon = True  # Make process daemon so it exits with main process
            self.SearchProcess.start()
        else:
            self.SearchProcess = Process(target=self.searchForDirectories, args=[self.initialSearchDirectory, self.queueRef])
            self.SearchProcess.daemon = True  # Make process daemon so it exits with main process
            self.SearchProcess.start()
        
    def cleanup(self):
        """Cleanup method to properly terminate the search process"""
        if self._is_closed:
            return
            
        self._should_stop = True
        if self.SearchProcess:
            try:
                if self.SearchProcess.is_alive():
                    self.SearchProcess.terminate()
                    self.SearchProcess.join(timeout=0.5)
                    if self.SearchProcess.is_alive():
                        self.SearchProcess.kill()
                        self.SearchProcess.join(timeout=0.5)
                # Clean up any remaining process resources
                self.SearchProcess.close()
            except (ValueError, AttributeError):
                # Process already closed or terminated
                pass
            finally:
                self._is_closed = True
        
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass  # Ignore any errors during deletion

    def stillSearching(self):
        """Check if the search process is still running"""
        if self._is_closed:
            return False
        try:
            return self.SearchProcess and self.SearchProcess.is_alive() and not self._should_stop
        except (ValueError, AttributeError):
            return False

    def searchForDirectories(self, dirPath, qRef=None):
        try:
            with os.scandir(dirPath) as dirResults:
                fileCount = 0
                for entry in dirResults:
                    if self._should_stop:
                        return
                    if not entry.name.startswith(".") and entry.is_dir():
                        self.searchForDirectories(entry.path, qRef)
                    if not entry.name.startswith(".") and entry.is_file():
                        fileCount = fileCount + 1
                if qRef and not self._should_stop:
                    qRef.put((dirPath, fileCount))
        except Exception as e:
            logging.error(f"Error in searchForDirectories: {str(e)}")
            raise

    def searchDirectory(self, dirPath, qRef=None):
        try:
            with os.scandir(dirPath) as dirResults:
                for entry in dirResults:
                    if self._should_stop:
                        return
                    if not entry.name.startswith(".") and entry.is_dir():
                        self.searchDirectory(entry.path, qRef)
                    if not entry.name.startswith(".") and entry.is_file():
                        if qRef and not self._should_stop:
                            qRef.put(f"{dirPath}/{entry.name}")
        except Exception as e:
            logging.error(f"Error in searchDirectory: {str(e)}")
            raise


        return
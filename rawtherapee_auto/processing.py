import shutil
import tempfile
import pkg_resources
import os
import subprocess
import tqdm
import time
from threading import Timer
import logging
from typing import Optional


logger = logging.getLogger(__name__)


class NotInstalledError(Exception):
    def __init__(self, software: str, advice: Optional[str]=None) -> None:
        msg = f"Cannot find {software} installed on your system. "
        
        if advice is None:
            advice = "Please install this dependency before continuing."
        
        msg += advice
        super().__init__(msg)


class FileLocations():
    
    def __init__(
        self, 
        input_dir: str, 
        monitor_dir: str, 
        output_dir: str, 
        raw_file_name: str
    ) -> None:
        self._base_name = os.path.splitext(raw_file_name)[0]
        
        self.input_raw_path = os.path.join(input_dir, raw_file_name)
        self.output_raw_path = os.path.join(output_dir, raw_file_name)
        
        self.png_path = os.path.join(monitor_dir, self._base_name + ".png")
        
        self.input_pp3_path = self.png_path + ".pp3"
        self.output_pp3_path = os.path.join(output_dir, raw_file_name + ".pp3")
        
        self.png_exists = False
        self.pp3_exists = False
        self._block = False
    
    def __str__(self) -> str:
        return self._base_name
    
    def move(self) -> bool:
        if self.png_exists and self.pp3_exists and not self._block:
            self._block = True
            
            os.remove(self.png_path)
            self.png_exists = False
            
            os.rename(self.input_pp3_path, self.output_pp3_path)
            self.pp3_exists = False
            
            os.rename(self.input_raw_path, self.output_raw_path)
            
            return True
        
        return False


class DirectoryMonitor():
    
    def __init__(self, input_dir: str, monitor_dir: str, output_dir: str) -> None:
        self._timer = None
        self.is_running = False
        
        self.input_dir = input_dir
        self.monitor_dir = monitor_dir
        self.output_dir = output_dir
        
        self.parsed_extensions = [
            "3fr", "arw", "arq", "cr2", "cr3", "crf", "crw", "dcr", "dng", "fff", "iiq",
            "jpg", "jpeg", "kdc", "mef", "mos", "mrw", "nef", "nrw", "orf", "ori",
            "pef", "png", "raf", "raw", "rw2", "rwl", "rwz", "sr2", "srf", "srw", "tif",
            "tiff", "x3f"
        ]
    
        self._files = self._get_file_data()
            
        self._pbar = tqdm.tqdm(total=len(self._files), unit="photo", dynamic_ncols=True)
    
    
    def __del__(self) -> None:
        self.stop()
    
    
    def _get_file_data(self) -> dict:
        file_data = {}
        
        with os.scandir(self.input_dir) as directory_contents:
            for object in directory_contents:
                if object.is_file():
                    input_file_ext = os.path.splitext(object.name)[-1]
                    input_file_ext_formatted = input_file_ext.lower().replace(".", "")
                    
                    if input_file_ext_formatted in self.parsed_extensions:
                        base_name = os.path.splitext(object.name)[0]
                        if base_name in file_data.keys():
                            raise Warning(
                                f"File {base_name} exists with multiple file "
                                "extensions, only one of which will be processed."
                            )
                        
                        file_data[base_name] = FileLocations(
                            self.input_dir, 
                            self.monitor_dir, 
                            self.output_dir, 
                            object.name
                        )
        
        return file_data
    
    
    def _find_and_move(self) -> None:
        with os.scandir(self.monitor_dir) as directory_contents:
            for object in directory_contents:
                if object.is_file():
                    object_ext = os.splitext(object.name)[-1].lower()
                    base_name = None
                    
                    if object_ext == ".png":
                        base_name = os.splitext(object.name)[0]
                    
                    if object_ext == ".pp3":
                        base_name = os.splitext(os.splitext(object.name)[0])[0]
                    
                    locator = self._files.get(base_name)
                    if locator is None:
                        continue
                    
                    if object_ext == ".png":
                        locator.png_exists = True
                    
                    if object_ext == ".pp3":
                        locator.pp3_exists = True
                    
        for key, locator in self._files.items():
            moved = locator.move()
            if moved:
                del self._files[key]
                self._pbar.update(1)


    def _run(self) -> None:
        self.is_running = False
        self.start()
        self._find_and_move()


    def start(self) -> None:
        if not self.is_running and len(self._files) > 0:
            self._timer = Timer(0.1, self._run)
            self._timer.start()
            self.is_running = True


    def stop(self) -> None:        
        if self._timer is not None:
            self._timer.cancel()
        
        if self._pbar is not None:
            self._pbar.close()
        
        self.is_running = False
    
    
    @property
    def done(self) -> bool:
        return len(self._files) == 0



class Processor():
    
    def __init__(self, input_directory: str, output_directory: str) -> None:
        self.tmp_directory_object = tempfile.TemporaryDirectory()
        self.tmp_dir = self.tmp_directory_object.name
        
        self.pp3_path = pkg_resources.resource_filename(__name__, "auto-correction.pp3")
        
        self.rawtherapee_path = self.rawtherapee_location()
        
        self.output_dir = output_directory
        self.ensure_exists(self.output_dir)
        
        self.input_dir = input_directory
        
        self.rawtherapee_proc = None
        self.monitor = DirectoryMonitor(self.input_dir, self.tmp_dir, self.output_dir)
        
    
    def __del__(self) -> None:
        del self.tmp_directory_object
        del self.monitor
    
    
    def run(self) -> None:
        self.rawtherapee_proc = self.start_rawtherapee(self.input_dir)
        self.monitor.start()
    
    
    def rawtherapee_location(self) -> str | None:
        location = shutil.which("rawtherapee-cli")
        if location is None:
            raise NotInstalledError(
                "RawTherapee CLI", 
                "Please go to rawtherapee.com and install the CLI tool before continuing."
            )
        
        return location
    
    def ensure_exists(self, directory: str) -> None:
        if os.path.isdir(directory) == False:
            logger.warn(f"Creating {directory} since it does not currently exist.")
            os.makedirs(directory)
        
    
    def start_rawtherapee(self, input_directory: str) -> None:
        proc = subprocess.Popen([
            self.rawtherapee_path, 
            "-p", self.pp3_path, 
            "-O", self.tmp_dir, 
            "-n", # Specify output to be compressed PNG (16-bit).
            "-Y", # Overwrite output if present.
            "-a", # Process all supported image file types when specifying a folder, 
                  # even those not currently selected in Preferences > File Browser > 
                  # Parsed Extensions.
            "-c", input_directory
        ])
        return proc
    
    
    @property
    def done(self) -> bool:
        if self.rawtherapee_proc is None:
            return False
        
        if self.rawtherapee_proc.poll() is None:
            return False
        
        return self.monitor.done
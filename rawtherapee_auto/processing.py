import shutil
import tempfile
import pkg_resources
import os
import subprocess
import shutil
import logging
from typing import Optional
from rawtherapee_auto import monitor


logger = logging.getLogger(__name__)


class NotInstalledError(Exception):
    def __init__(self, software: str, advice: Optional[str] = None) -> None:
        msg = f"Cannot find {software} installed on your system. "

        if advice is None:
            advice = "Please install this dependency before continuing."

        msg += advice
        super().__init__(msg)


class Processor:

    def __init__(self, input_directory: str, output_directory: str) -> None:
        self.tmp_directory_object = tempfile.TemporaryDirectory()
        self.tmp_dir = self.tmp_directory_object.name

        self.pp3_path = pkg_resources.resource_filename(
            __name__, "res/auto-correction.pp3"
        )
        if os.path.isfile(self.pp3_path) == False:
            raise FileNotFoundError(
                f"Failed to locate auto-correction.pp3 in {self.pp3_path}"
            )

        self.rawtherapee_path = self.rawtherapee_location()

        self.output_dir = output_directory
        self.ensure_exists(self.output_dir)

        self.input_dir = input_directory

        self.rawtherapee_proc = None
        self.monitor = None
        self.monitor = monitor.Monitor(self.input_dir, self.tmp_dir, self.output_dir)

    def __del__(self) -> None:
        if self.monitor is not None:
            self.monitor.stop()

        del self.tmp_directory_object

    def run(self) -> None:
        self.start_rawtherapee()
        self.monitor.start()

    def rawtherapee_location(self) -> str | None:
        location = shutil.which("rawtherapee-cli")
        if location is None:
            raise NotInstalledError(
                "RawTherapee CLI",
                "Please go to rawtherapee.com and install the CLI tool before continuing.",
            )

        return location

    def ensure_exists(self, directory: str) -> None:
        if os.path.isdir(directory) == False:
            logger.warn(f"Creating {directory} since it does not currently exist.")
            os.makedirs(directory)

    def start_rawtherapee(self) -> None:
        self.rawtherapee_proc = subprocess.Popen(
            [
                self.rawtherapee_path,
                "-p",
                self.pp3_path,
                "-O",
                self.tmp_dir,
                "-n",  # Specify output to be compressed PNG (16-bit).
                "-Y",  # Overwrite output if present.
                "-a",  # Process all supported image file types when specifying a folder,
                # even those not currently selected in Preferences > File Browser >
                # Parsed Extensions.
                "-c",
                self.input_dir,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @property
    def done(self) -> bool:
        if self.rawtherapee_proc is None:
            return False

        if self.rawtherapee_proc.poll() is None:
            return False

        return self.monitor.done

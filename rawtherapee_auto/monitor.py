import tqdm
import os
import threading
from rawtherapee_auto import file_mover


class Monitor:

    def __init__(self, input_dir: str, monitor_dir: str, output_dir: str) -> None:
        self._timer = None
        self.is_running = False

        self.input_dir = input_dir
        self.monitor_dir = monitor_dir
        self.output_dir = output_dir

        self.parsed_extensions = [
            "3fr",
            "arw",
            "arq",
            "cr2",
            "cr3",
            "crf",
            "crw",
            "dcr",
            "dng",
            "fff",
            "iiq",
            "jpg",
            "jpeg",
            "kdc",
            "mef",
            "mos",
            "mrw",
            "nef",
            "nrw",
            "orf",
            "ori",
            "pef",
            "png",
            "raf",
            "raw",
            "rw2",
            "rwl",
            "rwz",
            "sr2",
            "srf",
            "srw",
            "tif",
            "tiff",
            "x3f",
        ]

        self._files = self._get_file_data()
        if len(self._files) == 0:
            self._pbar = None
            raise FileNotFoundError(f"No raw photos found in {self.input_dir}")

        self._pbar = tqdm.tqdm(total=len(self._files), unit="photo", dynamic_ncols=True)

    def __del__(self) -> None:
        self.stop()

    def _get_file_data(self) -> dict[str, file_mover.FileMover]:
        file_data = {}

        with os.scandir(self.input_dir) as directory_contents:
            for object in directory_contents:
                if object.is_file():
                    input_file_ext = os.path.splitext(object.name)[-1]
                    input_file_ext_formatted = input_file_ext.lower().replace(".", "")

                    if input_file_ext_formatted in self.parsed_extensions:
                        fm = file_mover.FileMover(
                            self.input_dir,
                            self.monitor_dir,
                            self.output_dir,
                            object.name,
                        )
                        if str(fm) in file_data.keys():
                            raise Warning(
                                f"File {fm} exists with multiple file "
                                "extensions, only one of which will be processed."
                            )

                        file_data[str(fm)] = fm

        return file_data

    def _find_and_move(self) -> None:
        if os.path.isdir(self.monitor_dir):
            with os.scandir(self.monitor_dir) as directory_contents:
                for object in directory_contents:
                    if object.is_file():
                        object_ext = os.path.splitext(object.name)[-1].lower()
                        base_name = None

                        if object_ext == ".png":
                            base_name = os.path.splitext(object.name)[0]

                        if object_ext == ".pp3":
                            base_name = os.path.splitext(
                                os.path.splitext(object.name)[0]
                            )[0]

                        locator = self._files.get(base_name)
                        if locator is None:
                            continue

                        if object_ext == ".png":
                            locator.png_exists = True

                        if object_ext == ".pp3":
                            locator.pp3_exists = True

        for locator in self._files.values():
            if locator.done == False:
                locator.move()
                if locator.done:
                    self._pbar.update(1)

    def _run(self) -> None:
        self.is_running = False
        self.start()
        self._find_and_move()

    def start(self) -> None:
        if not self.is_running and len(self._files) > 0:
            self._timer = threading.Timer(0.1, self._run)
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
        return all(locator.done for locator in self._files.values())

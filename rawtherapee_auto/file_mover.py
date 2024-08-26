import os
import shutil


class FileMover:

    def __init__(
        self, input_dir: str, monitor_dir: str, output_dir: str, raw_file_name: str
    ) -> None:
        self.output_dir = output_dir
        self._base_name = os.path.splitext(raw_file_name)[0]

        self.input_raw_path = os.path.join(input_dir, raw_file_name)

        self.png_path = os.path.join(monitor_dir, self._base_name + ".png")

        self.input_pp3_path = self.png_path + ".pp3"
        self.output_pp3_path = os.path.join(self.output_dir, raw_file_name + ".pp3")

        self.png_exists = False
        self.pp3_exists = False
        self._block = False
        self._moved = False

    def __str__(self) -> str:
        return self._base_name

    def move(self) -> None:
        if self.png_exists and self.pp3_exists and not self._block:
            self._block = True

            os.remove(self.png_path)
            self.png_exists = False

            shutil.move(self.input_pp3_path, self.output_pp3_path)
            self.pp3_exists = False

            shutil.copy2(self.input_raw_path, self.output_dir)

            self._block = False
            self._moved = True

    @property
    def done(self) -> bool:
        return self._moved

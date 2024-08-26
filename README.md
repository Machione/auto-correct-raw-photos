# RawTherapee Auto

A CLI to automatically adjust raw photos using RawTherapee.

## Installation

RawTherapee is an excellent, free and open-source raw photo editor. Download it from <https://rawtherapee.com>. Note that you will need to install both the application and the CLI tool for `rawtherapee-auto` to function.

After this, install `rawtherapee-auto` using Pip or your Python package management tool of choice.

## Usage

```shell
rawtherapee-auto /path/to/raw/photos /desired/output/location
```

This will run RawTherapee on all the raw photos found in `/path/to/raw/photos`. It will use RawTherapee's auto-level functionality to try to get exposure, contrast, etc. in the right ball-park for each photo found. Then it will move the original raw photo along with the outputted .pp3 file from RawTherapee's processing to the `/desired/output/location`.

Run `rawtherapee-auto --help` for additional help.

# MediaMigr8tr (Beta)

Keep in mind that this is a beta product. Please report any bugs or crashes as an issue.

## Description

If you're tired of manually migrating your movies and tv shows from the download folder into your respective target media folders, then this project was made for you.

It will monitor a source directory that you choose at installation time and detect new files and put them in target movie and tv show folders of your choosing using a widely favored folder 
organization structure accepted by many media servers.

## Movie Structure

/path/to/movies/[A-Z]/[Move File] 

## TV Show Structure

/path/to/tv shows/[TV Show Name]/[Season Number]/[TV Show File]

## Installation

`sudo ./install`

## Requirements

- Python 3
- python3-setuptools
- upstart or systemd
- sudo on the installation system
- Debian based Linux distribution (Install script assumes Debian, please contribute installation patches for other distros)

## Contributions

I welcome all and any improvements to make this software more useful and robust. Thanks for your support.
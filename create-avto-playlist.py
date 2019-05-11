#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import plistlib
import re
import urllib.parse
import shutil
from pathlib import Path
import subprocess

TRACK_FIELD_TRACKS = 'Tracks'
TRACK_FIELD_LOCATION = 'Location'
TRACK_FIELD_ALBUM = 'Album'
TRACK_FIELD_YEAR = 'Year'
TRACK_FIELD_NUMBER = 'Track Number'
TRACK_FIELD_NAME = 'Name'
TRACK_FIELD_ARTIST = 'Artist'


def get_itunes_library():
    itunes_library_path = Path.joinpath(Path.home(), "Music", "iTunes", "iTunes Music Library.xml")

    with itunes_library_path.open('rb') as fp:
        return plistlib.load(fp)


def exec_shell(shell_command):
    cmd = subprocess.Popen(shell_command, shell=True, stdout=subprocess.PIPE)
    out, err = cmd.communicate()

    if not (err is None):
        return err

    return out.decode(encoding="utf8")


def get_tracks_map(library):
    result = {}

    # Берется только то, что лежит в каталоге с наименованием Music и ниже.
    drive_re = re.compile(r'.+(/Volumes/\w+/Music.+)')

    for trackId, trackInfo in library[TRACK_FIELD_TRACKS].items():
        location = urllib.parse.unquote(trackInfo[TRACK_FIELD_LOCATION])
        match = drive_re.match(location)

        if match is None:
            continue

        track = {
            TRACK_FIELD_LOCATION: match[1],
            TRACK_FIELD_NAME: trackInfo[TRACK_FIELD_NAME] if TRACK_FIELD_NAME in trackInfo else '',
            TRACK_FIELD_ARTIST: trackInfo[TRACK_FIELD_ARTIST] if TRACK_FIELD_ARTIST in trackInfo else '',
            TRACK_FIELD_ALBUM: trackInfo[TRACK_FIELD_ALBUM] if TRACK_FIELD_ALBUM in trackInfo else '',
            TRACK_FIELD_YEAR: trackInfo[TRACK_FIELD_YEAR] if TRACK_FIELD_YEAR in trackInfo else 0,
            TRACK_FIELD_NUMBER: trackInfo[TRACK_FIELD_NUMBER] if TRACK_FIELD_NUMBER in trackInfo else 0
        }

        result[trackId] = track

    return result


def get_avto_tracks(library, tracks_map):
    tracks = []

    for playlist in library['Playlists']:
        playlist_name = playlist['Name']

        if playlist_name != 'Avto':
            continue

        playlist_items = 'Playlist Items'
        if not (playlist_items in playlist):
            # Пропускаем пустые списки воспроизведения.
            continue

        for track in playlist[playlist_items]:
            tracks.append(tracks_map[str(track['Track ID'])])

    return tracks


def create_playlist_files(tracks):
    remove_punctuation_map = dict((ord(char), None) for char in '\'\\/*?:"<>|')
    out_folder = Path.joinpath(Path.home(), "Downloads", "Avto Music")

    if out_folder.exists():
        shutil.rmtree(out_folder.as_posix())

    out_folder.mkdir()

    for track in tracks:
        source_file = Path(track[TRACK_FIELD_LOCATION])

        artist = track[TRACK_FIELD_ARTIST].translate(remove_punctuation_map)
        name = track[TRACK_FIELD_NAME].translate(remove_punctuation_map)

        destination_file = Path.joinpath(
            out_folder,
            f'{artist} - {name}.mp3')

        if source_file.suffix == '.m4a':
            print(f'Convert {source_file.as_posix()} to {destination_file.as_posix()} ...')
            convert_cmd = f'ffmpeg -i "{source_file.as_posix()}" -loglevel panic -y -vn -acodec libmp3lame -ab 320k "{destination_file.as_posix()}"'
            print(exec_shell(convert_cmd))
        else:
            print(f'Copy {source_file.as_posix()} to {destination_file.as_posix()} ...')
            shutil.copyfile(source_file.as_posix(), destination_file.as_posix())


if __name__ == "__main__":
    g_library = get_itunes_library()
    g_tracks_map = get_tracks_map(g_library)
    g_tracks = get_avto_tracks(g_library, g_tracks_map)
    create_playlist_files(g_tracks)

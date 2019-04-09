#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import plistlib
import re
import urllib.parse
import shutil
from pathlib import Path

# Наименования исключаемых умных списков воспроизведения.
except_playlist_names = {
    'Radio',
    'Genius',
    'Аудиокниги',
    'Телешоу',
    'Загружено',
    'Фильмы',
    'Загружено',
    'Музыка',
    'Загружено',
    'Медиатека'}


def get_itunes_library():
    itunes_library_path = Path.joinpath(Path.home(), "Music", "iTunes", "iTunes Music Library.xml")

    with itunes_library_path.open('rb') as fp:
        return plistlib.load(fp)


def get_tracks_map(library):
    result = {}

    drive_re = re.compile(r'.+(/Music.+)')

    for trackId, trackInfo in library['Tracks'].items():
        location = urllib.parse.unquote(trackInfo['Location'])
        match = drive_re.match(location)

        if match is None:
            continue

        track_path = 'TF1:' + match[1]
        result[trackId] = track_path.replace('/', '\\')

    return result


def get_smart_playlist_map(library, tracks_map):
    result = {}

    for playlist in library['Playlists']:
        playlist_name = playlist['Name']

        if playlist_name in except_playlist_names:
            # Пропускаем стандартные списки воспроизведения.
            continue

        playlist_items = 'Playlist Items'
        if not (playlist_items in playlist):
            # Пропускаем пустые списки воспроизведения.
            continue

        tracks = []
        for track in playlist[playlist_items]:
            tracks.append(tracks_map[str(track['Track ID'])])

        result[playlist_name] = tracks

    return result


def create_playlist_files(playlist_map):
    out_folder = Path.joinpath(Path.home(), "Downloads", "Playlists").as_posix()

    if os.path.exists(out_folder):
        shutil.rmtree(out_folder)

    os.makedirs(out_folder)

    for playlist_name, tracks in playlist_map.items():
        playlist_name1 = re.sub(r'[^\-\d\s\w_\']+', '', playlist_name)
        out_playlist_filename = os.path.join(out_folder, playlist_name1) + '.m3u'

        with open(out_playlist_filename, 'wt', encoding="utf-8") as outfile:
            print('Create:', playlist_name, ' =>', out_playlist_filename)
            outfile.write('#EXTM3U\n')

            for track in tracks:
                outfile.write(track)
                outfile.write('\n')


if __name__ == "__main__":
    g_library = get_itunes_library()
    g_tracks_map = get_tracks_map(g_library)
    g_smart_playlist_map = get_smart_playlist_map(g_library, g_tracks_map)
    create_playlist_files(g_smart_playlist_map)

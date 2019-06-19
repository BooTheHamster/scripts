#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import plistlib
import re
import urllib.parse
import shutil
from pathlib import Path
from operator import itemgetter

# Наименования исключаемых умных списков воспроизведения.
EXCEPT_PLAYLIST_NAMES = {
    'Radio',
    'Genius',
    'Аудиокниги',
    'Телешоу',
    'Загружено',
    'Фильмы',
    'Загружено',
    'Музыка',
    'Загружено',
    'Медиатека',
    'Покупки'}

TRACK_FIELD_TRACKS = 'Tracks'
TRACK_FIELD_LOCATION = 'Location'
TRACK_FIELD_ALBUM = 'Album'
TRACK_FIELD_YEAR = 'Year'
TRACK_FIELD_NUMBER = 'Track Number'
TRACK_FIELD_ID = 'Track ID'

def get_itunes_library():
    itunes_library_path = Path.joinpath(Path.home(), "Music", "iTunes", "iTunes Music Library.xml")

    with itunes_library_path.open('rb') as fp:
        return plistlib.load(fp)


def get_tracks_map(library):
    result = {}

    # Берется только то, что лежит в каталоге с наименованием Music и ниже.
    drive_re = re.compile(r'.+(/Music.+)')

    for trackId, trackInfo in library[TRACK_FIELD_TRACKS].items():

        if TRACK_FIELD_LOCATION not in trackInfo:
            continue

        location = urllib.parse.unquote(trackInfo[TRACK_FIELD_LOCATION])
        match = drive_re.match(location)

        if match is None:
            continue

        # Fiio X1 II использует Windows пути (проверить возможно ли использование posix пути).
        track = {
            TRACK_FIELD_LOCATION: 'TF1:' + match[1].replace('/', '\\'),
            TRACK_FIELD_ALBUM: trackInfo[TRACK_FIELD_ALBUM] if TRACK_FIELD_ALBUM in trackInfo else '',
            TRACK_FIELD_YEAR: trackInfo[TRACK_FIELD_YEAR] if TRACK_FIELD_YEAR in trackInfo else 0,
            TRACK_FIELD_NUMBER: trackInfo[TRACK_FIELD_NUMBER] if TRACK_FIELD_NUMBER in trackInfo else 0
        }

        result[trackId] = track

    return result


def get_smart_playlist_map(library, tracks_map):
    result = {}

    for playlist in library['Playlists']:
        playlist_name = playlist['Name']

        if playlist_name in EXCEPT_PLAYLIST_NAMES:
            # Пропускаем стандартные списки воспроизведения.
            continue

        playlist_items = 'Playlist Items'
        if not (playlist_items in playlist):
            # Пропускаем пустые списки воспроизведения.
            continue

        tracks = []
        for track in playlist[playlist_items]:

            track_id = str(track[TRACK_FIELD_ID])

            if track_id not in tracks_map:
                continue

            tracks.append(tracks_map[track_id])

        if tracks:
            result[playlist_name] = tracks

    return result


def create_playlist_files(playlist_map):
    out_folder = Path.joinpath(Path.home(), "Downloads", "Playlists")

    if out_folder.exists():
        shutil.rmtree(out_folder.as_posix())

    out_folder.mkdir()

    for playlist_name, tracks in playlist_map.items():
        # Сортировка треков в списке воспроизведения по году, альбому и номеру трека.
        tracks.sort(key=itemgetter(TRACK_FIELD_YEAR, TRACK_FIELD_ALBUM, TRACK_FIELD_NUMBER))

        playlist_name1 = re.sub(r'[^\-\d\s\w_\']+', '', playlist_name)
        out_playlist_filename = Path.joinpath(out_folder, playlist_name1).with_suffix('.m3u')

        with out_playlist_filename.open('wt', encoding="utf-8") as outfile:
            print('Create:', playlist_name, ' =>', out_playlist_filename)
            outfile.write('#EXTM3U\n')

            for track in tracks:
                outfile.write(track[TRACK_FIELD_LOCATION])
                outfile.write('\n')


if __name__ == "__main__":
    g_library = get_itunes_library()
    g_tracks_map = get_tracks_map(g_library)
    g_smart_playlist_map = get_smart_playlist_map(g_library, g_tracks_map)
    create_playlist_files(g_smart_playlist_map)

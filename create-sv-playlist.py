#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import plistlib
import re
import urllib.parse
import shutil
from pathlib import Path
import subprocess
import multiprocessing as mp

TRACK_FIELD_TRACKS = 'Tracks'
TRACK_FIELD_LOCATION = 'Location'
TRACK_FIELD_ALBUM = 'Album'
TRACK_FIELD_YEAR = 'Year'
TRACK_FIELD_NUMBER = 'Track Number'
TRACK_FIELD_NAME = 'Name'
TRACK_FIELD_ARTIST = 'Artist'

remove_punctuation_map = dict((ord(char), None) for char in '\'\\/*?:"<>|')
target_i = -20.0
target_lra = 7.0
target_tp = -2.0
target_offset = 0.0

input_i_re = re.compile(r'\"input_i\"\s:\s\"(-?\d+.?\d+)')
input_tp_re = re.compile(r'\"input_tp\"\s:\s\"(-?\d+.?\d+)')
input_lra_re = re.compile(r'\"input_lra\"\s:\s\"(-?\d+.?\d+)')
input_thresh_re = re.compile(r'\"input_thresh\"\s:\s\"(-?\d+.?\d+)')


class Configuration:
    # Наименования списков воспроизведения из которых собираются треки.
    playlists = ['Avto', 'VA Sv']

    # Наименование каталога в который копируются файлы.
    out_folder = 'VA Sv'

    # Тег прописываемый в треки для упрощения создания плейлиста в iTunes.
    out_file_tag = 'VA Sv'


def get_itunes_library():
    itunes_library_path = Path.joinpath(Path.home(), 'Music', 'iTunes', 'iTunes Music Library.xml')

    with itunes_library_path.open('rb') as fp:
        return plistlib.load(fp)


def exec_shell(shell_command):
    cmd = subprocess.Popen(
        shell_command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    out, err = cmd.communicate()

    if not (err is None):
        return str(err, 'utf-8')

    return out.decode(encoding='utf8')


def get_tracks_map(library):
    result = {}

    print('Process iTunes library export file')

    # Берется только то, что ссылается на локальный файл.
    drive_re = re.compile(r'file:(.*)')

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


def get_avto_tracks(library, tracks_map, configuration: Configuration):
    tracks = []

    for playlist in library['Playlists']:
        playlist_name = playlist['Name']

        if playlist_name not in configuration.playlists:
            continue

        playlist_items = 'Playlist Items'
        if not (playlist_items in playlist):
            # Пропускаем пустые списки воспроизведения.
            continue

        for track in playlist[playlist_items]:
            tracks.append(tracks_map[str(track['Track ID'])])

    return tracks


def get_loudnorm_parameter(parameter_reg, analyze_result):
    match = parameter_reg.findall(analyze_result, re.M)
    value_str = next(iter(match), None)

    return value_str


def process_track(track, out_folder):
    source_file = Path(track[TRACK_FIELD_LOCATION])

    artist = track[TRACK_FIELD_ARTIST].translate(remove_punctuation_map)
    name = track[TRACK_FIELD_NAME].translate(remove_punctuation_map)

    destination_file = Path.joinpath(
        out_folder,
        f'{artist} - {name}.mp3')

    source_path = source_file.as_posix()
    destination_path = destination_file.as_posix()

    normalize_filter_cmd = f'-filter:a ' \
        f'loudnorm=print_format=json' \
        f':i={target_i}' \
        f':lra={target_lra}' \
        f':tp={target_tp}' \
        f':offset={target_offset}'

    # Получение информации о громкости трека.
    analyze_cmd = f'ffmpeg -i "{source_path}" {normalize_filter_cmd} -vn -sn -dn -f null /dev/null'
    analyze_result = exec_shell(analyze_cmd)
    input_i = get_loudnorm_parameter(input_i_re, analyze_result)
    input_tp = get_loudnorm_parameter(input_tp_re, analyze_result)
    input_lra = get_loudnorm_parameter(input_lra_re, analyze_result)
    input_thresh = get_loudnorm_parameter(input_thresh_re, analyze_result)

    normalize_filter_cmd = f'-filter:a ' \
        f'loudnorm=linear=true' \
        f':i={target_i}' \
        f':lra={target_lra}' \
        f':tp={target_tp}' \
        f':offset={target_offset}' \
        f':measured_I={input_i}' \
        f':measured_LRA={input_lra}' \
        f':measured_tp={input_tp}' \
        f':measured_thresh={input_thresh}'

    ffmpeg_cmd = f'ffmpeg -i "{source_path}" ' \
        f'-loglevel panic ' \
        f'-y {normalize_filter_cmd} -vn -acodec ' \
        f'libmp3lame -ab 320k -ar 44100 "{destination_path}"'

    print(f'Process {source_path} to {destination_path} ...')
    exec_shell(ffmpeg_cmd)


def create_playlist_files(tracks, configuration: Configuration):
    out_folder = Path.joinpath(Path.home(), 'Downloads', configuration.out_folder)
    pool = mp.Pool(mp.cpu_count())

    if out_folder.exists():
        shutil.rmtree(out_folder.as_posix())

    out_folder.mkdir()

    result = [pool.apply_async(process_track, [track, out_folder]) for track in tracks]

    pool.close()
    pool.join()


def main(configuration: Configuration):
    library = get_itunes_library()
    tracks_map = get_tracks_map(library)
    tracks = get_avto_tracks(library, tracks_map, configuration)
    create_playlist_files(tracks, configuration)


if __name__ == "__main__":
    main(Configuration())

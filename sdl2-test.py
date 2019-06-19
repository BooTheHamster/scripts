#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Установка каталога по которому находится библиотека SDL.
# Необходимо делать перед импортом модуля.
os.environ['PYSDL2_DLL_PATH'] = str(Path(sys.argv[0]).parent)
import sdl2.ext  # nopep8


class SoftwareRenderer(sdl2.ext.SoftwareSpriteRenderSystem):
    def __init__(self, window):
        super(SoftwareRenderer, self).__init__(window)

    def render(self, components):
        sdl2.ext.fill(self.surface, sdl2.ext.Color(0, 0, 0))
        super(SoftwareRenderer, self).render(components)


class Game:
    _size = ()
    _title = ''

    def __init__(self, title, size):
        sdl2.ext.init()
        self._size = size
        self._title = title

    def run(self):
        window = sdl2.ext.Window(self._title, size=self._size)
        window.show()

        world = sdl2.ext.World()
        renderer = SoftwareRenderer(window)
        #world.add_system(renderer)

        running = True
        while running:
            events = sdl2.ext.get_events()
            for event in events:
                if event.type == sdl2.SDL_QUIT:
                    running = False
                    break

            sdl2.SDL_Delay(10)
            world.process()

        sdl2.ext.quit()


if __name__ == "__main__":
    game = Game("ElecTap", (600, 800))
    game.run()
    sys.exit()

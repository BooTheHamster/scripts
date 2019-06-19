#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Установка каталога по которому находится библиотека SDL.
# Необходимо делать перед импортом модуля.
os.environ['PYSDL2_DLL_PATH'] = str(Path(sys.argv[0]).parent)
import sdl2.ext  # nopep8


class Renderer(sdl2.ext.SoftwareSpriteRenderSystem):
    def __init__(self, window):
        super(Renderer, self).__init__(window)

    def render(self, sprites, x=None, y=None):
        sdl2.ext.fill(self.surface, sdl2.ext.Color(0, 0, 0))
        super(Renderer, self).render(sprites)


class SpriteFactory(sdl2.ext.SpriteFactory):
    def __init__(self):
        super(SpriteFactory, self).__init__(sdl2.ext.SOFTWARE)


class NegativeBlock(sdl2.ext.Entity):
    _color = sdl2.ext.Color(0, 0, 255)

    def __init__(self, factory, x=0, y=0):
        self.sprite = factory.from_color(self._color)
        self.sprite.position = x, y


class PositiveBlock(sdl2.ext.Entity):
    _color = sdl2.ext.Color(255, 0, 0)

    def __init__(self, factory, size, x=0, y=0):
        self.sprite = factory.from_color(self._color, size)
        self.sprite.position = x, y


class MovementSystem(sdl2.ext.Applicator):
    def __init__(self, left, top, right, bottom):
        super(MovementSystem, self).__init__()
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.componenttypes = Velocity, sdl2.ext.Sprite

    def process(self, world, components):
        for velocity, sprite in components:
            width, height = sprite.size

            # Спрайты вышедшие за границу видимой области не двигаются.
            if (sprite.x >= (self.left - width)) and (sprite.x <= self.right):
                sprite.x += velocity.vx

            if (sprite.y >= (self.top - height)) and (sprite.y <= self.bottom):
                sprite.y += velocity.vy


class Velocity(object):
    def __init__(self):
        super(Velocity, self).__init__()
        self.vx = 0
        self.vy = 0


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
        factory = SpriteFactory()

        positive_block = PositiveBlock(world, factory, (20, 20))

        renderer = Renderer(window)
        world.add_system(renderer)

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

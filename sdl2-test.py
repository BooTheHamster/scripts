#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Установка каталога по которому находится библиотека SDL.
# Необходимо делать перед импортом модуля.
from random import randint

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


class Block(sdl2.ext.Entity):
    def __init__(self, world, factory, color, x, y, size):
        self.sprite = factory.from_color(color, size)
        self.sprite.position = x, y
        self.velocity = Velocity()


class NegativeBlock(Block):
    _color = sdl2.ext.Color(0, 0, 255)

    def __init__(self, world, factory, x, y, size):
        super().__init__(world, factory, self._color, x, y, size)


class PositiveBlock(Block):
    _color = sdl2.ext.Color(255, 0, 0)

    def __init__(self, world, factory, x, y, size):
        super().__init__(world, factory, self._color, x, y, size)


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
            sprite.x += velocity.vx
            sprite.y += velocity.vy


class Velocity(object):
    def __init__(self):
        super().__init__()
        self.vx = 0
        self.vy = 0


class PositiveBlockFactory(object):
    def __init__(self, world, factory, world_size):
        super().__init__()
        self._world_width = world_size[0]
        self._world_height = world_size[1]
        self._world = world
        self._factory = factory

    def create_block(self):
        width = randint(0, self._world_width / 3)
        height = randint(0, self._world_height / 5)
        x = self._world_width - width
        y = int(-height / 2)

        block = PositiveBlock(self._world, self._factory, x, y, (width, height))
        block.velocity.vy += 1;

        return block


class Game:
    def __init__(self, title, size):
        sdl2.ext.init()
        self._size = size
        self._title = title

    def run(self):
        window = sdl2.ext.Window(self._title, size=self._size)
        window.show()

        world = sdl2.ext.World()
        factory = SpriteFactory()
        movement_system = MovementSystem(0, 0, self._size[0], self._size[1])
        renderer = Renderer(window)
        positive_block_factory = PositiveBlockFactory(world, factory, self._size)

        world.add_system(movement_system)
        world.add_system(renderer)

        positive_block_factory.create_block()

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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
from random import randint

# Установка каталога по которому находится библиотека SDL.
# Необходимо делать перед импортом модуля.
os.environ['PYSDL2_DLL_PATH'] = str(Path(sys.argv[0]).parent)

import sdl2.ext  # nopep8


class Velocity(object):
    def __init__(self):
        super().__init__()
        self.vx = 0
        self.vy = 0


class Renderer(sdl2.ext.SoftwareSpriteRenderSystem):
    def __init__(self, window):
        super().__init__(window)

    def render(self, sprites, x=None, y=None):
        sdl2.ext.fill(self.surface, sdl2.ext.Color(0, 0, 0))
        super().render(sprites)


class SpriteFactory(sdl2.ext.SpriteFactory):
    def __init__(self):
        super(SpriteFactory, self).__init__(sdl2.ext.SOFTWARE)


class Block(sdl2.ext.Entity):
    def __init__(self, world, factory, color, x, y, width, height):
        self.sprite = factory.from_color(color, (width, height))
        self.sprite.position = x, y
        self.velocity = Velocity()

    @property
    def y(self):
        return self.sprite.y

    @property
    def height(self):
        return self.sprite.size[1]


class NegativeBlock(Block):
    _color = sdl2.ext.Color(0, 0, 255)

    def __init__(self, world, factory, x, y, width, height):
        super().__init__(world, factory, self._color, x, y, width, height)


class PositiveBlock(Block):
    _color = sdl2.ext.Color(255, 0, 0)

    def __init__(self, world, factory, x, y, width, height):
        super().__init__(world, factory, self._color, x, y, width, height)


class BlockFactory(object):
    def __init__(self, world, factory, size):
        super().__init__()
        self._width = size[0]
        self._height = size[1]
        self._world = world
        self._factory = factory

    def get_block_size(self):
        width = randint(int(self._width / 5), int(self._width / 3))
        height = randint(int(self._height / 7), int(self._height / 5))

        return width, height

    def do_create_block(self, width, height):
        raise NotImplementedError()

    def create_block(self):
        width, height = self.get_block_size()
        block = self.do_create_block(width, height)
        block.velocity.vy = 1

        return block


class PositiveBlockFactory(BlockFactory):
    def __init__(self, world, factory, size):
        super().__init__(world, factory, size)

    def do_create_block(self, width, height):
        x = self._width - width
        y = -height - 1

        block = PositiveBlock(self._world, self._factory, x, y, width, height)

        return block


class NegativeBlockFactory(BlockFactory):
    def __init__(self, world, factory, size):
        super().__init__(world, factory, size)

    def do_create_block(self, width, height):
        x = 0
        y = -height - 1

        block = NegativeBlock(self._world, self._factory, x, y, width, height)

        return block


class BlockMovementSystem(sdl2.ext.Applicator):
    def __init__(self, size):
        super().__init__()
        self._width = size[0]
        self._height = size[1]
        self.componenttypes = Velocity, sdl2.ext.Sprite

    def process(self, world, components):
        for velocity, sprite in components:
            sprite.y += velocity.vy


class BlockManagementSystem(sdl2.ext.Applicator):
    def __init__(self, size, factory: BlockFactory):
        super().__init__()
        self._factory = factory
        self._blocks = []
        self._height = size[1]
        self.componenttypes = sdl2.ext.Sprite, sdl2.ext.Sprite

    def create_block(self):
        block = self._factory.create_block()
        self._blocks.append(block)

    def process(self, world, components):
        if not self._blocks:
            self.create_block()
            return

        blocks = []
        need_create_block = True
        for block in self._blocks:
            if need_create_block and (block.y < 0):
                need_create_block = False

            if (block.y - block.height) > self._height:
                block.delete()
            else:
                blocks.append(block)

        self._blocks = blocks

        if need_create_block:
            self.create_block()


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
        positive_block_factory = PositiveBlockFactory(world, factory, self._size)
        negative_block_factory = NegativeBlockFactory(world, factory, self._size)
        movement_system = BlockMovementSystem(self._size)
        positive_block_management_system = BlockManagementSystem(self._size, positive_block_factory)
        negative_block_management_system = BlockManagementSystem(self._size, negative_block_factory)
        renderer = Renderer(window)

        world.add_system(negative_block_management_system)
        world.add_system(positive_block_management_system)
        world.add_system(movement_system)
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

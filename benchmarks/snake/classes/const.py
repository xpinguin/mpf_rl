#!/usr/bin/env python

import sys, pygame


FPS = 12
MIN_FPS = 3
MAX_FPS = 60
FREEZING_POINT = 9  # target FPS when Blueberry (slow) is in effect.

# set width and height of screen - optional arguments:
# python snakey_party.py [width] [height]
if len(sys.argv) > 1:
    try:
        WINDOWWIDTH = int(sys.argv[1])
    except ValueError:
        print("Width is not an integer.")
    if len(sys.argv) > 2:
        try:
            WINDOWHEIGHT = int(sys.argv[2])
        except ValueError:
            print("Height is not an integer.")
    else:
        WINDOWHEIGHT = 480
else:
    WINDOWWIDTH = 640
    WINDOWHEIGHT = 480

CELLSIZE = 20

# displays in-game info
# set so that 1 cell is reserved for 640x480, 2 cells for 800x600
TOP_BUFFER = CELLSIZE * int(WINDOWWIDTH * WINDOWHEIGHT / 200000)
CELLWIDTH = int(WINDOWWIDTH / CELLSIZE)
CELLHEIGHT = int((WINDOWHEIGHT - TOP_BUFFER) / CELLSIZE)

# text sizes for titles
MEDIUMTITLE = int(WINDOWWIDTH * WINDOWHEIGHT / 9600)
LARGETITLE = int(WINDOWWIDTH * WINDOWHEIGHT / 6400)
XLARGETITLE = int(WINDOWWIDTH * WINDOWHEIGHT / 4800)

# colors - (R G B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
COBALTGREEN = (61, 145, 64)
DARKBLUE = (25, 25, 112)
DARKGRAY = (40, 40, 40)
FORESTGREEN = (34, 139, 34)
GOLDENROD = (218, 165, 32)
GREEN = (0, 255, 0)
IVORY = (205, 205, 193)
ORANGE = (255, 127, 0)
PINK = (255, 105, 180)
PURPLE = (142, 56, 142)
RED = (255, 0, 0)
SLATEBLUE = (131, 111, 255)
YELLOW = (238, 238, 0)

BACKGROUNDCLR = BLACK
BUTTONCLR = GREEN
BUTTONTXT = DARKGRAY
BUTTONCLR_SEL = COBALTGREEN
BUTTONTXT_SEL = GOLDENROD
MESSAGECLR = GREEN

# for consistency
UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'
SNAKEY = 'snakey'
LINUS = 'linus'
WIGGLES = 'wiggles'
GOOBER = 'goober'

MPFBOT = 'MPF Bot'

# index of snake's head
HEAD = 0

# minimum and maximum frames fruit remains on screen - determined randomly
POISONTIMER = (100, 200)
ORANGETIMER = (35, 65)
RASPBERRYTIMER = (30, 45)
BLUEBERRYTIMER = (20, 40)
LEMONTIMER = (100, 100)
EGGTIMER = (40, 70)

global FPSCLOCK, DISPLAYSURF, DEBUG

pygame.init()
FPSCLOCK = pygame.time.Clock()
DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
DEBUG = False
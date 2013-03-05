#!/usr/bin/env python

import random, pygame, sys
from pygame.locals import *
from const import *
from methods import *
from fruit import *


class GameData:
    """
    Responsible for dynamics for a particular game instance.
    fruitEaten - a dictionary containing a numeric tally of each fruit eaten.
    speedTrigger - the frequency (based on apples consumed) in which gamespeed is increased by one.
    bonusFruitTrigger - the frequency (based on apples consumed) in which a bonus game is launched.
    easyTrigger - a threshold (apples consumed); once reached fruit can be placed anywhere on screen (as opposed to away from edges).
    currentplace - the current 'place' of snake. When snake has died.
    apples - number of apples on screen.
    """
    def __init__(self, st=20, bft=10, et=20, a=0):
        self.fruitEaten = {'apple':0, 'poison':0, 'orange':0, 'raspberry':0,
                           'blueberry':0, 'lemon':0, 'egg':0}
        self.speedTrigger = st
        self.bonusFruitTrigger = bft
        self.easyTrigger = et
        self.currentplace = 1
        self.apples = a
        self.basespeed = FPS
        self.currentspeed = self.basespeed
        self.slowtimer = 0
        self.trailing = False
        self.poisonDrop = 4
        self.orangeDrop = 5
        self.raspberryDrop = 6
        self.blueberryDrop = 25
        self.lemonDrop = 100
        self.eggDrop = 12

    def checkSpeedTrigger(self):
        """
        Returns true if number of apples consumed modulo speedTrigger equals zero.
        """
        if self.fruitEaten['apple'] % self.speedTrigger == 0:
            return True
        else:
            return False

    def checkBonusTrigger(self):
        """
        Returns true if number of apples consumed modulo bonusTrigger equals zero.
        """
        if self.fruitEaten['apple'] % self.bonusFruitTrigger == 0:
            return True
        else:
            return False

    def checkEasyTrigger(self):
        """
        Returns true if number of apples consumed is less than or equal to easyTrigger.
        """
        if self.fruitEaten['apple'] <= self.easyTrigger:
            return True
        else:
            return False
            
    def checkSnakeDeath(self, allsnake):
        """
        Returns true if there are no more living snakes.
        Sets place of snake if recently died.
        """
        gameover = True
        for snake in allsnake:
            if snake.scored == True:
                if snake.alive == True:
                    gameover = False
                elif snake.place == False:
                    snake.place = self.currentplace
                    self.currentplace = self.currentplace + 1
        return gameover
        
    def updateBaseSpeed(self, value):
        """
        Updates basespeed by value inputted.
        Checks against parameters
        """
        if (self.basespeed + value > MIN_FPS) and \
           (self.basespeed + value < MAX_FPS):
            self.basespeed = self.basespeed + value
            self.currentspeed = self.basespeed
            
    def updateCurrentSpeed(self, goal=False, force=False):
        """
        Adjusts currentspeed one towards goal.
        Goal defaults to basespeed.
        Optional 'force' will set currentspeed to goal instead.
        """
        if goal == False:
            goal = self.basespeed
            
        if force != False:
            self.currentspeed = goal
        else:
            if self.currentspeed < goal:
                self.currentspeed = self.currentspeed + 1
            elif self.currentspeed > goal:
                self.currentspeed = self.currentspeed - 1

    def checkSlowTimer(self):
        """
        Returns true if slowtimer is greater than 0.
        """
        if self.slowtimer > 0:
            return True
        else:
            return False

    def updateSlowTimer(self):
        """
        Decrements slowtimer by one
        """
        self.slowtimer = self.slowtimer - 1
        
    def runDrop(self, allfruit, allsnake):
        """
        Adds fruit randomly to screen.
        If newapple is turned on, replaces apple that was eaten.
        """
        # chance of poison drop
        if self.poisonDrop != False and random.randint(1,self.poisonDrop) == 1:
            p = Poison(allfruit, allsnake, self)
            allfruit.append(p)
        # chance of orange drop
        if self.orangeDrop != False and random.randint(1,self.orangeDrop) == 1:
            o = Orange(allfruit, allsnake, self)
            allfruit.append(o)
        # chance of raspberry drop
        if self.raspberryDrop != False and random.randint(1,self.raspberryDrop) == 1:
            r = Raspberry(allfruit, allsnake, self)
            allfruit.append(r)
        # chance of blueberry drop
        if self.blueberryDrop != False and random.randint(1,self.blueberryDrop) == 1:
            b = Blueberry(allfruit, allsnake, self)
            allfruit.append(b)
        # chance of lemon drop
        if self.lemonDrop != False and random.randint(1,self.lemonDrop) == 1:
            l = Lemon(allfruit, allsnake, self)
            allfruit.append(l)
        # chance of egg drop
        if self.eggDrop != False and random.randint(1,self.eggDrop) == 1:
            e = Egg(allfruit, allsnake, self)
            allfruit.append(e)
        # create new apple
        a = Apple(allfruit, allsnake, self)
        allfruit.append(a)

    def runBonusFruit(self, allfruit, allsnake):
        """
        Returns a list containing fruit (as strings) to be added to game from bonus game.
        An integer (determined randomly between typeMin and typeMax) corresponds to bonus game run.
        A basic set-up would randomly choose between 1 and 10; 6 through 10 initiating a fruit specific bonus.
        Default will contain an assortment of fruit.
        """
        bonus = []
        type = random.randint(1, 20)
        
        # drop amounts based on size of playing field
        squares = CELLWIDTH * CELLHEIGHT
        tinyLower = int(squares / 600)
        tinyUpper = int(squares / 135)
        smallLower = int(squares / 68)
        smallUpper = int(squares / 45)
        largeLower = int(squares / 34)
        largeUpper = int(squares / 19)
        
        # based on bonus type, create fruits
        if type == 1:
            counter = random.randint(smallLower,smallUpper)
            while counter > 0:
                bonus.append('egg')
                counter = counter - 1
        elif type == 2 or type == 3:
            counter = random.randint(largeLower,largeUpper)
            while counter > 0:
                bonus.append('poison')
                counter = counter - 1
        elif type == 4 or type == 5:
            counter = random.randint(largeLower,largeUpper)
            while counter > 0:
                bonus.append('orange')
                counter = counter - 1
        elif type == 6:
            counter = random.randint(largeLower,largeUpper)
            while counter > 0:
                bonus.append('raspberry')
                counter = counter - 1
        elif type == 7:
            counter = random.randint(largeLower,largeUpper)
            while counter > 0:
                bonus.append('blueberry')
                counter = counter - 1
        # default bonus
        else:
            counter = random.randint(tinyLower, tinyUpper)
            while counter > 0:
                bonus.append('poison')
                counter = counter - 1
            counter = random.randint(5,20)
            while counter > 0:
                bonus.append('orange')
                counter = counter - 1
            counter = random.randint(tinyLower, tinyUpper)
            while counter > 0:
                bonus.append('raspberry')
                counter = counter - 1
            counter = random.randint(tinyLower, tinyUpper)
            while counter > 0:
                bonus.append('blueberry')
                counter = counter - 1
        
        # add fruits
        for bonusfruit in bonus:
            if bonusfruit == 'poison':
                f = Poison(allfruit, allsnake, self)
            elif bonusfruit == 'orange':
                f = Orange(allfruit, allsnake, self)
            elif bonusfruit == 'raspberry':
                f = Raspberry(allfruit, allsnake, self)
            elif bonusfruit == 'blueberry':
                f = Blueberry(allfruit, allsnake, self)
            elif bonusfruit == 'lemon':
                f = Lemon(allfruit, allsnake, self)
            elif bonusfruit == 'egg':
                f = Egg(allfruit, allsnake, self)
            allfruit.append(f)
            
    def drawScreen(self, allfruit, allsnake, player):
        """
        Responsible for drawing everything onto screen.
        """
        # clear background
        DISPLAYSURF.fill(BACKGROUNDCLR)

        # check slow and adjust fps as needed
        # draw grid to screen as well (color based on slow or normal)
        if self.checkSlowTimer():
            self.updateSlowTimer()
            self.updateCurrentSpeed(FREEZING_POINT)
            self.drawGrid(DARKBLUE)
        else:
            self.updateCurrentSpeed()
            self.drawGrid()

        # draw everything else to screen
        for fruit in allfruit:
            fruit.drawFruit()
        for snake in allsnake:
            snake.drawSnake()
            
        # print scores only if snake is scored
        position = 1
        for snake in allsnake:
            if snake.scored == True:
                snake.drawScore(position, allsnake)
                position = position + 1

        # if player is dead, print extra messages
        if player == False or player.alive == False:
            endMessage = 'press (e) to end game early'
            fastMessage = 'press (f) to fast-forward game'
            slowMessage = 'press (s) to slow game'
            drawMessage(endMessage, WINDOWWIDTH / 2, WINDOWHEIGHT / 20 * 16)
            drawMessage(fastMessage, WINDOWWIDTH / 2, WINDOWHEIGHT / 20 * 17)
            drawMessage(slowMessage, WINDOWWIDTH / 2, WINDOWHEIGHT / 20 * 18)
        pygame.display.update()
        FPSCLOCK.tick(self.currentspeed)
        
    def drawGrid(self, color=DARKGRAY):
        """
        Draws grid to screen.
        """
        for x in range(0, WINDOWWIDTH, CELLSIZE): # draw vertical lines
            pygame.draw.line(DISPLAYSURF, color, (x, TOP_BUFFER), (x, WINDOWHEIGHT))
        for y in range(TOP_BUFFER, WINDOWHEIGHT, CELLSIZE): # draw horizontal lines
            pygame.draw.line(DISPLAYSURF, color, (0, y), (WINDOWWIDTH, y))

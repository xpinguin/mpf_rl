#!/usr/bin/env python


from pygame.locals import *
from const import *
from snake import *

import random, pygame, sys

class Fruit:
    """
    Fruit class houses all information for fruit objects. 
    Base class is not meant to be instantiated, but rather provide base methods shared by all fruit.
    """
    def __init__(self):
        self.timer = 0

    def getRandomLocation(self, allfruit, allsnake, game):
        """
        Returns random coordinates (for fruit to be placed). Ensures that coordinates are not occupied by fruit or snake head.
        Will keep fruit away from edges (outside 20%) if in an "easy mode" determined in Tally object.
        """
        while True:
            conflict = False
            if game.checkEasyTrigger():
                x = random.randint(int(CELLWIDTH/5), CELLWIDTH - int(CELLWIDTH/5) - 1)
                y = random.randint(int(CELLHEIGHT/5), CELLHEIGHT - int(CELLHEIGHT/5) - 1)
            else:
                x = random.randint(0, CELLWIDTH - 1)
                y = random.randint((TOP_BUFFER / CELLSIZE), CELLHEIGHT - 1)
            # ensure coordinates are not already occupied by fruit
            for fruit in allfruit:
                if fruit.coords['x'] == x and fruit.coords['y'] == y:
                    conflict = True
            # ensure coordinates are not already occupied by snake head
            for snake in allsnake:
                if snake.getCoords('x') == x and snake.getCoords('y') == y:
                    conflict = True
            if conflict == False:
                return {'x':x, 'y':y}

    def updateTimer(self):
        """
        Returns true and decrements if there is still time left for fruit to be on screen.
        """
        if self.timer > 0:
            self.timer = self.timer - 1
            return True 
        else:
            return False

    def drawFruit(self):
        """
        Responsible for drawing fruit image to screen.
        """
        x = self.coords['x'] * CELLSIZE
        y = self.coords['y'] * CELLSIZE
        fruitRect = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
        pygame.draw.rect(DISPLAYSURF, self.color, fruitRect)


class Apple(Fruit):
    """
    Apples are a unique fruit in that they never leave the screen and once one is eaten, it is always replaced with another.
    They also add points and one growth
    """
    def __init__(self, allfruit, allsnake, game):
        self.coords = Fruit.getRandomLocation(self, allfruit, allsnake, game)
        self.color = RED
        self.points = 10
        self.growth = 1

    def isEaten(self, snake, game):
        snake.fruitEaten['apple'] = snake.fruitEaten['apple'] + 1
        game.fruitEaten['apple'] = game.fruitEaten['apple'] + 1
        snake.updateScore(self.points)
        snake.updateGrowth(self.growth)
        snake.updateColor({'red': 6, 'green': -5, 'blue': -5})

    def drawFruit(self):
        Fruit.drawFruit(self)


class Poison(Fruit):
    """
    Poison will shorten a snake (by adding a negative growth value) and reduce points.
    """
    def __init__(self, allfruit, allsnake, game):
        self.coords = Fruit.getRandomLocation(self, allfruit, allsnake, game)
        self.timer = random.randint(POISONTIMER[0], POISONTIMER[1])
        self.color = GREEN
        self.points = -25
        self.growth = -3

    def isEaten(self, snake, game):
        snake.fruitEaten['poison'] = snake.fruitEaten['poison'] + 1
        game.fruitEaten['poison'] = game.fruitEaten['poison'] + 1
        snake.updateScore(self.points)
        snake.updateGrowth(self.growth)
        snake.updateColor({'red': -20, 'green': 20})

    def updateTimer(self):
        return Fruit.updateTimer(self)

    def drawFruit(self):
        Fruit.drawFruit(self)
        

class Orange(Fruit):
    """
    Orange will grow snake substantially and are worth points.
    """
    def __init__(self, allfruit, allsnake, game):
        self.coords = Fruit.getRandomLocation(self, allfruit, allsnake, game)
        self.timer = random.randint(ORANGETIMER[0], ORANGETIMER[1])
        self.color = ORANGE
        self.points = 50
        self.growth = 3

    def isEaten(self, snake, game):
        snake.fruitEaten['orange'] = snake.fruitEaten['orange'] + 1
        game.fruitEaten['orange'] = game.fruitEaten['orange'] + 1
        snake.updateScore(self.points)
        snake.updateGrowth(self.growth)
        snake.updateColor({'red': 10, 'green': 3, 'blue': -10})

    def updateTimer(self):
        return Fruit.updateTimer(self)

    def drawFruit(self):
        Fruit.drawFruit(self)


class Raspberry(Fruit):
    """
    Raspberry will set snake's multiplier to two for a period of time.
    """
    def __init__(self, allfruit, allsnake, game):
        self.coords = Fruit.getRandomLocation(self, allfruit, allsnake, game)
        self.timer = random.randint(RASPBERRYTIMER[0], RASPBERRYTIMER[1])
        self.color = PURPLE
        self.multiplier = 2
        self.multipliertimer = 100

    def isEaten(self, snake, game):
        snake.fruitEaten['raspberry'] = snake.fruitEaten['raspberry'] + 1
        game.fruitEaten['raspberry'] = game.fruitEaten['raspberry'] + 1
        snake.updateMultiplier(self.multiplier, self.multipliertimer)
        snake.updateColor({'red': 12, 'green': -15, 'blue': 13})

    def updateTimer(self):
        return Fruit.updateTimer(self)

    def drawFruit(self):
        Fruit.drawFruit(self)


class Blueberry(Fruit):
    """
    Blueberry will reduce the frame rate (slowing down game iterations) for a period of time.
    It is also worth a lot of points.
    """
    def __init__(self, allfruit, allsnake, game):
        self.coords = Fruit.getRandomLocation(self, allfruit, allsnake, game)
        self.timer = random.randint(BLUEBERRYTIMER[0], BLUEBERRYTIMER[1])
        self.color = BLUE
        self.score = 100
        self.slowtimer = 80

    def isEaten(self, snake, game):
        snake.fruitEaten['blueberry'] = snake.fruitEaten['blueberry'] + 1
        game.fruitEaten['blueberry'] = game.fruitEaten['blueberry'] + 1
        snake.updateScore(self.score)
        snake.updateColor({'red': -20, 'green': -15, 'blue': 60})

    def updateTimer(self):
        return Fruit.updateTimer(self)

    def drawFruit(self):
        Fruit.drawFruit(self)


class Lemon(Fruit):
    """
    Lemon will grow snake to mythic proportions.
    """
    def __init__(self, allfruit, allsnake, game):
        self.coords = Fruit.getRandomLocation(self, allfruit, allsnake, game)
        self.timer = random.randint(LEMONTIMER[0], LEMONTIMER[1])
        self.color = YELLOW
        self.score = 500
        self.growth = 20

    def isEaten(self, snake, game):
        snake.fruitEaten['lemon'] = snake.fruitEaten['lemon'] + 1
        game.fruitEaten['lemon'] = game.fruitEaten['lemon'] + 1
        snake.updateScore(self.score)
        snake.updateGrowth(self.growth)
        snake.updateColor({'blue': -20})

    def updateTimer(self):
        return Fruit.updateTimer(self)

    def drawFruit(self):
        Fruit.drawFruit(self)
        
        
class Egg(Fruit):
    """
    Eggs spawn another snake if not eaten.
    """
    def __init__(self, allfruit, allsnake, game):
        self.coords = Fruit.getRandomLocation(self, allfruit, allsnake, game)
        self.timer = random.randint(EGGTIMER[0], EGGTIMER[1])
        self.color = GOLDENROD
        self.colorBorder = WHITE
        self.points = 250
        self.growth = 1
        self.radius = CELLSIZE / 2

    def isEaten(self, snake, game):
        snake.fruitEaten['egg'] = snake.fruitEaten['egg'] + 1
        game.fruitEaten['egg'] = game.fruitEaten['egg'] + 1
        snake.updateScore(self.points)
        snake.updateGrowth(self.growth)
        snake.updateColor({'red': -35, 'green': -30, 'blue': -25})

    def updateTimer(self):
        """
        Also adjusts radius size depending on time remaining.
        """
        if self.timer < (EGGTIMER[0] + EGGTIMER[1]) * 2 / 3:
            self.radius = CELLSIZE / 3
        if self.timer < (EGGTIMER[0] + EGGTIMER[1]) / 2:
            self.radius = CELLSIZE / 4
        if self.timer < (EGGTIMER[0] + EGGTIMER[1]) / 3:
            self.radius = CELLSIZE / 5
        return Fruit.updateTimer(self)

    def isHatched(self, allsnake):
        """
        Add new snake with coords as coords of fruit, and growth of 3.
        Snake is not scored (name and score does not appear).
        """
        junior = Opponent('junior', [{'x':self.coords['x'] , 'y':self.coords['y']}], PINK, GREEN, 10, 10, -20, [35, 5, 40, 30, 35, 15, 0])
        junior.growth = 3
        junior.scored = False
        allsnake.append(junior)

    def drawFruit(self):
        """
        Responsible for drawing image to screen.
        """
        x = self.coords['x'] * CELLSIZE
        y = self.coords['y'] * CELLSIZE
        xNext = (self.coords['x'] + 1) * CELLSIZE
        yNext = (self.coords['y'] + 1) * CELLSIZE
        center = ((xNext + x) / 2, (yNext + y) / 2)
        fruitRect = pygame.Rect(x, y, CELLSIZE, CELLSIZE)
        pygame.draw.rect(DISPLAYSURF, self.colorBorder, fruitRect)
        pygame.draw.circle(DISPLAYSURF, self.color, center, self.radius)

#!/usr/bin/env python

import random, pygame, sys
from pygame.locals import *
from const import *


class Button():
    """
    A clickable button that is rendered on screen.
    """
    def __init__(self, text, x, y):
        self.text = text
        size = int (WINDOWWIDTH / 18)
        self.font = pygame.font.Font('freesansbold.ttf', size)
        self.startSurf = self.font.render(self.text, True, BUTTONCLR, BUTTONTXT)
        self.rect = self.startSurf.get_rect()
        self.rect.center = x,y

    def display(self):
        DISPLAYSURF.blit(self.startSurf, self.rect)

    def pressed(self, mouse):
        if mouse[0] > self.rect.topleft[0] and \
           mouse[1] > self.rect.topleft[1] and \
           mouse[0] < self.rect.bottomright[0] and \
           mouse[1] < self.rect.bottomright[1]:
            return True
        else:
            return False


class SelectButton(Button):
    """
    Selected by color. Clicking will turn active state to True.
    Contains a value that is returned with getValue().
    """
    def __init__(self, text, x, y, v, a=False):
        Button.__init__(self, text, x, y)
        self.value = v
        self.active = a
        
    def display(self):
        if self.active == True:
            self.startSurf = self.font.render(self.text, True, BUTTONCLR_SEL, BUTTONTXT_SEL)
        else:
            self.startSurf = self.font.render(self.text, True, BUTTONCLR, BUTTONTXT)
            
        DISPLAYSURF.blit(self.startSurf, self.rect)
        
    def pressed(self, mouse):
        return Button.pressed(self, mouse)

    def getActive(self):
        return self.active

    def setActive(self, buttonlist):
        for button in buttonlist:
            if button == self:
                self.active = True
            else:
                button.active = False
                
    def getValue(self):
        return self.value


class InputButton(Button, SelectButton):
    """
    still in testing
    """
    def __init__(self, value, x, y, min=1, max=9999, a=False):
        # set-up center rectangle
        self.value = value
        size = int (WINDOWWIDTH / 18)
        self.font = pygame.font.Font('freesansbold.ttf', size)
        self.startSurf = self.font.render('-', True, BUTTONCLR, BUTTONTXT)
        self.rect = self.startSurf.get_rect()
        self.rect.center = x,y
        self.min = min
        self.max = max
        self.active = a
        # set-up decrease arrow
        self.decreaseSurf = pygame.Surface((size, size))
        self.decreaseSurf.fill(GREEN)
        # set-up increase arrow
        self.increaseSurf = pygame.Surface((size, size))
        self.increaseSurf.fill(GREEN)
        #arrowcenterleft = (self.rect.left - size, self.rect.centery)
        #self.decrease = pygame.draw.lines(self.decreaseSurf, BLACK, True, [self.rect.topleft, arrowcenterleft, self.rect.bottomleft], 3)
        self.decrease = self.decreaseSurf.get_rect(topleft=(self.rect.topleft[0] - size, self.rect.topleft[1]))
        self.increase = self.increaseSurf.get_rect(topleft=(self.rect.topright[0] + size, self.rect.topright[1]))

    def display(self):
        if self.active == True:
            self.startSurf = self.font.render(str(self.value), True, BUTTONCLR_SEL, BUTTONTXT_SEL)
        else:
            self.startSurf = self.font.render(str(self.value), True, BUTTONCLR, BUTTONTXT)

        DISPLAYSURF.blit(self.startSurf, self.rect)
        DISPLAYSURF.blit(self.decreaseSurf, self.decrease)
        DISPLAYSURF.blit(self.increaseSurf, self.increase)
        
    def pressed(self, mouse, buttonlist):
        # if decrease is pressed
        if mouse[0] > self.decrease.topleft[0] and \
           mouse[1] > self.decrease.topleft[1] and \
           mouse[0] < self.decrease.bottomright[0] and \
           mouse[1] < self.decrease.bottomright[1]:
            self.setActive(buttonlist)
            self.setValue(-1)
        # if increase is pressed
        elif mouse[0] > self.increase.topleft[0] and \
           mouse[1] > self.increase.topleft[1] and \
           mouse[0] < self.increase.bottomright[0] and \
           mouse[1] < self.increase.bottomright[1]:
            self.setActive(buttonlist)
            self.setValue(1)
        elif Button.pressed(self, mouse):
            self.setActive(buttonlist)

    def getActive(self):
        return SelectButton.getActive(self)
        
    def setActive(self, buttonlist):
        SelectButton.setActive(self, buttonlist)
        
    def getValue(self):
        return SelectButton.getValue(self)
        
    def setValue(self, change):
        newValue = self.value + change
        if newValue <= self.max and newValue >= self.min:
            self.value = newValue

import pygame 
import os 
os.environ['SDL_VIDEO_CENTERED'] = '1'

from pygame.locals import *

#Helper class that controls interaction loop in Pygame
from pygamehelper import *

#Get the definition of the World
from BugWorld import *

#main control loop of the pygame
class BugSim( PygameHelper ):
	
	def __init__(Self):
		Self.BW = BugWorld() #instantiate the world and its objects
		super(BugSim,Self).__init__( (Self.BW.BOUNDARY_WIDTH, Self.BW.BOUNDARY_HEIGHT), Color.WHITE )

	def update(Self): #update everything in the world
		Self.BW.update()


	def draw( Self ): #draw the resulting world
		Self.screen.fill(Color.WHITE)
		Self.BW.draw(Self.screen)
		pygame.display.update()

	def keyDown(Self, key):
		
		if key == K_SPACE:
			pass
		elif key == K_LEFT:
			pass
		elif key == K_RIGHT:
			pass
		else:
			print(key)

		
if __name__ == "__main__":
	g = BugSim()
	g.mainLoop(60)
    

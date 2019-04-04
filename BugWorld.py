
#PGBugWorld where pygame dependent code goes
#contains draw code
#toggle display of light, smell, sound

#----------------- START PYGAME SPECIFIC CODE ---------------------------------------
import pygame

#assume 2D graphics and using Pygame to render.
class PGObject():
	color = (0, 0, 0)  # default, must be overwritten
	size = 1  # default, must be overwritten

	def draw(self, surface, fill=0): #fill = 0 means solid, = 1 means outline only
		x = int(self.get_abs_x())
		y = int(self.get_abs_y())
		r, g, b = self.color #unpack the tuple

#TODO modulate color based on health
		# hp = Self.health/100 #what is the health percentage
		# r *= hp
		# g *= hp
		# b *= hp

		pygame.draw.circle(surface, (int(r), int(g), int(b)), (x, y), self.size, fill)
	
	def get_abs_x(self):  # must be overwritten
		return 0

	def get_abs_y(self):  # must be overwritten
		return 0


#world for simulations to happen 
#has boundaries
#has objects
#	- determines which type
#	- determines where and when
#	- kills objects
#	- determines rules for affecting object attributes (health, mutating, mating)


#objects register for different types of collisions (physical, sound, smell, light(RGB))
#objects have hitboxes for each sensor.


#objects emit light at 1/r^2 three different colors
#how do you keep senses from sensing itself
#objects emit sound (varies on speed)
#objects emit smell
#objects have physical collision
#objects have smell collision
#objects have sound collision
#eyes collide with objects and extracts RGB values from the target object .color tuple
#eye collision also gives distance
#bodies collide with other solid bodies

# has the sample time which is the update loop time...used for velocity and accleration

#detects collisions
#	- different hitbox shapes.  Hitbox needed for eyes so that collisions can be detected
#		in field of vision (use circles to start for everything.  Could use cones for vision eventually)
#	- should return "distance" so can be used for intensity
#	- returns an intensity of collision (for eye interaction with light, sound, smell)


#contains rules of interactions
#how do bugs die
#have a score that indicates successfulness (distance travelled, area covered, energy amount (expended moving, gained eating) )
#how do bugs reproduce (should we use the "weakest 500" to avoid extinction events)

#need global counters so can do rates to keep populations stable.
#timer
	#controls rates like food introduction, mating
	#creates extinction events

#Iterations/generations/epoch:
	#can be used to create extinction events in so many cycles

#Need a point system to keep track of goal reinforcement
	#points for distance travelled (would incent to move.  otherwise would just sit still to max energy/health)
	#points for time alive
	#points for food eaten
	#could use energy and health

#Need an energy system
	#controls whether starves
	#consume energy based on speed
	#speed driven by amount of energy

import numpy as np
import random

#Going to use 3D matrices even if in 2d
#See http://matthew-brett.github.io/transforms3d/ for details on the lib used
#Object's local coord frame is in the x,y plane and faces in the x direction.  
#Positive rotation follow RHR, x-axis into the y-axis...so z is up.
import transforms3d.affines as AFF 
import transforms3d.euler as E

from Collisions import *

#Color class so can separate out code from PG specific stuff.
#http://www.discoveryplayground.com/computer-programming-for-kids/rgb-colors/
class Color(): #RGB values
	BLACK = (0, 0, 0)
	WHITE = (255, 255, 255)
	RED = (255, 0, 0)
	GREEN = (0, 255, 0)
	BLUE = (0, 0, 255)
	YELLOW = (255, 255, 0)
	PINK = (255, 192, 203)
	BROWN = (160, 82, 45)
	ORANGE = (255, 165, 0)
	DARK_GREEN = (34, 139, 34)
	GREY = (190, 190, 190)


class BWOType:
	''' Defines the different types of objects allowed within a Bug World '''

	# use integers so it is faster for dict lookups
	BUG = int(1)
	HERB = int(2)  	# Herbivore
	OMN = int(3)  	# Omnivore
	CARN = int(4)  	# Carnivore
	OBST = int(5)  	# Obstacle
	MEAT = int(6)  	# Food for Carnivore and Omnivore
	PLANT = int(7)  # Food for Herbivore and Omnivore
	EYE = int(8)  	# for eyes
	OBJ = int(9)  	# catch all for the base class.  Shouldn't ever show up

	
class BWCollisionDict:  	# Dictionary: two types as the keys, function as the item
							# passes pointers into each object

	def print_collision(OB1, OB2):
		# print(OB1.name + 'T: ' + str(OB1.type) + ' H: ' + str(OB1.health) + ', ' 
			# + OB2.name + 'T: ' + str(OB2.type) + ' H: ' + str(OB2.health))
		pass

#Bug to Bug interactions
	def herb_omn(self, herb, omn):  # handle herbivore an omnivore collision
		BWCollisionDict.print_collision(herb, omn)
		# do damage to herbivore
		herb.health -= 1

	def herb_carn(self, herb, carn):
		BWCollisionDict.print_collision(herb, carn )
		# do damage to herbivore
		herb.health -= 20

	def herb_herb(self, herb1, herb2):
		BWCollisionDict.print_collision(herb1, herb2)
		#certain probability of mating?

	def omn_omn(self, omn1, omn2):
		BWCollisionDict.print_collision(omn1, omn2)
		# certain probability of mating?

	def omn_carn(self, omn, carn):
		BWCollisionDict.print_collision(omn, carn)
		# do damage to omn
		omn.health -= 20
		carn.health -= 5

	def carn_carn(self, carn1, carn2):
		BWCollisionDict.print_collision(carn1, carn2)
		# certain probability of mating or fighting?
		carn1.health -= 5
		carn2.health -= 5

#Bug to food interactions
	def herb_plant(self, herb, plant):
		BWCollisionDict.print_collision(herb, plant)
		herb.energy += 10
		plant.health -= 10
		if plant.size > 1: plant.size -= 1

	def omn_plant(self, omn, plant):
		BWCollisionDict.print_collision(omn, plant)
		omn.energy += 10
		plant.health -= 10
		if plant.size > 1 : plant.size -= 1

	def omn_meat(self, omn, meat):
		BWCollisionDict.print_collision(omn, meat)
		omn.energy += 10
		meat.health -= 10
		if meat.size > 1: meat.size -= 1

	def carn_meat(self, carn, meat):
		BWCollisionDict.print_collision(carn, meat)
		carn.energy += 10
		meat.health -= 10
		if meat.size > 1: meat.size -= 1

#Bug obstacle interactions
	def herb_obst(self, herb, obst):
		BWCollisionDict.print_collision( herb, obst )
		herb.health -= 1  # ouch obstacles hurt

	def omn_obst(self, omn, obst):
		BWCollisionDict.print_collision(omn, obst)
		omn.health -= 1  # ouch obstacles hurt

	def carn_obst(self, carn, obst):
		BWCollisionDict.print_collision(carn, obst)
		carn.health -= 1  # ouch obstacles hurt

	CollisionDict = {  # look up which function to call when two objects of certain types collide
		(BWOType.HERB, BWOType.OMN): herb_omn,
		(BWOType.HERB, BWOType.CARN): herb_carn,
		(BWOType.HERB, BWOType.HERB): herb_herb,
		(BWOType.OMN, BWOType.OMN): omn_omn,
		(BWOType.OMN, BWOType.CARN): omn_carn,
		(BWOType.CARN, BWOType.CARN): carn_carn,
		(BWOType.HERB, BWOType.PLANT): herb_plant,
		(BWOType.OMN, BWOType.PLANT): omn_plant,
		(BWOType.OMN, BWOType.MEAT): omn_meat,
		(BWOType.CARN, BWOType.MEAT): carn_meat,
		(BWOType.HERB, BWOType.OBST): herb_obst,
		(BWOType.OMN, BWOType.OBST): omn_obst,
		(BWOType.CARN, BWOType.OBST): carn_obst
		}

	def handle_collision(self, ob1, ob2):
		if ob1.type > ob2.type: self.handle_dict(ob2, ob1) #order the keys for dict lookup
		else: self.handle_dict(ob1, ob2)

	def handle_dict(self, ob1, ob2):
		try:
			self.CollisionDict[(ob1.type,ob2.type)](self, ob1, ob2)  # use types to lookup function to call and then call it
		except KeyError:
			pass  # ignore it if isn't in dictionary

			# for debugging
			# if not (OB1.type == BWOType.OBST or OB2.type == BWOType.OBST ): #ignore if something dies on an obstacle
			# 	print('No handler for: ' + OB1.name + ' T:' + str(OB1.type)	+ ", " +
			# 							OB2.name + ' T:' + str(OB2.type))


class BugWorld:  # defines the world, holds the objects, defines the rules of interaction

# --- Class Constants
	BOUNDARY_WIDTH = 800
	BOUNDARY_HEIGHT = 600
	BOUNDARY_WRAP = True

	NUM_CARNIVORE_BUGS = 5
	NUM_OMNIVORE_BUGS = 3
	NUM_HERBIVORE_BUGS = 10
	NUM_PLANT_FOOD = 20
	NUM_MEAT_FOOD = 1
	NUM_OBSTACLES = 5
	IDENTITY = [[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1]]  # equates to x=0, y=0, z=0, rotation = 0
	MAP_TO_CANVAS = [[1,0,0,0], [0,-1,0,BOUNDARY_HEIGHT], [0,0,-1,0], [0,0,0,1]]  # flip x-axis and translate origin

	WorldObjects = []
	BWD = BWCollisionDict()  # instantiate a dictionary to handle collisions

#used for collisions
	#SolidObjects = [] #bugbodies, food, obstacles add themselves to this list
	#LightEmittingObjects = [] #bugbodies, food, obstacles add themselves to this list
	#LightDetectingObjects = [] #add eye hit boxes themselves to this list
	#OdorEmittingObjects 
	#OdorDetectingObjects
	#SoundEmittingObjects
	#SoundDetectingObjects

#--- Instance Methods	
	def __init__(self):
		self.rel_position = BugWorld.MAP_TO_CANVAS #maps Bug World coords to the canvas coords in Pygame
		for i in range(0, BugWorld.NUM_HERBIVORE_BUGS): #instantiate all of the Herbivores with a default name
			start_pos = BugWorld.get_random_location_in_world(self)
			self.WorldObjects.append( Herbivore(start_pos, "H" + str(i)))

		for i in range(0, BugWorld.NUM_CARNIVORE_BUGS):
			start_pos = BugWorld.get_random_location_in_world(self)
			self.WorldObjects.append(Carnivore( start_pos, "C" + str(i)))

		for i in range(0, BugWorld.NUM_OMNIVORE_BUGS):
			start_pos = BugWorld.get_random_location_in_world(self)
			self.WorldObjects.append(Omnivore( start_pos, "O" + str(i)))

		for i in range(0, BugWorld.NUM_OBSTACLES):
			start_pos = BugWorld.get_random_location_in_world(self)
			self.WorldObjects.append( Obstacle( start_pos, "B" + str(i)))

		for i in range(0, BugWorld.NUM_PLANT_FOOD ):
			start_pos = BugWorld.get_random_location_in_world(self)
			self.WorldObjects.append( Plant( start_pos, "P" + str(i)))

		for i in range(0, BugWorld.NUM_MEAT_FOOD):
			start_pos = BugWorld.get_random_location_in_world(self)
			self.WorldObjects.append( Meat( start_pos, "M" + str(i)))

	def update(self):
		for BWO in self.WorldObjects:
			BWO.update(self.rel_position)

		self.detect_collisions()
		self.post_collision_processing()

	def draw(self, surface):
		for BWO in self.WorldObjects:
			BWO.draw(surface)
	
	def detect_collisions(self):
		self.detect_light_collisions()
		self.detect_physical_collisions()

		#detect odor collisions
		#detect sound collisions

	def post_collision_processing(self):
		#loop through objects and delete them, convert them etc.
		#if health < 0, delete.
		#if was a bug, convert it to meat
		#if it was a plant, just delete it

		#need to keep track of where in list when deleting so that when an item is deleted, the range is shortened.
		list_len = len(self.WorldObjects)  # starting length of the list of objects
		i = 0 #index as to where we are in the list

		#loop through every object in the list
		while ( i < list_len ):
			if (self.WorldObjects[i].health <= 0 ): #if the objects health is gone, deal with it.
				co = self.WorldObjects[i] # get the current object

				# if it is a bug, then convert it to meat
				if( co.type in { BWOType.HERB, BWOType.OMN, BWOType.CARN } ):
					start_pos = co.get_abs_position() #get location of the dead bug
					self.WorldObjects.append( Meat( start_pos, "M"+ str(i) )) #create a meat object at same location
					#list length hasn't changed because we are going to delete and add one
				else:
					list_len -= 1	#reduce the length of the list 

				del self.WorldObjects[i] #get rid of the object
				#'i' should now point to the next one in the list because an item was removed so shouldn't have to increment
			else:
				i += 1 #manually increment index pointer because didn't delete the object

	def detect_light_collisions(self):
		#loop through light emitting objects and see if they collide with light detecting
		#make sure doesn't collide with self
		#need to differientiate between RGB detection/emission
		#need to differentiate intensities so objects further away stimulate less
		pass

	def detect_physical_collisions(self):
		#loop through solid bodies
		#call collision handlers on each object
		for bwo1 in self.WorldObjects:
			for bwo2 in self.WorldObjects:
				if bwo1 == bwo2: continue
				elif self.circle_collision(bwo1, bwo2):
					# print("Hit " + bwo1.name + " and " + bwo2.name )
					self.BWD.handle_collision(bwo1, bwo2)

	def circle_collision(self, bwo1, bwo2):	#takes two BugWorld Objects in.
		dx = bwo1.abs_position[0][3] - bwo2.abs_position[0][3]
		dy = bwo1.abs_position[1][3] - bwo2.abs_position[1][3]

		dist_sqrd = (dx * dx) + (dy * dy)
		#size is radius of objections circle hit box
		if (dist_sqrd < (bwo1.size + bwo2.size)**2): return True
		else: return False

#----- Utility Class Methods ----------------

	def adjust_for_boundary(wt):  # adjust an inputed transform to account for world boundaries and wrap
		if BugWorld.BOUNDARY_WRAP:
			if wt[0][3] < 0:  wt[0][3] = BugWorld.BOUNDARY_WIDTH
			elif wt[0][3] > BugWorld.BOUNDARY_WIDTH: wt[0][3] = 0

			if wt[1][3] < 0: wt[1][3] = BugWorld.BOUNDARY_HEIGHT
			elif wt[1][3] > BugWorld.BOUNDARY_HEIGHT: wt[1][3] = 0
		else:
			if wt[0][3] < 0:  wt[0][3] = 0
			elif wt[0][3] > BugWorld.BOUNDARY_WIDTH: wt[0][3] = BugWorld.BOUNDARY_WIDTH

			if wt[1][3] < 0: wt[1][3] = 0
			elif wt[1][3] > BugWorld.BOUNDARY_HEIGHT: wt[1][3] = BugWorld.BOUNDARY_HEIGHT

		return wt  # return the updated transform

	def get_pos_transform(x=0, y=0, z=0, theta=0):  # utility function to encapsulate translation and rotation
		#use this anytime a transform is needed in the world.  
		#assume the angle is measured in the x,y plane around z axis
		#it will be an absolute transform in the local x, y, theta space
		T = [x, y, z] #create a translation matrix
		R = E.euler2mat( 0, 0, theta ) #create a rotation matrix around Z axis.
		Z = [1, 1, 1] # zooms...only included because API required it... will ignore the skew
		return AFF.compose(T, R, Z)

	def get_x(position):
		return position[0][3] 

	def get_y(position):
		return position[1][3] 

	def get_random_location_in_world(self):
		x = random.randint(0, BugWorld.BOUNDARY_WIDTH )
		y = random.randint(0, BugWorld.BOUNDARY_HEIGHT)
		z = 0
		theta = random.uniform(0, 2*np.pi)  # orientation in radians
		return BugWorld.get_pos_transform(x, y, z, theta)
	

class BWObject(PGObject):  # Bug World Object

	#Everything is a BWObject including bug body parts (e.g., eyes, ears, noses).
	#has a position and orientation relative to the container, which could be the world.  But it could be the body, the eye
	#has a color
	#has a size
	#has a name
	#stores an absolute position to prevent recalculating it when passing to contained objects.
	#BWO's should have a draw method that includes itself, hitboxes (based on global var)
	#stub methods for what collisions to register for

	def __init__(self, starting_pos = BugWorld.IDENTITY, name ="BWOBject"):
		self.rel_position = starting_pos
		self.abs_position = starting_pos
		self.name = name
		self.size = 1  # default...needs to be overridden
		self.color = Color.BLACK  # default...needs to be overridden
		self.type = BWOType.OBJ  # default...needs to be overridden
		self.health = 100  # default...needs to be overridden

	def __repr__(self):
		return self.name + ": abs position={}".format(self.abs_position)  # print its name and transform

	def set_rel_position(self, pos_transform = BugWorld.IDENTITY):  # position relative to its container
		self.rel_position = BugWorld.adjust_for_boundary(pos_transform)  # class method handles boundary adjustment
		return self.rel_position

	def set_abs_position(self, base_transform = BugWorld.IDENTITY):
		self.abs_position = np.matmul(base_transform, self.rel_position)
		return self.abs_position

	def get_abs_position(self):
		return self.abs_position

	def get_abs_x(self):
		return BugWorld.get_x(self.abs_position)

	def get_abs_y(self):
		return BugWorld.get_y(self.abs_position)

	def update(self, base): #stub method. Override to move this object each sample period
		pass	


#Things to do
#import logging
#have a scale for drawing in pygame that is independent of bug kinematics


#have a sample period so can do velocity
#simulate collision dynamics to mimic accelerometer
#kinematics for zumo
#kinematics for gopigo

#range
#collisions could do damage
#minimize energy spent
#maximize health


#Bug
#knows how to move
#holds attributes
#has a brain
#has sensors
#has outputs
#Bug parts
#has a shape, size, color, location(relative to base), hitbox(relative to location)
#knows how to draw itself
#knows what type of collisions to register for

class BugEyeHitbox(BWObject):
	def __init__(self, pos_transform=BugWorld.IDENTITY, size=15):
		self.name = "EHB"
		#position should be center of eye + radius of hitbox
		super().__init__(pos_transform, self.name)
		self.size = size
		self.color = Color.GREY

	def update(Self, base):
		# eyes don't move independent of bug, so relative pos won't change.
		Self.set_abs_position(base)  # update it based on the passed in ref frame


class BugEye(BWObject):
	def __init__(self, pos_transform=BugWorld.IDENTITY, size=1):
		self.name = "E"
		super().__init__(pos_transform, self.name)
		self.size = size
		self.color = Color.BLACK
		self.HITBOX_SIZE = self.size * 5

		#add the eye hitbox for the current eye
		#put hitbox so tangent with eye center...actually add 1 so avoid collision with bug just for efficiency
		self.HITBOX_LOC = BugWorld.get_pos_transform((self.HITBOX_SIZE + 1), 0, 0, 0)
		self.hitbox = BugEyeHitbox(self.HITBOX_LOC, self.HITBOX_SIZE)

	def update(self, base):
		# eyes don't move independent of bug, so relative pos won't change.
		self.set_abs_position(base) #update it based on the passed in ref frame
		self.hitbox.update(self.abs_position)

	def draw(self, surface):
		super().draw(surface) #inherited from BWObject
		self.hitbox.draw(surface, 1)


class Bug(BWObject):

	DEFAULT_TURN_AMT = np.deg2rad(30) # turns are in radians
	DEFAULT_MOVE_AMT = 5

	def __init__(self, initial_pos, name ="Bug"):
		super().__init__( initial_pos, name )
		self.size = 10 #override default and set the intial radius of bug
		self.color = Color.PINK #override default and set the initial color of a default bug
		self.energy = 100 #default...needs to be overridden
		self.score = 0 #used to reinforce behaviour.  Add to the score when does a "good" thing

		#add the eyes for a default bug
		#put eye center on circumference, rotate then translate.
		rT = BugWorld.get_pos_transform( 0, 0, 0, np.deg2rad(-30) )
		tT = BugWorld.get_pos_transform(self.size, 0, 0, 0)
		self.RIGHT_EYE_LOC = np.matmul(rT, tT)

		rT = BugWorld.get_pos_transform( 0, 0, 0, np.deg2rad(30) )
		self.LEFT_EYE_LOC = np.matmul(rT, tT)

		self.EYE_SIZE = int(self.size * 0.50) #set a percentage the size of the bug
		#instantiate the eyes
		self.RightEye = BugEye(self.RIGHT_EYE_LOC, self.EYE_SIZE)
#		Self.RightEye.color = Color.RED

		self.LeftEye = BugEye(self.LEFT_EYE_LOC, self.EYE_SIZE)

	def update(self, base):
#		self.wander() #changes the relative position
#		self.move_forward( 1 )
		self.kinematic_wander()
		self.set_abs_position(base)
		self.RightEye.update(self.abs_position)
		self.LeftEye.update(self.abs_position)

	def draw(self, surface):
		super().draw(surface)  # inherited from BWObject
		self.RightEye.draw(surface)
		self.LeftEye.draw(surface)

	def move_forward( Self, amount_to_move = DEFAULT_MOVE_AMT ):
		# assume bug's 'forward' is along the x direction in local coord frame
		tM = BugWorld.get_pos_transform( x=amount_to_move, y=0, z=0, theta=0 ) #create an incremental translation
		Self.set_rel_position ( np.matmul(Self.rel_position, tM)) #update the new position

	def turn_left( Self, theta = DEFAULT_TURN_AMT ):
		rM = BugWorld.get_pos_transform( x=0, y=0, z=0, theta=theta ) #create an incremental rotation
		Self.set_rel_position (np.matmul(Self.rel_position, rM )) #update the new position

	def turn_right(self, theta  = DEFAULT_TURN_AMT):
		#'turning right is just a negative angle passed to turn left'
		self.turn_left(-theta)

	def wander(self):
		rand_x = random.randint( 0, Bug.DEFAULT_MOVE_AMT )
		rand_theta = random.uniform( -Bug.DEFAULT_TURN_AMT, Bug.DEFAULT_TURN_AMT )
		wM = BugWorld.get_pos_transform( x=rand_x, y=0, z=0, theta=rand_theta ) #create an incremental movement
		self.set_rel_position(np.matmul(self.rel_position, wM)) #update the new relative position

	def kinematic_wander(self):

		rand_vr = random.uniform( -.5, 1 )  # random right wheel velocity normalized
		rand_vl = random.uniform( -.5, 1 )  # biased to move forward though
											# eventually will be driven by a neuron

		delta_x, delta_y, delta_theta = self.kinematic_move(rand_vr, rand_vl)
		wM = BugWorld.get_pos_transform( x=delta_x, y=delta_y, z=0, theta=delta_theta ) #create an incremental movement
		self.set_rel_position(np.matmul(self.rel_position, wM))  # update the new relative position
		
	def kinematic_move(self, vel_r, vel_l):  	# assume bugbot with two wheels on each side of it.
												# taken from GRIT robotics course
		wheel_radius = self.size * 0.5  # wheel radius is some proportion of the radius of the body
		wheel_separation = self.size * 2  # wheels are separated by the size of the bug
		delta_theta = ( wheel_radius/wheel_separation)*(vel_r - vel_l )
		temp_vect = (wheel_radius/2)*(vel_r + vel_l)
		delta_x = temp_vect * np.cos( delta_theta )
		delta_y = temp_vect * np.sin( delta_theta )
		return delta_x, delta_y, delta_theta


class Herbivore(Bug):
	def __init__ (self, starting_pos, name="HERB"):
		super().__init__( starting_pos, name )
		self.color = Color.GREEN
		self.type = BWOType.HERB


class Omnivore(Bug):
	def __init__(self, starting_pos, name="OMN"):
		super().__init__( starting_pos, name )
		self.color = Color.ORANGE
		self.type = BWOType.OMN


class Carnivore(Bug):
	def __init__(self, starting_pos, name="CARN"):
		super().__init__( starting_pos, name )
		self.color = Color.RED
		self.type = BWOType.CARN


class Obstacle(BWObject):
	def __init__ (self, starting_pos, name="OBST"):
		super().__init__( starting_pos, name )
		self.color = Color.YELLOW
		self.type = BWOType.OBST
		self.size = 7


class Meat(BWObject):
	def __init__ (self, starting_pos, name ="MEAT"):
		super().__init__(starting_pos, name )
		self.color = Color.BROWN
		self.type = BWOType.MEAT
		self.size = 10


class Plant(BWObject):
	def __init__(self, starting_pos, name="PLANT"):
		super().__init__(starting_pos, name )
		self.color = Color.DARK_GREEN
		self.type = BWOType.PLANT
		self.size = 5




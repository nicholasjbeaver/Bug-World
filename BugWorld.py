import logging
import numpy as np
import random
from itertools import count

#comment out debugging imports
#from memory_profiler import profile
#import sys
#import gc
#import objgraph
#import os
#os.environ["PATH"] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin/'


#Going to use 3D matrices even if in 2d
#See http://matthew-brett.github.io/transforms3d/ for details on the lib used
#Object's local coord frame is in the x,y plane and faces in the x direction.
#Positive rotation follow RHR, x-axis into the y-axis...so z is up.
import transforms3d.affines as AFF
import transforms3d.euler as E

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

#PGBugWorld where pygame dependent code goes
#contains draw code
#toggle display of light, smell, sound

#----------------- START PYGAME SPECIFIC CODE ---------------------------------------
import pygame

# assume 2D graphics and using Pygame to render.
class PGObject():
	color = (0, 0, 0)  # default, must be overwritten
	size = 1  # default, must be overwritten
	visible = True  # will indicate whether to draw the object or not

	def draw(self, surface, fill=0):  # fill = 0 means solid, = 1 means outline only
		x = int(self.get_abs_x())
		y = int(self.get_abs_y())
		r, g, b = self.color  # unpack the tuple

#TODO modulate color based on health
		# hp = Self.health/100 #what is the health percentage
		# r *= hp
		# g *= hp
		# b *= hp
		if self.visible:
			pygame.draw.circle(surface, (int(r), int(g), int(b)), (x, y), self.size, fill)
	
	def get_abs_x(self):  # must be overwritten
		return 0

	def get_abs_y(self):  # must be overwritten
		return 0


# world for simulations to happen
#	- has boundaries
#	- has objects
#		- determines which type
#		- determines where and when
#	- kills objects
#	- determines rules for affecting object attributes (health, mutating, mating)

# objects register for different types of collisions (physical, sound, smell, light(RGB))
# senses are modeled as a collision between sensory hitbox and stimulus
# 	(e.g., eye hit box collides with bug body visual emittter
# contains rules of interactions between objects
# how do bugs die

#objects have hitboxes for each sensor.

# Phase 1
# objects have physical collision...bodies collide with other solid bodies
# eye hitboxes collide with objects that emit visual data and extracts RGB values from the target object .color tuple

# Phase 1b
# Need an energy system
	# controls whether starves
	# consume energy based on speed
	# speed driven by amount of energy

# Phase 1c - Implement Genetic Algorithm

# Phase 2
# objects emit sound (varies on speed)
# objects emit smell
# objects have smell collision
# objects have sound collision
# eye collision also gives distance and possibly object type (so brain doesn't have to learn)


# Phase 3
# has the sample time which is the update loop time...used for velocity and acceleration
# extended collisions
# 	- different hitbox shapes.  Hitbox needed for eyes so that collisions can be detected
# 		in field of vision (use circles to start for everything.  Could use cones for vision eventually)
# 	- should return "distance" so can be used for intensity
# 	- returns an intensity of collision (for eye interaction with light, sound, smell)


# Genetic Algorithm
# have a score that indicates successfulness (distance travelled, area covered, energy amount \
# 	(expended moving, gained eating) this score will be used as the fitness function
# how do bugs reproduce (should we use the "weakest 500" to avoid extinction events)
# need global counters so can do rates to keep populations stable.
# 	Iterations/generations/epoch:can be used to create extinction events in so many cycles

# Need a timer to schedule events
	#controls rates like food introduction, mating
	#creates extinction events

# For Reinforcement Learning
# Need a point system to keep track of goal reinforcement
	# points for distance travelled (would incent to move.  otherwise would just sit still to max energy/health)
	# points for time alive
	# points for food eaten
	# could use energy and health


class BWObject(PGObject):  # Bug World Object
	"""Abstract base class.  All objects in the BugWorld must be of this type"""

	#Everything is a BWObject including bug body parts (e.g., eyes, ears, noses) and non bug inanimate objects.
	#has a position and orientation relative to the container, which could be the world.
	#has a color
	#has a size
	#has a name
	#stores an absolute position to prevent recalculating it when passing to contained objects.
	#BWO's should have a draw method that includes itself
	#BWO's should have an update method that includes itself and any subcomponents

	def __init__(self, bug_world, starting_pos, name="BWOBject"):
		self.bug_world = bug_world 		  # the world that holds this object
		self.rel_position = starting_pos  # relative the position that holds it (e.g., it is a subcomponent of a bug)
		self.abs_position = starting_pos  # absolute position in the BugWorld
		self.name = name
		self.size = 1  # default...needs to be overridden
		self.color = Color.BLACK  # default...needs to be overridden
		self.default_color = self.color
		self.type = BWOType.OBJ  # default...needs to be overridden
		self._subcomponents = []  # a list of subcomponents in the object

	def __repr__(self):
		return self.name + ": abs position={}".format(self.abs_position)  # print its name and transform

	def set_rel_position(self, pos_transform):  # position relative to its container
		self.rel_position = BugWorld.adjust_for_boundary(pos_transform)  # class method handles boundary adjustment
		return self.rel_position

	def get_rel_position(self):  # position relative to its container
		return self.rel_position

	def set_abs_position(self, base_transform):
		self.abs_position = np.matmul(base_transform, self.rel_position)
		return self.abs_position

	def get_abs_position(self):
		return self.abs_position

	def get_abs_x(self):
		return BugWorld.get_x(self.abs_position)

	def get_abs_y(self):
		return BugWorld.get_y(self.abs_position)

	def get_size(self):
		return self.size

	def update(self, base):
		# eyes don't move independent of bug, so relative pos won't change.
		self.set_abs_position(base)  # update it based on the passed in ref frame
		self.update_subcomponents(self.abs_position)

	def update_subcomponents(self, base):
		for sc in self._subcomponents:
			sc.update(base)

	def draw(self, surface, fill=0):
		super().draw(surface, fill)
		self.color = self.default_color
		self.draw_subcomponents(surface)

	def draw_subcomponents(self, surface):
		for sc in self._subcomponents:
			sc.draw(surface)

	def add_subcomponent(self, bwo):
		self._subcomponents.append(bwo)

	def reset_fitness(self):
		pass

	def kill(self):
		"""this is necessary to make sure all of subcomponents and interfaces are cleaned up"""
		self.kill_subcomponents()
		self._subcomponents.clear()
		self.bug_world = None

		try:
			self.ci.deregister_all()
		except:
			pass

	def kill_subcomponents(self):
		for sc in self._subcomponents:
			sc.kill()


import Bug
import Collisions as coll
import BugPopulation as pop
import BugBrain as bb


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
	""" Defines the different types of objects allowed within a Bug World"""

#TODO make a dictionary so can get the text for debugging and filenames.

	# use integers so it is faster for dict lookups
	# can use count from itertools to increment an index

	ndx = count(0)  # use auto indexer so can add other objects without an error.  actual value doesn't matter
	BUG = next(ndx)		# generic base class
	HERB = next(ndx)  	# Herbivore
	OMN = next(ndx)  	# Omnivore
	CARN = next(ndx)  	# Carnivore
	OBST = next(ndx)  	# Obstacle
	MEAT = next(ndx)  	# Food for Carnivore and Omnivore
	PLANT = next(ndx)  	# Food for Herbivore and Omnivore
	EYE = next(ndx)  	# for eyes
	EHB = next(ndx)	    # for eye hit boxes
	OBJ = next(ndx)  	# catch all for the base class.  Shouldn't ever show up

	_BWONames = {  	# Used to control text look up for a type so can get consistent logging and data messages
					BUG: 'BUG',
					HERB: 'HERB',
					OMN: 'OMN',
					CARN: 'CARN',
					OBST: 'OBST',
					MEAT: 'BUG',
					PLANT: 'PLANT',
					EYE: 'EYE',
					EHB: 'EHB',
					OBJ: 'OBJ'
				}

	def get_name(type_index):
		return BWOType._BWONames.get(type_index)

	
class PhysicalCollisionMatrix(coll.CollisionMatrix):
	"""This class controls what happens when objects physcialy collide"""

	def __init__(self, collisions):
		super().__init__(self.get_collision_dictionary())
		self.collisions = collisions
		self.collisions.set_collision_handler(coll.Collisions.PHYSICAL, self.invoke_handler)

# Bug to Bug interactions
	def herb_omn(self, herb, omn):  # handle herbivore an omnivore collision
		self.print_collision(herb, omn)
		logging.info('danger there is an omnivore!')
		# if the herb detects the omn, do nothing

	def omn_herb(self, omn, herb):  # handle herbivore an omnivore collision
		self.print_collision(omn, herb)
		# do damage to herbivore
		logging.info('herb says that the omn hurt him')
		herb.health -= 1

	def herb_carn(self, herb, carn):
		self.print_collision(herb, carn )
		# if the herb detects the carn, do nothing
		logging.info('danger there is a carnivore!')

	def carn_herb(self, carn, herb):  # handle herbivore an omnivore collision
		self.print_collision(carn, herb)
		# do damage to herbivore
		logging.info('herb says that the carn hurt him')
		herb.health -= 1

	def herb_herb(self, herb1, herb2):
		self.print_collision(herb1, herb2)
		#certain probability of mating?
		logging.info("should herbivores mate?")

	def omn_omn(self, omn1, omn2):
		self.print_collision(omn1, omn2)
		# certain probability of mating?
		logging.info("should omnivores mate?")

	def carn_omn(self, carn, omn):
		self.print_collision(carn, omn)
		# do damage to omn
		logging.info('carn and omn did battle')

		omn.health -= 20
		carn.health -= 5

	def omn_carn(self, omn, carn):
		self.print_collision(omn, carn)
		# do damage to omn
		omn.health -= 5
		carn.health -= 5
		logging.info('omn says did a little damage to that carnivore!')

	def carn_carn(self, carn1, carn2):
		self.print_collision(carn1, carn2)
		# certain probability of mating or fighting?
		logging.info('carn beatn up on his own kind')
		carn2.health -= 5

# Bug to food interactions

	def herb_plant(self, herb, plant):
		self.print_collision(herb, plant)

		#TODO: this is very redundant code.  should be refactored, wait until put into a population control.
		# could be collided with and take health below 0 before it is cleaned up from the world.
		if plant.health > 0:  # only process if the plant is still alive (i.e., has health)
			food_consumed = min(10, plant.health)  # only consume as much as the plant has left
			herb.energy += food_consumed
			plant.health -= food_consumed
			herb.bug_world.global_plant_food_amount -= food_consumed
			if plant.size > 1:
				plant.size -= 1  # makes sure that if the object is in BWO, it is displayed

	def omn_plant(self, omn, plant):
		self.print_collision(omn, plant)
		# could be collided with and take health below 0 before it is cleaned up from the world.
		if plant.health > 0:  # only process if the plant is still alive (i.e., has health)
			food_consumed = min(10, plant.health)  # only consume as much as the plant has left
			omn.energy += food_consumed
			plant.health -= food_consumed
			omn.bug_world.global_plant_food_amount -= food_consumed
			if plant.size > 1:
				plant.size -= 1  # makes sure that if the object is in BWO, it is displayed

	def omn_meat(self, omn, meat):
		self.print_collision(omn, meat)
		# could be collided with and take health below 0 before it is cleaned up from the world.
		if meat.health > 0:  # only process if the plant is still alive (i.e., has health)
			food_consumed = min(10, meat.health)  # only consume as much as the plant has left
			omn.energy += food_consumed
			meat.health -= food_consumed
			meat.bug_world.global_meat_food_amount -= food_consumed
			if meat.size > 1:
				meat.size -= 1  # makes sure that if the object is in BWO, it is displayed


	def carn_meat(self, carn, meat):
		if meat.health > 0:  # only process if the plant is still alive (i.e., has health)
			food_consumed = min(10, meat.health)  # only consume as much as the plant has left
			carn.energy += food_consumed
			meat.health -= food_consumed
			meat.bug_world.global_meat_food_amount -= food_consumed
			if meat.size > 1:
				meat.size -= 1  # makes sure that if the object is in BWO, it is displayed

#Bug obstacle interactions
	def herb_obst(self, herb, obst):
		self.print_collision( herb, obst )
		herb.health -= 1  # ouch obstacles hurt

	def omn_obst(self, omn, obst):
		self.print_collision(omn, obst)
		omn.health -= 1  # ouch obstacles hurt

	def carn_obst(self, carn, obst):
		self.print_collision(carn, obst)
		carn.health -= 1  # ouch obstacles hurt

	def get_collision_dictionary(self):
		cd = {  # look up which function to call when two objects of certain types collide
			(BWOType.HERB, BWOType.OMN): self.herb_omn,
			(BWOType.HERB, BWOType.CARN): self.herb_carn,
			(BWOType.HERB, BWOType.HERB): self.herb_herb,
			(BWOType.OMN, BWOType.HERB): self.omn_herb,
			(BWOType.OMN, BWOType.OMN): self.omn_omn,
			(BWOType.OMN, BWOType.CARN): self.omn_carn,
			(BWOType.CARN, BWOType.HERB): self.carn_herb,
			(BWOType.CARN, BWOType.OMN): self.carn_omn,
			(BWOType.CARN, BWOType.CARN): self.carn_carn,
			(BWOType.HERB, BWOType.PLANT): self.herb_plant,
			(BWOType.OMN, BWOType.PLANT): self.omn_plant,
			(BWOType.OMN, BWOType.MEAT): self.omn_meat,
			(BWOType.CARN, BWOType.MEAT): self.carn_meat,
			(BWOType.HERB, BWOType.OBST): self.herb_obst,
			(BWOType.OMN, BWOType.OBST): self.omn_obst,
			(BWOType.CARN, BWOType.OBST): self.carn_obst
		}
		return cd


class VisualCollisionMatrix(coll.CollisionMatrix):
	"""This class controls what happens when a bug's eye hit box collides with something that emits visual info"""

	def __init__(self, collisions):
		super().__init__(self.get_collision_dictionary())
		self.collisions = collisions
		self.collisions.set_collision_handler(coll.Collisions.VISUAL, self.invoke_handler)

# Eye to Bug interactions, i.e., when a bug sees another bug or object
	def ehb_omn(self, ehb, omn):  # handle herbivore an omnivore collision
		self.print_collision(ehb, omn)
		logging.info('I see an omnivore!')

	def ehb_herb(self, ehb, herb):  # handle herbivore an omnivore collision
		self.print_collision(ehb, herb)
		logging.info('I see an herbivore')

	def ehb_carn(self, ehb, carn):
		self.print_collision(ehb, carn )
		logging.info('I see a carnivore!')

	def ehb_plant(self, ehb, plant):
		self.print_collision(ehb, plant )
		logging.info('I see a plant!')

	def ehb_meat(self, ehb, meat):
		self.print_collision(ehb, meat )
		logging.info('I see meat!')

	def get_collision_dictionary(self):
		cd = {  # look up which function to call when two objects of certain types collide
			(BWOType.EHB, BWOType.OMN): self.ehb_omn,
			(BWOType.EHB, BWOType.CARN): self.ehb_carn,
			(BWOType.EHB, BWOType.HERB): self.ehb_herb,
			(BWOType.EHB, BWOType.PLANT): self.ehb_plant,
			(BWOType.EHB, BWOType.MEAT): self.ehb_meat
		}
		return cd

	def extract_collision_data(self, detector, emitter): # for visual collisions
		"""
			want the distance between the emitter object and the bug...not the eye_hitbox
		"""
		detector = detector.owner  # use the the bug as the detector

		dx = detector.get_abs_x() - emitter.get_abs_x()
		dy = detector.get_abs_y() - emitter.get_abs_y()
		dist_sqrd = (dx * dx) + (dy * dy)
		return {'dist_sqrd':dist_sqrd}

	def invoke_handler(self, detector, emitter):  # for visual collisions
		collision_data = self.extract_collision_data(detector, emitter)
		detector.color = emitter.color
		owner = detector.owner

		dist_sqrd = collision_data.get('dist_sqrd', 0)
		# TODO: hide this implementation detail for the eye hitbox name
		if detector.name == 'R':
			brain_data = {'right_eye': (emitter.color, dist_sqrd)}
		elif detector.name == 'L':
			brain_data = {'left_eye': (emitter.color, dist_sqrd)}
		else:  # should be an eye, if not just return
			return

		owner.bi.update_brain_inputs(brain_data)
		logging.info(owner.name + ':' + detector.name + ' saw ' + emitter.name + ' at a distance of: ' + str(round(collision_data.get("dist_sqrd"))))


class BugWorld:  # defines the world, holds the objects, defines the rules of interaction

	# World Constants used to define the size of the world and for drawing the screen
	BOUNDARY_WIDTH = 1000
	BOUNDARY_HEIGHT = 800
	BOUNDARY_WRAP = True  # controls whether bugs go off one side and enter the other (WRAP), or hit a wall

	# controls the initial number of objects in the World to start
	NUM_CARNIVORE_BUGS = 0
	NUM_OMNIVORE_BUGS = 0
	NUM_HERBIVORE_BUGS = 30
	NUM_PLANT_FOOD = 30
	NUM_MEAT_FOOD = 0
	NUM_OBSTACLES = 10

	# control reproduction in the world
	NUM_STEPS_BEFORE_REPRODUCTION = 500

	IDENTITY = np.identity(4, int)  # make a specific version in case change dimension from 3 to 2
	MAP_TO_CANVAS = [[1,0,0,0], [0,-1,0,BOUNDARY_HEIGHT], [0,0,-1,0], [0,0,0,1]]  # flip x-axis and translate origin

	# used to control what types of objects will be controlled by the population interface
	valid_population_types = {BWOType.OMN, BWOType.HERB, BWOType.CARN}  # the different types of populations allowed

	global_plant_food_amount = 0
	global_meat_food_amount = 0


	def __init__(self):

		self.rel_position = BugWorld.MAP_TO_CANVAS  # maps Bug World coords to the canvas coords in Pygame
		self.WorldObjects = []  # collection of all of the objects in the world

		# instantiate the collision system
		self.collisions = coll.Collisions()
		self.pcm = PhysicalCollisionMatrix(self.collisions)
		self.vcm = VisualCollisionMatrix(self.collisions)

		# instantiate the populations system
		self.populations = pop.BugPopulations(self, self.valid_population_types)
		self.sim_step = 0
		self.reproduction_countdown = BugWorld.NUM_STEPS_BEFORE_REPRODUCTION

		for i in range(0, BugWorld.NUM_HERBIVORE_BUGS):  # instantiate all of the Herbivores with a default name
			start_pos = BugWorld.get_random_location_in_world(self)
			self.WorldObjects.append(Herbivore(self, start_pos, "H" + str(i)))

		for i in range(0, BugWorld.NUM_CARNIVORE_BUGS):
			start_pos = BugWorld.get_random_location_in_world(self)
			self.WorldObjects.append(Carnivore(self, start_pos, "C" + str(i)))

		for i in range(0, BugWorld.NUM_OMNIVORE_BUGS):
			start_pos = BugWorld.get_random_location_in_world(self)
			self.WorldObjects.append(Omnivore(self, start_pos, "O" + str(i)))

		for i in range(0, BugWorld.NUM_OBSTACLES):
			start_pos = BugWorld.get_random_location_in_world(self)
			self.WorldObjects.append(Obstacle(self, start_pos, "B" + str(i)))

		for i in range(0, BugWorld.NUM_PLANT_FOOD ):
			start_pos = BugWorld.get_random_location_in_world(self)
			plant = Plant(self, start_pos, "P" + str(i))
			self.WorldObjects.append(plant)

		for i in range(0, BugWorld.NUM_MEAT_FOOD):
			start_pos = BugWorld.get_random_location_in_world(self)
			self.WorldObjects.append(Meat(self, start_pos, "M" + str(i)))

	def update(self):
		for BWO in self.WorldObjects:
			BWO.update(self.rel_position)

		self.collisions.detect_collisions()
		self.post_collision_processing()

		self.adjust_populations()
		self.sim_step += 1

	def draw(self, surface):
		for BWO in self.WorldObjects:
			BWO.draw(surface)

	def adjust_populations(self):
		objs_to_del = []
		objs_to_add = []
		self.reproduction_countdown -= 1

		if self.reproduction_countdown == 0:
			self.reproduction_countdown = BugWorld.NUM_STEPS_BEFORE_REPRODUCTION
			objs_to_del, objs_to_add = self.populations.reproduce()

			# now add food back in TODO: move this to a plant population controller
			health_per_plant = 100  # hard coded but it is what is in plant class
			target_food = BugWorld.NUM_PLANT_FOOD * health_per_plant
			amt_needed = target_food - self.global_plant_food_amount
			num_to_add = int(amt_needed/health_per_plant)

			# TODO: change this to objs_to_add once returned from plant population
			for i in range(0, num_to_add):
				start_pos = BugWorld.get_random_location_in_world(self)
				self.WorldObjects.append(Plant(self, start_pos, "P" + str(i)))

		# Clean out all of the old bugs
		delete_list = []
		working_list = []

		#loop through every object in the list
		for wo in self.WorldObjects:
			if wo in objs_to_del:  # if the objects health is gone, add it to the list of objects to delete
				delete_list.append(wo)
			else:  # copy the object over to the working list
				wo.reset_fitness()  # NEAT evaluations
				working_list.append(wo)

		self.WorldObjects = working_list  # copy working list back over to the WorldObjects

		# call the kill method on each object that was marked for deletion.
		# That will deregister from collisions it and clean up from the population
		for dl in delete_list:
			dl.kill()

		# if len(delete_list):
		# 	temp_dl = delete_list[0]
		# else:
		# 	temp_dl = None
		#
		# for dl in delete_list:
		# 	rc = sys.getrefcount(dl)
		# 	print("before kill:" + str(rc))
		# 	dl.kill()
		# 	rc = sys.getrefcount(dl)
		# 	print("after kill:" + str(rc))

		# if temp_dl is not None:
		# 	gc.collect()
		# 	rc = sys.getrefcount(temp_dl)
		# 	objgraph.show_backrefs(temp_dl, filename='temp_dl.png')
		# 	print("after gc:" + str(rc))

		# now add all of the new bugs
		for ao in objs_to_add:
			bug_type, genome = ao
			new_bug = self.world_object_factory(bwo_type=bug_type, genome=genome)
			self.WorldObjects.append(new_bug)

	def post_collision_processing(self):
		#loop through objects and delete them, convert them etc.

		#if health < 0, delete.
		#if was a bug, convert it to meat
		#if it was a plant, just delete it

		delete_list = []
		working_list = []

		#loop through every object in the list
		for wo in self.WorldObjects:
			if wo.health <= 0:  # if the objects health is gone, add it to the list of objects to delete
				if wo.type in {BWOType.PLANT, BWOType.MEAT}:  # let adjust_populations clean out bugs
					delete_list.append(wo)

				# if it is a bug, then add a meat object to the same location
				if wo.type in {BWOType.HERB, BWOType.OMN, BWOType.CARN}:
					start_pos = wo.get_rel_position()  # get location of the dead bug
					working_list.append(Meat(self, start_pos, "M-" + wo.name)) # create a meat object at same location
			else:  # copy the object over to the working list
				working_list.append(wo)

		self.WorldObjects = working_list  # copy working list back over to the WorldObjects

		# call the kill method on each object that was marked for deletion.
		# That will deregister from collisions it and clean up from the population
		for dl in delete_list:
			dl.kill()

	def kill_em_all(self):  # ...and let the garbage collector sort them out.  This deletes all of the objs, collisions etc
		#TODO implement this once you put it into the main loop
		pass

	def world_object_factory(self, bwo_type, starting_pos=None, name=None, genome=None):
		"""This should be used to create the main objects in the world...not subcomponents, or hitboxes"""

		if starting_pos is None:
			starting_pos = self.get_random_location_in_world()

		if name is None:
			name = BWOType.get_name(bwo_type)
			#TODO add unique counter for the bug

		if bwo_type == BWOType.HERB:
			return Herbivore(self, starting_pos, name, genome)
		elif bwo_type == BWOType.CARN:
			return Carnivore(self, starting_pos, name, genome)
		elif bwo_type == BWOType.OMN:
			return Omnivore(self, starting_pos, name, genome)
		elif bwo_type == BWOType.OBST:
			if not genome:
				logging.error("shouldn't have a genome for an obstacle")
			return Obstacle(self, starting_pos, name)
		elif bwo_type == BWOType.MEAT:
			if not genome:
				logging.error("shouldn't have a genome for an meat")
			return Meat(self, starting_pos, name)
		elif bwo_type == BWOType.PLANT:
			if not genome:
				logging.error("shouldn't have a genome for an plant ( yet :-} )")
			return Plant(self, starting_pos, name)
		else:
			logging.error("invalid Object Type: " + str(bwo_type))

	# ----- Utility Class Methods ----------------

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
		x = random.randint(0, BugWorld.BOUNDARY_WIDTH)
		y = random.randint(0, BugWorld.BOUNDARY_HEIGHT)
		z = 0
		theta = random.uniform(0, 2*np.pi)  # orientation in radians
		return BugWorld.get_pos_transform(x, y, z, theta)


# ------------- definitions of all of the objects in the world --------------------
class Herbivore(Bug.Bug):
	def __init__(self, bug_world, starting_pos, name="HERB", genome=None):
		super().__init__(bug_world, starting_pos, name, genome, bug_type=BWOType.HERB )
		self.color = Color.GREEN
		self.default_color = self.color


class Omnivore(Bug.Bug):
	def __init__(self, bug_world, starting_pos, name="OMN", genome=None):
		super().__init__(bug_world, starting_pos, name, genome, bug_type=BWOType.OMN )
		self.color = Color.ORANGE
		self.default_color = self.color


class Carnivore(Bug.Bug):
	def __init__(self, bug_world, starting_pos, name="CARN", genome=None):
		super().__init__(bug_world, starting_pos, name, genome, bug_type=BWOType.CARN)
		self.color = Color.RED
		self.default_color = self.color


class Obstacle(BWObject):
	def __init__ (self, bug_world, starting_pos, name="OBST"):
		super().__init__(bug_world, starting_pos, name )
		self.color = Color.YELLOW
		self.default_color = self.color
		self.type = BWOType.OBST
		self.size = 7
		self.health = 100
		self.ci = coll.CollisionInterface(bug_world.collisions, self)
		self.ci.register_as_emitter(self, coll.Collisions.PHYSICAL)
		self.ci.register_as_emitter(self, coll.Collisions.VISUAL)


class Meat(BWObject):
	def __init__ (self, bug_world, starting_pos, name ="MEAT"):
		super().__init__(bug_world, starting_pos, name )
		self.color = Color.BROWN
		self.default_color = self.color
		self.type = BWOType.MEAT
		self.size = 10
		self.health = 100
		self.ci = coll.CollisionInterface(bug_world.collisions, self)
		self.ci.register_as_emitter(self, coll.Collisions.PHYSICAL)
		self.ci.register_as_emitter(self, coll.Collisions.VISUAL)
		self.bug_world.global_plant_meat_amount += self.health



class Plant(BWObject):
	def __init__(self, bug_world, starting_pos, name="PLANT"):
		super().__init__(bug_world, starting_pos, name )
		# self.color = Color.DARK_GREEN
		self.color = Color.RED
		self.default_color = self.color
		self.type = BWOType.PLANT
		self.size = 5
		self.health = 100
		self.ci = coll.CollisionInterface(bug_world.collisions, self)
		self.ci.register_as_emitter(self, coll.Collisions.PHYSICAL)
		self.ci.register_as_emitter(self, coll.Collisions.VISUAL)
		self.bug_world.global_plant_food_amount += self.health



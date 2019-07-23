
import logging
import numpy as np
import random

import BugWorld as bw
import Collisions as coll
import BugPopulation as pop

logger = logging.getLogger()
logger.setLevel(logging.ERROR)


class BugEyeHitbox(bw.BWObject):
	"""This object is mounted on an eye so it can be offset and larger than the physical eye"""

	def __init__(self, bug_world, owner, pos_transform, size=15):
		self.name = "EHB"
		# position should be center of eye + radius of hitbox
		super().__init__(pos_transform, self.name)
		self.size = size
		self.color = bw.Color.GREY
		self.default_color = self.color
		self.type = bw.BWOType.EHB
		self.owner = owner
		self.ci = coll.CollisionInterface(bug_world.collisions, owner)
		self.ci.register_as_detector(self, coll.Collisions.VISUAL)

	def update(self, base):
		# eyes don't move independent of bug, so relative pos won't change.
		self.set_abs_position(base)  # update it based on the passed in ref frame

	def draw(self, surface):
		super().draw(surface, 1)  # the 1 says to draw the outline only
		self.color = self.default_color



class BugEye(bw.BWObject):

	def __init__(self, bug_world, owner, pos_transform, size=1):
		self.name = "E"
		super().__init__(pos_transform, self.name)
		self.size = size
		self.color = bw.Color.BLACK
		self.default_color = self.color
		self.type = bw.BWOType.EHB
		self.owner = owner
		self.HITBOX_SIZE = self.size * 5

		# add the eye hitbox for the current eye
		# put hitbox so tangent with eye center...actually add 1 so avoid collision with bug just for efficiency
		self.HITBOX_LOC = bw.BugWorld.get_pos_transform((self.HITBOX_SIZE + 1), 0, 0, 0)
		self.add_subcomponent(BugEyeHitbox(bug_world, owner, self.HITBOX_LOC, self.HITBOX_SIZE))

	def update(self, base):
		# eyes don't move independent of bug, so relative pos won't change.
		self.set_abs_position(base) #update it based on the passed in ref frame
		self.update_subcomponents(self.abs_position)


class Bug(bw.BWObject):
	"""Abstract base class.  All bugs in the BugWorld must be of this type
		Bug is made up of different parts:
		body, left eye, right eye,

		Phase 2
			left ear, right ear, antenna, nose, gland (to emit odor), speaker (to emit sound)
		Phase 3
			display text

		most of these are Subcomponents because they have hitboxes"""

	DEFAULT_TURN_AMT = np.deg2rad(30)  	# turns are in radians, used for random moving
	DEFAULT_MOVE_AMT = 5				# used for random moving

	def __init__(self, bug_world, initial_pos, name="Bug", genome=None, bug_type=None):
		super().__init__(initial_pos, name)
		self.size = 10  # override default and set the intial radius of bug
		self.color = bw.Color.PINK  # override default and set the initial color of a default bug
		self.default_color = self.color
		self.energy = 100  # default...needs to be overridden
		self.health = 100
		self.score = 0  # used to reinforce behaviour.  Add to the score when does a "good" thing
		self.owner = self

		if not bug_type:  # if none passed it, set it to default
			bug_type = bw.BWOType.BUG
		self.type = bug_type

		# participate in the collision system
		self.ci = coll.CollisionInterface(bug_world.collisions, self.owner)
		self.ci.register_as_emitter(self, coll.Collisions.PHYSICAL)  	# can be hit
		self.ci.register_as_detector(self, coll.Collisions.PHYSICAL) 	# can detect hitting something
		self.ci.register_as_emitter(self, coll.Collisions.VISUAL)		# can be seen

		# participate in the population system.
		self.pi = pop.BugPopulationInterface(bug_world, self, genome) # uses bug_type


		# add the eyes for a default bug
		# put eye center on circumference of bug body, rotate then translate.
		rT = bw.BugWorld.get_pos_transform(0, 0, 0, np.deg2rad(-30))
		tT = bw.BugWorld.get_pos_transform(self.size, 0, 0, 0)
		self.RIGHT_EYE_LOC = np.matmul(rT, tT)

		rT = bw.BugWorld.get_pos_transform(0, 0, 0, np.deg2rad(30))
		self.LEFT_EYE_LOC = np.matmul(rT, tT)

		self.EYE_SIZE = int(self.size * 0.50)  # set a percentage the size of the bug

		# instantiate the eyes
		self.add_subcomponent(BugEye(bug_world, self.owner, self.RIGHT_EYE_LOC, self.EYE_SIZE))
		self.add_subcomponent(BugEye(bug_world, self.owner, self.LEFT_EYE_LOC, self.EYE_SIZE))

	def calc_fitness(self):
		logging.warning("must override fitness method to calculate appropriate fitness for a given bug")
		default_fitness = self.energy + self.health + self.score
		return default_fitness

	def update(self, base):
		# TODO implement the brain interface to control motion here
		self.kinematic_wander()
		self.set_abs_position(base)

		# update subcomponents
		self.update_subcomponents(self.abs_position)

		#update the score for this iteration
		self.update_score()

		#update the energy for this iteration
		self.update_energy()

	def update_score(self):
		"""override this method to change how a bug's score is calculated"""
		self.score += 1

	def update_energy(self):
		"""override this method to change how a bug's energy is calculated"""
		self.energy -= 1

	def kill(self):  # overridden to include bug specific stuff
		super().kill()
		try:
			self.pi.deregister()  # if part of a population, deregister it
		except:
			pass


	############ Movement stuff #######################
	def move_forward(self, amount_to_move=DEFAULT_MOVE_AMT):
		# assume bug's 'forward' is along the x direction in the bug's local coord frame
		tM = bw.BugWorld.get_pos_transform(x=amount_to_move, y=0, z=0, theta=0)  # create an incremental translation
		self.set_rel_position(np.matmul(self.rel_position, tM))  # update the new position

	def turn_left(self, theta=DEFAULT_TURN_AMT):
		rM = bw.BugWorld.get_pos_transform(x=0, y=0, z=0, theta=theta)  # create an incremental rotation
		self.set_rel_position(np.matmul(self.rel_position, rM))  # update the new position

	def turn_right(self, theta=DEFAULT_TURN_AMT):
		# 'turning right is just a negative angle passed to turn left'
		self.turn_left(-theta)

	def wander(self):
		"""this method deprecated. use the kinematics of the bug instead"""
		rand_x = random.randint(0, Bug.DEFAULT_MOVE_AMT)
		rand_theta = random.uniform(-Bug.DEFAULT_TURN_AMT, Bug.DEFAULT_TURN_AMT)
		wM = bw.BugWorld.get_pos_transform(x=rand_x, y=0, z=0, theta=rand_theta)  # create an incremental movement
		self.set_rel_position(np.matmul(self.rel_position, wM))  # update the new relative position

	def kinematic_wander(self):
		rand_vr = random.uniform(-.5, 1)  # random right wheel velocity normalized
		rand_vl = random.uniform(-.5, 1)  # biased to move forward though
		# eventually will be driven by a neuron

		delta_x, delta_y, delta_theta = self.kinematic_move(rand_vr, rand_vl)
		wM = bw.BugWorld.get_pos_transform(x=delta_x, y=delta_y, z=0, theta=delta_theta)  # create an incremental movement
		self.set_rel_position(np.matmul(self.rel_position, wM))  # update the new relative position

	def kinematic_move(self, vel_r, vel_l):  # assume bugbot with two wheels on each side of it.
		# taken from GRIT robotics course
		wheel_radius = self.size * 0.5  # wheel radius is some proportion of the radius of the body
		wheel_separation = self.size * 2  # wheels are separated by the size of the bug
		delta_theta = (wheel_radius / wheel_separation) * (vel_r - vel_l)
		temp_vect = (wheel_radius / 2) * (vel_r + vel_l)
		delta_x = temp_vect * np.cos(delta_theta)
		delta_y = temp_vect * np.sin(delta_theta)
		return delta_x, delta_y, delta_theta





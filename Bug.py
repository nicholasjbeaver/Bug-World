
#need gracefully delete
#need gracefull deregister
#break out utility methods
#factor code into modules for import
#global values for visibility

import numpy as np
import random
import BugWorld as bw
import Collisions as coll

class BugEyeHitbox(bw.BWObject):
	def __init__(self, collisions, owner, pos_transform, size=15):
		self.name = "EHB"
		# position should be center of eye + radius of hitbox
		super().__init__(pos_transform, self.name)
		self.size = size
		self.color = bw.Color.GREY
		self.ci = coll.CollisionInterface(collisions, owner)
		self.ci.register_as_detector(self, coll.Collisions.VISUAL)

	def update(self, base):
		# eyes don't move independent of bug, so relative pos won't change.
		self.set_abs_position(base)  # update it based on the passed in ref frame

	def draw(self, surface):
		super().draw(surface, 1)  # the 1 says to draw the outline only


class BugEye(bw.BWObject):

	def __init__(self, collisions, owner, pos_transform, size=1):
		self.name = "E"
		super().__init__(pos_transform, self.name)
		self.size = size
		self.color = bw.Color.BLACK
		self.owner = owner
		self.HITBOX_SIZE = self.size * 5

		# add the eye hitbox for the current eye
		# put hitbox so tangent with eye center...actually add 1 so avoid collision with bug just for efficiency
		self.HITBOX_LOC = bw.BugWorld.get_pos_transform((self.HITBOX_SIZE + 1), 0, 0, 0)
		self.add_subcomponent(BugEyeHitbox(collisions, owner, self.HITBOX_LOC, self.HITBOX_SIZE))

	def update(self, base):
		# eyes don't move independent of bug, so relative pos won't change.
		self.set_abs_position(base) #update it based on the passed in ref frame
		self.update_subcomponents(self.abs_position)

	def draw(self, surface):
		super().draw(surface)
		self.draw_subcomponents(surface)

	'''Bug is made up of different parts'''
	'''body, left eye, right eye, left ear, right ear, antenna, nose, gland (to emit odor), speaker (to emit sound)
		display text'''
	'''most of these are Subcomponents because they have hitboxes'''

class Bug(bw.BWObject):
	DEFAULT_TURN_AMT = np.deg2rad(30)  # turns are in radians
	DEFAULT_MOVE_AMT = 5

	def __init__(self, collisions, initial_pos, name="Bug"):
		super().__init__(initial_pos, name)
		self.size = 10  # override default and set the intial radius of bug
		self.color = bw.Color.PINK  # override default and set the initial color of a default bug
		self.energy = 100  # default...needs to be overridden
		self.health = 100
		self.score = 0  # used to reinforce behaviour.  Add to the score when does a "good" thing
		self.owner = self
		self.ci = coll.CollisionInterface(collisions, self.owner)
		self.ci.register_as_emitter(self, coll.Collisions.PHYSICAL)
		self.ci.register_as_detector(self, coll.Collisions.PHYSICAL)
		self.ci.register_as_emitter(self, coll.Collisions.VISUAL)

		# add the eyes for a default bug
		# put eye center on circumference, rotate then translate.
		rT = bw.BugWorld.get_pos_transform(0, 0, 0, np.deg2rad(-30))
		tT = bw.BugWorld.get_pos_transform(self.size, 0, 0, 0)
		self.RIGHT_EYE_LOC = np.matmul(rT, tT)

		rT = bw.BugWorld.get_pos_transform(0, 0, 0, np.deg2rad(30))
		self.LEFT_EYE_LOC = np.matmul(rT, tT)

		self.EYE_SIZE = int(self.size * 0.50)  # set a percentage the size of the bug
		# instantiate the eyes
		self.add_subcomponent(BugEye(collisions, self.owner, self.RIGHT_EYE_LOC, self.EYE_SIZE))
		self.add_subcomponent(BugEye(collisions, self.owner, self.LEFT_EYE_LOC, self.EYE_SIZE))

	def update(self, base):
		#		self.wander() #changes the relative position
		#		self.move_forward( 1 )
		self.kinematic_wander()
		self.set_abs_position(base)

		#update subcomponents
		self.update_subcomponents(self.abs_position)

	def draw(self, surface):
		super().draw(surface)  # inherited from BWObject

		#draw subcomponents
		self.draw_subcomponents(surface)





############ Movement stuff #######################
	def move_forward(self, amount_to_move=DEFAULT_MOVE_AMT):
		# assume bug's 'forward' is along the x direction in local coord frame
		tM = bw.BugWorld.get_pos_transform(x=amount_to_move, y=0, z=0, theta=0)  # create an incremental translation
		self.set_rel_position(np.matmul(self.rel_position, tM))  # update the new position

	def turn_left(self, theta=DEFAULT_TURN_AMT):
		rM = bw.BugWorld.get_pos_transform(x=0, y=0, z=0, theta=theta)  # create an incremental rotation
		self.set_rel_position(np.matmul(self.rel_position, rM))  # update the new position

	def turn_right(self, theta=DEFAULT_TURN_AMT):
		# 'turning right is just a negative angle passed to turn left'
		self.turn_left(-theta)

	def wander(self):
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





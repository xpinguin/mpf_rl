"""
	- Generates three types of figures: circle, triangle, rectangle
	
	- Transforms figures through: translation, rotation and scaling
	
	- Generation of training and test datasets, noise (transformation)
		separately adjusted for each
		
	- The result is 4-D numpy array with following shape:
		(number_of_samples, number_of_frames, m, n),
		where:
			* 'number_of_samples' - number of samples in dataset
			* 'number_of_frames' - number of frames in each animation
			* 'm' - view field width
			* 'n' - view field height
"""

from numpy import *

import pylab as plt
from time import sleep
import sys

VIEW_FIELD_SHAPE = (32, 32)

# figures' classes names
FIG_RECTANGLE = 1
FIG_TRIANGLE = 2
FIG_CIRCLE = 3
# ---

def _draw_line(pos1, pos2):
	pos1 = asarray(pos1)
	pos2 = asarray(pos2)
	
	length = linalg.norm(pos2 - pos1)

	delta = array([(pos2[0] - pos1[0]) / length, (pos2[1] - pos1[1]) / length])
	
	res_points = zeros((2, ceil(length)))
	
	for i in xrange(res_points.shape[1]):
		res_points[:, i] = pos1
		pos1 = pos1 + delta
		
	return res_points
	
def _plot_points(points, local_transform, pos = (0, 0)):
	field = ones(VIEW_FIELD_SHAPE)
	
	points = dot(local_transform, points)
	points = points + array([[pos[0]], [pos[1]]])
	
	for i in xrange(points.shape[1]):
		int_x = round(points[0, i])
		int_y = round(points[1, i])
		
		if ((int_x >= 0) and (int_x < field.shape[0]) and \
			(int_y >= 0) and (int_y < field.shape[1])):
			field[int_y, int_x] = 0.0
			
	return field

def rectangle():
	p = _draw_line((-VIEW_FIELD_SHAPE[0] / 2.0 + 1, -VIEW_FIELD_SHAPE[1] / 2.0 + 1), \
					(-VIEW_FIELD_SHAPE[0] / 2.0 + 1, VIEW_FIELD_SHAPE[1] / 2.0))
	
	p = concatenate((p, \
			_draw_line((-VIEW_FIELD_SHAPE[0] / 2.0 + 1, -VIEW_FIELD_SHAPE[1] / 2.0 + 1), \
					(VIEW_FIELD_SHAPE[0] / 2.0, -VIEW_FIELD_SHAPE[1] / 2.0 + 1))), 1)
	
	p = concatenate((p, \
			_draw_line((-VIEW_FIELD_SHAPE[0] / 2.0 + 1, VIEW_FIELD_SHAPE[1] / 2.0), \
					(VIEW_FIELD_SHAPE[0] / 2.0,  VIEW_FIELD_SHAPE[1] / 2.0))), 1)
					
	p = concatenate((p, \
			_draw_line((VIEW_FIELD_SHAPE[0] / 2.0, -VIEW_FIELD_SHAPE[1] / 2.0 + 1), \
					(VIEW_FIELD_SHAPE[0] / 2.0, VIEW_FIELD_SHAPE[1] / 2.0 + 1))), 1)		
	
	
	return p


def triangle():
	p = _draw_line((VIEW_FIELD_SHAPE[0] / 2.0, 0), (0, VIEW_FIELD_SHAPE[1]))
	
	
	p = concatenate((p, \
			_draw_line((VIEW_FIELD_SHAPE[0] / 2.0, 0), \
						(VIEW_FIELD_SHAPE[0], VIEW_FIELD_SHAPE[1]))), 1)
	
	
	p = concatenate((p, \
			_draw_line((0, VIEW_FIELD_SHAPE[1]-1), \
						(VIEW_FIELD_SHAPE[0], VIEW_FIELD_SHAPE[1]-1))), 1)
	
	# move the center of mass to (0, 0)
	p = p + array([[-VIEW_FIELD_SHAPE[0] / 2.0], [-VIEW_FIELD_SHAPE[1] * 2.0 / 3.0]])
	
	return p


def circle():
	center = [0, 0]
	radius = min(VIEW_FIELD_SHAPE) / 2.0 - 1.0
	
	t = linspace(0, 2*pi, ceil(4*pi*radius))
	p = empty((2, t.shape[0]))
	
	p[0, :] = radius * cos(t) + center[0]
	p[1, :] = radius * sin(t) + center[1]

	return p


def scale(factor):
	return eye(2, 2) * factor
	
def rotate(angle):
	return array([[sin(angle), -cos(angle)], [cos(angle), sin(angle)]])
	
# different animations for figures
def anim_move(fig_points, pos1, pos2, pre_transform = None):
	pos1 = asarray(pos1)
	pos2 = asarray(pos2)
	
	length = linalg.norm(pos2 - pos1)
	delta = array([(pos2[0] - pos1[0]) / length, (pos2[1] - pos1[1]) / length])
	
	anim_fields = zeros((ceil(length), VIEW_FIELD_SHAPE[0], VIEW_FIELD_SHAPE[1]))
	
	if (pre_transform == None): pre_transform = eye(2, 2)
	
	for i in xrange(anim_fields.shape[0]):
		anim_fields[i, :, :] = _plot_points(fig_points, pre_transform, pos1)
		pos1 = pos1 + delta
		
	return anim_fields
	
def anim_scale(fig_points, scale_range, frames_num = None, pre_transform = None, pos = (0, 0)):
	scale_step = 0.1
	scale_factor = min(scale_range)
	
	if (frames_num == None):
		frames_num = ceil((max(scale_range) - min(scale_range)) / scale_step)
	
	anim_fields = zeros((frames_num, \
						VIEW_FIELD_SHAPE[0], VIEW_FIELD_SHAPE[1]))
	
	if (pre_transform == None): pre_transform = eye(2, 2)
	
	for i in xrange(anim_fields.shape[0]):
		transform = dot(pre_transform, scale(scale_factor))
		
		scale_factor = scale_factor + scale_step
		if (scale_factor > max(scale_range)) or (scale_factor < min(scale_range)):
			scale_step = -scale_step
	
		anim_fields[i, :, :] = _plot_points(fig_points, transform, pos)
		
	return anim_fields

def anim_rotate(fig_points, angle_step, frames_num, pre_transform = None, pos = (0, 0)):
	anim_fields = zeros((frames_num, VIEW_FIELD_SHAPE[0], VIEW_FIELD_SHAPE[1]))
	
	if (pre_transform == None): transform = eye(2, 2)
	else: transform = pre_transform
	
	for i in xrange(anim_fields.shape[0]):
		pre_transform = dot(rotate(angle_step), pre_transform)
		anim_fields[i, :, :] = _plot_points(fig_points, pre_transform, pos)
		
	return anim_fields
	
def anim_move_scale(fig_points, pos1, pos2, scale_range):
	pass
	
def anim_move_rotate(fig_points, pos1, pos2, angle_step):
	pass
	
def anim_scale_rotate(fig_points, scale_range, angle_step):
	pass
	
def anim_move_scale_rotate(fig_points, pos1, pos2, scale_range, angle_step):
	pass
	
	
# =======================================================================

# TEST CODE
# =======================================================================

fig_points = [[rectangle(), FIG_RECTANGLE], [triangle(), FIG_TRIANGLE]]

#fig_anim = anim_move(fig_points, (-16, -16), (32, 60), eye(2) * 0.4)
#fig_anim = anim_scale(fig_points, (0.4, 0.9), None, None, (15, 15))
#fig_anim = anim_rotate(fig_points, pi / 20.0, 100, scale(0.5), (15, 15))

figs_anims = zeros((len(fig_points),), dtype = ("object,u1"))

for i in xrange(len(fig_points)):
	figs_anims[i] = (
			anim_move(fig_points[i][0], (-16 + i, 15), (48, 30), scale(0.4)),
			fig_points[i][1]
	)
	
#figs_anims = asarray(figs_anims)

print figs_anims.dtype
print figs_anims[0][0].dtype
#print figs_anims[1]

save("two_figs.npy", figs_anims)



"""
plt.ion()

plt.set_cmap('gray')

line = plt.imshow(fig_anim[0], interpolation = 'none', vmin = 0, vmax = 1)
plt.draw()


for i in xrange(1, fig_anim.shape[0]):
	line.set_data(fig_anim[i])
	plt.draw()
	
	sleep(0.2)
	
plt.ioff()
"""	


# ====================================================
# OLD TEST CODE
# ====================================================

"""	
	
scale_mat = eye(2, 2) * 0.4
#rot_mat = rotate(pi * 30 / 180)
#rot_mat = eye(2, 2)

### Position of drawed figures - should be their centre!!!!


transform_mat = scale_mat
#transform_mat = eye(2, 2)


fig_points = circle()
#fig_points = _draw_line((1, 1), (16, 31))
#fig_points = triangle()
#fig_points = rectangle()

fig = _plot_points(fig_points, transform_mat, (15, 15))

plt.ion()
line = plt.imshow(fig, cmap =  plt.cm.get_cmap(name = 'gray'), interpolation = 'none')
#plt.show()

#sys.exit(0)

scale_factor = 0.4
sf_step = 0.05

rot_mat = eye(2, 2)

while (True):
	sleep(0.2)
	
	
	rot_mat = dot(rot_mat, rotate(0.05 * pi))
	scale_mat = scale(scale_factor)
	
	scale_factor = scale_factor + sf_step
	if (scale_factor > 0.8) or (scale_factor < 0.4): sf_step = -sf_step
	
	transform_mat = dot(rot_mat, scale_mat)
	
	fig = _plot_points(fig_points, transform_mat, (15, 15))
	
	line.set_data(fig)
	plt.draw()
	
	
plt.ioff()
	
#plt.show()
"""
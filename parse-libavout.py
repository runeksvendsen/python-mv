#!/usr/bin/env python

from PIL import Image, ImageDraw
from itertools import combinations
import random, numpy, math

random.seed(open('/dev/urandom').read(32))

def points_sum(*points):
	zp = zip(*points)
	newpoint = (sum(zp[0]), sum(zp[1]))
	return newpoint

def points_avg(*points):
	point_list_sz = len(points)
	huge_point = points_sum(*points)
	return (huge_point[0]/point_list_sz, huge_point[1]/point_list_sz)

def find_coeffs(pa, pb):
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])

    A = numpy.matrix(matrix, dtype=numpy.float)
    B = numpy.array(pb).reshape(8)

    res = numpy.dot(numpy.linalg.inv(A.T * A) * A.T, B)
    return numpy.array(res).reshape(8)

class Frame(object):
	def __init__(self, width, height, num):
		self.width = int(width)
		self.height = int(height)
		self.num = int(num)
		self.mbs = []
		self.mbs_groups = None

	def add_macroblock(self, mb):
		self.mbs.append(mb)
		self.mbs_groups = None

	def _distance(self, point1, point2):
		(x1,y1) = (point1[0], point1[1])
		(x2,y2) = (point2[0], point2[1])
		return math.sqrt((x2-x1)**2 + (y2-y1)**2)

	def find_near_mbs_new(self, per_group_min=5, per_group_max=7):
		#dists = [(sum([ self._distance(m,n) for m,n in combinations([a,b,c,d], 2) ]), [a,b,c,d]) for a,b,c,d in combinations(self.mbs, 4)]
		#pass
		for i,a in enumerate(self.mbs):
			dists = [(sum([ self._distance(m,n) for m,n in combinations([a,b,c,d], 2) ]), [a,b,c,d]) for b in self.mbs[)]

	def find_near_mbs(self, per_group_min=5, per_group_max=7):
		if self.mbs_groups == None:
			MAX_DIST_FACTOR = 0.10
			MAX_DIST = (self.width+self.height)/2 * MAX_DIST_FACTOR #pixels

			mbs_groups = []

			#for a, b in combinations(mbs, 2):
			for a in self.mbs:
				mbs_list = [a]
				for b in self.mbs:
					#mva = a.mvs[0]
					#mvb = b.mvs[0]

					#(x1,y1) = (mva.mx, mva.my)
					#(x2,y2) = (mvb.mx, mvb.my)
					#distance = self._distance((x1,y1), (x2,y2))
					distance = self._distance(a.get_mean_pos(), b.get_mean_pos())

					if distance <= MAX_DIST:
						#print a.get_mean_pos(), b.get_mean_pos()
						#print distance, "<=", MAX_DIST
						mbs_list.append(b)
						if len(mbs_list) > per_group_max:
							continue							

				if len(mbs_list) >= per_group_min and len(mbs_list) <= per_group_max:
					mbs_groups.append(MacroblockGroup(mbs_list))
					if mbs_groups[-1].avg_center()[0] >= 60 and mbs_groups[-1].avg_center()[0] <= 180 and mbs_groups[-1].avg_center()[1] >= 90 and mbs_groups[-1].avg_center()[1] <= 170:
						pass

			self.mbs_groups = mbs_groups
			return self.mbs_groups

	#@profile
	def get_four_mbgs(self, per_group_min=3, per_group_max=20):
		self.find_near_mbs(per_group_min)

		max_distance = 0
		best_mb_group = None

		for a,b,c,d in combinations(self.mbs_groups, 4):
			#print "handling group of 4"
			#distance = sum([self._distance(a.avg_center(), o.avg_center()) for o in (b,c,d)])
			distance = sum([ self._distance(a.avg_center(), b.avg_center()) for a,b in combinations([a,b,c,d], 2) ])

			if distance > max_distance:
				best_mb_group = [a,b,c,d]
				max_distance = distance
				print distance, best_mb_group

		return best_mb_group
			

	def __repr__(self):
		return "<Frame 'width: {}, height: {}'>".format(self.width, self.height)

class Macroblock(object):
	def __init__(self, x, y):
		self.x = int(x)
		self.y = int(y)
		self.vb = None
		self.mvs = []

	def get_mean_pos(self):
		return points_avg(*[mv.get_base_point() for mv in self.mvs])

	def add_mv(self, mv):
		self.mvs.append(mv)

	def __repr__(self):
		#return "<Macroblock 'x: {}, y: {}, pos: {}, mvs: {}'>".format(self.x, self.y, self.get_mean_pos(), [str(mv) for mv in self.mvs ])
		return "<Macroblock 'x: {}, y: {}, pos: {}>".format(self.x, self.y, self.get_mean_pos())

class Vectorblock(object):
	def __init__(self, size, type):
		self.size = int(size)
		self.type = str(type)
		self.mvs = []

	def add_mv(self, mv):
		self.mvs.append(mv)

	def __repr__(self):
		return "<Vectorblock 'size: {}, type: {}, mvs:\n\t{}'>".format(self.size, self.type, "\n\t\t".join([str(mv) for mv in self.mvs ]))

class Motionvector(object):
	def __init__(self, sx, sy, mx, my, type):
		self.type = type

		if self.type == "8x8" or "16x16":
			self.sx = int(sx) #base point
			self.sy = int(sy) #base point
			self.mx = int(mx)
			self.my = int(my)
		else:
			self.sx = int(sx)
			self.sy = int(sy)
			self.mx = int(mx+sx)
			self.my = int(my+sy)
		
		self.dx = self.sx-self.mx
		self.dy = self.sy-self.my

		self.x = self.dx
		self.y = self.dy

	def get_base_point(self):
		return (self.sx, self.sy)

	def __repr__(self):
		return "<Motionvector 'dx: {}, dy: {}, sx: {}, sy: {}'>".format(self.dx, self.dy, self.sx, self.sy)

class MacroblockGroup(object):
	def __init__(self, mbs=[]):
		self.mbs = mbs
		self.size = len(self.mbs)
		self.avg_c = None

	def avg_center(self):
		if self.avg_c == None:
			point_list = [ mb.get_mean_pos() for mb in self.mbs ]
			#print point_list
			#point_list_sz = len(point_list)
			#huge_point = points_sum( *point_list )
			#self.avg_c = (huge_point[0]/point_list_sz, huge_point[1]/point_list_sz)
			self.avg_c = points_avg(*point_list)
		return self.avg_c

	def add_mb(self, mb):
		self.mbs.append(mb)
		self.size = len(self.mbs)
		self.avg_c = None

	def __repr__(self):
		return "<MacroblockGroup 'size: {}, center: {}'>".format(self.size, self.avg_center())

class Deserialize(object):
	def __init__(self, ser):
		fields = ser.split(";")
		self.type = fields[0]

		if fields[-1] == '':
			fields.pop()

		self.kws = { a.split('=')[0] : a.split('=')[1] for a in fields[1:] }

frames = []

with open("example-parse.txt", 'r') as f:
	data = f.read()

vb_type = None
for line in data.split('\n'):
	des = Deserialize(line)

	if des.type == 'NEWFRAME':
		frames.append(Frame(**des.kws))
		continue

	if des.type == 'MACROBLOCK':
		frames[-1].add_macroblock(Macroblock(**des.kws))

	if des.type == 'VECTOR':
		des.kws['type'] = vb_type
		frames[-1].mbs[-1].add_mv(Motionvector(**des.kws))

	if des.type == 'VECTORBLOCK':
		#frames[-1].mbs[-1].vb = Vectorblock(**des.kws)
		vb_type = des.type

count = 0
total_x = 0
total_y = 0
frame = frames[0]

#TEST
mbs_groups = frame.find_near_mbs_new()

mbs_groups = frame.find_near_mbs()
#print mbs_groups
print len(mbs_groups)
four_mbgs = frame.get_four_mbgs()



#IMG="/home/rune/Programming/scripts/hdr-mocomp/frame_0002.jpg"
IMG="/home/rune/Programming/scripts/hdr-mocomp/shot0001.png"
IMGSAVED="/home/rune/Programming/scripts/hdr-mocomp/nframe_0002.jpg"
img = Image.open(IMG)

draw = ImageDraw.Draw(img)

for mbg in four_mbgs:
	for mb in mbg.mbs:
		for mv in mb.mvs:
			RADIUS=3
			coord =  (mv.sx-RADIUS, mv.sy-RADIUS, mv.sx+RADIUS, mv.sy+RADIUS)
			draw.ellipse(coord, fill=(255,0,0,128))
			

img.show()

test="""

width, height = img.size
size = (width, height)
m = -0.5
xshift = abs(m) * width
new_width = width + int(round(xshift))



coeffs = find_coeffs(
        [(0, 0), (256, 0), (256, 256), (0, 256)],
        [(0, 0), (256, 0), (new_width, height), (xshift, height)])

#find four random motion vectors
pa = []
random_vcs = []

for i in range(0,4):
	random_mb_index = random.randint(0, len(frame.mbs)-1)
	random_mb = frame.mbs.pop(random_mb_index)

	random_vc_index = random.randint(0, random_mb.size-1)
	random_vc = random_mb.mvs.pop(random_vc_index)

	random_vcs.append(random_vc)

pa = [ (v.sx, v.sy) for v in random_vcs ]
pb = [ (v.mx, v.my) for v in random_vcs ]



coeffs = find_coeffs(
         [(0, 0), (width, 0), (width, height), (0, height)],
         [(0, 0), (width, 0), (width, height), (0, height)])

coeffs = find_coeffs(
			[(2888, 1608), (2500, 2316), (1468, 1992), (2404, 2428)],
			[(2866, 1612), (2473, 2316), (1447, 1989), (2386, 2425)])

coeffs = find_coeffs(
			[(0, 0), (2500, 2316), (1468, 1992), (2404, 2428)],
			[(0, 0), (2473, 2316), (1447, 1989), (2386, 2425)])

print "Transform from {} to {}".format(pa, pb)

#coeffs = find_coeffs(pa, pb)

newimg = img.transform((width, height), Image.PERSPECTIVE, coeffs, Image.BICUBIC)

newimg.save(IMGSAVED)
newimg.show()
img.show()
"""

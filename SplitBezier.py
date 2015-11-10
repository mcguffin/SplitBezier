import math
import os
from AppKit import NSImage
from lib.UI.toolbarGlyphTools import ToolbarGlyphTools
from mojo.events import addObserver, removeObserver
from mojo.extensions import ExtensionBundle
from mojo.UI import CurrentGlyphWindow
from fontTools.pens.basePen import AbstractPen, BasePen
from robofab.pens.adapterPens import PointToSegmentPen, SegmentToPointPen
from robofab.pens.filterPen import _estimateCubicCurveLength
from robofab.misc.bezierTools import splitQuadraticAtT,splitCubicAtT
from robofab.world import CurrentFont


extensionDomain = 'net.flyingletters.splitBezier'

bezierBundle = ExtensionBundle("SplitBezier")

def unique(seq):
	'''Returns list with duplicates removed
		
		>>> unique( ['spam','spam','spam','spam','bacon','eggs','ham'] )
		['spam','bacon','eggs','ham']
	'''
	seen = set()
	seen_add = seen.add
	return [ x for x in seq if not (x in seen or seen_add(x))]

def splitLineAtT(pt1,pt2,*ts):
	'''Split the line between pt1 and pt2 at one or more
	values of t. Return a list of curve segments.
	
		>>> splitLineAtT((50,50),(200,20),0.5)
		[((50, 50), (125.0, 35.0)), ((125.0, 35.0), (200.0, 20.0))]
		>>> splitLineAtT((50,50),(200,20),0.33333333333,0.66666666666)
		[((50, 50), (99.9999999995, 40.0000000001)), ((99.9999999995, 40.0000000001), 
		(149.999999999, 30.0000000002)), ((149.999999999, 30.0000000002), (200.0, 20.0))]
	'''

	ts = list(ts)
	ts.append(1.0)
	segments = []

	prevPt = pt1x, pt1y = pt1
	pt2x, pt2y = pt2
	ax = (pt2x - pt1x)
	ay = (pt2y - pt1y)

	for i in range(len(ts)):
		pt = pt1x + ax * ts[i], pt1y + ay * ts[i]
		segments.append((prevPt,pt))
		prevPt = pt

	return segments


class BisectBezierPen(BasePen):

	"""Pen that bisects
	"""
	
	def __init__(self, otherPen, selected = [], *splits ):
		BasePen.__init__(self, {})
		self.otherPen = otherPen
		self.currentPt = None
		self.firstPt = None
		self.selected = selected
		self.splits = splits

	def _moveTo(self, pt):
		self.otherPen.moveTo(pt)
		self.currentPt = pt
		self.firstPt = pt

	def _lineTo(self, pt):
		if self.currentPt in self.selected and pt in self.selected:
			splitLns = splitLineAtT(self.currentPt,pt,*self.splits)
			for p0,p1 in splitLns:
				self.otherPen.lineTo(p1)
		else:
			self.otherPen.lineTo(pt)
		self.currentPt = pt

	def _curveToOne(self, *pts):
		if self.currentPt in self.selected and pts[-1] in self.selected:
			if len(pts) == 2 :
				splitBez = splitQuadraticAtT(self.currentPt,pts[0],pts[1],*self.splits)
				for p0,p1,p2 in splitBez:
					self.otherPen.qCurveTo(p1,p2)
			elif len(pts) == 3:
				splitBez = splitCubicAtT(self.currentPt,pts[0],pts[1],pts[2],*self.splits)
				for p0,p1,p2,p3 in splitBez:
					self.otherPen.curveTo(p1,p2,p3)
		else:
			self.otherPen.curveTo(*pts)
		self.currentPt = pts[-1]
		
	def _closePath(self):
		self.lineTo(self.firstPt)
		self.otherPen.closePath()
		self.currentPt = None
	
	def _endPath(self):
		self.otherPen.endPath()
		self.currentPt = None
		
	def addComponent(self, glyphName, transformation):
		self.otherPen.addComponent(glyphName, transformation)

class BisectBezierTool(object):

	base_path = os.path.dirname(__file__)
	toolbarItems = None
	menuItem = None

	def __init__(self):
		addObserver(self, "addBisectBezierToolbarItem", "glyphWindowWillShowToolbarItems")

	def addBisectBezierToolbarItem(self, info):
		toolbarItems = info['toolbarItems']

		filename = 'SplitBezier.pdf'
		index=1
		
		imagePath = os.path.join(self.base_path, 'resources', filename)
		image = NSImage.alloc().initByReferencingFile_(imagePath)

		label = 'Bisect Curve'
		self.menuItem = dict(
			itemIdentifier='bisectBezier',
			label = label,
			callback = self.bisectBezier,
			view = ToolbarGlyphTools((30, 25), 
				[dict(image=image, toolTip=label)], trackingMode="one")
		)
		toolbarItems.insert(index, self.menuItem)

	def bisectBezier(self, sender):
		## return the toolbar tool tip
		g = CurrentGlyph()
		if len(g.contours) == 0:
			return

		points = []
		segments = []

		current_segment = None
		for p in g.selection:
			points.append((p.x, p.y))
		new = RGlyph()
		writerPen = new.getPen()
		filterpen = BisectBezierPen(writerPen, points,0.5)
		wrappedPen = PointToSegmentPen(filterpen)

		g.prepareUndo("Bisect Segment")
		
		g.drawPoints(wrappedPen)
		g.clear()
		g.appendGlyph(new)
		
		g.performUndo()
		g.update()
		
		

BisectBezierTool()

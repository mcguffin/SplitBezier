import re, mojo, vanilla, fontTools, robofab

from vanilla import *


class ObjectBrowserController():

	def __init__(self, inspectObject):

		if inspectObject is None:
			raise TypeError, "can not inspect None value"

		self.w = vanilla.Window((700, 500),
								"inspect %s" %inspectObject,
								minSize=(100, 100))
		self.w.b = vanilla.ObjectBrowser((0, 0, -0, -0),
								inspectObject)
		self.w.open()


class ObjectBrowserPalette:

	def __init__(self):
		self.p = FloatingWindow((390, 140),
								"Inspect Objects")
		self.p.vn = Button((20,20,100,30),
								'vanilla',
								callback = self.libBrowser)
		self.p.mj = Button((140,20,100,30),
								'mojo',
								callback = self.libBrowser)
		self.p.rf = Button((260,20,100,30),
								'robofab',
								callback = self.libBrowser)
								
		self.p.tx = EditText((20,60,350,20),text='mojo.UI')

		self.p.eb = Button((140,90,100,30),
								'eval & inspect',
								callback = self.evalInspectBrowser)
		self.p.ib = Button((260,90,100,30),
								'import & inspect',
								callback = self.importInspectBrowser)
		self.p.open()
	
	def importInspectBrowser(self,sender):
		name = self.p.tx.get()
		obj = __import__(name)
		ObjectBrowserController(obj)
	
	def evalInspectBrowser(self,sender):
		name = self.p.tx.get()
		obj = eval(name)
		ObjectBrowserController(obj)
	
	def libBrowser(self,sender):
		name = sender.getTitle()
		obj = __import__(name)
		ObjectBrowserController(obj)
	
	
	

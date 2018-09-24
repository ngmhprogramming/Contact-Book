#Stack wrapper to simplify actual flask code
#Used for both Undo and Redo stack
#Logic for undo and redo
#Case 1:
#Insertion / Deletion
#Change is pushed to undo stack
#Redo stack is reset
#_______.______> Original path
#Assume we have undone until this point
#_______.(______>) this part is on the redo stack
#The path will change when we make a change
#_______.(______>) this part will cause conflict with the other path
#       \____>
#Even if we undo back
#_______.(______>) we now have
#       \(____>) 2 path choices
#Case 2:
#Undo
#Most recent change is undone, and pushed to redo stack
#Case 3:
#Redo
#Most recent change is redone, and pushed to undo stack

from stack import Stack
from os import path
from csv import writer, DictReader

class Changes():
	def __init__(self, user, name, ext):
		self.user = user
		self.name = name
		self.ext = ext
		self.file = user+"_"+name
		self.fields = ["Type", "First Name", "Last Name", "Phone Number", "Birthday", "Email", "Importance"]
		self.stack = Stack()
	#Push a change to a stack
	def insert(self, type, row):
		row["Type"] = type
		self.stack.push(row)
	#Check if a stack has changes
	def empty(self):
		return self.stack.empty()
	#Get most recent change
	def top(self):
		return self.stack.top()
	#Remove most recent change
	def pop(self):
		self.stack.pop()
	#Read changes from save file
	def load(self, name=None):
		if name is None: name = self.file
		if not path.isfile("saves/"+name+"."+self.ext): return
		rows = []
		with open("saves/"+name+"."+self.ext, "r") as file:
			r = DictReader(file)
			for i in r:
				a = dict(i)
				a["Birthday"] = int(a["Birthday"])
				a["Importance"] = int(a["Importance"])
				self.stack.push(a)
	#Remove all changes
	def reset(self):
		with open("saves/"+self.file+"."+self.ext, "w+") as file:
			fwriter = writer(file, delimiter=',', quotechar='"')
			fwriter.writerow(self.fields)
	#Write changes to save file
	def save(self):
		a = []
		while not self.stack.empty():
			a.append(self.stack.top())
			self.stack.pop()
		a.reverse()
		with open("saves/"+self.file+"."+self.ext, "w+") as file:
			fwriter = writer(file, delimiter=',', quotechar='"')
			fwriter.writerow(self.fields)
			for i in a:
				row = []
				for j in self.fields: row.append(i[j])
				fwriter.writerow(row)
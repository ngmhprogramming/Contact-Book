#AVLTree wrapper to simplify actual flask code

from AVLTree import AVLTreeNode, AVLTree 
from os import path
from csv import writer, DictReader
from datetime import datetime
from time import strftime, gmtime

class Book:
    def __init__(self, user, name):
        self.user = user
        self.name = name
        self.file = user+"_"+name
        self.fields = ["First Name", "Last Name", "Phone Number", "Birthday", "Email", "Importance"]
        self.trees = []
        self.tree = AVLTree()
        for i in range(len(self.fields)): self.trees.append(None)
    #Check if phone number is a duplicate
    def used(self, pnumber):
        r = self.tree.search(self.trees[2], pnumber)
        return r is not None
    #Insert a contact
    def insert(self, row):
        for i in range(len(self.fields)):
            without = {}
            for k in row.keys():
                if k != self.fields[i]: without[k] = row[k]
            self.trees[i] = self.tree.insert(self.trees[i], row[self.fields[i]], without)
    #Get row associated with phone number
    def pnumber(self, pnumber):
        r = self.tree.search(self.trees[2], pnumber)
        if r is None: return None
        row = r.values[0]
        row["Phone Number"] = r.key
        return row
    #Delete contact from book
    def delete(self, pnumber):
        r = self.tree.search(self.trees[2], pnumber)
        if r is None: return False
        row = r.values[0]
        row["Phone Number"] = r.key
        for i in range(len(self.fields)):
            without = {}
            for k in row.keys():
                if k != self.fields[i]: without[k] = row[k]
            self.trees[i] = self.tree.delete(self.trees[i], row[self.fields[i]], without)
        return True
    #Get all contacts
    #Option to sort by field
    def all(self, field=None):
        if field is None: field = "Phone Number"
        r = self.tree.all(self.trees[self.fields.index(field)])
        a = []
        for i in r:
            for j in i.values:
                d = {}
                for k in j.keys():
                    d[k] = str(j[k])
                d[field] = i.key
                d["Birthday"] = strftime("%Y-%m-%d", gmtime(int(d["Birthday"])))
                a.append(d)
        return a
    #Read in contacts
    def load(self, name=None):
        if name is None: name = self.file
        if not path.isfile("saves/"+name+".cb"): return
        for i in range(len(self.trees)): self.trees[i] = None
        rows = []
        with open("saves/"+name+".cb", "r") as file:
            r = DictReader(file)
            for i in r:
                a = dict(i)
                a["Birthday"] = int(a["Birthday"])
                a["Importance"] = int(a["Importance"])
                self.insert(a)
    #Save contacts
    def save(self):
        r = self.tree.all(self.trees[0])
        a = []
        for i in r:
            for j in i.values:
                d = {}
                for k in j.keys():
                    d[k] = str(j[k])
                d[self.fields[0]] = i.key
                a.append(d)
        with open("saves/"+self.file+".cb", "w+") as file:
            fwriter = writer(file, delimiter=',', quotechar='"')
            fwriter.writerow(self.fields)
            for i in a:
                row = []
                for j in self.fields: row.append(i[j])
                fwriter.writerow(row)
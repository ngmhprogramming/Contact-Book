from flask import Flask, session, request, url_for, redirect, render_template, send_file
from werkzeug.utils import secure_filename
import sqlite3
import hashlib
import time
import datetime
from csv import writer, DictReader
from book import Book
from changes import Changes
from connectivity import Connectivity

app = Flask(__name__)
app.secret_key = "secretysecret"

#Configure upload details
#Folder which files are saved (technically unecessary)
UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = set(['csv', 'cb'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Read cookies to get username
def get_username():
    if "username" in session: return session["username"]
    return None

#Get average of all fields
def get_average(r):
    if len(r) == 0: return {"First Name": "", "Last Name": "", "Phone Number": "", "Birthday": "", "Email": "", "Importance": ""}
    av = {}

    #Calculate for First Name
    #Aligns words on right
    #one and three is aligned as
    #  one
    #three
    #Get average of ASCII values for each position
    t = []
    c = []
    for i in r:
        s = i["First Name"][::-1]
        for j in range(len(s)):
            ascii = ord(s[j])
            if len(t) <= j:
                t.append(ascii)
                c.append(1)
        else:
                t[j] += ascii
                c[j] += 1
    av["First Name"] = ""
    for j in range(len(t)):
        av["First Name"] += chr(int(t[j]/c[j]))
    av["First Name"] = av["First Name"][::-1]

    #Calculate for Last Name
    #Similar to First Name
    t = []
    c = []
    for i in r:
        s = i["Last Name"][::-1]
        for j in range(len(s)):
            ascii = ord(s[j])
            if len(t) <= j:
                t.append(ascii)
                c.append(1)
            else:
                t[j] += ascii
                c[j] += 1
    av["Last Name"] = ""
    for j in range(len(t)):
        av["Last Name"] += chr(int(t[j]/c[j]))
    av["Last Name"] = av["Last Name"][::-1]

    #Calculate for Phone Number
    #Strip characters that are not digits
    #Find the average of the sum of integers
    t = 0
    for i in r:
        s = i["Phone Number"]
        o = ""
        for j in s:
            if j.isdigit():
                o += j
        if o != "":
            t += int(o)
    av["Phone Number"] = int(t/len(r))

    #Calculate for Birthday
    #Get average of seconds since epoch
    t = 0
    for i in r:
        t += datetime.datetime.strptime(i["Birthday"], "%Y-%m-%d").timestamp()
    av["Birthday"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(int(t/len(r))))

    #Caluclate for Email
    #Similar to First Name
    t = []
    c = []
    for i in r:
        s = i["Email"][::-1]
        for j in range(len(s)):
            ascii = ord(s[j])
            if len(t) <= j:
                t.append(ascii)
                c.append(1)
            else:
                t[j] += ascii
                c[j] += 1
    av["Email"] = ""
    for j in range(len(t)):
        av["Email"] += chr(int(t[j]/c[j]))
    av["Email"] = av["Email"][::-1]

    #Calculate for Importance
    #Simply an average of sum
    t = 0
    for i in r:
        t += int(i["Importance"])
    av["Importance"] = int(t/len(r))
    return av

#Check if file is valid
#Prevent malicious files from being uploaded
#Such as scripts
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#Homepage
@app.route('/', methods=["GET"])
def index():
    username = get_username()
    return render_template("index.html", username=username, success=request.args.get("success"), warning=request.args.get("warning"), error=request.args.get("error"))

#Login to account
@app.route('/login', methods=["GET", "POST"])
def login():
    username = get_username()
    if request.method == "POST":
        #Get arguments
        username1 = request.form["username"]
        password = request.form["password"]

        #Hit up database for user account
        conn = sqlite3.connect("storage.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username1,))
        r = c.fetchall()

        #Account does not exist
        if r == []:
            return render_template("login.html", username=username, error="User does not exist!")
        
        #Prepare password
        hashed = hashlib.sha512((password+"saltysalt").encode("utf-8")).hexdigest()
        
        #Wrong password
        if r[0][2] != hashed:
            return render_template("login.html", username=username, error="Password is incorrect!")
        session["username"] = username1
        return redirect(url_for("index", success="Successfully logged in."))
    else:
        return render_template("login.html", username=username)

#Signup for account
@app.route('/signup', methods=["GET", "POST"])
def signup():
    username = get_username()
    if request.method == "POST":
        #Get arguments
        username1 = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm"]
        pnumber = request.form["pnumber"]

        #Hit up database to see if username is already taken
        conn = sqlite3.connect('storage.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username1,))
        r = c.fetchall()
        
        #Username is taken
        if r != []:
            return render_template("signup.html", username=username, error="Username is currently in use.")
        
        #Hit up database to see if phone number is already taken
        c.execute("SELECT * FROM users WHERE pnumber=?", (pnumber,))
        r = c.fetchall()

        #Phone number is taken
        if r != []:
            return render_template("signup.html", username=username, error="Phone number is currently in use.")
        
        #Passwords do not match
        if password != confirm:
            return render_template("signup.html", error="Password and confirmation passwords are not the same!")
        hashed = hashlib.sha512((password+"saltysalt").encode("utf-8")).hexdigest()
        c.execute("INSERT INTO users VALUES (NULL, ?, ?, ?)", (username1, hashed, pnumber,))
        conn.commit()
        c.close()
        conn.close()
        return redirect(url_for("login", success="Account successfully created."))
    else:
        return render_template("signup.html", username=username)

#Sign out of account, remove cookies
@app.route('/logout')
def logout():
    username = get_username()
    #Logging out is pointless if you are not logged in
    if username is None:
        return redirect(url_for("index", warning="Please login first!"))
    #Remove cookie
    session.pop("username", None)
    return redirect(url_for("index"))

#View contact books
@app.route('/books')
def books():
    username = get_username()
    if request.method == "GET":
        #Hit up database for all books beloging to a user
        conn = sqlite3.connect("storage.db")
        c = conn.cursor()
        c.execute("SELECT * FROM books WHERE username=?", (username,))
        r = c.fetchall()
        c.close()
        conn.close()

        #Organise book information
        un = []
        for i in r: un.append([i[2], i[1], i[4]])
        un = sorted(un ,key=lambda x: x[0])

        #Format book information nicely
        out = []
        for i in un:
            print(i[1])
            #Output date, not seconds since epoch
            s = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(i[1]))
            #Correct privacy settings
            if i[2] == "Y": p = "Public"
            else: p = "Private"
            out. append([i[0], s, p])
        return render_template("books.html", username=username, books=out)
    else:
        return render_template("books.html", username=username)

#Create a new book
@app.route('/new_book', methods=["GET", "POST"])
def new_book():
    username = get_username()
    if request.method == "GET":
        #Books belong to users, not anonymous people
        if username is None:
            return redirect(url_for("index", error="Please login first!"))
        return render_template("new_book.html", username=username)
    else:
        #Get arguments
        bookname = request.form["bookname"]
        privacy = request.form["privacy"]
        #Format settigns correctly
        if privacy == "public": privacy = "Y"
        else: privacy = "N"

        #Having two identical books is pointless
        conn = sqlite3.connect('storage.db')
        c = conn.cursor()
        c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
        r = c.fetchall()
        
        #Name is in use
        if r != []:
            return render_template("new_book.html", username=username, error="Book already exists!")
        
        c.execute("INSERT INTO books VALUES (NULL, ?, ?, ?, ?)", (int(time.time()), bookname, username, privacy,))
        conn.commit()
        c.close()
        conn.close()

        #Intialise save file
        with open("saves/"+username+"_"+bookname+".cb", "w+") as file:
            fwriter = writer(file, delimiter=',', quotechar='"')
            fwriter.writerow(["First Name", "Last Name", "Birthday", "Phone Number", "Email", "Importance"])
        return redirect(url_for("books"))

#View contacts in books
#Get prepared for try excepts
#If you demand an explanation,
#it's because I don't know how to check if a field was filled up
@app.route('/view_book', methods=["GET", "POST"])
def view_book():
    username = get_username()
    if request.method == "GET":
        bookname = request.args.get("bookname")
        if username is None:
            return redirect(url_for("index", error="Please login first!"))
        conn = sqlite3.connect('storage.db')
        c = conn.cursor()
        c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
        r = c.fetchall()
        c.close()
        conn.close()
        
        #No book exists
        if r == []:
            return redirect(url_for("books"))
        book = Book(username, bookname)
        book.load()
        r = book.all()
        av = get_average(r)
        
        #Sort rows if needed
        s = request.args.get("sort")
        if s not in ["FNAME", "LNAME", "PNUMBER", "BDAY", "EMAIL", "IMP"]:
            return render_template("view_book.html", username=username, bookname=bookname, book=r, av=av)
        convert = {"FNAME": "First Name", "LNAME": "Last Name", "BDAY": "Birthday", "PNUMBER": "Phone Number", "EMAIL": "Email", "IMP": "Importance"}
        r = book.all(convert[s])

        #Use logic to switch sorting directions
        #It will still switch even when you clcik another field
        #TODO: Reset direction when changing field
        v = request.args.get("reverse")
        if v != "T":
            return render_template("view_book.html", username=username, bookname=bookname, book=r, rev="F", av=av)
        r.reverse()
        return render_template("view_book.html", username=username, bookname=bookname, book=r, rev="T", av=av)
    else:
        #Check if the user wants to upload a file
        try:
            load = request.form["load"]
            bookname = request.args.get("bookname")

            #Please don't upload to a nonexistent book
            conn = sqlite3.connect('storage.db')
            c = conn.cursor()
            c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
            r = c.fetchall()

            #Book does not exist
            if r == []:
                return redirect(url_for("books"))

            #Most recent change updated
            c.execute("UPDATE books SET time=? WHERE username=? AND bookname=?", (int(time.time()), username, bookname,))
            conn.commit()
            c.close()
            conn.close()
            book = Book(username, bookname)
            book.load()

            #Why bother uploading nothing at all?
            if 'file' not in request.files:
                r = book.all()
                av = get_average(r)
                return render_template("view_book.html", username=username, bookname=bookname, book=r, error="No file uploaded!", av=av)
            
            #Woah there's a file!
            fileup = request.files["file"]
            if fileup.filename == "":
                r = book.all()
                av = get_average(r)
                return render_template("view_book.html", username=username, bookname=bookname, book=r, error="Empty file name!", av=av)
            
            #You are not allowed to attack my website!
            if not allowed_file(fileup.filename):
                r = book.all()
                av = get_average(r)
                return render_template("view_book.html", username=username, bookname=bookname, book=r, error="File is not .csv or .cb!", av=av)

            #Edit graph if it is public
            if r[0][4] == "Y":
                #Get owner's phone number
                conn = sqlite3.connect('storage.db')
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=?", (username,))
                s = c.fetchall()[0][3]
                l = []
                a = book.all()

                #Read graph
                with open("graph.gr", "r") as file:
                    re = DictReader(file)
                    for i in re:
                        for j in a:
                            if i["source"] != s or i["end"] != j["Phone Number"]: l.append(dict(i))
                
                #Output graph without deleted edges
                with open("graph.gr", "w+") as file:
                    fwriter = writer(file, delimiter=',', quotechar='"')
                    fwriter.writerow(["source", "end"])
                    for i in l:
                        fwriter.writerow([i["source"], i["end"]])

            #Read uploaded file as dictionary
            #Saving and reading is unecessary
            #Thanks StackOverFlow!
            #Way Yan has requested an explanation
            #We decode each line from bytes to text
            #And send a list of decoded lines to be parsed
            #At first I had to rebuild the file from a string
            #But I googled and found out that a list is a valid argument!
            co = []
            reader = DictReader([i.decode('utf-8') for i in fileup.readlines()])
            
            #Empty attributes are not allowed
            for row in reader:
                e = False
                for i in row.keys():
                    if row[i] is "":
                        e = True
                        break
                if not e:
                    co.append(dict(row))

            #You don't match the hardcoded attributes I have!
            fields = ['First Name', 'Last Name', 'Phone Number', 'Birthday', 'Email', 'Importance']
            if reader.fieldnames != fields:
                r = book.all()
                av = get_average(r)
                return render_template("view_book.html", username=username, bookname=bookname, book=r, error="Field names not valid!", av=av)

            #All past changes do not apply anymore
            undo = Changes(username, bookname, "un")
            undo.reset()
            redo = Changes(username, bookname, "re")
            redo.reset()            

            #Edit graph if it is public
            if r[0][4] == "Y":
                #Get owner's phone number
                conn = sqlite3.connect('storage.db')
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=?", (username,))
                s = c.fetchall()[0][3]

                #Output graph without new edges
                with open("graph.gr", "a+") as file:
                    fwriter = writer(file, delimiter=',', quotechar='"')
                    fwriter.writerow(["source", "end"])
                    for i in co:
                        fwriter.writerow([s, i["Phone Number"]])

            #We have finished checking and are ready to saves
            with open("saves/"+username+"_"+bookname+".cb", "w+") as file:
                fwriter = writer(file, delimiter=',', quotechar='"')
                fwriter.writerow(fields)
                for i in co:
                    row = []
                    i["Birthday"] = int(i["Birthday"])
                    i["Importance"] = int(i["Importance"])
                    for j in fields: row.append(i[j])
                    fwriter.writerow(row)
            book.load()
            r = book.all()
            av = get_average(r)
            return render_template("view_book.html", username=username, bookname=bookname, book=r, success="Successfully uploaded!", av=av)
        except:
            #Check if we need to delete
            try:
                #Get arguments
                delete = request.form["delete"]
                bookname = request.args.get("bookname")

                #Retrieve contact book from the bookshelf, known as SQLite
                conn = sqlite3.connect('storage.db')
                c = conn.cursor()
                c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
                r = c.fetchall()

                #Book does not exist
                if r == []:
                    return redirect(url_for("books"))
                c.execute("UPDATE books SET time=? WHERE username=? AND bookname=?", (int(time.time()), username, bookname,))
                conn.commit()
                c.close()
                conn.close()

                #Let's read
                book = Book(username, bookname)
                book.load()

                #Phone number is not used
                t = book.pnumber(delete)
                if t is None:
                    r = book.all()
                    av = get_average(r)
                    return render_template("view_book.html", username=username, bookname=bookname, book=r, error="Phone Number is invalid!", av=av)
                
                #Begone, contact
                book.delete(delete)
                book.save()
                book.load()

                #Push to undo stack
                undo = Changes(username, bookname, "un")
                undo.load()
                undo.insert("DELETE", t)
                undo.save()

                #Do we need to update the graph?
                conn = sqlite3.connect('storage.db')
                c = conn.cursor()
                c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
                r = c.fetchall()

                #Edit graph if it is public
                if r[0][4] == "Y":
                    c.execute("SELECT * FROM users WHERE username=?", (username,))
                    r = c.fetchall()[0]
                    l = []

                    #Read graph
                    with open("graph.gr", "r") as file:
                        re = DictReader(file)
                        for i in re:
                            if i["source"] != r[3] or i["end"] != delete: l.append(dict(i))
                    
                    #Output graph without deleted edge
                    with open("graph.gr", "w+") as file:
                        fwriter = writer(file, delimiter=',', quotechar='"')
                        fwriter.writerow(["source", "end"])
                        for i in l:
                            fwriter.writerow([i["source"], i["end"]])
                r = book.all()
                av = get_average(r)
                return render_template("view_book.html", username=username, bookname=bookname, book=r, success="Successfully Deleted!", av=av)
            except:
                #Check if we are filtering search results
                try:
                    #Get arguments
                    filter = request.form["filter"]
                    field1 = request.form["field1"]
                    value1 = request.form["value1"]
                    operator = request.form["operator"]
                    field2 = request.form["field2"]
                    value2 = request.form["value2"]
                    cond = []
                    #Convert values into dictionary keys
                    #I didn't want to do this in HTML, because I wasn't sure if it will mess up or not
                    convert = {"fname": "First Name", "lname": "Last Name", "birthday": "Birthday", "pnumber": "Phone Number", "email": "Email", "importance": "Importance"}
                    
                    #If it's None why should I consider
                    #I also need to handle people who fill up field 2 without filling up field 1
                    if field1 != "none":
                        cond.append([convert[field1], value1])
                    if field2 != "none":
                        cond.append([convert[field2], value2])
                    bookname = request.args.get("bookname")

                    #Sup database, can I have my book back?
                    conn = sqlite3.connect('storage.db')
                    c = conn.cursor()
                    c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
                    r = c.fetchall()
                    
                    #You stole my book!
                    if r == []:
                        return redirect(url_for("books"))
                    c.close()
                    conn.close()
                    book = Book(username, bookname)
                    book.load()
                    r = book.all()

                    #Check which rows fit the conditions
                    m = []
                    for i in r:
                        #Count how many conditions it fufils
                        g = 0
                        for j in cond:
                            if j[1] in str(i[j[0]]):
                                g += 1

                        #Quick crash course on Bitwise Operators
                        #and needs both bits set
                        #or needs at least one bit set
                        #xor needs exactly one bit set
                        #none needs at least one bit set
                        if operator == "and":
                            if g == 2: m.append(i)
                        elif operator == "or" or operator == "none":
                            if g > 0: m.append(i)
                        elif operator == "xor":
                            if g == 1: m.append(i)
                    av = get_average(m)
                    return render_template("view_book.html", username=username, bookname=bookname, book=m, success="Succesfully filtered!", av=av)
                except:
                    #Check if we need to undo or redo changes
                    try:
                        state = request.form["revert"]
                        bookname = request.args.get("bookname")
                        
                        #Time to mug contacts
                        conn = sqlite3.connect('storage.db')
                        c = conn.cursor()
                        c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
                        r = c.fetchall()

                        #I can't find my mugging notes!
                        if r == []:
                            return redirect(url_for("books"))
                        c.execute("UPDATE books SET time=? WHERE username=? AND bookname=?", (int(time.time()), username, bookname,))
                        conn.commit()
                        c.close()
                        conn.close()

                        #Check which way we are doing
                        if state == "undo":
                            book = Book(username, bookname)
                            book.load()
                            undo = Changes(username, bookname, "un")
                            undo.load()

                            #Nothing to be done
                            if undo.empty():
                                r = book.all()
                                av = get_average(r)
                                return render_template("view_book.html", username=username, bookname=bookname, book=r, error="Nothing to undo!", av=av)
                            t = undo.top()
                            undo.pop()
                            undo.save()

                            #We need to undo an insert operation
                            if t["Type"] == "INSERT":
                                t.pop("Type", None)

                                #Push to redo stack
                                redo = Changes(username, bookname, "re")
                                redo.load()
                                redo.insert("DELETE", t)
                                redo.save()

                                #The graph matters
                                if r[0][4] == "Y":
                                    #Find owner's phone number
                                    conn = sqlite3.connect('storage.db')
                                    c = conn.cursor()
                                    c.execute("SELECT * FROM users WHERE username=?", (username,))
                                    r = c.fetchall()[0]

                                    #Read graph
                                    l = []
                                    with open("graph.gr", "r") as file:
                                        re = DictReader(file)
                                        for i in re:
                                            if i["source"] != r[3] or i["end"] != t["Phone Number"]: l.append(dict(i))
                                    
                                    #Output graph without deleted edge
                                    with open("graph.gr", "w+") as file:
                                        fwriter = writer(file, delimiter=',', quotechar='"')
                                        fwriter.writerow(["source", "end"])
                                        for i in l:
                                            fwriter.writerow([i["source"], i["end"]])

                                #Edit book
                                book.delete(t["Phone Number"])
                                book.save()
                                book.load()
                                r = book.all()
                                av = get_average(r)
                                return render_template("view_book.html", username=username, bookname=bookname, book=r, success="Succesfully changed!", av=av)
                            #We need to undo a delete operation
                            elif t["Type"] == "DELETE":
                                t.pop("Type", None)

                                #Push to redo stack
                                redo = Changes(username, bookname, "re")
                                redo.load()
                                redo.insert("INSERT", t)
                                redo.save()

                                #Graph is changing!
                                if r[0][4] == "Y":
                                    conn = sqlite3.connect('storage.db')
                                    c = conn.cursor()
                                    c.execute("SELECT * FROM users WHERE username=?", (username,))
                                    r = c.fetchall()[0]

                                    #Append to edge list
                                    with open("graph.gr", "a+") as file:
                                        fwriter = writer(file, delimiter=',', quotechar='"')
                                        fwriter.writerow([r[3], t["Phone Number"]])

                                #Edit book
                                book.insert(t)
                                book.save()
                                book.load()
                                r = book.all()
                                av = get_average(r)
                                return render_template("view_book.html", username=username, bookname=bookname, book=r, success="Succesfully changed!", av=av)
                            elif t["Type"] == "EDIT":
                                #Assemble row to delete, and row to insert
                                #If you are wondering why it's first name / last name / phone number / email
                                #It's because the file was like this for insert and delete changes, so I used the space accordingly
                                #First Name -> Field Changed
                                #Last Name -> Old Value
                                #Phone Number -> New Value
                                #Email -> Phone Number
                                t.pop("Type", None)
                                field = t["First Name"]
                                o = t["Last Name"]
                                n = t["Phone Number"]
                                pnumber = t["Email"]
                                new = t
                                new["Phone Number"] = o
                                new["Last Name"] = n

                                #Changing phone number changes the key and messes up stuff
                                if field == "Phone Number":
                                    new["Email"] = new["Phone Number"]

                                #Push to redo stack
                                redo = Changes(username, bookname, "re")
                                redo.load()
                                redo.insert("EDIT", new)
                                redo.save()

                                #I'm going to vandalise a book
                                conn = sqlite3.connect('storage.db')
                                c = conn.cursor()
                                c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
                                r = c.fetchall()

                                #More changes to graph
                                if r[0][4] == "Y":
                                    #Get owner's phone number
                                    conn = sqlite3.connect('storage.db')
                                    c = conn.cursor()
                                    c.execute("SELECT * FROM users WHERE username=?", (username,))
                                    r = c.fetchall()[0]
                                    l = []

                                    #Read graph
                                    with open("graph.gr", "r") as file:
                                        re = DictReader(file)
                                        for i in re:
                                            if i["source"] != r[3] or i["end"] != pnumber: l.append(dict(i))
                                    l.append({"source": r[3], "end": o})

                                    #Output graph without deleted edge
                                    with open("graph.gr", "w+") as file:
                                        fwriter = writer(file, delimiter=',', quotechar='"')
                                        fwriter.writerow(["source", "end"])
                                        for i in l:
                                            fwriter.writerow([i["source"], i["end"]])

                                book = Book(username, bookname)
                                book.load()
                                #Changing phone number messes things up
                                if field == "Phone Number":
                                    pnumber = t["Last Name"]

                                #Yes, this is very hacky, but I didn't want to
                                #Write an edit function for my book and AVLTree
                                #Delete old row
                                row = book.pnumber(pnumber)
                                book.delete(pnumber)
                                book.save()
                                book.load()

                                #Insert new row
                                row[field] = t["Phone Number"]
                                book.insert(row)
                                book.save()
                                book.load()

                                r = book.all()
                                av = get_average(r)
                                return render_template("view_book.html", username=username, bookname=bookname, book=r, success="Successfully changed!", av=av)
                        elif state == "redo":
                            book = Book(username, bookname)
                            book.load()
                            redo = Changes(username, bookname, "re")
                            redo.load()

                            #Nothing to be done
                            if redo.empty():
                                r = book.all()
                                av = get_average(r)
                                return render_template("view_book.html", username=username, bookname=bookname, book=r, error="Nothing to redo!", av=av)
                            t = redo.top()
                            redo.pop()
                            redo.save()

                            #We need to redo an insert operation
                            if t["Type"] == "INSERT":
                                t.pop("Type", None)

                                #Push to undo stack
                                undo = Changes(username, bookname, "un")
                                undo.load()
                                undo.insert("DELETE", t)
                                undo.save()

                                #I'm going to touch your graph
                                if r[0][4] == "Y":
                                    #Find user's phone number
                                    conn = sqlite3.connect('storage.db')
                                    c = conn.cursor()
                                    c.execute("SELECT * FROM users WHERE username=?", (username,))
                                    r = c.fetchall()[0]

                                    #Read graph
                                    l = []
                                    with open("graph.gr", "r") as file:
                                        re = DictReader(file)
                                        for i in re:
                                            if i["source"] != r[3] or i["end"] != t["Phone Number"]: l.append(dict(i))
                                    
                                    #Output graph without deleted edge
                                    with open("graph.gr", "w+") as file:
                                        fwriter = writer(file, delimiter=',', quotechar='"')
                                        fwriter.writerow(["source", "end"])
                                        for i in l:
                                            fwriter.writerow([i["source"], i["end"]])

                                #Edit book
                                book.delete(t["Phone Number"])
                                book.save()
                                book.load()
                                r = book.all()
                                av = get_average(r)
                                return render_template("view_book.html", username=username, bookname=bookname, book=r, success="Succesfully changed!", av=av)
                            #We need to redo a delete operation
                            elif t["Type"] == "DELETE":
                                t.pop("Type", None)

                                #Push to undo stack
                                undo = Changes(username, bookname, "un")
                                undo.load()
                                undo.insert("INSERT", t)
                                undo.save()

                                #Your graph is not safe
                                if r[0][4] == "Y":
                                    #Current user's phone number
                                    conn = sqlite3.connect('storage.db')
                                    c = conn.cursor()
                                    c.execute("SELECT * FROM users WHERE username=?", (username,))
                                    r = c.fetchall()[0]

                                    #Append to edge list
                                    with open("graph.gr", "a+") as file:
                                        fwriter = writer(file, delimiter=',', quotechar='"')
                                        fwriter.writerow([r[3], t["Phone Number"]])

                                #Edit book
                                book.insert(t)
                                book.save()
                                book.load()
                                r = book.all()
                                av = get_average(r)
                                return render_template("view_book.html", username=username, bookname=bookname, book=r, success="Succesfully changed!", av=av)
                            elif t["Type"] == "EDIT":
                                #Assemble row to delete, and row to insert
                                #If you are wondering why it's first name / last name / phone number / email
                                #It's because the file was like this for insert and delete changes, so I used the space accordingly
                                #First Name -> Field Changed
                                #Last Name -> Old Value
                                #Phone Number -> New Value
                                #Email -> Phone Number
                                t.pop("Type", None)
                                field = t["First Name"]
                                o = t["Last Name"]
                                n = t["Phone Number"]
                                pnumber = t["Email"]
                                new = t
                                new["Phone Number"] = o
                                new["Last Name"] = n

                                #Changing phone number changes the key and messes up stuff
                                if field == "Phone Number":
                                    new["Email"] = new["Phone Number"]

                                #Push to undo stack
                                undo = Changes(username, bookname, "un")
                                undo.load()
                                undo.insert("EDIT", new)
                                undo.save()

                                #Please let me borrow a book
                                conn = sqlite3.connect('storage.db')
                                c = conn.cursor()
                                c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
                                r = c.fetchall()

                                #Graph to be updated
                                if r[0][4] == "Y":
                                    #Find owner's phone number
                                    conn = sqlite3.connect('storage.db')
                                    c = conn.cursor()
                                    c.execute("SELECT * FROM users WHERE username=?", (username,))
                                    r = c.fetchall()[0]
                                    l = []

                                    #Read graph
                                    with open("graph.gr", "r") as file:
                                        re = DictReader(file)
                                        for i in re:
                                            if i["source"] != r[3] or i["end"] != pnumber: l.append(dict(i))
                                    l.append({"source": r[3], "end": o})

                                    #Output graph without deleted edge
                                    with open("graph.gr", "w+") as file:
                                        fwriter = writer(file, delimiter=',', quotechar='"')
                                        fwriter.writerow(["source", "end"])
                                        for i in l:
                                            fwriter.writerow([i["source"], i["end"]])

                                book = Book(username, bookname)
                                book.load()

                                #Changing phone number messes things up
                                if field == "Phone Number":
                                    pnumber = t["Last Name"]

                                #Yes, this is very hacky, but I didn't want to
                                #Write an edit function for my book and AVLTree
                                #Delete old row
                                row = book.pnumber(pnumber)
                                book.delete(pnumber)
                                book.save()
                                book.load()

                                #Insert new row
                                row[field] = t["Phone Number"]
                                book.insert(row)
                                book.save()
                                book.load()

                                r = book.all()
                                av = get_average(r)
                                return render_template("view_book.html", username=username, bookname=bookname, book=r, success="Successfully changed!", av=av)
                        return redirect(url_for("books"))
                    except:
                        #An edit is to be made
                        #TODO: Allow edits for multiple fields with dynamic forms
                        #*vomits blood*
                        try:
                            #Get arguments
                            edit = request.form["edit"]
                            field = request.form["field"]
                            pnumber = request.form["pnumber"]
                            #Convert values into dictionary keys
                            #I didn't want to do this in HTML, because I wasn't sure if it will mess up or not
                            convert = {"fname": "First Name", "lname": "Last Name", "birthday": "Birthday", "pnumber": "Phone Number", "email": "Email", "importance": "Importance"}
                            bookname = request.args.get("bookname")

                            #Get value form appropriate field
                            #Different fields have different input types!
                            if convert[field] in ["First Name", "Last Name", "Phone Number"]:
                                value = request.form["value1"]
                            elif convert[field] == "Birthday":
                                value = int(datetime.datetime.strptime(request.form["value2"], "%Y-%m-%d").timestamp())
                            elif convert[field] == "Email":
                                value = request.form["value3"]
                            elif convert[field] == "Importance":
                                value = int(request.form["value4"])

                            #I need to mend contacts in the book
                            conn = sqlite3.connect('storage.db')
                            c = conn.cursor()
                            c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
                            r = c.fetchall()

                            #Book does not exist
                            if r == []:
                                return redirect(url_for("books"))
                            c.execute("UPDATE books SET time=? WHERE username=? AND bookname=?", (int(time.time()), username, bookname,))
                            conn.commit()
                            c.close()
                            conn.close()
                            book = Book(username, bookname)
                            book.load()

                            #I want to change phone number
                            t = book.pnumber(pnumber)
                            if convert[field] == "Phone Number":
                                c = book.pnumber(value)
                                #You can't just steal another number like that!
                                if c is not None:
                                    r = book.all()
                                    av = get_average(r)
                                    return render_template("view_book.html", username=username, bookname=bookname, book=r, error="Phone Number is invalid!", av=av)
                                #Change the graph again
                                elif r[0][4] == "Y":
                                    #Get user's phone number
                                    conn = sqlite3.connect('storage.db')
                                    c = conn.cursor()
                                    c.execute("SELECT * FROM users WHERE username=?", (username,))
                                    r = c.fetchall()[0]
                                    l = []

                                    #Read graph
                                    with open("graph.gr", "r") as file:
                                        re = DictReader(file)
                                        for i in re:
                                            if i["source"] != r[3] or i["end"] != pnumber: l.append(dict(i))
                                    l.append({"source": r[3], "end": value})

                                    #Output graph without deleted edge
                                    with open("graph.gr", "w+") as file:
                                        fwriter = writer(file, delimiter=',', quotechar='"')
                                        fwriter.writerow(["source", "end"])
                                        for i in l:
                                            fwriter.writerow([i["source"], i["end"]])

                            #No empty attributes please
                            if value == "" or value == 0:
                                r = book.all()
                                av = get_average(r)
                                return render_template("view_book.html", username=username, bookname=bookname, book=r, error="No new value!", av=av)

                            #You can't modify something that doesn't exist
                            row = book.pnumber(pnumber)
                            if row is None:
                                r = book.all()
                                av = get_average(r)
                                return render_template("view_book.html", username=username, bookname=bookname, book=r, error="No new value!", av=av)
                            
                            #Not a hacky solution
                            #Explained above
                            #Delete the row
                            book.delete(pnumber)
                            book.save()
                            book.load()

                            #Insert back
                            old = row[convert[field]]
                            row[convert[field]] = value
                            book.insert(row)
                            book.save()
                            book.load()

                            #Push to undo stack
                            undo = Changes(username, bookname, "un")
                            undo.load()

                            #I like storing things with random keys to confuse myself
                            #Empty values which are integers get padded with 0
                            t = {"First Name": convert[field], "Last Name": old, "Phone Number": value, "Birthday": 0, "Email": pnumber, "Importance": 0}
                            undo.insert("EDIT", t)
                            undo.save()

                            r = book.all()
                            av = get_average(r)
                            return render_template("view_book.html", username=username, bookname=bookname, book=r, success="Successfully edited!", av=av)
                        except:
                            #The last case is an insert
                            #Let me fill up the book
                            bookname = request.args.get("bookname")
                            conn = sqlite3.connect('storage.db')
                            c = conn.cursor()
                            c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
                            r = c.fetchall()

                            #Book does not exist
                            if r == []:
                                return redirect(url_for("books"))
                            c.execute("UPDATE books SET time=? WHERE username=? AND bookname=?", (int(time.time()), username, bookname,))
                            conn.commit()
                            c.close()
                            conn.close()
                            book = Book(username, bookname)
                            book.load()

                            #Prepare row to insert
                            d = {}
                            d["First Name"] = request.form["fname"]
                            d["Last Name"] = request.form["lname"]
                            #Convert bithday to seconds since epoch
                            #Technically a bad storage method for a date
                            #Dates too far back will fail
                            #But nobody is that old... right?
                            #If you want to be from the future so be it
                            #I don't discriminate against time travellers like Teng Yi
                            #Maybe my website clock is off
                            try:
                                d["Birthday"] = int(datetime.datetime.strptime(request.form["birthday"], "%Y-%m-%d").timestamp())
                            except:
                                r = book.all()
                                av = get_average(r)
                                return render_template("view_book.html", username=username, bookname=bookname, book=r, error="Invalid Birthday!", av=av)
                            d["Phone Number"] = request.form["pnumber"]
                            d["Email"] = request.form["email"]
                            d["Importance"] = int(request.form["importance"])

                            #Check for empty fields
                            for i in d.keys():
                                if d[i] == "":
                                    r = book.all()
                                    av = get_average(r)
                                    return render_template("view_book.html", username=username, bookname=bookname, book=r, error="Please fill all fields!", av=av)
                            
                            #Check if phone number is a duplicate
                            if book.used(d["Phone Number"]):
                                r = book.all()
                                av = get_average(r)
                                return render_template("view_book.html", username=username, bookname=bookname, book=r, error="Phone Number has been assigned!", av=av)
                            book.insert(d)
                            conn = sqlite3.connect('storage.db')
                            c = conn.cursor()
                            c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
                            r = c.fetchall()

                            #Draw edge if book is public
                            if r[0][4] == "Y":
                                c.execute("SELECT * FROM users WHERE username=?", (username,))
                                r = c.fetchall()[0]

                                #Append to edge list
                                with open("graph.gr", "a+") as file:
                                    fwriter = writer(file, delimiter=',', quotechar='"')
                                    fwriter.writerow([r[3], d["Phone Number"]])
                            book.save()
                            book.load()
                            r = book.all()
                            av = get_average(r)

                            #Push to undo stack
                            undo = Changes(username, bookname, "un")
                            undo.load()
                            undo.insert("INSERT", d)
                            undo.save()
                            redo = Changes(username, bookname, "re")
                            redo.reset()
                            return render_template("view_book.html", username=username, bookname=bookname, book=r, success="Succesfully inserted!", av=av)

#Download raw CSV file as a cb file
@app.route('/download')
def download():
    username = get_username()
    bookname = request.args.get("bookname")
    #Downloading nothing is pointless
    conn = sqlite3.connect('storage.db')
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
    r = c.fetchall()
    if r == []:
        return redirect(url_for("books"))
    return send_file("saves/"+username+"_"+bookname+".cb", attachment_filename=username+"_"+bookname+".cb", mimetype="text/csv", as_attachment=True)

#Check if end can be reached from source
@app.route('/connectivity', methods=["GET", "POST"])
def connectivity():
    username = get_username()
    if request.method == "GET":
        return render_template("connectivity.html", username=username)
    else:
        source = request.form["source"]
        end = request.form["end"]

        #Check that nodes are not empty
        if source == "" or end == "":
            return render_template("connectivity.html", username=username, error="Please fill up both fields!")
        conn = sqlite3.connect('storage.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        r = c.fetchall()[0]
        
        connect = Connectivity()
        connect.read()
        res = connect.path(source, end, r[3])
        return render_template("connectivity.html", username=username, success="Finished Calculations!", r=res)
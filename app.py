from flask import Flask, session, request, url_for, redirect, render_template, send_file
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

#Read cookies to get username
def get_username():
    if "username" in session: return session["username"]
    return None

#Get average of all fields
def get_average(r):
    if len(r) == 0: return {"First Name": "", "Last Name": "", "Phone Number": "", "Birthday": "", "Email": "", "Importance": ""}
    av = {}

    #Calculate for First Name
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
    t = 0
    for i in r:
        t += datetime.datetime.strptime(i["Birthday"], "%Y-%m-%d").timestamp()
    av["Birthday"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(int(t/len(r))))

    #Caluclate for Email
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
    t = 0
    for i in r:
        t += int(i["Importance"])
    av["Importance"] = int(t/len(r))
    return av

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
        username1 = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("storage.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username1,))
        r = c.fetchall()

        #Account does not exist
        if r == []:
            return render_template("login.html", username=username, error="User does not exist!")
        hashed = hashlib.sha512((password+"saltysalt").encode("utf-8")).hexdigest()
        
        #Wrong password
        if r[0][2] != hashed:
            return render_template("login.html", username=username, error="Password is incorrect!")
        session["username"] = username1
        return redirect(url_for("index", success="Successfully logged in."))
    else:
        return render_template("login.html", username=username)

#Signup for accoutn
@app.route('/signup', methods=["GET", "POST"])
def signup():
    username = get_username()
    if request.method == "POST":
        username1 = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm"]
        pnumber = request.form["pnumber"]
        conn = sqlite3.connect('storage.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username1,))
        r = c.fetchall()
        
        #Username is taken
        if r != []:
            return render_template("signup.html", username=username, error="Username is currently in use.")
        c.execute("SELECT * FROM users WHERE pnumber=?", (pnumber,))
        r = c.fetchall()

        #No username given
        if username == "":
            return render_template("signup.html", username=username, error="A username is required.")
        
        #No password given
        if password == "":
            return render_template("signup.html", username=username, error="A password is required.")
        
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
    if username is None:
        return redirect(url_for("index", warning="Please login first!"))
    session.pop("username", None)
    return redirect(url_for("index"))

#View contact books
@app.route('/books')
def books():
    username = get_username()
    if request.method == "GET":
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
            s = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(i[1]))
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
        if username is None:
            return redirect(url_for("index", error="Please login first!"))
        return render_template("new_book.html", username=username)
    else:
        bookname = request.form["bookname"]
        privacy = request.form["privacy"]
        if privacy == "public": privacy = "Y"
        else: privacy = "N"
        conn = sqlite3.connect('storage.db')
        c = conn.cursor()
        c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
        r = c.fetchall()
        
        #Name is in use
        if r != []:
            return render_template("new_book.html", username=username, error="Book already exists!")
        
        #No name specified
        if bookname == "":
            return render_template("new_book.html", username=username, error="A name is required.")
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
        r = sorted(r, key=lambda x: x[convert[s]])

        #Use logic to switch sorting directions
        v = request.args.get("reverse")
        if v != "T":
            return render_template("view_book.html", username=username, bookname=bookname, book=r, rev="F", av=av)
        r.reverse()
        return render_template("view_book.html", username=username, bookname=bookname, book=r, rev="T", av=av)
    else:
        #Check if we need to delete
        try:
            delete = request.form["delete"]
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

            #Phone number is not used
            t = book.pnumber(delete)
            if t is None:
                r = book.all()
                av = get_average(r)
                return render_template("view_book.html", username=username, bookname=bookname, book=r, error="Phone Number is invalid!")
            book.delete(delete)
            book.save()
            book.load()

            #Push to undo stack
            undo = Changes(username, bookname, "un")
            undo.load()
            undo.insert("DELETE", t)
            undo.save()

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
                filter = request.form["filter"]
                field1 = request.form["field1"]
                value1 = request.form["value1"]
                operator = request.form["operator"]
                field2 = request.form["field2"]
                value2 = request.form["value2"]
                cond = []
                convert = {"fname": "First Name", "lname": "Last Name", "birthday": "Birthday", "pnumber": "Phone Number", "email": "Email", "importance": "Importance"}
                if field1 != "none":
                    cond.append([convert[field1], value1])
                if field2 != "none":
                    cond.append([convert[field2], value2])
                bookname = request.args.get("bookname")
                conn = sqlite3.connect('storage.db')
                c = conn.cursor()
                c.execute("SELECT * FROM books WHERE username=? AND bookname=?", (username, bookname,))
                r = c.fetchall()
                
                #Book does not exist
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
                        if j[1] in i[j[0]]:
                            g += 1

                    # and needs both bits set
                    # or needs at least one bit set
                    # xor needs exactly one bit set
                    # none needs at least one bit set
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

                            #Edit book
                            book.insert(t)
                            book.save()
                            book.load()
                            r = book.all()
                            av = get_average(r)
                            return render_template("view_book.html", username=username, bookname=bookname, book=r, success="Succesfully changed!", av=av)
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

                            #Edit book
                            book.insert(t)
                            book.save()
                            book.load()
                            r = book.all()
                            av = get_average(r)
                            return render_template("view_book.html", username=username, bookname=bookname, book=r, success="Succesfully changed!", av=av)
                    return redirect(url_for("books"))
                #We are making an insertion
                except:
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
                    try:
                        d["Birthday"] = int(datetime.datetime.strptime(request.form["birthday"], "%Y-%m-%d").timestamp())
                    except:
                        r = book.all()
                        av = get_average(r)
                        return render_template("view_book.html", username=username, bookname=bookname, book=r, error="Please fill all fields!", av=av)
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

#Download raw CSV file
#Upload is not implemented yet
@app.route('/download')
def download():
    username = get_username()
    bookname = request.args.get("bookname")
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
        
        #If we are starting from ourselves
        if r[3] == source:
            return render_template("connectivity.html", username=username, error="Source cannot be yourself!")
        connect = Connectivity()
        connect.read()
        res = connect.path(source, end, r[3])
        return render_template("connectivity.html", username=username, success="Finished Calculations!", r=res)
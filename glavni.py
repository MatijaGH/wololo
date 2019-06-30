import bottle
from bottle import *
#import auth as auth
import psycopg2, psycopg2.extensions, psycopg2.extras
import hashlib
import webbrowser

#priklop na bazo
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) #da imamo lahko sumnike
baza = psycopg2.connect(database='sem2019_matijagh', host='baza.fmf.uni-lj.si', user='matijagh', password='f3wl64em')
#baza = psycopg2.connect(database=auth.db, host=auth.host, user=auth.user, password=auth.password)
baza.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogocimo transakcije
cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)

#bottle.TEMPLATE_PATH.insert(0,"./CoolAdmin-master")


###Pomožne funkcije
def is_int(input):
  try:
    num = int(input)
  except ValueError:
    return False
  return True


################
#test priklopa na bazo(ni še v redu, popraviti moram program za tabelo)

##def test():
##    cur.execute('''
##                    SELECT * FROM uporabnik WHERE vloga = 'agent;'
##                    ''')
##    return (cur.fetchall())
##
##print(test())
##def test2():
##    cur.execute('''
##                    SELECT * FROM uporabnik WHERE vloga = 'igralec;'
##                    ''')
##    return (cur.fetchall())
##print(test2())

################
#bottle uvod, pomozne funkcije

static_dir = "./static"
secret = "to skrivnost je zelo tezko uganiti 1094107c907cw982982c42"

def vloga(user):
    cur.execute("SELECT pooblastilo FROM uporabnik WHERE username=%s",
              [user])
    r = cur.fetchone()[0]
    return r


#def password_md5(s):
    """Vrni MD5 hash danega UTF-8 niza. Gesla vedno spravimo v bazo
       kodirana s to funkcijo."""
    #p = hashlib.md5()
    #p.update(s.encode('utf-8'))
    #return p.hexdigest()


def get_user(auto_login = True, auto_redir=False):
    """Poglej cookie in ugotovi, kdo je prijavljeni uporabnik,
       vrni njegov username in ime. Ce ni prijavljen, presumeri
       na stran za prijavo ali vrni None (advisno od auto_login).
    """
    # Dobimo username iz piskotka
    username = request.get_cookie('username', secret=secret) 
    print(username)
    c = baza.cursor()
    cur.execute('''
                    SELECT * FROM uporabnik WHERE uporabnisko_ime=%s
                    ''', [username])
    tmp = cur.fetchone()
    # Preverimo, ali ta uporabnik obstaja
    if username is not None:
        #Ce uporabnik ze prijavljen, nima smisla, da je na route login
        if auto_redir:
                if tmp[3] == 'igralec;':
                    redirect('/index-igralec/')
                elif tmp[3] == 'agent;':
                    redirect("/index-agent/")
                else:
                    redirect("/index-klub/")
        else:
            c = baza.cursor()
            c.execute("SELECT uporabnik FROM uporabnik WHERE uporabnisko_ime=%s",
					  [username])
            r = c.fetchone()
            c.close ()
            if r is not None:
                # uporabnik obstaja, vrnemo njegove podatke
                return r
    # Ce pridemo do sem, uporabnik ni prijavljen, naredimo redirect
    if auto_login:
        redirect('/login/')
    else:
        return None


#tukaj bo potrebno narediti še strani, kamor želimo preusmerjati in pogledati, kaj točno so parametri
def preusmeri(parameter, pooblastilo):
    if parameter == "agent":
        redirect('/index-agent/')
    elif parameter == "igralec":
        redirect('/index-igralec/')
    


@route("/static/<filename:path>")
def static(filename):
    """Splosna funkcija, ki servira vse staticne datoteke iz naslova
       /static/..."""
    return static_file(filename, root=static_dir)


################
#bottle routes
@get("/")
def zero_get():
    "Takoj preusmeri na login stran."
    curuser = get_user(auto_login = False, auto_redir = True)
    return template("login.html",
                           napaka=None,
                           username=None)


@get("/login/")
def login_get():
    """Serviraj formo za login."""
    curuser = get_user(auto_login = False, auto_redir = True)
    return template("login.html",
                           napaka=None,
                           username=None)

@post('/login/', method='post')
def do_login():
    """Obdelaj izpolnjeno formo za prijavo"""
    # Uporabnisko ime, ki ga je uporabnik vpisal v formo
    username = request.forms.get('username')
    # Spravimo geslo v bazo
    password = request.forms.get('password')
##    print(username)
##    print(password)
    # Preverimo, ali se je uporabnik pravilno prijavil
    c = baza.cursor()
    cur.execute('''
                    SELECT * FROM uporabnik WHERE uporabnisko_ime=%s AND geslo=%s
                    ''', [username, password])
    tmp = cur.fetchone()
    # preverimo, če je uporabnik v bazi
    if tmp is None:
            return template("login.html",
                            napaka="Nepravilna prijava.",
                            username=None
                     )
    else:
        response.set_cookie('username', username, path='/', secret=secret)
        if tmp[3] == 'igralec;':
            redirect('/index-igralec/')
        elif tmp[3] == 'agent;':
            redirect("/index-agent/")
        else:
            redirect("/index-klub/")
# else:
    #     # Vse je v redu, nastavimo cookie in preusmerimo na glavno stran
    #     response.set_cookie('username', username, path='/', secret=secret)
    #     redirect("/index/")


###GET METODE, DA PRAVILNO POKAŽE DOMAČO STRAN

@get("/index-agent/")
def index_agent_get():
    """Serviraj formo za index-agent.html"""
    username = request.get_cookie('username', secret = secret)
    cur.execute('''
                    SELECT * FROM uporabnik WHERE uporabnisko_ime=%s
                    ''', [username])
    tmp = cur.fetchone()
    ID = tmp[0]
    cur.execute(''' SELECT * FROM agent WHERE ID = %s''', [ID])
    podatki = cur.fetchone()
    ime = podatki[1]
    priimek = podatki[2]
    return template("index-agent.html", ime = ime, priimek = priimek, username = username, napaka = None)

@get("/index-igralec/")
def index_igralec_get():
    """Serviraj formo za index-igralec.html"""
    username = request.get_cookie('username', secret = secret)
    cur.execute('''
                    SELECT * FROM uporabnik WHERE uporabnisko_ime=%s
                    ''', [username])
    tmp = cur.fetchone()
    ID = tmp[0]
    print(ID)
    cur.execute(''' SELECT * FROM igralci WHERE ID = %s''', [ID])
    podatki = cur.fetchone()
    ime = podatki[1]
    priimek = podatki[2]
    drzava = podatki[3]
    placa = podatki[4]
    datum_rojstva = podatki[5]
    vrednost = podatki[6]
    klub_id = podatki[7]
    agent_id = podatki[8]

    cur.execute('''SELECT * FROM klub WHERE id = %s''',[klub_id])
    klub_vse = cur.fetchone()
    klub = klub_vse[1]
    klub_naslov = klub_vse[2]

    cur.execute('''SELECT * FROM agent WHERE id = %s''', [agent_id])
    agent_vse = cur.fetchone()
    agent_ime = agent_vse[1]
    agent_priimek = agent_vse[2]
    
  #Tukaj zbere vse ponudbe, ki so za igralca in mu pošlje obvestilo.
    cur.execute('''SELECT * FROM prestop WHERE igralec = %s
                    AND stanje_agent = %s AND stanje_klub = %s
                    AND stanje_igralec = %s''', [ID, 'TRUE','TRUE','0'])
    ponudbe = cur.fetchall()
    print(ponudbe)
    

    

    return template("index-igralec.html", klub = klub, klub_naslov = klub_naslov,
                    ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                    napaka = None)

@get("/index-klub/")
def index_klub_get():
    """Serviraj formo za index-klub.html"""
    username = request.get_cookie('username', secret = secret)
    cur.execute('''
                    SELECT * FROM uporabnik WHERE uporabnisko_ime=%s
                    ''', [username])
    tmp = cur.fetchone()
    ID = tmp[0]
    cur.execute(''' SELECT * FROM klub WHERE ID = %s''', [ID])
    podatki = cur.fetchone()
    ime = podatki[1]
    naslov = podatki[2]
    return template("index-klub.html", ime = ime, naslov = naslov, username = username, napaka = None)

@get("/index-igralec/menjaj-agenta.html")
def index_igralec_menjaj_get():
    username = request.get_cookie('username', secret = secret)
    cur.execute('''
                    SELECT * FROM uporabnik WHERE uporabnisko_ime=%s
                    ''', [username])
    tmp = cur.fetchone()
    ID = tmp[0]
    cur.execute(''' SELECT * FROM igralci WHERE ID = %s''', [ID])
    podatki = cur.fetchone()
    ime = podatki[1]
    priimek = podatki[2]
    drzava = podatki[3]
    placa = podatki[4]
    datum_rojstva = podatki[5]
    vrednost = podatki[6]
    klub_id = podatki[7]
    agent_id = podatki[8]

    cur.execute('''SELECT * FROM klub WHERE id = %s''',[klub_id])
    klub_vse = cur.fetchone()
    klub = klub_vse[1]
    klub_naslov = klub_vse[2]

    cur.execute('''SELECT * FROM agent WHERE id = %s''', [agent_id])
    agent_vse = cur.fetchone()
    agent_ime = agent_vse[1]
    agent_priimek = agent_vse[2]

    cur.execute('''SELECT * FROM agent WHERE id != %s''', [agent_id])
    ostali_agenti = cur.fetchall()
    return template("menjaj-agenta.html", klub = klub, klub_naslov = klub_naslov,
                    ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                    ostali_agenti = ostali_agenti, napaka = None)
    

@post("/index-igralec/menjaj-agenta.html")
def index_igralec_menjaj_post():
    username = request.get_cookie('username', secret = secret)
    cur.execute('''
                    SELECT * FROM uporabnik WHERE uporabnisko_ime=%s
                    ''', [username])
    tmp = cur.fetchone()
    ID = tmp[0]
    cur.execute(''' SELECT * FROM igralci WHERE ID = %s''', [ID])
    podatki = cur.fetchone()
    ime = podatki[1]
    priimek = podatki[2]
    drzava = podatki[3]
    placa = podatki[4]
    datum_rojstva = podatki[5]
    vrednost = podatki[6]
    klub_id = podatki[7]
    agent_id = podatki[8]

    cur.execute('''SELECT * FROM klub WHERE id = %s''',[klub_id])
    klub_vse = cur.fetchone()
    klub = klub_vse[1]
    klub_naslov = klub_vse[2]

    cur.execute('''SELECT * FROM agent WHERE id = %s''', [agent_id])
    agent_vse = cur.fetchone()
    agent_ime = agent_vse[1]
    agent_priimek = agent_vse[2]

    cur.execute('''SELECT * FROM agent WHERE id != %s''', [agent_id])
    ostali_agenti = cur.fetchall()  
    
    izbrani_agent = request.forms.get('select')
    if izbrani_agent is not None:
        cur.execute('''UPDATE igralci SET agent = %s''',[izbrani_agent])
        baza.commit()
        return template("menjaj-agenta.html", klub = klub, klub_naslov = klub_naslov,
                    ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                    ostali_agenti = ostali_agenti, napaka = None)
    else:
        return template("menjaj-agenta.html", klub = klub, klub_naslov = klub_naslov,
                    ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                    ostali_agenti = ostali_agenti, napaka = None)



  
    poizvedba = request.forms.get('search')
    if is_int(poizvedba):
        cur.execute('''SELECT * FROM igralci WHERE id = %s''', [poizvedba])
        rezultat_poizvedbe_igralec = cur.fetchone()
        cur.execute('''SELECT * FROM agent WHERE id = %s''', [poizvedba])
        rezultat_poizvedbe_agent = cur.fetchone()
        cur.execute('''SELECT * FROM klub WHERE id = %s''', [poizvedba])
        rezultat_poizvedbe_klub = cur.fetchone()

        rezultat_poizvedbe = [rezultat_poizvedbe_igralec, rezultat_poizvedbe_agent, rezultat_poizvedbe_klub]
        if rezultat_poizvedbe == [None, None, None]:
            return template("menjaj-agenta.html", klub = klub, klub_naslov = klub_naslov,
                    ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                    ostali_agenti = ostali_agenti, napaka = "Uporabnik z iskanim ID ne obstaja!")
        else:
            return template("menjaj-agenta.html", klub = klub, klub_naslov = klub_naslov,
                    ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                    ostali_agenti = ostali_agenti, napaka = None)
          

        
    elif isinstance(poizvedba, str):
        #Zaenkrat je treba ime napisati točno tako kot je v bazi, drugače ne njade, da se spremeniti s tem,
        #da bi pretvoril niz iz poizvedbe
        cur.execute('''SELECT * FROM igralci WHERE ime = %s''', [poizvedba])
        rezultat_poizvedbe_igralec = cur.fetchone()
        cur.execute('''SELECT * FROM agent WHERE ime = %s''', [poizvedba])
        rezultat_poizvedbe_agent = cur.fetchone()
        cur.execute('''SELECT * FROM klub WHERE ime = %s''', [poizvedba])
        rezultat_poizvedbe_klub = cur.fetchone()

        rezultat_poizvedbe = [rezultat_poizvedbe_igralec, rezultat_poizvedbe_agent, rezultat_poizvedbe_klub]
        print(rezultat_poizvedbe)
        if rezultat_poizvedbe == [None, None, None]:
            return template("menjaj-agenta.html", klub = klub, klub_naslov = klub_naslov,
                    ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                    ostali_agenti = ostali_agenti, napaka = "Uporabnik z iskanim imenom ne obstaja!")
        else:
            return template("menjaj-agenta.html", klub = klub, klub_naslov = klub_naslov,
                    ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                    ostali_agenti = ostali_agenti, napaka = None)

    return template("menjaj-agenta.html", klub = klub, klub_naslov = klub_naslov,
                    ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                    ostali_agenti = ostali_agenti, napaka = None)


###POST METODE, DA PRAVILNO DELA PO VNOSU ČESARKOLI

@post("/index-igralec/")
def index_igralec_post():
    "Kaj vse lahko stori na strani index-igralec."
    username = request.get_cookie('username', secret = secret)
    cur.execute('''
                    SELECT * FROM uporabnik WHERE uporabnisko_ime=%s
                    ''', [username])
    tmp = cur.fetchone()
    ID = tmp[0]
    cur.execute(''' SELECT * FROM igralci WHERE ID = %s''', [ID])
    podatki = cur.fetchone()
    ime = podatki[1]
    priimek = podatki[2]
    drzava = podatki[3]
    placa = podatki[4]
    datum_rojstva = podatki[5]
    vrednost = podatki[6]
    klub_id = podatki[7]
    agent_id = podatki[8]

    cur.execute('''SELECT * FROM klub WHERE id = %s''',[klub_id])
    klub_vse = cur.fetchone()
    klub = klub_vse[1]
    klub_naslov = klub_vse[2]

    cur.execute('''SELECT * FROM agent WHERE id = %s''', [agent_id])
    agent_vse = cur.fetchone()
    agent_ime = agent_vse[1]
    agent_priimek = agent_vse[2]    
    
    #Zaenkrat lahko išče le po id-jih, lahko bi dodali, da tudi po imenih, priimkih...
    #Do crasha pride tudi, če namesto številke vnesemo niz...
    poizvedba = request.forms.get('search')
    if is_int(poizvedba):
        cur.execute('''SELECT * FROM igralci WHERE id = %s''', [poizvedba])
        rezultat_poizvedbe_igralec = cur.fetchone()
        cur.execute('''SELECT * FROM agent WHERE id = %s''', [poizvedba])
        rezultat_poizvedbe_agent = cur.fetchone()
        cur.execute('''SELECT * FROM klub WHERE id = %s''', [poizvedba])
        rezultat_poizvedbe_klub = cur.fetchone()

        rezultat_poizvedbe = [rezultat_poizvedbe_igralec, rezultat_poizvedbe_agent, rezultat_poizvedbe_klub]
        if rezultat_poizvedbe == [None, None, None]:
            return template("index-igralec.html", klub = klub, klub_naslov = klub_naslov, ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                        napaka = "Oseba z iskanim ID ne obstaja!")
        else:
            return template("index-igralec.html", klub = klub, klub_naslov = klub_naslov, ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                            napaka = None)
        
    elif isinstance(poizvedba, str):
        #Zaenkrat je treba ime napisati točno tako kot je v bazi, drugače ne njade, da se spremeniti s tem,
        #da bi pretvoril niz iz poizvedbe
        cur.execute('''SELECT * FROM igralci WHERE ime = %s''', [poizvedba])
        rezultat_poizvedbe_igralec = cur.fetchone()
        cur.execute('''SELECT * FROM agent WHERE ime = %s''', [poizvedba])
        rezultat_poizvedbe_agent = cur.fetchone()
        cur.execute('''SELECT * FROM klub WHERE ime = %s''', [poizvedba])
        rezultat_poizvedbe_klub = cur.fetchone()

        rezultat_poizvedbe = [rezultat_poizvedbe_igralec, rezultat_poizvedbe_agent, rezultat_poizvedbe_klub]
        print(rezultat_poizvedbe)
        if rezultat_poizvedbe == [None, None, None]:
            return template("index-igralec.html", klub = klub, klub_naslov = klub_naslov, ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                        napaka = "Uporabnik z iskanim imenom ne obstaja!")
        else:
            return template("index-igralec.html", klub = klub, klub_naslov = klub_naslov, ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username, napaka = None)

    return template("index-igralec.html", klub = klub, klub_naslov = klub_naslov, ime = ime, priimek = priimek, drzava = drzava, placa = placa,
                    datum_rojstva = datum_rojstva, vrednost = vrednost,
                    agent_ime = agent_ime, agent_priimek = agent_priimek, username = username,
                    napaka = None)
    

@post("/index-agent/")
def index_agent_post():

    username = request.get_cookie('username', secret = secret)
    cur.execute('''
                    SELECT * FROM uporabnik WHERE uporabnisko_ime=%s
                    ''', [username])
    tmp = cur.fetchone()
    ID = tmp[0]
    cur.execute(''' SELECT * FROM agent WHERE ID = %s''', [ID])
    podatki = cur.fetchone()
    ime = podatki[1]
    priimek = podatki[2]
    
    poizvedba = request.forms.get('search')
    if is_int(poizvedba):
        cur.execute('''SELECT * FROM igralci WHERE id = %s''', [poizvedba])
        rezultat_poizvedbe_igralec = cur.fetchone()
        cur.execute('''SELECT * FROM agent WHERE id = %s''', [poizvedba])
        rezultat_poizvedbe_agent = cur.fetchone()
        cur.execute('''SELECT * FROM klub WHERE id = %s''', [poizvedba])
        rezultat_poizvedbe_klub = cur.fetchone()

        rezultat_poizvedbe = [rezultat_poizvedbe_igralec, rezultat_poizvedbe_agent, rezultat_poizvedbe_klub]
        if rezultat_poizvedbe == [None, None, None]:
            return template("index-agent.html", ime = ime, priimek = priimek, username = username,
                            napaka = "Uporabnik z iskanim ID ne obstaja!")
        else:
            return template("index-agent.html", ime = ime, priimek = priimek, username = username, napaka = None)
        
    elif isinstance(poizvedba, str):
        #Zaenkrat je treba ime napisati točno tako kot je v bazi, drugače ne njade, da se spremeniti s tem,
        #da bi pretvoril niz iz poizvedbe
        cur.execute('''SELECT * FROM igralci WHERE ime = %s''', [poizvedba])
        rezultat_poizvedbe_igralec = cur.fetchone()
        cur.execute('''SELECT * FROM agent WHERE ime = %s''', [poizvedba])
        rezultat_poizvedbe_agent = cur.fetchone()
        cur.execute('''SELECT * FROM klub WHERE ime = %s''', [poizvedba])
        rezultat_poizvedbe_klub = cur.fetchone()

        rezultat_poizvedbe = [rezultat_poizvedbe_igralec, rezultat_poizvedbe_agent, rezultat_poizvedbe_klub]
        print(rezultat_poizvedbe)
        if rezultat_poizvedbe == [None, None, None]:
            return template("index-agent.html", ime = ime, priimek = priimek, username = username,
                            napaka = "Uporabnik z iskanim imenom ne obstaja!")
        else:
            return template("index-agent.html", ime = ime, priimek = priimek, username = username, napaka = None)

    return template("index-agent.html", ime = ime, priimek = priimek, username = username, napaka = None)


@post("/index-klub/")
def index_klub_post():

    username = request.get_cookie('username', secret = secret)
    cur.execute('''
                    SELECT * FROM uporabnik WHERE uporabnisko_ime=%s
                    ''', [username])
    tmp = cur.fetchone()
    ID = tmp[0]
    cur.execute(''' SELECT * FROM klub WHERE ID = %s''', [ID])
    podatki = cur.fetchone()
    ime = podatki[1]
    naslov = podatki[2]
    return template("index-klub.html", ime = ime, naslov = naslov, username = username, napaka = None)
    
    poizvedba = request.forms.get('search')
    if is_int(poizvedba):
        cur.execute('''SELECT * FROM igralci WHERE id = %s''', [poizvedba])
        rezultat_poizvedbe_igralec = cur.fetchone()
        cur.execute('''SELECT * FROM agent WHERE id = %s''', [poizvedba])
        rezultat_poizvedbe_agent = cur.fetchone()
        cur.execute('''SELECT * FROM klub WHERE id = %s''', [poizvedba])
        rezultat_poizvedbe_klub = cur.fetchone()

        rezultat_poizvedbe = [rezultat_poizvedbe_igralec, rezultat_poizvedbe_agent, rezultat_poizvedbe_klub]
        if rezultat_poizvedbe == [None, None, None]:
            return template("index-klub.html", ime = ime, naslov = naslov, username = username,
                            napaka = "Uporabnik z iskanim ID ne obstaja!")
        else:
            return template("index-klub.html", ime = ime, naslov = naslov, username = username, napaka = None)
        
    elif isinstance(poizvedba, str):
        #Zaenkrat je treba ime napisati točno tako kot je v bazi, drugače ne njade, da se spremeniti s tem,
        #da bi pretvoril niz iz poizvedbe
        cur.execute('''SELECT * FROM igralci WHERE ime = %s''', [poizvedba])
        rezultat_poizvedbe_igralec = cur.fetchone()
        cur.execute('''SELECT * FROM agent WHERE ime = %s''', [poizvedba])
        rezultat_poizvedbe_agent = cur.fetchone()
        cur.execute('''SELECT * FROM klub WHERE ime = %s''', [poizvedba])
        rezultat_poizvedbe_klub = cur.fetchone()

        rezultat_poizvedbe = [rezultat_poizvedbe_igralec, rezultat_poizvedbe_agent, rezultat_poizvedbe_klub]
        print(rezultat_poizvedbe)
        if rezultat_poizvedbe == [None, None, None]:
            return template("index-klub.html", ime = ime, naslov = naslov, username = username,
                            napaka = "Uporabnik z iskanim imenom ne obstaja!")
        else:
            return template("index-klub.html", ime = ime, naslov = naslov, username = username, napaka = None)

    return template("index-klub.html", ime = ime, naslov = naslov, username = username, napaka = None)



@get("/prestopi/")
def prestopi_get():
    """Serviraj formo za prestopi.html"""
    return template("prestopi.html")

@get("/register/")
def register_get():
    """Serviraj formo za registracijo"""
    curuser = get_user(auto_login = False, auto_redir = True)
    return template("register.html", username = None, ime = None,
                    priimek = None, vloga = None, email = None,
                    DatumRojstva = None, geslo = None, geslo2 = None,
                    naslov = None, država = None, napaka = None)

@post("/register/", method = 'post')
def nov_zahtevek():

    #Za agenta
    username = request.forms.get('username')
    ime = request.forms.get('ime')
    priimek = request.forms.get('priimek')
    vloga= request.forms.get('vloga')
    email = request.forms.get('email')
    DatumRojstva = request.forms.get('DatumRojstva')
    naslov = request.forms.get('naslov')
    država = request.forms.get('država')

    geslo = request.forms.get('geslo')
    geslo2 = request.forms.get('geslo2')

    #Za klub
    username_klub = request.forms.get('username_klub')
    ime_klub = request.forms.get('ime_klub')
    naslov_klub = request.forms.get('naslov_klub')
##    print(vloga)
##    print(username_klub)
##    print(ime_klub)
##    print(geslo)
##    print(geslo2)
    print(država)

    
    c1 = baza.cursor()
    c1.execute("SELECT * FROM uporabnik WHERE uporabnisko_ime=%s",
              [username])
    tmp = c1.fetchone()
        
    if tmp is not None:
        return template("register.html", username = username, ime = ime,
                    priimek = priimek, vloga = vloga, email = email,
                    DatumRojstva = DatumRojstva, geslo = geslo, geslo2 = geslo2,
                    naslov = naslov, država = država, napaka="Uporabniško ime je že zavzeto, izberi novega.")

    #preverimo, ali se gesli ujemata
    if geslo != geslo2:
        return template("register.html", username = username, ime = ime,
                    priimek = priimek, vloga = vloga, email = email,
                    DatumRojstva = DatumRojstva, geslo = geslo, geslo2 = geslo2,
                    naslov = naslov, država = država, napaka="Gesli se ne ujemata!")


    #ce pridemo, do sem, je vse uredu in lahko vnesemo zahtevek v bazo

    #pogledam največji id, da bom dodajal za tem
    c1.execute("SELECT id FROM uporabnik ORDER BY id DESC LIMIT 1")
    dolzina = c1.fetchone()[0]
    id = dolzina + 1
    c = baza.cursor()
    #vnesem agenta v bazo
    if vloga == '1':
        c.execute("""INSERT INTO uporabnik (id, uporabnisko_ime, geslo, vloga)
                VALUES (%s, %s, %s, %s)""",
              [id, username, geslo, 'agent;'])
        c.execute("""INSERT INTO agent (id, ime, priimek)
                VALUES (%s, %s, %s) """,
                  [id, ime, priimek])
        return template("register.html", username = None, ime = None,
                    priimek = None, vloga = None, email = None,
                    starost = None, geslo = None, geslo2 = None,
                    naslov = None, napaka="Prošnja poslana uspešno!")
    #vnesem igralca v bazo
    elif vloga == '2':
        c.execute("""INSERT INTO uporabnik (id, uporabnisko_ime, geslo, vloga)
                VALUES (%s, %s, %s, %s)""",
              [id, username, geslo, 'igralec;'])
        c.execute("""INSERT INTO igralci (id, ime, priimek, država, plača, datum_rojstva, vrednost, klub, agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s) """,
                  [id, ime, priimek, država, '0', DatumRojstva, '0', None, None])
        print("Uspeh!")
        return template("register.html", username = None, ime = None,
                    priimek = None, vloga = None, email = None,
                    starost = None, geslo = None, geslo2 = None,
                    naslov = None, napaka="Prošnja poslana uspešno!")
    #vnesem klub v bazo
    elif vloga == '3':
        print('Gasa')
        c.execute("""INSERT INTO uporabnik (id, uporabnisko_ime, geslo, vloga)
                VALUES (%s, %s, %s, %s)""",
              [id, username, geslo, 'klub;'])
        c.execute("""INSERT INTO klub (id, ime, naslov)
                VALUES (%s, %s, %s) """,
                  [id, ime, naslov])
        print("Uspeh!")
        return template("register.html", username = None, ime = None,
                    priimek = None, vloga = None, email = None,
                    starost = None, geslo = None, geslo2 = None,
                    naslov = None, napaka="Prošnja poslana uspešno!")

@get("/logout/")
def logout():
    """Pobrisi cookie in preusmeri na login."""
    response.delete_cookie('username', path='/', secret=secret)
    #print(get_user())
    redirect('/login/')

@get("/forget-pass/")
def forget_pass_get():
    """Serviraj formo za pozabjeno geslo"""
    curuser = get_user(auto_login = False, auto_redir = True)
    return template("forget-pass.html")

@get("/form/")
def form_get():
    """Serviraj formo za form"""
    return template("form.html")





run(host='localhost', port=8080)

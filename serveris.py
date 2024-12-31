import socket
import os
import shutil
from datetime import datetime
import random
import json

def ikelti_indelius(failo_vardas):
    """Įkelia indėlius iš JSON failo. Jei failas neegzistuoja, grąžina tuščią žodyną."""
    if not os.path.exists(failo_vardas):
        return {}

    try:
        with open(failo_vardas, 'r') as f:
            data = json.load(f)

        # Konvertuojame ISO formato eilutes į datetime objektus 'pradLaikas' laukui
        for indelis in data.values():
            indelis['pradLaikas'] = datetime.fromisoformat(indelis['pradLaikas'])
        return data

    except json.JSONDecodeError as e:
        print(f"Klaida apdorojant failą '{failo_vardas}': {e}")
        return {}
    except Exception as e:
        print(f"Klaida: {e}")
        return {}

def issaugoti_indeli(data, failo_vardas):
    """Išsaugo indėlius į JSON failą. Rašo atominiu būdu, kad būtų išvengta duomenų sugadinimo."""
    try:
        # Konvertuojame datetime objektus į ISO formato eilutes
        for indelis in data.values():
            if isinstance(indelis['pradLaikas'], datetime):
                indelis['pradLaikas'] = indelis['pradLaikas'].isoformat()
            #else:
                #print(f"Klaida: 'pradLaikas' nėra datetime objektas - {indelis['pradLaikas']}")

        """Sukuriamas laikinas failas, iš kurio bus viskas atomiškai perrašyta į JSON failą"""
        laikinas_failas = f"{failo_vardas}.tmp"
        with open(laikinas_failas, 'w') as f:
            json.dump(data, f, indent=4)

        os.replace(laikinas_failas, failo_vardas)  # Atominis pakeitimas
        print(f"Sėkmingai išsaugota '{failo_vardas}'.")
    except Exception as e:
        print(f"Klaida: {e}")

def naujasIndelis(indeliai, kliento_id, suma):
    """Sukuria naują indėlį nurodytam kliento ID."""
    kliento_id = str(kliento_id)
    if kliento_id in indeliai:
        print(f"Klaida: Indėlis klientui ID {kliento_id} jau egzistuoja.")
        return  

    indeliai[kliento_id] = {
        'suma': suma,
        'pradLaikas': datetime.now()
    }

    print(f"Indėlis sukurtas klientui ID {kliento_id} su suma {suma} EUR.")

def papildytiIndeli(indeliai, kliento_id, suma):
    """Atnaujina esamo indėlio sumą."""
    if f"{kliento_id}" not in indeliai:
        raise ValueError(f"Indėlis klientui ID {kliento_id} neegzistuoja.")

    indeliai[kliento_id]['suma'] += suma
    print(f"Indėlis klientui ID {kliento_id} atnaujintas. Nauja suma: {indeliai[kliento_id]['suma']} EUR.")

def indeliuInfo(indeliai, kliento_id):
    """Patikrina esamo indėlio detales."""
    kliento_id = str(kliento_id)
    if kliento_id not in indeliai:
        raise ValueError(f"Indėlis klientui ID {kliento_id} neegzistuoja.")

    indelis = indeliai[kliento_id]
    return f"Suma: {indelis['suma']:.2f} EUR\n"

# Nustatome failų kelius ir mokestį
JSON_FAILAS = "./indeliai.json"  # JSON failo kelias, kuriame saugomi indėliai
SOKETO_FAILAS = "./banko_sim.sock"  # Socket failo kelias
MOKESTIS = 1.99  # Mokestis už operacijas

class Klientas:
    def __init__(self, id, slapt):
        """Inicializuoja klientą su ID ir slaptažodžiu."""
        self.id = id  # Kliento ID
        self.slapt = slapt  # Kliento slaptažodis

    def __str__(self):
        """Grąžina kliento informaciją kaip eilutę."""
        return (
            f"{self.id}\n"
            f"{self.slapt}\n"
        )

class Admin:
    def __init__(self, id, slapt):
        """Inicializuoja administratorių su ID ir slaptažodžiu."""
        self.id = id  # Administratoriaus ID
        self.slapt = slapt  # Administratoriaus slaptažodis

    def __str__(self):
        """Grąžina administratoriaus informaciją kaip eilutę."""
        return (
            f"{self.id}\n"
            f"{self.slapt}\n"
        )

class Kliento_seansas:
    def __init__(self):
        """Inicializuoja kliento seansą su pradžia, pabaiga ir veiksmu."""
        self.pradLaikas = None  # Seanso pradžia
        self.pabLaikas = None   # Seanso pabaiga
        self.veiksmas = None    # Seanso veiksmas

    def __str__(self):
        """Grąžina seanso informaciją kaip eilutę."""
        return (
            f"\nSeanso pradžia: {self.pradLaikas}\n"
            f"Seanso pabaiga: {self.pabLaikas}\n"
        )

####################################################################################################

def generuoti_saskaitos_numeri():
    salies_kodas = "LT"
    kontrolinis_skaicius = random.randint(10, 99)
    banko_kodas = "7300"
    kliento_nr = str(random.randint(10000000000, 99999999999))  
    return f"{salies_kodas}{kontrolinis_skaicius}{banko_kodas}{kliento_nr}"

def atidaryti_sask(veiksmas, kliento_dir, klientoSoketas):

    sask_nr = generuoti_saskaitos_numeri()

    try:
        """Sukuria sąskaitos failą su nuline sąskaitos suma"""
        with open(f"{kliento_dir}{sask_nr}.dat", "w") as f:
            f.write("0")

        veiksmas.append(f"Sukurta nauja sąskaita {sask_nr}")
        serverioPranesimas = f"Sėkmingai sukurta nauja sąskaita Nr. {sask_nr}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

    except FileNotFoundError as e:
        serverioPranesimas = f"Klaida: Nurodyta direktorija nerastas - {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"Atidarymo klaida: {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

def pervedimas(veiksmas, kliento_dir, klientoSoketas):
    try:
        #Gaunama gavėjo ID
        serverioPranesimas = "\n*** Pervedimas ***\n\nĮveskite gavėjo ID"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        gavejo_id = int(klientoSoketas.recv(4096).decode('utf-8').strip())
        if not gavejo_id:  # jeigu nesigavo skaityti soketo  
            raise Exception("Nepavyko gauti atsakymo")
        
        #Gaunama gavėjo sąskaita
        serverioPranesimas = "Įveskite gavejo sąskaitos numerį"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        gavejo_sask = klientoSoketas.recv(4096).decode('utf-8').strip()
        if not gavejo_sask:  # jeigu nesigavo skaityti soketo  
            raise Exception("Nepavyko gauti atsakymo")
        
        #Gaunama siuntėjo sąskaita
        serverioPranesimas = "Įveskite sąskaitos numerį, iš kurios norite pervesti"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        siuntejo_sask = klientoSoketas.recv(4096).decode('utf-8').strip()
        if not siuntejo_sask:  # jeigu nesigavo skaityti soketo  
            raise Exception("Nepavyko gauti atsakymo")
        
        siuntejo_dir = kliento_dir
        gavejo_dir = f"./vartotojai/{gavejo_id}/"
        vu_banko_dir = "./admin/LT11730011122233344.dat"

        #Nuskaitomi likučiai
        try:   
            with open(f"{siuntejo_dir}{siuntejo_sask}.dat") as f:
                siuntejo_likutis = float(f.read())
            with open(f"{gavejo_dir}{gavejo_sask}.dat") as f:
                gavejo_likutis = float(f.read())
            with open(f"{vu_banko_dir}", "r") as f:
                vu_banko_likutis = float(f.read())
        except FileNotFoundError:
            serverioPranesimas = "Klaida: Nurodyta sąskaita nerasta.\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return
        
        """Gaunama suma"""
        serverioPranesimas = "Įveskite pervedimo sumą"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        suma = float(klientoSoketas.recv(4096).decode('utf-8').strip())
        if suma <= 0:
            raise ValueError("Pervedimo suma turi būti teigiama.")   
        if siuntejo_likutis < suma + MOKESTIS: #Jei nepakanka lėšų
            raise ValueError("Nepakanka lėšų sąskaitoje.")

        siuntejo_likutis -= suma + MOKESTIS
        vu_banko_likutis += MOKESTIS
        gavejo_likutis += suma

        """Įrašomi nauji likučiai"""
        with open(f"{siuntejo_dir}{siuntejo_sask}.dat", 'w') as f:
            f.write(f"{siuntejo_likutis}")
        with open(f"{gavejo_dir}{gavejo_sask}.dat", 'w') as f:
            f.write(f"{gavejo_likutis}")
        with open(f"{vu_banko_dir}", 'w') as f:
            f.write(f"{vu_banko_likutis}")
        
        veiksmas.append(f"Pervesta {suma} EUR  iš {siuntejo_sask} į {gavejo_id} sąskaitą {gavejo_sask}")

        serverioPranesimas = (
            f"Pervedimas sėkmingas! Perduota {suma:.2f} EUR gavėjui ID {gavejo_id}.\n"
            f"Naujas jūsų likutis: {siuntejo_likutis:.2f} EUR\n"
        )
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

    except ValueError as e:
        serverioPranesimas = f"Klaida: {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"Pervedimo klaida: {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

def isimti_pinigus(veiksmas, kliento_dir, klientoSoketas):
    try:
        """Gaunama sąskaita"""
        serverioPranesimas = "Įveskite sąskaitos numerį"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        sask_nr = klientoSoketas.recv(4096).decode('utf-8').strip()
        if not sask_nr:  # jeigu nesigavo skaityti soketo  
            raise Exception("Nepavyko gauti atsakymo")
        
        """Gaunamas likutis, jei sąskaita nerandama, išvedama klaida"""
        try:
            with open(f"{kliento_dir}{sask_nr}.dat") as f:
                likutis = float(f.read())
        except FileNotFoundError:
            serverioPranesimas = "Klaida: Nurodyta sąskaita nerasta.\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return
        
        serverioPranesimas = "Įveskite sumą, kurią norite išimti:"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        suma = float(klientoSoketas.recv(4096).decode('utf-8').strip())

        if suma <= 0:
            raise ValueError("Įvesta suma turi būti teigiama.")
        if suma > likutis:
            raise ValueError("Nepakanka lėšų sąskaitoje.")

        likutis -= suma

        """Įrašomas naujas likutis"""
        with open(f"{kliento_dir}{sask_nr}.dat", 'w') as f: 
            f.write(f"{likutis}")

        veiksmas.append(f"Išimta {suma} EUR iš {sask_nr}")
        serverioPranesimas = f"Sėkmingai išimta {suma:.2f} EUR. Naujas likutis: {likutis:.2f} EUR\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

    except ValueError as e:
        serverioPranesimas = f"Klaida: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"Klaida išimant pinigus: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

def ideti_pinigus(veiksmas, kliento_dir, klientoSoketas):
    try:
        """Gaunama sąskaita"""
        serverioPranesimas = "Įveskite sąskaitos numerį"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        sask_nr = klientoSoketas.recv(4096).decode('utf-8').strip()
        print(sask_nr)
        if not sask_nr:  # jeigu nesigavo skaityti soketo  
            raise Exception("Nepavyko gauti atsakymo")

        """Gaunamas likutis, jei sąskaita nerasta, išvedama klaida"""
        try:
            with open(f"{kliento_dir}{sask_nr}.dat") as f:
                likutis = float(f.read())
        except FileNotFoundError:
            serverioPranesimas = "Klaida: Nurodyta sąskaita nerasta.\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return
        
        serverioPranesimas = "Įveskite sumą, kurią norite įdėti"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        suma = float(klientoSoketas.recv(4096).decode('utf-8').strip())
        if suma <= 0:  # jeigu nesigavo skaityti soketo  
            raise ValueError("Įvesta suma turi būti teigiama.")

        likutis += suma

        """Įrašomas naujas likutis"""
        with open(f"{kliento_dir}{sask_nr}.dat", 'w') as f: 
            f.write(f"{likutis}")

        veiksmas.append(f"Ideta {suma} EUR i {sask_nr}")
        serverioPranesimas = f"Sėkmingai pridėta {suma:.2f} EUR. Naujas likutis: {likutis:.2f} EUR\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

    except ValueError as e:
        serverioPranesimas = f"Klaida: {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"Klaida įdedant pinigus: {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

def likutis(veiksmas, kliento_dir, klientoSoketas):
    try:
        """Gaunama sąskaita"""
        serverioPranesimas = "Įveskite sąskaitos numerį"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        sask_nr = klientoSoketas.recv(4096).decode('utf-8').strip()
        if not sask_nr:  # jeigu nesigavo skaityti soketo  
            raise Exception("Nepavyko gauti atsakymo")

        """Parodomas likutis, jei sąskaita nerasta, išvedama klaida"""
        try:
            with open(f"{kliento_dir}{sask_nr}.dat", "r") as f:
                likutis = float(f.read())
                veiksmas.append(f"Pažiūrėtas sąskaitos {sask_nr} likutis")
                serverioPranesimas = f"Jūsų sąskaitos likutis: {likutis:.2f} EUR\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        except FileNotFoundError:
            serverioPranesimas = "Klaida: Nurodyta sąskaita nerasta.\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return
    except Exception as e:
        serverioPranesimas = f"Klaida gaunant likutį: {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

def prisijungti(klientoSoketas):

    """Gaunamas vartotojo ID"""
    serverioPranesimas ="\n*** Prisijungimas ***\n\nĮveskite vartotojo ID"
    klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    kliento_id = int(klientoSoketas.recv(4096).decode('utf-8').strip())
    if not kliento_id: # jeigu nesigavo skaityti soketo  
        raise Exception("nepavyko gauti atsakymo")

    """Gaunamas slaptažodis"""     
    serverioPranesimas = "\nĮveskite slaptažodį "
    klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    slapt = klientoSoketas.recv(4096).decode('utf-8').strip()
    if not slapt: # jeigu nesigavo skaityti soketo  
        raise Exception("nepavyko gauti atsakymo")
            
    kliento_dir = f"./vartotojai/{kliento_id}/"

    try:
        """Jei yra įvykusi failo išsaugojimo klaida, ar failas yra tuščias, išvedama klaida"""
        if os.stat(f"{kliento_dir}").st_size == 0:
                raise Exception("Failas yra tuščias, negalima įvykdyti užduoties")

        with open(f"{kliento_dir}asm_duom.dat", "r") as f:

            data = f.read().splitlines()
            varSlapt = data[1]

            """Jei įvestas slaptažodis sutampa su faile išsaugotu, prisijungiama prie paskyros"""
            if varSlapt == slapt:
                seansoPrad = datetime.now()
                serverioPranesimas = "Prisijungimas sėkmingas!\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
                return seansoPrad, kliento_id  # Return session start time and client ID
            else:
                serverioPranesimas = "ATSIJUNGTA: Neteisingas slaptažodis.\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except FileNotFoundError:
        serverioPranesimas = "ATSIJUNGTA: Naudotojas nerastas.\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

def registruoti(klientoSoketas):

    kliento_id = random.randint(10000000, 99999999)
    sask_nr = generuoti_saskaitos_numeri()

    """Sugeneruojamas vartotojo ID ir pirma sąskaita, prašoma slaptažodžio"""
    serverioPranesimas = f"\n*** Naujas klientas ***\n\nVartotojo ID: {kliento_id}\nVartotojo sąskaita: {sask_nr}\nSukurkite slaptažodį"
    klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    slapt = klientoSoketas.recv(4096).decode('utf-8').strip()
    if not slapt: # jeigu nesigavo skaityti soketo  
        raise Exception("nepavyko gauti atsakymo")

    kliento_dir = f"./vartotojai/{kliento_id}/"
    os.makedirs(kliento_dir, exist_ok=True)  # Sukuria direktoriją jei ji neegzistuoja
    klientas = Klientas(kliento_id, slapt)

    """Kliento duomenys užrašomi į failą ir į naują sąskaitą įrašoma nulinė suma"""
    try:
        with open(f"{kliento_dir}asm_duom.dat", "w") as f:
            f.write(str(klientas))
        with open(f"{kliento_dir}{sask_nr}.dat", "w") as f:
            f.write("0")

        serverioPranesimas = "Klientas sėkmingai užregistruotas!"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"ATSIJUNGTA: Nepavyko užregistruoti kliento: {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        return None, None  # Return None if registration fails

    seansoPrad = datetime.now()
    return seansoPrad, kliento_id

###########################################################################################################

def pervedimas_admin(veiksmas, failas, klientoSoketas):
    try:
        #Gaunama gavėjo ID
        serverioPranesimas = "\n*** Pervedimas ***\n\nĮveskite gavėjo ID:\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        gavejo_id = int(klientoSoketas.recv(4096).decode('utf-8').strip())
        if not gavejo_id:  # jeigu nesigavo skaityti soketo  
            raise Exception("nepavyko gauti atsakymo")
        
        #Gaunama gavėjo sąskaita
        serverioPranesimas = "Įveskite gavėjo sąskaitos numerį"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        gavejo_sask = klientoSoketas.recv(4096).decode('utf-8').strip()
        if not gavejo_sask:  # jeigu nesigavo skaityti soketo  
            raise Exception("Nepavyko gauti atsakymo")
        
        siuntejo_dir = failas
        gavejo_dir = f"./vartotojai/{gavejo_id}/"

        #Nuskaitomi likučiai
        try:
            with open(f"{siuntejo_dir}") as f:
                siuntejo_likutis = float(f.read())
            with open(f"{gavejo_dir}{gavejo_sask}.dat") as f:
                gavejo_likutis = float(f.read())

        except FileNotFoundError:
            serverioPranesimas = "Klaida: Nurodyta sąskaita nerasta.\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return
        
        """Gaunama suma"""
        serverioPranesimas = "Įveskite pervedimo sumą"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        suma = float(klientoSoketas.recv(4096).decode('utf-8').strip())
        if suma <= 0:
            raise ValueError("Pervedimo suma turi būti teigiama.")   
        if siuntejo_likutis < suma: #jei nepakanka lėšų
            raise ValueError("Nepakanka lėšų sąskaitoje.")

        siuntejo_likutis -= suma
        gavejo_likutis += suma

        """Įrašomi nauji likučiai"""
        with open(f"{siuntejo_dir}", 'w') as f:
            f.write(f"{siuntejo_likutis}")
        with open(f"{gavejo_dir}{gavejo_sask}.dat", 'w') as f:
            f.write(f"{gavejo_likutis}")
        
        veiksmas.append(f"Pervesta {suma} EUR  iš banko saskaitos į {gavejo_id} sąskaita {gavejo_sask}")

        serverioPranesimas = (
            f"Pervedimas sėkmingas! Perduota {suma:.2f} EUR gavėjui ID {gavejo_id}.\n"
            f"Naujas jūsų likutis: {siuntejo_likutis:.2f} EUR\n"
        )
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

    except ValueError as e:
        serverioPranesimas = f"Klaida: {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"Pervedimo klaida: {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

def isimti_pinigus_admin(veiksmas, failas, klientoSoketas):
    try:
        try:
            """Gaunamas likutis, jei sąskaita nerandama, išvedama klaida"""
            with open(f"{failas}") as f:
                likutis = float(f.read())
        except FileNotFoundError:
            serverioPranesimas = "Klaida: Nurodyta sąskaita nerasta.\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return
        
        serverioPranesimas = "Įveskite sumą, kurią norite išimti"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        suma = float(klientoSoketas.recv(4096).decode('utf-8').strip())

        if suma <= 0:
            raise ValueError("Įvesta suma turi būti teigiama.")
        if suma > likutis:
            raise ValueError("Nepakanka lėšų sąskaitoje.")

        likutis -= suma

        """Įrašomas naujas likutis"""
        with open(f"{failas}", 'w') as f: 
            f.write(f"{likutis}")

        veiksmas.append(f"Išimta {suma} EUR iš VU banko sąskaitos")
        serverioPranesimas = f"Sėkmingai išimta {suma:.2f} EUR. Naujas likutis: {likutis:.2f} EUR\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except ValueError as e:
        serverioPranesimas = f"Klaida: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"Klaida išimant pinigus: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

def ideti_pinigus_admin(veiksmas, failas, klientoSoketas):
    try:
        """Gaunamas likutis, jei sąskaita nerasta, išvedama klaida"""
        try:
            with open(f"{failas}") as f:
                likutis = float(f.read())
        except FileNotFoundError:
            serverioPranesimas = "Klaida: Nurodyta sąskaita nerasta.\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return
        
        serverioPranesimas = "Įveskite sumą, kurią norite įdėti"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        suma = float(klientoSoketas.recv(4096).decode('utf-8').strip())
        if suma <= 0:  # jeigu nesigavo skaityti soketo  
            raise ValueError("Įvesta suma turi būti teigiama.")

        likutis += suma

        """Įrašomas naujas likutis"""
        with open(f"{failas}", 'w') as f: 
            f.write(f"{likutis}")

        veiksmas.append(f"Įdėta {suma} EUR į VU banko sąskaita")
        serverioPranesimas = f"Sėkmingai pridėta {suma:.2f} EUR. Naujas likutis: {likutis:.2f} EUR\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

    except ValueError as e:
        serverioPranesimas = f"Klaida: {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"Klaida įdedant pinigus: {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

def likutis_admin(veiksmas, failas, klientoSoketas):
    try:
        try:
            with open(f"{failas}", "r") as f:
                likutis = float(f.read())
                veiksmas.append(f"Pažiūrėtas VU banko sąskaitos likutis")
                serverioPranesimas = f"Jūsų sąskaitos likutis: {likutis:.2f} EUR\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        except FileNotFoundError:
            serverioPranesimas = "Klaida: Nurodyta sąskaita nerasta.\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return
    except Exception as e:
        serverioPranesimas = f"Klaida gaunant likutį: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

def prisijungti_admin(klientoSoketas):
     
    """Gaunamas administratoriaus ID"""
    serverioPranesimas ="\n*** ADMINISTRATORIUS ***\n\nĮveskite administratoriaus ID"
    klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    admin_id = int(klientoSoketas.recv(4096).decode('utf-8').strip())
    if not admin_id: # jeigu nesigavo skaityti soketo  
        raise Exception("nepavyko gauti atsakymo")
    
    """Gaunamas slaptažodis"""
    serverioPranesimas = "\nIveskite slaptazodi "
    klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    slapt = klientoSoketas.recv(4096).decode('utf-8').strip()
    if not slapt: # jeigu nesigavo skaityti soketo  
        raise Exception("nepavyko gauti atsakymo")
    
    admin_dir = f"./admin/{admin_id}/"

    try:
        """Jei yra įvykusi failo išsaugojimo klaida, ar failas yra tuščias, išvedama klaida"""
        if os.stat(f"{admin_dir}").st_size == 0:
                raise Exception("Failas yra tuščias, negalima įvykdyti užduoties")
    
        with open(f"{admin_dir}duom.dat", "r") as f:

            data = f.read().splitlines()
            adminSlapt = data[1]

            """Jei įvestas slaptažodis sutampa su faile išsaugotu, prisijungiama prie paskyros"""
            if adminSlapt == slapt:
                seansoPrad = datetime.now()
                serverioPranesimas = "Prisijungimas sėkmingas!\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
                return seansoPrad, admin_id
            else:
                serverioPranesimas = "ATSIJUNGTA: Neteisingas slaptažodis.\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
                return None, None  # Return None if login fails

    except FileNotFoundError:
        serverioPranesimas = "ATSIJUNGTA: Administratorius nerastas.\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        return None, None  # Return None if user not found

def registruoti_admin(klientoSoketas):
    
    admin_id = random.randint(10000000, 99999999)

    serverioPranesimas = f"\n*** Naujas Administratorius ***\n\nAdministratoriaus ID: {admin_id}\nSukurkite slaptazodi"
    klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    slapt = klientoSoketas.recv(4096).decode('utf-8').strip()
    if not slapt: # jeigu nesigavo skaityti soketo  
        raise Exception("nepavyko gauti atsakymo")

    admin_dir = f"./admin/{admin_id}/"
    os.makedirs(admin_dir, exist_ok=True)  # Sukuria direktoriją jei ji neegzistuoja
    admin = Admin(admin_id, slapt)

    """Sukuriama naujo administratoriaus direktorija"""
    try:
        with open(f"{admin_dir}duom.dat", "w") as f:
            f.write(str(admin))

        serverioPranesimas = "Administratorius sėkmingai užregistruotas!\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

    except Exception as e:
        serverioPranesimas = f"ATSIJUNGTA: Nepavyko užregistruoti administratoriaus: {e}\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        return None, None  # Return None if registration fails

    seansoPrad = datetime.now()
    return seansoPrad, admin_id

def perziureti_vartotojus(veiksmas, klientoSoketas):
    try:
        # Nustatykite katalogą, kuriame saugomi vartotojai
        vartotoju_katalogas = "./vartotojai/"
        
        # Patikrinkite, ar katalogas egzistuoja
        if not os.path.exists(vartotoju_katalogas):
            klientoSoketas.send("Klaida: vartotojų katalogas neegzistuoja.\n\n".encode('utf-8'))
            return
        
        # Gaukite visus katalogo failų pavadinimus (vartotojų ID kaip katalogai)
        vartotojai = os.listdir(vartotoju_katalogas)
        
        # Patikrinkite, ar katalogas tuščias
        if not vartotojai:
            klientoSoketas.send("Nėra registruotų vartotojų.\n\n".encode('utf-8'))
            return

        # Sukurkite sąrašą vartotojams rodyti
        serverioPranesimas = "\n\n*** Registruoti vartotojai ***\n"
        for vartotojas in vartotojai:
            if os.path.isdir(os.path.join(vartotoju_katalogas, vartotojas)):
                serverioPranesimas += f"- Vartotojo ID: {vartotojas}\n"
                vartotojo_sask = os.listdir(f"{vartotoju_katalogas}{vartotojas}")
                for saskaita in vartotojo_sask:
                    if os.path.isdir(os.path.join(vartotoju_katalogas, vartotojas)):
                        serverioPranesimas += f"-    Sąskaita: {saskaita}\n"

        # Patikrinkite, ar bent vienas vartotojas rastas
        if serverioPranesimas == "*** Registruoti vartotojai ***\n":
            klientoSoketas.send("Nėra registruotų vartotojų.\n\n".encode('utf-8'))
        else:
            # Siųskite sąrašą administratoriui
            klientoSoketas.send((serverioPranesimas + "\n").encode('utf-8'))

        veiksmas.append("Peržiūrėti vartotojai")

    except OSError as e:
        klaidos_pranesimas = f"Klaida prieinant katalogą: {e.strerror}\n\n"
        klientoSoketas.send(klaidos_pranesimas.encode('utf-8'))
    except Exception as e:
        klaidos_pranesimas = f"Nenumatyta klaida peržiūrint vartotojus: {e}\n\n"
        klientoSoketas.send(klaidos_pranesimas.encode('utf-8'))

def istrinti_vartotoja(veiksmas, klientoSoketas):
    try:
        # Prašome įvesti vartotojo ID
        klientoSoketas.send("Įveskite vartotojo ID, kurį norite ištrinti:\n".encode('utf-8'))
        atsakymas = klientoSoketas.recv(1024).decode('utf-8').strip()

        # Nustatykite vartotojo katalogą
        vartotojo_katalogas = f"./vartotojai/{atsakymas}"

        # Patikrinkite, ar katalogas egzistuoja, jei taip, jį ištrina, jei ne išveda klkaidą
        if os.path.exists(vartotojo_katalogas) and os.path.isdir(vartotojo_katalogas):
            try:
                shutil.rmtree(vartotojo_katalogas)
                klientoSoketas.send(f"Vartotojas su ID '{atsakymas}' sėkmingai ištrintas!\n".encode('utf-8'))
                veiksmas.append(f"Ištrintas {atsakymas} vartotojas")
            except OSError as e:
                klaidos_pranesimas = f"Klaida šalinant vartotojo katalogą: {e.strerror}\n"
                klientoSoketas.send(klaidos_pranesimas.encode('utf-8'))
        else:
            klientoSoketas.send("Toks vartotojo ID nerastas arba nenurodyta katalogas.\n".encode('utf-8'))

    except Exception as e:
        klaidos_pranesimas = f"Nenumatyta klaida: {e}\n"
        klientoSoketas.send(klaidos_pranesimas.encode('utf-8'))

###########################################################################################################

def atnaujinti_indelius():
    try:
        # Įkeliame indėlius iš JSON failo
        indeliai = ikelti_indelius(JSON_FAILAS)

        dabar = datetime.now()

        vu_banko_dir = "./admin/LT11730011122233344.dat"

        """Žodyno reikšmės surašomos į sąrašą, kad būtų galima per iteracijas koreguoti"""
        for indelis in list(indeliai.values()):  
            # Skaičiuojamas skirtumas sekundėmis
            skirtumas = (dabar - indelis["pradLaikas"]).total_seconds()

            """Palūkanos skaičiuojamaos kas 3 min, 2%, jei prisijungta daug vėliau, 
            skaičiavimas kartojamas tiek kartų, kiek prabėgo laiko"""
            if skirtumas >= 180:  
                
                """Palūkanos pridedamos prie vartotojo indėlio ir atimamos iš VU banko sąskaitos"""
                for i in range(0, int(skirtumas)//30):
                    with open(f"{vu_banko_dir}", "r") as f:
                        vu_banko_likutis = float(f.read())
                    
                    vu_banko_likutis -= indelis["suma"] * 1.02 - indelis["suma"]

                    with open(f"{vu_banko_dir}", 'w') as f:
                        f.write(f"{vu_banko_likutis:.2f}")

                    indelis["suma"] *= 1.02
                    indelis["pradLaikas"] = dabar

        #Išsuagoma į JSON failą
        issaugoti_indeli(indeliai, "indeliai.json")
        print("Indėliai sėkmingai perskaičiuoti ir įrašyti")

    except Exception as e:
        print(f"Klaida atnaujinant indėlius: {e}")

def indeliai_funk(veiksmas, kliento_id, klientoSoketas):

    def indelio_lik(veiksmas, kliento_id, klientoSoketas):
        try:
            informacija = indeliuInfo(indeliai, kliento_id)
            klientoSoketas.send(f"{informacija}\n".encode('utf-8'))
            veiksmas.append("Patikrinta indėlio suma")
            return
        except ValueError as e:
            klientoSoketas.send(f"Klaida: {e}\n".encode('utf-8'))
            return

    def indelio_pap(veiksmas, kliento_id, klientoSoketas):
        try:
            """Gaunama suma"""
            serverioPranesimas = "Įveskite sumą, kurią norite įdėti:\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            suma = float(klientoSoketas.recv(4096).decode('utf-8').strip())
            if suma <= 0:  
                raise ValueError("Įvesta suma turi būti teigiama.")
            
            #Papildoma indėlio suma
            papildytiIndeli(indeliai, kliento_id, suma)
            veiksmas.append(f"Įdėta {suma} EUR į {kliento_id} indėlį")
            
            #Išsuagoma JSON faile
            issaugoti_indeli(indeliai, 'indeliai.json')
            serverioPranesimas = f"Sėkmingai pridėta {suma:.2f} EUR. Naujas likutis: {indeliai[kliento_id]['suma']:.2f} EUR\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return
        except ValueError as e:
            serverioPranesimas = f"Klaida: {e}\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return
        except Exception as e:
            serverioPranesimas = f"Klaida įdedant pinigus: {e}\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return

    def sukurti_indeli(veiksmas, kliento_id, klientoSoketas):
        try:
            #Gaunama suma
            serverioPranesimas = "Įveskite sumą, kurią norite įdėti:\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            suma = float(klientoSoketas.recv(4096).decode('utf-8').strip())
            if suma <= 0:  
                raise ValueError("Įvesta suma turi būti teigiama.")

            """Sukuriamas naujas indėlis"""
            naujasIndelis(indeliai, kliento_id, suma)
            veiksmas.append(f"Sukurtas indėlis su suma {suma:.2f} EUR")

            """Išsaugomas indėli JSON faile"""
            issaugoti_indeli(indeliai, 'indeliai.json')
            serverioPranesimas = f"Sėkmingai sukurtas indėlis. Suma: {suma:.2f} EUR\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        except ValueError as e:
            serverioPranesimas = f"Klaida: {e}\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        except Exception as e:
            serverioPranesimas = f"Klaida įdedant pinigus: {e}\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            
    def isimti_is_indelio(veiksmas, kliento_id, klientoSoketas):
        
        kliento_dir = f"./vartotojai/{kliento_id}/"

        kliento_id = str(kliento_id)

        try:
            """Gaunama sąskaita"""
            serverioPranesimas = "Įveskite banko sąskaitos numerį, i kuria perkelti pinigus:\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            sask_nr = klientoSoketas.recv(4096).decode('utf-8').strip()
            if not sask_nr:  # jei nesigavo skaityti soketo
                raise Exception("Nepavyko gauti atsakymo")

            suma = indeliai[kliento_id]["suma"]

            """Nuskaitomas likutis, suma pridedama prie likučio ir jis vėl įrašomas į failą"""
            try:
                with open(f"{kliento_dir}{sask_nr}.dat", "r") as f:
                    likutis = float(f.read())

                likutis += suma
                
                with open(f"{kliento_dir}{sask_nr}.dat", "w") as f:
                    f.write(f"{likutis}")

                del indeliai[kliento_id]

                veiksmas.append(f"Pervesta {suma:.2f} EUR į banko sąskaitą {sask_nr} iš indėlio")
                
                serverioPranesimas = (
                    f"Pervedimas sėkmingas! Perduota {suma:.2f} EUR į sąskaitą {sask_nr}.\n"
                    f"Naujas sąskaitos likutis: {likutis:.2f} EUR\n"
                )
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
                return
            except FileNotFoundError:
                serverioPranesimas = "Klaida: Nurodyta banko sąskaita nerasta.\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
                return
        except ValueError as e:
            serverioPranesimas = f"Klaida: {e}\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return
        except Exception as e:
            serverioPranesimas = f"Klaida pervedant pinigus: {e}\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            return

    grizti = 0

    try:
        while not grizti:

            indeliai = ikelti_indelius(JSON_FAILAS)

            serverioPranesimas = (
                "\n*** INDĖLIS ***\n\n"
                "1. INDĖLIO SUMA\n"
                "2. PAPILDYTI INDĖLĮ\n"
                "3. SUKURTI NAUJĄ INDĖLĮ\n"
                "4. IŠIMTI IŠ INDĖLIO PINIGUS\n"
                "5. GRĮŽTI\n\n"
                "Pasirinkite veiksmą(1-5)"        
            )

            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            atsakymas = klientoSoketas.recv(4096).decode('utf-8').strip()
            if not atsakymas:  # jeigu nesigavo skaityti soketo  
                raise Exception("Nepavyko gauti atsakymo")
            if not atsakymas.isdigit() or int(atsakymas) not in range(1, 6):
                klientoSoketas.send("Neteisingas pasirinkimas. Bandykite dar kartą.\n".encode('utf-8'))
                continue

            pasirinkimas = int(atsakymas)

            match pasirinkimas:
                case 1:
                    indelio_lik(veiksmas, kliento_id, klientoSoketas)
                case 2:
                    indelio_pap(veiksmas, kliento_id, klientoSoketas)
                case 3:
                    sukurti_indeli(veiksmas, kliento_id, klientoSoketas)
                case 4:
                    isimti_is_indelio(veiksmas, kliento_id, klientoSoketas)
                case 5:
                    grizti = 1
                
    except Exception as e:
        print(f"Klaida apdorojant kliento sesiją: {e}")
        klientoSoketas.send(f"Klaida: {e}\n".encode('utf-8'))
        return            

###########################################################################################################

def valdykAdmin(klientoSoketas):

    atsijungti = False
    pasirinkimas = 0
    seansas = Kliento_seansas()
    veiksmai = []

    try:

        while not pasirinkimas:
            serverioPranesimas = (
                "\n\n*** ADMINISTRATORIUS ***\n\n"
                "1. PRISIJUNGTI\n"
                "2. NAUJAS ADMINISTRATORIUS\n\n"
                "Pasirinkite veiksmą (1-2)"
            )

            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            atsakymas = klientoSoketas.recv(4096).decode('utf-8').strip()
            if not atsakymas:  # jeigu nesigavo skaityti soketo  
                raise Exception("Nepavyko gauti atsakymo")
            if not atsakymas.isdigit() or int(atsakymas) not in (1, 2):
                klientoSoketas.send("Neteisingas pasirinkimas. Bandykite dar kartą.\n".encode('utf-8'))
                continue

            pasirinkimas = int(atsakymas)

        if pasirinkimas == 1:
            seansas.pradLaikas, admin_id = prisijungti_admin(klientoSoketas)
        else:
            seansas.pradLaikas, admin_id = registruoti_admin(klientoSoketas)

        while not atsijungti:
            serverioPranesimas = (
                "\n*** ADMINISTRATORIUS ***\n\n"
                "1. PERŽIŪRĖTI VISUS VARTOTOJUS\n"
                "2. IŠTRINTI VARTOTOJĄ\n"
                "3. VU BANKO SĄSKAITOS LIKUTIS\n"
                "4. ĮDĖTI PINIGUS\n"
                "5. IŠIMTI PINIGUS\n"
                "6. PERVEDIMAS\n"
                "7. ATSIJUNGTI\n"
                "Pasirinkite veiksmą (1-7)"
            )
            
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            atsakymas = klientoSoketas.recv(4096).decode('utf-8').strip()
            if not atsakymas: # jeigu nesigavo skaityti soketo  
                raise Exception("nepavyko gauti atsakymo")
            if not atsakymas.isdigit() or int(atsakymas) not in range(1, 8):
                klientoSoketas.send("Neteisingas pasirinkimas. Bandykite dar kartą.\n".encode('utf-8'))
                continue

            pasirinkimas = int(atsakymas)
            admin_dir = f"./admin/{admin_id}/"
            banko_sask_dir = "./admin/LT11730011122233344.dat"

            match pasirinkimas:
                case 1:
                    perziureti_vartotojus(veiksmai, klientoSoketas)
                case 2:
                    istrinti_vartotoja(veiksmai, klientoSoketas)
                case 3:
                    likutis_admin(veiksmai, banko_sask_dir, klientoSoketas)
                case 4:
                    ideti_pinigus_admin(veiksmai, banko_sask_dir, klientoSoketas)
                case 5:
                    isimti_pinigus_admin(veiksmai, banko_sask_dir, klientoSoketas)
                case 6:
                    pervedimas_admin(veiksmai, banko_sask_dir, klientoSoketas)
                case 7:
                    atsijungti = True

        seansas.pabLaikas = datetime.now()

        try:
            with open(f"{admin_dir}seansai.dat", "a") as f:
                f.write(str(seansas))
                f.write(f"Atlikta: {', '.join(veiksmai)}")
        except Exception as e:
            print(f"Klaida išsaugant seanso informaciją: {e}")

        return
    except Exception as e:
        print(f"Klaida apdorojant administratoriaus sesiją: {e}")
        klientoSoketas.send(f"Klaida: {e}\n".encode('utf-8'))

def valdykKlienta(klientoSoketas):

    atnaujinti_indelius()
    atsijungti = False
    pasirinkimas = 0
    seansas = Kliento_seansas()
    veiksmai = []

    try:
        while not pasirinkimas:
            serverioPranesimas = (
                "\n\n*** VU BANKAS ***\n\n"
                "1. PRISIJUNGTI\n"
                "2. REGISTRUOTIS\n"
                "3. ADMINISTRATORIUS\n\n"
                "Pasirinkite veiksmą (1-3)"
            )

            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            atsakymas = klientoSoketas.recv(4096).decode('utf-8').strip()
            if not atsakymas:  # jeigu nesigavo skaityti soketo  
                raise Exception("Nepavyko gauti atsakymo")
            if not atsakymas.isdigit() or int(atsakymas) not in range(1, 4):
                klientoSoketas.send("Neteisingas pasirinkimas. Bandykite dar kartą.\n".encode('utf-8'))
                continue

            pasirinkimas = int(atsakymas)

        if pasirinkimas in (1, 2):
            if pasirinkimas == 1:
                seansas.pradLaikas, kliento_id = prisijungti(klientoSoketas)
            elif pasirinkimas == 2:
                seansas.pradLaikas, kliento_id = registruoti(klientoSoketas)
            
                    

            while not atsijungti:
                serverioPranesimas = (
                    "\n*** VU BANKAS ***\n\n"
                    "1. LIKUTIS\n"
                    "2. ĮDĖTI PINIGUS\n"
                    "3. IŠIMTI PINIGUS\n"
                    "4. PERVESTI PINIGUS\n"
                    "5. ATIDARYTI NAUJA SASKAITA\n"
                    "6. INDELIAI\n"
                    "7. ATSIJUNGTI\n\n"
                    "Pasirinkite veiksmą (1-7)"
                )

                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
                atsakymas = klientoSoketas.recv(4096).decode('utf-8').strip()
                if not atsakymas: # jeigu nesigavo skaityti soketo  
                    raise Exception("nepavyko gauti atsakymo")
                if not atsakymas.isdigit() or int(atsakymas) not in range(1, 8):
                    klientoSoketas.send("Neteisingas pasirinkimas. Bandykite dar kartą.\n".encode('utf-8'))
                    continue

                pasirinkimas = int(atsakymas)
                kliento_dir = f"./vartotojai/{kliento_id}/"

                match pasirinkimas:
                    case 1:
                        likutis(veiksmai, kliento_dir, klientoSoketas)
                    case 2:
                        ideti_pinigus(veiksmai, kliento_dir, klientoSoketas)
                    case 3:
                        isimti_pinigus(veiksmai, kliento_dir, klientoSoketas)
                    case 4:
                        pervedimas(veiksmai, kliento_dir, klientoSoketas)
                    case 5:
                        atidaryti_sask(veiksmai, kliento_dir, klientoSoketas)
                    case 6:
                        indeliai_funk(veiksmai, kliento_id, klientoSoketas)
                    case 7:
                        serverioPranesimas = "ATSIJUNGTA: Sėkmingai atsijungta. Iki pasimatymo!\n\n"
                        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
                        atsijungti = True

            seansas.pabLaikas = datetime.now()

            try:
                with open(f"{kliento_dir}seansai.dat", "a") as f:
                    f.write(str(seansas))
                    f.write(f"Atlikta: {', '.join(veiksmai)}")
            except Exception as e:
                print(f"Klaida išsaugant seanso informaciją: {e}")
        else:
            valdykAdmin(klientoSoketas)
            serverioPranesimas = "ATSIJUNGTA: Sėkmingai atsijungta. Iki pasimatymo!\n\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))

    except Exception as e:
        print(f"Klaida apdorojant kliento sesiją: {e}")
        klientoSoketas.send(f"Klaida: {e}\n".encode('utf-8'))
    finally:
        print("Klientas atsijungė...")
        klientoSoketas.close()

###########################################################################################################

def startuokServeri():
    if os.path.exists(SOKETO_FAILAS):
        os.remove(SOKETO_FAILAS)

    serverioSoketas = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    serverioSoketas.bind(SOKETO_FAILAS)
    serverioSoketas.listen()

    print(f"Serveris įjungtas:  {SOKETO_FAILAS}")
    try:
        while True:
            klientoSoketas, _ = serverioSoketas.accept()
            print("Naujas klientas")
            valdykKlienta(klientoSoketas)
    except KeyboardInterrupt:
        print("\nServeris baigia darbą.")
    finally:
        serverioSoketas.close()
        os.remove(SOKETO_FAILAS)

if __name__ == "__main__":
    
    startuokServeri()

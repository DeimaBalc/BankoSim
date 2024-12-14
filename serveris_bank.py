import socket
import os
import time
from datetime import datetime
import random

SOKETO_FAILAS = "./banko_sim.sock"

class Klientas:
    def __init__(self, id, saskaita, slapt):
        self.id = id
        self.saskaita = saskaita
        self.slapt = slapt
        self.likutis = 0
        

    def __str__(self):
        return (
            f"{self.id}\n"
            f"{self.saskaita}\n"
            f"{self.slapt}\n"
            f"{self.likutis}\n"
            
        )
    
class Kliento_seansas:
    def __init__(self, pradLaikas, pabLaikas):
        self.pradLaikas = pradLaikas
        self.pabLaikas = pabLaikas

    def __str__(self):
        return (
            
            f"\nSeanso pradzia{self.pradLaikas}\n"
            f"Seanso pabaiga{self.pabLaikas}\n\n"
        )

def dataLaikas(dt):
    rez = f'{dt.year}-{dt.month}-{dt.day}, {dt.hour}:{dt.minute}:{dt.second}'
    return rez

#def atsijungimas():



def valdykKlienta(klientoSoketas):
    try:

        serverioPranesimas = "\n\n*** VU BANKAS ***\n\nPRISIJUNGTI (1)\nREGISTRUOTIS (2)\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        atsakymas = klientoSoketas.recv(4096).decode('utf-8')
        if not atsakymas: # jeigu nesigavo skaityti soketo  
            raise Exception("nepavyko gauti atsakymo")
        login = int(atsakymas.strip())

        def registruoti():

            kliento_id = random.randint(1000, 9999)
            kliento_sask = random.randint(10000, 99999)

            serverioPranesimas = f"*** Naujas klientas ***\n\nVartotojo ID: {kliento_id}\nVartotojo Saskaita: {kliento_sask}\nSukurkite slaptazodi "
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            atsakymas = klientoSoketas.recv(4096).decode('utf-8')
            if not atsakymas: # jeigu nesigavo skaityti soketo  
                raise Exception("nepavyko gauti atsakymo")
            slapt = atsakymas.strip()

            kliento_dir = f"./vartotojai/{kliento_id}/"
            os.makedirs(kliento_dir, exist_ok=True)  # Create directory if it doesn't exist
            klientas = Klientas(kliento_id, kliento_sask, slapt)
            try:
                seansoPrad = Kliento_seansas.pradLaikas = datetime.now()
                with open(f"{kliento_dir}asm_duom.dat", "w") as f:
                    f.write(str(klientas))
                serverioPranesimas = "PABAIGA: Klientas sėkmingai užregistruotas!\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            except Exception as e:
                serverioPranesimas = f"PABAIGA: Nepavyko užregistruoti kliento: {e}\n\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))

            return seansoPrad
        
        def prisijungti():

            serverioPranesimas ="*** Prisijungimas ***\n\nIveskite vartotojo ID"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            atsakymas = klientoSoketas.recv(4096).decode('utf-8')
            if not atsakymas: # jeigu nesigavo skaityti soketo  
                raise Exception("nepavyko gauti atsakymo")
            kliento_id = int(atsakymas.strip())
            
            serverioPranesimas = "\nIveskite slaptazodi: "
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            atsakymas = klientoSoketas.recv(4096).decode('utf-8')
            if not atsakymas: # jeigu nesigavo skaityti soketo  
                raise Exception("nepavyko gauti atsakymo")
            slapt = atsakymas.strip()
            
            kliento_dir = f"./vartotojai/{kliento_id}/"
            try:
                with open(f"{kliento_dir}asm_duom.dat", "r") as f:
                    data = f.read().splitlines()
                    saved_password = data[2]
                    if saved_password == slapt:
                        seansoPrad = Kliento_seansas(datetime.now(), 0)
                        serverioPranesimas = "PABAIGA: Prisijungimas sėkmingas!\n\n"
                        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
                    else:
                        serverioPranesimas ="PABAIGA: Neteisingas slaptažodis.\n\n"
                        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            except FileNotFoundError:
                serverioPranesimas ="PABAIGA: Naudotojas nerastas.\n\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            
            return seansoPrad
            
        match login:
            case 1:
                seansoPrad = prisijungti()
            case 2:
                seansoPrad = registruoti()
        
        data = f.read().splitlines

        

        def atsijungimas(seansoPrad):

            seansas = Kliento_seansas(seansoPrad, datetime.now())
            kliento_dir = f"./vartotojai/{kliento_id}/"
            try:
                with open(f"{kliento_dir}asm_duom.dat", "w") as f:
                    f.write(str(seansas))
            finally:
                serverioPranesimas = "PABAIGA: Atsijungta!\n\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))

            

       
    except Exception as e:
        print(f"Klaida apdorojant kliento soketą: {e}")
    finally:
        print("Klientas atsijungė...")
        klientoSoketas.close()

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
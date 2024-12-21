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
    def __init__(self):
        self.pradLaikas = None
        self.pabLaikas = None
        self.veiksmas = None

    def __str__(self):
        return (
            f"\nSeanso pradžia: {self.pradLaikas}\n"
            f"Seanso pabaiga: {self.pabLaikas}\n"
            f"Atlikta: {self.veiksmas}\n"
        )



def likutis(kliento_dir, klientoSoketas):
    try:
        with open(f"{kliento_dir}asm_duom.dat") as f:
            data = f.read().splitlines()
            likutis = float(data[3])
            serverioPranesimas = f"Jūsų sąskaitos likutis: {likutis:.2f} EUR\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except FileNotFoundError:
        serverioPranesimas = "Naudotojas nerastas.\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"Klaida gaunant likutį: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))


def ideti_pinigus(kliento_dir, klientoSoketas):
    try:
        # Open the user's data file to read the current balance
        with open(f"{kliento_dir}asm_duom.dat") as f:
            data = f.read().splitlines()
        
        # Prompt the user for the amount to deposit
        serverioPranesimas = "Įveskite sumą, kurią norite įdėti:\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        
        # Receive the response from the client
        atsakymas = klientoSoketas.recv(4096).decode('utf-8') 
        suma = float(atsakymas.strip())  # Convert the response to a float
        
        # Validate the input amount
        if suma <= 0:
            raise ValueError("Įvesta suma turi būti teigiama.")

        # Update the balance
        likutis = float(data[3])  # Assuming the balance is on the fourth line
        likutis += suma

        # Write the updated balance back to the file
        with open(f"{kliento_dir}asm_duom.dat", 'w') as f:  # Open the file in write mode
            data[3] = str(likutis)  # Update the balance in the data list
            f.write("\n".join(data) + "\n")  # Ensure to add a newline at the end

        # Send success message to the client
        serverioPranesimas = f"Sėkmingai pridėta {suma:.2f} EUR. Naujas likutis: {likutis:.2f} EUR\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

    except FileNotFoundError:
        serverioPranesimas = "Naudotojas nerastas.\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except ValueError as e:
        serverioPranesimas = f"Klaida: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"Klaida įdedant pinigus: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))


def isimti_pinigus(kliento_dir, klientoSoketas):
    try:
        with open(f"{kliento_dir}asm_duom.dat") as f:
            data = f.read().splitlines()
            serverioPranesimas = "Įveskite sumą, kurią norite išimti:\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            atsakymas = klientoSoketas.recv(4096).decode('utf-8')
            suma = float(atsakymas.strip())
            likutis = float(data[3])
            if suma <= 0:
                raise ValueError("Įvesta suma turi būti teigiama.")
            if suma > likutis:
                raise ValueError("Nepakanka lėšų sąskaitoje.")

            likutis = float(data[3])

            likutis -= suma

            with open(f"{kliento_dir}asm_duom.dat", 'w') as f:  # Open the file in write mode
                data[3] = str(likutis)  # Update the balance in the data list
                f.write("\n".join(data))


        serverioPranesimas = f"Sėkmingai išimta {suma:.2f} EUR. Naujas likutis: {data['likutis']:.2f} EUR\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except FileNotFoundError:
        serverioPranesimas = "Naudotojas nerastas.\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except ValueError as e:
        serverioPranesimas = f"Klaida: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"Klaida išimant pinigus: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

def registruoti(klientoSoketas):

    kliento_id = random.randint(1000, 9999)
    kliento_sask = random.randint(10000, 99999)

    serverioPranesimas = f"\n*** Naujas klientas ***\n\nVartotojo ID: {kliento_id}\nVartotojo Saskaita: {kliento_sask}\nSukurkite slaptazodi "
    klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    atsakymas = klientoSoketas.recv(4096).decode('utf-8')
    if not atsakymas: # jeigu nesigavo skaityti soketo  
        raise Exception("nepavyko gauti atsakymo")
    slapt = atsakymas.strip()

    kliento_dir = f"./vartotojai/{kliento_id}/"
    os.makedirs(kliento_dir, exist_ok=True)  # Create directory if it doesn't exist
    klientas = Klientas(kliento_id, kliento_sask, slapt)
    try:
        with open(f"{kliento_dir}asm_duom.dat", "w") as f:
            f.write(str(klientas))
            serverioPranesimas = "Klientas sėkmingai užregistruotas!\n"
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"ATSIJUNGTA: Nepavyko užregistruoti kliento: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

    seansoPrad = datetime.now()

    return seansoPrad, kliento_id

def prisijungti(klientoSoketas):

    serverioPranesimas ="\n*** Prisijungimas ***\n\nIveskite vartotojo ID"
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
            varSlapt = data[2]
            if varSlapt == slapt:
                seansoPrad = datetime.now()
                kliento_sask = data[1]
                serverioPranesimas = "Prisijungimas sėkmingas!\n\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            else:
                serverioPranesimas ="ATSIJUNGTA: Neteisingas slaptažodis.\n\n"
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except FileNotFoundError:
        serverioPranesimas ="ATSIJUNGTA: Naudotojas nerastas.\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            
    return seansoPrad, kliento_id

def pervedimas(kliento_dir, klientoSoketas):
    try:
        serverioPranesimas = "\n*** Pervedimas ***\n\nĮveskite gavėjo ID:\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        atsakymas = klientoSoketas.recv(4096).decode('utf-8').strip()
        gavejo_id = int(atsakymas.strip())
        if not atsakymas: # jeigu nesigavo skaityti soketo  
                raise Exception("nepavyko gauti atsakymo")
        
        siuntejo_dir = kliento_dir
        gavejo_dir = f"./vartotojai/{gavejo_id}/"

        with open(f"{siuntejo_dir}asm_duom.dat") as f1:
            siuntejo_data = f1.read().splitlines()
            siuntejo_likutis = float(siuntejo_data[3])
        with open(f"{gavejo_dir}asm_duom.dat") as f2:
            gavejo_data = f2.read().splitlines()
            gavejo_likutis = float(gavejo_data[3])
        
        serverioPranesimas = "Įveskite pervedimo sumą:\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
        atsakymas = klientoSoketas.recv(4096).decode('utf-8')
        suma = float(atsakymas.strip())
        if suma <= 0:
            raise ValueError("Pervedimo suma turi būti teigiama.")   

        if siuntejo_likutis < suma:
            raise ValueError("Nepakanka lėšų sąskaitoje.")

        siuntejo_likutis = float(siuntejo_data[3])
        siuntejo_likutis -= suma

        gavejo_likutis = float(gavejo_data[3])
        gavejo_likutis += suma

        with open(f"{siuntejo_dir}asm_duom.dat", 'w') as f:  # Open the file in write mode
            siuntejo_data[3] = str(siuntejo_likutis)  # Update the balance in the data list
            f.write("\n".join(siuntejo_data))

        with open(f"{gavejo_dir}asm_duom.dat", 'w') as f:  # Open the file in write mode
            gavejo_data[3] = str(gavejo_likutis)  # Update the balance in the data list
            f.write("\n".join(gavejo_data))
        
        serverioPranesimas = (
            f"Pervedimas sėkmingas! Perduota {suma:.2f} EUR gavėjui ID {gavejo_id}.\n"
            f"Naujas jūsų likutis: {siuntejo_data[3]:.2f} EUR\n\n"
        )
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

    except FileNotFoundError:
        serverioPranesimas = "Gavėjo ID nerastas.\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except ValueError as e:
        serverioPranesimas = f"Klaida: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
    except Exception as e:
        serverioPranesimas = f"Pervedimo klaida: {e}\n\n"
        klientoSoketas.send(serverioPranesimas.encode('utf-8'))

def valdykKlienta(klientoSoketas):
    
    atsijungti = 0
    seansas = Kliento_seansas()
    try:
        while not atsijungti:
            
            serverioPranesimas = (
                "\n\n*** VU BANKAS ***\n\n"
                "1. PRISIJUNGTI\n"
                "2. REGISTRUOTIS\n\n"
                "Pasirinkite veiksmą (1/2): "
            )
            klientoSoketas.send(serverioPranesimas.encode('utf-8'))
            atsakymas = klientoSoketas.recv(4096).decode('utf-8').strip()
            if not atsakymas: # jeigu nesigavo skaityti soketo  
                raise Exception("Nepavyko gauti atsakymo")
            if not atsakymas.isdigit() or int(atsakymas) not in (1, 2):
                klientoSoketas.send("Neteisingas pasirinkimas. Bandykite dar kartą.\n".encode('utf-8'))
                continue

            pasirinkimas = int(atsakymas)

            if pasirinkimas == 1:
                seansas.pradLaikas, kliento_id = prisijungti(klientoSoketas)
            elif pasirinkimas == 2:
                seansas.pradLaikas, kliento_id = registruoti(klientoSoketas)


            while not atsijungti:
            
                serverioPranesimas = (
                    "\n\n*** VU BANKAS ***\n\n"
                    "1. LIKUTIS\n"
                    "2. ĮDĖTI PINIGUS\n"
                    "3. IŠIMTI PINIGUS\n"
                    "4. PERVESTI PINIGUS\n"
                    "5. ATSIJUNGTI\n\n"
                    "Pasirinkite veiksmą (1-5):\n"
                )
                klientoSoketas.send(serverioPranesimas.encode('utf-8'))
                atsakymas = klientoSoketas.recv(4096).decode('utf-8').strip()
                if not atsakymas: # jeigu nesigavo skaityti soketo  
                    raise Exception("nepavyko gauti atsakymo")
                if not atsakymas.isdigit() or int(atsakymas) not in range(1, 6):
                    klientoSoketas.send("Neteisingas pasirinkimas. Bandykite dar kartą.\n".encode('utf-8'))
                    continue

                veiksmas = int(atsakymas)
                kliento_dir = f"./vartotojai/{kliento_id}/"

                match veiksmas:
                    case 1:
                        likutis(kliento_dir, klientoSoketas)
                    case 2:
                        ideti_pinigus(kliento_dir, klientoSoketas)
                    case 3:
                        isimti_pinigus(kliento_dir, klientoSoketas)
                    case 4:
                        pervedimas(kliento_dir, klientoSoketas)
                    case 5:
                        serverioPranesimas = "ATSIJUNGTA: Sėkmingai atsijungta. Iki pasimatymo!\n\n"
                        klientoSoketas.send(serverioPranesimas.encode('utf-8'))
                        atsijungti = 1

        seansas.pabLaikas = datetime.now()
    #Kliento_seansas(seansoPrad, seansoPabaiga)

        try:
            with open(f"{kliento_dir}asm_duom.dat", "a") as f:
                f.write(str(seansas))
        except Exception as e:
            print(f"Klaida išsaugant seanso informaciją: {e}")

    except Exception as e:
        print(f"Klaida apdorojant kliento sesiją: {e}")
        klientoSoketas.send(f"Klaida: {e}\n".encode('utf-8'))
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

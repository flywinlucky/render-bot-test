import os
import requests
from bs4 import BeautifulSoup

# --- Configurari ---
url = "https://pumamoldova.md/ru/shop/male/footwear/shoes/371128-05"
folder_imagini = "imagini_produs"

# !!! ADAUGARE NOUA: Adaugam un User-Agent pentru a simula un browser !!!
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}

# --- Inceputul scriptului ---

if not os.path.exists(folder_imagini):
    os.makedirs(folder_imagini)
    print(f"Folderul '{folder_imagini}' a fost creat cu succes.")

try:
    # !!! MODIFICARE: Adaugam headers=headers la cererea noastra !!!
    raspuns = requests.get(url, headers=headers)
    raspuns.raise_for_status() 

    soup = BeautifulSoup(raspuns.text, 'html.parser')
    elemente_imagini = soup.find_all('a', attrs={'data-fancybox': 'gallery'})

    if not elemente_imagini:
        print("Nu am gasit imagini pe pagina folosind selectorul specificat.")
    else:
        print(f"Am gasit {len(elemente_imagini)} imagini. Incep descarcarea...")

        for index, element in enumerate(elemente_imagini):
            link_imagine = element['href']
            
            try:
                # !!! MODIFICARE: Folosim headers si la descarcarea imaginilor !!!
                imagine_data = requests.get(link_imagine, headers=headers).content
                
                nume_fisier = f"imagine_{index + 1}.jpg"
                cale_completa = os.path.join(folder_imagini, nume_fisier)

                with open(cale_completa, 'wb') as f:
                    f.write(imagine_data)
                
                print(f"✔️  Imaginea {index + 1} a fost salvata ca '{nume_fisier}'")

            except Exception as e:
                print(f"❌ A aparut o eroare la descarcarea imaginii {link_imagine}: {e}")
        
        print("\nToate imaginile au fost descarcate cu succes!")

except requests.exceptions.RequestException as e:
    print(f"❌ A aparut o eroare la accesarea URL-ului: {e}")
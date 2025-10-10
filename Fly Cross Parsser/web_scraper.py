import os
import requests
from bs4 import BeautifulSoup

# --- Configurari ---
url = "https://pumamoldova.md/ru/shop/male/footwear/shoes/371128-05"
folder_imagini = "imagini_produs"
fisier_detalii = "detalii_produs.txt"

# Adaugam un User-Agent pentru a simula un browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}

# --- Inceputul scriptului ---

try:
    print(f"Se acceseaza URL-ul: {url}")
    raspuns = requests.get(url, headers=headers)
    raspuns.raise_for_status()

    soup = BeautifulSoup(raspuns.text, 'html.parser')
    print("Pagina a fost descarcata cu succes. Incep extragerea datelor...")

    # --- 1. EXTRAGEREA DETALIILOR PRODUSULUI ---

    # Extragem numele produsului (din tag-ul <h1>)
    try:
        nume_produs = soup.find('h1').get_text(strip=True)
    except AttributeError:
        nume_produs = "Numele nu a fost gasit"

    # Extragem pretul si moneda
    try:
        valoare_pret = soup.find('span', class_='styles_prices_base_value__1SsGq').get_text(strip=True)
        moneda = soup.find('span', class_='styles_prices_base_currency__waD_x').get_text(strip=True)
        pret_complet = f"{valoare_pret} {moneda}"
    except AttributeError:
        pret_complet = "Pretul nu a fost gasit"

    # Extragem marimile disponibile
    try:
        container_marimi = soup.find('div', class_='styles_sizes_items___VYog')
        elemente_marimi = container_marimi.find_all('div', class_='styles_sizes_items_item__X5XFg')
        # Cream o lista cu marimile, curatand textul de spatii goale
        lista_marimi = [marime.get_text(strip=True) for marime in elemente_marimi]
        marimi_text = ", ".join(lista_marimi)
    except AttributeError:
        marimi_text = "Marimile nu au fost gasite"

    # Extragem descrierea completa, caracteristicile si materialele
    try:
        # Folosim .get_text() cu separator pentru a pastra randurile noi si a face textul mai lizibil
        descriere_completa = soup.find('div', id='fullDescription').get_text(separator='\n', strip=True)
    except AttributeError:
        descriere_completa = "Descrierea completa nu a fost gasita"

    # --- 2. SALVAREA DETALIILOR IN FISIER TXT ---

    # Formatam continutul pentru fisier
    continut_fisier = f"""
========================================
    DETALII PRODUS EXTRAS
========================================

Nume Produs: {nume_produs}

Pret: {pret_complet}

Marimi Disponibile:
{marimi_text}

========================================
    DESCRIERE & SPECIFICATII
========================================

{descriere_completa}
"""
    # Scriem in fisier folosind encoding='utf-8' pentru caracterele speciale (chirilice)
    with open(fisier_detalii, 'w', encoding='utf-8') as f:
        f.write(continut_fisier)
    
    print(f"✔️  Detaliile produsului au fost salvate cu succes in fisierul '{fisier_detalii}'")


    # --- 3. DESCARCAREA IMAGINILOR (ca si inainte) ---

    if not os.path.exists(folder_imagini):
        os.makedirs(folder_imagini)
    
    elemente_imagini = soup.find_all('a', attrs={'data-fancybox': 'gallery'})

    if not elemente_imagini:
        print("\nNu am gasit imagini pe pagina.")
    else:
        print(f"\nAm gasit {len(elemente_imagini)} imagini. Incep descarcarea...")
        for index, element in enumerate(elemente_imagini):
            link_imagine = element['href']
            try:
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
except Exception as e:
    print(f"❌ A aparut o eroare neasteptata: {e}")
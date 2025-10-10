import os
import requests
import re
from bs4 import BeautifulSoup

# --- Configurari ---
url = "https://pumamoldova.md/ru/shop/male/footwear/shoes/371128-05"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}

def clean_folder_name(name):
    """Elimina caracterele invalide dintr-un string pentru a-l face un nume de folder valid."""
    name = name.replace(' ', '_')
    name = re.sub(r'[^\w\-]', '', name)
    return name

# --- Inceputul scriptului ---
try:
    print(f"Se acceseaza URL-ul: {url}")
    raspuns = requests.get(url, headers=headers)
    raspuns.raise_for_status()

    soup = BeautifulSoup(raspuns.text, 'html.parser')
    print("Pagina a fost descarcata. Incep extragerea datelor...")

    # --- PASUL 1: Extragem numele si cream folderul principal ---
    try:
        nume_produs = soup.find('h1').get_text(strip=True)
    except AttributeError:
        nume_produs = "produs_necunoscut"

    folder_principal = clean_folder_name(nume_produs)
    
    if not os.path.exists(folder_principal):
        os.makedirs(folder_principal)
        print(f"Folderul principal '{folder_principal}' a fost creat.")

    # --- PASUL 2: Definim caile de salvare ---
    folder_imagini = os.path.join(folder_principal, "imagini")
    fisier_detalii = os.path.join(folder_principal, "detalii_produs.txt")

    # --- PASUL 3: Extragem restul detaliilor ---
    try:
        pret_complet = f"{soup.find('span', class_='styles_prices_base_value__1SsGq').get_text(strip=True)} {soup.find('span', class_='styles_prices_base_currency__waD_x').get_text(strip=True)}"
    except AttributeError:
        pret_complet = "Pretul nu a fost gasit"

    try:
        container_marimi = soup.find('div', class_='styles_sizes_items___VYog')
        lista_marimi = [marime.get_text(strip=True) for marime in container_marimi.find_all('div', class_='styles_sizes_items_item__X5XFg')]
        marimi_text = ", ".join(lista_marimi)
    except AttributeError:
        marimi_text = "Marimile nu au fost gasite"

    try:
        descriere_container = soup.find('div', id='fullDescription')
        descriere_completa = descriere_container.get_text(separator='\n', strip=True)
        
        # !!! MODIFICARE NOUA: Adaugam un rand liber inainte de sectiunile specificate !!!
        descriere_completa = descriere_completa.replace('Характеристики:', '\nХарактеристики:').replace('Материалы:', '\nМатериалы:')
        
    except AttributeError:
        descriere_completa = "Descrierea completa nu a fost gasita"

    # --- PASUL 4: Salvam detaliile in fisierul TXT ---
    continut_fisier = f"""
========================================
    DETALII PRODUS EXTRAS
========================================

Nume Produs: {nume_produs}
Pret: {pret_complet}
Marimi Disponibile: {marimi_text}

========================================
    DESCRIERE & SPECIFICATII
========================================

{descriere_completa}
"""
    with open(fisier_detalii, 'w', encoding='utf-8') as f:
        f.write(continut_fisier)
    
    print(f"✔️ Detaliile produsului au fost salvate in '{fisier_detalii}'")

    # --- PASUL 5: Descarcam imaginile ---
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
                print(f"✔️ Imaginea {index + 1} a fost salvata in '{cale_completa}'")
            except Exception as e:
                print(f"❌ A aparut o eroare la descarcarea imaginii {link_imagine}: {e}")
        
        print("\nToate fisierele au fost sortate cu succes!")

except requests.exceptions.RequestException as e:
    print(f"❌ A aparut o eroare la accesarea URL-ului: {e}")
except Exception as e:
    print(f"❌ A aparut o eroare neasteptata: {e}")
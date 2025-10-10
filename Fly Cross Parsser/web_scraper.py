import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin # Biblioteca pentru a combina URL-uri

# --- Configurari ---
# Poti schimba acest URL cu oricare alt produs de pe site
initial_url = "https://pumamoldova.md/ru/shop/unisex/accessories/bottle/053518-36" 
base_url = "https://pumamoldova.md"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}

def clean_folder_name(name):
    """Elimina caracterele invalide pentru a crea un nume de folder valid."""
    name = name.replace(' ', '_')
    name = re.sub(r'[^\w\-]', '', name)
    return name

# --- Inceputul scriptului ---
try:
    print(f"1. Se acceseaza URL-ul initial: {initial_url}")
    raspuns_initial = requests.get(initial_url, headers=headers)
    raspuns_initial.raise_for_status()
    soup_initial = BeautifulSoup(raspuns_initial.text, 'html.parser')

    # --- Gasim toate linkurile catre culori ---
    urls_de_procesat = set([initial_url]) # Folosim un set pentru a evita duplicatele
    culori_disponibile = []
    
    container_culori = soup_initial.find('div', class_='styles_colors__xzK99')
    if container_culori:
        print("S-a gasit un bloc de culori. Se colecteaza linkurile...")
        linkuri_culori = container_culori.find_all('a', class_='styles_colors_item__ugdmF')
        for link in linkuri_culori:
            # Construim URL-ul complet (ex: https://site.com + /ru/shop/...)
            url_complet = urljoin(base_url, link['href'])
            urls_de_procesat.add(url_complet)
            
            # Extragem si numele culorii
            nume_culoare = link.find('span', class_='styles_colors_item_name__5MA9U')
            if nume_culoare:
                culori_disponibile.append(nume_culoare.get_text(strip=True))
    else:
        print("Nu s-au gasit alte culori. Se proceseaza doar produsul curent.")

    urls_de_procesat = list(urls_de_procesat)
    print(f"Total URL-uri de procesat: {len(urls_de_procesat)}")

    # --- Extragem detaliile principale de pe prima pagina ---
    nume_produs = soup_initial.find('h1').get_text(strip=True)
    folder_principal = clean_folder_name(nume_produs)
    if not os.path.exists(folder_principal):
        os.makedirs(folder_principal)

    fisier_detalii = os.path.join(folder_principal, "detalii_produs.txt")
    folder_imagini = os.path.join(folder_principal, "imagini")
    if not os.path.exists(folder_imagini):
        os.makedirs(folder_imagini)

    # Colectam celelalte detalii o singura data
    pret_complet = f"{soup_initial.find('span', class_='styles_prices_base_value__1SsGq').get_text(strip=True)} {soup_initial.find('span', class_='styles_prices_base_currency__waD_x').get_text(strip=True)}"
    
    try:
        container_marimi = soup_initial.find('div', class_='styles_sizes_items___VYog')
        lista_marimi = [m.get_text(strip=True) for m in container_marimi.find_all('div', class_='styles_sizes_items_item__X5XFg')]
        marimi_text = ", ".join(lista_marimi)
    except AttributeError:
        marimi_text = "N/A"

    descriere_completa = soup_initial.find('div', id='fullDescription').get_text(separator='\n', strip=True)
    descriere_completa = descriere_completa.replace('Характеристики:', '\nХарактеристики:').replace('Материалы:', '\nМатериалы:')

    # Scriem detaliile in fisier, inclusiv lista de culori
    with open(fisier_detalii, 'w', encoding='utf-8') as f:
        f.write(f"Nume Produs: {nume_produs}\n")
        f.write(f"Pret: {pret_complet}\n")
        f.write(f"Marimi Disponibile: {marimi_text}\n")
        if culori_disponibile:
            f.write(f"Culori Disponibile: {', '.join(culori_disponibile)}\n")
        f.write("\n================ DESCRIERE =================\n\n")
        f.write(descriere_completa)
    print(f"✔️ Detaliile complete au fost salvate in '{fisier_detalii}'")

    # --- Procesam fiecare URL pentru a descarca imaginile ---
    contor_imagini = 1
    print("\n2. Incepe descarcarea imaginilor pentru toate culorile...\n")
    for i, url in enumerate(urls_de_procesat):
        try:
            print(f"--- Procesare URL {i+1}/{len(urls_de_procesat)}: {url} ---")
            raspuns = requests.get(url, headers=headers)
            soup = BeautifulSoup(raspuns.text, 'html.parser')
            
            elemente_imagini = soup.find_all('a', attrs={'data-fancybox': 'gallery'})
            if not elemente_imagini:
                print("   -> Nu s-au gasit imagini la acest link.")
                continue

            for element in elemente_imagini:
                link_imagine = element['href']
                imagine_data = requests.get(link_imagine, headers=headers).content
                nume_fisier = f"imagine_{contor_imagini}.jpg"
                cale_completa = os.path.join(folder_imagini, nume_fisier)
                with open(cale_completa, 'wb') as f:
                    f.write(imagine_data)
                print(f"   -> ✔️ Imaginea salvata ca '{nume_fisier}'")
                contor_imagini += 1
        except Exception as e:
            print(f"   -> ❌ Eroare la procesarea URL-ului {url}: {e}")

    print(f"\nProces finalizat! Au fost descarcate in total {contor_imagini - 1} imagini.")

except requests.exceptions.RequestException as e:
    print(f"❌ A aparut o eroare la accesarea URL-ului initial: {e}")
except Exception as e:
    print(f"❌ A aparut o eroare neasteptata: {e}")
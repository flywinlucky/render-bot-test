import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- Configurari ---
initial_url = "https://pumamoldova.md/ru/shop/unisex/accessories/bottle/053518-36" 
base_url = "https://pumamoldova.md"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}

def clean_folder_name(name):
    """Curata un string pentru a fi un nume de folder valid."""
    name = name.replace(' ', '_')
    # Elimina orice caracter invalid
    name = re.sub(r'[^\w\-\.]', '', name)
    return name

# --- Inceputul scriptului ---
try:
    print(f"1. Se acceseaza URL-ul initial: {initial_url}")
    raspuns_initial = requests.get(initial_url, headers=headers)
    raspuns_initial.raise_for_status()
    soup_initial = BeautifulSoup(raspuns_initial.text, 'html.parser')

    # --- Colectam informatii despre culori (nume + URL) ---
    culori_de_procesat = []
    
    container_culori = soup_initial.find('div', class_='styles_colors__xzK99')
    if container_culori:
        print("S-a gasit un bloc de culori. Se colecteaza datele...")
        linkuri_culori = container_culori.find_all('a', class_='styles_colors_item__ugdmF')
        for link in linkuri_culori:
            nume_culoare_tag = link.find('span', class_='styles_colors_item_name__5MA9U')
            if link.has_attr('href') and nume_culoare_tag:
                nume_culoare = nume_culoare_tag.get_text(strip=True)
                url_complet = urljoin(base_url, link['href'])
                culori_de_procesat.append({'nume': nume_culoare, 'url': url_complet})
    
    # Daca nu am gasit culori, procesam doar pagina curenta
    if not culori_de_procesat:
        print("Nu s-au gasit alte culori. Se proceseaza doar produsul curent.")
        culori_de_procesat.append({'nume': 'imagini', 'url': initial_url})

    # --- Extragem detaliile o singura data si cream folderul principal ---
    nume_produs = soup_initial.find('h1').get_text(strip=True)
    folder_principal = clean_folder_name(nume_produs)
    if not os.path.exists(folder_principal):
        os.makedirs(folder_principal)
    
    print(f"S-a creat folderul principal: '{folder_principal}'")

    fisier_detalii = os.path.join(folder_principal, "detalii_produs.txt")

    # Colectam celelalte detalii
    pret_complet = f"{soup_initial.find('span', class_='styles_prices_base_value__1SsGq').get_text(strip=True)} {soup_initial.find('span', class_='styles_prices_base_currency__waD_x').get_text(strip=True)}"
    try:
        container_marimi = soup_initial.find('div', class_='styles_sizes_items___VYog')
        lista_marimi = [m.get_text(strip=True) for m in container_marimi.find_all('div', class_='styles_sizes_items_item__X5XFg')]
        marimi_text = ", ".join(lista_marimi)
    except: marimi_text = "N/A"
    descriere_completa = soup_initial.find('div', id='fullDescription').get_text(separator='\n', strip=True).replace('Характеристики:', '\nХарактеристики:').replace('Материалы:', '\nМатериалы:')

    # Scriem detaliile in fisier
    with open(fisier_detalii, 'w', encoding='utf-8') as f:
        f.write(f"Nume Produs: {nume_produs}\n")
        f.write(f"Pret: {pret_complet}\n")
        f.write(f"Marimi Disponibile: {marimi_text}\n")
        if len(culori_de_procesat) > 1 or culori_de_procesat[0]['nume'] != 'imagini':
             f.write(f"Culori Disponibile: {', '.join([c['nume'] for c in culori_de_procesat])}\n")
        f.write("\n================ DESCRIERE =================\n\n")
        f.write(descriere_completa)
    print(f"✔️ Detaliile complete au fost salvate in '{fisier_detalii}'")

    # --- Procesam fiecare culoare pentru a descarca imaginile in foldere separate ---
    print("\n2. Incepe descarcarea imaginilor in foldere separate pentru fiecare culoare...\n")
    for culoare_info in culori_de_procesat:
        nume_culoare = culoare_info['nume']
        url = culoare_info['url']
        
        # Cream un folder pentru culoare
        folder_culoare_curata = clean_folder_name(nume_culoare)
        cale_folder_culoare = os.path.join(folder_principal, folder_culoare_curata)
        if not os.path.exists(cale_folder_culoare):
            os.makedirs(cale_folder_culoare)
            
        try:
            print(f"--- Procesare culoare: '{nume_culoare}' ---")
            raspuns = requests.get(url, headers=headers)
            soup = BeautifulSoup(raspuns.text, 'html.parser')
            
            elemente_imagini = soup.find_all('a', attrs={'data-fancybox': 'gallery'})
            if not elemente_imagini:
                print("   -> Nu s-au gasit imagini la acest link.")
                continue

            # Descarcam imaginile in folderul specific culorii
            for index, element in enumerate(elemente_imagini):
                link_imagine = element['href']
                imagine_data = requests.get(link_imagine, headers=headers).content
                nume_fisier = f"imagine_{index + 1}.jpg"
                cale_completa = os.path.join(cale_folder_culoare, nume_fisier)
                with open(cale_completa, 'wb') as f:
                    f.write(imagine_data)
                print(f"   -> ✔️ Imaginea salvata in '{cale_completa}'")

        except Exception as e:
            print(f"   -> ❌ Eroare la procesarea culorii {nume_culoare}: {e}")

    print(f"\nProces finalizat! Imaginile au fost sortate pe foldere.")

except Exception as e:
    print(f"❌ A aparut o eroare generala: {e}")
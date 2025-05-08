import cloudscraper
from lxml import html

def get_name_from_rut(rut):
    url = f"https://www.nombrerutyfirma.com/rut?term={rut}"
    
    # Iniciar un scraper que evade Cloudflare
    scraper = cloudscraper.create_scraper()

    response = scraper.get(url)

    if response.status_code == 200:
        tree = html.fromstring(response.content)
        name_xpath = "/html/body/div[2]/div/table/tbody/tr[1]/td[1]"
        name_elements = tree.xpath(name_xpath)
        
        if name_elements:
            return name_elements[0].text.strip()
        else:
            return "Nombre no encontrado"
    else:
        return f"Error {response.status_code}: Acceso bloqueado"

if __name__ == "__main__":
    rut = "9.637.604-9"
    name = get_name_from_rut(rut)
    print(f"Nombre asociado al RUT {rut}: {name}")

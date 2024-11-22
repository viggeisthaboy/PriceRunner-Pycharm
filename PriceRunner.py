import os  # För att köra Git-kommandon och ljud
import time
import requests
import csv
import random
import re
import datetime
import ctypes  # För Windows-notifikation

# URLs for API endpoints
search_url = "https://www.pricerunner.se/se/api/search-compare-gateway/public/search/v5/SE?q={EAN}"
product_detail_url = "https://www.pricerunner.se/se/api/search-compare-gateway/public/product-detail/v0/offers/SE/{ID}?af_ORIGIN=NATIONAL&af_ITEM_CONDITION=NEW,UNKNOWN&sortByPreset=PRICE"

# Headers for requests
headers = {
    "accept": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
}

# Basic colors in Swedish and English
swedish_colors = {
    "Röd", "Ljusröd", "Mörkröd", "Blå", "Ljusblå", "Mörkblå", "Gul", "Ljusgul", "Mörkgul",
    "Grön", "Ljusgrön", "Mörkgrön", "Orange", "Ljusorange", "Mörkorange", "Lila", "Ljuslila",
    "Mörklila", "Rosa", "Ljusrosa", "Mörkrosa", "Brun", "Ljusbrun", "Mörkbrun", "Svart",
    "Vit", "Grå", "Ljusgrå", "Mörkgrå", "Turkos", "Ljusturkos", "Mörkturkos", "Cyan",
    "Ljuscyan", "Mörkcyan", "Magenta", "Ljusmagenta", "Mörkmagenta", "Indigo", "Ljusindigo",
    "Mörkindigo", "Violett", "Ljusviolett", "Mörkviolett", "Guld", "Silver", "Beige", "Ockra"
}

def fetch_product_id(ean):
    """Fetch product ID from EAN."""
    response = requests.get(search_url.format(EAN=ean), headers=headers)
    if response.status_code == 200:
        data = response.json()
        products = data.get("products", [])
        if products:
            return products[0]["id"]  # Return the first product ID found
    else:
        print(f"Failed to retrieve product ID for EAN: {ean}. Status code: {response.status_code}")
    return None

def fetch_price_and_merchant_info(product_id, expected_color=None):
    """Fetch unique offers (price, merchant, color, offer ID) for a given product ID."""
    url = product_detail_url.format(ID=product_id)
    response = requests.get(url, headers=headers)
    offers_list = []

    if response.status_code == 200:
        data = response.json()
        offers = data.get("offers", [])
        if offers:
            for offer in offers:
                if offer.get("availability") == "AVAILABLE" and offer.get("stockStatus") == "IN_STOCK":
                    price = float(offer["price"]["amount"])
                    merchant_name = data["merchants"].get(str(offer["merchantId"]), {}).get("name", "Unknown Merchant")
                    offer_id = offer.get("id", "No Offer ID")

                    color = "Not Sure"  # Default if color is not detected
                    if expected_color and expected_color.lower() in offer.get("name", "").lower():
                        color = expected_color

                    offers_list.append({
                        "price": int(price) if price.is_integer() else price,
                        "merchantName": merchant_name,
                        "color": color,
                        "offer_id": offer_id
                    })
    return offers_list

def show_notification(title, message):
    """Visa en Windows-notifikation."""
    ctypes.windll.user32.MessageBoxW(0, message, title, 0)

def play_sound():
    """Spela ett enkelt ljud."""
    duration = 300  # millisekunder
    freq = 750  # Hz
    os.system(f"echo -en '\007'")

def display_animation():
    """Visa en enkel animation."""
    animation = "|/-\\"
    for i in range(10):
        print(f"\rBearbetar... {animation[i % len(animation)]}", end="")
        time.sleep(0.1)
    print("\rBearbetningen är klar!          ")


def main():
    # Input och output fil
    input_filename = "PriceRunner - Input.csv"
    brand_name = input("Ange varumärkets namn: ").strip()
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Ange sökväg till Downloads-mappen
    downloads_folder = r"C:\Users\vigge\Downloads"
    output_filename = f"{downloads_folder}\\{brand_name} - Output ({current_date}).csv"

    with open(input_filename, mode="r", encoding="utf-8") as infile, open(output_filename, mode="w", newline="",
                                                                          encoding="utf-8") as csvfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["BrandName", "Sell Price", "Color", "Offer ID"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            ean = row["EAN"]
            product_id = fetch_product_id(ean)

            if product_id:
                offers = fetch_price_and_merchant_info(product_id)
                if offers:
                    for offer in offers:
                        row.update({
                            "BrandName": offer["merchantName"],
                            "Sell Price": offer["price"],
                            "Color": offer["color"],
                            "Offer ID": offer["offer_id"]
                        })
                        writer.writerow(row)
                else:
                    row.update({"BrandName": "No Product Found"})
                    writer.writerow(row)
            else:
                row.update({"BrandName": "No Product Found"})
                writer.writerow(row)

    print(f"Output sparades i: {output_filename}")

    # Animation, ljud och notifikation
    display_animation()
    play_sound()
    show_notification("Skriptet är klart", f"Output sparades i: {output_filename}")

    # Git automation
    print("Pushing changes to GitHub...")
    os.system('git add .')
    os.system(f'git commit -m "Automatisk commit från {brand_name} script run"')
    os.system('git push origin main')
    print("Ändringar pushades framgångsrikt till GitHub!")


if __name__ == "__main__":
    main()
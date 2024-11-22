import os  # För Git-kommandon och ljud
import requests
import csv
import time
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

color_translation = {
    "Red": "Röd", "Light Red": "Ljusröd", "Dark Red": "Mörkröd",
    "Blue": "Blå", "Light Blue": "Ljusblå", "Dark Blue": "Mörkblå",
    "Yellow": "Gul", "Light Yellow": "Ljusgul", "Dark Yellow": "Mörkgul",
    "Green": "Grön", "Light Green": "Ljusgrön", "Dark Green": "Mörkgrön",
    "Orange": "Orange", "Light Orange": "Ljusorange", "Dark Orange": "Mörkorange",
    "Purple": "Lila", "Light Purple": "Ljuslila", "Dark Purple": "Mörklila",
    "Pink": "Rosa", "Light Pink": "Ljusrosa", "Dark Pink": "Mörkrosa",
    "Brown": "Brun", "Light Brown": "Ljusbrun", "Dark Brown": "Mörkbrun",
    "Black": "Svart", "White": "Vit", "Gray": "Grå", "Light Gray": "Ljusgrå",
    "Dark Gray": "Mörkgrå", "Turquoise": "Turkos", "Light Turquoise": "Ljusturkos",
    "Dark Turquoise": "Mörkturkos"
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

def detect_color_from_name(product_name, expected_color=None):
    """Detect color based on expected color or by checking against basic colors."""
    if expected_color and re.search(rf"\b{re.escape(expected_color.lower())}\b", product_name.lower()):
        return expected_color

    for color in swedish_colors.union(color_translation.keys()):
        if re.search(rf"\b{color.lower()}\b", product_name.lower()):
            return color_translation.get(color, color)
    return "Not Sure"

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

                    color = None
                    for label in offer.get("labels", {}).get("attributeLabels", []):
                        if label["name"].lower() == "färg":
                            if expected_color is None or label["value"].lower() == expected_color.lower():
                                color = label["value"]
                                break

                    if not color:
                        color = detect_color_from_name(offer["name"], expected_color)

                    offers_list.append({
                        "price": int(price) if price.is_integer() else price,
                        "merchantName": merchant_name,
                        "color": color or "Not Sure",
                        "offer_id": offer_id
                    })
    else:
        print(f"Failed to retrieve details for Product ID {product_id}. Status code: {response.status_code}")

    return offers_list

def main():
    downloads_folder = r"C:\Users\vigge\Downloads"
    input_filename = "PriceRunner - Input.csv"
    brand_name = input("Ange varumärkets namn: ").strip()
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    output_filename = f"{downloads_folder}\\{brand_name} - Output ({current_date}).csv"

    with open(input_filename, mode="r", encoding="utf-8") as infile, open(output_filename, mode="w", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["BrandName", "Sell Price", "Color", "Offer ID"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            ean = row["EAN"]
            expected_color = row.get("Brand Color")
            print(f"Fetching offers for EAN: {ean} with expected color: {expected_color}")
            product_id = fetch_product_id(ean)

            if product_id:
                offers = fetch_price_and_merchant_info(product_id, expected_color)
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
                    row.update({
                        "BrandName": "No Product Found",
                        "Sell Price": "",
                        "Color": "Not Sure",
                        "Offer ID": "No Offer ID"
                    })
                    writer.writerow(row)
            else:
                row.update({
                    "BrandName": "No Product Found",
                    "Sell Price": "",
                    "Color": "Not Sure",
                    "Offer ID": "No Offer ID"
                })
                writer.writerow(row)

            time.sleep(random.randint(1, 6))

    print(f"Bearbetningen är klar. Output sparades i: {output_filename}")

    # Ljud och notifikation
    ctypes.windll.user32.MessageBoxW(0, f"Output sparades i: {output_filename}", "Skriptet är klart!", 1)

    # Git automation
    print("Pushing changes to GitHub...")
    os.system('git add .')
    os.system(f'git commit -m "Automatisk commit från {brand_name} script run"')
    os.system('git push origin main')
    print("Ändringar pushades framgångsrikt till GitHub!")

if __name__ == "__main__":
    main()
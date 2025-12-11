"""
Name:       Group 4 – Kevin Tom, Randy Estrin, Jinhua Yan
URL:         [Link to your Streamlit Cloud app, if deployed]
Description: This program sends HTTP requests to Wikipedia, parses the "List of cocktails" page and builds a structured cocktail dataset. Each row represents a cocktail with its name, Wikipedia URL, category (section/base spirit), and selected infobox fields. The resulting cleaned dataset is used in our Streamlit py file for further queries, analysis, and visualizations

"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import re

USER_AGENT = '(Educational Cocktail Scraper v1.0)'
BASE_URL = 'https://en.wikipedia.org'
TARGET_URL = f'{BASE_URL}/wiki/List_of_cocktails'

HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

def scrape_by_category():
    response = requests.get(TARGET_URL, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    categories = {}
# See section 1 of Web Scraping AI usage
    content = soup.find('div', {'class': 'mw-parser-output'})
    if not content:
        content = soup.find('div', {'id': 'mw-content-text'})
    if not content:
        print("Error: Could not find main content area")
        return categories
    skip_sections = ['See also', 'References', 'External links',
                    'Navigation menu', 'Notes', 'Further reading',
                    'Bibliography', 'Contents']
    current_category = None
    processing_stopped = False
    all_elements = content.find_all(['h2', 'h3', 'ul'])

    for element in all_elements:
        if processing_stopped:
            break
        if element.name in ['h2', 'h3']:
            category_name = None
            headline = element.find('span', {'class': 'mw-headline'})
            if headline:
                category_name = headline.get_text(strip=True)
            if not category_name:
                span_with_id = element.find('span', id=True)
                if span_with_id:
                    category_name = span_with_id.get_text(strip=True)
            if not category_name:
                category_name = element.get_text(strip=True)
                if '[edit]' in category_name:
                    category_name = category_name.replace('[edit]', '').strip()
            if category_name in skip_sections:
                processing_stopped = True
                break
            if not category_name:
                continue
            current_category = category_name
            if current_category not in categories:
                categories[current_category] = []

        elif element.name == 'ul' and current_category and not processing_stopped:
            for li in element.find_all('li', recursive=False):
                link = li.find('a', href=True)
                if link:
                    name = link.get_text(strip=True) #get_text will extract all the text content within a tag
                    href = link.get('href', '')
                    if (href.startswith('/wiki/') and
                        ':' not in href and
                        'action=edit' not in href):
                        cocktail = {
                            'name': name,
                            'url': f"{BASE_URL}{href}"
                        }
                        if cocktail not in categories[current_category]:
                            categories[current_category].append(cocktail)

    categories = {k: v for k, v in categories.items() if v}

    return categories

def scrape_cocktail_infobox(url):
#scrapes each cocktail URL for the infobox text
#[PY3]
    try:
        time.sleep(0.5)
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        infobox = soup.find('table', {'class': 'infobox hrecipe hproduct'})
        if not infobox:
            infobox = soup.find('table', {'class': 'infobox'})
        if not infobox:
            return None
        target_fields = {
            'base spirit': 'Base spirit',
            'primary alcohol': 'Base spirit',
            'primary alcohol by volume': 'Base spirit',
            'ingredients': 'Ingredients',
            'preparation': 'Preparation',
            'served': 'Served',
            'standard drinkware': 'Standard drinkware',
            'drinkware': 'Standard drinkware',
            'standard garnish': 'Standard garnish',
            'garnish': 'Standard garnish',
            'type': 'Type'
        }

        infobox_data = {}
        rows = infobox.find_all('tr')
        for row in rows:
            header = row.find('th')
            data = row.find('td')
            if header and data:
                try:
                    key = header.get_text(strip=True).lower()
                    if key in ['ingredients']:
                        list_items = data.find_all('li')
                        if list_items:
                            ingredient_list = []
                            seen_ingredients = set()
                            for li in list_items:
                                try:
                                    parts = []
                                    for element in li.descendants:
                                        if isinstance(element, str):
                                            text = element.strip()
                                            if text:
                                                parts.append(text)
                                        elif element.name == 'a':
                                            link_text = element.get_text(strip=True)
                                            if link_text:
                                                parts.append(link_text)
                                    item_text = ' '.join(parts) #[DA1] #See section 2 of Web Scraping AI usage
                                    item_text = item_text.replace('\xa0', ' ')
                                    item_text = item_text.replace('\u00a0', ' ')
                                    item_text = item_text.replace('\n', ' ')
                                    item_text = item_text.replace('\r', ' ')
                                    item_text = re.sub(r'\s+', ' ', item_text).strip()
                                    item_text = re.sub(r'\.\w+\s*\{[^}]*\}', '', item_text)
                                    item_text = re.sub(r'\{[^}]*\}', '', item_text)
                                    item_text = re.sub(r'\(\s*\.[a-zA-Z-]+[^)]*\)', '', item_text)
                                    item_text = re.sub(r'\.mw-parser-output[^\s]*', '', item_text)
                                    item_text = re.sub(r'\(\s*\.mw-parser-output\s*[^)]*\)', '', item_text)
                                    item_text = re.sub(r'\.(frac|num|den|sr-only)(\s+\.\w+)*[^a-zA-Z0-9]', ' ',item_text)
                                    item_text = re.sub(r'[a-z-]+:[^;}\s]+[;\s]', '', item_text)
                                    item_text = re.sub(r'\s+\.\w+', '', item_text)
                                    item_text = re.sub(r'\s+', ' ', item_text).strip()
                                    words = item_text.split()
                                    deduped_words = []
                                    prev_word = None
                                    for word in words:
                                        if word.lower() != prev_word:
                                            deduped_words.append(word)
                                            prev_word = word.lower()
                                    item_text = ' '.join(deduped_words)
                                    item_text = re.sub(r'\bml\b', 'mL', item_text, flags=re.IGNORECASE)
                                    item_text = re.sub(r'\bOZ\b', 'oz', item_text)
                                    item_text = re.sub(r'\bcl\b', 'cL', item_text, flags=re.IGNORECASE)
                                    item_text_lower = item_text.lower()
                                    if item_text and item_text_lower not in seen_ingredients:
                                        ingredient_list.append(item_text)
                                        seen_ingredients.add(item_text_lower)
                                except Exception as e:
                                    print(f"Could not process ingredient item in {url}")
                                    continue
                            value = ' '.join(ingredient_list)
                        else:
                            value = data.get_text(strip=True)
                            value = value.replace('\xa0', ' ')
                            value = value.replace('\u00a0', ' ')
                            value = value.replace('\n', ' ')
                            value = value.replace('\r', ' ')
                            value = re.sub(r'\s+', ' ', value).strip()
                            value = re.sub(r'\.mw-parser-output[^\s]*', '', value).strip()
                            value = re.sub(r'\(\s*\.mw-parser-output\s*[^)]*\)', '', value).strip()
                            value = re.sub(r'\bml\b', 'mL', value, flags=re.IGNORECASE)
                            value = re.sub(r'\bOZ\b', 'oz', value)
                            value = re.sub(r'\bcl\b', 'cL', value, flags=re.IGNORECASE)
                    else:
                        value = data.get_text(strip=True)
                        value = value.replace('\xa0', ' ')
                        value = value.replace('\u00a0', ' ')
                        value = value.replace('\n', ' ')
                        value = value.replace('\r', ' ')
                        value = re.sub(r'\s+', ' ', value).strip()
                    if key in target_fields:
                        normalized_key = target_fields[key]
                        if normalized_key not in infobox_data:
                            infobox_data[normalized_key] = value

                except Exception as e:
                    print(f"Could not process field in {url}: {str(e)}")
                    continue

        image_url = None
        infobox_image = infobox.find('td', {'class': 'infobox-image'})
        if infobox_image:
            img_tag = infobox_image.find('img')
            if img_tag and img_tag.get('src'):
                image_src = img_tag.get('src')
                if image_src.startswith('//'):
                    image_url = 'https:' + image_src
                elif image_src.startswith('/'):
                    image_url = BASE_URL + image_src
                else:
                    image_url = image_src

        infobox_data['Image URL'] = image_url if image_url else ''

        return infobox_data if infobox_data else None

    except Exception as e:

        print(f"Error scraping {url}: {str(e)}")
        return None


def scrape_categorized_cocktails_with_details():
#Scrape by category first then scrape the infobox
    categorized = scrape_by_category()
    total_cocktails = sum(len(drinks) for drinks in categorized.values())
    detailed_categories = {}
    overall_count = 0

    for category, cocktails in categorized.items(): #[PY5]
        print(f"\nCategory: {category} ({len(cocktails)} cocktails)")
        detailed_categories[category] = []

        for cocktail in cocktails:
            overall_count += 1
            print(f"  [{overall_count}/{total_cocktails}] {cocktail['name']}")

            infobox_data = scrape_cocktail_infobox(cocktail['url'])

            detailed_cocktail = {
                'name': cocktail['name'],
                'url': cocktail['url'],
                'infobox': infobox_data
            }

            detailed_categories[category].append(detailed_cocktail)

    return detailed_categories

def save_detailed_categorized_to_csv(categorized, filename='cocktails_categorized_detailed_test_final.csv'):
#See section 3 of Web Scraping AI usage
    fieldnames = ['category', 'name', 'url', 'Image URL', 'Type', 'Base spirit', 'Ingredients',
                  'Preparation', 'Served', 'Standard drinkware', 'Standard garnish']

    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for category, cocktails in categorized.items():
            for cocktail in cocktails:
                row = {
                    'category': category,
                    'name': cocktail['name'],
                    'url': cocktail['url'],
                    'Image URL': '',
                    'Type': '',
                    'Base spirit': '',
                    'Ingredients': '',
                    'Preparation': '',
                    'Served': '',
                    'Standard drinkware': '',
                    'Standard garnish': ''
                }

                if cocktail.get('infobox'):
                    for key, value in cocktail['infobox'].items():
                        if key in fieldnames:
                            row[key] = value

                writer.writerow(row)




def main():
    print("=" * 80)
    print("WIKIPEDIA COCKTAILS WEB SCRAPER")
    print("=" * 80)
    print(f"Target URL: {TARGET_URL}")

    try:
        print("=" * 80)
        detailed_categories = scrape_categorized_cocktails_with_details()
        save_detailed_categorized_to_csv(detailed_categories)

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"\nError: {str(e)}")
        raise

main()
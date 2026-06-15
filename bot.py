import os
import sys
import base64
import json
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

VISION_MODELS = [
    "llama-3.2-11b-vision-preview"
]

MATH_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]

def get_image_base64(page, img_element):
    try:
        # Robimy screenshot elementu, co omija problemy z canvasem i autoryzacją
        img_element.scroll_into_view_if_needed()
        img_bytes = img_element.screenshot()
        return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        print(f"Błąd podczas pobierania obrazka: {e}")
        return None

def call_openrouter_vision(base64_image):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    for model in VISION_MODELS:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Opisz dokładnie ten obrazek matematyczny na potrzeby rozwiązania zadania. Zwróć szczególną uwagę na wzory, liczby, wykresy."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        }
        try:
            print(f"Próbuję model Vision: {model}...")
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'error' in data:
                    print(f"Błąd modelu {model}: {data['error']}")
                    continue
                return data['choices'][0]['message']['content']
            else:
                print(f"Błąd HTTP dla {model}: {response.text}")
        except Exception as e:
            print(f"Wyjątek dla {model}: {e}")
            
    return ""

def call_openrouter_math(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    schema = {
        "type": "object",
        "properties": {
            "answer_type": {
                "type": "string",
                "enum": ["radio", "checkbox", "text", "select"],
                "description": "Typ odpowiedzi."
            },
            "selected_options": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lista tekstów wyznaczających poprawne opcje (dla radio tylko 1 element, dla checkbox wiele)."
            },
            "text_answer": {
                "type": "string",
                "description": "Dokładna odpowiedź do wpisania w polu tekstowym."
            }
        },
        "required": ["answer_type"]
    }
    
    for model in MATH_MODELS:
        payload = {
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "Jesteś ekspertem z matematyki. Udziel precyzyjnej odpowiedzi. MUSISZ zwrócić dane wyłącznie w formacie JSON zawierającym klucze z tego schematu:\n" + json.dumps(schema)
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        try:
            print(f"Próbuję model Math: {model}...")
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'error' in data:
                    print(f"Błąd modelu {model}: {data['error']}")
                    continue
                    
                content = data['choices'][0]['message']['content']
                try:
                    return json.loads(content)
                except Exception as e:
                    print(f"Zwrócono błędny JSON z {model}:", content)
                    continue
            else:
                print(f"Błąd HTTP dla {model}: {response.text}")
        except Exception as e:
            print(f"Wyjątek dla {model}: {e}")
            
    print("Wszystkie modele Math zawiodły.")
    return None

def run_bot():
    if not GROQ_API_KEY or "twoj_klucz" in GROQ_API_KEY:
        print("UZUPEŁNIJ KLUCZ API W PLIKU .env!")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--start-maximized'])
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        
        page.goto("https://moodle2.e-wsb.pl/login/index.php")
        print("Zaloguj się i wejdź do quizu.")
        
        while True:
            cmd = input("\nWciśnij [Enter] aby rozwiązać stronę, lub 'q' aby wyjść: ")
            if cmd.lower() == 'q':
                break
                
            print("Analizuję stronę...")
            questions = page.locator(".que")
            count = questions.count()
            if count == 0:
                print("Nie znaleziono pytania (.que). Czy jesteś w quizie?")
                continue
                
            for i in range(count):
                q_container = questions.nth(i)
                
                # Tekst pytania
                q_text_el = q_container.locator(".qtext")
                q_text = q_text_el.inner_text() if q_text_el.count() > 0 else ""
                
                # Obrazki
                images = q_text_el.locator("img")
                img_desc_list = []
                for j in range(images.count()):
                    img = images.nth(j)
                    b64 = get_image_base64(page, img)
                    if b64:
                        print(f"Obrazek {j+1} - Generowanie opisu Vision...")
                        desc = call_openrouter_vision(b64)
                        img_desc_list.append(f"Z obrazka odczytano: {desc}")
                
                # Opcje
                prompt_options = ""
                labels = q_container.locator(".answer label")
                if labels.count() > 0:
                    for j in range(labels.count()):
                        lbl = labels.nth(j)
                        prompt_options += f"- {lbl.inner_text().strip()}\n"
                
                inputs = q_container.locator("input[type='text']")
                has_text = inputs.count() > 0
                
                selects = q_container.locator("select")
                if selects.count() > 0:
                    for j in range(selects.count()):
                        opts = selects.nth(j).locator("option").all_inner_texts()
                        prompt_options += f"Wybór z listy: {', '.join(opts)}\n"
                
                prompt = f"Treść:\n{q_text}\n"
                if img_desc_list:
                    prompt += "\n".join(img_desc_list) + "\n"
                if prompt_options:
                    prompt += f"\nDostępne opcje:\n{prompt_options}\nZwróć typ 'radio', 'checkbox' lub 'select' w 'answer_type' oraz wybór w 'selected_options'."
                elif has_text:
                    prompt += "\nPytanie otwarte. Zwróć 'answer_type': 'text' i podaj treść do wpisania w 'text_answer'."
                
                print(f"Pytanie {i+1} do modelu...")
                ans = call_openrouter_math(prompt)
                print(f"Otrzymano odpowiedź: {ans}")
                
                if ans:
                    a_type = ans.get("answer_type")
                    if a_type in ["radio", "checkbox"] and ans.get("selected_options"):
                        for opt in ans["selected_options"]:
                            try:
                                loc = q_container.locator("label", has_text=opt).first
                                if loc.count() > 0:
                                    loc.click()
                                    print(f"Zaznaczono opcję zawierającą: {opt}")
                                else:
                                    print(f"Nie znaleziono opcji: {opt}")
                            except Exception as e:
                                print("Błąd kliknięcia:", e)
                                
                    elif a_type == "select" and ans.get("selected_options"):
                        if selects.count() > 0:
                            opt = ans["selected_options"][0]
                            selects.first.select_option(label=opt)
                            print(f"Wybrano z listy: {opt}")
                            
                    elif a_type == "text" and ans.get("text_answer"):
                        if inputs.count() > 0:
                            inputs.first.fill(ans["text_answer"])
                            print(f"Wpisano tekst: {ans['text_answer']}")
            
            # Nawigacja
            next_btn = page.locator("input#mod_quiz-next-nav[value*='Następna']")
            end_btn = page.locator("input#mod_quiz-next-nav[value*='Zapisz podejście']")
            
            if next_btn.count() > 0:
                print("Przechodzę do następnej strony...")
                next_btn.click()
            elif end_btn.count() > 0:
                print("Quiz zakończony (pojawiło się 'Zapisz podejście'). Czekam w trybie oczekiwania na nowe polecenia.")
            else:
                print("Brak przycisku nawigacji.")

if __name__ == "__main__":
    run_bot()

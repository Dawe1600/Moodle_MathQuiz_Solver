import os
import sys
import base64
import json
import time
import msvcrt
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MATH_MODELS = [
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite"    
]

VISION_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3-flash"
]

def check_escape(raise_exc=False):
    escaped = False
    while msvcrt.kbhit():
        key = msvcrt.getch()
        if key == b'\x1b':
            escaped = True
    if escaped and raise_exc:
        raise InterruptedError("Przerwano przez klawisz ESC")
    return escaped

def get_image_base64(page, img_element):
    try:
        # Robimy screenshot elementu, co omija problemy z canvasem i autoryzacją
        img_element.scroll_into_view_if_needed()
        img_bytes = img_element.screenshot()
        return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        print(f"Błąd podczas pobierania obrazka: {e}")
        return None

def call_gemini_vision(base64_image):
    if not GEMINI_API_KEY or "twoj_klucz" in GEMINI_API_KEY:
        print("Brak klucza GEMINI_API_KEY. Nie można opisać obrazka.")
        return ""
        
    for model in VISION_MODELS:
        check_escape(True)
        try:
            print(f"Próbuję model Vision: {model} (Google AI Studio)...")
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(
                        data=base64.b64decode(base64_image),
                        mime_type='image/png',
                    ),
                    "Opisz dokładnie ten obrazek matematyczny na potrzeby rozwiązania zadania. Zwróć szczególną uwagę na wzory, liczby, wykresy."
                ]
            )
            return response.text
        except Exception as e:
            print(f"Wyjątek modelu Gemini ({model}): {e}")
            continue
    return ""

def call_gemini_math(prompt):
    if not GEMINI_API_KEY or "twoj_klucz" in GEMINI_API_KEY:
        print("Brak klucza GEMINI_API_KEY. Nie można rozwiązać matematyki.")
        return None
        
    schema = {
        "type": "object",
        "properties": {
            "answer_type": {
                "type": "string",
                "enum": ["radio", "checkbox", "text", "select"],
                "description": "Typ odpowiedzi."
            },
            "selected_indices": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Lista numerów indeksów (ID) poprawnych opcji z listy Dostępnych opcji (np. [0], [1, 2]). Używaj tylko dla radio/checkbox."
            },
            "selected_options": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lista tekstów wyznaczających poprawne opcje dla pytań typu select."
            },
            "text_answer": {
                "type": "string",
                "description": "Dokładna odpowiedź do wpisania w polu tekstowym."
            }
        },
        "required": ["answer_type"]
    }
    
    full_prompt = "Jesteś ekspertem z matematyki. Udziel precyzyjnej odpowiedzi. MUSISZ zwrócić dane wyłącznie w formacie JSON zawierającym klucze z tego schematu:\n" + json.dumps(schema) + "\n\n" + prompt

    for model in MATH_MODELS:
        check_escape(True)
        try:
            print(f"Próbuję model Math: {model} (Google AI Studio)...")
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            content = response.text
            try:
                return json.loads(content)
            except Exception as e:
                print(f"Zwrócono błędny JSON z {model}:", content)
                continue
        except Exception as e:
            print(f"Wyjątek dla {model}: {e}")
            
    print("Wszystkie modele Math zawiodły.")
    return None

def run_bot():
    if not GEMINI_API_KEY or "twoj_klucz" in GEMINI_API_KEY:
        print("UZUPEŁNIJ KLUCZ GEMINI_API_KEY W PLIKU .env!")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--start-maximized'])
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        
        page.goto("https://moodle2.e-wsb.pl/login/index.php")
        print("Zaloguj się i wejdź do quizu.")
        
        auto_mode = False
        
        while True:
            if not auto_mode:
                cmd = input("\nWciśnij [Enter] aby włączyć tryb AUTO (rozwiązywanie bez przerwy), lub 'q' aby wyjść: ")
                if cmd.lower() == 'q':
                    break
                auto_mode = True
                
            try:
                check_escape(True)
                print("Analizuję stronę... (wciśnij klawisz ESC w oknie terminala, aby natychmiast przerwać!)")
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
                            desc = call_gemini_vision(b64)
                            img_desc_list.append(f"Z obrazka odczytano: {desc}")
                    
                    # Opcje
                    prompt_options = ""
                    labels_elements = []
                    labels = q_container.locator(".answer [data-region='answer-label'], .answer label")
                    if labels.count() > 0:
                        for j in range(labels.count()):
                            lbl = labels.nth(j)
                            labels_elements.append(lbl)
                            
                            lbl_text = lbl.inner_text().strip()
                            
                            lbl_imgs = lbl.locator("img")
                            img_texts = []
                            if lbl_imgs.count() > 0:
                                for k in range(lbl_imgs.count()):
                                    b64 = get_image_base64(page, lbl_imgs.nth(k))
                                    if b64:
                                        print(f"Opcja {j} zawiera obrazek - Generowanie opisu Vision...")
                                        desc = call_gemini_vision(b64)
                                        img_texts.append(f"[Obrazek: {desc}]")
                                        
                            combined_text = lbl_text + " " + " ".join(img_texts)
                            prompt_options += f"Opcja {j}: {combined_text.strip()}\n"
                    
                    inputs = q_container.locator("input:not([type='hidden']):not([type='radio']):not([type='checkbox']):not([type='submit']):not([type='button'])")
                    has_text = inputs.count() > 0
                    
                    checkboxes = q_container.locator("input[type='checkbox']")
                    is_multiple = checkboxes.count() > 0
                    
                    selects = q_container.locator("select")
                    if selects.count() > 0:
                        for j in range(selects.count()):
                            opts = selects.nth(j).locator("option").all_inner_texts()
                            prompt_options += f"Wybór z listy: {', '.join(opts)}\n"
                    
                    prompt = f"Treść:\n{q_text}\n"
                    if img_desc_list:
                        prompt += "\n".join(img_desc_list) + "\n"
                    if prompt_options:
                        prompt += f"\nDostępne opcje:\n{prompt_options}\nZwróć typ 'radio', 'checkbox' w 'answer_type' oraz wybór w 'selected_indices' (jako tablica liczb np. [0] lub [1, 3]). Dla typu 'select' zwróć listę stringów w 'selected_options'."
                        if is_multiple:
                            prompt += "\nUWAGA: To jest pytanie WIELOKROTNEGO WYBORU (checkbox). Przeanalizuj uważnie wszystkie warianty i zwróć w tablicy 'selected_indices' wszystkie poprawne opcje (np. [0, 2]). Pamiętaj jednak, że poprawna może okazać się też tylko JEDNA odpowiedź (np. [1]) - zaznacz tylko to, co jest bezwzględnie prawdziwe."
                    elif has_text:
                        prompt += "\nPytanie otwarte. Zwróć 'answer_type': 'text' i podaj treść do wpisania w 'text_answer'."
                    
                    print(f"Pytanie {i+1} do modelu...")
                    ans = call_gemini_math(prompt)
                    print(f"Otrzymano odpowiedź: {ans}")
                    
                    if ans:
                        a_type = ans.get("answer_type")
                        if a_type in ["radio", "checkbox"] and ans.get("selected_indices") is not None:
                            for idx in ans["selected_indices"]:
                                try:
                                    if 0 <= idx < len(labels_elements):
                                        labels_elements[idx].click()
                                        print(f"Zaznaczono opcję {idx}")
                                    else:
                                        print(f"Błąd: Model zwrócił nieprawidłowy indeks opcji: {idx}")
                                except Exception as e:
                                    print(f"Błąd kliknięcia opcji {idx}: {e}")
                                    
                        elif a_type == "select" and ans.get("selected_options"):
                            if selects.count() > 0:
                                opt = ans["selected_options"][0]
                                selects.first.select_option(label=opt)
                                print(f"Wybrano z listy: {opt}")
                                
                        elif a_type == "text" and ans.get("text_answer"):
                            if inputs.count() > 0:
                                inputs.first.fill(str(ans["text_answer"]))
                                print(f"Wpisano tekst: {ans['text_answer']}")
                            else:
                                print(f"UWAGA: Model wygenerował odpowiedź tekstową ({ans['text_answer']}), ale na stronie nie znaleziono żadnego pola do wpisania tekstu!")
                
                
                    check_escape(True)
                    # Nawigacja
                    next_btn = page.locator("input#mod_quiz-next-nav[value*='Następna']")
                    end_btn = page.locator("input#mod_quiz-next-nav[value*='Zapisz podejście']")
                    
                    if next_btn.count() > 0:
                        print("Przechodzę do następnej strony...")
                        next_btn.click()
                        time.sleep(1) # Zabezpieczenie przed zbyt szybkim wczytywaniem
                    elif end_btn.count() > 0:
                        print("Quiz zakończony (pojawiło się 'Zapisz podejście'). Przechodzę w tryb oczekiwania.")
                        auto_mode = False
                    else:
                        print("Brak przycisku nawigacji. Zatrzymuję tryb AUTO.")
                        auto_mode = False
                        
            except InterruptedError as e:
                print(f"\n[!] {e}. Zatrzymano tryb AUTO. Wracam do oczekiwania na klawisz Enter.")
                auto_mode = False
                continue

if __name__ == "__main__":
    run_bot()

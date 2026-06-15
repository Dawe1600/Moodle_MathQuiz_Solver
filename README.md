# Moodle MathQuiz Solver

Ten projekt to Twój prywatny asystent AI, który pomaga w automatycznym rozwiązywaniu quizów matematycznych na platformie Moodle. Skrypt korzysta z biblioteki **Playwright** do nawigowania po stronie, a jako głównego mózgu używa najnowocześniejszych modeli tekstowych i wizyjnych z **Google AI Studio**.

## Cechy projektu
- **Pełna automatyzacja:** Bot sam czyta treść, zaznacza odpowiedzi (pojedynczego oraz wielokrotnego wyboru) i wpisuje tekst w puste pola.
- **W 100% za darmo:** Cały system opiera się na dostępie do darmowych modeli (free tier) w Google AI Studio, dzięki czemu korzystanie z bota nie kosztuje Cię ani grosza.
- **Analiza obrazków:** Masz na teście skomplikowany wykres albo wzór w formie zdjęcia? Skrypt prześle je do modeli Vision, które przeanalizują układ graficzny i "odczytają" zadanie.
- **Zaawansowana Matematyka:** Po zebraniu danych z ekranu, trafiają one do inteligentnych modeli matematycznych, które zajmują się rozwiązywaniem obliczeń.
- **Zawsze pod Twoją kontrolą:** W każdej ułamku sekundy podczas pracy skryptu możesz po prostu nacisnąć klawisz **ESC** w swoim terminalu. Bot momentalnie wstrzyma tryb automatyczny, dzięki czemu unikniesz jakichkolwiek problemów.

## Obsługiwane typy pytań
Bot bez problemu radzi sobie z najpopularniejszymi formatami testów na platformie Moodle:
- **Jednokrotnego wyboru** (Pola typu Radio)
- **Wielokrotnego wyboru** (Checkboxy - bot z automatu wie, żeby szukać wielu poprawnych odpowiedzi)
- **Pytania otwarte** (Wpisywanie obliczonego wyniku do pustego pola tekstowego)
- **Dopasowanie** (Zaawansowana obsługa wielu list rozwijanych `select` jednocześnie, wraz z analizowaniem zdjęć przypisanych do poszczególnych wierszy!)

## Pobranie projektu

Aby zacząć, po prostu skopiuj ten projekt na swój dysk za pomocą programu git i wejdź do nowo utworzonego folderu:
```bash
git clone https://github.com/Dawe1600/Moodle_MathQuiz_Solver.git
cd Moodle_MathQuiz_Solver
```

## Szybka instalacja (Automatycznie)

Dla ułatwienia instalacji przygotowane zostały automatyczne skrypty przygotowujące środowisko. Wystarczy je uruchomić w głównym folderze:

- **Windows:** Dwukliknij na plik `setup.bat` lub uruchom go w terminalu:
  ```cmd
  .\setup.bat
  ```

- **Linux/macOS:** Nadaj skryptowi uprawnienia do wykonania i uruchom go w terminalu:
  ```bash
  chmod +x setup.sh
  ./setup.sh
  ```

## Ręczna instalacja

Jeżeli preferujesz ręczną instalację krok po kroku:
1. Zainstaluj wirtualne środowisko (venv): `python -m venv venv`
2. Aktywuj środowisko: 
   - Windows: `.\venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
3. Zainstaluj biblioteki: `pip install -r requirements.txt`
4. Zainstaluj przeglądarki dla Playwright: `playwright install`

## Konfiguracja API

Zanim włączysz bota, powinieneś posiadać klucz API od Google AI Studio. 
1. Utwórz kopię pliku `.env.example` w tym samym folderze i nazwij ją **`.env`**.
2. Wklej do niej swój klucz w miejsce `twoj_klucz_z_google_ai_studio`:
   ```env
   GEMINI_API_KEY=tu_wklej_swoj_klucz
   ```

## Użycie Bota

1. Aktywuj środowisko wirtualne (jeśli terminal został wyłączony).
2. Wpisz w terminalu polecenie uruchamiające bota:
   ```bash
   python bot.py
   ```
3. Otworzy się przeglądarka Chromium. **Zaloguj się na Moodle i wejdź do wybranego Quizu**, bezpośrednio na stronę z pierwszym pytaniem.
4. W terminalu naciśnij klawisz `ENTER`, aby przejść w Tryb Automatyczny (AUTO).
5. Bot samodzielnie będzie odpowiadał na pytania, przeskakiwał na następne strony i przetwarzał całą platformę, aż do momentu trafienia na "Zapisz podejście".

### Przerywanie Bota (Klawisz ESC)
- W dowolnym ułamku sekundy, przebywając w oknie terminala, możesz wcisnąć klawisz **ESC**. 
- Zabezpiecza to przed np. dziwnymi zachowaniami platformy Moodle. 
- Tryb automatyczny natychmiastowo zostanie wyłączony dla następnych akcji - bot poczeka na Twój "Enter" zanim wyśle kolejne zapytanie lub przejdzie na nową stronę.

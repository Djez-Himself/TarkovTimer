import time
import os
import json
from datetime import datetime, timedelta, timezone
import tkinter as tk
from tkinter import ttk
import threading
from PIL import Image, ImageTk
import io
import logging
import sys
import requests
import pytz
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
try:
    import pygame
    pygame.mixer.init()
except ImportError:
    pygame = None
try:
    import winsound
except ImportError:
    winsound = None

# Définition des chemins
BASE_DIR = os.path.dirname(__file__)
IMG_DIR = os.path.join(BASE_DIR, 'img')
SONS_DIR = os.path.join(BASE_DIR, 'sons')
SELECTION_FILE = os.path.join(BASE_DIR, 'selection.json')
LOG_FILE = os.path.join(BASE_DIR, 'app.log')
ALERT_10MIN_SOUND = os.path.join(SONS_DIR, 'Yeet-sound-effect.mp3')
RESET_SOUND = os.path.join(SONS_DIR, 'Toilet-flushing.mp3')

# Nettoyage du fichier de log au démarrage
if os.path.exists(LOG_FILE):
    try:
        os.remove(LOG_FILE)
    except Exception as e:
        print(f"Erreur lors du nettoyage du fichier log: {e}")

# Configuration du logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Log du démarrage
logging.info("Démarrage de l'application")

# URLs pour le scraping
URL_PVP = "https://tarkovbot.eu/tools/trader-resets/gettimes"
URL_PVE = "https://tarkovbot.eu/tools/pve/trader-resets/gettimes"

# Headers pour le scraping
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Origin': 'https://tarkovbot.eu',
    'Referer': 'https://tarkovbot.eu/tools/trader-resets',
    'Connection': 'keep-alive'
}

# Mapping des noms de traders
TRADER_MAPPING = {
    "prapor": "Prapor",
    "thérapute": "Therapist",
    "skier": "Skier",
    "pissekeeper": "Peacekeeper",
    "mechanic": "Mechanic",
    "ragman": "Ragman",
    "jaeger": "Jaeger",
    "fence": "Fence",
    "ref": "Lightkeeper"
}

TRADER_COLORS = {
    "prapor": "#4a90e2",
    "thérapute": "#50e3c2",
    "pissekeeper": "#f5a623",
    "skier": "#00ffff",
    "fence": "#95a5a6",
    "ragman": "#9b59b6",
    "jaeger": "#e74c3c",
    "ref": "#e1e1e1",
    "mechanic": "#f39c12"
}

def format_time_remaining(time_remaining):
    # Convertir en total de secondes pour faciliter la comparaison
    total_seconds = time_remaining.days * 86400 + time_remaining.hours * 3600 + time_remaining.minutes * 60 + time_remaining.seconds
    
    if total_seconds < 0:
        return "Reset en cours..."
    
    hours = time_remaining.hours
    minutes = time_remaining.minutes
    seconds = time_remaining.seconds
    
    if hours > 0:
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
    elif minutes > 0:
        return f"{minutes:02d}m {seconds:02d}s"
    else:
        return f"{seconds:02d}s"

def play_sound(sound_file):
    try:
        if pygame and os.path.exists(sound_file):
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
            logging.info(f"Son joué: {sound_file}")
        elif winsound:
            winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du son {sound_file}: {e}")

class TraderCard:
    def __init__(self, parent, trader_name, color):
        self.frame = tk.Frame(parent, bg="#232323", bd=1, relief="ridge")
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        
        # Conteneur principal pour centrer le contenu
        self.container = tk.Frame(self.frame, bg="#232323")
        self.container.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Avatar avec taille responsive
        self.avatar_label = tk.Label(self.container, bg="#232323")
        self.avatar_label.grid(row=0, column=0, pady=(2,1), sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        
        # Nom du trader
        self.name_label = tk.Label(self.container, text=trader_name, fg=color, bg="#232323", 
                                 font=("Helvetica", 9, "bold"))
        self.name_label.grid(row=1, column=0, sticky="ew")
        
        # Timer
        self.timer_label = tk.Label(self.container, text="", fg="#00ff00", bg="#232323", 
                                  font=("Helvetica", 8))
        self.timer_label.grid(row=2, column=0, sticky="ew", pady=(1,0))
        
        # Heure locale
        self.localtime_label = tk.Label(self.container, text="", fg="#bbbbbb", bg="#232323", 
                                      font=("Helvetica", 7))
        self.localtime_label.grid(row=3, column=0, sticky="ew", pady=(0,2))
        
        self.avatar_img = None
        self.set_avatar_local(trader_name)
        self.reset_notified = False
        self.was_in_reset = False

    def set_avatar_local(self, trader_name):
        local_file = f"{trader_name}.png"
        local_path = os.path.join(IMG_DIR, local_file)
        if os.path.exists(local_path):
            try:
                im = Image.open(local_path).convert("RGBA")
                # Taille de base pour l'avatar
                base_size = 60
                # Calcul de la taille en fonction de la taille de la fenêtre
                window_width = self.frame.winfo_width()
                if window_width > 1:  # Évite la division par zéro
                    size = min(base_size, max(40, window_width // 12))
                else:
                    size = base_size
                im = im.resize((size, size), Image.LANCZOS)
                self.avatar_img = ImageTk.PhotoImage(im)
                self.avatar_label.config(image=self.avatar_img)
                return
            except Exception as e:
                logging.error(f"Erreur chargement image pour {trader_name}: {e}")
        self.avatar_label.config(text="?")

    def set_timer(self, timer_text, local_time_str, time_remaining):
        self.timer_label.config(text=timer_text)
        
        # Convertir en total de secondes
        total_seconds = time_remaining.days * 86400 + time_remaining.hours * 3600 + time_remaining.minutes * 60 + time_remaining.seconds
        
        # Si le timer est négatif (reset en cours)
        if total_seconds < 0:
            self.localtime_label.config(text="")
            # On met le fond en bleu pour indiquer le reset en cours
            self.frame.config(bg="#0066cc")
            self.container.config(bg="#0066cc")
            self.avatar_label.config(bg="#0066cc")
            self.name_label.config(bg="#0066cc")
            self.timer_label.config(bg="#0066cc")
            self.localtime_label.config(bg="#0066cc")
            
            # Jouer le son de reset uniquement quand on entre en reset
            if not self.was_in_reset:
                play_sound(RESET_SOUND)
                self.was_in_reset = True
            return
            
        # Si on sort du reset
        if self.was_in_reset and total_seconds >= 0:
            self.was_in_reset = False
            
        self.localtime_label.config(text=local_time_str)
        
        # Calcul du temps total en minutes pour le seuil des 10 minutes
        total_minutes = time_remaining.hours * 60 + time_remaining.minutes + time_remaining.seconds / 60
        
        # Change la couleur du cadre en fonction du temps restant
        if total_minutes <= 10:
            self.frame.config(bg="#ff3333")  # Rouge pour < 10min
            self.container.config(bg="#ff3333")
            self.avatar_label.config(bg="#ff3333")
            self.name_label.config(bg="#ff3333")
            self.timer_label.config(bg="#ff3333")
            self.localtime_label.config(bg="#ff3333")
        else:
            self.frame.config(bg="#232323")  # Normal pour > 10min
            self.container.config(bg="#232323")
            self.avatar_label.config(bg="#232323")
            self.name_label.config(bg="#232323")
            self.timer_label.config(bg="#232323")
            self.localtime_label.config(bg="#232323")

class TraderGridApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tarkov Trader Timers")
        self.root.configure(bg="#181818")
        self.root.geometry("700x750")
        self.root.minsize(500, 400)
        
        # Initialisation du nombre de colonnes
        self.current_col_count = self.get_col_count()
        
        # Configuration de la grille principale
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self.main_frame = tk.Frame(root, bg="#181818")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)  # La grille des traders prend l'espace restant
        
        title = tk.Label(self.main_frame, text="Trader Restock Timers", fg="white", bg="#181818", 
                        font=("Helvetica", 22, "bold"), anchor="center", justify="center")
        title.grid(row=0, column=0, pady=18)
        
        # Frame pour les boutons
        button_frame = tk.Frame(self.main_frame, bg="#181818")
        button_frame.grid(row=1, column=0, pady=(0, 10))
        
        # Bouton Rafraîchir
        refresh_btn = tk.Button(button_frame, text="Rafraîchir", command=self.manual_refresh, 
                              font=("Helvetica", 11))
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Menu déroulant pour la sélection des traders
        self.trader_menu_btn = tk.Menubutton(button_frame, text="Sélection Traders ▼", 
                                           relief="raised", font=("Helvetica", 11))
        self.trader_menu_btn.pack(side=tk.LEFT, padx=5)
        
        self.trader_menu = tk.Menu(self.trader_menu_btn, tearoff=0)
        self.trader_menu_btn["menu"] = self.trader_menu
        
        self.trader_vars = {}
        self.load_or_init_selection()
        self.create_trader_menu()
        
        self.grid_frame = tk.Frame(self.main_frame, bg="#181818")
        self.grid_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.grid_frame.grid_columnconfigure(0, weight=1)
        self.grid_frame.grid_rowconfigure(0, weight=1)
        
        self.cards = {}
        self.trader_order = []
        self.initialized = False
        self.ten_min_notified = {k: False for k in TRADER_MAPPING.keys()}
        
        self.update_thread = threading.Thread(target=self.update_timers, daemon=True)
        self.update_thread.start()
        
        self.root.bind('<Configure>', self.on_resize)

    def create_trader_menu(self):
        # Créer les options du menu avec les cases à cocher
        for name in TRADER_MAPPING.keys():
            var = self.trader_vars.get(name, tk.BooleanVar(value=True))
            self.trader_vars[name] = var
            # Utiliser la couleur du trader pour le texte du menu
            color = TRADER_COLORS.get(name, "white")
            # Créer une commande lambda qui appelle update_trader_visibility avec le nom du trader
            self.trader_menu.add_checkbutton(
                label=name,
                variable=var,
                command=lambda n=name: self.update_trader_visibility(n),
                foreground=color,
                selectcolor="#232323",
                activebackground="#232323",
                activeforeground=color
            )

    def update_trader_visibility(self, trader_name):
        # Sauvegarder la sélection
        self.save_selection_callback()
        # Mettre à jour l'affichage
        self.regrid_cards()

    def save_selection_callback(self):
        try:
            with open(SELECTION_FILE, 'w', encoding='utf-8') as f:
                json.dump({k: v.get() for k, v in self.trader_vars.items()}, f)
        except Exception as e:
            logging.error(f"Erreur sauvegarde sélection: {e}")

    def load_or_init_selection(self):
        try:
            with open(SELECTION_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for name in TRADER_MAPPING.keys():
                    var = tk.BooleanVar(value=data.get(name, True))
                    self.trader_vars[name] = var
        except Exception as e:
            logging.error(f"Erreur chargement sélection: {e}")
            for name in TRADER_MAPPING.keys():
                var = tk.BooleanVar(value=True)
                self.trader_vars[name] = var

    def get_col_count(self):
        width = self.root.winfo_width()
        if width < 600:
            return 2
        elif width < 900:
            return 3
        else:
            return 4

    def on_resize(self, event):
        if event.widget == self.root:  # Ne réagir qu'aux changements de taille de la fenêtre principale
            new_col_count = self.get_col_count()
            if new_col_count != self.current_col_count:
                self.current_col_count = new_col_count
                self.regrid_cards()
                # Forcer la mise à jour des avatars pour la nouvelle taille
                for card in self.cards.values():
                    card.set_avatar_local(card.name_label.cget("text").lower())

    def regrid_cards(self):
        visible_cards = [card for name, card in self.cards.items() 
                        if self.trader_vars.get(name, tk.BooleanVar(value=True)).get()]
        
        # Calculer la taille optimale des cartes
        window_width = self.grid_frame.winfo_width()
        window_height = self.grid_frame.winfo_height()
        if window_width > 1 and window_height > 1:
            card_width = window_width // self.current_col_count
            card_height = window_height // ((len(visible_cards) + self.current_col_count - 1) // self.current_col_count)
            card_size = min(card_width, card_height) - 10  # Réduction de la marge de 20 à 10 pixels
        else:
            card_size = 80  # Réduction de la taille par défaut de 100 à 80
            
        for i, card in enumerate(visible_cards):
            row, col = divmod(i, self.current_col_count)
            card.frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")  # Réduction des marges de 10 à 5
            
        # Configurer les colonnes et lignes de la grille
        for i in range(self.current_col_count):
            self.grid_frame.grid_columnconfigure(i, weight=1)
        for i in range((len(visible_cards) + self.current_col_count - 1) // self.current_col_count):
            self.grid_frame.grid_rowconfigure(i, weight=1)

    def create_cards(self, traders):
        col_count = self.current_col_count
        self.trader_order = []
        for idx, name in enumerate(traders):
            if not self.trader_vars.get(name, tk.BooleanVar(value=True)).get():
                continue
            color = TRADER_COLORS.get(name, "white")
            card = TraderCard(self.grid_frame, name, color)
            row, col = divmod(len(self.trader_order), col_count)
            card.frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")  # Réduction des marges de 18 à 8
            self.cards[name] = card
            self.trader_order.append(name)
        for i in range(col_count):
            self.grid_frame.grid_columnconfigure(i, weight=1)
        self.initialized = True

    def update_cards(self, traders):
        to_remove = [name for name in self.cards 
                    if not self.trader_vars.get(name, tk.BooleanVar(value=True)).get() 
                    or name not in traders]
        for name in to_remove:
            self.cards[name].frame.destroy()
            del self.cards[name]
        col_count = self.current_col_count
        current_names = set(self.cards.keys())
        idx = 0
        for name in traders:
            if not self.trader_vars.get(name, tk.BooleanVar(value=True)).get():
                continue
            if name not in current_names:
                color = TRADER_COLORS.get(name, "white")
                card = TraderCard(self.grid_frame, name, color)
                row, col = divmod(idx, col_count)
                card.frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")  # Réduction des marges de 18 à 8
                self.cards[name] = card
            idx += 1
        for i in range(col_count):
            self.grid_frame.grid_columnconfigure(i, weight=1)

    def scrape_trader_resets(self):
        try:
            response_pve = requests.get(URL_PVE, headers=HEADERS)
            response_pve.raise_for_status()
            
            data_pve = response_pve.json()
            traders_pve = {trader['name']: trader for trader in data_pve}
            
            now = datetime.now(pytz.UTC)
            
            for local_name, api_name in TRADER_MAPPING.items():
                if not self.trader_vars.get(local_name, tk.BooleanVar(value=True)).get():
                    continue
                    
                if api_name not in traders_pve:
                    continue
                    
                trader_pve = traders_pve[api_name]
                
                pve_reset_time = parse(trader_pve['resetTime'])
                pve_remaining = relativedelta(pve_reset_time, now)
                pve_time_str = format_time_remaining(pve_remaining)
                
                card = self.cards.get(local_name)
                if card:
                    local_time = pve_reset_time.astimezone().strftime('%H:%M:%S')
                    local_time_str = f"Reset à {local_time} (local)"
                    card.set_timer(pve_time_str, local_time_str, pve_remaining)
                    
                    # Calcul du temps total en minutes
                    total_minutes = pve_remaining.hours * 60 + pve_remaining.minutes + pve_remaining.seconds / 60
                    
                    # Alerte sonore si passage sous les 10 minutes
                    if total_minutes <= 10 and not self.ten_min_notified.get(local_name, False):
                        play_sound(ALERT_10MIN_SOUND)
                        self.ten_min_notified[local_name] = True
                    elif total_minutes > 10:
                        self.ten_min_notified[local_name] = False
                    
        except Exception as e:
            logging.error(f"Erreur lors du scraping: {e}")

    def manual_refresh(self):
        logging.info("Bouton Rafraîchir cliqué.")
        self.scrape_trader_resets()

    def update_timers(self):
        while True:
                traders = list(TRADER_MAPPING.keys())
                filtered_traders = [t for t in traders if self.trader_vars.get(t, tk.BooleanVar(value=True)).get()]
                if not self.initialized:
                    self.create_cards(filtered_traders)
                else:
                    self.update_cards(traders)
                self.scrape_trader_resets()
                time.sleep(2)

def log_uncaught_exceptions(exctype, value, tb):
    import traceback
    logging.critical("Uncaught exception:", exc_info=(exctype, value, tb))
    print("Une erreur fatale a été loggée dans app.log.")

sys.excepthook = log_uncaught_exceptions

if __name__ == "__main__":
    root = tk.Tk()
    app = TraderGridApp(root)
    try:
        root.mainloop()
    except Exception as e:
        logging.critical(f"Crash interface principale: {e}", exc_info=True)
        print("Une erreur fatale a été loggée dans app.log.")

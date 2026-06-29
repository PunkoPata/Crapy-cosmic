import os
import glob
import re
import sys
import time
import traceback
import pyperclip

# System paths
LOGS_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "EVE", "logs", "Gamelogs")
HISTORY_FOLDER = os.path.join(os.path.expanduser("~"), "firmas_eve_multisistema")

os.makedirs(HISTORY_FOLDER, exist_ok=True)

CHECK_INTERVAL = 1.0

# ANSI Colors
RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
GRAY = "\033[90m"
WHITE = "\033[97m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"

EVE_TERMS = ["Cosmic Signature", "Firma cósmica", "Cosmic Anomaly", "Anomalía cósmica"]


class EVEMonitor:
    def __init__(self):
        self.current_system = "Unknown"
        self.current_log_file = None
        self.current_character = "Unknown"
        self.last_lines_counted = 0
        self.last_clipboard_text = ""
        
    def get_txt_file_path(self):
        safe_name = "".join(c for c in self.current_system if c.isalnum() or c in ("-", "_")).strip()
        return os.path.join(HISTORY_FOLDER, f"firmas_{safe_name}.txt")

    def find_all_gamelogs_sorted(self):
        pattern = os.path.join(LOGS_FOLDER, "*.txt")
        files = glob.glob(pattern)
        if not files:
            return []
        
        gamelog_pattern = re.compile(r"^\d{8}_\d{6}_\d+\.txt$")
        valid_gamelogs = [
            f for f in files 
            if gamelog_pattern.match(os.path.basename(f))
        ]
        
        if not valid_gamelogs:
            return []
            
        return sorted(valid_gamelogs, key=os.path.getmtime, reverse=True)

    def extract_listener_and_system(self, log_path):
        listener = None
        system = None
        
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            for line in lines[:10]:
                match_listener = re.search(r"Listener:\s+(.+)", line)
                if match_listener:
                    listener = match_listener.group(1).strip()
                    break
            
            for line in reversed(lines):
                match_jump = re.search(r"Jumping from ([A-Za-z0-9\- ]+) to ([A-Za-z0-9\- ]+)", line)
                if match_jump:
                    system = match_jump.group(2).strip()
                    break
                
                match_undock = re.search(r"Undocking from .+? to ([A-Za-z0-9\- ]+) solar system", line)
                if match_undock:
                    system = match_undock.group(1).strip()
                    break
                    
        except Exception:
            pass
            
        return listener, system

    def trace_historical_location(self, target_character):
        all_logs = self.find_all_gamelogs_sorted()
        
        if len(all_logs) <= 1:
            return None
            
        for log_path in all_logs[1:]:
            listener, system = self.extract_listener_and_system(log_path)
            if listener == target_character and system:
                return system
        return None

    def track_system_change(self):
        all_logs = self.find_all_gamelogs_sorted()
        if not all_logs:
            return
            
        recent_log = all_logs[0]

        if recent_log != self.current_log_file:
            self.current_log_file = recent_log
            
            try:
                with open(recent_log, "r", encoding="utf-8", errors="ignore") as f:
                    initial_lines = f.readlines()
                self.last_lines_counted = len(initial_lines)
            except Exception:
                self.last_lines_counted = 0
                initial_lines = []
                
            self.current_character = "Unknown"
            for line in initial_lines[:10]:
                match_listener = re.search(r"Listener:\s+(.+)", line)
                if match_listener:
                    self.current_character = match_listener.group(1).strip()
                    break

            print()
            print(f"{GRAY}[PILOT]{RESET} Active character detected: {MAGENTA}{self.current_character}{RESET}")
            
            self.current_system = "Unknown"
            for line in reversed(initial_lines):
                match_jump = re.search(r"Jumping from ([A-Za-z0-9\- ]+) to ([A-Za-z0-9\- ]+)", line)
                if match_jump:
                    self.current_system = match_jump.group(2).strip()
                    self._print_system_banner("Detected in active session")
                    return
                
                match_undock = re.search(r"Undocking from .+? to ([A-Za-z0-9\- ]+) solar system", line)
                if match_undock:
                    self.current_system = match_undock.group(1).strip()
                    self._print_system_banner("Detected upon undocking")
                    return
            
            if self.current_character != "Unknown":
                historical_system = self.trace_historical_location(self.current_character)
                
                if historical_system:
                    self.current_system = historical_system
                    self._print_system_banner("Recovered from history")
                    return
            
            print(f"\n{RED} ⚠️  [CURRENT SYSTEM] Location unknown. No previous history found for {self.current_character}.{RESET}")
            print(f"{YELLOW} 👉 Please undock from station or perform a jump (Stargate) to start the monitor.{RESET}\n")
            return

        try:
            with open(recent_log, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            total_lines_now = len(lines)
            
            if total_lines_now > self.last_lines_counted:
                new_lines = lines[self.last_lines_counted:]
                self.last_lines_counted = total_lines_now

                for line in new_lines:
                    new_system = None

                    match_jump = re.search(r"Jumping from ([A-Za-z0-9\- ]+) to ([A-Za-z0-9\- ]+)", line)
                    if match_jump:
                        new_system = match_jump.group(2).strip()
                    else:
                        match_undock = re.search(r"Undocking from .+? to ([A-Za-z0-9\- ]+) solar system", line)
                        if match_undock:
                            new_system = match_undock.group(1).strip()

                    if new_system and new_system != self.current_system:
                        self.current_system = new_system
                        self._print_system_banner("System Changed")
            
            elif total_lines_now < self.last_lines_counted:
                self.last_lines_counted = total_lines_now

        except Exception:
            pass

    def _print_system_banner(self, trigger_type):
        print(f"{GRAY}[SYSTEM] {WHITE}{self.current_system:<22}{RESET} {GRAY}({trigger_type}){RESET}")


def get_clipboard_text():
    try:
        return pyperclip.paste()
    except Exception:
        return None


def get_site_icon(info_text, is_anomaly=False):
    """Asigna icono y color de texto basándose en las palabras clave del scanner"""
    info_lower = info_text.lower()
    
    if "wormhole" in info_lower or "agujero de gusano" in info_lower:
        return "🕳️ ", MAGENTA
    elif "relic" in info_lower or "reliquias" in info_lower:
        return "🔑", YELLOW
    elif "data" in info_lower or "datos" in info_lower:
        return "💾", CYAN
    elif "gas" in info_lower:
        return "☁️ ", WHITE
    elif "combat" in info_lower or "combate" in info_lower:
        return "💀", RED
    
    if is_anomaly:
        return "🔸", GREEN  # Si es otra anomalía genérica (ore, etc)
        
    return "🌀", GRAY  # Firma cósmica sin escanear al 100%


def extract_signature_data(text):
    sig_data = {}
    if not text:
        return sig_data
    clean_text = text.replace("<br>", "\n").replace("\r\n", "\n")
    lines = clean_text.split("\n")
    for line in lines:
        if any(term in line for term in EVE_TERMS):
            is_anomaly = "Anomaly" in line or "Anomaly" in line or "Anomalía" in line or "anomalía" in line
            
            match = re.search(r"([A-Za-z]{3}-\d{3})", line)
            if match:
                sig_id = str(match.group(1)).upper()
                processable_line = line.split(">", 1)[1].strip() if ">" in line else line
                parts = [p.strip() for p in re.split(r"\t| {2,}", processable_line) if p.strip()]
                
                percentage = 0.0
                match_percentage = re.search(r"(\d+([.,]\d+)?)\s*%", processable_line)
                if match_percentage:
                    percentage = float(match_percentage.group(1).replace(",", "."))

                extra_info = "Unscanned"
                type_idx = -1
                for i, part in enumerate(parts):
                    if any(t in part for t in EVE_TERMS):
                        type_idx = i
                        break
                if type_idx != -1:
                    name_blocks = []
                    for part in parts[type_idx + 1:]:
                        if "%" not in part and not part.endswith("AU") and not part.endswith("km") and "Zona de" not in part and "Combat Zone" not in part:
                            name_blocks.append(part)
                    if name_blocks:
                        extra_info = " - ".join(name_blocks)
                
                sig_data[sig_id] = {"percentage": percentage, "info": extra_info, "is_anomaly": is_anomaly}
    return sig_data


def save_merged_history(file_path, merged_sigs):
    lines_to_save = []
    for sig_id, data in merged_sigs.items():
        pct_str = str(data["percentage"]).replace(".", ",") + " %"
        type_str = "Cosmic Anomaly" if data.get("is_anomaly") else "Cosmic Signature"
        if data["info"] != "Unscanned":
            line = f"{sig_id}\t{type_str}\t{data['info']}\t{pct_str}\t1,0 AU"
        else:
            line = f"{sig_id}\t{type_str}\t{pct_str}\t1,0 AU"
        lines_to_save.append(line)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_to_save))


numChanges = 0

def process_changes(current_text, monitor):
    global numChanges
    if monitor.current_system == "Unknown":
        return

    current_sigs = extract_signature_data(current_text)
    if not current_sigs:
        return

    if numChanges != 0:
        print("\033[2J\033[H")

    txt_path = monitor.get_txt_file_path()
    previous_sigs = {}
    if os.path.exists(txt_path):
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                previous_sigs = extract_signature_data(f.read())
        except Exception:
            pass

    if not previous_sigs:
        print(f"{GREEN}[OK]{RESET} Initialized system: {CYAN}{monitor.current_system}{RESET}. Registered {YELLOW}{len(current_sigs)}{RESET} sites.\n")
        save_merged_history(txt_path, current_sigs)
        return

    set_current = set(current_sigs.keys())
    set_previous = set(previous_sigs.keys())

    new_sigs = set_current - set_previous
    desp_sigs = set_previous - set_current
    common_sigs = set_current & set_previous

    final_merged_sigs = {}
    updated_report = {}

    for sig_id in new_sigs:
        final_merged_sigs[sig_id] = current_sigs[sig_id]

    for sig_id in common_sigs:
        actual = current_sigs[sig_id]
        anterior = previous_sigs[sig_id]
        if actual["percentage"] >= anterior["percentage"]:
            final_merged_sigs[sig_id] = actual
            if actual["percentage"] > anterior["percentage"] and actual["info"] != anterior["info"]:
                updated_report[sig_id] = actual
        else:
            final_merged_sigs[sig_id] = anterior

    if new_sigs or desp_sigs or updated_report:
        current_time = time.strftime("%H:%M:%S")
        print(YELLOW + "═" * 65 + RESET)
        print(f" 🛰️  SYSTEM: {CYAN}{monitor.current_system:<10}{RESET} [{current_time}] ({YELLOW}{len(current_sigs)}{RESET} in space)")
        print(YELLOW + "═" * 65 + RESET)

        # --- SECCIÓN DE NUEVOS SITIOS ---
        if new_sigs:
            # Separar anomalías de firmas
            new_anoms = [s for s in new_sigs if current_sigs[s]["is_anomaly"]]
            new_signatures = [s for s in new_sigs if not current_sigs[s]["is_anomaly"]]

            if new_signatures:
                print(f" {GREEN}[S] NEW COSMIC SIGNATURES ({len(new_signatures)}):{RESET}")
                for sig_id in sorted(new_signatures):
                    info = current_sigs[sig_id]["info"]
                    pct = f"{current_sigs[sig_id]['percentage']}%"
                    icon, text_color = get_site_icon(info, is_anomaly=False)
                    print(f"   {GREEN}[+]{RESET} {icon} {GREEN}{sig_id}{RESET}  ->  {pct:<6}  {text_color}{info}{RESET}")

            if new_anoms:
                if new_signatures: print()  # Añadir salto si hay ambos tipos
                print(f" {GRAY}[A] NEW COSMIC ANOMALIES ({len(new_anoms)}):{RESET}")
                for sig_id in sorted(new_anoms):
                    info = current_sigs[sig_id]["info"]
                    pct = f"{current_sigs[sig_id]['percentage']}%"
                    icon, text_color = get_site_icon(info, is_anomaly=True)
                    # Forzar color verde suave para el texto de anomalías para que no sature la vista
                    print(f"   {GREEN}[+]{RESET} {icon} {GRAY}{sig_id}{RESET}  ->  {pct:<6}  {GREEN}{info}{RESET}")

        # --- SECCIÓN DE PROGRESO DE ESCANEO ---
        if updated_report:
            prog_anoms = [s for s in updated_report if updated_report[s]["is_anomaly"]]
            prog_signatures = [s for s in updated_report if not updated_report[s]["is_anomaly"]]

            if prog_signatures:
                print(f"\n {CYAN}[S] SCAN PROGRESS ({len(prog_signatures)}):{RESET}")
                for sig_id in sorted(prog_signatures):
                    info = updated_report[sig_id]["info"]
                    pct = f"{updated_report[sig_id]['percentage']}%"
                    icon, text_color = get_site_icon(info, is_anomaly=False)
                    print(f"   {CYAN}[*]{RESET} {icon} {CYAN}{sig_id}{RESET}  ->  {pct:<6}  {text_color}{info}{RESET}")

            if prog_anoms:
                print(f"\n {CYAN}[A] ANOMALY UPDATE ({len(prog_anoms)}):{RESET}")
                for sig_id in sorted(prog_anoms):
                    info = updated_report[sig_id]["info"]
                    pct = f"{updated_report[sig_id]['percentage']}%"
                    icon, text_color = get_site_icon(info, is_anomaly=True)
                    print(f"   {CYAN}[*]{RESET} {icon} {GRAY}{sig_id}{RESET}  ->  {pct:<6}  {GREEN}{info}{RESET}")

        # --- SECCIÓN DE SITIOS DESAPARECIDOS ---
        if desp_sigs:
            desp_anoms = [s for s in desp_sigs if previous_sigs[s]["is_anomaly"]]
            desp_signatures = [s for s in desp_sigs if not previous_sigs[s]["is_anomaly"]]

            if desp_signatures:
                print(f"\n {RED}[S] DESPAWNED SIGNATURES ({len(desp_signatures)}):{RESET}")
                for sig_id in sorted(desp_signatures):
                    info = previous_sigs[sig_id]["info"]
                    icon, _ = get_site_icon(info, is_anomaly=False)
                    print(f"   {RED}[-]{RESET} {icon} {WHITE}{sig_id}{RESET}              {GRAY}({info}){RESET}")

            if desp_anoms:
                print(f"\n {RED}[A] DESPAWNED ANOMALIES ({len(desp_anoms)}):{RESET}")
                for sig_id in sorted(desp_anoms):
                    info = previous_sigs[sig_id]["info"]
                    icon, _ = get_site_icon(info, is_anomaly=True)
                    print(f"   {RED}[-]{RESET} {icon} {GRAY}{sig_id}{RESET}              {GRAY}({info}){RESET}")

        #print(YELLOW + "-" * 65 + RESET + "\n")                
        save_merged_history(txt_path, final_merged_sigs)
        numChanges += 1


def get_current_solar_system(html_text):
    pattern = r'<a[^>]*alt=["\']Current Solar System["\'][^>]*>(.*?)</a>'
    match = re.search(pattern, html_text, re.IGNORECASE | re.DOTALL)

    if match:
        return match.group(1).strip()

    return None


def main():
    os.makedirs(HISTORY_FOLDER, exist_ok=True)
    os.system("")  # Enable ANSI colors on Windows

    print(YELLOW + "═" * 65 + RESET)
    print(YELLOW + "      📡     === Crapy Cosmic Probe Monitor ===     📡       " + RESET)
    print(YELLOW + "═" * 65 + RESET)
    print()

    print(WHITE + "  This program helps you track changes in the Probe Scanner window." + RESET)
    print()
    print(GREEN + "  How to use it:" + RESET)
    print(WHITE + "  Open the Scanner, select all (Ctrl+A), and copy (Ctrl+C)." + RESET)
    print(WHITE + "  The monitor will instantly print the differences with the previous data." + RESET)

    print()
    print(WHITE + "  If you find this program useful, feel free to send an in-game" + RESET)
    print(WHITE + f"  tip to {BOLD}{CYAN}\"Perkutor Jakuard\"{CYAN}{RESET}{WHITE}. It will be greatly appreciated!" + RESET)
    print()


    print()
    print(YELLOW + "═" * 65 + RESET)
    #print(f"  {GRAY}Reverse tracking active. Watching logs...{RESET}\n")

    monitor = EVEMonitor()

    try:
        while True:
            monitor.track_system_change()

            current_text = get_clipboard_text()

            # For WH where the logs don't appears.
            if current_text:
                system=get_current_solar_system(current_text)
                if system and system != monitor.current_system:
                    monitor.current_system = system
                    print(YELLOW + "═" * 65 + RESET)
                    print(
                        f" 🛰️  SYSTEM: {CYAN}{monitor.current_system:<10}{RESET} from clipboard")
                    print(YELLOW + "═" * 65 + RESET)


            if (
                current_text
                and current_text.strip()
                and current_text != monitor.last_clipboard_text
            ):
                if any(t in current_text for t in EVE_TERMS):
                    process_changes(current_text, monitor)
                    monitor.last_clipboard_text = current_text

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n{CYAN}[INFO]{RESET} Monitor stopped cleanly.")
    except Exception as e:
        print(f"\n{RED}❌ CRITICAL ERROR IN THE MONITOR!{RESET}")
        print("-" * 50)
        traceback.print_exc()
        print("-" * 50)
        input("\nPress ENTER to exit...")


if __name__ == "__main__":
    main()

import os
import re
import sys
import time
import traceback
from tkinter import Tk

# Archivo de historial en tu carpeta de usuario
ARCHIVO_TXT = os.path.join(os.path.expanduser("~"), "firmas_anteriores.txt")

# Frecuencia de revisión en segundos
INTERVALO_REVISION = 1.0

# Códigos de color ANSI para la consola
RESET = "\033[0m"
VERDE = "\033[92m"
ROJO = "\033[91m"
CIAN = "\033[96m"
AMARILLO = "\033[93m"
GRIS = "\033[90m"


def obtener_texto_portapapeles():
    """Lee el portapapeles usando Tkinter de forma limpia."""
    try:
        root = Tk()
        root.withdraw()
        root.update()
        texto = root.clipboard_get()
        root.destroy()
        return str(texto)
    except Exception:
        return None


def extraer_datos_firmas(texto):
    """Mapea cada ID con su nombre/información extra si existe."""
    datos_firmas = {}
    if not texto:
        return datos_firmas
        
    lineas = texto.replace("\r\n", "\n").split("\n")
    for linea in lineas:
        if "Cosmic Signature" in linea:
            match = re.search(r"([A-Za-z]{3}-\d{3})", linea)
            if match:
                id_firma = str(match.group(1)).upper()
                
                partes = [p.strip() for p in re.split(r"\t| {2,}", linea) if p.strip()]
                info_extra = "Sin escanear"
                
                if "Cosmic Signature" in partes:
                    idx = partes.index("Cosmic Signature")
                    if idx + 1 < len(partes):
                        siguiente = partes[idx + 1]
                        if "%" not in siguiente and not siguiente.endswith("AU"):
                            info_extra = siguiente
                            
                datos_firmas[id_firma] = info_extra
    return datos_firmas


def procesar_cambios(texto_actual):
    """Compara las firmas actuales e incluye sus nombres en el reporte con colores."""
    firmas_actuales = extraer_datos_firmas(texto_actual)

    if not firmas_actuales:
        return

    firmas_anteriores = {}
    if os.path.exists(ARCHIVO_TXT):
        try:
            with open(ARCHIVO_TXT, "r", encoding="utf-8") as f:
                firmas_anteriores = extraer_datos_firmas(f.read())
        except Exception:
            pass

    # Si es el primer escaneo de la sesión
    if not firmas_anteriores:
        print(f"\n{VERDE}[OK]{RESET} Base de datos inicializada. Registradas {AMARILLO}{len(firmas_actuales)}{RESET} firmas.")
        with open(ARCHIVO_TXT, "w", encoding="utf-8") as f:
            f.write(texto_actual)
        return

    set_actuales = set(firmas_actuales.keys())
    set_anteriores = set(firmas_anteriores.keys())

    nuevas = set_actuales - set_anteriores
    desaparecidas = set_anteriores - set_actuales

    # Revisamos si una firma vieja ahora tiene nombre
    actualizadas = {}
    for id_comun in set_actuales & set_anteriores:
        if firmas_actuales[id_comun] != firmas_anteriores[id_comun] and firmas_actuales[id_comun] != "Sin escanear":
            actualizadas[id_comun] = firmas_actuales[id_comun]

    # Imprimimos si hay novedades
    if nuevas or desaparecidas or actualizadas:
        hora_actual = time.strftime("%H:%M:%S")

        print("\n" + AMARILLO + "=" * 50 + RESET)
        print(f"   ACTUALIZACIÓN [{hora_actual}] ({AMARILLO}{len(firmas_actuales)}{RESET} en espacio)")
        print(AMARILLO + "=" * 50 + RESET)

        if nuevas:
            print(f"{VERDE}NUEVAS ({len(nuevas)}):{RESET}")
            for id_firma in sorted(nuevas):
                info = firmas_actuales[id_firma]
                info_color = GRIS + info + RESET if info == "Sin escanear" else CIAN + info + RESET
                print(f"  {VERDE}[+]{RESET} {id_firma} -> {info_color}")
        else:
            print(f"{GRIS}No hay firmas nuevas.{RESET}")

        if actualizadas:
            print(f"\n{CIAN}ESCANEADAS/CAMBIADAS ({len(actualizadas)}):{RESET}")
            for id_firma in sorted(actualizadas):
                print(f"  {CIAN}[*]{RESET} {id_firma} -> {AMARILLO}{actualizadas[id_firma]}{RESET}")

        if desaparecidas:
            print(f"\n{ROJO}DESAPARECIDAS ({len(desaparecidas)}):{RESET}")
            for id_firma in sorted(desaparecidas):
                print(f"  {ROJO}[-]{RESET} {id_firma} {GRIS}({firmas_anteriores[id_firma]}){RESET}")
        else:
            print(f"\n{GRIS}Ninguna firma ha desaparecido.{RESET}")

        print(AMARILLO + "=" * 50 + RESET)

        # Guardamos el estado actual para la siguiente vuelta
        with open(ARCHIVO_TXT, "w", encoding="utf-8") as f:
            f.write(texto_actual)
    else:
        print(f"\n {AMARILLO} [=] {RESET} No hay Cambios" + RESET)

def main():
    # Forzar a la consola de Windows a aceptar códigos de color ANSI
    os.system("")

    print(AMARILLO + "=== MONITOR DE FIRMAS EVE ONLINE ===" + RESET)
    print(VERDE + "\nSi lo encuentras util, puedes enviar un poco de isk a 'Perkutor Jakuard'. Gracias !!" + RESET)
    print("");
    print("Para usarlo ve copiando el contenido de la ventana de escaneo de sondas / Probe Scanner")
    print("Te dirá cuando las cosmic signatures han cambiado.")
    print("De momento No soporta multiples sistemas.\n")
    print(f"{GRIS}Escuchando portapapeles de Windows...{RESET}")
    print("Copia el Probe Scanner (Ctrl+A y Ctrl+C) en el juego para actualizar.\n")

    ultimo_texto_procesado = ""

    try:
        while True:
            texto_actual = obtener_texto_portapapeles()

            if (
                texto_actual
                and texto_actual.strip()
                and texto_actual != ultimo_texto_procesado
            ):
                if "Cosmic Signature" in texto_actual:
                    procesar_cambios(texto_actual)
                    ultimo_texto_procesado = texto_actual

            time.sleep(INTERVALO_REVISION)

    except KeyboardInterrupt:
        print(f"\n{CIAN}[INFO]{RESET} Monitor detenido por el usuario.")
    except Exception as e:
        print(f"\n{ROJO}❌ ¡EL MONITOR HA SUFRIDO UN ERROR!{RESET}")
        print("-" * 50)
        traceback.print_exc()
        print("-" * 50)
        input("\nPresiona ENTER para salir...")


if __name__ == "__main__":
    main()
    

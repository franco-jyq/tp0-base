# Mecanismos de Sincronización Utilizados

## 1. Barrier (`multiprocessing.Barrier`)

- **Ubicación:** `server.py` en la función `run()` y `__handle_client_connection()`.
- **Descripción:**
  - Se utiliza una barrera para sincronizar a los clientes que se conectan al servidor.
  - La barrera asegura que todos los procesos de los clientes (definidos como procesos separados) esperen a que todos los demás hayan llegado a un punto específico (cuando todos los clientes han almacenado sus apuestas) antes de proceder.

## 2. Condition Variable (`multiprocessing.Condition`)

- **Ubicación:** `server.py` en la función `run()` y `__handle_client_connection()`.
- **Descripción:**
  - Se utiliza una condición para notificar a los clientes cuando la lotería ha finalizado y los ganadores han sido seleccionados.
  - Una vez que todos los procesos de los clientes han llegado a la barrera y la lotería se ha realizado, el servidor utiliza la condición para despertar a todos los procesos de los clientes y permitirles proceder con el envío de los resultados.

## 3. Locks (`multiprocessing.Lock`)

- **Ubicación:** `gambler_protocol.py` en las funciones `store_bets()` y `load_lottery_winners()`.
- **Descripción:**
  - Se utiliza un (`Lock`) para asegurar que las operaciones de almacenamiento y carga de apuestas en el archivo CSV no sean interrumpidas por otros procesos.

## 4. Eventos (`threading.Event`)

- **Ubicación:** `server.py` en la clase `Server`.
- **Descripción:**
  - Se utiliza un evento para gestionar el gracefull shutdowns del servidor.
  - Cuando se recibe una señal de terminación (`SIGTERM`), el evento se establece, lo que permite al servidor cerrar las conexiones de manera ordenada.

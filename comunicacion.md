# Protocolo de Comunicación para Lotería Nacional

Este protocolo maneja la interacción entre un servidor central (en Python) y múltiples clientes (en Go) que simulan agencias de lotería enviando batchs de apuestas. A continuación se detalla cómo se lleva a cabo el envío, recepción y procesamiento de los mensajes entre las agencias y el servidor.

## Estructura del Mensaje

### Cliente (Agencias de Quiniela)

El cliente envía las apuestas utilizando la clase `GamblerProtocol` y `Gambler` en Go, que gestiona los datos:

1. **HouseID**: ID de la agencia que envía las apuestas (1 byte).
1. **Nombre del Jugador**: Nombre del apostador (hasta 30 bytes).
1. **Apellido del Jugador**: Apellido del apostador (hasta 30 bytes).
1. **DNI del Jugador**: Número de DNI del apostador (4 bytes).
1. **Fecha de Nacimiento**: Fecha de nacimiento del apostador (10 bytes).
1. **Número de Apuesta**: Número apostado (4 bytes).

Cada apuesta enviada tiene un tamaño fijo de **79 bytes**. Un batch puede tener hasta **8137 bytes** (equivalente a 103 apuestas) para garantizar una comunicación eficiente.

### Mensaje de Finalización

El batch enviado por el cliente finaliza con un mensaje especial llamado `END_MESSAGE` que tiene el mismo tamaño que una apuesta (79 bytes) y se utiliza para indicar el fin del batch.

### Acknowledgement

Por cada batch recibido el servidor responde con una batch de aknowledges confirmando la recepcion de las apuestas recibidas. Cada mensaje de confirmación tiene un tamaño de **9 bytes**, e incluye:

1. **DNI**: Número de DNI del apostador (4 bytes).
2. **Número de Apuesta**: Número de la apuesta (4 bytes).
3. **Código de Estado**: Código que indica si la apuesta fue almacenada exitosamente (1 byte).

El batch de confirmaciones finaliza con el mensaje `END`, de **9 bytes**.

## Servidor (Central de Lotería)

El servidor recibe los batch de apuestas, los deserializa y almacena en un archivo CSV haciendo uso de la clase `GamblerProtocol` y `Gambler`. El protocolo del servidor sigue estos pasos:

1. **Recepción del Batch**:
   El servidor utiliza la metodo `receieve_batch_packets` para recibir las apuestas del cliente. El batch se procesa hasta que se detecta el mensaje `END_MESSAGE`, que marca el fin de las apuestas.

2. **Almacenamiento de Apuestas**:
   Una vez recibidos los datos, el servidor deserializa las apuestas mediante el metodo `deserialize_packets` y luego las almacena en un archivo usando `store_bets`.

3. **Envío de Confirmaciones**:
   Después de almacenar las apuestas, el servidor envía una confirmación al cliente con el metodo `send_packets_ack`.

4. **Cálculo de Ganadores**:
   Después de procesar todas las apuestas, el servidor utiliza la metodo `load_lottery_winners` para cargar los resultados y determinar los ganadores. Cada cliente recibirá una lista de los ganadores correspondiente a las apuestas de su agencia.

### Mensaje de Ganadores

Cuando se completa la evaluación de las apuestas, el servidor envía un mensaje que incluye la lista de documentos ganadores a través de la función `serialize_winners_documents`. Este mensaje tiene la siguiente estructura:

1. **Longitud del Mensaje**: El servidor primero envía 2 bytes que indican la longitud total del mensaje.
2. **Documentos Ganadores**: Luego, se envían los números de DNI ganadores, cada uno de 4 bytes.

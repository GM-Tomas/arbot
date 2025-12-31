# Arbitbot - Documentación Técnica

## Arquitectura del Proyecto

Este proyecto sigue una arquitectura **MVC (Modelo-Vista-Controlador)** simplificada, diseñada para ser minimalista, mantenible y escalable.

### Principios SOLID Aplicados

1.  **SRP (Principio de Responsabilidad Única):**
    *   `BinanceKlineWebSocket`: Solo se encarga de la conexión técnica y recepción de datos. No sabe nada de la UI ni del estado global.
    *   `PriceMonitor`: Es el "dueño" del estado de los datos (precios actuales). Su única responsabilidad es mantener esta información actualizada y disponible.
    *   `dashboard_view.py`: Solo se encarga de presentar los datos al usuario. No manipula lógica de negocio.

2.  **OCP (Principio Abierto/Cerrado):**
    *   La clase `PriceMonitor` está diseñada para ser extendida (ej: agregar nuevos métodos de cálculo) sin modificar su lógica base de conexión.

3.  **DIP (Principio de Inversión de Dependencias):**
    *   La vista no depende directamente del WebSocket de bajo nivel, sino de la abstracción de alto nivel `PriceMonitor`.

### Patrones de Diseño

#### 1. Singleton (PriceMonitor)
Utilizamos el patrón **Singleton** para la clase `PriceMonitor`.
*   **¿Por qué?** Necesitamos una única "fuente de verdad" para los precios de las criptomonedas en toda la aplicación web. No queremos múltiples conexiones WebSocket abiertas duplicando datos.
*   **Implementación:** El método estático `get_instance()` asegura que siempre accedamos a la misma instancia de la clase.

#### 2. Observer (WebSocket)
Aunque implementado internamente en nuestra clase `BinanceKlineWebSocket`, se usa el patrón **Observer**.
*   **Flujo:** El WebSocket "observa" el stream de Binance y "notifica" (vía callbacks) al `PriceMonitor` cada vez que llega un nuevo precio.

---

## Flujo de Datos

1.  **Inicio:** Al arrancar, `PriceMonitor` inicia una conexión WebSocket con una lista de pares por defecto.
2.  **Ingesta:** 
    *   Binance envía datos -> `BinanceKlineWebSocket` recibe.
    *   `BinanceKlineWebSocket` invoca callback -> `PriceMonitor` actualiza su diccionario interno `_prices`.
3.  **Visualización (Loop):**
    *   Dash (`dashboard_view.py`) tiene un intervalo (cada 1s).
    *   Llama a `PriceMonitor.get_prices()`.
    *   Actualiza el DOM del navegador con los nuevos valores.
4.  **Interacción (Cambio de Pares):**
    *   Usuario escribe nuevos pares en la UI y clickea "Actualizar".
    *   `dashboard_view` llama a `PriceMonitor.update_pairs()`.
    *   `PriceMonitor` reinicia el WebSocket con la nueva lista.
    *   El flujo de Ingesta se reanuda con los nuevos pares.

---

## Estructura de Archivos

*   `run_dashboard.py`: Punto de entrada. Inicia el servidor web.
*   `classes/`
    *   `price_monitor.py`: **Modelo**. Singleton que gestiona los datos.
    *   `binance_kline_websocket.py`: **Infraestructura**. Cliente WebSocket.
*   `web/`
    *   `app.py`: **Configuración**. Inicialización de la app Dash.
    *   `views/dashboard_view.py`: **Vista**. Interfaz gráfica.

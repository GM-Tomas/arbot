# Arbitbot Dashboard

Esta es la aplicación web del dashboard de Arbitbot con navegación entre dos páginas principales.

## Estructura de Archivos

```
web/
├── app.py                 # Archivo principal de la aplicación
├── layout.py             # Layout principal con navegación
├── views/                # Directorio de vistas
│   ├── __init__.py       # Archivo de inicialización del paquete
│   ├── dashboard_view.py # Vista del dashboard de precios y volumen
│   └── arbitrage_view.py # Vista de oportunidades de arbitraje
└── README.md             # Este archivo
```

## Páginas Disponibles

### 1. Dashboard de Precios y Volumen (`/` o `/dashboard`)
- Muestra precios en tiempo real de criptomonedas
- Gráfico de volumen
- Panel de control para WebSocket
- Actualización automática cada segundo

### 2. Oportunidades de Arbitraje (`/arbitrage`)
- Página informativa sobre análisis de arbitraje
- Descripción de funcionalidades futuras
- Placeholder para implementación completa

## Navegación

La aplicación incluye una barra de navegación en la parte superior que permite cambiar entre las dos páginas:
- **Dashboard de Precios**: Para ver precios y volumen en tiempo real
- **Oportunidades de Arbitraje**: Para información sobre análisis de arbitraje

## Ejecutar la Aplicación

```bash
cd web
python app.py
```

La aplicación estará disponible en `http://localhost:8050`

## Características

- **Navegación SPA**: Single Page Application con routing basado en URL
- **Diseño Responsivo**: Usando Bootstrap para adaptarse a diferentes tamaños de pantalla
- **Actualización en Tiempo Real**: WebSocket para datos de precios
- **Modular**: Código separado en vistas independientes 
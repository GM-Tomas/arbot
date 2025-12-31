#!/usr/bin/env python3
"""
Script para ejecutar el dashboard de Arbitbot
"""

import sys
import os

# Add the web directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'web'))

if __name__ == '__main__':
    print("🚀 Iniciando Arbitbot Dashboard...")
    print("📊 Dashboard disponible en: http://localhost:8050")
    print("=" * 50)
    
    try:
        from web.app import app
        app.run_server(debug=True, host='0.0.0.0', port=8050)
    except KeyboardInterrupt:
        print("\n👋 Dashboard detenido")
    except Exception as e:
        print(f"❌ Error iniciando dashboard: {e}")
        sys.exit(1) 
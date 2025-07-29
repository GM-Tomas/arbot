#!/usr/bin/env python3
"""
Script de inicio para el sistema de arbitraje triangular

Este script ejecuta:
1. La API de streaming (FastAPI)
2. El dashboard web (Dash)
3. Monitorea el estado del sistema
"""

import subprocess
import sys
import os
import time
import threading
import signal
import requests
from datetime import datetime

class ArbitrageSystem:
    def __init__(self):
        self.api_process = None
        self.dashboard_process = None
        self.running = True
        
        # Configurar manejo de señales para cierre limpio
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Maneja las señales de interrupción"""
        print("\n🛑 Recibida señal de interrupción. Cerrando sistema...")
        self.stop_system()
        sys.exit(0)
    
    def start_api(self):
        """Inicia la API de streaming"""
        try:
            print("🚀 Iniciando API de streaming...")
            self.api_process = subprocess.Popen([
                sys.executable, "api/streaming_api.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Esperar un momento para que la API se inicie
            time.sleep(3)
            
            # Verificar que la API esté funcionando
            try:
                response = requests.get("http://localhost:8000/", timeout=5)
                if response.status_code == 200:
                    print("✅ API iniciada correctamente en http://localhost:8000")
                    return True
                else:
                    print("❌ Error: API no responde correctamente")
                    return False
            except requests.exceptions.RequestException:
                print("❌ Error: No se puede conectar a la API")
                return False
                
        except Exception as e:
            print(f"❌ Error iniciando API: {e}")
            return False
    
    def start_dashboard(self):
        """Inicia el dashboard web"""
        try:
            print("🌐 Iniciando dashboard web...")
            self.dashboard_process = subprocess.Popen([
                sys.executable, "web/dashboard.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Esperar un momento para que el dashboard se inicie
            time.sleep(5)
            
            # Verificar que el dashboard esté funcionando
            try:
                response = requests.get("http://localhost:8050/", timeout=5)
                if response.status_code == 200:
                    print("✅ Dashboard iniciado correctamente en http://localhost:8050")
                    return True
                else:
                    print("❌ Error: Dashboard no responde correctamente")
                    return False
            except requests.exceptions.RequestException:
                print("❌ Error: No se puede conectar al dashboard")
                return False
                
        except Exception as e:
            print(f"❌ Error iniciando dashboard: {e}")
            return False
    
    def monitor_system(self):
        """Monitorea el estado del sistema"""
        while self.running:
            try:
                # Verificar API
                api_status = "✅ Activa" if self.check_api_status() else "❌ Inactiva"
                
                # Verificar Dashboard
                dashboard_status = "✅ Activo" if self.check_dashboard_status() else "❌ Inactivo"
                
                # Mostrar estado
                print(f"\n📊 Estado del Sistema - {datetime.now().strftime('%H:%M:%S')}")
                print(f"🔗 API: {api_status}")
                print(f"🌐 Dashboard: {dashboard_status}")
                print("💡 Presiona Ctrl+C para detener")
                
                time.sleep(30)  # Verificar cada 30 segundos
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error monitoreando sistema: {e}")
                time.sleep(10)
    
    def check_api_status(self):
        """Verifica el estado de la API"""
        try:
            response = requests.get("http://localhost:8000/api/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_dashboard_status(self):
        """Verifica el estado del dashboard"""
        try:
            response = requests.get("http://localhost:8050/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def stop_system(self):
        """Detiene el sistema completo"""
        print("\n🛑 Deteniendo sistema de arbitraje...")
        
        # Detener dashboard
        if self.dashboard_process:
            print("🛑 Deteniendo dashboard...")
            self.dashboard_process.terminate()
            try:
                self.dashboard_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.dashboard_process.kill()
        
        # Detener API
        if self.api_process:
            print("🛑 Deteniendo API...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
        
        self.running = False
        print("✅ Sistema detenido correctamente")
    
    def run(self):
        """Ejecuta el sistema completo"""
        print("🤖 Sistema de Arbitraje Triangular")
        print("=" * 50)
        
        # Verificar dependencias
        if not self.check_dependencies():
            print("❌ Error: Faltan dependencias. Ejecuta: pip install -r support/requirements.txt")
            return
        
        # Iniciar API
        if not self.start_api():
            print("❌ No se pudo iniciar la API. Verificando errores...")
            if self.api_process:
                stdout, stderr = self.api_process.communicate()
                print(f"Error API: {stderr.decode()}")
            return
        
        # Iniciar Dashboard
        if not self.start_dashboard():
            print("❌ No se pudo iniciar el dashboard. Verificando errores...")
            if self.dashboard_process:
                stdout, stderr = self.dashboard_process.communicate()
                print(f"Error Dashboard: {stderr.decode()}")
            return
        
        print("\n🎉 Sistema iniciado correctamente!")
        print("📊 Dashboard: http://localhost:8050")
        print("🔗 API: http://localhost:8000")
        print("📖 Documentación API: http://localhost:8000/docs")
        print("\n" + "=" * 50)
        
        # Iniciar monitoreo
        self.monitor_system()
    
    def check_dependencies(self):
        """Verifica que las dependencias estén instaladas"""
        try:
            import fastapi
            import dash
            import plotly
            import uvicorn
            return True
        except ImportError as e:
            print(f"❌ Dependencia faltante: {e}")
            return False

def main():
    """Función principal"""
    system = ArbitrageSystem()
    
    try:
        system.run()
    except KeyboardInterrupt:
        print("\n🛑 Interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error en el sistema: {e}")
    finally:
        system.stop_system()

if __name__ == "__main__":
    main() 
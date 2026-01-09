import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classes.volume_scanner import VolumeScanner

def test_volume_scanner():
    print("🚀 Probando Volume Scanner...")
    
    # Archivo de salida temporal para testing
    output_file = os.path.join(os.path.dirname(__file__), "test_sorted_pairs.json")
    
    scanner = VolumeScanner(output_file=output_file)
    
    print("⏳ Iniciando escaneo (timeout 10s)...")
    start_time = time.time()
    pairs = scanner.scan_and_save(timeout=10)
    duration = time.time() - start_time
    
    if pairs:
        print(f"\n✅ ÉXITO: Se encontraron {len(pairs)} pares.")
        print(f"⏱️ Tiempo tomado: {duration:.2f} segundos")
        print(f"📂 Archivo generado: {output_file}")
        
        print("\n🏆 Top 10 Pares por Volumen:")
        for i, pair in enumerate(pairs[:10], 1):
            print(f"   {i}. {pair}")
            
    else:
        print("\n❌ FALLO: No se obtuvieron pares o se agotó el tiempo.")

if __name__ == "__main__":
    test_volume_scanner()

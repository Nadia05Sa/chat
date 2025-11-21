#!/usr/bin/env python3
"""
Script para calcular MD5 de archivos del proyecto
Genera archivo MD5_CHECKSUMS.txt con los hashes
"""

import hashlib
import os
from datetime import datetime

def calcular_md5(archivo):
    """Calcula el hash MD5 de un archivo"""
    md5_hash = hashlib.md5()
    try:
        with open(archivo, "rb") as f:
            # Leer en bloques para archivos grandes
            for bloque in iter(lambda: f.read(4096), b""):
                md5_hash.update(bloque)
        return md5_hash.hexdigest()
    except FileNotFoundError:
        return "ARCHIVO NO ENCONTRADO"
    except Exception as e:
        return f"ERROR: {str(e)}"

def obtener_tamanio(archivo):
    """Obtiene el tamaño del archivo en bytes"""
    try:
        return os.path.getsize(archivo)
    except:
        return 0

def contar_lineas(archivo):
    """Cuenta las líneas de código en un archivo"""
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except:
        return 0

def generar_reporte_md5():
    """Genera reporte completo de MD5 checksums"""
    
    # Archivos a verificar
    archivos = [
        "app.py",
        "config.py",
        "db_manager.py",
        "index.py",
        "manejadores.py",
        "security.py",
        "ws_server.py",
        "keys.py"
        "templates/chat.html",
        "templates/denied.html",
        "templates/login.html",
        "templates/perfil.html",
        "static/css/index.css",
        "static/js/chat.js",
        "static/js/login.js",
        "README.txt",
        "CONTROL_CAMBIOS.txt"
    ]
    
    # Crear contenido del reporte
    reporte = []
    reporte.append("=" * 80)
    reporte.append("MD5 CHECKSUMS - CHAT GRUPAL SEGURO")
    reporte.append("=" * 80)
    reporte.append(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    reporte.append(f"Versión del Proyecto: 1.0.0")
    reporte.append("=" * 80)
    reporte.append("")
    
    print("\n" + "=" * 80)
    print("CALCULANDO MD5 CHECKSUMS")
    print("=" * 80 + "\n")
    
    # Calcular MD5 para cada archivo
    for archivo in archivos:
        print(f"Procesando: {archivo}...", end=" ")
        md5 = calcular_md5(archivo)
        tamanio = obtener_tamanio(archivo)
        lineas = contar_lineas(archivo)
        
        if "ERROR" not in md5 and "NO ENCONTRADO" not in md5:
            print("✓")
            reporte.append(f"Archivo: {archivo}")
            reporte.append(f"  MD5:     {md5}")
            reporte.append(f"  Tamaño:  {tamanio:,} bytes")
            reporte.append(f"  Líneas:  {lineas:,}")
            reporte.append("")
        else:
            print(f"✗ ({md5})")
            reporte.append(f"Archivo: {archivo}")
            reporte.append(f"  Estado:  {md5}")
            reporte.append("")
    
    # Agregar formato para verificación manual
    reporte.append("=" * 80)
    reporte.append("FORMATO PARA VERIFICACIÓN")
    reporte.append("=" * 80)
    reporte.append("")
    reporte.append("Para verificar la integridad de un archivo:")
    reporte.append("  Windows: certutil -hashfile <archivo> MD5")
    reporte.append("  Linux:   md5sum <archivo>")
    reporte.append("  Mac:     md5 <archivo>")
    reporte.append("")
    
    # Agregar resumen
    reporte.append("=" * 80)
    reporte.append("RESUMEN")
    reporte.append("=" * 80)
    reporte.append("")
    
    archivos_ok = sum(1 for archivo in archivos 
                     if "ERROR" not in calcular_md5(archivo) 
                     and "NO ENCONTRADO" not in calcular_md5(archivo))
    
    reporte.append(f"Total de archivos procesados: {len(archivos)}")
    reporte.append(f"Archivos con MD5 calculado: {archivos_ok}")
    reporte.append(f"Archivos con error: {len(archivos) - archivos_ok}")
    reporte.append("")
    
    # Agregar tabla de referencia rápida
    reporte.append("=" * 80)
    reporte.append("TABLA DE REFERENCIA RÁPIDA")
    reporte.append("=" * 80)
    reporte.append("")
    reporte.append(f"{'Archivo':<30} {'MD5 Hash':<40}")
    reporte.append("-" * 80)
    
    for archivo in archivos:
        md5 = calcular_md5(archivo)
        if len(md5) == 32:  # MD5 válido
            reporte.append(f"{archivo:<30} {md5:<40}")
        else:
            reporte.append(f"{archivo:<30} {md5:<40}")
    
    reporte.append("")
    reporte.append("=" * 80)
    reporte.append("NOTAS IMPORTANTES")
    reporte.append("=" * 80)
    reporte.append("")
    reporte.append("1. Estos checksums deben actualizarse con cada modificación")
    reporte.append("2. Guardar este archivo en control de versiones")
    reporte.append("3. Verificar integridad antes de despliegue en producción")
    reporte.append("4. Comparar con versión anterior para detectar cambios")
    reporte.append("")
    reporte.append("=" * 80)
    
    # Guardar reporte
    nombre_archivo = "MD5_CHECKSUMS.txt"
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        f.write('\n'.join(reporte))
    
    print("\n" + "=" * 80)
    print(f"✓ Reporte guardado en: {nombre_archivo}")
    print("=" * 80 + "\n")
    
    # Mostrar resumen en consola
    print("RESUMEN:")
    print(f"  Archivos procesados: {len(archivos)}")
    print(f"  Archivos OK: {archivos_ok}")
    print(f"  Archivos con error: {len(archivos) - archivos_ok}")
    print("")
    
    return nombre_archivo

def verificar_archivo(archivo, md5_esperado):
    """Verifica si el MD5 de un archivo coincide con el esperado"""
    md5_actual = calcular_md5(archivo)
    if md5_actual == md5_esperado:
        print(f"✓ {archivo}: VERIFICADO")
        return True
    else:
        print(f"✗ {archivo}: NO COINCIDE")
        print(f"  Esperado: {md5_esperado}")
        print(f"  Actual:   {md5_actual}")
        return False

def main():
    """Función principal"""
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║  CALCULADORA DE MD5 CHECKSUMS - CHAT GRUPAL SEGURO       ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    # Generar reporte
    archivo_reporte = generar_reporte_md5()
    
    # Mostrar algunos MD5 importantes
    print("\nMD5 DE ARCHIVOS PRINCIPALES:")
    print("-" * 80)
    
    archivos_principales = ["chat_server.py", "index.html"]
    for archivo in archivos_principales:
        md5 = calcular_md5(archivo)
        if len(md5) == 32:
            print(f"{archivo:20} : {md5}")
    
    print("-" * 80)
    print("\nPara actualizar README.txt y CONTROL_CAMBIOS.txt con estos MD5,")
    print(f"consulta el archivo: {archivo_reporte}")
    print("")

if __name__ == "__main__":
    main()
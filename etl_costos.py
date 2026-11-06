# ==============================================================================
# PROCESO ETL DE COSTOS: INTEGRACIÓN DE REALES VS PRESUPUESTO Y CATÁLOGOS
# Autor: Juan Diego Gutiérrez Suárez
# Descripción: Script modular para la extracción, validación de formatos (CECO/Cuentas),
#              cruce de fuentes separadas y clasificación de desviaciones financieras.
# ==============================================================================

import pandas as pd
import re
import os

def validar_formato_ceco_cuenta(df, nombre_fuente):
    """
    Valida que los Centros de Costo (CECO) y las Cuentas Contables cumplan 
    estrictamente con las reglas de negocio de longitud y formato numérico:
    - CECO: Exactamente 4 dígitos numéricos.
    - Cuenta: Exactamente 7 dígitos numéricos (sin letras ni caracteres extraños).
    """
    print(f"[VALIDACIÓN] Analizando integridad de formatos en: {nombre_fuente}")
    
    # Expresiones regulares para asegurar patrones estrictos
    patron_ceco = re.compile(r'^\d{4}$')
    patron_cuenta = re.compile(r'^\d{7}$')
    
    # Filtrado estricto mediante match de expresiones regulares
    df_valido = df[
        df['ceco'].astype(str).str.match(patron_ceco) & 
        df['cuenta'].astype(str).str.match(patron_cuenta)
    ].copy()
    
    # Auditoría de registros descartados por errores humanos de dedo
    registros_descartados = len(df) - len(df_valido)
    if registros_descartados > 0:
        print(f"  -> Alerta: Se descartaron {registros_descartados} registros en '{nombre_fuente}' por formato inválido.")
        
    return df_valido

def ejecutar_pipeline_costos():
    print("=== INICIANDO PIPELINE DE INTEGRACIÓN DE COSTOS (MENSUAL) ===")
    
    # --------------------------------------------------------------------------
    # 1. FASE DE EXTRACCIÓN 
    # --------------------------------------------------------------------------
    try:
        df_real = pd.read_csv("data/real_mes.csv")
        df_ppto = pd.read_csv("data/ppto_mes.csv")
        df_catalogo = pd.read_csv("data/catalogo_maestro.csv")
    except FileNotFoundError as e:
        print(f"Error crítico: No se encontró algún archivo de datos necesario. Detalle: {e}")
        return

    # Estandarización preliminar de espacios en blanco en las llaves de cruce
    for df in [df_real, df_ppto]:
        df['ceco'] = df['ceco'].astype(str).str.strip()
        df['cuenta'] = df['cuenta'].astype(str).str.strip()

    # --------------------------------------------------------------------------
    # 2. FASE DE VALIDACIÓN Y LIMPIEZA DE FORMATOS
    # --------------------------------------------------------------------------

    df_real = validar_formato_ceco_cuenta(df_real, "Transacciones Reales")
    df_ppto = validar_formato_ceco_cuenta(df_ppto, "Presupuesto Autorizado")

    # --------------------------------------------------------------------------
    # 3. FASE DE TRANSFORMACIÓN Y AGRUPACIÓN POR MES 
    # --------------------------------------------------------------------------
    print(" Agrupando montos por Periodo (Mes), CECO y Cuenta Contable...")
    
    # Agrupación del consumo real mensual
    df_real_grp = df_real.groupby(['mes', 'ceco', 'cuenta'], as_index=False)['monto_real'].sum()
    
    # Agrupación del presupuesto planeado mensual
    df_ppto_grp = df_ppto.groupby(['mes', 'ceco', 'cuenta'], as_index=False)['monto_ppto'].sum()

    # --------------------------------------------------------------------------
    # 4. CRUCE DE FUENTES Y CLASIFICACIÓN FINANCIERA
    # --------------------------------------------------------------------------
    
    # Outer join para conservar los gastos reales incluso si no existían en el presupuesto
    df_consolidado = pd.merge(
        df_real_grp,
        df_ppto_grp,
        on=['mes', 'ceco', 'cuenta'],
        how='outer'
    )

    # Rellenar nulos con ceros para operaciones matemáticas estables
    df_consolidado['monto_ppto'] = df_consolidado['monto_ppto'].fillna(0)
    df_consolidado['monto_real'] = df_consolidado['monto_real'].fillna(0)

    # Regla de negocio: Clasificación del comportamiento del gasto
    def clasificar_estatus(row):
        if row['monto_ppto'] == 0 and row['monto_real'] > 0:
            return 'NO PRESUPUESTADO'
        elif row['monto_real'] > row['monto_ppto']:
            return 'SOBREPRESUPUESTO'
        else:
            return 'EN ORDEN / AHORRO'

    df_consolidado['estatus_gasto'] = df_consolidado.apply(clasificar_estatus, axis=1)

    # Limpieza de llaves en el catálogo maestro oficial
    df_catalogo['ceco'] = df_catalogo['ceco'].astype(str).str.strip()
    df_catalogo['cuenta'] = df_catalogo['cuenta'].astype(str).str.strip()

    # Cruce left join para traer las descripciones oficiales del catálogo
    df_final = pd.merge(
        df_consolidado,
        df_catalogo[['ceco', 'cuenta', 'nombre_ceco', 'descripcion_cuenta']],
        on=['ceco', 'cuenta'],
        how='left'
    )

    # Cálculo financiero de la variación neta (Real menos Presupuesto)
    df_final['variacion_neta'] = df_final['monto_real'] - df_final['monto_ppto']
    df_final['porcentaje_cumplimiento'] = round(
        (df_final['monto_real'] / df_final['monto_ppto'].replace(0, 1)) * 100, 2
    )

    # --------------------------------------------------------------------------
    # 5. FASE DE CARGA Y EXPORTACIÓN (Load)
    # --------------------------------------------------------------------------
    os.makedirs("output", exist_ok=True)
    ruta_salida = "output/reporte_costos_consolidado_mensual.csv"
    df_final.to_csv(ruta_salida, index=False)
    
    print(f" ¡Proceso ETL finalizado con éxito!")
    print(f"  -> Archivo maestro generado: {ruta_salida}")
    print(f"  -> Total de registros consolidados: {len(df_final)}")

if __name__ == "__main__":
    ejecutar_pipeline_costos()
# python-cost-cleaning-pipeline (Pipeline de Limpieza y Cruce de Costos en Python)

Script desarrollado para automatizar la integracion, validacion de formatos y cruce de reportes de costos operativos a partir de fuentes separadas.

## Problema que resuelve
En la gestion de costos, los registros de gastos reales y los presupuestos suelen encontrarse en archivos independientes. Ademas, es comun encontrar errores de captura (espacios en blanco, letras en campos numericos o longitudes incorrectas). Este script automatiza:
- Validacion estricta de formatos mediante expresiones regulares (centros de costo a 4 digitos y cuentas contables a 7 digitos).
- Cruce de fuentes separadas (consumo real frente a presupuesto) utilizando llaves maestras.
- Clasificacion automatizada del comportamiento del gasto (en orden, sobrepresupuesto o no presupuestado).
- Enriquecimiento de datos mediante un catalogo maestro oficial para inyectar descripciones y nombres oficiales.

## Tecnologias utilizadas
- Python
- Pandas
- Modulo Re (Expresiones regulares)

## Estructura del proyecto 

python-cost-cleaning-pipeline/
│
├── data/
│   ├── real_mes.csv          # Transacciones reales de gastos
│   ├── ppto_mes.csv          # Presupuesto autorizado
│   └── catalogo_maestro.csv  # Catalogo de centros de costo y cuentas
├── output/
│   └── reporte_costos_consolidado_mensual.csv  # Archivo maestro final depurado
├── etl_costos.py             # Script principal del proceso
├── requirements.txt          # Dependencias
└── README.md

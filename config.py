import os

NEGOCIO = os.getenv("NEGOCIO", "barbería")
DURACION_TURNO = int(os.getenv("DURACION_TURNO", "60"))
HORA_APERTURA = int(os.getenv("HORA_APERTURA", "8"))
HORA_CIERRE = int(os.getenv("HORA_CIERRE", "18"))
DIAS_A_CONSULTAR = int(os.getenv("DIAS_A_CONSULTAR", "5"))

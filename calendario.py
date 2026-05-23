from datetime import datetime, timedelta, date, time, timezone
from googleapiclient.discovery import build
from auth_calendar import autenticar

HORA_APERTURA = 8
HORA_CIERRE = 18
DURACION_TURNO = 60
DIAS_A_CONSULTAR = 5


def obtener_service():
    creds = autenticar()
    return build("calendar", "v3", credentials=creds)


def obtener_eventos(service, dias=DIAS_A_CONSULTAR):
    now = datetime.now(timezone.utc)
    fin = now + timedelta(days=dias)
    eventos = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=fin.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    return eventos.get("items", [])


def slot_libre(service, fecha: str, hora: str) -> bool:
    inicio = datetime.fromisoformat(f"{fecha}T{hora}:00-03:00")
    fin = inicio + timedelta(minutes=DURACION_TURNO)
    eventos = obtener_eventos(service, dias=7)
    for ev in eventos:
        try:
            oci = datetime.fromisoformat(ev["start"].get("dateTime"))
            ocf = datetime.fromisoformat(ev["end"].get("dateTime"))
        except (ValueError, TypeError):
            continue
        if inicio < ocf and fin > oci:
            return False
    return True


def slots_libres(service=None):
    if service is None:
        service = obtener_service()
    eventos = obtener_eventos(service)

    ocupados = []
    for ev in eventos:
        inicio = ev["start"].get("dateTime", ev["start"].get("date"))
        fin = ev["end"].get("dateTime", ev["end"].get("date"))
        ocupados.append((inicio, fin))

    hoy = date.today()
    libres = []
    zona = timezone(timedelta(hours=-3))

    for i in range(DIAS_A_CONSULTAR):
        dia = hoy + timedelta(days=i)
        if dia.weekday() >= 5:
            continue
        hora_actual = time(HORA_APERTURA, 0)
        hora_fin_jornada = time(HORA_CIERRE, 0)

        while hora_actual < hora_fin_jornada:
            slot_start = datetime.combine(dia, hora_actual, tzinfo=zona)
            slot_end = slot_start + timedelta(minutes=DURACION_TURNO)

            if slot_end.time() > hora_fin_jornada:
                break

            libre = True
            for inicio, fin in ocupados:
                try:
                    oci = datetime.fromisoformat(inicio)
                    ocf = datetime.fromisoformat(fin)
                except ValueError:
                    continue
                if slot_start < ocf and slot_end > oci:
                    libre = False
                    try:
                        hora_actual = ocf.time()
                    except AttributeError:
                        pass
                    break

            if libre:
                libres.append(slot_start.isoformat())
                hora_actual = slot_end.time()

    return libres


def reservar_turno(fecha: str, hora: str, nombre: str, telefono: str) -> str:
    inicio = f"{fecha}T{hora}:00-03:00"
    fin_dt = datetime.fromisoformat(inicio) + timedelta(minutes=DURACION_TURNO)
    fin = fin_dt.isoformat()

    evento = {
        "summary": f"Turno: {nombre}",
        "description": f"Reservado por Bot Secretario. Tel: {telefono}",
        "start": {"dateTime": inicio, "timeZone": "America/Argentina/Buenos_Aires"},
        "end": {"dateTime": fin, "timeZone": "America/Argentina/Buenos_Aires"},
    }

    service = obtener_service()
    creado = service.events().insert(calendarId="primary", body=evento).execute()
    return creado.get("htmlLink")


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        link = reservar_turno(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "sin tel")
        print(f"Turno creado: {link}")
    else:
        for s in slots_libres():
            print(s)

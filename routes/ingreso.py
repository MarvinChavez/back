from fastapi import APIRouter, UploadFile, File, HTTPException, Depends,Query
from sqlalchemy.orm import Session
import pandas as pd
import aiofiles
from database import SessionLocal
from models import Auto, Ruta, Turno, Ingreso
from datetime import date
from typing import Optional, List
from sqlalchemy.sql import func
import math
from sqlalchemy import text
from schemas import RutaResponse,AutoResponse
from sqlalchemy import func
from collections import OrderedDict
from sqlalchemy import func
import os
from fastapi import Form
from sqlalchemy import tuple_

router = APIRouter()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Diccionario de abreviaciones de ciudades
ABREVIACIONES = {
    'TRUJILLO': 'TRUJ',
    'CAJAMARCA': 'CAXA',
    'JAEN': 'JAEN',
    'CHICLAYO': 'CHIC',
    'PIURA': 'PIUR',
    'LA VICTORIA': 'LIMA',
    'MORALES': 'TARA',
}

def case_ciudad(campo: str) -> str:
    """Genera la cláusula CASE para abreviar las ciudades."""
    case_statement = "CASE "
    for ciudad, abreviacion in ABREVIACIONES.items():
        case_statement += f"WHEN TRIM({campo}) = '{ciudad}' THEN '{abreviacion}' "
    case_statement += f"ELSE TRIM({campo}) END"
    return case_statement

@router.get("/bingresosruta")
def ingresos_por_ruta_hoy(
    fecha_inicio: Optional[date] = Query(None),
    servicio: Optional[str] = Query(None),
    empresa_id: Optional[int] = Query(None),  # Agregar empresa_id como parámetro
    db: Session = Depends(get_db)
):
    fecha = fecha_inicio if fecha_inicio else date.today()
    ciudad_inicial_case = case_ciudad("ruta.ciudad_inicial")
    ciudad_final_case = case_ciudad("ruta.ciudad_final")

    query_str = f"""
        SELECT 
            ruta.id AS ruta_id,
            CONCAT({ciudad_inicial_case}, ' - ', {ciudad_final_case}) AS ruta,
            SUM(ingreso.monto) AS total,
            SUM(ingreso.pasajero) AS total_pasajeros
        FROM ingreso
        JOIN ruta ON ingreso.ruta_id = ruta.id
        WHERE ingreso.fecha = :fecha
    """

    params = {"fecha": fecha}

    # Si se recibe empresa_id, agregarlo a la consulta
    if empresa_id:
        query_str += " AND ingreso.empresa_id = :empresa_id"
        params["empresa_id"] = empresa_id

    # Si se especifica un servicio, agregarlo a la consulta
    if servicio:
        query_str += " AND ingreso.servicio = :servicio"
        params["servicio"] = servicio.strip().replace("'", "") 

    query_str += """
        GROUP BY ruta.id, ruta.ciudad_inicial, ruta.ciudad_final
        ORDER BY total DESC
    """
    query = db.execute(text(query_str), params)
    ingresos = query.fetchall()

    print(f"Fecha inicio: {fecha_inicio}, Servicio: {servicio}, Empresa ID: {empresa_id}")

    # Calcular totales
    total_monto = sum(ingreso.total for ingreso in ingresos)
    total_pasajeros = sum(ingreso.total_pasajeros for ingreso in ingresos)

    return {
        "labels": [ingreso.ruta for ingreso in ingresos],
        "montos": [math.ceil(ingreso.total) for ingreso in ingresos],
        "pasajeros": [ingreso.total_pasajeros for ingreso in ingresos],
        "montoTotal": "{:,.0f}".format(math.ceil(total_monto)),  # Separador de miles
        "totalPasajeros": total_pasajeros
    }

@router.get("/bingresosoficina")
def ingresos_por_oficina_hoy(
    fecha_inicio: Optional[date] = Query(None),
    servicio: Optional[str] = Query(None),
    empresa_id: Optional[int] = Query(None),  # Agregado el parámetro empresa_id
    db: Session = Depends(get_db)
):
    fecha = fecha_inicio if fecha_inicio else date.today()
    ciudad_inicial_case = case_ciudad("ruta.ciudad_inicial")

    query_str = f"""
        SELECT 
            {ciudad_inicial_case} AS ciudad_inicial,
            SUM(ingreso.monto) AS total,
            SUM(ingreso.pasajero) AS total_pasajeros
        FROM ingreso
        JOIN ruta ON ingreso.ruta_id = ruta.id
        WHERE ingreso.fecha = :fecha
    """
    
    params = {"fecha": fecha}

    # Filtrar por servicio si es proporcionado
    if servicio:
        query_str += " AND ingreso.servicio = :servicio"
        params["servicio"] = servicio.strip().replace("'", "") 
    
    # Filtrar por empresa_id si es proporcionado
    if empresa_id:
        query_str += " AND ingreso.empresa_id = :empresa_id"
        params["empresa_id"] = empresa_id

    query_str += """
        GROUP BY ruta.ciudad_inicial
        ORDER BY total DESC
    """

    # Usar text() para que SQLAlchemy reconozca la consulta
    query = db.execute(text(query_str), params)
    ingresos = query.fetchall()

    # Calcular totales
    total_monto = sum(ingreso.total for ingreso in ingresos)
    total_pasajeros = sum(ingreso.total_pasajeros for ingreso in ingresos)

    return {
        "labels": [ingreso.ciudad_inicial for ingreso in ingresos],
        "montos": [math.ceil(ingreso.total) for ingreso in ingresos],
        "pasajeros": [ingreso.total_pasajeros for ingreso in ingresos],
        "montoTotal": "{:,.0f}".format(math.ceil(total_monto)),  # Formato con separador de miles
        "totalPasajeros": total_pasajeros
    }
@router.get("/bingresosturno")
def ingresos_por_turno_hoy(
    fecha_inicio: Optional[date] = Query(None),
    servicio: Optional[str] = Query(None),
    empresa_id: Optional[int] = Query(None),  # Agregado el parámetro empresa_id
    db: Session = Depends(get_db)
):
    fecha = fecha_inicio if fecha_inicio else date.today()
    ciudad_inicial_case = case_ciudad("ruta.ciudad_inicial")
    ciudad_final_case = case_ciudad("ruta.ciudad_final")

    query_str = f"""
        SELECT 
            CONCAT({ciudad_inicial_case}, ' - ', {ciudad_final_case}) AS ruta,
            turno.hora AS turno,
            SUM(ingreso.monto) AS total,
            SUM(ingreso.pasajero) AS total_pasajeros
        FROM ingreso
        JOIN ruta ON ingreso.ruta_id = ruta.id
        JOIN turno ON ingreso.turno_id = turno.id
        WHERE ingreso.fecha = :fecha
    """

    params = {"fecha": fecha}

    # Filtrar por servicio si es proporcionado
    if servicio:
        query_str += " AND ingreso.servicio = :servicio"
        params["servicio"] = servicio.strip().replace("'", "")
    
    # Filtrar por empresa_id si es proporcionado
    if empresa_id:
        query_str += " AND ingreso.empresa_id = :empresa_id"
        params["empresa_id"] = empresa_id

    query_str += """
        GROUP BY ruta.ciudad_inicial, ruta.ciudad_final, turno.hora
        ORDER BY total DESC
    """

    # Ejecutar la consulta con text()
    query = db.execute(text(query_str), params)
    ingresos = query.fetchall()

    # Calcular totales
    total_monto = sum(ingreso.total for ingreso in ingresos)
    total_pasajeros = sum(ingreso.total_pasajeros for ingreso in ingresos)

    return {
        "labels": [f"{ingreso.ruta} ({ingreso.turno})" for ingreso in ingresos],
        "montos": [math.ceil(ingreso.total) for ingreso in ingresos],
        "pasajeros": [ingreso.total_pasajeros for ingreso in ingresos],
        "montoTotal": "{:,.0f}".format(math.ceil(total_monto)),  # Formato con separador de miles
        "totalPasajeros": total_pasajeros
    }
@router.post("/upload-excel")
async def upload_excel(
    file: UploadFile = File(...),
    empresa_id: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        temp_file_path = f"temp_{file.filename}"
        async with aiofiles.open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            await temp_file.write(content)

        df = pd.read_excel(temp_file_path, engine="openpyxl", header=None)
        df = df.iloc[:, 5:16]

        expected_columns = [
            "serial1", "serial2", "proveedor", "placa", "pasajero",
            "fecha", "servicio", "hora_turno", "ciudad_inicial", "ciudad_final", "monto"
        ]
        df.columns = expected_columns

        for _, row in df.iterrows():
            if row.isnull().any():
                continue  # O puedes registrar el error y continuar

            serial = str(row["serial1"]).strip() + str(row["serial2"]).strip()
            proveedor = str(row["proveedor"]).strip()
            placa = str(row["placa"]).strip()
            pasajero = int(row["pasajero"])
            fecha = pd.to_datetime(row["fecha"]).date()
            servicio = str(row["servicio"]).strip()
            hora_turno = str(row["hora_turno"]).strip()
            ciudad_inicial = str(row["ciudad_inicial"]).strip()
            ciudad_final = str(row["ciudad_final"]).strip()
            monto = float(row["monto"])

            # AUTO
            auto = db.query(Auto).filter_by(placa=placa, empresa_id=empresa_id).first()
            if not auto:
                auto = Auto(placa=placa, proveedor=proveedor, empresa_id=empresa_id)
                db.add(auto)
                db.flush()

            # RUTA
            ruta = db.query(Ruta).filter_by(
                ciudad_inicial=ciudad_inicial,
                ciudad_final=ciudad_final,
                empresa_id=empresa_id
            ).first()
            if not ruta:
                ruta = Ruta(ciudad_inicial=ciudad_inicial, ciudad_final=ciudad_final, empresa_id=empresa_id)
                db.add(ruta)
                db.flush()

            # TURNO
            turno = db.query(Turno).filter_by(hora=hora_turno, empresa_id=empresa_id).first()
            if not turno:
                turno = Turno(hora=hora_turno, empresa_id=empresa_id)
                db.add(turno)
                db.flush()

            # INGRESO
            ingreso = Ingreso(
                auto=auto,
                ruta=ruta,
                turno=turno,
                fecha=fecha,
                monto=monto,
                servicio=servicio,
                serial=serial,
                pasajero=pasajero,
                empresa_id=empresa_id
            )
            db.add(ingreso)

        db.commit()
        return {"message": "Archivo procesado y datos guardados exitosamente (duplicados ignorados)"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {str(e)}")

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.get("/filtrar_ingresos")
def filtrar_ingresos(
    fecha_inicio: Optional[date] = Query(None), 
    fecha_fin: Optional[date] = Query(default=date.today()),  # 🔹 Corregido
    servicio: Optional[str] = Query(None),
    empresa_id: Optional[int] = Query(None),  # Agregado el parámetro empresa_id
    db: Session = Depends(get_db)
):
    query = db.query(
        func.date(Ingreso.fecha).label("fecha"),
        func.sum(Ingreso.monto).label("total"),
        func.sum(Ingreso.pasajero).label("total_pasajeros")
    ).group_by(func.date(Ingreso.fecha)).order_by("fecha")

    if fecha_inicio:
        query = query.filter(Ingreso.fecha.between(fecha_inicio, fecha_fin))
    else:
        query = query.filter(Ingreso.fecha <= fecha_fin)

    if servicio:
        servicio = servicio.strip().replace("'", "")  # 🔹 Elimina espacios, saltos de línea y comillas
        query = query.filter(Ingreso.servicio == servicio)

    # Filtrar por empresa_id si es proporcionado
    if empresa_id:
        query = query.filter(Ingreso.empresa_id == empresa_id)

    print(f"Fecha inicio: {fecha_inicio}, Fecha fin: {fecha_fin}, Servicio: '{servicio}', Empresa ID: {empresa_id}")

    ingresos = query.all()

    ingresosFormateados = [
        {"fecha": i.fecha, "monto": math.ceil(i.total), "pasajeros": i.total_pasajeros}
        for i in ingresos
    ]

    return {
        "ingresos": ingresosFormateados,
        "montoTotal": f"{sum(i.total for i in ingresos):,.0f}",
        "totalPasajeros": sum(i.total_pasajeros for i in ingresos),
    }

@router.get("/filtrar-oficina")
def filtrar_oficina(
    ciudades: List[str] = Query(..., description="Lista de ciudades a filtrar"),
    servicio: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    empresa_id: Optional[int] = Query(None),  # Agregado el parámetro empresa_id
    db: Session = Depends(get_db)
):
    # Construcción de la consulta
    query = (
        db.query(
            Ruta.ciudad_inicial,
            Ingreso.fecha,
            func.sum(Ingreso.monto).label("total_monto"),
            func.sum(Ingreso.pasajero).label("total_pasajeros")
        )
        .join(Ruta, Ingreso.ruta_id == Ruta.id)
        .filter(Ruta.ciudad_inicial.in_(ciudades))
    )

    # Filtros opcionales
    if servicio:
        query = query.filter(Ingreso.servicio == servicio)
    if fecha_inicio and fecha_fin:
        query = query.filter(Ingreso.fecha.between(fecha_inicio, fecha_fin))
    elif fecha_inicio:
        query = query.filter(Ingreso.fecha >= fecha_inicio)
    elif fecha_fin:
        query = query.filter(Ingreso.fecha <= fecha_fin)

    # Agregar filtro por empresa_id si es proporcionado
    if empresa_id:
        query = query.filter(Ingreso.empresa_id == empresa_id)

    resultados = query.group_by(Ruta.ciudad_inicial, Ingreso.fecha).order_by(Ruta.ciudad_inicial, Ingreso.fecha).all()

    # Si no hay resultados, devolver valores vacíos
    if not resultados:
        return {"ciudades": [], "total_general": 0, "total_pasajeros": 0}

    ciudades_resultados = []
    total_general = 0
    total_pasajeros = 0

    for ciudad in ciudades:
        datos_ciudad = [r for r in resultados if r.ciudad_inicial.strip().upper() == ciudad.strip().upper()]

        fechas = [r.fecha for r in datos_ciudad]
        montos = [round(r.total_monto) for r in datos_ciudad]
        pasajeros = [r.total_pasajeros for r in datos_ciudad]

        monto_total_ciudad = sum(montos)
        pasajeros_ciudad = sum(pasajeros)
        promedio = round(monto_total_ciudad / len(montos), 0) if montos else 0

        ultimo_registro = datos_ciudad[-1] if datos_ciudad else None
        ultima_fecha = ultimo_registro.fecha if ultimo_registro else None
        ultimo_monto = round(ultimo_registro.total_monto, 2) if ultimo_registro else None

        ciudades_resultados.append({
            "ciudad_inicial": ABREVIACIONES.get(ciudad.strip().upper(), ciudad.strip().upper()),
            "montoTotal": f"{monto_total_ciudad:,}",
            "fechas": fechas,
            "montos": montos,
            "pasajeros": pasajeros,
            "promedio": promedio,
            "ultimo_registro": {"fecha": ultima_fecha, "monto": ultimo_monto},
            "total_pasajeros": pasajeros_ciudad
        })

        total_general += monto_total_ciudad
        total_pasajeros += pasajeros_ciudad

    return {
        "ciudades": ciudades_resultados,
        "total_general": f"{total_general:,}",
        "total_pasajeros": total_pasajeros
    }
@router.get("/filtrar-ruta")
def filtrar_ruta(
    rutas: List[int] = Query(..., title="Lista de IDs de rutas"),
    servicio: Optional[str] = Query(None, title="Servicio opcional"),
    fecha_inicio: Optional[str] = Query(None, title="Fecha de inicio"),
    fecha_fin: Optional[str] = Query(None, title="Fecha de fin"),
    empresa_id: Optional[int] = Query(None, title="ID de la empresa"),
    db: Session = Depends(get_db)
):
    query = (
        db.query(
            Ingreso.ruta_id,
            Ingreso.fecha,
            func.sum(Ingreso.monto).label("total_monto"),
            func.sum(Ingreso.pasajero).label("total_pasajeros"),
            Ruta.ciudad_inicial,
            Ruta.ciudad_final,
        )
        .join(Ruta, Ingreso.ruta_id == Ruta.id)
        .filter(Ingreso.ruta_id.in_(rutas))
    )

    # Filtros opcionales
    if servicio:
        query = query.filter(Ingreso.servicio == servicio)
    if fecha_inicio and fecha_fin:
        query = query.filter(Ingreso.fecha.between(fecha_inicio, fecha_fin))
    elif fecha_inicio:
        query = query.filter(Ingreso.fecha >= fecha_inicio)
    elif fecha_fin:
        query = query.filter(Ingreso.fecha <= fecha_fin)

    if empresa_id:
        query = query.filter(Ingreso.empresa_id == empresa_id)

    resultados = query.group_by(
        Ingreso.ruta_id,
        Ingreso.fecha,
        Ruta.ciudad_inicial,
        Ruta.ciudad_final
    ).order_by(Ingreso.fecha).all()

    if not resultados:
        return {"rutas": []}

    abreviaciones = {
        'TRUJILLO': 'TRUJ', 'CAJAMARCA': 'CAXA', 'JAEN': 'JAEN',
        'CHICLAYO': 'CHIC', 'PIURA': 'PIUR', 'LA VICTORIA': 'LIMA', 'MORALES': 'TARA'
    }

    rutas_data = []
    total_general = 0
    total_general_pasajeros = 0

    for ruta_id in rutas:
        datos_ruta = [r for r in resultados if r.ruta_id == ruta_id]

        if not datos_ruta:
            continue

        fechas = [r.fecha for r in datos_ruta]
        montos_originales = [r.total_monto for r in datos_ruta]
        montos_redondeados = [round(m, 0) for m in montos_originales]
        pasajeros = [r.total_pasajeros for r in datos_ruta]
        total_montos = sum(montos_originales)
        total_pasajeros = sum(pasajeros)

        ciudad_inicial = abreviaciones.get(datos_ruta[0].ciudad_inicial.upper(), datos_ruta[0].ciudad_inicial)
        ciudad_final = abreviaciones.get(datos_ruta[0].ciudad_final.upper(), datos_ruta[0].ciudad_final)
        nombre_ruta = f"{ciudad_inicial} - {ciudad_final}"

        monto_promedio = round(total_montos / len(montos_originales)) if montos_originales else 0

        rutas_data.append({
            "nombre": nombre_ruta,
            "fechas": fechas,
            "montos": montos_redondeados,
            "pasajeros": pasajeros,
            "monto_promedio": monto_promedio,
            "ultimo_registro": {
                "fecha": datos_ruta[-1].fecha,
                "monto": datos_ruta[-1].total_monto,
            } if datos_ruta else None,
            "total": f"{total_montos:,.0f}",
            "total_pasajeros": total_pasajeros,
        })

        total_general += total_montos
        total_general_pasajeros += total_pasajeros

    return {
        "rutas": rutas_data,
        "total_general": f"{total_general:,.0f}",
        "total_pasajeros": total_general_pasajeros,
    }


@router.get("/filtrar-auto")
def filtrar_auto(
    autos: List[int] = Query(...),
    servicio: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    empresa_id: Optional[int] = Query(None, title="ID de la empresa"),  # Agregado el parámetro empresa_id
    db: Session = Depends(get_db)
):
    try:
        query = (
            db.query(
                Ingreso.auto_id,
                Auto.placa,
                func.sum(Ingreso.monto).label("total_monto"),
                func.sum(Ingreso.pasajero).label("total_pasajeros"),
                func.count(Ingreso.turno_id).label("total_turnos"),
                func.date(Ingreso.fecha).label("fecha")
            )
            .join(Auto, Ingreso.auto_id == Auto.id)
            .filter(Ingreso.auto_id.in_(autos))
        )

        # Filtros opcionales
        if servicio:
            query = query.filter(Ingreso.servicio == servicio)
        if fecha_inicio and fecha_fin:
            query = query.filter(Ingreso.fecha.between(fecha_inicio, fecha_fin))
        elif fecha_inicio:
            query = query.filter(Ingreso.fecha >= fecha_inicio)
        elif fecha_fin:
            query = query.filter(Ingreso.fecha <= fecha_fin)
        
        # Agregar filtro por empresa_id si es proporcionado
        if empresa_id:
            query = query.filter(Ingreso.empresa_id == empresa_id)

        query = query.group_by(Ingreso.auto_id, Auto.placa, "fecha").order_by("fecha")
        resultados = query.all()

        if not resultados:
            return {
                "autos": [],
                "total_general": 0,
                "total_pasajeros": 0,
                "total_turnos": 0,
            }

        autos_data = []
        total_general = 0
        total_pasajeros = 0
        total_turnos = 0

        for auto_id in autos:
            datos_auto = [res for res in resultados if res.auto_id == auto_id]
            
            if not datos_auto:
                continue

            fechas, montos, pasajeros, turnos = [], [], [], []
            total_montos, total_pasajeros_auto, total_turnos_auto = 0, 0, 0
            nombre_auto = datos_auto[0].placa
            ultimo_registro = None

            for resultado in datos_auto:
                fechas.append(resultado.fecha)
                montos.append(round(resultado.total_monto))
                pasajeros.append(resultado.total_pasajeros)
                turnos.append(resultado.total_turnos)
                total_montos += resultado.total_monto
                total_pasajeros_auto += resultado.total_pasajeros
                total_turnos_auto += resultado.total_turnos
                ultimo_registro = resultado

            monto_promedio = total_montos / len(montos) if montos else 0

            autos_data.append({
                "nombre": nombre_auto,
                "fechas": fechas,
                "montos": montos,
                "pasajeros": pasajeros,
                "turnos": turnos,
                "monto_promedio": round(monto_promedio, 0),
                "total_pasajeros": total_pasajeros_auto,
                "total_turnos": total_turnos_auto,
                "ultimo_registro": {
                    "fecha": ultimo_registro.fecha,
                    "monto": ultimo_registro.total_monto
                } if ultimo_registro else None,
                "total": f"{total_montos:,.0f}",
            })

            total_general += total_montos
            total_pasajeros += total_pasajeros_auto
            total_turnos += total_turnos_auto

        return {
            "autos": autos_data,
            "total_general": f"{total_general:,.0f}",
            "total_pasajeros": total_pasajeros,
            "total_turnos": total_turnos,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la solicitud: {str(e)}")

@router.get("/obtener_turnos_por_ruta")
def obtener_turnos_por_ruta(
    ruta_id: int = Query(...),  # Requerido
    servicio: Optional[str] = Query(None),  # Opcional
    db: Session = Depends(get_db)
):
    query = db.query(Ingreso.turno_id).filter(Ingreso.ruta_id == ruta_id).distinct()
    
    if servicio and servicio != "Total":
        query = query.filter(Ingreso.servicio == servicio)

    print(f"Ruta ID: {ruta_id}, Servicio: {servicio}")

    turnos_ids = [t[0] for t in query.all()]

    if not turnos_ids:
        return []

    turnos_detalles = db.query(Turno).filter(Turno.id.in_(turnos_ids)).order_by(Turno.hora).all()

    return turnos_detalles


@router.get("/ingresos_turno")
def obtener_ingresos_filtrados(
    idRuta: int,
    empresa_id: int,  # ✅ Nuevo parámetro obligatorio
    servicio: Optional[str] = None,
    turnos: List[int] = Query(...),
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if not turnos:
        raise HTTPException(status_code=400, detail="La lista de turnos es obligatoria")

    query = db.query(
        Ingreso.turno_id,
        Turno.hora,
        func.sum(Ingreso.monto).label("total_monto"),
        func.sum(Ingreso.pasajero).label("total_pasajeros"),
        func.date(Ingreso.fecha).label("fecha")
    ).join(Turno, Ingreso.turno_id == Turno.id) \
     .filter(
         Ingreso.turno_id.in_(turnos),
         Ingreso.ruta_id == idRuta,
         Ingreso.empresa_id == empresa_id  # ✅ Se aplica el filtro por empresa
     )

    if servicio != "Total":
        query = query.filter(Ingreso.servicio == servicio)

    if fecha_inicio and fecha_fin:
        query = query.filter(Ingreso.fecha.between(fecha_inicio, fecha_fin))
    elif fecha_inicio:
        query = query.filter(Ingreso.fecha >= fecha_inicio)
    elif fecha_fin:
        query = query.filter(Ingreso.fecha <= fecha_fin)

    query = query.group_by(Ingreso.turno_id, Turno.hora, func.date(Ingreso.fecha)).order_by(func.date(Ingreso.fecha))

    resultados = query.all()

    if not resultados:
        return {
            "turnos": [],
            "total_general": 0,
            "total_pasajeros": 0,
        }

    turnos_respuesta = []
    total_general = 0
    total_pasajeros = 0

    for turno_id in turnos:
        datos_turno = [r for r in resultados if r.turno_id == turno_id]

        if not datos_turno:
            continue

        fechas, montos, cantidad_pasajeros = [], [], []
        total_montos = 0
        total_pasajeros_turno = 0
        ultimo_registro = None
        nombre_turno = ""

        for resultado in datos_turno:
            fechas.append(resultado.fecha)
            montos.append(resultado.total_monto)
            cantidad_pasajeros.append(resultado.total_pasajeros)
            total_montos += resultado.total_monto
            total_pasajeros_turno += resultado.total_pasajeros
            nombre_turno = resultado.hora
            ultimo_registro = resultado

        monto_promedio = total_montos / len(montos) if montos else 0

        turnos_respuesta.append({
            "nombre": nombre_turno or f"Turno {turno_id}",
            "fechas": fechas,
            "montos": montos,
            "total": f"{total_montos:,}",
            "pasajeros": cantidad_pasajeros,
            "total_pasajeros": total_pasajeros_turno,
            "monto_promedio": round(monto_promedio, 0),
            "ultimo_registro": {
                "fecha": ultimo_registro.fecha,
                "monto": ultimo_registro.total_monto,
            } if ultimo_registro else None
        })

        total_general += total_montos
        total_pasajeros += total_pasajeros_turno

    return {
        "turnos": turnos_respuesta,
        "total_general": f"{total_general:,}",
        "total_pasajeros": total_pasajeros,
    }

@router.get("/ciudades", response_model=List[str])
def obtener_ciudades(
    empresa_id: int,
    db: Session = Depends(get_db)
):
    ciudades = db.query(Ruta.ciudad_inicial).filter(
        Ruta.empresa_id == empresa_id
    ).distinct().all()
    
    return [ciudad[0] for ciudad in ciudades]

@router.get("/rutas", response_model=List[RutaResponse])
def obtener_rutas(
    empresa_id: int,
    db: Session = Depends(get_db)
):
    rutas = db.query(Ruta.id, Ruta.ciudad_inicial, Ruta.ciudad_final).\
        filter(Ruta.empresa_id == empresa_id).\
        distinct().all()

    return [
        RutaResponse(
            id=ruta[0], 
            ciudad_inicial=ABREVIACIONES.get(ruta[1].upper(), ruta[1]), 
            ciudad_final=ABREVIACIONES.get(ruta[2].upper(), ruta[2])
        ) 
        for ruta in rutas
    ]

@router.get("/autos", response_model=List[AutoResponse])
def obtener_autos(
    empresa_id: int,
    db: Session = Depends(get_db)
):
    autos = db.query(Auto.id, Auto.placa).\
        filter(Auto.empresa_id == empresa_id).\
        distinct().all()

    return [
        AutoResponse(
            id=auto[0], 
            placa=auto[1]
        ) 
        for auto in autos
    ]

@router.get("/pieingresos_rutas")
def ingresos_por_rutas(
    empresa_id: int,  # ✅ Nuevo parámetro obligatorio
    rutas: List[int] = Query(...),
    fecha_inicio: str = Query(...),
    fecha_fin: str = Query(...),
    servicio: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = (
        db.query(
            Ingreso.ruta_id,
            func.sum(Ingreso.monto).label("total_monto"),
            func.sum(Ingreso.pasajero).label("total_pasajeros")
        )
        .filter(
            Ingreso.ruta_id.in_(rutas),
            Ingreso.fecha.between(fecha_inicio, fecha_fin),
            Ingreso.empresa_id == empresa_id  # ✅ Filtro por empresa
        )
    )

    if servicio and servicio != "Total":
        query = query.filter(Ingreso.servicio == servicio)

    resultados = query.group_by(Ingreso.ruta_id).all()

    total_general = sum(res.total_monto for res in resultados) if resultados else 0
    total_pasajeros_general = sum(res.total_pasajeros for res in resultados) if resultados else 0

    data = []
    for resultado in resultados:
        ruta = db.query(Ruta).filter(Ruta.id == resultado.ruta_id).first()
        if ruta:
            ciudad_inicial = ruta.ciudad_inicial.strip().upper()
            ciudad_final = ruta.ciudad_final.strip().upper()
            rutainicial = ABREVIACIONES.get(ciudad_inicial, ciudad_inicial)
            rutafinal = ABREVIACIONES.get(ciudad_final, ciudad_final)
        
            porcentaje = (resultado.total_monto / total_general * 100) if total_general > 0 else 0

            data.append({
                "rutainicial": rutainicial,
                "rutafinal": rutafinal,
                "total_monto": resultado.total_monto,
                "total_pasajeros": resultado.total_pasajeros,
                "porcentaje": round(porcentaje, 2),
                "total_general": round(total_general, 2),
                "total_pasajeros_general": total_pasajeros_general
            })
    
    return data

@router.get("/pieingresos_autos")
def ingresos_por_autos(
    empresa_id: int,  # ✅ Nuevo parámetro obligatorio
    autos: List[int] = Query(...),
    fecha_inicio: str = Query(...),
    fecha_fin: str = Query(...),
    servicio: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = (
        db.query(
            Ingreso.auto_id, 
            func.sum(Ingreso.monto).label("total_monto"),
            func.sum(Ingreso.pasajero).label("total_pasajeros")
        )
        .filter(
            Ingreso.auto_id.in_(autos),
            Ingreso.fecha.between(fecha_inicio, fecha_fin),
            Ingreso.empresa_id == empresa_id  # ✅ Filtro por empresa
        )
    )

    if servicio and servicio != "Total":
        query = query.filter(Ingreso.servicio == servicio)

    resultados = query.group_by(Ingreso.auto_id).all()
    
    total_general = sum(r.total_monto for r in resultados) if resultados else 0
    total_pasajeros_general = sum(r.total_pasajeros for r in resultados) if resultados else 0

    data = []
    for resultado in resultados:
        auto = db.query(Auto).filter(Auto.id == resultado.auto_id).first()
        porcentaje = (resultado.total_monto / total_general * 100) if total_general > 0 else 0
        
        data.append({
            "placa": auto.placa if auto else "Desconocido",
            "total_monto": resultado.total_monto,
            "total_pasajeros": resultado.total_pasajeros,
            "porcentaje": round(porcentaje, 2),
            "total_general": round(total_general, 0),
            "total_pasajeros_general": total_pasajeros_general
        })
    
    return data

@router.get("/ingresos_rutas_auto")
def obtener_ingresos_por_rutas_por_auto(
    empresa_id: int = Query(..., description="ID de la empresa"),  # ✅ Nuevo parámetro obligatorio
    auto_id: int = Query(..., description="ID del auto"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha de inicio"),
    fecha_fin: Optional[str] = Query(None, description="Fecha de fin"),
    servicio: Optional[str] = Query(None, description="Tipo de servicio"),
    db: Session = Depends(get_db)
):
    query = db.query(
        Ruta.ciudad_inicial,
        Ruta.ciudad_final,
        func.count(Ingreso.turno_id).label("numero_turnos"),
        func.sum(Ingreso.monto).label("monto"),
        func.sum(Ingreso.pasajero).label("total_pasajeros")
    ).join(Ruta, Ingreso.ruta_id == Ruta.id)
    
    query = query.filter(
        Ingreso.auto_id == auto_id,
        Ingreso.empresa_id == empresa_id  # ✅ Filtro por empresa
    )
    
    if fecha_inicio:
        query = query.filter(Ingreso.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Ingreso.fecha <= fecha_fin)
    if servicio and servicio != "Total":
        query = query.filter(Ingreso.servicio == servicio)
    
    query = query.group_by(Ruta.ciudad_inicial, Ruta.ciudad_final)
    ingresos = query.all()

    labels, data, numero_turnos, pasajeros_por_ruta = [], [], [], []
    total_ingresos, total_pasajeros_general = 0, 0

    for ingreso in ingresos:
        ciudad_inicial = ABREVIACIONES.get(ingreso.ciudad_inicial.upper(), ingreso.ciudad_inicial.upper())
        ciudad_final = ABREVIACIONES.get(ingreso.ciudad_final.upper(), ingreso.ciudad_final.upper())
        
        labels.append(f"{ciudad_inicial} - {ciudad_final}")
        data.append(ingreso.monto)
        numero_turnos.append(ingreso.numero_turnos)
        pasajeros_por_ruta.append(ingreso.total_pasajeros)
        total_ingresos += ingreso.monto
        total_pasajeros_general += ingreso.total_pasajeros

    return {
        "labels": labels,
        "data": data,
        "numeroTurnos": numero_turnos,
        "pasajerosPorRuta": pasajeros_por_ruta,
        "total": total_ingresos,
        "total_pasajeros_general": total_pasajeros_general,
    }

@router.get("/comparaciontotales")
def comparar_ingresos(
    empresa_id: int,
    fecha_inicio_1: date,
    fecha_fin_1: date,
    fecha_inicio_2: date,
    fecha_fin_2: date,
    db: Session = Depends(get_db)
):
    ingresos_rango_1 = db.query(
        Ingreso.fecha, 
        func.sum(Ingreso.pasajero).label("total_pasajeros"), 
        func.sum(Ingreso.monto).label("total_monto")
    ).filter(
        Ingreso.empresa_id == empresa_id,  # ✅ filtro por empresa
        Ingreso.fecha >= fecha_inicio_1,
        Ingreso.fecha <= fecha_fin_1
    ).group_by(Ingreso.fecha).order_by(Ingreso.fecha).all()

    ingresos_rango_2 = db.query(
        Ingreso.fecha, 
        func.sum(Ingreso.pasajero).label("total_pasajeros"), 
        func.sum(Ingreso.monto).label("total_monto")
    ).filter(
        Ingreso.empresa_id == empresa_id,  # ✅ filtro por empresa
        Ingreso.fecha >= fecha_inicio_2,
        Ingreso.fecha <= fecha_fin_2
    ).group_by(Ingreso.fecha).order_by(Ingreso.fecha).all()

    def procesar_ingresos(ingresos):
        total_pasajeros = sum(pasajeros for _, pasajeros, _ in ingresos)
        monto_total = sum(int(monto) for _, _, monto in ingresos)
        datos_por_fecha = {
            fecha: {"pasajeros": pasajeros, "monto": int(monto)} 
            for fecha, pasajeros, monto in ingresos
        }
        return total_pasajeros, monto_total, datos_por_fecha

    pasajeros_1, monto_1, datos_1 = procesar_ingresos(ingresos_rango_1)
    pasajeros_2, monto_2, datos_2 = procesar_ingresos(ingresos_rango_2)

    return {
        "rango_1": {"total_pasajeros": pasajeros_1, "monto_total": monto_1, "detalles": datos_1},
        "rango_2": {"total_pasajeros": pasajeros_2, "monto_total": monto_2, "detalles": datos_2}
    }

@router.get("/comparacionauto")
def comparar_ingresos(
    empresa_id: int,
    auto_id: int,
    fecha_inicio_1: date,
    fecha_fin_1: date,
    fecha_inicio_2: date,
    fecha_fin_2: date,
    db: Session = Depends(get_db)
):
    # Obtener ingresos del primer rango de fechas
    ingresos_rango_1 = db.query(
        Ingreso.fecha, 
        func.sum(Ingreso.pasajero).label("total_pasajeros"), 
        func.sum(Ingreso.monto).label("total_monto")
    ).filter(
        Ingreso.empresa_id == empresa_id,     # ✅ filtro por empresa
        Ingreso.auto_id == auto_id,
        Ingreso.fecha >= fecha_inicio_1,
        Ingreso.fecha <= fecha_fin_1
    ).group_by(Ingreso.fecha).order_by(Ingreso.fecha).all()

    # Obtener ingresos del segundo rango de fechas
    ingresos_rango_2 = db.query(
        Ingreso.fecha, 
        func.sum(Ingreso.pasajero).label("total_pasajeros"), 
        func.sum(Ingreso.monto).label("total_monto")
    ).filter(
        Ingreso.empresa_id == empresa_id,     # ✅ filtro por empresa
        Ingreso.auto_id == auto_id,
        Ingreso.fecha >= fecha_inicio_2,
        Ingreso.fecha <= fecha_fin_2
    ).group_by(Ingreso.fecha).order_by(Ingreso.fecha).all()

    # Procesar ingresos
    def procesar_ingresos(ingresos):
        total_pasajeros = sum(pasajeros for _, pasajeros, _ in ingresos)
        monto_total = sum(int(monto) for _, _, monto in ingresos)
        datos_por_fecha = {
            fecha: {"pasajeros": pasajeros, "monto": int(monto)} 
            for fecha, pasajeros, monto in ingresos
        }
        return total_pasajeros, monto_total, datos_por_fecha

    pasajeros_1, monto_1, datos_1 = procesar_ingresos(ingresos_rango_1)
    pasajeros_2, monto_2, datos_2 = procesar_ingresos(ingresos_rango_2)

    return {
        "rango_1": {"total_pasajeros": pasajeros_1, "monto_total": monto_1, "detalles": datos_1},
        "rango_2": {"total_pasajeros": pasajeros_2, "monto_total": monto_2, "detalles": datos_2}
    }

@router.get("/comparacionoficina")
def comparar_ingresos(
    empresa_id: int,
    oficina: str,
    fecha_inicio_1: date,
    fecha_fin_1: date,
    fecha_inicio_2: date,
    fecha_fin_2: date,
    db: Session = Depends(get_db)
):
    # Consultar ingresos para el primer rango de fechas
    ingresos_rango_1 = db.query(
        Ingreso.fecha, 
        func.sum(Ingreso.pasajero), 
        func.sum(Ingreso.monto)
    ).join(Ruta, Ingreso.ruta_id == Ruta.id).filter(
        Ingreso.empresa_id == empresa_id,          # ✅ filtro por empresa
        Ruta.ciudad_inicial == oficina,  
        Ingreso.fecha >= fecha_inicio_1,
        Ingreso.fecha <= fecha_fin_1
    ).group_by(Ingreso.fecha).all()

    # Consultar ingresos para el segundo rango de fechas
    ingresos_rango_2 = db.query(
        Ingreso.fecha, 
        func.sum(Ingreso.pasajero), 
        func.sum(Ingreso.monto)
    ).join(Ruta, Ingreso.ruta_id == Ruta.id).filter(
        Ingreso.empresa_id == empresa_id,          # ✅ filtro por empresa
        Ruta.ciudad_inicial == oficina,  
        Ingreso.fecha >= fecha_inicio_2,
        Ingreso.fecha <= fecha_fin_2
    ).group_by(Ingreso.fecha).all()

    # Procesar datos
    def procesar_ingresos(ingresos):
        total_pasajeros = sum(pasajeros for _, pasajeros, _ in ingresos)
        monto_total = sum(int(monto) for _, _, monto in ingresos)
        datos_por_fecha = {
            fecha: {"pasajeros": pasajeros, "monto": int(monto)} 
            for fecha, pasajeros, monto in ingresos
        }
        return total_pasajeros, monto_total, datos_por_fecha

    pasajeros_1, monto_1, datos_1 = procesar_ingresos(ingresos_rango_1)
    pasajeros_2, monto_2, datos_2 = procesar_ingresos(ingresos_rango_2)

    return {
        "rango_1": {"total_pasajeros": pasajeros_1, "monto_total": monto_1, "detalles": datos_1},
        "rango_2": {"total_pasajeros": pasajeros_2, "monto_total": monto_2, "detalles": datos_2}
    }

@router.get("/comparacionruta")
def comparar_ingresos(
    empresa_id: int,
    ruta_id: int,
    fecha_inicio_1: date,
    fecha_fin_1: date,
    fecha_inicio_2: date,
    fecha_fin_2: date,
    db: Session = Depends(get_db)
):
    ingresos_rango_1 = db.query(
        Ingreso.fecha, 
        func.sum(Ingreso.pasajero).label("total_pasajeros"), 
        func.sum(Ingreso.monto).label("total_monto")
    ).filter(
        Ingreso.empresa_id == empresa_id,      
        Ingreso.ruta_id == ruta_id,
        Ingreso.fecha >= fecha_inicio_1,
        Ingreso.fecha <= fecha_fin_1
    ).group_by(Ingreso.fecha).all()

    ingresos_rango_2 = db.query(
        Ingreso.fecha, 
        func.sum(Ingreso.pasajero).label("total_pasajeros"), 
        func.sum(Ingreso.monto).label("total_monto")
    ).filter(
        Ingreso.empresa_id == empresa_id,       
        Ingreso.ruta_id == ruta_id,
        Ingreso.fecha >= fecha_inicio_2,
        Ingreso.fecha <= fecha_fin_2
    ).group_by(Ingreso.fecha).all()

    def procesar_ingresos(ingresos):
        total_pasajeros = sum(pasajeros for _, pasajeros, _ in ingresos)
        monto_total = sum(int(monto) for _, _, monto in ingresos)
        datos_por_fecha = {
            fecha: {"pasajeros": pasajeros, "monto": int(monto)} 
            for fecha, pasajeros, monto in ingresos
        }
        return total_pasajeros, monto_total, datos_por_fecha

    pasajeros_1, monto_1, datos_1 = procesar_ingresos(ingresos_rango_1)
    pasajeros_2, monto_2, datos_2 = procesar_ingresos(ingresos_rango_2)

    return {
        "rango_1": {"total_pasajeros": pasajeros_1, "monto_total": monto_1, "detalles": datos_1},
        "rango_2": {"total_pasajeros": pasajeros_2, "monto_total": monto_2, "detalles": datos_2}
    }

@router.get("/ultima-fecha", response_model=dict[str, date])
def obtener_ultima_fecha(
    empresa_id: int = Query(..., description="ID de la empresa"),  # ✅ parámetro obligatorio
    db: Session = Depends(get_db)
):
    ultima_fecha = db.query(Ingreso.fecha).\
        filter(Ingreso.empresa_id == empresa_id).\
        order_by(Ingreso.fecha.desc()).\
        first()
        
    if ultima_fecha:
        return {"fecha": ultima_fecha[0]}
    return {"fecha": None}



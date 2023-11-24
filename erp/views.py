import os
import uuid
from django.db import connections
from django.shortcuts import render, redirect
from decimal import Decimal
from datetime import datetime, timedelta
import json
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.conf import settings
from django.http import JsonResponse
# Función para convertir objetos Decimal a números de punto flotante (float)
from erp_ishida.settings import BASE_DIR


def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


@login_required
def mq2010New(request):
    codtrans = 'feja'

    connection = connections['empresa']  # Asegúrate de reemplazar 'empresa' con el nombre correcto de tu base de datos.

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT codvendedor, Nombrevendedor, codlinea1, descripciongrupo1lineas, NombreCliente, FechaTrans, Cantidad*-1 as Cantidad, PrecioRealTotal*-1 as PrecioRealTotal, CostoRealTotal*-1 as CostoRealTotal, Utilidad*-1 as Utilidad FROM view_reports WHERE codtrans = %s",
            [codtrans])
        results = cursor.fetchall()
        results = sorted(results, key=lambda x: x[0])
        username = request.user
        # Obtén la fecha actual
        fecha_actual = datetime.now()
        primer_dia_mes_actual = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        fecha_dia_anterior = fecha_actual - timedelta(days=1)

        fecha_dia_anterior = fecha_dia_anterior.date()

        dias_hasta_inicio_semana = (fecha_actual.weekday() - 6) % 7
        fecha_inicio_semana = fecha_actual - timedelta(days=dias_hasta_inicio_semana)
        fecha_fin_semana = fecha_inicio_semana + timedelta(days=6)
        cursor.execute(
            "SELECT CONVERT(date, FechaTrans) as Fecha, SUM(PrecioRealTotal * -1) as VentasDiarias FROM view_reports WHERE FechaTrans BETWEEN %s AND %s AND codtrans = %s GROUP BY CONVERT(date, FechaTrans)",
            [fecha_inicio_semana, fecha_fin_semana, codtrans])
        ventas_diarias_semana = cursor.fetchall()

        fecha_hoy = datetime.now().strftime("%Y/%m/%d")
        cursor.execute(
            "SELECT COUNT(codtrans) as Ofertas FROM GNComprobante WHERE estado <> 3 and codtrans = 'ofd' AND fechatrans = %s",
            [fecha_hoy])
        ofertas_hoy = cursor.fetchone()
        cantidad_ofertas_hoy = ofertas_hoy[0] if ofertas_hoy else 0

        def serialize_date(date):
            if date is not None:
                return date.strftime("%Y-%m-%d")
            return None

        cursor.execute(
            "SELECT CONVERT(date, FechaTrans) as Fecha, SUM(PrecioRealTotal * -1) as VentasDiarias FROM view_reports WHERE FechaTrans = %s AND codtrans = %s GROUP BY CONVERT(date, FechaTrans)",
            [fecha_hoy, codtrans]
        )
        ventas_hoy = cursor.fetchone()
        ventas_hoy = ventas_hoy[1] if ventas_hoy else 0

        # Consulta para obtener las ventas del día anterior
        cursor.execute(
            "SELECT CONVERT(date, FechaTrans) as Fecha, SUM(PrecioRealTotal * -1) as VentasDiarias FROM view_reports WHERE FechaTrans = %s AND codtrans = %s GROUP BY CONVERT(date, FechaTrans)",
            [fecha_dia_anterior, codtrans]
        )
        ventas_dia_anterior = cursor.fetchone()
        ventas_dia_anterior = ventas_dia_anterior[1] if ventas_dia_anterior else 0

        # Calcular el porcentaje de cambio en una nueva variable
        cambio_porcentual_diario = 0
        if ventas_dia_anterior != 0:
            cambio_porcentual_diario = ((ventas_hoy - ventas_dia_anterior) / ventas_dia_anterior) * 100

        # Serializar las fechas en ventas_diarias_semana y ventas_diarias_semana_anterior
        ventas_diarias_semana_serialized = [
            {"Fecha": serialize_date(row[0]), "VentasDiarias": row[1]}
            for row in ventas_diarias_semana
        ]

        total_ventas_semana = sum(row["VentasDiarias"] for row in ventas_diarias_semana_serialized)

        cursor.execute(
            "SELECT Top 5 DescripcionItem, SUM(PrecioRealTotal * -1) AS Total "
            "FROM view_reports "
            "WHERE FechaTrans BETWEEN %s AND %s AND codtrans = %s "
            "GROUP BY DescripcionItem "
            "ORDER BY Total DESC ",
            [primer_dia_mes_actual, fecha_actual, codtrans]
        )
        productos_mas_vendidos = cursor.fetchall()

        # Convertir ventas_diarias_semana y ventas_diarias_semana_anterior a formato JSON
        ventas_diarias_semana_json = json.dumps(ventas_diarias_semana_serialized, cls=DjangoJSONEncoder)

        cursor.execute(
            "SELECT Codlinea1, SUM(PrecioRealTotal * -1) AS Total "
            "FROM view_reports "
            "WHERE FechaTrans BETWEEN %s AND %s AND codtrans = %s "
            "GROUP BY Codlinea1 "
            "ORDER BY Total DESC ",
            [primer_dia_mes_actual, fecha_actual, codtrans]
        )
        lineas_mas_vendidas = cursor.fetchall()

    año_actual = datetime.now().year
    año_anterior = año_actual - 1
    mes_actual = datetime.now().month

    ventas_mensual_año_actual = [0] * 12
    ventas_mensual_año_anterior = [0] * 12
    cambio_porcentual = 0
    prueba = 42.55
    ventas_totales_año_actual = 0
    ventas_totales_año_anterior = 0

    for fila in results:
        fecha_trans = fila[5]
        año = fecha_trans.year
        mes = fecha_trans.month
        precio = fila[7]

        if año == año_actual:
            ventas_mensual_año_actual[mes - 1] += precio
            ventas_totales_año_actual += precio
        elif año == año_anterior:
            ventas_mensual_año_anterior[mes - 1] += precio
            ventas_totales_año_anterior += precio

    if mes_actual > 1:
        mes_anterior = mes_actual - 1
        if ventas_mensual_año_actual[mes_anterior - 1] != 0:
            cambio_porcentual = ((ventas_mensual_año_actual[mes_actual - 1] - ventas_mensual_año_actual[
                mes_anterior - 1]) / ventas_mensual_año_actual[mes_anterior - 1]) * 100

    etiquetas_mes = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']

    contexto = {
        'username': username,
        'total_ventas_semana': total_ventas_semana,
        'etiquetas_mes': json.dumps(etiquetas_mes),
        'ventas_mensual_año_actual': json.dumps(ventas_mensual_año_actual, default=decimal_to_float),
        'ventas_mensual_año_anterior': json.dumps(ventas_mensual_año_anterior, default=decimal_to_float),
        'ventas_totales_año_actual': ventas_totales_año_actual,
        'ventas_totales_año_anterior': ventas_totales_año_anterior,
        'cambio_porcentual': cambio_porcentual,
        'prueba': prueba,
        'ventas_diarias_semana': ventas_diarias_semana_json,
        'año_actual': año_actual,
        'año_anterior': año_anterior,
        'cantidad_ofertas_hoy': cantidad_ofertas_hoy,
        'cambio_porcentual_diario': cambio_porcentual_diario,
        'productos_mas_vendidos': json.dumps(productos_mas_vendidos, default=decimal_to_float),
        'lineas_mas_vendidas': json.dumps(lineas_mas_vendidas, default=decimal_to_float)
    }

    print('lineas_mas_vendidas', productos_mas_vendidos)
    return render(request, 'mq2010New.html', contexto)


@login_required
def consgeneraltrans(request):
    connection = connections['empresa']
    username = request.user
    # Obtiene el valor de @CodTrans de la solicitud (puede provenir de un formulario o parámetro GET/POST)
    codtrans_param = request.GET.get('CodTrans',
                                     '')  # Obtiene el valor de la solicitud, o un valor por defecto en blanco
    estado_param = request.GET.getlist('Estado')

    fecha_desde = request.GET.get('fecha_desde', '')  # Obtener la fecha "Desde" del formulario
    fecha_hasta = request.GET.get('fecha_hasta', '')  # Obtener la fecha "Hasta" del formulario

    if not fecha_desde and not fecha_hasta:
        # Si no se proporcionan fechas, utiliza today_str por defecto
        today = date.today()
        today_str = today.strftime('%Y-%m-%d')
        fecha_desde = today_str
        fecha_hasta = today_str

    # Construye la consulta SQL para obtener una lista de transacciones únicas
    sql_query_unique_trans = """
        SELECT DISTINCT CodTrans AS Trans
        FROM gncomprobante
    """

    sql_query_unique_trans_estado = """
            SELECT DISTINCT
    CASE Estado
        WHEN 0 THEN 'No Aprobados'
        WHEN 1 THEN 'Aprobados'
        WHEN 2 THEN 'Despachados'
        WHEN 3 THEN 'Anulados'
        WHEN 4 THEN 'Semi Despachados'
        ELSE 'Otro'
    END AS EstadoL, Estado
FROM gncomprobante
ORDER BY Estado;
        """

    # Construye la consulta SQL dinámica en función de si se proporciona un valor para @CodTrans
    sql_query = """
            SELECT
                CONVERT(date,fechatrans) AS Fecha,
                codasiento AS Asiento,
                CodTrans AS Trans,
                NumTrans AS '#Trans',
                NumDocRef AS '#Ref',
                Nombre,
                descripcion,
                Estado,
                CASE
                    WHEN Estado = 0 THEN 'NOCOUNT'
                    WHEN Estado = 1 THEN 'APROV'
                    WHEN Estado = 2 THEN 'DESPA'
                    WHEN Estado = 3 THEN 'ANULA'
                    ELSE 'Desconocido'
                END AS Estadol, Enviado,informacionAdicional as MensajeComproanteElectronico 
            FROM vwconsgntrans
            WHERE fechatrans BETWEEN '{}' AND '{}'
        """.format(fecha_desde, fecha_hasta)

    if codtrans_param:
        # Agrega la condición para filtrar por CodTrans si se proporciona un valor
        sql_query += f"AND CodTrans = '{codtrans_param}'"

    if estado_param and '' not in estado_param:
        # Si no se ha seleccionado "Todos", agrega la condición para filtrar por Estado
        estados_condition = " OR ".join([f"Estado = '{estado}'" for estado in estado_param])
        sql_query += f"AND ({estados_condition})"

    # Realiza la consulta SQL a la base de datos para obtener transacciones únicas
    with connection.cursor() as cursor:
        cursor.execute(sql_query_unique_trans)
        unique_trans = [row[0] for row in cursor.fetchall()]

    # Realiza la consulta SQL a la base de datos para obtener estados únicas
    with connection.cursor() as cursor:
        cursor.execute(sql_query_unique_trans_estado)
        unique_trans_estado = [{'Estado': row[0], 'EstadoL': row[1]} for row in cursor.fetchall()]

    # Realiza la consulta SQL a la base de datos para obtener los detalles de las transacciones
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        results = cursor.fetchall()

    # Convierte los resultados a un formato serializable
    data = []
    for row in results:
        data.append({
            'Fecha': row[0].strftime("%Y-%m-%d"),  # Convierte a cadena de texto
            'Asiento': row[1],
            'Trans': row[2],
            '#Trans': row[3],
            '#Ref': row[4],
            'Nombre': row[5],
            'descripcion': row[6],
            'Estado': row[7],
            'Estadol': row[8],
            'Enviado': row[9],
            'Mensaje Comprobante Electrónico': row[10]

        })

    # Pasa los datos en un contexto y renderiza la plantilla
    context = {
        'username': username,
        'results_json': json.dumps(data),
        'unique_trans': unique_trans,
        'unique_trans_estado': unique_trans_estado,
    }

    return render(request, 'consgeneraltrans.html', context)


@login_required
def listaprecios(request):
    username = request.user

    context = {
        'username': username
    }
    return render(request, 'listaprecios.html', context)


def listapreciojson(request):
    coditem = request.GET.get('coditem', '')
    codalterno = request.GET.get('codalterno', '')
    descripcion = request.GET.get('descripcion', '')
    bodegas = request.GET.get('bodegas', '')
    tipo = request.GET.get('tipo', '')
    filtroitems = request.GET.get('filtroitems', '')

    # Construir la cláusula WHERE
    where_clause = "WHERE IVInventario.BandValida = 1 "
    if coditem:
        where_clause += "AND IVInventario.CodInventario LIKE '%%%s%%'" % coditem
    if codalterno:
        where_clause += "AND IVInventario.CodAlterno1 LIKE '%%%s%%'" % codalterno
    if descripcion:
        where_clause += "AND IVInventario.Descripcion LIKE '%%%s%%'" % descripcion
    if bodegas:
        where_clause += "AND Ivbodega.Idbodega IN (%s)" % bodegas
    if tipo:
        where_clause += "AND IVInventario.Tipo = %s" % tipo
    if filtroitems:
        resultados_ivgrupo1 = ivgrupo1_json(request).content.decode('utf-8')
        resultados_ivgrupo1 = json.loads(resultados_ivgrupo1)
        contiene_en_ivgrupo1 = any(item['CodGrupo1'] == filtroitems for item in resultados_ivgrupo1)
        print(contiene_en_ivgrupo1)

        resultados_ivgrupo2 = ivgrupo2_json(request).content.decode('utf-8')
        resultados_ivgrupo2 = json.loads(resultados_ivgrupo2)
        contiene_en_ivgrupo2 = any(item['CodGrupo2'] == filtroitems for item in resultados_ivgrupo2)
        print(contiene_en_ivgrupo2)

        resultados_ivgrupo6 = ivgrupo6_json(request).content.decode('utf-8')
        resultados_ivgrupo6 = json.loads(resultados_ivgrupo6)
        contiene_en_ivgrupo6 = any(item['CodGrupo6'] == filtroitems for item in resultados_ivgrupo6)
        print(contiene_en_ivgrupo6)

        if contiene_en_ivgrupo1:
            where_clause += "AND IVGrupo1.CodGrupo1 IN ('%s')" % filtroitems
        elif contiene_en_ivgrupo2:
            where_clause += "AND IVGrupo2.CodGrupo2 IN ('%s')" % filtroitems
        elif contiene_en_ivgrupo6:
            where_clause += "AND IVGrupo6.CodGrupo6 IN ('%s')" % filtroitems

    raw_sql_query = """
SELECT 
    IVGrupo1.CodGrupo1,
    IVGrupo1.Descripcion as DescripcionCodGrupo1,
    IVGrupo2.CodGrupo2,
    IVGrupo2.Descripcion as DescripcionCodGrupo2,
    IVGrupo4.CodGrupo4,
    IVInventario.CodInventario,
    IVInventario.Descripcion as DescripcionItem,
    IVUnidad.codUnidad,
    IVInventario.Precio1,
    ROUND((IVInventario.Precio1 * (1 + IVInventario.PorcentajeIVA)), 2) AS Precio1IVA,
    IVInventario.Precio2,
    ROUND((IVInventario.Precio2 * (1 + IVInventario.PorcentajeIVA)), 2) AS Precio2IVA,
    IVInventario.Precio3,
    ROUND((IVInventario.Precio3 * (1 + IVInventario.PorcentajeIVA)), 2) AS Precio3IVA,
    IVInventario.Precio4,
    ROUND((IVInventario.Precio4 * (1 + IVInventario.PorcentajeIVA)), 2) AS Precio4IVA,
    IVInventario.Precio5,
    ROUND((IVInventario.Precio5 * (1 + IVInventario.PorcentajeIVA)), 2) AS Precio5IVA,
    IVInventario.Precio6,
    ROUND((IVInventario.Precio6 * (1 + IVInventario.PorcentajeIVA)), 2) AS Precio6IVA,
    IVInventario.Precio7,
    ROUND((IVInventario.Precio7 * (1 + IVInventario.PorcentajeIVA)), 2) AS Precio7IVA,
    IVInventario.CodMoneda,
    SUM(IVExist.Exist) AS Existencia,
    ivinventario.observacion,
    ivinventario.pordesperdicio,
    IVInventario.Descripcion2 as Descripcion2,
    IVInventario.Tipo
FROM
    IVGrupo1
    RIGHT JOIN (
        IVGrupo2
        RIGHT JOIN (
            IVGrupo3
            RIGHT JOIN (
                IVGrupo4
                RIGHT JOIN (
                    IVGrupo5
                    RIGHT JOIN (
                        IVGrupo6  -- Agregado
                        RIGHT JOIN (
                            IVInventario
                            LEFT JOIN
                                IVExist
                                LEFT JOIN
                                    ivbodega
                                ON
                                    ivexist.idbodega = ivbodega.idbodega
                                ON
                                    IVInventario.IdInventario = IVExist.IDInventario
                        )
                        ON IVGrupo6.IdGrupo6 = IVInventario.IdGrupo6  -- Agregado
                    )
                    ON IVGrupo5.IdGrupo5 = IVInventario.IdGrupo5
                )
                ON IVGrupo4.IdGrupo4 = IVInventario.IdGrupo4
            )
            ON IVGrupo3.Idgrupo3 = IvInventario.Idgrupo3
        )
        ON IVGrupo2.Idgrupo2 = IvInventario.Idgrupo2
    )
    ON IVGrupo1.Idgrupo1 = IvInventario.Idgrupo1
LEFT JOIN IVUnidad ON IVUnidad.IdUnidad = IVinventario.idunidad
%s
GROUP BY
    IVGrupo1.CodGrupo1,
    IVGrupo1.Descripcion,
    IVGrupo2.CodGrupo2,
    IVGrupo2.Descripcion,
    IVGrupo3.CodGrupo3,
    IVGrupo3.Descripcion,
    IVGrupo4.CodGrupo4,
    IVGrupo4.Descripcion,
    IVGrupo5.CodGrupo5,
    IVGrupo5.Descripcion,
	IVGrupo6.CodGrupo6,
    IVGrupo6.Descripcion,
    IVInventario.CodInventario,
    IVInventario.CodAlterno1,
    IVInventario.Descripcion,
    IVUnidad.codUnidad,
    IVInventario.Precio1,
    (IVInventario.Precio1 * (1 + IVInventario.PorcentajeIVA)),
    IVInventario.Precio2,
    (IVInventario.Precio2 * (1 + IVInventario.PorcentajeIVA)),
    IVInventario.Precio3,
    (IVInventario.Precio3 * (1 + IVInventario.PorcentajeIVA)),
    IVInventario.Precio4,
    (IVInventario.Precio4 * (1 + IVInventario.PorcentajeIVA)),
    IVInventario.Precio5,
    (IVInventario.Precio5 * (1 + IVInventario.PorcentajeIVA)),
    IVInventario.Precio6,
    (IVInventario.Precio6 * (1 + IVInventario.PorcentajeIVA)),
    IVInventario.Precio7,
    (IVInventario.Precio7 * (1 + IVInventario.PorcentajeIVA)),
    IVInventario.CodMoneda,
    ivinventario.observacion,
    IVInventario.pordesperdicio,
    IVInventario.Descripcion2,
    IVInventario.Tipo
HAVING
    SUM(IVExist.Exist) > 0

    """ % where_clause
    connection = connections['empresa']

    with connection.cursor() as cursor:
        cursor.execute(raw_sql_query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    results = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(results, safe=False)


@login_required
def listaexistencia(request):
    username = request.user

    context = {
        'username': username
    }
    return render(request, 'listaexistencia.html', context)


def listaexistenciajson(request):
    coditem = request.GET.get('coditem', '')
    codalterno = request.GET.get('codalterno', '')
    descripcion = request.GET.get('descripcion', '')
    bodegas = request.GET.get('bodegas', '')
    tipo = request.GET.get('tipo', '')
    ctacontable = request.GET.get('ctacont', '')
    fecha_seleccionada = request.GET.get('fecha', '')  # Obtener la fecha seleccionada desde la solicitud
    filtroitems = request.GET.get('filtroitems', '')
    print('filtroitems',filtroitems)

    # Construir la cláusula WHERE
    where_clause = (
        "WHERE ((GNtrans.AfectaCantidad) = 1) "
        "AND GNComprobante.Estado <> 3 "
        "AND BandServicio = 0 "
    )
    if fecha_seleccionada:
        where_clause += "AND GNComprobante.FechaTrans <= '%s'" % fecha_seleccionada
    if coditem:
        where_clause += "AND IVInventario.CodInventario LIKE '%%%s%%'" % coditem
    if codalterno:
        where_clause += "AND IVInventario.CodAlterno1 LIKE '%%%s%%'" % codalterno
    if descripcion:
        where_clause += "AND IVInventario.Descripcion LIKE '%%%s%%'" % descripcion
    if bodegas:
        where_clause += "AND Ivbodega.Idbodega IN (%s)" % bodegas
    if tipo:
        where_clause += "AND IVInventario.Tipo = %s" % tipo
    if ctacontable:
        where_clause += "AND ct.codcuenta = '%s'" % ctacontable
    if filtroitems:
        resultados_ivgrupo1 = ivgrupo1_json(request).content.decode('utf-8')
        resultados_ivgrupo1 = json.loads(resultados_ivgrupo1)
        contiene_en_ivgrupo1 = any(item['CodGrupo1'] == filtroitems for item in resultados_ivgrupo1)
        print(contiene_en_ivgrupo1)

        resultados_ivgrupo2 = ivgrupo2_json(request).content.decode('utf-8')
        resultados_ivgrupo2 = json.loads(resultados_ivgrupo2)
        contiene_en_ivgrupo2 = any(item['CodGrupo2'] == filtroitems for item in resultados_ivgrupo2)
        print(contiene_en_ivgrupo2)

        resultados_ivgrupo6 = ivgrupo6_json(request).content.decode('utf-8')
        resultados_ivgrupo6 = json.loads(resultados_ivgrupo6)
        contiene_en_ivgrupo6 = any(item['CodGrupo6'] == filtroitems for item in resultados_ivgrupo6)
        print(contiene_en_ivgrupo6)
        if contiene_en_ivgrupo1:
            where_clause += "AND IVGrupo1.CodGrupo1 IN ('%s')" % filtroitems
        elif contiene_en_ivgrupo2:
            where_clause += "AND IVGrupo2.CodGrupo2 IN ('%s')" % filtroitems
        elif contiene_en_ivgrupo6:
            where_clause += "AND IVGrupo6.CodGrupo6 IN ('%s')" % filtroitems

    raw_sql_query = """
SELECT 
    IVGrupo1.CodGrupo1,
	IVInventario.CodInventario,
	IVInventario.Descripcion, 
	IVBodega.CodBodega,
	SUM(IVKardex.Cantidad) AS Existencia, 
	IVUnidad.CodUnidad as Uni,
	IVInventario.CodMoneda,
	IVInventario.Precio1,
	IVInventario.Precio2,
	IVInventario.Precio3,
	IVInventario.Precio4,
	IVInventario.Precio5,
	IVInventario.Precio6,
	0 AS Util6,
	IVInventario.Precio7,
	0 AS Util7,
	IVInventario.Observacion,
	CASE WHEN IVInventario.porcentajeiva = 0 THEN 'N' ELSE 'S' END AS IVA,
	IVInventario.porcentajeiva * 100 AS PorIVA,
	CantRelUni,
	CantRelUniCont,
	CASE 
        WHEN ISNULL(CantRelUni, 0) <> 0 THEN FLOOR(SUM(IVKardex.Cantidad) / CantRelUni) 
        ELSE FLOOR(SUM(IVKardex.Cantidad) / 1) 
    END AS ExistenciaCont,
	IVUc.CodUnidad,
	CASE 
        WHEN ISNULL(CantRelUni, 0) <> 0 THEN SUM(IVKardex.Cantidad) - (FLOOR(SUM(IVKardex.Cantidad) / CantRelUni)) * CantRelUni 
        ELSE SUM(IVKardex.Cantidad) - (FLOOR(SUM(IVKardex.Cantidad) / 1)) * CantRelUni 
    END AS CantRestoCont,
	CASE 
        WHEN ivinventario.IdCuentaActivo = ct.idcuenta THEN ct.codcuenta 
        ELSE 'Sin cuenta' 
    END AS codcuentaactivo,
	pesoneto, 
    pesobruto,
	ivexist.TiempoRep, 
    ivexist.Buffer,
	FechaUltimOIngreso, 
    FechaUltimOEgreso
FROM 
    IVGrupo1 
    RIGHT JOIN (
        IVGrupo2 
        RIGHT JOIN (
            IVGrupo3 
            RIGHT JOIN (
                IVGrupo4 
                RIGHT JOIN (
                    IVGrupo5 
                    RIGHT JOIN (
                        IVGrupo6 
                        RIGHT JOIN (
                            IVInventario 
                            LEFT JOIN ctcuenta ct ON ct.idcuenta = ivinventario.idcuentaactivo 
                            LEFT JOIN ivunidad ON ivunidad.idunidad = ivinventario.idunidad  
                            LEFT JOIN ivunidad ivuC ON ivuc.idunidad = ivinventario.idunidadconteo  
                            INNER JOIN (
                                IVBodega 
                                INNER JOIN (
                                    IVKardex 
                                    LEFT JOIN ivexist ON ivkardex.idinventario = ivexist.idinventario 
                                    AND ivkardex.idbodega = ivexist.idBodega 
                                    INNER JOIN (
                                        GNtrans 
                                        INNER JOIN GNComprobante ON GNtrans.Codtrans = GNCOmprobante.Codtrans
                                    ) ON IVKardex.transID = GNComprobante.transID
                                ) ON IVBodega.IdBodega = IVKArdex.IdBodega
                            ) ON IVInventario.IdInventario = IVKardex.IdInventario
                        ) ON IVGrupo6.IdGrupo6 = IVInventario.IdGrupo6
                    ) ON IVGrupo5.IdGrupo5 = IVInventario.IdGrupo5
                ) ON IVGrupo4.IdGrupo4 = IVInventario.IdGrupo4
            ) ON IVGrupo3.Idgrupo3 = IvInventario.Idgrupo3
        ) ON IVGrupo2.Idgrupo2 = IvInventario.Idgrupo2
    ) ON IVGrupo1.Idgrupo1 = IvInventario.Idgrupo1
%s
GROUP BY 
    IVGrupo1.CodGrupo1, 
    IVGrupo1.Descripcion, 
    IVGrupo2.CodGrupo2, 
    IVGrupo2.Descripcion, 
    IVGrupo3.CodGrupo3, 
    IVGrupo3.Descripcion, 
    IVGrupo4.CodGrupo4, 
    IVGrupo4.Descripcion, 
    IVGrupo5.CodGrupo5, 
    IVGrupo5.Descripcion, 
    IVGrupo6.CodGrupo6, 
    IVGrupo6.Descripcion, 
    IVInventario.CodInventario, 
    IVInventario.CodAlterno1, 
    IVInventario.CodAlterno2, 
    IVInventario.Descripcion, 
    IVinventario.m3, 
    IVBodega.CodBodega, 
    ivexist.TiempoRep, 
    ivexist.Buffer, 
    FechaUltimoIngreso, 
    FechaUltimoEgreso, 
    IVUnidad.CodUnidad, 
    IVInventario.CodMoneda, 
    IVInventario.Precio1, 
    IVInventario.Precio2, 
    IVInventario.Precio3, 
    IVInventario.Precio4, 
    IVInventario.Precio5, 
    IVInventario.Precio6, 
    IVInventario.Precio7, 
    IvInventario.Observacion, 
    IVUc.CodUnidad, 
    IVInventario.porcentajeiva, 
    CantRelUni, 
    CantRelUniCont, 
    IVInventario.CostoUltimoIngreso, 
    pesoneto, 
    pesobruto, 
    ivinventario.IdCuentaActivo, 
    ct.CodCuenta, 
    ct.IdCuenta 
HAVING 
    SUM(IVKardex.Cantidad) <> 0 
ORDER BY 
    IVGrupo1.Descripcion, 
    IVInventario.CodInventario, 
    IVBodega.CodBodega;""" % where_clause
    connection = connections['empresa']

    with connection.cursor() as cursor:
        cursor.execute(raw_sql_query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    results = [dict(zip(columns, row)) for row in rows]

    return JsonResponse(results, safe=False)



@login_required
def contact(request):
    username = request.user

    context = {
        'username': username
    }
    return render(request, 'contact.html', context)


@login_required
def facturacion(request):
    connection = connections['empresa1']
    username = request.user

    with connection.cursor() as cursor:
        cursor.execute("""
               SELECT gnt.codtrans, gnt.NumTransSiguiente, gnt.IdResponsablePre, gnr.codresponsable,gnt.MonedaPre,gnt.Descripcion
               FROM gntrans gnt
               INNER JOIN gnresponsable gnr ON gnr.idresponsable = gnt.IdResponsablePre
               WHERE gnt.codtrans = 'feja'
           """)

        # Recupera los resultados de la consulta
        results = cursor.fetchall()

        # Realiza la consulta SQL en la base de datos
        cursor.execute("""
                    SELECT 
                            ISNULL(fc.Nombre,'' ) as Vendedor,
                            pcpro.LimiteCredito,
                            pcpro.Diasplazo AS diascredito,
                            pcpro.nombre,
                            pcpro.Direccion1,
                            CONVERT(VARCHAR(MAX), DECRYPTBYPASSPHRASE('0102070612aq', pcpro.ruc)) AS ruc,
                            pcpro.telefono1,
                            pcpro.email,
                            pcpro.telefono3 AS celular,
                            pcpro.Observacion,
                            ISNULL(pcg1.descripcion, '') as pcgrupo1,
                            ISNULL(pcg2.descripcion, '') as pcgrupo2,
                            ISNULL(pcg3.descripcion, '') as pcgrupo3,
                            ISNULL(pcg4.descripcion, '') as pcgrupo4
                    FROM pcprovcli AS pcpro
                    LEFT JOIN pcgrupo1 AS pcg1 ON pcg1.idgrupo1 = pcpro.idgrupo1
                    LEFT JOIN pcgrupo2 AS pcg2 ON pcg2.idgrupo2 = pcpro.idgrupo2
                    LEFT JOIN pcgrupo3 AS pcg3 ON pcg3.idgrupo3 = pcpro.idgrupo3
                    LEFT JOIN pcgrupo4 AS pcg4 ON pcg4.idgrupo4 = pcpro.idGrupo4
                    Left JOIN FCVendedor as fc on fc.IdVendedor = pcpro.IdVendedor
                    WHERE pcpro.bandcliente = 1 AND pcpro.nombre LIKE '%%'
                """)
        pcprovcli_results = cursor.fetchall()

        data = []
        for row in pcprovcli_results:
            data.append({
                'vendedor': row[0],
                'limitecredito': row[1],
                'diascredito': row[2],
                'nombre': row[3],
                'Direccion1': row[4],
                'ruc': row[5],
                'telefono1': row[6],
                'email': row[7],
                'celular': row[8],
                'observacion': row[9],
                'pcgrupo1': row[10],
                'pcgrupo2': row[11],
                'pcgrupo3': row[12],
                'pcgrupo4': row[13]
            })

        cursor.execute("""
                    select EtiquetaPCGrupo1, EtiquetaPCGrupo2, EtiquetaPCGrupo3,EtiquetaAFGrupo4
                    from gnopcion""")
        etiquetaspcgrupos = cursor.fetchall()

        pcgrupos = []
        for row in etiquetaspcgrupos:
            pcgrupos.append({
                'pcgrupo1': row[0],
                'pcgrupo2': row[1],
                'pcgrupo3': row[2],
                'pcgrupo4': row[3]
            })

        cursor.execute("""
                select nombre from fcvendedor
        """)
        listavendedores = cursor.fetchall()

        listvend = []
        for row in listavendedores:
            listvend.append({
                'nombre': row[0],
            })

        cursor.execute("""
            SELECT
                iv.exist,
                p.idinventario as identificador, 
                p.codinventario as cod_item, 
                p.descripcion, 
                p.codalterno1 as cod_alterno, 
                p.observacion as observacion, 
                p.precio1, 
                p.precio2, 
                p.precio3, 
                p.precio4, 
                p.precio5, 
                p.precio6, 
                p.precio6, 
                p.precio7, 
                p.porcentajeiva as porc_iva, 
                p.bandiva as band_iva, 
                p.idgrupo1 as ivg1, 
                p.idgrupo2 as ivg2, 
                p.idgrupo3 as ivg3, 
                p.idgrupo4 as ivg4, 
                p.idgrupo5 as ivg5, 
                p.idgrupo6 as ivg6, 
                p.bandvalida as estado, 
                ivb.codbodega as codbodega,
                CASE 
                    WHEN p.descripcion2 IS NULL THEN '' 
                    ELSE p.descripcion2 
                END as presentacion,           
                p.fechagrabado as fecha_grabado, 
                p.descripciondetalle as descDetalle, 
                p.tipo
            FROM dbo.ivinventario p
            INNER JOIN dbo.ivexist iv ON p.idinventario = iv.idinventario
            INNER JOIN dbo.ivbodega ivb ON iv.idbodega = ivb.idbodega
            WHERE ivb.bandvalida = 1 and p.bandvalida = 1
                AND iv.exist > 0   
                AND iv.idbodega = (SELECT IdBodegaPre FROM gntrans WHERE codtrans = 'feja')
        """)
        consultasql = cursor.fetchall()

        factura = []
        for row in consultasql:
            factura.append({
                'exist': row[0],
                'identificador': row[1],
                'cod_item': row[2],
                'descripcion': row[3],
                'cod_alterno': row[4],
                'observacion': row[5],
                'precio1': row[6],
                'precio2': row[7],
                'precio3': row[8],
                'precio4': row[9],
                'precio5': row[10],
                'precio6': row[11],
                'precio7': row[12],
                'porc_iva': row[14],
                'bandiva': row[15],
                'estado': row[22],
                'bodega': row[23],
                'imagen': os.path.exists(os.path.join(settings.MEDIA_ROOT, 'imagenes', f"{row[2]}.jpg"))
                # Verifica si la imagen existe en el sistema de archivos

            })

    if request.method == 'POST':
        for producto in factura:
            cod_item = producto['cod_item']
            imagen = request.FILES.get(f'imagen_producto_{cod_item}')
            if imagen:
                with default_storage.open(f'imagenes/{cod_item}.jpg', 'wb') as destination:
                    for chunk in imagen.chunks():
                        destination.write(chunk)
                # Actualiza el campo "imagen" en el producto
                producto['imagen'] = True  # Indica que la imagen existe

    context = {
        'username': username,
        'results': results,  # Agrega los resultados al contexto
        'data': data,
        'pcgrupos': pcgrupos,
        'listvend': listvend,
        'factura': factura,
        'media_url': settings.MEDIA_URL

    }
    print(factura)
    return render(request, 'facturacion.html', context)


def infoempresa(request):
    connection = connections['empresa1']
    username = request.user

    if request.method == 'POST':
        # Procesa el formulario, incluyendo la carga de imagen
        nombreempresa = request.POST.get('nombreempresa')
        direccion1 = request.POST.get('direccion1')
        direccion2 = request.POST.get('direccion2')
        Telefono1 = request.POST.get('Telefono1')
        ruc = request.POST.get('ruc')
        email = request.POST.get('email')
        tipoempresa = request.POST.get('tipoempresa')

        # Obtiene la imagen cargada
        imagen = request.FILES.get('imagen')

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE GNOpcion SET nombreempresa = %s, direccion1 = %s, direccion2 = %s, Telefono1 = %s, ruc = %s, email = %s, tipoempresa = %s",
                (nombreempresa, direccion1, direccion2, Telefono1, ruc, email, tipoempresa))

        if imagen:
            # Verifica si la imagen existente debe eliminarse
            if default_storage.exists('empresa_imagen.png'):
                default_storage.delete('empresa_imagen.png')
                # Guarda la nueva imagen en el almacenamiento
            default_storage.save('empresa_imagen.png', imagen)

        messages.success(request, 'Información de la empresa actualizada exitosamente.')
        return redirect('infoempresa')

    else:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT nombreempresa, direccion1, direccion2, Telefono1, ruc, email, tipoempresa FROM GNOpcion")
            empresa_data = cursor.fetchone()

    # Obtiene la URL de la imagen si existe
    imagen_url = default_storage.url('empresa_imagen.png') if default_storage.exists('empresa_imagen.png') else None

    context = {
        'username': username,
        'empresa_data': empresa_data,
        'imagen_url': imagen_url,
    }

    return render(request, 'infoempresa.html', context)


###------BACKENDJSON--------###


def ivgrupo1_json(request):
    # Definir tu consulta SQL
    sql_query = "SELECT IVGrupo1.*, gnopcion.etiquetagrupo1 FROM IVGrupo1, gnopcion;"
    connection = connections['empresa']
    # Ejecutar la consulta
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Devolver los resultados como JSON
    return JsonResponse(results, safe=False)


def ivgrupo2_json(request):
    # Definir tu consulta SQL
    sql_query = "SELECT IVGrupo2.*, gnopcion.etiquetagrupo2 FROM IVGrupo2, gnopcion;"
    connection = connections['empresa']
    # Ejecutar la consulta
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]


    # Devolver los resultados como JSON junto con la verificación
    return JsonResponse(results, safe=False)



def ivgrupo6_json(request):
    # Definir tu consulta SQL
    sql_query = "SELECT IVGrupo6.*, gnopcion.etiquetagrupo6 FROM IVGrupo6, gnopcion;"
    connection = connections['empresa']
    # Ejecutar la consulta
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Devolver los resultados como JSON
    return JsonResponse(results, safe=False)


def obtener_ctacontable(request):
    # Obtener una conexión a la base de datos
    connection = connections['empresa']
    with connection.cursor() as cursor:
        # Ejecutar la consulta SQL
        cursor.execute('SELECT * FROM CTCUENTA WHERE NIVEL IN  (1,2,3,4,5) AND BandTotal = 0 order by CodCuenta')

        # Obtener los resultados de la consulta
        resultados = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

    # Devolver los resultados en formato JSON
    return JsonResponse(resultados, safe=False)


def obtener_bodegas(request):
    # Obtener una conexión a la base de datos
    connection = connections['empresa']
    with connection.cursor() as cursor:
        # Ejecutar la consulta SQL
        cursor.execute('SELECT * FROM IVBodega')

        # Obtener los resultados de la consulta
        resultados = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]

    # Devolver los resultados en formato JSON
    return JsonResponse(resultados, safe=False)
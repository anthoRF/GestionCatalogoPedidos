"""Caso reproducible: los resultados se calculan con las clases de la plataforma."""
from decimal import Decimal as D

from tienda.carrito import Carrito, Recomendaciones, Stock
from tienda.facturas import EmisorExportacion, EmisorNacional, EmisorSimplificado
from tienda.pedidos import Pedido
from tienda.precios import Catalogo, Descuento, Envio, Impuesto, Producto


def escenario():
    catalogo = Catalogo()
    for producto in (Producto("TEC", "Teclado mecánico", "Periféricos", D("100")),
                     Producto("RAT", "Ratón óptico", "Periféricos", D("25")),
                     Producto("ALF", "Alfombrilla", "Periféricos", D("12")),
                     Producto("SOP", "Soporte de monitor", "Escritorio", D("32"))):
        catalogo.registrar(producto)
    stock = Stock({"TEC": 4, "RAT": 3, "ALF": 6, "SOP": 2})
    carrito, recomendaciones = nuevo_carrito(catalogo, stock)
    return catalogo, stock, carrito, recomendaciones


def nuevo_carrito(catalogo, stock):
    carrito = Carrito(stock)
    recomendaciones = Recomendaciones(catalogo)
    carrito.suscribir(recomendaciones)
    return carrito, recomendaciones


def teclado_con_ajustes(producto):
    rebajado = Descuento(producto, D("0.10"))
    gravado = Impuesto(rebajado, D("0.10"))
    con_envio = Envio(gravado, D("5"))
    return rebajado, gravado, con_envio


def demostrar() -> dict:
    catalogo, stock, carrito, recomendaciones = escenario()
    teclado, raton = catalogo.buscar("TEC"), catalogo.buscar("RAT")
    rebajado, gravado, con_envio = teclado_con_ajustes(teclado)
    pasos = []

    def estado(accion):
        pasos.append({
            "accion": accion, "contenido": [l.articulo.producto_base().codigo for l in carrito.lineas()],
            "total_usd": str(carrito.total()),
            "stock_libre": {p.codigo: stock.disponibles(p.codigo) for p in (teclado, raton)},
            "sugerencias": [p.codigo for p in recomendaciones.sugerir()],
        })

    estado("Carrito vacío")
    carrito.agregar(con_envio)
    estado("Agregar TEC")
    id_raton = carrito.agregar(raton)
    estado("Agregar RAT")
    carrito.eliminar(id_raton)
    estado("Eliminar RAT")
    nacional = Pedido.desde_carrito("CP2-001", carrito)
    documentos = [nacional.facturar(EmisorNacional())]
    # Cada alternativa parte de un pedido propio con el mismo artículo y precio.
    for numero, emisor in (("CP2-002", EmisorExportacion("Lima, Perú")),
                           ("CP2-003", EmisorSimplificado())):
        otro_catalogo, _, otro_carrito, _ = escenario()
        otro_carrito.agregar(teclado_con_ajustes(otro_catalogo.buscar("TEC"))[-1])
        documentos.append(Pedido.desde_carrito(numero, otro_carrito).facturar(emisor))
    return {
        "moneda": "USD",
        "precios": {"base": str(teclado.precio_base), "con_descuento": str(rebajado.calcular_precio()),
                    "con_impuesto": str(gravado.calcular_precio()), "con_envio": str(con_envio.calcular_precio()),
                    "base_despues": str(teclado.calcular_precio())},
        "carrito": pasos, "facturas": documentos,
    }


def presentar(datos: dict) -> str:
    p = datos["precios"]
    lineas = ["PLATAFORMA DE GESTIÓN DE CATÁLOGO Y PEDIDOS", "",
              "Precio del teclado (USD)",
              f"Catálogo: {p['base']}  |  descuento del 10 %: {p['con_descuento']}",
              f"Impuesto ilustrativo del 10 % sobre el precio rebajado: {p['con_impuesto']}",
              f"Con envío de USD 5: {p['con_envio']}  |  catálogo al final: {p['base_despues']}", "",
              "Carrito · stock disponible · recomendaciones"]
    for paso in datos["carrito"]:
        contenido = ", ".join(paso["contenido"]) or "vacío"
        sugerencias = ", ".join(paso["sugerencias"]) or "ninguna"
        stock = paso["stock_libre"]
        lineas.append(f"{paso['accion']}: [{contenido}] | USD {paso['total_usd']} | "
                      f"TEC: {stock['TEC']}, RAT: {stock['RAT']} | sugiere: {sugerencias}")
    lineas.extend(["", "Facturación · tres pedidos independientes con igual contenido", "",
                   "\n\n".join(datos["facturas"])])
    return "\n".join(lineas)

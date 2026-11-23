"""Punto de entrada. Todas las operaciones funcionan sin conexión."""
import argparse
import json
from decimal import Decimal, InvalidOperation

from demostracion import demostrar, escenario, nuevo_carrito, presentar
from tienda.facturas import EmisorExportacion, EmisorNacional, EmisorSimplificado
from tienda.pedidos import Pedido
from tienda.precios import Descuento, Envio, Impuesto, Producto


def decimal_usuario(pregunta: str) -> Decimal:
    return Decimal((input(pregunta).strip() or "0").replace(",", "."))


def menu() -> None:
    catalogo, stock, carrito, recomendaciones = escenario()
    secuencia = 1
    while True:
        print("\n1 Catálogo  |  2 Agregar al carrito  |  3 Retirar una línea  |  "
              "4 Ver carrito  |  5 Emitir factura  |  6 Registrar producto  |  0 Salir")
        opcion = input("Opción: ").strip()
        try:
            if opcion == "0":
                return
            if opcion == "1":
                for p in catalogo.listar():
                    print(f"{p.codigo}: {p.nombre} · {p.categoria} · USD {p.precio_base:.2f} · "
                          f"{stock.disponibles(p.codigo)} disponibles")
            elif opcion == "2":
                articulo = catalogo.buscar(input("Código del producto: ").strip().upper())
                descuento = decimal_usuario("Descuento en % (vacío = 0): ") / 100
                impuesto = decimal_usuario("Impuesto en % (vacío = 0): ") / 100
                envio = decimal_usuario("Envío por unidad en USD (vacío = 0): ")
                if descuento:
                    articulo = Descuento(articulo, descuento)
                if impuesto:
                    articulo = Impuesto(articulo, impuesto)
                if envio:
                    articulo = Envio(articulo, envio)
                identificador = carrito.agregar(articulo)
                print(f"Línea {identificador} agregada. Precio: USD {articulo.calcular_precio():.2f}")
            elif opcion == "3":
                carrito.eliminar(int(input("Identificador de la línea: ")))
                print("Línea retirada y unidad liberada.")
            elif opcion == "4":
                for l in carrito.lineas():
                    print(f"{l.id_linea}: {l.articulo.producto_base().nombre} · "
                          f"USD {l.articulo.calcular_precio():.2f}")
                print(f"Total: USD {carrito.total():.2f}")
                print("Recomendaciones:", ", ".join(p.nombre for p in recomendaciones.sugerir()) or "ninguna")
            elif opcion == "5":
                tipo = input("1 Nacional, 2 Exportación, 3 Simplificada: ").strip()
                # La elección pertenece a la interfaz; Pedido nunca importa los emisores concretos.
                if tipo == "1":
                    emisor = EmisorNacional()
                elif tipo == "2":
                    emisor = EmisorExportacion(input("Destino de exportación: "))
                elif tipo == "3":
                    emisor = EmisorSimplificado()
                else:
                    print("Tipo de factura no válido.")
                    continue
                pedido = Pedido.desde_carrito(f"CP2-{secuencia:03d}", carrito)
                print(pedido.facturar(emisor))
                secuencia += 1
                carrito, recomendaciones = nuevo_carrito(catalogo, stock)
            elif opcion == "6":
                codigo = input("Código nuevo: ").strip().upper()
                nombre = input("Nombre: ").strip()
                categoria = input("Categoría: ").strip()
                precio = decimal_usuario("Precio base en USD: ")
                unidades = int(input("Existencias iniciales: "))
                if unidades < 0:
                    raise ValueError("Las existencias no pueden ser negativas.")
                catalogo.registrar(Producto(codigo, nombre, categoria, precio))
                if unidades:
                    stock.reponer(codigo, unidades)
                print("Producto registrado.")
            else:
                print("Elige una opción de la lista.")
        except InvalidOperation:
            print("Escribe un número decimal válido.")
        except ValueError as error:
            print(error)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plataforma de gestión de catálogo y pedidos")
    modos = parser.add_mutually_exclusive_group()
    modos.add_argument("--menu", action="store_true", help="Abrir la aplicación interactiva")
    modos.add_argument("--json", action="store_true", help="Imprimir la ejecución en formato JSON")
    opciones = parser.parse_args()
    if opciones.menu:
        try:
            menu()
        except (EOFError, KeyboardInterrupt):
            print("\nSesión terminada.")
    elif opciones.json:
        print(json.dumps(demostrar(), ensure_ascii=False, indent=2))
    else:
        print(presentar(demostrar()))

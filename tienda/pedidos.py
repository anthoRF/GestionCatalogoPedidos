"""El pedido depende del contrato de emisión, no de un formato de factura."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from .carrito import Carrito
from .precios import CERO, dinero

if TYPE_CHECKING:
    from .facturas import EmisorFactura


@dataclass(frozen=True, slots=True)
class LineaPedido:
    codigo: str
    nombre: str
    importe: Decimal

    def __post_init__(self) -> None:
        if not self.codigo.strip() or not self.nombre.strip():
            raise ValueError("La línea del pedido necesita un código y un nombre.")
        object.__setattr__(self, "importe", dinero(self.importe))


@dataclass(frozen=True, slots=True)
class Pedido:
    numero: str
    lineas: tuple[LineaPedido, ...]

    def __post_init__(self) -> None:
        detalle = tuple(LineaPedido(l.codigo, l.nombre, l.importe) for l in self.lineas)
        if not self.numero.strip() or not detalle:
            raise ValueError("El pedido necesita un número y al menos una línea.")
        object.__setattr__(self, "lineas", detalle)

    @classmethod
    def desde_carrito(cls, numero: str, carrito: Carrito) -> Pedido:
        detalle = []
        for linea in carrito.lineas():
            producto = linea.articulo.producto_base()
            detalle.append(LineaPedido(producto.codigo, producto.nombre,
                                       linea.articulo.calcular_precio()))
        pedido = cls(numero, tuple(detalle))
        carrito.cerrar()
        return pedido

    def total(self) -> Decimal:
        return sum((linea.importe for linea in self.lineas), CERO)

    def facturar(self, emisor: EmisorFactura) -> str:
        return emisor.emitir(self)

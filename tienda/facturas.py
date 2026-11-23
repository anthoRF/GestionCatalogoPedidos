"""Creadores y productos del patrón Factory Method."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .pedidos import Pedido


@dataclass(frozen=True, slots=True)
class Factura(ABC):
    pedido: Pedido

    @abstractmethod
    def renderizar(self) -> str:
        raise NotImplementedError


class FacturaNacional(Factura):
    def renderizar(self) -> str:
        detalle = [f"{l.codigo} · {l.nombre}: USD {l.importe:.2f}" for l in self.pedido.lineas]
        return "\n".join(["FACTURA NACIONAL", f"Pedido: {self.pedido.numero}", *detalle,
                          f"Total: USD {self.pedido.total():.2f}"])


@dataclass(frozen=True, slots=True)
class FacturaExportacion(Factura):
    destino: str

    def renderizar(self) -> str:
        detalle = [f"{l.codigo} · {l.nombre}: USD {l.importe:.2f}" for l in self.pedido.lineas]
        return "\n".join(["FACTURA DE EXPORTACIÓN", f"Pedido: {self.pedido.numero}",
                          f"Destino: {self.destino}", *detalle, f"Total: USD {self.pedido.total():.2f}"])


class FacturaSimplificada(Factura):
    def renderizar(self) -> str:
        return "\n".join(["FACTURA SIMPLIFICADA", f"Pedido: {self.pedido.numero}",
                          f"Unidades: {len(self.pedido.lineas)}", f"Total: USD {self.pedido.total():.2f}"])


class EmisorFactura(ABC):
    def emitir(self, pedido: Pedido) -> str:
        factura = self.crear_factura(pedido)
        return factura.renderizar()

    @abstractmethod
    def crear_factura(self, pedido: Pedido) -> Factura:
        raise NotImplementedError


class EmisorNacional(EmisorFactura):
    def crear_factura(self, pedido: Pedido) -> Factura:
        return FacturaNacional(pedido)


class EmisorExportacion(EmisorFactura):
    def __init__(self, destino: str) -> None:
        if not destino.strip():
            raise ValueError("La factura de exportación requiere un destino.")
        self._destino = destino.strip()

    def crear_factura(self, pedido: Pedido) -> Factura:
        return FacturaExportacion(pedido, self._destino)


class EmisorSimplificado(EmisorFactura):
    def crear_factura(self, pedido: Pedido) -> Factura:
        return FacturaSimplificada(pedido)

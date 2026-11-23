"""Catálogo y cálculo de precios en USD."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

CENTAVO = Decimal("0.01")
CERO = Decimal("0.00")


def no_negativo(valor: Decimal) -> Decimal:
    if not isinstance(valor, Decimal) or not valor.is_finite() or valor < 0:
        raise ValueError("Se requiere un decimal finito y no negativo.")
    return valor


def dinero(valor: Decimal) -> Decimal:
    return no_negativo(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


class ComponentePrecio(ABC):
    @abstractmethod
    def calcular_precio(self) -> Decimal:
        raise NotImplementedError

    @abstractmethod
    def producto_base(self) -> Producto:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Producto(ComponentePrecio):
    codigo: str
    nombre: str
    categoria: str
    precio_base: Decimal

    def __post_init__(self) -> None:
        if any(not campo.strip() for campo in (self.codigo, self.nombre, self.categoria)):
            raise ValueError("El código, el nombre y la categoría son obligatorios.")
        object.__setattr__(self, "precio_base", dinero(self.precio_base))

    def calcular_precio(self) -> Decimal:
        return self.precio_base

    def producto_base(self) -> Producto:
        return self


@dataclass(frozen=True, slots=True)
class DecoradorPrecio(ComponentePrecio):
    envuelto: ComponentePrecio

    def producto_base(self) -> Producto:
        return self.envuelto.producto_base()


@dataclass(frozen=True, slots=True)
class Descuento(DecoradorPrecio):
    tasa: Decimal

    def __post_init__(self) -> None:
        if no_negativo(self.tasa) > 1:
            raise ValueError("El descuento no puede superar el 100 %.")

    def calcular_precio(self) -> Decimal:
        return dinero(self.envuelto.calcular_precio() * (1 - self.tasa))


@dataclass(frozen=True, slots=True)
class Impuesto(DecoradorPrecio):
    tasa: Decimal

    def __post_init__(self) -> None:
        no_negativo(self.tasa)

    def calcular_precio(self) -> Decimal:
        return dinero(self.envuelto.calcular_precio() * (1 + self.tasa))


@dataclass(frozen=True, slots=True)
class Envio(DecoradorPrecio):
    costo: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "costo", dinero(self.costo))

    def calcular_precio(self) -> Decimal:
        return dinero(self.envuelto.calcular_precio() + self.costo)


class Catalogo:
    def __init__(self) -> None:
        self._productos: dict[str, Producto] = {}

    def registrar(self, producto: Producto) -> None:
        if producto.codigo in self._productos:
            raise ValueError(f"El código {producto.codigo} ya está registrado.")
        self._productos[producto.codigo] = producto

    def buscar(self, codigo: str) -> Producto:
        try:
            return self._productos[codigo]
        except KeyError:
            raise ValueError(f"Producto no encontrado: {codigo}.") from None

    def listar(self) -> tuple[Producto, ...]:
        return tuple(self._productos.values())

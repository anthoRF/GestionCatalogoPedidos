"""El carrito publica hechos consumados: una unidad agregada o eliminada."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .precios import CERO, Catalogo, ComponentePrecio, Producto


class TipoCambio(Enum):
    AGREGADO = "agregado"
    ELIMINADO = "eliminado"


@dataclass(frozen=True, slots=True)
class EventoCarrito:
    tipo: TipoCambio
    producto: Producto
    contenido: tuple[Producto, ...]  # Estado del carrito después del cambio.


class ObservadorCarrito(ABC):
    @abstractmethod
    def actualizar(self, evento: EventoCarrito) -> None:
        raise NotImplementedError


class ControlStock(ObservadorCarrito):
    @abstractmethod
    def disponibles(self, codigo: str) -> int:
        raise NotImplementedError


class Stock(ControlStock):
    def __init__(self, existencias: dict[str, int]) -> None:
        if any(type(n) is not int or n < 0 for n in existencias.values()):
            raise ValueError("Las existencias deben ser enteros no negativos.")
        self._existencias = dict(existencias)
        self._reservas: Counter[str] = Counter()

    def disponibles(self, codigo: str) -> int:
        return self._existencias.get(codigo, 0) - self._reservas[codigo]

    def reponer(self, codigo: str, unidades: int) -> None:
        if not codigo.strip() or type(unidades) is not int or unidades <= 0:
            raise ValueError("Indica un código y un número positivo de unidades.")
        self._existencias[codigo] = self._existencias.get(codigo, 0) + unidades

    def reservadas(self, codigo: str) -> int:
        return self._reservas[codigo]

    def actualizar(self, evento: EventoCarrito) -> None:
        codigo = evento.producto.codigo
        if evento.tipo is TipoCambio.AGREGADO:
            if self.disponibles(codigo) < 1:
                raise ValueError("No quedan unidades para reservar.")
            self._reservas[codigo] += 1
        else:
            if self._reservas[codigo] < 1:
                raise ValueError("No hay una reserva que liberar.")
            self._reservas[codigo] -= 1


class Recomendaciones(ObservadorCarrito):
    def __init__(self, catalogo: Catalogo) -> None:
        self._catalogo = catalogo
        self._sugerencias: tuple[Producto, ...] = ()

    def actualizar(self, evento: EventoCarrito) -> None:
        elegidos = {p.codigo for p in evento.contenido}
        interes = Counter(p.categoria for p in evento.contenido)
        candidatos = (p for p in self._catalogo.listar()
                      if p.codigo not in elegidos and interes[p.categoria])
        self._sugerencias = tuple(sorted(candidatos,
                                        key=lambda p: (-interes[p.categoria], p.codigo)))

    def sugerir(self) -> tuple[Producto, ...]:
        return self._sugerencias


@dataclass(frozen=True, slots=True)
class LineaCarrito:
    id_linea: int
    articulo: ComponentePrecio


class Carrito:
    def __init__(self, control: ControlStock) -> None:
        self._control = control
        self._observadores: list[ObservadorCarrito] = [control]
        self._lineas: dict[int, LineaCarrito] = {}
        self._siguiente_id = 1
        self._cerrado = False

    def suscribir(self, observador: ObservadorCarrito) -> None:
        if not any(o is observador for o in self._observadores):
            self._observadores.append(observador)

    def desuscribir(self, observador: ObservadorCarrito) -> None:
        if observador is self._control:
            raise ValueError("El control de stock debe permanecer suscrito.")
        self._observadores = [o for o in self._observadores if o is not observador]

    def agregar(self, articulo: ComponentePrecio) -> int:
        if self._cerrado:
            raise ValueError("El carrito está cerrado.")
        producto = articulo.producto_base()
        if self._control.disponibles(producto.codigo) < 1:
            raise ValueError(f"No hay stock disponible de {producto.codigo}.")
        identificador = self._siguiente_id
        self._siguiente_id += 1
        self._lineas[identificador] = LineaCarrito(identificador, articulo)
        self._notificar(TipoCambio.AGREGADO, producto)
        return identificador

    def eliminar(self, id_linea: int) -> None:
        if self._cerrado:
            raise ValueError("El carrito está cerrado.")
        if id_linea not in self._lineas:
            raise ValueError("La línea indicada no pertenece al carrito.")
        articulo = self._lineas.pop(id_linea).articulo
        self._notificar(TipoCambio.ELIMINADO, articulo.producto_base())

    def lineas(self) -> tuple[LineaCarrito, ...]:
        return tuple(self._lineas.values())

    def total(self) -> Decimal:
        return sum((l.articulo.calcular_precio() for l in self._lineas.values()), CERO)

    def cerrar(self) -> None:
        if self._cerrado or not self._lineas:
            raise ValueError("Solo se puede cerrar un carrito abierto con productos.")
        self._cerrado = True

    def _notificar(self, tipo: TipoCambio, producto: Producto) -> None:
        contenido = tuple(l.articulo.producto_base() for l in self._lineas.values())
        evento = EventoCarrito(tipo, producto, contenido)
        for observador in tuple(self._observadores):
            observador.actualizar(evento)

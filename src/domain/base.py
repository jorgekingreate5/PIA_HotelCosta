class RaizDeAgregado:
    """Base de los agregados: acumula los eventos de dominio que ocurrieron."""

    def __init__(self):
        self._eventos = []

    def _registrar(self, evento):
        self._eventos.append(evento)

    def sacar_eventos(self):
        eventos, self._eventos = self._eventos, []
        return eventos

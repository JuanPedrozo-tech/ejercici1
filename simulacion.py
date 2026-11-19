"""Simulación de 14 operaciones entre ellas tenemos valida e invalidas. El programa nunca se
detiene: porque se ejecuta todo dentro de su propio try/except."""
import logging

from excepciones import ErrorSoftwareFJ
from gestor import GestorFJ

log = logging.getLogger("software_fj")


def ejecutar_simulacion(gestor: GestorFJ) -> list[str]:
    resultados: list[str] = []
    estado: dict = {}

    def paso(n, descripcion, accion):
        try:
            res = accion()
        except ErrorSoftwareFJ as e:
            resultados.append(f"{n:02d}. [ERROR CONTROLADO] {descripcion}\n      -> {type(e).__name__}: {e}")
        except Exception as e:  # cualquier error inesperado tampoco detiene el sistema
            log.exception("Error inesperado en simulación (paso %s)", n)
            resultados.append(f"{n:02d}. [ERROR INESPERADO] {descripcion}\n      -> {type(e).__name__}: {e}")
        else:
            resultados.append(f"{n:02d}. [OK] {descripcion}\n      -> {res}")
        finally:
            log.debug("Paso de simulación %s finalizado", n)

    log.info("=== INICIO DE SIMULACIÓN ===")

    def a(k, v):  # guarda un objeto creado y lo devuelve
        estado[k] = v
        return v

    paso(1, "Registrar cliente válido (Ana Gómez)",
         lambda: a("ana", gestor.registrar_cliente("Ana Gómez", "1065432100", "ana@mail.com", "3001234567")))
    paso(2, "Registrar cliente con documento inválido",
         lambda: gestor.registrar_cliente("Pedro Ruiz", "12ab", "pedro@mail.com", "3109876543"))
    paso(3, "Registrar cliente con email inválido",
         lambda: gestor.registrar_cliente("Laura Díaz", "1098765432", "laura-correo", "3151112233"))
    paso(4, "Registrar cliente válido (Luis Pérez)",
         lambda: a("luis", gestor.registrar_cliente("Luis Pérez", "79456123", "luis@mail.com", "3204445566")))
    paso(5, "Crear sala válida",
         lambda: a("sala", gestor.crear_servicio("sala", nombre="Sala Ejecutiva", tarifa_hora=50000, capacidad=10)))
    paso(6, "Crear sala con tarifa negativa",
         lambda: gestor.crear_servicio("sala", nombre="Sala Fantasma", tarifa_hora=-100, capacidad=5))
    paso(7, "Crear alquiler de equipo válido",
         lambda: a("equipo", gestor.crear_servicio("equipo", nombre="Videobeam HD", tarifa_hora=15000, deposito=100000)))
    paso(8, "Crear asesoría sin el parámetro 'nivel' (parámetro faltante)",
         lambda: gestor.crear_servicio("asesoria", nombre="Asesoría en Redes", tarifa_hora=80000))
    paso(9, "Crear asesoría senior válida",
         lambda: a("asesoria", gestor.crear_servicio("asesoria", nombre="Asesoría en Python", tarifa_hora=80000, nivel="senior")))
    paso(10, "Reserva válida: Ana reserva la sala 5 h",
         lambda: a("res1", gestor.crear_reserva(estado["ana"].id, estado["sala"].id, 5)))
    paso(11, "Confirmar y procesar la reserva (IVA 19 %, descuento 5 %)",
         lambda: (gestor.confirmar_reserva(estado["res1"].id),
                  gestor.procesar_reserva(estado["res1"].id, 0.19, 0.05))[1])
    paso(12, "Reserva inválida: sala por 30 horas",
         lambda: gestor.crear_reserva(estado["luis"].id, estado["sala"].id, 30))
    paso(13, "Reserva con servicio no disponible",
         lambda: (gestor.cambiar_disponibilidad(estado["equipo"].id, False),
                  gestor.crear_reserva(estado["luis"].id, estado["equipo"].id, 3))[1])
    paso(14, "Procesar una reserva sin confirmar (operación no permitida)",
         lambda: gestor.procesar_reserva(
             a("res2", gestor.crear_reserva(estado["luis"].id, estado["asesoria"].id, 2)).id))
    paso(15, "Procesar con descuento inconsistente (150 %)",
         lambda: (gestor.confirmar_reserva(estado["res2"].id),
                  gestor.procesar_reserva(estado["res2"].id, 0.19, 1.5))[1])
    paso(16, "Cancelar una reserva ya cancelada",
         lambda: (gestor.cancelar_reserva(estado["res1"].id)))

    log.info("=== FIN DE SIMULACIÓN (el sistema siguió activo) ===")
    resultados.append("\nSimulación completada: el sistema continuó funcionando pese a los errores.")
    return resultados


if __name__ == "__main__":
    from logger import configurar_logging
    configurar_logging()
    print("\n".join(ejecutar_simulacion(GestorFJ())))

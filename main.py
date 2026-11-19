"""Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas.
Interfaz gráfica con Tkinter. Ejecutar:  python main.py
"""
import tkinter as tk
from tkinter import messagebox, ttk

from excepciones import ErrorSoftwareFJ
from gestor import GestorFJ
from logger import RUTA_LOG, configurar_logging
from simulacion import ejecutar_simulacion

log = configurar_logging()

EXTRA_SERVICIO = {
    "sala": "Capacidad (personas)",
    "equipo": "Depósito (COP)",
    "asesoria": "Nivel (junior/senior)",
}
CAMPO_EXTRA = {"sala": "capacidad", "equipo": "deposito", "asesoria": "nivel"}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Software FJ - Gestión de Clientes, Servicios y Reservas")
        self.geometry("1020x660")
        self.gestor = GestorFJ()

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        self.tab_clientes = ttk.Frame(nb)
        self.tab_servicios = ttk.Frame(nb)
        self.tab_reservas = ttk.Frame(nb)
        self.tab_sim = ttk.Frame(nb)
        nb.add(self.tab_clientes, text="Clientes")
        nb.add(self.tab_servicios, text="Servicios")
        nb.add(self.tab_reservas, text="Reservas")
        nb.add(self.tab_sim, text="Simulación y Logs")

        self._construir_clientes()
        self._construir_servicios()
        self._construir_reservas()
        self._construir_simulacion()
        self.refrescar()

    # ------------------------------------------------------------------ util
    def _ejecutar(self, accion, exito=None):
        """Ejecuta una acción sin que ningún error detenga la aplicación."""
        try:
            resultado = accion()
        except ErrorSoftwareFJ as e:
            messagebox.showerror("Operación rechazada", str(e))
            return None
        except Exception as e:
            log.exception("Error inesperado en la interfaz")
            messagebox.showerror("Error inesperado", f"{type(e).__name__}: {e}\n(registrado en el log)")
            return None
        else:
            if exito:
                messagebox.showinfo("Listo", exito(resultado) if callable(exito) else exito)
            return resultado
        finally:
            self.refrescar()

    @staticmethod
    def _tabla(parent, columnas, anchos):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        tree = ttk.Treeview(frame, columns=columnas, show="headings", height=10)
        for col, ancho in zip(columnas, anchos):
            tree.heading(col, text=col)
            tree.column(col, width=ancho, anchor="w")
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tree

    @staticmethod
    def _fila(parent, etiqueta, fila, ancho=28):
        ttk.Label(parent, text=etiqueta).grid(row=fila, column=0, sticky="w", padx=6, pady=3)
        entrada = ttk.Entry(parent, width=ancho)
        entrada.grid(row=fila, column=1, padx=6, pady=3)
        return entrada

    # -------------------------------------------------------------- clientes
    def _construir_clientes(self):
        form = ttk.LabelFrame(self.tab_clientes, text="Registrar cliente")
        form.pack(fill="x", padx=8, pady=8)
        self.c_nombre = self._fila(form, "Nombre", 0)
        self.c_doc = self._fila(form, "Documento", 1)
        self.c_email = self._fila(form, "Email", 2)
        self.c_tel = self._fila(form, "Teléfono", 3)
        ttk.Button(form, text="Registrar", command=self._registrar_cliente).grid(row=4, column=1, sticky="e", pady=6)
        self.t_clientes = self._tabla(self.tab_clientes, ("ID", "Nombre", "Documento", "Email", "Teléfono"),
                                      (80, 220, 110, 240, 110))

    def _registrar_cliente(self):
        def accion():
            return self.gestor.registrar_cliente(self.c_nombre.get(), self.c_doc.get(),
                                                 self.c_email.get(), self.c_tel.get())
        cliente = self._ejecutar(accion, lambda c: f"Cliente {c.id} registrado.")
        if cliente:
            for e in (self.c_nombre, self.c_doc, self.c_email, self.c_tel):
                e.delete(0, "end")

    # ------------------------------------------------------------- servicios
    def _construir_servicios(self):
        form = ttk.LabelFrame(self.tab_servicios, text="Crear servicio")
        form.pack(fill="x", padx=8, pady=8)
        ttk.Label(form, text="Tipo").grid(row=0, column=0, sticky="w", padx=6, pady=3)
        self.s_tipo = ttk.Combobox(form, values=list(EXTRA_SERVICIO), state="readonly", width=26)
        self.s_tipo.current(0)
        self.s_tipo.grid(row=0, column=1, padx=6, pady=3)
        self.s_tipo.bind("<<ComboboxSelected>>", self._cambiar_etiqueta_extra)
        self.s_nombre = self._fila(form, "Nombre", 1)
        self.s_tarifa = self._fila(form, "Tarifa por hora (COP)", 2)
        self.lbl_extra = ttk.Label(form, text=EXTRA_SERVICIO["sala"])
        self.lbl_extra.grid(row=3, column=0, sticky="w", padx=6, pady=3)
        self.s_extra = ttk.Entry(form, width=28)
        self.s_extra.grid(row=3, column=1, padx=6, pady=3)
        botones = ttk.Frame(form)
        botones.grid(row=4, column=1, sticky="e", pady=6)
        ttk.Button(botones, text="Crear servicio", command=self._crear_servicio).pack(side="left", padx=4)
        ttk.Button(botones, text="Habilitar / deshabilitar seleccionado",
                   command=self._alternar_disponibilidad).pack(side="left", padx=4)
        self.t_servicios = self._tabla(self.tab_servicios, ("ID", "Tipo", "Descripción", "Disponible"),
                                       (80, 90, 640, 90))

    def _cambiar_etiqueta_extra(self, _evento=None):
        self.lbl_extra.config(text=EXTRA_SERVICIO[self.s_tipo.get()])

    def _crear_servicio(self):
        tipo = self.s_tipo.get()
        datos = {"nombre": self.s_nombre.get(), "tarifa_hora": self.s_tarifa.get()}
        extra = self.s_extra.get()
        if extra.strip():  # si queda vacío, el gestor detecta el parámetro faltante
            datos[CAMPO_EXTRA[tipo]] = extra
        servicio = self._ejecutar(lambda: self.gestor.crear_servicio(tipo, **datos),
                                  lambda s: f"Servicio {s.id} creado.")
        if servicio:
            for e in (self.s_nombre, self.s_tarifa, self.s_extra):
                e.delete(0, "end")

    def _alternar_disponibilidad(self):
        sel = self.t_servicios.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccione un servicio de la tabla.")
            return
        id_srv = self.t_servicios.item(sel[0], "values")[0]
        actual = self.gestor.buscar_servicio(id_srv).disponible
        self._ejecutar(lambda: self.gestor.cambiar_disponibilidad(id_srv, not actual))

    # --------------------------------------------------------------- reservas
    def _construir_reservas(self):
        form = ttk.LabelFrame(self.tab_reservas, text="Nueva reserva")
        form.pack(fill="x", padx=8, pady=8)
        ttk.Label(form, text="Cliente").grid(row=0, column=0, sticky="w", padx=6, pady=3)
        self.r_cliente = ttk.Combobox(form, state="readonly", width=40)
        self.r_cliente.grid(row=0, column=1, padx=6, pady=3)
        ttk.Label(form, text="Servicio").grid(row=1, column=0, sticky="w", padx=6, pady=3)
        self.r_servicio = ttk.Combobox(form, state="readonly", width=40)
        self.r_servicio.grid(row=1, column=1, padx=6, pady=3)
        self.r_horas = self._fila(form, "Duración (horas)", 2, ancho=42)
        ttk.Button(form, text="Crear reserva", command=self._crear_reserva).grid(row=3, column=1, sticky="e", pady=6)

        acciones = ttk.LabelFrame(self.tab_reservas, text="Acciones sobre la reserva seleccionada")
        acciones.pack(fill="x", padx=8, pady=4)
        ttk.Label(acciones, text="IVA (0-1)").pack(side="left", padx=4)
        self.r_iva = ttk.Entry(acciones, width=6)
        self.r_iva.insert(0, "0.19")
        self.r_iva.pack(side="left")
        ttk.Label(acciones, text="Descuento (0-1)").pack(side="left", padx=4)
        self.r_desc = ttk.Entry(acciones, width=6)
        self.r_desc.insert(0, "0")
        self.r_desc.pack(side="left")
        ttk.Button(acciones, text="Confirmar", command=lambda: self._accion_reserva("confirmar")).pack(side="left", padx=6)
        ttk.Button(acciones, text="Procesar", command=lambda: self._accion_reserva("procesar")).pack(side="left", padx=6)
        ttk.Button(acciones, text="Cancelar", command=lambda: self._accion_reserva("cancelar")).pack(side="left", padx=6)

        self.t_reservas = self._tabla(self.tab_reservas,
                                      ("ID", "Cliente", "Servicio", "Horas", "Estado", "Total"),
                                      (80, 200, 260, 70, 100, 140))

    @staticmethod
    def _id_de(texto):
        return texto.split(" - ")[0].strip() if texto else ""

    def _crear_reserva(self):
        id_c, id_s = self._id_de(self.r_cliente.get()), self._id_de(self.r_servicio.get())
        reserva = self._ejecutar(lambda: self.gestor.crear_reserva(id_c, id_s, self.r_horas.get()),
                                 lambda r: f"Reserva {r.id} creada (pendiente).")
        if reserva:
            self.r_horas.delete(0, "end")

    def _accion_reserva(self, accion):
        sel = self.t_reservas.selection()
        if not sel:
            messagebox.showwarning("Selección", "Seleccione una reserva de la tabla.")
            return
        id_res = self.t_reservas.item(sel[0], "values")[0]
        if accion == "confirmar":
            self._ejecutar(lambda: self.gestor.confirmar_reserva(id_res), f"Reserva {id_res} confirmada.")
        elif accion == "cancelar":
            self._ejecutar(lambda: self.gestor.cancelar_reserva(id_res), f"Reserva {id_res} cancelada.")
        else:
            def procesar():
                try:
                    iva, desc = float(self.r_iva.get()), float(self.r_desc.get())
                except ValueError as e:
                    raise ErrorSoftwareFJ("IVA y descuento deben ser numéricos (ej. 0.19).") from e
                return self.gestor.procesar_reserva(id_res, iva, desc)
            self._ejecutar(procesar, lambda t: f"Reserva {id_res} procesada.\nTotal: ${t:,.2f}")

    # ------------------------------------------------------------- simulación
    def _construir_simulacion(self):
        barra = ttk.Frame(self.tab_sim)
        barra.pack(fill="x", padx=8, pady=8)
        ttk.Button(barra, text="Ejecutar simulación (16 operaciones)", command=self._simular).pack(side="left", padx=4)
        ttk.Button(barra, text="Ver archivo de log", command=self._ver_log).pack(side="left", padx=4)
        ttk.Button(barra, text="Limpiar pantalla", command=lambda: self._escribir("")).pack(side="left", padx=4)
        marco = ttk.Frame(self.tab_sim)
        marco.pack(fill="both", expand=True, padx=8, pady=8)
        self.txt = tk.Text(marco, wrap="word", font=("Consolas", 10))
        sb = ttk.Scrollbar(marco, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=sb.set, state="disabled")
        self.txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _escribir(self, texto):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("end", texto)
        self.txt.configure(state="disabled")

    def _simular(self):
        lineas = self._ejecutar(lambda: ejecutar_simulacion(self.gestor))
        if lineas:
            self._escribir("\n".join(lineas))

    def _ver_log(self):
        try:
            contenido = RUTA_LOG.read_text(encoding="utf-8")
        except OSError as e:
            contenido = f"No se pudo leer el log: {e}"
        self._escribir(contenido or "(el log está vacío)")
        self.txt.see("end")

    # ---------------------------------------------------------------- refresco
    def refrescar(self):
        for tree in (self.t_clientes, self.t_servicios, self.t_reservas):
            tree.delete(*tree.get_children())
        for c in self.gestor.clientes:
            self.t_clientes.insert("", "end", values=(c.id, c.nombre, c.documento, c.email, c.telefono))
        for s in self.gestor.servicios:
            self.t_servicios.insert("", "end", values=(s.id, s.TIPO, s.describir(), "Sí" if s.disponible else "No"))
        for r in self.gestor.reservas:
            total = f"${r.costo_total:,.2f}" if r.costo_total is not None else "-"
            self.t_reservas.insert("", "end", values=(r.id, r.cliente.nombre, r.servicio.nombre,
                                                      f"{r.horas:g}", r.estado.value, total))
        self.r_cliente["values"] = [f"{c.id} - {c.nombre}" for c in self.gestor.clientes]
        self.r_servicio["values"] = [f"{s.id} - {s.nombre}" for s in self.gestor.servicios if s.disponible]


if __name__ == "__main__":
    log.info("Aplicación iniciada")
    App().mainloop()

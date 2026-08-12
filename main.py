"""
Aplicación de Notas - Nivel 1 Principiante
Hecha con Kivy (Python) para funcionar en Windows y empaquetarse para Android.

Funciones:
- Crear nota
- Editar nota
- Eliminar nota (con confirmación y opción de deshacer)
- Las notas se guardan en un archivo y se recuperan al reabrir la app
- El contenido se escribe en Markdown y se convierte a HTML al guardar
- Se muestra la fecha de creación de cada nota
- Pantalla de bienvenida (splash)
- Buscador de notas por título
- Ordenar por fecha o por título
- Notas favoritas (fijadas arriba)
- Contador de notas y contador de caracteres
- Aviso de "guardado exitoso"
"""

import json
import os
import re
import uuid
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup

# La librería "markdown" convierte texto Markdown a HTML.
# Si no está instalada, la app sigue funcionando pero sin convertir a HTML.
try:
    import markdown as md_lib
except ImportError:
    md_lib = None

NOMBRE_ARCHIVO_DATOS = "notas.json"
SEGUNDOS_MENSAJE_TEMPORAL = 2
SEGUNDOS_PARA_DESHACER = 4

# ---------------------------------------------------------------------------
# Paleta de colores - Tema Rosado Pastel 🌸
# ---------------------------------------------------------------------------
COLOR_FONDO = (1, 0.93, 0.96, 1)
COLOR_BOTON = (0.97, 0.75, 0.85, 1)
COLOR_BOTON_ELIMINAR = (0.93, 0.6, 0.72, 1)
COLOR_ACENTO = (0.85, 0.35, 0.55, 1)
COLOR_TEXTO = (0.45, 0.28, 0.35, 1)
COLOR_TEXTO_SUAVE = (0.65, 0.5, 0.56, 1)
COLOR_CAJA_TEXTO = (1, 0.98, 0.99, 1)
COLOR_EXITO = (0.55, 0.75, 0.55, 1)
COLOR_FAVORITA = (0.95, 0.75, 0.25, 1)


def markdown_a_texto_visual(texto_md):
    """Convierte Markdown a 'markup' de Kivy (negrita real, títulos, listas)."""
    lineas = texto_md.split("\n")
    lineas_convertidas = []
    for linea in lineas:
        if linea.startswith("# "):
            lineas_convertidas.append(f"[size=24][b]{linea[2:]}[/b][/size]")
        elif linea.startswith("## "):
            lineas_convertidas.append(f"[size=20][b]{linea[3:]}[/b][/size]")
        elif linea.startswith("- "):
            lineas_convertidas.append(f"   •  {linea[2:]}")
        else:
            lineas_convertidas.append(linea)
    resultado = "\n".join(lineas_convertidas)
    resultado = re.sub(r"\*\*(.+?)\*\*", r"[b]\1[/b]", resultado)
    resultado = re.sub(r"\*(.+?)\*", r"[i]\1[/i]", resultado)
    return resultado


# ---------------------------------------------------------------------------
# Interfaz visual (KV)
# ---------------------------------------------------------------------------
KV = """
<PantallaSplash>:
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        Widget:
        Label:
            text: 'NotaMD'
            font_size: 44
            bold: True
            color: 0.85, 0.35, 0.55, 1
        Label:
            text: 'Tus notas, con estilo 🌸'
            font_size: 18
            color: 0.65, 0.5, 0.56, 1
        Widget:

<PantallaLista>:
    BoxLayout:
        orientation: 'vertical'
        padding: 16
        spacing: 8

        BoxLayout:
            size_hint_y: None
            height: 44
            Label:
                text: 'Mis Notas 🌸'
                font_size: 28
                bold: True
                color: 0.85, 0.35, 0.55, 1
                halign: 'left'
                text_size: self.width, None
            Label:
                id: etiqueta_contador
                text: ''
                font_size: 13
                color: 0.65, 0.5, 0.56, 1
                halign: 'right'
                text_size: self.width, None
                size_hint_x: None
                width: 130

        Label:
            id: etiqueta_mensaje_temporal
            text: ''
            size_hint_y: None
            height: 26 if self.text else 0
            font_size: 14
            bold: True
            color: 0.3, 0.55, 0.3, 1

        BoxLayout:
            size_hint_y: None
            height: 42
            spacing: 8

            TextInput:
                id: campo_busqueda
                hint_text: '🔍 Buscar por título...'
                multiline: False
                font_size: 15
                background_color: 1, 0.98, 0.99, 1
                foreground_color: 0.45, 0.28, 0.35, 1
                hint_text_color: 0.75, 0.6, 0.66, 1
                cursor_color: 0.85, 0.35, 0.55, 1
                padding: 8, 8
                on_text: root.refrescar_notas()

            Button:
                id: boton_orden
                text: '📅 Fecha'
                size_hint_x: None
                width: 90
                font_size: 13
                background_normal: ''
                background_color: 0.97, 0.75, 0.85, 1
                color: 0.45, 0.28, 0.35, 1
                on_release: root.cambiar_orden()

        ScrollView:
            GridLayout:
                id: contenedor_notas
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: 10
                padding: 0, 4, 0, 10

        BoxLayout:
            id: contenedor_deshacer
            size_hint_y: None
            height: 0
            opacity: 0
            spacing: 10

        Button:
            text: '+ Nueva nota'
            size_hint_y: None
            height: 54
            font_size: 18
            bold: True
            background_normal: ''
            background_color: 0.85, 0.35, 0.55, 1
            color: 1, 1, 1, 1
            on_release: root.manager.get_screen('editar').nueva_nota()

<PantallaEditar>:
    BoxLayout:
        orientation: 'vertical'
        padding: 16
        spacing: 6

        TextInput:
            id: campo_titulo
            hint_text: 'Título de la nota'
            multiline: False
            size_hint_y: None
            height: 44
            font_size: 18
            background_color: 1, 0.98, 0.99, 1
            foreground_color: 0.45, 0.28, 0.35, 1
            hint_text_color: 0.75, 0.6, 0.66, 1
            cursor_color: 0.85, 0.35, 0.55, 1
            padding: 10, 10

        Label:
            id: etiqueta_fecha
            text: ''
            size_hint_y: None
            height: 22
            font_size: 13
            color: 0.65, 0.5, 0.56, 1

        TextInput:
            id: campo_contenido
            hint_text: 'Escribe tu nota en Markdown... (ej: **negrita**, # Título, - lista)'
            font_size: 16
            background_color: 1, 0.98, 0.99, 1
            foreground_color: 0.45, 0.28, 0.35, 1
            hint_text_color: 0.75, 0.6, 0.66, 1
            cursor_color: 0.85, 0.35, 0.55, 1
            padding: 10, 10

        Label:
            text: f'{len(campo_contenido.text)} caracteres'
            size_hint_y: None
            height: 20
            font_size: 12
            color: 0.65, 0.5, 0.56, 1
            halign: 'right'
            text_size: self.width, None

        BoxLayout:
            size_hint_y: None
            height: 54
            spacing: 10

            Button:
                text: 'Guardar'
                font_size: 18
                bold: True
                background_normal: ''
                background_color: 0.85, 0.35, 0.55, 1
                color: 1, 1, 1, 1
                on_release: root.guardar_nota()

            Button:
                text: 'Cancelar'
                font_size: 18
                background_normal: ''
                background_color: 0.97, 0.75, 0.85, 1
                color: 0.45, 0.28, 0.35, 1
                on_release: root.manager.current = 'lista'

<PantallaVer>:
    BoxLayout:
        orientation: 'vertical'
        padding: 16
        spacing: 10

        Label:
            id: etiqueta_titulo_ver
            text: ''
            font_size: 24
            bold: True
            size_hint_y: None
            height: 40
            color: 0.85, 0.35, 0.55, 1
            text_size: self.width, None
            halign: 'left'

        Label:
            id: etiqueta_fecha_ver
            text: ''
            font_size: 13
            size_hint_y: None
            height: 22
            color: 0.65, 0.5, 0.56, 1

        ScrollView:
            Label:
                id: etiqueta_contenido_ver
                text: ''
                markup: True
                font_size: 16
                color: 0.45, 0.28, 0.35, 1
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None
                halign: 'left'
                valign: 'top'

        BoxLayout:
            size_hint_y: None
            height: 54
            spacing: 10

            Button:
                text: 'Editar'
                font_size: 18
                background_normal: ''
                background_color: 0.97, 0.75, 0.85, 1
                color: 0.45, 0.28, 0.35, 1
                on_release: root.editar()

            Button:
                text: 'Volver'
                font_size: 18
                bold: True
                background_normal: ''
                background_color: 0.85, 0.35, 0.55, 1
                color: 1, 1, 1, 1
                on_release: root.manager.current = 'lista'
"""


class PantallaSplash(Screen):
    """Pantalla de bienvenida que se muestra un par de segundos al abrir la app."""

    def on_enter(self):
        Clock.schedule_once(self._ir_a_lista, 1.5)

    def _ir_a_lista(self, dt):
        self.manager.current = "lista"


class PantallaLista(Screen):
    """Pantalla que muestra la lista de todas las notas guardadas."""

    orden_por_titulo = False
    nota_pendiente_de_eliminar = None
    evento_deshacer = None

    def on_pre_enter(self):
        self.refrescar_notas()

    def cambiar_orden(self):
        self.orden_por_titulo = not self.orden_por_titulo
        self.ids.boton_orden.text = "🔤 Título" if self.orden_por_titulo else "📅 Fecha"
        self.refrescar_notas()

    def refrescar_notas(self):
        contenedor = self.ids.contenedor_notas
        contenedor.clear_widgets()
        app = App.get_running_app()

        texto_busqueda = self.ids.campo_busqueda.text.strip().lower()
        notas_visibles = [
            n for n in app.notas if texto_busqueda in n["titulo"].lower()
        ]

        if self.orden_por_titulo:
            notas_ordenadas = sorted(notas_visibles, key=lambda n: n["titulo"].lower())
        else:
            notas_ordenadas = sorted(
                notas_visibles, key=lambda n: n.get("creado_en_iso", ""), reverse=True
            )

        # Las notas favoritas siempre van primero, sin importar el orden elegido
        notas_ordenadas = sorted(
            notas_ordenadas, key=lambda n: not n.get("favorita", False)
        )

        self.ids.etiqueta_contador.text = (
            f"{len(app.notas)} nota" + ("" if len(app.notas) == 1 else "s")
        )

        if not notas_ordenadas:
            mensaje = (
                "No se encontraron notas con ese título."
                if texto_busqueda
                else "Todavía no tienes notas.\n¡Crea la primera! 🌸"
            )
            contenedor.add_widget(
                Label(text=mensaje, size_hint_y=None, height=80, color=COLOR_TEXTO_SUAVE)
            )
            return

        for nota in notas_ordenadas:
            contenedor.add_widget(self._crear_fila_nota(nota))

    def _crear_fila_nota(self, nota):
        fila = BoxLayout(size_hint_y=None, height=76, spacing=6)

        boton_favorita = Button(
            text="⭐" if nota.get("favorita", False) else "☆",
            size_hint_x=None,
            width=44,
            background_normal="",
            background_color=COLOR_FAVORITA if nota.get("favorita", False) else COLOR_BOTON,
            color=(1, 1, 1, 1),
        )
        boton_favorita.bind(on_release=lambda x, n=nota: self._alternar_favorita(n))
        fila.add_widget(boton_favorita)

        info = BoxLayout(orientation="vertical")
        info.add_widget(
            Label(
                text=nota["titulo"] or "(sin título)",
                bold=True,
                font_size=17,
                halign="left",
                text_size=(None, None),
                color=COLOR_TEXTO,
            )
        )
        info.add_widget(
            Label(
                text=f"Creada: {nota['creado_en']}",
                font_size=12,
                color=COLOR_TEXTO_SUAVE,
            )
        )
        fila.add_widget(info)

        boton_ver = Button(
            text="Ver", size_hint_x=None, width=60,
            background_normal="", background_color=COLOR_ACENTO, color=(1, 1, 1, 1),
        )
        boton_ver.bind(on_release=lambda x, n=nota: self._ver(n))
        fila.add_widget(boton_ver)

        boton_editar = Button(
            text="Editar", size_hint_x=None, width=80,
            background_normal="", background_color=COLOR_BOTON, color=COLOR_TEXTO,
        )
        boton_editar.bind(on_release=lambda x, n=nota: self._editar(n))
        fila.add_widget(boton_editar)

        boton_eliminar = Button(
            text="Eliminar", size_hint_x=None, width=90,
            background_normal="", background_color=COLOR_BOTON_ELIMINAR, color=(1, 1, 1, 1),
        )
        boton_eliminar.bind(on_release=lambda x, n=nota: self._confirmar_eliminar(n))
        fila.add_widget(boton_eliminar)

        return fila

    def _alternar_favorita(self, nota):
        app = App.get_running_app()
        for n in app.notas:
            if n["id"] == nota["id"]:
                n["favorita"] = not n.get("favorita", False)
                break
        app.guardar_notas()
        self.refrescar_notas()

    def _ver(self, nota):
        pantalla_ver = self.manager.get_screen("ver")
        pantalla_ver.cargar_nota(nota)
        self.manager.current = "ver"

    def _editar(self, nota):
        pantalla_editar = self.manager.get_screen("editar")
        pantalla_editar.cargar_nota(nota)
        self.manager.current = "editar"

    def mostrar_mensaje_temporal(self, texto):
        self.ids.etiqueta_mensaje_temporal.text = texto
        Clock.schedule_once(self._limpiar_mensaje_temporal, SEGUNDOS_MENSAJE_TEMPORAL)

    def _limpiar_mensaje_temporal(self, dt):
        self.ids.etiqueta_mensaje_temporal.text = ""

    # ---------------- Eliminar con confirmación y opción de deshacer ----------------

    def _confirmar_eliminar(self, nota):
        contenido = BoxLayout(orientation="vertical", spacing=12, padding=12)
        contenido.add_widget(
            Label(
                text=f"¿Seguro que quieres eliminar\n\"{nota['titulo'] or '(sin título)'}\"?",
                color=COLOR_TEXTO,
                halign="center",
            )
        )
        fila_botones = BoxLayout(size_hint_y=None, height=48, spacing=10)

        popup = Popup(
            title="Confirmar eliminación",
            content=contenido,
            size_hint=(0.8, 0.4),
            auto_dismiss=False,
        )

        boton_si = Button(
            text="Sí, eliminar", background_normal="", background_color=COLOR_BOTON_ELIMINAR, color=(1, 1, 1, 1)
        )
        boton_no = Button(
            text="Cancelar", background_normal="", background_color=COLOR_BOTON, color=COLOR_TEXTO
        )

        def confirmar(instancia):
            popup.dismiss()
            self._eliminar_con_deshacer(nota)

        def cancelar(instancia):
            popup.dismiss()

        boton_si.bind(on_release=confirmar)
        boton_no.bind(on_release=cancelar)
        fila_botones.add_widget(boton_no)
        fila_botones.add_widget(boton_si)
        contenido.add_widget(fila_botones)

        popup.open()

    def _eliminar_con_deshacer(self, nota):
        app = App.get_running_app()
        app.notas = [n for n in app.notas if n["id"] != nota["id"]]
        self.refrescar_notas()

        self.nota_pendiente_de_eliminar = nota
        self._mostrar_barra_deshacer()
        self.evento_deshacer = Clock.schedule_once(
            self._finalizar_eliminacion, SEGUNDOS_PARA_DESHACER
        )

    def _mostrar_barra_deshacer(self):
        contenedor = self.ids.contenedor_deshacer
        contenedor.clear_widgets()
        contenedor.height = 44
        contenedor.opacity = 1

        etiqueta = Label(text="Nota eliminada", color=COLOR_TEXTO, halign="left")
        boton_deshacer = Button(
            text="Deshacer", size_hint_x=None, width=110,
            background_normal="", background_color=COLOR_ACENTO, color=(1, 1, 1, 1),
        )
        boton_deshacer.bind(on_release=self._deshacer_eliminacion)

        contenedor.add_widget(etiqueta)
        contenedor.add_widget(boton_deshacer)

    def _ocultar_barra_deshacer(self):
        contenedor = self.ids.contenedor_deshacer
        contenedor.clear_widgets()
        contenedor.height = 0
        contenedor.opacity = 0

    def _deshacer_eliminacion(self, instancia):
        if self.evento_deshacer:
            self.evento_deshacer.cancel()
            self.evento_deshacer = None

        if self.nota_pendiente_de_eliminar:
            app = App.get_running_app()
            app.notas.append(self.nota_pendiente_de_eliminar)
            self.nota_pendiente_de_eliminar = None

        self._ocultar_barra_deshacer()
        self.refrescar_notas()

    def _finalizar_eliminacion(self, dt):
        # Pasado el tiempo de espera, la eliminación se vuelve permanente
        app = App.get_running_app()
        app.guardar_notas()
        self.nota_pendiente_de_eliminar = None
        self.evento_deshacer = None
        self._ocultar_barra_deshacer()


class PantallaEditar(Screen):
    """Pantalla para crear o editar una nota."""

    id_nota_actual = None

    def nueva_nota(self):
        self.id_nota_actual = None
        self.ids.campo_titulo.text = ""
        self.ids.campo_contenido.text = ""
        self.ids.etiqueta_fecha.text = ""
        self.manager.current = "editar"

    def cargar_nota(self, nota):
        self.id_nota_actual = nota["id"]
        self.ids.campo_titulo.text = nota["titulo"]
        self.ids.campo_contenido.text = nota["contenido_md"]
        self.ids.etiqueta_fecha.text = f"Creada: {nota['creado_en']}"

    def guardar_nota(self):
        app = App.get_running_app()
        titulo = self.ids.campo_titulo.text.strip()
        contenido_md = self.ids.campo_contenido.text

        if md_lib:
            contenido_html = md_lib.markdown(contenido_md)
        else:
            contenido_html = contenido_md

        if self.id_nota_actual:
            for n in app.notas:
                if n["id"] == self.id_nota_actual:
                    n["titulo"] = titulo
                    n["contenido_md"] = contenido_md
                    n["contenido_html"] = contenido_html
                    break
        else:
            ahora = datetime.now()
            nueva = {
                "id": str(uuid.uuid4()),
                "titulo": titulo,
                "contenido_md": contenido_md,
                "contenido_html": contenido_html,
                "creado_en": ahora.strftime("%d/%m/%Y %H:%M"),
                "creado_en_iso": ahora.isoformat(),
                "favorita": False,
            }
            app.notas.append(nueva)

        app.guardar_notas()
        self.manager.current = "lista"
        self.manager.get_screen("lista").mostrar_mensaje_temporal("✓ Nota guardada")


class PantallaVer(Screen):
    """Pantalla que muestra la nota ya formateada (negrita, títulos, etc. reales)."""

    nota_actual = None

    def cargar_nota(self, nota):
        self.nota_actual = nota
        self.ids.etiqueta_titulo_ver.text = nota["titulo"] or "(sin título)"
        self.ids.etiqueta_fecha_ver.text = f"Creada: {nota['creado_en']}"
        self.ids.etiqueta_contenido_ver.text = markdown_a_texto_visual(nota["contenido_md"])

    def editar(self):
        pantalla_editar = self.manager.get_screen("editar")
        pantalla_editar.cargar_nota(self.nota_actual)
        self.manager.current = "editar"


class NotasApp(App):
    notas = []

    def build(self):
        Window.clearcolor = COLOR_FONDO
        Builder.load_string(KV)
        self.cargar_notas()

        gestor = ScreenManager()
        gestor.add_widget(PantallaSplash(name="splash"))
        gestor.add_widget(PantallaLista(name="lista"))
        gestor.add_widget(PantallaEditar(name="editar"))
        gestor.add_widget(PantallaVer(name="ver"))
        gestor.current = "splash"
        return gestor

    def _ruta_archivo_datos(self):
        return os.path.join(self.user_data_dir, NOMBRE_ARCHIVO_DATOS)

    def cargar_notas(self):
        ruta = self._ruta_archivo_datos()
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                self.notas = json.load(f)
        else:
            self.notas = []

    def guardar_notas(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        ruta = self._ruta_archivo_datos()
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(self.notas, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    NotasApp().run()
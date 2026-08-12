"""
Prueba mínima - Paso 0
Este archivo NO es la app de notas todavía. Solo sirve para comprobar
que Kivy quedó bien instalado antes de escribir la app completa.

Cómo probarlo:
1. Guarda este archivo como prueba.py en tu carpeta:
   C:\\Users\\sm047\\Downloads\\pryecto Feria de logros notas
2. En la misma terminal donde ya instalaste kivy (con el entorno virtual activado),
   ejecuta:
   python prueba.py
3. Debería abrirse una ventana con un botón que dice "¡Funciona!".
   Si le das clic, el texto del botón cambia.

Si esta ventana se abre sin errores, ya puedes pasar al main.py de la app de notas.
"""

from kivy.app import App
from kivy.uix.button import Button


class AppDePrueba(App):
    def build(self):
        boton = Button(text="¡Funciona!", font_size=30)
        boton.bind(on_release=self.cambiar_texto)
        return boton

    def cambiar_texto(self, instancia_boton):
        instancia_boton.text = "Kivy está instalado correctamente 🎉"


if __name__ == "__main__":
    AppDePrueba().run()
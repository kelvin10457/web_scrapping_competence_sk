"""Motores reutilizados por mas de un pais (mismo sitio, distinto catalogo).

Cada pais tiene su propio modulo `paises/<pais>/<empresa>.py` que llama a estos
motores con sus parametros; si un pais necesita divergir, se cambia ese modulo
sin tocar a los demas.
"""

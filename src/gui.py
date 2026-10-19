"""GUI de escritorio para correr el pipeline sin usar terminal.

Doble clic (o `python src/gui.py`) abre una ventana con una tarjeta por
empresa. Al presionar "Scrapear seleccionados" cada empresa corre en su
propio hilo secuencial dentro de un try/except: si una falla, se marca en
rojo con el error visible y las demas siguen corriendo (mismo criterio de
aislamiento que pipeline.main). Al terminar se regenera master.csv/xlsx.

Empaquetado a .exe: `pyinstaller --onefile --windowed src/gui.py`
"""
from __future__ import annotations

import os
import sys
import threading
import traceback
from pathlib import Path
from tkinter import Tk, BooleanVar, END, Toplevel, Text
from tkinter import ttk, messagebox, scrolledtext, filedialog

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manual_store  # noqa: E402
import merge_human  # noqa: E402
import pipeline  # noqa: E402
import schema  # noqa: E402

ESTADO_PENDIENTE = "pendiente"
ESTADO_CORRIENDO = "corriendo"
ESTADO_OK = "ok"
ESTADO_ERROR = "error"

ESTADO_TEXTO = {
    ESTADO_PENDIENTE: "En espera",
    ESTADO_CORRIENDO: "Corriendo...",
    ESTADO_OK: "Completado",
    ESTADO_ERROR: "Error",
}

# Paleta neutra, alto contraste, apta para light/dark de Windows.
COLOR_BG = "#f3f4f6"
COLOR_CARD = "#ffffff"
COLOR_CARD_BORDER = "#e2e4e9"
COLOR_TEXT = "#1f2430"
COLOR_TEXT_MUTED = "#6b7280"
COLOR_ACCENT = "#2563eb"
COLOR_ACCENT_HOVER = "#1d4ed8"
COLOR_OK = "#16a34a"
COLOR_OK_BG = "#dcfce7"
COLOR_ERROR = "#dc2626"
COLOR_ERROR_BG = "#fee2e2"
COLOR_PENDIENTE = "#9ca3af"
COLOR_CORRIENDO = "#d97706"
COLOR_CORRIENDO_BG = "#fef3c7"

FUSION_MANUAL_KEY = "fusion_manual"

NOMBRES_EMPRESA = {
    "nicovita": "Nicovita",
    "haid": "HAID",
    "aquaxcel": "Aquaxcel (Cargill)",
    "biomar": "BioMar (via Agrizon)",
    "agripac": "Agripac",
    # No es una empresa scrapeada -- se agrega aca para que _mostrar_error()
    # (que busca el nombre bonito por esta misma tabla) le pueda dar titulo
    # sin necesitar un dict aparte solo para este caso.
    FUSION_MANUAL_KEY: "Fusión con datos manuales",
}

FONT_FAMILY = "Segoe UI"

# Valores de "empresa" que ya escriben los parsers (ver schema.empty_record()
# en cada src/parsers/*.py) -- el formulario manual usa los mismos textos
# para que el matching por nombre (merge_human.find_name_candidates) los
# reconozca contra el master ya scrapeado. Combobox editable (no restringido
# a esta lista) por si aparece un competidor nuevo que todavia no se scrapea.
EMPRESAS_MANUAL = ["Nicovita", "HAID", "Cargill", "BioMar", "Agripac"]

# Campos editables del formulario manual, en el orden en que se muestran.
# Se excluyen a proposito: fuente_url/fecha_extraccion (se autogeneran,
# ver ManualRecordDialog._build_record) y etapa_skt/particula_min_mm/
# particula_max_mm (siempre derivadas, igual que en merge_human.apply_merge
# -- nunca se toma un valor que el humano haya escrito ahi).
FORM_FIELDS = [
    ("empresa", "Empresa", "combobox", EMPRESAS_MANUAL),
    ("nombre_producto", "Nombre del producto", "entry", None),
    ("etapa_competidor", "Etapa (competidor)", "combobox", sorted(schema.ETAPA_VALUES)),
    ("producto_salud", "¿Producto de salud?", "combobox", ["True", "False"]),
    ("tamano_pellet_mm", "Tamaño de pellet (mm)", "entry", None),
    ("tipo_presentacion", "Tipo de presentación", "combobox", sorted(schema.TIPO_PRESENTACION_VALUES)),
    ("empaque_kg", "Empaque (kg)", "entry", None),
    ("proteina_pct", "Proteína (%)", "entry", None),
]


class EmpresaCard:
    """Tarjeta visual por empresa: checkbox, nombre, badge de estado, boton detalle."""

    def __init__(self, parent: "ttk.Frame", empresa: str, on_ver_detalle) -> None:
        self.empresa = empresa
        self.estado = ESTADO_PENDIENTE
        self.var = BooleanVar(value=True)

        self.frame = ttk.Frame(parent, style="Card.TFrame", padding=(14, 10))
        self.frame.columnconfigure(1, weight=1)

        self.check = ttk.Checkbutton(
            self.frame, variable=self.var, style="Card.TCheckbutton"
        )
        self.check.grid(row=0, column=0, sticky="w")

        nombre = NOMBRES_EMPRESA.get(empresa, empresa)
        self.nombre_lbl = ttk.Label(
            self.frame, text=nombre, style="CardTitle.TLabel"
        )
        self.nombre_lbl.grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.badge = ttk.Label(
            self.frame, text=ESTADO_TEXTO[ESTADO_PENDIENTE], style="BadgePendiente.TLabel"
        )
        self.badge.grid(row=0, column=2, sticky="e", padx=(8, 8))

        self.detalle_btn = ttk.Button(
            self.frame, text="Ver detalle", style="Link.TButton",
            command=lambda: on_ver_detalle(empresa), state="disabled",
        )
        self.detalle_btn.grid(row=0, column=3, sticky="e")

    def set_estado(self, estado: str, extra: str = "") -> None:
        self.estado = estado
        estilo_map = {
            ESTADO_PENDIENTE: "BadgePendiente.TLabel",
            ESTADO_CORRIENDO: "BadgeCorriendo.TLabel",
            ESTADO_OK: "BadgeOk.TLabel",
            ESTADO_ERROR: "BadgeError.TLabel",
        }
        texto = ESTADO_TEXTO[estado] + (f" {extra}" if extra else "")
        self.badge.configure(text=texto, style=estilo_map[estado])
        self.detalle_btn.configure(state=("normal" if estado == ESTADO_ERROR else "disabled"))

    def pack(self, **kwargs) -> None:
        self.frame.pack(**kwargs)


class ManualRecordDialog:
    """Formulario para agregar o corregir un producto a mano (conversacion
    con el usuario, 2026-09-16). Antes de guardar, busca TODOS los productos
    con el mismo empresa+nombre_producto en el master actual --
    merge_human.find_name_candidates(), que a proposito NO filtra todavia
    por tamano/proteina -- y se los muestra al usuario para que confirme a
    ojo si es un producto ya existente (una variante por etapa/tamano con el
    mismo nombre) o uno nuevo, en vez de dejar que el matching automatico
    decida solo -- ahi es donde nombres repetidos con atributos distintos se
    prestan a error.

    Guarda siempre en data/competencia_manual.db (SQLite, ver
    manual_store.py) -- nunca escribe directo sobre master_prototipo.xlsx,
    para que el registro sobreviva a la proxima corrida de scraping (que
    regenera master_prototipo.xlsx desde cero)."""

    def __init__(self, parent: Tk, app: "App") -> None:
        self.app = app
        self._candidate_master_df: pd.DataFrame | None = None

        self.dlg = Toplevel(parent)
        self.dlg.title("Agregar o corregir producto manual")
        self.dlg.geometry("680x620")
        self.dlg.minsize(560, 480)
        self.dlg.configure(bg=COLOR_BG)
        self.dlg.transient(parent)
        self.dlg.grab_set()

        self.vars: dict[str, ttk.Entry] = {}
        self._build_form()
        self._build_candidates()
        self._build_actions()

    # ---------- construccion ----------

    def _build_form(self) -> None:
        wrap = ttk.Frame(self.dlg, padding=(16, 14, 16, 6))
        wrap.pack(fill="x")
        wrap.columnconfigure(1, weight=1)
        for row, (col, label, kind, options) in enumerate(FORM_FIELDS):
            ttk.Label(wrap, text=label, background=COLOR_BG, foreground=COLOR_TEXT).grid(
                row=row, column=0, sticky="w", pady=3, padx=(0, 10)
            )
            if kind == "combobox":
                widget = ttk.Combobox(wrap, values=[""] + list(options), state="normal")
            else:
                widget = ttk.Entry(wrap)
            widget.grid(row=row, column=1, sticky="ew", pady=3)
            self.vars[col] = widget

    def _build_candidates(self) -> None:
        wrap = ttk.Frame(self.dlg, padding=(16, 6, 16, 6))
        wrap.pack(fill="both", expand=True)

        ttk.Button(
            wrap, text="Buscar coincidencias por nombre", style="Secondary.TButton",
            command=self._buscar_coincidencias,
        ).pack(anchor="w", pady=(0, 6))

        columns = ("nombre", "etapa", "tamano", "tipo", "proteina", "empaque", "fuente")
        headers = {
            "nombre": "Nombre", "etapa": "Etapa", "tamano": "Tamaño mm",
            "tipo": "Tipo", "proteina": "Proteína %", "empaque": "Empaque kg",
            "fuente": "Fuente",
        }
        self.tree = ttk.Treeview(wrap, columns=columns, show="headings", height=8, selectmode="browse")
        for c in columns:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=90, anchor="w")
        self.tree.column("fuente", width=180)
        self.tree.pack(fill="both", expand=True)

        self.candidates_status = ttk.Label(
            wrap, text="Escribe empresa + nombre y presiona \"Buscar coincidencias\".",
            background=COLOR_BG, foreground=COLOR_TEXT_MUTED,
        )
        self.candidates_status.pack(anchor="w", pady=(6, 0))

    def _build_actions(self) -> None:
        wrap = ttk.Frame(self.dlg, padding=(16, 8, 16, 14))
        wrap.pack(fill="x")
        ttk.Button(
            wrap, text="Es este producto (corregir)", style="Secondary.TButton",
            command=self._guardar_como_correccion,
        ).pack(side="left")
        ttk.Button(
            wrap, text="Es un producto nuevo", style="Accent.TButton",
            command=self._guardar_como_nuevo,
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            wrap, text="Cancelar", style="Secondary.TButton",
            command=self.dlg.destroy,
        ).pack(side="right")

    # ---------- logica ----------

    def _get(self, col: str) -> str:
        return self.vars[col].get().strip()

    def _load_master_df(self) -> pd.DataFrame | None:
        path = merge_human.OUTPUT_PATH if merge_human.OUTPUT_PATH.exists() else merge_human.MASTER_PATH
        if not path.exists():
            return None
        return pd.read_excel(path)

    def _buscar_coincidencias(self) -> None:
        empresa = self._get("empresa")
        nombre = self._get("nombre_producto")
        if not empresa or not nombre:
            messagebox.showwarning(
                "Faltan datos", "Escribe empresa y nombre del producto antes de buscar.", parent=self.dlg,
            )
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        master_df = self._load_master_df()
        self._candidate_master_df = master_df
        if master_df is None:
            self.candidates_status.configure(
                text="No hay master.xlsx / master_prototipo.xlsx todavía -- corre el scraping primero."
            )
            return

        candidates = merge_human.find_name_candidates(master_df, empresa, nombre)
        if len(candidates) == 0:
            self.candidates_status.configure(text="Sin coincidencias por nombre -- parece un producto nuevo.")
            return

        for idx in candidates:
            row = master_df.loc[idx]
            self.tree.insert(
                "", "end", iid=str(idx),
                values=(
                    row["nombre_producto"],
                    row["etapa_competidor"] if pd.notna(row["etapa_competidor"]) else "",
                    row["tamano_pellet_mm"] if pd.notna(row["tamano_pellet_mm"]) else "",
                    row["tipo_presentacion"] if pd.notna(row["tipo_presentacion"]) else "",
                    row["proteina_pct"] if pd.notna(row["proteina_pct"]) else "",
                    row["empaque_kg"] if pd.notna(row["empaque_kg"]) else "",
                    row["fuente_url"] if pd.notna(row["fuente_url"]) else "",
                ),
            )
        self.candidates_status.configure(
            text=f"{len(candidates)} coincidencia(s) por nombre -- revisa si alguna es el mismo producto."
        )

    def _build_record(self) -> dict:
        record = {col: None for col in schema.SCHEMA_COLUMNS}
        for col, _, _, _ in FORM_FIELDS:
            value = self._get(col)
            record[col] = value if value else None
        record["fuente_url"] = "revision manual"
        record["fecha_extraccion"] = manual_store.today_str()
        return record

    def _validar(self, record: dict) -> list[str]:
        df = pd.DataFrame([record], columns=schema.SCHEMA_COLUMNS)
        return merge_human.validate_rows(df)

    def _guardar(self, record: dict, mensaje_log: str) -> None:
        errors = self._validar(record)
        if errors:
            messagebox.showerror(
                "Datos inválidos", "No se pudo guardar:\n" + "\n".join(f"- {e}" for e in errors),
                parent=self.dlg,
            )
            return
        manual_store.insert_record(record)
        self.app._log(mensaje_log)
        self.dlg.destroy()
        self.app._refrescar_tras_manual()

    def _guardar_como_nuevo(self) -> None:
        record = self._build_record()
        if not record["empresa"] or not record["nombre_producto"]:
            messagebox.showwarning(
                "Faltan datos", "Empresa y nombre del producto son obligatorios.", parent=self.dlg,
            )
            return
        self._guardar(
            record,
            f"Manual: agregado '{record['nombre_producto']}' ({record['empresa']}) como producto nuevo.",
        )

    def _guardar_como_correccion(self) -> None:
        seleccion = self.tree.selection()
        if not seleccion or self._candidate_master_df is None:
            messagebox.showwarning(
                "Selecciona una coincidencia",
                "Selecciona en la lista cuál producto existente es este, o usa \"Es un producto nuevo\".",
                parent=self.dlg,
            )
            return
        idx = int(seleccion[0])
        candidato = self._candidate_master_df.loc[idx]
        record = self._build_record()
        # Fija la clave de matching (tamano/proteina) con los valores del
        # candidato elegido si el usuario los dejo en blanco -- si no, la
        # proxima fusion vuelve a ver el mismo nombre ambiguo entre varias
        # filas y esta correccion no sabria a cual de todas aplicarse.
        if record["tamano_pellet_mm"] is None and pd.notna(candidato["tamano_pellet_mm"]):
            record["tamano_pellet_mm"] = candidato["tamano_pellet_mm"]
        if record["proteina_pct"] is None and pd.notna(candidato["proteina_pct"]):
            record["proteina_pct"] = candidato["proteina_pct"]
        self._guardar(
            record,
            f"Manual: corregido '{record['nombre_producto']}' ({record['empresa']}) "
            f"identificado por tamaño={record['tamano_pellet_mm']}, proteína={record['proteina_pct']}.",
        )


class App:
    def __init__(self, root: Tk) -> None:
        self.root = root
        root.title("Scraper de Competencia - Camaronicultura")
        root.geometry("700x680")
        root.minsize(640, 560)
        root.configure(bg=COLOR_BG)

        self._setup_styles()

        self.cards: dict[str, EmpresaCard] = {}
        self.errores: dict[str, str] = {}
        self.running = False
        # None hasta que el usuario elige uno explicitamente -- si sigue en
        # None al correr la fusion, se usa data/competencia_human.xlsx por
        # defecto si existe (ver _ruta_datos_humanos_efectiva). Solo dura la
        # sesion, no se persiste entre ejecuciones del programa.
        self.human_data_path: Path | None = None
        # .db de companeros importados esta sesion (ver _importar_companeros)
        # -- se suman al almacen local (manual_store.DEFAULT_DB_PATH) y al
        # xlsx legado como fuentes de la fusion, ver _recolectar_fuentes_humanas.
        self.companero_paths: list[Path] = []
        # None: la fusion no corrio. "vacio": corrio pero no habia ninguna
        # fuente de datos manuales con filas. "error": fallo validacion o
        # hubo una excepcion. tuple (n_new, n_updated, n_ambiguos): corrio bien.
        self.fusion_resultado = None

        self._build_header()
        self._build_cards_section()
        self._build_actions()
        self._build_progress()
        self._build_log()

    # ---------- estilos ----------

    def _setup_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background=COLOR_BG)
        style.configure("Card.TFrame", background=COLOR_CARD, relief="flat")
        style.configure(
            "Header.TFrame", background=COLOR_BG
        )

        style.configure(
            "Title.TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
            font=(FONT_FAMILY, 16, "bold"),
        )
        style.configure(
            "Subtitle.TLabel", background=COLOR_BG, foreground=COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, 9),
        )
        style.configure(
            "Section.TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
            font=(FONT_FAMILY, 10, "bold"),
        )
        style.configure(
            "CardTitle.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT,
            font=(FONT_FAMILY, 10),
        )

        for name, fg, bg in [
            ("Pendiente", COLOR_PENDIENTE, COLOR_BG),
            ("Corriendo", COLOR_CORRIENDO, COLOR_CORRIENDO_BG),
            ("Ok", COLOR_OK, COLOR_OK_BG),
            ("Error", COLOR_ERROR, COLOR_ERROR_BG),
        ]:
            style.configure(
                f"Badge{name}.TLabel", background=bg, foreground=fg,
                font=(FONT_FAMILY, 9, "bold"), padding=(8, 3),
            )

        style.configure(
            "Card.TCheckbutton", background=COLOR_CARD,
        )
        style.map("Card.TCheckbutton", background=[("active", COLOR_CARD)])

        style.configure(
            "Accent.TButton", background=COLOR_ACCENT, foreground="white",
            font=(FONT_FAMILY, 10, "bold"), padding=(14, 9), borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", COLOR_ACCENT_HOVER), ("disabled", "#9ab4f0")],
            foreground=[("disabled", "white")],
        )

        style.configure(
            "Secondary.TButton", background=COLOR_BG, foreground=COLOR_TEXT,
            font=(FONT_FAMILY, 9), padding=(10, 7), borderwidth=1,
        )
        style.map("Secondary.TButton", background=[("active", "#e5e7eb")])

        style.configure(
            "Link.TButton", background=COLOR_CARD, foreground=COLOR_ACCENT,
            font=(FONT_FAMILY, 8, "underline"), padding=(4, 2), borderwidth=0,
        )
        style.map(
            "Link.TButton",
            foreground=[("disabled", COLOR_TEXT_MUTED)],
            background=[("active", COLOR_CARD)],
        )

        style.configure(
            "Accent.Horizontal.TProgressbar", background=COLOR_ACCENT,
            troughcolor="#e5e7eb", borderwidth=0, thickness=8,
        )

    # ---------- secciones ----------

    def _build_header(self) -> None:
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(20, 18, 20, 8))
        header.pack(fill="x")
        ttk.Label(header, text="Scraper de Competencia", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Selecciona los sitios a scrapear. Si uno falla, los demas continuan.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

    def _build_cards_section(self) -> None:
        section = ttk.Frame(self.root, padding=(20, 4, 20, 0))
        section.pack(fill="x")
        ttk.Label(section, text="SITIOS", style="Section.TLabel").pack(anchor="w", pady=(0, 6))

        cards_container = ttk.Frame(self.root, padding=(20, 0, 20, 0))
        cards_container.pack(fill="x")

        def on_ver_detalle(empresa: str) -> None:
            self._mostrar_error(empresa)

        for empresa in pipeline.ALL_EMPRESAS:
            card = EmpresaCard(cards_container, empresa, on_ver_detalle)
            card.pack(fill="x", pady=(0, 6))
            self._add_card_border(card.frame)
            self.cards[empresa] = card

    def _add_card_border(self, frame: ttk.Frame) -> None:
        # ttk no soporta borde+color facilmente en 'clam' via configure directo
        # en algunos temas; un frame delgado alrededor simula el borde sutil.
        frame.configure(borderwidth=1, relief="solid")

    def _build_actions(self) -> None:
        actions = ttk.Frame(self.root, padding=(20, 14, 20, 10))
        actions.pack(fill="x")

        self.run_btn = ttk.Button(
            actions, text="▶  Scrapear seleccionados", style="Accent.TButton",
            command=self._on_run,
        )
        self.run_btn.pack(side="left")

        ttk.Button(
            actions, text="Todos", style="Secondary.TButton",
            command=lambda: self._set_all(True),
        ).pack(side="left", padx=(10, 0))

        ttk.Button(
            actions, text="Ninguno", style="Secondary.TButton",
            command=lambda: self._set_all(False),
        ).pack(side="left", padx=(6, 0))

        ttk.Button(
            actions, text="Abrir carpeta de resultados", style="Secondary.TButton",
            command=self._abrir_resultados,
        ).pack(side="right")

        ttk.Button(
            actions, text="Elegir archivo de datos manuales...", style="Secondary.TButton",
            command=self._elegir_datos_humanos,
        ).pack(side="right", padx=(0, 8))

        ttk.Button(
            actions, text="Importar de compañeros...", style="Secondary.TButton",
            command=self._importar_companeros,
        ).pack(side="right", padx=(0, 8))

        ttk.Button(
            actions, text="Agregar/corregir producto manual...", style="Accent.TButton",
            command=self._abrir_formulario_manual,
        ).pack(side="right", padx=(0, 8))

    def _build_progress(self) -> None:
        wrap = ttk.Frame(self.root, padding=(20, 0, 20, 10))
        wrap.pack(fill="x")
        self.progress = ttk.Progressbar(
            wrap, mode="determinate", style="Accent.Horizontal.TProgressbar"
        )
        self.progress.pack(fill="x")

    def _build_log(self) -> None:
        wrap = ttk.Frame(self.root, padding=(20, 0, 20, 18))
        wrap.pack(fill="both", expand=True)
        ttk.Label(wrap, text="REGISTRO", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        self.log = scrolledtext.ScrolledText(
            wrap, height=12, state="disabled", relief="flat",
            bg=COLOR_CARD, fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
            font=("Consolas", 9), borderwidth=1, highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER,
        )
        self.log.pack(fill="both", expand=True)

    # ---------- acciones ----------

    def _set_all(self, value: bool) -> None:
        for card in self.cards.values():
            card.var.set(value)

    def _log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert(END, text + "\n")
        self.log.see(END)
        self.log.configure(state="disabled")

    def _mostrar_error(self, empresa: str) -> None:
        detalle = self.errores.get(empresa)
        if not detalle:
            messagebox.showinfo(empresa, "Sin errores registrados para este sitio.")
            return
        dlg = Toplevel(self.root)
        nombre = NOMBRES_EMPRESA.get(empresa, empresa)
        dlg.title(f"Detalle del error - {nombre}")
        dlg.geometry("620x420")
        dlg.configure(bg=COLOR_BG)
        ttk.Label(
            dlg, text=f"Error - {nombre}", style="Section.TLabel",
            background=COLOR_BG,
        ).pack(anchor="w", padx=14, pady=(14, 6))
        txt = Text(dlg, wrap="word", bg=COLOR_CARD, fg=COLOR_ERROR, font=("Consolas", 9))
        txt.insert("1.0", detalle)
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    def _abrir_resultados(self) -> None:
        path = pipeline.PROCESSED_DIR.parent
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)  # noqa: S606 (Windows-only helper, GUI local)

    def _elegir_datos_humanos(self) -> None:
        actual = self.human_data_path if self.human_data_path else merge_human.HUMAN_PATH
        initialdir = actual.parent if actual.parent.exists() else merge_human.HUMAN_PATH.parent
        ruta = filedialog.askopenfilename(
            parent=self.root,
            title="Elegir archivo de datos manuales",
            initialdir=str(initialdir),
            initialfile=actual.name,
            filetypes=[("Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
        )
        if not ruta:
            return
        self.human_data_path = Path(ruta)
        self._log(f"Archivo de datos manuales seleccionado: {self.human_data_path}")

    def _ruta_datos_humanos_efectiva(self) -> Path | None:
        """Ruta a usar para la fusion: la que el usuario eligio esta sesion,
        o data/competencia_human.xlsx por defecto si existe. None si no hay
        ninguna de las dos -- en ese caso la fusion simplemente no corre."""
        if self.human_data_path is not None:
            return self.human_data_path
        if merge_human.HUMAN_PATH.exists():
            return merge_human.HUMAN_PATH
        return None

    def _reportar_error_fusion(self, titulo: str, errores: list[str]) -> None:
        detalle = titulo + ":\n" + "\n".join(f"- {e}" for e in errores)
        self.errores[FUSION_MANUAL_KEY] = detalle
        self.fusion_resultado = "error"
        self.root.after(0, self._log, f"  {titulo} en datos manuales ({len(errores)}):")
        for error in errores:
            self.root.after(0, self._log, f"    - {error}")
        self.root.after(
            0, self._log, "  No se aplico ningun cambio de fusion -- el scraping si se completo bien."
        )
        self.root.after(0, self._mostrar_error, FUSION_MANUAL_KEY)

    def _recolectar_fuentes_humanas(self) -> tuple[list[tuple[str, pd.DataFrame]], list[str]]:
        """Reune todas las fuentes de datos manuales de esta corrida: el
        xlsx legado (si el usuario eligio uno o existe competencia_human.xlsx
        por defecto), el almacen local de esta laptop
        (manual_store.DEFAULT_DB_PATH, alimentado por el formulario) y
        cualquier .db de companero importado esta sesion (ver
        _importar_companeros). Cada una se valida por separado, con el
        nombre del archivo al frente de cada error, para que un archivo malo
        no impida saber cuales de los otros si estaban bien. Devuelve
        (fuentes_validas, errores) -- si errores no esta vacio, NINGUNA
        fuente debe aplicarse (mismo criterio de todo-o-nada que ya tenia la
        version de un solo archivo)."""
        fuentes: list[tuple[str, pd.DataFrame]] = []
        errores: list[str] = []

        xlsx_path = self._ruta_datos_humanos_efectiva()
        if xlsx_path is not None:
            if not xlsx_path.exists():
                errores.append(f"{xlsx_path.name}: no se encontro el archivo.")
            else:
                df = pd.read_excel(xlsx_path)
                header_errors = merge_human.validate_headers(df)
                if header_errors:
                    errores.extend(f"{xlsx_path.name}: {e}" for e in header_errors)
                else:
                    df = df[merge_human.schema.SCHEMA_COLUMNS]
                    df = merge_human._drop_fully_empty_rows(df)
                    if not df.empty:
                        row_errors = merge_human.validate_rows(df)
                        if row_errors:
                            errores.extend(f"{xlsx_path.name}: {e}" for e in row_errors)
                        else:
                            fuentes.append((xlsx_path.name, df))

        local_df = manual_store.fetch_all()
        if not local_df.empty:
            row_errors = merge_human.validate_rows(local_df)
            if row_errors:
                errores.extend(f"{manual_store.DEFAULT_DB_PATH.name}: {e}" for e in row_errors)
            else:
                fuentes.append((manual_store.DEFAULT_DB_PATH.name, local_df))

        for path in self.companero_paths:
            try:
                df = manual_store.fetch_all(path)
            except ValueError as exc:
                errores.append(str(exc))
                continue
            if df.empty:
                continue
            row_errors = merge_human.validate_rows(df)
            if row_errors:
                errores.extend(f"{path.name}: {e}" for e in row_errors)
            else:
                fuentes.append((path.name, df))

        return fuentes, errores

    def _correr_fusion_manual(self) -> None:
        """Se llama despues de que build_master() termino bien (ver
        _run_pipeline), y tambien standalone desde el formulario manual (ver
        _refrescar_tras_manual) para que master_prototipo.xlsx quede al dia
        sin tener que volver a scrapear. Usa las funciones ya existentes de
        merge_human.py -- no reimplementa matching/validacion/recalculo aca,
        solo las orquesta sobre TODAS las fuentes de _recolectar_fuentes_humanas()
        en vez de un solo archivo."""
        if not merge_human.MASTER_PATH.exists():
            self.root.after(
                0, self._log,
                f"  Fusion con datos manuales: no existe {merge_human.MASTER_PATH.name} todavia "
                "-- corre el scraping al menos una vez primero.",
            )
            self.fusion_resultado = None
            return

        self.root.after(0, self._log, "--- fusion con datos manuales ---")
        fuentes, errores = self._recolectar_fuentes_humanas()

        if errores:
            self._reportar_error_fusion("Errores de validacion en datos manuales", errores)
            return

        if not fuentes:
            self.fusion_resultado = "vacio"
            self.root.after(0, self._log, "  No hay datos manuales para fusionar -- no se aplico nada.")
            return

        try:
            master_df = pd.read_excel(merge_human.MASTER_PATH)
            human_dfs = [df for _, df in fuentes]
            master_df, review_rows, n_new, n_updated = merge_human.apply_merge_many(master_df, human_dfs)
            merge_human.write_output(master_df, review_rows)

            self.fusion_resultado = (n_new, n_updated, len(review_rows))
            nombres = ", ".join(nombre for nombre, _ in fuentes)
            self.root.after(
                0, self._log,
                f"  OK ({nombres}): {n_new} fila(s) nueva(s), {n_updated} corregida(s), "
                f"{len(review_rows)} ambigua(s) -> {merge_human.OUTPUT_PATH.name}",
            )
        except PermissionError:
            detalle = (
                f"No se pudo escribir {merge_human.OUTPUT_PATH.name}: el archivo esta abierto "
                "en Excel u otro programa. Cierralo e intenta de nuevo."
            )
            self.errores[FUSION_MANUAL_KEY] = detalle
            self.fusion_resultado = "error"
            self.root.after(0, self._log, f"  ERROR: {detalle}")
            self.root.after(0, self._mostrar_error, FUSION_MANUAL_KEY)
        except Exception:
            detalle = traceback.format_exc()
            self.errores[FUSION_MANUAL_KEY] = detalle
            self.fusion_resultado = "error"
            self.root.after(0, self._log, f"  ERROR en fusion con datos manuales (ver detalle):\n{detalle}")
            self.root.after(0, self._mostrar_error, FUSION_MANUAL_KEY)

    def _abrir_formulario_manual(self) -> None:
        ManualRecordDialog(self.root, self)

    def _importar_companeros(self) -> None:
        rutas = filedialog.askopenfilenames(
            parent=self.root,
            title="Elegir archivo(s) de datos manuales de compañeros",
            filetypes=[("Base de datos SQLite", "*.db"), ("Todos los archivos", "*.*")],
        )
        if not rutas:
            return
        self.companero_paths = [Path(r) for r in rutas]
        self._log(f"Archivos de compañeros seleccionados ({len(self.companero_paths)}):")
        for p in self.companero_paths:
            self._log(f"  - {p}")

    def _refrescar_tras_manual(self) -> None:
        """Re-corre la fusion fuera del flujo de scraping (llamada al
        guardar un registro desde el formulario manual) para que
        master_prototipo.xlsx refleje el cambio de inmediato. En un hilo
        aparte porque implica leer/escribir .xlsx (puede tardar un poco y no
        debe congelar la ventana)."""
        def worker() -> None:
            self._correr_fusion_manual()
            self.root.after(0, self._on_fusion_manual_standalone_done)

        threading.Thread(target=worker, daemon=True).start()

    def _on_fusion_manual_standalone_done(self) -> None:
        msg = self._mensaje_fusion().strip()
        if self.fusion_resultado == "error":
            messagebox.showwarning("Fusión con errores", msg or "Revisa el detalle del error.")
        else:
            messagebox.showinfo("Fusión actualizada", msg or "No había nada nuevo que fusionar.")

    def _on_run(self) -> None:
        if self.running:
            return
        seleccionadas = [e for e, c in self.cards.items() if c.var.get()]
        if not seleccionadas:
            messagebox.showwarning("Nada seleccionado", "Elige al menos un sitio.")
            return

        self.running = True
        self.run_btn.configure(state="disabled")
        self.progress.configure(maximum=len(seleccionadas), value=0)
        for empresa in seleccionadas:
            self.cards[empresa].set_estado(ESTADO_PENDIENTE)
        self.errores.clear()
        self.fusion_resultado = None
        self.log.configure(state="normal")
        self.log.delete("1.0", END)
        self.log.configure(state="disabled")

        thread = threading.Thread(target=self._run_pipeline, args=(seleccionadas,), daemon=True)
        thread.start()

    def _run_pipeline(self, empresas: list[str]) -> None:
        for empresa in empresas:
            self.root.after(0, self.cards[empresa].set_estado, ESTADO_CORRIENDO)
            self.root.after(0, self._log, f"--- {empresa} ---")
            try:
                records = pipeline.run_empresa(empresa)
                pipeline.write_csv(records, pipeline.processed_path("ecuador", empresa))
                self.root.after(
                    0, self.cards[empresa].set_estado, ESTADO_OK, f"({len(records)})"
                )
                self.root.after(0, self._log, f"  OK: {len(records)} productos")
            except Exception:
                detalle = traceback.format_exc()
                self.errores[empresa] = detalle
                self.root.after(0, self.cards[empresa].set_estado, ESTADO_ERROR)
                self.root.after(0, self._log, f"  ERROR en {empresa} (ver detalle):\n{detalle}")
            self.root.after(0, self.progress.step, 1)

        try:
            pipeline.build_master()
            self.root.after(0, self._log, f"--- master.csv regenerado en {pipeline.MASTER_PATH} ---")
            self._correr_fusion_manual()
        except PermissionError:
            self.errores["master.csv/xlsx"] = (
                "No se pudo escribir master.csv/master.xlsx: el archivo esta abierto "
                "en Excel u otro programa. Cierralo e intenta de nuevo."
            )
            self.root.after(
                0, self._log,
                "  ERROR: no se pudo regenerar master.csv/xlsx (archivo abierto en Excel). "
                "Cierralo e intenta de nuevo.",
            )
        except Exception:
            detalle = traceback.format_exc()
            self.errores["master.csv/xlsx"] = detalle
            self.root.after(0, self._log, f"  ERROR regenerando master.csv/xlsx:\n{detalle}")
        self.root.after(0, self._on_finish)

    def _mensaje_fusion(self) -> str:
        if isinstance(self.fusion_resultado, tuple):
            n_new, n_updated, n_ambiguos = self.fusion_resultado
            return (
                f"\n\nFusion con datos manuales: {n_new} fila(s) nueva(s), "
                f"{n_updated} corregida(s), {n_ambiguos} ambigua(s)."
            )
        if self.fusion_resultado == "error":
            return "\n\nFusion con datos manuales: fallo -- revisa el dialogo de detalle que se abrio."
        if self.fusion_resultado == "vacio":
            return "\n\nFusion con datos manuales: el archivo no tenia filas, no se aplico nada."
        return ""

    def _on_finish(self) -> None:
        self.running = False
        self.run_btn.configure(state="normal")
        n_err = len(self.errores)
        fusion_msg = self._mensaje_fusion()
        if n_err:
            messagebox.showwarning(
                "Terminado con errores",
                f"Proceso terminado. {n_err} sitio(s) fallaron -- revisa 'Ver detalle'." + fusion_msg,
            )
        else:
            messagebox.showinfo("Terminado", "Proceso terminado sin errores." + fusion_msg)


def main() -> None:
    root = Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

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
from tkinter import ttk, messagebox, scrolledtext

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline  # noqa: E402

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

NOMBRES_EMPRESA = {
    "nicovita": "Nicovita",
    "haid": "HAID",
    "aquaxcel": "Aquaxcel (Cargill)",
    "biomar": "BioMar (via Agrizon)",
    "agripac": "Agripac",
}

FONT_FAMILY = "Segoe UI"


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
            dlg, text=f"Error al scrapear {nombre}", style="Section.TLabel",
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
                pipeline.write_csv(records, pipeline.PROCESSED_DIR / f"{empresa}.csv")
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

    def _on_finish(self) -> None:
        self.running = False
        self.run_btn.configure(state="normal")
        n_err = len(self.errores)
        if n_err:
            messagebox.showwarning(
                "Terminado con errores",
                f"Proceso terminado. {n_err} sitio(s) fallaron -- revisa 'Ver detalle'.",
            )
        else:
            messagebox.showinfo("Terminado", "Proceso terminado sin errores.")


def main() -> None:
    root = Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

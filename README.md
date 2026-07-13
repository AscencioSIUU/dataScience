# Data Science — Repositorio del Curso

Estructura de trabajo para ejercicios, laboratorios y exámenes.

## Carpetas

| Carpeta | Contenido |
|---|---|
| `ejercicios/` | Ejercicios en clase. |
| `laboratorios/` | Laboratorios |
| `proyectos/` | Exámenes o proyectos  |

## Convención por trabajo

Cada trabajo vive en su propia carpeta y es **auto-contenido**:

```
<carpeta>/<NombreDelTrabajo>/
├── README.md          # enunciado + instrucciones de ejecución
├── requirements.txt   # dependencias Python (si aplica)
├── script_o_notebook  # el código
└── Datos/             # datos generados (ignorado por git)
```

Para correr cualquier trabajo:
```bash
pip install -r requirements.txt
python <script>.py          # o abrir el .ipynb en Jupyter
```

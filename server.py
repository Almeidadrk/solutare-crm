import os, io, sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Garante que o diretório do servidor está no PATH do Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class DadosProposta(BaseModel):
    nome: str
    cidade: str
    kwh: float = 300
    qtd_pai: int
    wp_pai: int
    marca_pai: str
    qtd_inv: int
    kw_inv: float
    marca_inv: str
    tipo_inv: Optional[str] = "Inversor"
    inv: float
    tarifa: float = 0.92

# ── Diagnóstico ──────────────────────────────────────────────────────────
@app.get("/status")
async def status():
    template_path = os.path.join(BASE_DIR, "template.pdf")
    return {
        "ok": True,
        "base_dir": BASE_DIR,
        "template_exists": os.path.exists(template_path),
        "template_size_kb": round(os.path.getsize(template_path)/1024) if os.path.exists(template_path) else 0,
        "files": os.listdir(BASE_DIR),
    }

# ── Geração do PDF ───────────────────────────────────────────────────────
@app.post("/gerar-proposta")
async def gerar_proposta_endpoint(dados: DadosProposta):
    try:
        # Importa com caminho garantido
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "gerar_proposta",
            os.path.join(BASE_DIR, "gerar_proposta.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        dados_dict = dados.dict()
        buf = io.BytesIO()
        mod.gerar_proposta(dados_dict, buf)
        buf.seek(0)

        nome_arquivo = f"Proposta_{dados.nome.replace(' ', '_')}.pdf"

        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{nome_arquivo}"'
            }
        )
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "trace": traceback.format_exc()}
        )

# ── Frontend estático ────────────────────────────────────────────────────
app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)

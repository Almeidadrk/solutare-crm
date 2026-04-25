import os, io, math
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Modelo de dados da proposta ──────────────────────────────────────────
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
    inv: float          # preço de venda calculado
    tarifa: float = 0.92

# ── Endpoint geração de PDF ──────────────────────────────────────────────
@app.post("/gerar-proposta")
async def gerar_proposta_endpoint(dados: DadosProposta):
    try:
        from gerar_proposta import gerar_proposta

        dados_dict = dados.dict()

        # Gera em memória
        buf = io.BytesIO()
        gerar_proposta(dados_dict, buf)
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
        raise HTTPException(status_code=500, detail=str(e))

# ── Serve o frontend estático ────────────────────────────────────────────
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)

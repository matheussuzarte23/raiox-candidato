from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "dados" / "elosys.db"

app = FastAPI(title="Raio-X do Candidato", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    return con


# ============ TRADUÇÕES DE LINGUAGEM TÉCNICA ============
TRADUCOES = {
    "circular_donation": {
        "titulo": "💸 Dinheiro que sai e volta",
        "explicacao": "Dinheiro doado para uma campanha que, em vez de ser gasto, volta para o mesmo grupo por caminhos estranhos.",
        "porque_importa": "Isso pode ser usado para esconder a origem do dinheiro."
    },
    "disproportionate_expense": {
        "titulo": "🎈 Gasto fora do normal",
        "explicacao": "Uma compra foi feita por um valor muito maior do que o normal para aquele tipo de produto.",
        "porque_importa": "Pode indicar superfaturamento ou desvio."
    },
    "cheap_item_high_value": {
        "titulo": "💰 Item barato, preço absurdo",
        "explicacao": "O candidato gastou muito dinheiro em um material que normalmente é barato (como adesivos, panfletos ou canetas). No caso, o valor foi 39 vezes maior que a média histórica.",
        "porque_importa": "Pode ser superfaturamento, compra em lote não detalhada ou erro de digitação. Merece verificação."
    },
    "candidate_supplier_partner": {
        "titulo": "🤝 Amigo do fornecedor",
        "explicacao": "O candidato é sócio de uma empresa que recebeu dinheiro da própria campanha.",
        "porque_importa": "Pode ser conflito de interesse."
    },
}

# ============ HELPERS ============
def pluralizar(qtd, singular, plural):
    return singular if qtd == 1 else plural


def calcular_nota(sinais, doacoes_reais, bens_reais):
    """Calcula nota de 0 a 100 e classificação"""
    nota = 100
    for s in sinais:
        if s["severity"] == "high":
            nota -= 8
        elif s["severity"] == "medium":
            nota -= 2
        else:
            nota -= 0.5
        if s.get("amount_cents") and s["amount_cents"] > 100_000_000:
            nota -= 3

    nota = max(0, min(100, round(nota)))

    if nota >= 85:
        classificacao, cor, emoji = "BOM", "verde", "🟢"
        titulo = "Poucos alertas"
    elif nota >= 70:
        classificacao, cor, emoji = "ATENÇÃO", "amarelo", "🟡"
        titulo = "Atenção moderada"
    elif nota >= 50:
        classificacao, cor, emoji = "ALERTA", "laranja", "🟠"
        titulo = "Vários alertas"
    else:
        classificacao, cor, emoji = "CRÍTICO", "vermelho", "🔴"
        titulo = "Muitos alertas"

    return {
        "nota": nota,
        "classificacao": classificacao,
        "cor": cor,
        "emoji": emoji,
        "titulo": titulo,
    }


def calcular_cor_nota(total_sinais, high, medium, low, valor_alto):
    """Versão usada pelo ranking (a partir de contadores)"""
    nota = 100
    nota -= (high or 0) * 8
    nota -= (medium or 0) * 2
    nota -= (low or 0) * 0.5
    nota -= (valor_alto or 0) * 3
    nota = max(0, min(100, round(nota)))

    if nota >= 85:
        cor = "verde"
    elif nota >= 70:
        cor = "amarelo"
    elif nota >= 50:
        cor = "laranja"
    else:
        cor = "vermelho"

    return nota, cor


def gerar_analogias(doacoes_reais):
    """Transforma valores em coisas do dia a dia (com plural correto)"""
    if not doacoes_reais or doacoes_reais < 1000:
        return []

    analogias = []

    casas = int(doacoes_reais / 300_000)
    if casas >= 1:
        analogias.append({
            "icone": "🏠",
            "texto": f"{casas:,} {pluralizar(casas, 'casa popular', 'casas populares')}".replace(",", "."),
            "descricao": "Isso daria para construir"
        })

    carros = int(doacoes_reais / 70_000)
    if carros >= 1:
        analogias.append({
            "icone": "🚗",
            "texto": f"{carros:,} {pluralizar(carros, 'carro popular', 'carros populares')}".replace(",", "."),
            "descricao": "Isso daria para comprar"
        })

    anos_salario = int(doacoes_reais / 16_944)
    if anos_salario >= 1:
        analogias.append({
            "icone": "💼",
            "texto": f"{anos_salario:,} {pluralizar(anos_salario, 'ano de salário mínimo', 'anos de salário mínimo')}".replace(",", "."),
            "descricao": "Isso equivale a"
        })

    anos_cesta = int(doacoes_reais / 9_600)
    if anos_cesta >= 1:
        analogias.append({
            "icone": "🍚",
            "texto": f"{anos_cesta:,} {pluralizar(anos_cesta, 'ano de cesta básica', 'anos de cesta básica')}".replace(",", "."),
            "descricao": "Isso alimentaria uma família por"
        })

    return analogias[:3]


def gerar_resumo(nome, nota, sinais, doacoes_reais, bens_reais, historico):
    """Gera um resumo em 3 frases"""
    frases = []

    ultimo = historico[0] if historico else None
    if ultimo:
        frases.append(
            f"{nome} é candidato a {ultimo['office']} pelo {ultimo['party_abbr']}-{ultimo['state']} em {ultimo['year']}."
        )
    else:
        frases.append(f"{nome} já concorreu a cargos públicos no Brasil.")

    if doacoes_reais > 0:
        frases.append(
            f"Recebeu R$ {doacoes_reais:,.0f} em doações de campanha e declarou R$ {bens_reais:,.0f} em bens."
            .replace(",", "X").replace(".", ",").replace("X", ".")
        )
    else:
        frases.append("Não há registro de doações de campanha na base pública.")

    if nota >= 80:
        frases.append("✅ Não foram encontrados padrões preocupantes nas contas.")
    elif nota >= 60:
        frases.append(f"⚠️ Existem {len(sinais)} pontos que merecem atenção, mas nada grave até agora.")
    elif nota >= 40:
        frases.append(f"🟠 Foram encontrados {len(sinais)} padrões atípicos que precisam ser explicados.")
    else:
        frases.append(f"🔴 A base pública registra {len(sinais)} sinais preocupantes. Isso não significa crime, mas merece investigação.")

    return frases


# ============ ENDPOINTS ============
@app.get("/")
def home():
    return {"mensagem": "Raio-X do Candidato API v2", "status": "online"}


@app.get("/api/buscar")
def buscar_candidatos(q: str = ""):
    """Busca OTIMIZADA: prioriza quem começa com o termo"""
    if len(q) < 3:
        return {"candidatos": []}

    con = get_db()
    cursor = con.cursor()

    termo = q.upper()

    cursor.execute("""
        SELECT DISTINCT p.id, p.canonical_name, ph.ballot_name,
               ph.party_abbr, ph.state, ph.office, ph.year
        FROM people p
        JOIN politician_history ph ON p.id = ph.person_id
        WHERE p.canonical_name LIKE ?
           OR ph.ballot_name LIKE ?
        ORDER BY 
            CASE WHEN p.canonical_name LIKE ? THEN 0 ELSE 1 END,
            ph.year DESC
        LIMIT 20
    """, (f"%{termo}%", f"%{termo}%", f"{termo}%"))

    candidatos = [{
        "id": row["id"], "nome": row["canonical_name"],
        "nome_urna": row["ballot_name"], "partido": row["party_abbr"],
        "estado": row["state"], "cargo": row["office"], "ano": row["year"],
    } for row in cursor.fetchall()]

    con.close()
    return {"candidatos": candidatos}


@app.get("/api/candidato/{person_id}")
def detalhes_candidato(person_id: int):
    con = get_db()
    cursor = con.cursor()

    cursor.execute("SELECT canonical_name FROM people WHERE id = ?", (person_id,))
    row = cursor.fetchone()
    if not row:
        con.close()
        raise HTTPException(status_code=404, detail="Candidato não encontrado")
    nome = row["canonical_name"]

    cursor.execute("""
        SELECT year, office, party_abbr, state, candidacy_status, result
        FROM politician_history WHERE person_id = ?
        ORDER BY year DESC
    """, (person_id,))
    historico = [dict(h) for h in cursor.fetchall()]

    cursor.execute("""
        SELECT COUNT(*) as qtd, COALESCE(SUM(amount_cents), 0) as total
        FROM campaign_donation cd
        JOIN politician_history ph ON cd.tse_candidacy_id = ph.tse_candidacy_id
        WHERE ph.person_id = ?
    """, (person_id,))
    doacoes = dict(cursor.fetchone())

    cursor.execute("""
        SELECT COUNT(*) as qtd, COALESCE(SUM(value_cents), 0) as total
        FROM declared_assets WHERE person_id = ?
    """, (person_id,))
    bens = dict(cursor.fetchone())

    cursor.execute("""
        SELECT COUNT(*) as qtd FROM signal s
        JOIN signal_actor sa ON s.id = sa.signal_id
        WHERE sa.actor_id = ? AND sa.type = 'person'
    """, (person_id,))
    total_sinais = cursor.fetchone()["qtd"]

    cursor.execute("""
        SELECT s.id, s.type, s.severity, s.explanation, s.amount_cents
        FROM signal s
        JOIN signal_actor sa ON s.id = sa.signal_id
        WHERE sa.actor_id = ? AND sa.type = 'person'
        ORDER BY s.amount_cents DESC LIMIT 15
    """, (person_id,))
    sinais_raw = [dict(s) for s in cursor.fetchall()]

    sinais = []
    for s in sinais_raw:
        trad = TRADUCOES.get(s["type"], {
            "titulo": s["type"],
            "explicacao": s["explanation"] or "Padrão atípico detectado.",
            "porque_importa": "Merece verificação."
        })
        sinais.append({
            **s,
            "titulo_simples": trad["titulo"],
            "explicacao_simples": trad["explicacao"],
            "porque_importa": trad["porque_importa"]
        })

    con.close()

    doacoes_reais = doacoes["total"] / 100
    bens_reais = bens["total"] / 100

    nota_info = calcular_nota(sinais, doacoes_reais, bens_reais)
    analogias = gerar_analogias(doacoes_reais)
    resumo = gerar_resumo(nome, nota_info["nota"], sinais, doacoes_reais, bens_reais, historico)

    return {
        "id": person_id,
        "nome": nome,
        "nota": nota_info,
        "resumo": resumo,
        "analogias": analogias,
        "historico": historico,
        "doacoes": {"quantidade": doacoes["qtd"], "total_reais": doacoes_reais},
        "bens": {"quantidade": bens["qtd"], "total_reais": bens_reais},
        "sinais": sinais,
        "total_sinais": total_sinais,
    }


@app.get("/api/filtros")
def obter_filtros():
    """Retorna as opções disponíveis para os filtros"""
    con = get_db()
    cursor = con.cursor()

    cursor.execute("SELECT DISTINCT state FROM politician_history WHERE state IS NOT NULL AND state != '' ORDER BY state")
    estados = [r["state"] for r in cursor.fetchall()]

    cursor.execute("""
        SELECT party_abbr, COUNT(*) as total
        FROM politician_history
        WHERE party_abbr IS NOT NULL AND party_abbr != ''
        GROUP BY party_abbr
        ORDER BY total DESC
        LIMIT 30
    """)
    partidos = [r["party_abbr"] for r in cursor.fetchall()]

    cursor.execute("""
        SELECT office, COUNT(*) as total
        FROM politician_history
        WHERE office IS NOT NULL
        GROUP BY office
        ORDER BY total DESC
        LIMIT 20
    """)
    cargos = [r["office"] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT year FROM politician_history ORDER BY year DESC")
    anos = [r["year"] for r in cursor.fetchall()]

    con.close()

    return {
        "estados": estados,
        "partidos": partidos,
        "cargos": cargos,
        "anos": anos,
    }


@app.get("/api/ranking")
def ranking(
    estado: str = "",
    partido: str = "",
    cargo: str = "",
    ano: int = 0,
    nivel: str = "",
    ordem: str = "pior",
    limit: int = 30,
):
    """Ranking com filtros INDEPENDENTES e COMBINÁVEIS"""
    con = get_db()
    cursor = con.cursor()

    where = ["1=1"]
    params = []

    if estado:
        where.append("ph.state = ?")
        params.append(estado)
    if partido:
        where.append("ph.party_abbr = ?")
        params.append(partido)
    if cargo:
        where.append("ph.office = ?")
        params.append(cargo)
    if ano:
        where.append("ph.year = ?")
        params.append(ano)

    where_sql = " AND ".join(where)

    candidatos = []

    # ============ 1. Buscar candidatos COM sinais (sempre) ============
    query_com_sinais = f"""
        SELECT
            p.id,
            p.canonical_name as nome,
            ph.party_abbr,
            ph.state,
            ph.office,
            ph.year,
            COUNT(DISTINCT s.id) as total_sinais,
            SUM(CASE WHEN s.severity = 'high' THEN 1 ELSE 0 END) as high,
            SUM(CASE WHEN s.severity = 'medium' THEN 1 ELSE 0 END) as medium,
            SUM(CASE WHEN s.severity = 'low' THEN 1 ELSE 0 END) as low,
            SUM(CASE WHEN s.amount_cents > 100000000 THEN 1 ELSE 0 END) as valor_alto
        FROM people p
        JOIN politician_history ph ON p.id = ph.person_id
        JOIN signal_actor sa ON sa.actor_id = p.id AND sa.type = 'person'
        JOIN signal s ON s.id = sa.signal_id
        WHERE {where_sql}
        GROUP BY p.id
        LIMIT 500
    """
    cursor.execute(query_com_sinais, params)
    rows = cursor.fetchall()

    for row in rows:
        total_sinais = row["total_sinais"] or 0
        nota, cor = calcular_cor_nota(
            total_sinais,
            row["high"] or 0,
            row["medium"] or 0,
            row["low"] or 0,
            row["valor_alto"] or 0,
        )
        candidatos.append({
            "id": row["id"],
            "nome": row["nome"],
            "partido": row["party_abbr"],
            "estado": row["state"],
            "cargo": row["office"],
            "ano": row["year"],
            "nota": nota,
            "cor": cor,
            "total_sinais": total_sinais,
        })

    # ============ 2. Se precisar, buscar candidatos SEM sinais (só verdes) ============
    # Faz sentido buscar sem sinais apenas se o usuário não filtrar por cor
    # ou se ele filtrar especificamente por verde
    if not nivel or nivel == "verde":
        query_sem_sinais = f"""
            SELECT
                p.id,
                p.canonical_name as nome,
                ph.party_abbr,
                ph.state,
                ph.office,
                ph.year
            FROM people p
            JOIN politician_history ph ON p.id = ph.person_id
            WHERE {where_sql}
              AND NOT EXISTS (
                SELECT 1 FROM signal_actor sa
                WHERE sa.actor_id = p.id AND sa.type = 'person'
              )
            GROUP BY p.id
            LIMIT 200
        """
        cursor.execute(query_sem_sinais, params)
        for row in cursor.fetchall():
            candidatos.append({
                "id": row["id"],
                "nome": row["nome"],
                "partido": row["party_abbr"],
                "estado": row["state"],
                "cargo": row["office"],
                "ano": row["year"],
                "nota": 100,
                "cor": "verde",
                "total_sinais": 0,
            })

    # ============ 3. Aplicar filtro de nível ============
    if nivel:
        candidatos = [c for c in candidatos if c["cor"] == nivel]

    # ============ 4. Ordenação ============
    if ordem == "melhor":
        # Mais transparentes: menos sinais primeiro
        candidatos.sort(key=lambda x: (x["total_sinais"], -x["nota"]))
    else:
        # Mais alertas: mais sinais primeiro
        candidatos.sort(key=lambda x: (-x["total_sinais"], x["nota"]))

    resultado = candidatos[:limit]
    con.close()
    return {"candidatos": resultado, "total": len(resultado)}


# ============ MAIN (SEMPRE NO FINAL!) ============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
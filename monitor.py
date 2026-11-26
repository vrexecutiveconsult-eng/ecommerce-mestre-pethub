import base64
import html as html_lib
import json
import logging
import os
import random
import re
import time
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import gspread
import pytz
import requests
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials

# ==============================================================================
# CONFIGURAÇÕES E CONSTANTES
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pet_bi_monitor")

BRASILIA_TZ = pytz.timezone("America/Sao_Paulo")

GOOGLE_SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TAB_USUARIOS = "Usuarios"
TAB_CONFIGURACAO = "Configuracao"
TAB_HISTORICO_HORA = "Historico_Hora"
TAB_ANUNCIOS_SALVOS = "Anuncios_Salvos"
TAB_LOJAS_MONITORADAS = "Lojas_Monitoradas"
TAB_CATALOGO_LOJAS = "Catalogo_Lojas"
TAB_CONFIG_NOTIFICACOES = "Config_Notificacoes"
TAB_HISTORICO_NOTIFICACOES = "Historico_Notificacoes"

HEADERS_CONFIGURACAO = [
    "Usuario",
    "Tipo",
    "Grupo_Produto",
    "Marketplace",
    "URL",
    "Meu_Custo",
    "Imposto_Pct",
    "Comissao_Pct",
    "Taxa_Fixa",
    "Frete_Estimado",
]

HEADERS_HISTORICO_HORA = [
    "Usuario",
    "Data_Hora",
    "Hora_Cheia",
    "Tipo",
    "Grupo_Produto",
    "Marketplace",
    "Titulo",
    "Preco",
    "Estoque_Atual",
    "Vendas_na_Hora",
    "Faturamento_Hora",
    "Lucro_Liquido_Hora",
    "Full",
    "Catalogo",
    "Nota",
]

HEADERS_LOJAS_MONITORADAS = [
    "Usuario",
    "Tipo",
    "Nome_Loja",
    "Marketplace",
    "URL_Loja",
]

HEADERS_CATALOGO_LOJAS = [
    "Usuario",
    "Data_Hora",
    "Tipo",
    "Nome_Loja",
    "ID_Anuncio",
    "Titulo",
    "Preco",
    "Estoque",
    "Vendas_Periodo",
    "Full",
    "Catalogo",
    "Nota",
    "Tendencia",
    "Escalabilidade",
    "URL_Produto",
]

HEADERS_CONFIG_NOTIFICACOES = [
    "Usuario",
    "Ativo_Geral",
    "Telegram_Chat_ID",
    "Alerta_Estoque_Baixo",
    "Limite_Estoque",
    "Alerta_Promocao",
    "Alerta_Venda_Pico",
    "Limite_Venda_Hora",
    "Alerta_Catalogo_Full",
]

HEADERS_HISTORICO_NOTIFICACOES = [
    "Usuario",
    "Data_Hora",
    "Tipo_Alerta",
    "Concorrente",
    "Produto",
    "Mensagem",
    "Lida",
]

USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
]


# ==============================================================================
# UTILITÁRIOS DE TEXTO, NÚMEROS E TEMPO
# ==============================================================================


def normalize_text(value: Any) -> str:
    """Normaliza string para comparação segura (sem acentos, minúscula e sem espaços extras)."""
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text)


def parse_number(value: Any, default: float = 0.0) -> float:
    """Converte strings numéricas nos formatos BR (1.299,90 / 12%) ou US (1299.90) para float."""
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)

    raw = str(value).strip()
    if not raw:
        return default

    # Remove símbolos de moeda, porcentagem e espaços
    cleaned = re.sub(r"[R$\s%]", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"[^\d.,\-]", "", cleaned)
    if not cleaned or cleaned in {"-", ".", ","}:
        return default

    # Trata presença simultânea de ponto e vírgula
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            # Formato brasileiro: 1.234,56
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # Formato americano: 1,234.56
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # Ex: 129,90 ou 1,234
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            cleaned = cleaned.replace(",", ".")
        elif len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) <= 3:
            # Ambiguidade rara; assume decimal se houver apenas uma vírgula com zeros depois
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")

    try:
        return float(cleaned)
    except ValueError:
        return default


def parse_int(value: Any, default: int = 0) -> int:
    """Converte valor arbitrário para inteiro não-negativo quando aplicável."""
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))

    raw = str(value).strip()
    if not raw:
        return default

    digits = re.search(r"-?\d+", raw.replace(".", ""))
    if not digits:
        return default
    try:
        return int(digits.group(0))
    except ValueError:
        return default


def get_brasilia_now() -> datetime:
    """Retorna o datetime atual com fuso horário de Brasília (America/Sao_Paulo)."""
    return datetime.now(BRASILIA_TZ)


def format_timestamps_brasilia(dt: Optional[datetime] = None) -> Tuple[str, str]:
    """Retorna (Data_Hora, Hora_Cheia) formatados no horário de Brasília."""
    now_br = dt.astimezone(BRASILIA_TZ) if dt else get_brasilia_now()
    data_hora = now_br.strftime("%Y-%m-%d %H:%M:%S")
    hora_cheia = now_br.strftime("%Y-%m-%d %H:00:00")
    return data_hora, hora_cheia


# ==============================================================================
# AUTENTICAÇÃO E INTEGRAÇÃO GOOGLE SHEETS
# ==============================================================================


def _load_service_account_info() -> Dict[str, Any]:
    """
    Carrega credenciais da Service Account do Google via:
    1) Variável de ambiente GCP_SERVICE_ACCOUNT_JSON (GitHub Actions / servidor)
    2) st.secrets['gcp_service_account'] (Streamlit Cloud)
    """
    env_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON", "").strip()
    if env_json:
        try:
            if env_json.startswith("{"):
                return json.loads(env_json)
            if os.path.isfile(env_json):
                with open(env_json, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            decoded = base64.b64decode(env_json).decode("utf-8")
            return json.loads(decoded)
        except Exception as exc:
            raise ValueError(
                f"Falha ao interpretar GCP_SERVICE_ACCOUNT_JSON: {exc}"
            ) from exc

    try:
        import streamlit as st  # Importação tardia para evitar dependência de contexto web

        if "gcp_service_account" in st.secrets:
            secret_data = st.secrets["gcp_service_account"]
            if isinstance(secret_data, str):
                return json.loads(secret_data)
            return dict(secret_data)
    except Exception as exc:
        logger.debug("st.secrets indisponível ou não configurado: %s", exc)

    raise RuntimeError(
        "Credenciais do Google não encontradas em GCP_SERVICE_ACCOUNT_JSON "
        "nem em st.secrets['gcp_service_account']."
    )


def _resolve_sheet_name() -> str:
    """Obtém o nome ou URL da planilha a partir de env var ou st.secrets."""
    sheet_name = os.environ.get("SHEET_NAME", "").strip()
    if sheet_name:
        return sheet_name

    try:
        import streamlit as st

        if "SHEET_NAME" in st.secrets:
            return str(st.secrets["SHEET_NAME"]).strip()
    except Exception:
        pass

    raise RuntimeError(
        "Variável SHEET_NAME não definida no ambiente nem em st.secrets."
    )


def connect_google_sheets() -> Optional[gspread.Spreadsheet]:
    """Conecta à planilha do Google Sheets com tratamento seguro de erros."""
    try:
        sa_info = _load_service_account_info()
        sheet_identifier = _resolve_sheet_name()
        credentials = Credentials.from_service_account_info(
            sa_info, scopes=GOOGLE_SHEETS_SCOPES
        )
        client = gspread.authorize(credentials)

        if sheet_identifier.startswith("https://"):
            spreadsheet = client.open_by_url(sheet_identifier)
        else:
            spreadsheet = client.open(sheet_identifier)

        logger.info("Conectado com sucesso à planilha '%s'.", spreadsheet.title)
        return spreadsheet
    except Exception as exc:
        logger.error("Erro ao conectar ao Google Sheets: %s", exc)
        return None


def get_or_create_worksheet(
    spreadsheet: gspread.Spreadsheet,
    title: str,
    expected_headers: List[str],
) -> Optional[gspread.Worksheet]:
    """Obtém uma aba existente ou cria com o cabeçalho esperado."""
    try:
        try:
            ws = spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            logger.warning("Aba '%s' não encontrada. Criando automaticamente...", title)
            ws = spreadsheet.add_worksheet(
                title=title, rows=1000, cols=max(len(expected_headers), 15)
            )
            ws.append_row(expected_headers, value_input_option="RAW")
            return ws

        existing_first_row = ws.row_values(1)
        if not existing_first_row:
            ws.append_row(expected_headers, value_input_option="RAW")
        return ws
    except Exception as exc:
        logger.error("Erro ao acessar/criar aba '%s': %s", title, exc)
        return None


def read_sheet_records(worksheet: Optional[gspread.Worksheet]) -> List[Dict[str, Any]]:
    """Lê todos os registros da aba de forma resiliente, sem quebrar com cabeçalhos parciais."""
    if worksheet is None:
        return []
    try:
        values = worksheet.get_all_values()
        if not values or len(values) < 2:
            return []

        headers = [h.strip() for h in values[0]]
        records: List[Dict[str, Any]] = []
        for row in values[1:]:
            if not any(str(cell).strip() for cell in row):
                continue
            item: Dict[str, Any] = {}
            for idx, header in enumerate(headers):
                if not header:
                    continue
                item[header] = row[idx].strip() if idx < len(row) else ""
            records.append(item)
        return records
    except Exception as exc:
        logger.error("Erro ao ler registros da aba '%s': %s", worksheet.title, exc)
        return []


# ==============================================================================
# WEB SCRAPING PÚBLICO E RESILIENTE (SEM API PRIVADA)
# ==============================================================================


def create_http_session() -> requests.Session:
    """Cria sessão HTTP com headers realistas para coleta pública."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    return session


def fetch_html_resilient(
    session: requests.Session, url: str, max_attempts: int = 3, timeout: int = 20
) -> Tuple[Optional[str], str]:
    """Faz download do HTML público com retries, rotação de User-Agent e try/except."""
    if not url or not url.startswith(("http://", "https://")):
        logger.warning("URL inválida ignorada: %s", url)
        return None, url

    for attempt in range(1, max_attempts + 1):
        try:
            session.headers["User-Agent"] = random.choice(USER_AGENTS)
            response = session.get(url, timeout=timeout, allow_redirects=True)
            final_url = response.url or url
            if response.status_code == 200 and response.text:
                return response.text, final_url

            if response.status_code in {429, 500, 502, 503, 504}:
                wait_seconds = attempt * 2.0 + random.uniform(0.3, 1.2)
                logger.warning(
                    "HTTP %s em %s (tentativa %d/%d). Aguardando %.1fs...",
                    response.status_code,
                    url,
                    attempt,
                    max_attempts,
                    wait_seconds,
                )
                time.sleep(wait_seconds)
                continue

            logger.warning(
                "Status HTTP inesperado %s para %s.", response.status_code, url
            )
            return (response.text if response.text else None), final_url
        except requests.RequestException as exc:
            wait_seconds = attempt * 1.5
            logger.warning(
                "Erro de rede ao acessar %s (tentativa %d/%d): %s",
                url,
                attempt,
                max_attempts,
                exc,
            )
            if attempt < max_attempts:
                time.sleep(wait_seconds)
        except Exception as exc:
            logger.error("Erro inesperado no fetch de %s: %s", url, exc)
            return None, url

    return None, url


def _extract_json_ld_products(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extrai objetos Product de tags <script type='application/ld+json'>."""
    products: List[Dict[str, Any]] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        candidates = data if isinstance(data, list) else [data]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            if "@graph" in item and isinstance(item["@graph"], list):
                for node in item["@graph"]:
                    if isinstance(node, dict) and "Product" in str(
                        node.get("@type", "")
                    ):
                        products.append(node)
            elif "Product" in str(item.get("@type", "")):
                products.append(item)
    return products


def _deep_find_first(data: Any, target_keys: Tuple[str, ...]) -> Any:
    """Busca recursivamente a primeira ocorrência não-nula de qualquer chave em JSON."""
    if isinstance(data, dict):
        for key in target_keys:
            if key in data and data[key] is not None and data[key] != "":
                return data[key]
        for val in data.values():
            found = _deep_find_first(val, target_keys)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _deep_find_first(item, target_keys)
            if found is not None:
                return found
    return None


def _extract_embedded_state_jsons(soup: BeautifulSoup, html: str) -> List[Dict[str, Any]]:
    """Extrai blocos JSON públicos embutidos no HTML (__PRELOADED_STATE__, __NEXT_DATA__, etc.)."""
    parsed_blobs: List[Dict[str, Any]] = []

    for script_id in ("__PRELOADED_STATE__", "__NEXT_DATA__", "__INITIAL_STATE__"):
        tag = soup.find("script", id=script_id)
        if tag:
            text = (tag.string or tag.get_text() or "").strip()
            if text.startswith("{"):
                try:
                    parsed_blobs.append(json.loads(text))
                except Exception:
                    pass

    patterns = [
        r"window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});?\s*</script>",
        r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\});?\s*</script>",
        r"__PRELOADED_STATE__\s*=\s*(\{.*?\});",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.DOTALL)
        if match:
            try:
                parsed_blobs.append(json.loads(match.group(1)))
            except Exception:
                continue

    return parsed_blobs


def _detect_marketplace(url: str, declared_marketplace: str) -> str:
    """Identifica o marketplace pela URL ou pelo campo declarado na Configuracao."""
    host = urlparse(url).netloc.lower()
    if "mercadolivre" in host or "mercadolibre" in host:
        return "mercadolivre"
    if "amazon." in host:
        return "amazon"
    if "shopee." in host:
        return "shopee"
    if "magazineluiza" in host or "magalu" in host:
        return "magalu"
    if "petz." in host:
        return "petz"
    if "cobasi." in host:
        return "cobasi"
    return normalize_text(declared_marketplace) or "generico"


def _scrape_mercadolivre(
    soup: BeautifulSoup, html: str, url: str
) -> Dict[str, Any]:
    """Extrator especializado para páginas públicas do Mercado Livre."""
    json_lds = _extract_json_ld_products(soup)
    embedded_jsons = _extract_embedded_state_jsons(soup, html)

    # 1. Título
    titulo = ""
    h1 = soup.select_one("h1.ui-pdp-title") or soup.find("h1")
    if h1:
        titulo = h1.get_text(" ", strip=True)
    if not titulo and json_lds:
        titulo = str(json_lds[0].get("name", "")).strip()
    if not titulo:
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title and og_title.get("content"):
            titulo = str(og_title["content"]).strip()

    # 2. Preço
    preco = 0.0
    if json_lds:
        offers = json_lds[0].get("offers")
        if isinstance(offers, list) and offers:
            offers = offers[0]
        if isinstance(offers, dict) and offers.get("price") is not None:
            preco = parse_number(offers.get("price"), 0.0)

    if preco <= 0:
        meta_price = soup.find("meta", attrs={"itemprop": "price"})
        if meta_price and meta_price.get("content"):
            preco = parse_number(meta_price["content"], 0.0)

    if preco <= 0:
        price_container = soup.select_one(
            ".ui-pdp-price__second-line .andes-money-amount"
        ) or soup.select_one(".ui-pdp-price__main-container .andes-money-amount")
        if price_container:
            frac = price_container.select_one(".andes-money-amount__fraction")
            cents = price_container.select_one(".andes-money-amount__cents")
            frac_txt = frac.get_text(strip=True) if frac else ""
            cents_txt = cents.get_text(strip=True) if cents else "00"
            if frac_txt:
                preco = parse_number(f"{frac_txt},{cents_txt}", 0.0)

    if preco <= 0:
        price_match = re.search(
            r'"price"\s*:\s*(\d+(?:\.\d+)?)', html
        )
        if price_match:
            preco = parse_number(price_match.group(1), 0.0)

    # 3. Estoque disponível (JSON público + HTML público)
    estoque: Optional[int] = None

    for blob in embedded_jsons:
        # Prioriza caminho principal da PDP no __PRELOADED_STATE__
        pdp_scope = (
            blob.get("initialState", {}).get("components", {}).get("available_quantity")
            if isinstance(blob.get("initialState"), dict)
            else None
        )
        if pdp_scope is not None:
            val = _deep_find_first(
                pdp_scope,
                ("available_quantity", "availableQuantity", "value", "max_quantity"),
            )
            parsed_val = parse_int(val, -1)
            if parsed_val >= 0:
                estoque = parsed_val
                break

        val = _deep_find_first(
            blob,
            (
                "available_quantity",
                "availableQuantity",
                "remaining_stock",
                "stock_quantity",
            ),
        )
        if val is not None:
            parsed_val = parse_int(val, -1)
            if parsed_val >= 0:
                estoque = parsed_val
                break

    if estoque is None:
        json_stock_patterns = [
            r'"available_quantity"\s*:\s*(\d+)',
            r'"availableQuantity"\s*:\s*(\d+)',
            r'"quantity_available"\s*:\s*(\d+)',
            r'"stock"\s*:\s*\{\s*"available"\s*:\s*(\d+)',
        ]
        for pattern in json_stock_patterns:
            match = re.search(pattern, html)
            if match:
                estoque = int(match.group(1))
                break

    if estoque is None:
        qty_el = soup.select_one(".ui-pdp-buybox__quantity__available") or soup.select_one(
            ".ui-pdp-stock-information__title"
        )
        qty_text = qty_el.get_text(" ", strip=True) if qty_el else ""
        if qty_text:
            num_match = re.search(r"(\d+)", qty_text.replace(".", ""))
            if num_match:
                estoque = int(num_match.group(1))
            elif "ultimo" in normalize_text(qty_text) or "ultima" in normalize_text(qty_text):
                estoque = 1
            elif "disponivel" in normalize_text(qty_text):
                estoque = 1

    if estoque is None:
        page_text_norm = normalize_text(soup.get_text(" ", strip=True))
        if "produto pausado" in page_text_norm or "sem estoque" in page_text_norm:
            estoque = 0
        else:
            estoque = 0

    # 4. Selo FULL
    is_full = False
    full_selectors = [
        "svg.ui-pdp-icon--full",
        ".ui-pdp-icon--full",
        "[aria-label*='Full' i]",
        "use[href*='full']",
    ]
    for sel in full_selectors:
        if soup.select_one(sel):
            is_full = True
            break

    if not is_full:
        if re.search(
            r'"logistic_type"\s*:\s*"fulfillment"|"is_full"\s*:\s*true|"full_icon"\s*:\s*true',
            html,
        ):
            is_full = True
        else:
            shipping_block = soup.select_one(".ui-pdp-media__title") or soup.select_one(
                ".ui-pdp-color--GREEN"
            )
            if shipping_block and "full" in normalize_text(shipping_block.get_text(" ", strip=True)):
                is_full = True

    # 5. Catálogo
    is_catalog = False
    canonical = soup.find("link", rel="canonical")
    canonical_href = str(canonical.get("href", "")) if canonical else ""
    if "/p/MLB" in url.upper() or "/P/MLB" in canonical_href.upper():
        is_catalog = True
    elif re.search(r'"catalog_listing"\s*:\s*true', html):
        is_catalog = True
    elif soup.select_one(".ui-pdp-products__list") or soup.select_one(
        "a[href*='/p/MLB']"
    ):
        is_catalog = True
    else:
        html_norm = normalize_text(
            " ".join(
                el.get_text(" ", strip=True)
                for el in soup.select(".ui-pdp-other-sellers, .ui-pdp-action-modal")
            )
        )
        if "opcoes de compra" in html_norm or "outros vendedores" in html_norm:
            is_catalog = True

    # 6. Nota (Avaliação)
    nota = 0.0
    if json_lds:
        agg = json_lds[0].get("aggregateRating")
        if isinstance(agg, dict) and agg.get("ratingValue") is not None:
            nota = parse_number(agg.get("ratingValue"), 0.0)

    if nota <= 0:
        rating_el = soup.select_one(".ui-pdp-review__rating") or soup.select_one(
            ".ui-review-capability__rating__average"
        )
        if rating_el:
            nota = parse_number(rating_el.get_text(strip=True), 0.0)

    if nota <= 0:
        rating_match = re.search(r'"rating_average"\s*:\s*([\d.]+)', html)
        if rating_match:
            nota = parse_number(rating_match.group(1), 0.0)

    return {
        "titulo": titulo or "Título não identificado",
        "preco": round(preco, 2),
        "estoque_atual": max(0, int(estoque)),
        "full": "Sim" if is_full else "Não",
        "catalogo": "Sim" if is_catalog else "Não",
        "nota": round(nota, 2),
    }


def _scrape_amazon(soup: BeautifulSoup, html: str) -> Dict[str, Any]:
    """Extrator especializado para páginas públicas da Amazon BR."""
    json_lds = _extract_json_ld_products(soup)

    # 1. Título
    titulo = ""
    title_el = soup.select_one("#productTitle") or soup.select_one("#title")
    if title_el:
        titulo = title_el.get_text(" ", strip=True)
    if not titulo and json_lds:
        titulo = str(json_lds[0].get("name", "")).strip()
    if not titulo:
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title and og_title.get("content"):
            titulo = str(og_title["content"]).strip()

    # 2. Preço
    preco = 0.0
    price_el = (
        soup.select_one("#corePriceDisplay_desktop_feature_div .a-price .a-offscreen")
        or soup.select_one("#corePrice_feature_div .a-price .a-offscreen")
        or soup.select_one(".a-price .a-offscreen")
    )
    if price_el:
        preco = parse_number(price_el.get_text(strip=True), 0.0)

    if preco <= 0:
        whole = soup.select_one(".a-price-whole")
        frac = soup.select_one(".a-price-fraction")
        if whole:
            whole_txt = re.sub(r"[^\d]", "", whole.get_text(strip=True))
            frac_txt = re.sub(r"[^\d]", "", frac.get_text(strip=True)) if frac else "00"
            if whole_txt:
                preco = parse_number(f"{whole_txt},{frac_txt}", 0.0)

    if preco <= 0:
        price_match = re.search(r'"priceAmount"\s*:\s*([\d.]+)', html)
        if price_match:
            preco = parse_number(price_match.group(1), 0.0)

    # 3. Estoque disponível
    estoque = 0
    avail_el = soup.select_one("#availability")
    avail_text = normalize_text(avail_el.get_text(" ", strip=True) if avail_el else "")
    qty_options = soup.select("#quantity option")

    stock_match = re.search(r"restam\s+(?:apenas\s+)?(\d+)", avail_text)
    if stock_match:
        estoque = int(stock_match.group(1))
    elif qty_options:
        numeric_opts = [
            parse_int(opt.get("value") or opt.get_text(strip=True), 0)
            for opt in qty_options
        ]
        max_opt = max(numeric_opts) if numeric_opts else 0
        estoque = max(0, max_opt)
    elif "em estoque" in avail_text:
        estoque = 1
    elif "indisponivel" in avail_text or "esgotado" in avail_text:
        estoque = 0
    else:
        json_qty = re.search(r'"maxOrderQuantity"\s*:\s*(\d+)', html)
        if json_qty:
            estoque = int(json_qty.group(1))

    # 4. Selo FULL (FBA / Prime / Enviado pela Amazon)
    fulfillment_text = normalize_text(
        " ".join(
            el.get_text(" ", strip=True)
            for el in soup.select(
                "#tabular-buybox, #merchant-info, #fulfilledByAmazon, .prime-logo"
            )
        )
    )
    is_full = bool(
        soup.select_one("i.a-icon-prime")
        or "enviado pela amazon" in fulfillment_text
        or "enviado por amazon" in fulfillment_text
        or "full" in fulfillment_text
    )

    # 5. Catálogo (Múltiplos vendedores na Buybox)
    is_catalog = bool(
        soup.select_one("#olp_feature_div")
        or soup.select_one("#aod-ingress-link")
        or "mais opcoes de compra" in normalize_text(html[:200000])
    )

    # 6. Nota
    nota = 0.0
    rating_el = (
        soup.select_one("#acrPopover .a-icon-alt")
        or soup.select_one("span[data-hook='rating-out-of-text']")
        or soup.select_one(".a-icon-star .a-icon-alt")
    )
    if rating_el:
        match_nota = re.search(r"(\d+[.,]\d+|\d+)", rating_el.get_text(strip=True))
        if match_nota:
            nota = parse_number(match_nota.group(1), 0.0)

    return {
        "titulo": titulo or "Título não identificado",
        "preco": round(preco, 2),
        "estoque_atual": max(0, int(estoque)),
        "full": "Sim" if is_full else "Não",
        "catalogo": "Sim" if is_catalog else "Não",
        "nota": round(nota, 2),
    }


def _scrape_generic(soup: BeautifulSoup, html: str) -> Dict[str, Any]:
    """Extrator genérico resiliente via JSON-LD, OpenGraph, Meta tags e __NEXT_DATA__."""
    json_lds = _extract_json_ld_products(soup)
    embedded_jsons = _extract_embedded_state_jsons(soup, html)

    # 1. Título
    titulo = ""
    if json_lds:
        titulo = str(json_lds[0].get("name", "")).strip()
    if not titulo:
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title and og_title.get("content"):
            titulo = str(og_title["content"]).strip()
    if not titulo:
        h1 = soup.find("h1")
        if h1:
            titulo = h1.get_text(" ", strip=True)
    if not titulo and soup.title:
        titulo = soup.title.get_text(" ", strip=True)

    # 2. Preço
    preco = 0.0
    if json_lds:
        offers = json_lds[0].get("offers")
        if isinstance(offers, list) and offers:
            offers = offers[0]
        if isinstance(offers, dict):
            preco = parse_number(
                offers.get("price") or offers.get("lowPrice"), 0.0
            )

    if preco <= 0:
        for attr in (
            {"property": "product:price:amount"},
            {"property": "og:price:amount"},
            {"itemprop": "price"},
        ):
            meta = soup.find("meta", attrs=attr)
            if meta and meta.get("content"):
                preco = parse_number(meta["content"], 0.0)
                if preco > 0:
                    break

    if preco <= 0:
        for blob in embedded_jsons:
            val = _deep_find_first(
                blob, ("salePrice", "bestPrice", "price", "spotPrice", "sellingPrice")
            )
            parsed_price = parse_number(val, 0.0)
            if parsed_price > 0:
                preco = parsed_price
                break

    if preco <= 0:
        price_match = re.search(
            r'"(?:price|sellingPrice|bestPrice|priceAmount)"\s*:\s*"?(\d+(?:[.,]\d+)?)"?',
            html,
        )
        if price_match:
            preco = parse_number(price_match.group(1), 0.0)

    # 3. Estoque disponível
    estoque: Optional[int] = None
    for blob in embedded_jsons:
        val = _deep_find_first(
            blob,
            (
                "available_quantity",
                "availableQuantity",
                "stock",
                "stockQuantity",
                "quantity",
                "inventory",
            ),
        )
        if val is not None and not isinstance(val, dict):
            parsed_qty = parse_int(val, -1)
            if parsed_qty >= 0:
                estoque = parsed_qty
                break

    if estoque is None:
        stock_match = re.search(
            r'"(?:available_quantity|availableQuantity|stockQuantity|stock|quantity)"\s*:\s*(\d+)',
            html,
        )
        if stock_match:
            estoque = int(stock_match.group(1))

    if estoque is None and json_lds:
        offers = json_lds[0].get("offers")
        if isinstance(offers, list) and offers:
            offers = offers[0]
        if isinstance(offers, dict):
            avail = str(offers.get("availability", ""))
            if "InStock" in avail:
                estoque = 1
            elif "OutOfStock" in avail:
                estoque = 0

    if estoque is None:
        estoque = 0

    # 4. Selo FULL
    html_lower = html.lower()
    is_full = bool(
        re.search(
            r'"fulfillment"\s*:\s*true|"is_full"\s*:\s*true|"logistic_type"\s*:\s*"fulfillment"',
            html_lower,
        )
    )

    # 5. Catálogo
    is_catalog = bool(
        re.search(
            r'"catalog_listing"\s*:\s*true|"is_catalog"\s*:\s*true|"sellers_count"\s*:\s*[2-9]',
            html_lower,
        )
    )

    # 6. Nota
    nota = 0.0
    if json_lds:
        agg = json_lds[0].get("aggregateRating")
        if isinstance(agg, dict) and agg.get("ratingValue") is not None:
            nota = parse_number(agg.get("ratingValue"), 0.0)

    if nota <= 0:
        for blob in embedded_jsons:
            val = _deep_find_first(
                blob, ("ratingValue", "rating_average", "averageRating", "rating")
            )
            parsed_rating = parse_number(val, 0.0)
            if 0 < parsed_rating <= 5.0:
                nota = parsed_rating
                break

    return {
        "titulo": titulo or "Título não identificado",
        "preco": round(preco, 2),
        "estoque_atual": max(0, int(estoque)),
        "full": "Sim" if is_full else "Não",
        "catalogo": "Sim" if is_catalog else "Não",
        "nota": round(nota, 2),
    }


def extract_product_data_from_html(
    html: str, url: str, declared_marketplace: str = ""
) -> Dict[str, Any]:
    """Faz o parsing completo do HTML/JSON público de acordo com o marketplace."""
    soup = BeautifulSoup(html, "lxml")
    marketplace_key = _detect_marketplace(url, declared_marketplace)

    if marketplace_key == "mercadolivre":
        return _scrape_mercadolivre(soup, html, url)
    if marketplace_key == "amazon":
        return _scrape_amazon(soup, html)
    return _scrape_generic(soup, html)


def scrape_listing_publicly(
    session: requests.Session, url: str, declared_marketplace: str = ""
) -> Optional[Dict[str, Any]]:
    """Executa a coleta pública completa com proteção total contra falhas."""
    try:
        html, final_url = fetch_html_resilient(session, url)
        if not html:
            return None
        return extract_product_data_from_html(html, final_url, declared_marketplace)
    except Exception as exc:
        logger.error("Falha ao processar HTML de %s: %s", url, exc)
        return None


# ==============================================================================
# LÓGICA DE HISTÓRICO, VENDAS, FATURAMENTO E LUCRO LÍQUIDO
# ==============================================================================


def build_previous_readings_index(
    historico_records: List[Dict[str, Any]],
    config_records: List[Dict[str, Any]],
) -> Tuple[Dict[Tuple[str, str, str, str, str], Dict[str, Any]], Dict[Tuple[str, str, str, str], Dict[str, Any]], Dict[Tuple[str, str, str, str], int]]:
    """
    Indexa a leitura mais recente de Historico_Hora para comparação segura.
    Retorna:
    - exact_index: chave (usuario, tipo, grupo_produto, marketplace, titulo) -> registro
    - group_index: chave (usuario, tipo, grupo_produto, marketplace) -> último registro
    - group_counts: quantidade de URLs configuradas por (usuario, tipo, grupo_produto, marketplace)
    """
    exact_index: Dict[Tuple[str, str, str, str, str], Dict[str, Any]] = {}
    group_index: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
    group_counts: Dict[Tuple[str, str, str, str], int] = {}

    for cfg in config_records:
        key_4 = (
            normalize_text(cfg.get("Usuario")),
            normalize_text(cfg.get("Tipo")),
            normalize_text(cfg.get("Grupo_Produto")),
            normalize_text(cfg.get("Marketplace")),
        )
        group_counts[key_4] = group_counts.get(key_4, 0) + 1

    # Garante ordem cronológica caso a planilha não esteja estritamente ordenada
    sorted_history = sorted(
        historico_records,
        key=lambda row: str(row.get("Data_Hora", "")),
    )

    for row in sorted_history:
        usuario = normalize_text(row.get("Usuario"))
        tipo = normalize_text(row.get("Tipo"))
        grupo = normalize_text(row.get("Grupo_Produto"))
        mkt = normalize_text(row.get("Marketplace"))
        titulo = normalize_text(row.get("Titulo"))

        if not usuario:
            continue

        key_5 = (usuario, tipo, grupo, mkt, titulo)
        key_4 = (usuario, tipo, grupo, mkt)
        exact_index[key_5] = row
        group_index[key_4] = row

    return exact_index, group_index, group_counts


def find_previous_reading(
    cfg: Dict[str, Any],
    scraped_title: str,
    exact_index: Dict[Tuple[str, str, str, str, str], Dict[str, Any]],
    group_index: Dict[Tuple[str, str, str, str], Dict[str, Any]],
    group_counts: Dict[Tuple[str, str, str, str], int],
) -> Optional[Dict[str, Any]]:
    """
    Busca a última leitura do mesmo Usuario e anúncio em Historico_Hora.
    Usa chave exata com título e fallback por grupo quando houver apenas 1 URL naquele grupo/tipo.
    """
    usuario = normalize_text(cfg.get("Usuario"))
    tipo = normalize_text(cfg.get("Tipo"))
    grupo = normalize_text(cfg.get("Grupo_Produto"))
    mkt = normalize_text(cfg.get("Marketplace"))
    titulo = normalize_text(scraped_title)

    key_5 = (usuario, tipo, grupo, mkt, titulo)
    if key_5 in exact_index:
        return exact_index[key_5]

    key_4 = (usuario, tipo, grupo, mkt)
    if group_counts.get(key_4, 0) <= 1 and key_4 in group_index:
        return group_index[key_4]

    return None


def calculate_hourly_metrics(
    cfg: Dict[str, Any],
    preco_atual: float,
    estoque_atual: int,
    previous_reading: Optional[Dict[str, Any]],
) -> Tuple[int, float, float]:
    """
    Calcula:
    - Vendas_na_Hora: redução positiva de estoque em relação à leitura anterior
    - Faturamento_Hora: Vendas_na_Hora * Preco
    - Lucro_Liquido_Hora: se Tipo == 'Meu Anuncio', desconta custo, imposto %, comissão %, taxa fixa e frete estimado
    """
    vendas_na_hora = 0
    if previous_reading is not None:
        estoque_anterior = parse_int(previous_reading.get("Estoque_Atual"), -1)
        if estoque_anterior >= 0 and estoque_atual < estoque_anterior:
            vendas_na_hora = estoque_anterior - estoque_atual

    faturamento_hora = round(vendas_na_hora * preco_atual, 2)

    tipo_norm = normalize_text(cfg.get("Tipo"))
    if tipo_norm == "meu anuncio" and vendas_na_hora > 0:
        meu_custo = parse_number(cfg.get("Meu_Custo"), 0.0)
        imposto_pct = parse_number(cfg.get("Imposto_Pct"), 0.0)
        comissao_pct = parse_number(cfg.get("Comissao_Pct"), 0.0)
        taxa_fixa = parse_number(cfg.get("Taxa_Fixa"), 0.0)
        frete_estimado = parse_number(cfg.get("Frete_Estimado"), 0.0)

        imposto_unit = preco_atual * (imposto_pct / 100.0)
        comissao_unit = preco_atual * (comissao_pct / 100.0)
        lucro_unitario = (
            preco_atual
            - meu_custo
            - imposto_unit
            - comissao_unit
            - taxa_fixa
            - frete_estimado
        )
        lucro_liquido_hora = round(vendas_na_hora * lucro_unitario, 2)
    else:
        lucro_liquido_hora = 0.0

    return vendas_na_hora, faturamento_hora, lucro_liquido_hora


# ==============================================================================
# RAIO-X DE LOJAS INTEIRAS (Lojas_Monitoradas -> Catalogo_Lojas)
# ==============================================================================


def extract_store_name_from_url_or_html(
    url_loja: str, soup: Optional[BeautifulSoup] = None
) -> str:
    """Extrai automaticamente o nome da loja a partir da página pública ou da URL."""
    if soup is not None:
        for selector in (
            "h1.ui-search-breadcrumb__title",
            "h1.store-header__title",
            "h1",
        ):
            el = soup.select_one(selector)
            if el:
                txt = el.get_text(" ", strip=True)
                if txt and len(txt) <= 80:
                    return txt

        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title and og_title.get("content"):
            raw = str(og_title["content"]).split("|")[0].split("-")[0].strip()
            if raw:
                return raw[:80]

    parsed = urlparse(url_loja)
    path_parts = [p for p in parsed.path.split("/") if p and not p.startswith("_")]
    if path_parts:
        candidate = re.sub(r"[-_]+", " ", path_parts[-1]).strip()
        if candidate and not candidate.lower().startswith("custid"):
            return candidate.title()[:80]
    return parsed.netloc.replace("www.", "") or "Loja Monitorada"


def _extract_ml_seller_id(url_loja: str, html: str = "") -> Optional[str]:
    """Identifica o seller_id numérico de uma loja do Mercado Livre via URL ou HTML público."""
    url_match = re.search(r"_CustId_(\d+)", url_loja, flags=re.IGNORECASE)
    if url_match:
        return url_match.group(1)

    for pattern in (
        r'"seller_id"\s*:\s*(\d+)',
        r'"seller"\s*:\s*\{\s*"id"\s*:\s*(\d+)',
        r"_CustId_(\d+)",
    ):
        m = re.search(pattern, html, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _fetch_ml_seller_api_items(
    session: requests.Session, seller_id: str, max_items: int = 50
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Consulta a API pública de busca por vendedor do Mercado Livre (/sites/MLB/search?seller_id=...)."""
    try:
        api_url = (
            f"https://api.mercadolibre.com/sites/MLB/search"
            f"?seller_id={seller_id}&limit={max_items}"
        )
        resp = session.get(api_url, timeout=18)
        if resp.status_code != 200:
            return [], None

        payload = resp.json()
        results = payload.get("results", [])
        if not results:
            return [], None

        seller_name = None
        seller_obj = payload.get("seller") or {}
        if isinstance(seller_obj, dict) and seller_obj.get("nickname"):
            seller_name = str(seller_obj["nickname"]).strip()

        items: List[Dict[str, Any]] = []
        for entry in results[:max_items]:
            item_id = str(entry.get("id", "")).strip()
            if not item_id:
                continue
            shipping = entry.get("shipping") or {}
            is_full = shipping.get("logistic_type") == "fulfillment"
            is_catalog = bool(
                entry.get("catalog_listing") or entry.get("catalog_product_id")
            )
            if not seller_name:
                ent_seller = entry.get("seller") or {}
                if isinstance(ent_seller, dict) and ent_seller.get("nickname"):
                    seller_name = str(ent_seller["nickname"]).strip()

            reviews = entry.get("reviews") or {}
            nota = parse_number(
                reviews.get("rating_average") if isinstance(reviews, dict) else 0.0,
                0.0,
            )

            items.append(
                {
                    "id_anuncio": item_id,
                    "titulo": str(entry.get("title", "")).strip() or item_id,
                    "preco": round(parse_number(entry.get("price"), 0.0), 2),
                    "estoque": max(0, parse_int(entry.get("available_quantity"), 0)),
                    "sold_quantity": max(0, parse_int(entry.get("sold_quantity"), 0)),
                    "full": "Sim" if is_full else "Não",
                    "catalogo": "Sim" if is_catalog else "Não",
                    "nota": round(nota, 2),
                    "url_produto": str(entry.get("permalink", "")).strip(),
                }
            )
        return items, seller_name
    except Exception as exc:
        logger.debug("Fallback HTML será usado para seller_id %s: %s", seller_id, exc)
        return [], None


def _scrape_ml_storefront_html(
    html: str, url_loja: str, max_items: int = 50
) -> Tuple[List[Dict[str, Any]], str]:
    """Extrai catálogo ativo da vitrine pública HTML do Mercado Livre caso API pública falhe."""
    soup = BeautifulSoup(html, "lxml")
    detected_name = extract_store_name_from_url_or_html(url_loja, soup)
    cards = soup.select("li.ui-search-layout__item, div.ui-search-result__wrapper")

    items: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for card in cards:
        if len(items) >= max_items:
            break
        title_el = card.select_one(
            "a.poly-component__title, h2.ui-search-item__title, a.ui-search-link"
        )
        if not title_el:
            continue
        titulo = title_el.get_text(" ", strip=True)
        url_prod = str(title_el.get("href", "")).strip()
        if not titulo or not url_prod:
            continue

        id_match = re.search(r"(MLB-?\d+)", url_prod, flags=re.IGNORECASE)
        id_anuncio = (
            id_match.group(1).replace("-", "").upper()
            if id_match
            else f"ML-{abs(hash(url_prod)) % 10**9}"
        )
        if id_anuncio in seen_ids:
            continue
        seen_ids.add(id_anuncio)

        price_box = card.select_one(".poly-price__current .andes-money-amount") or card.select_one(
            ".ui-search-price__second-line .andes-money-amount"
        )
        preco = 0.0
        if price_box:
            frac = price_box.select_one(".andes-money-amount__fraction")
            cents = price_box.select_one(".andes-money-amount__cents")
            f_txt = frac.get_text(strip=True) if frac else ""
            c_txt = cents.get_text(strip=True) if cents else "00"
            if f_txt:
                preco = parse_number(f"{f_txt},{c_txt}", 0.0)

        card_html = str(card).lower()
        is_full = (
            "fulfillment" in card_html
            or "poly-component__shipped-from" in card_html
            or "full" in normalize_text(card.get_text(" ", strip=True))
        )
        is_catalog = "/p/mlb" in url_prod.lower()

        rating_el = card.select_one(".poly-reviews__rating, .ui-search-reviews__rating-number")
        nota = parse_number(rating_el.get_text(strip=True), 0.0) if rating_el else 0.0

        items.append(
            {
                "id_anuncio": id_anuncio,
                "titulo": titulo,
                "preco": round(preco, 2),
                "estoque": 0,
                "sold_quantity": 0,
                "full": "Sim" if is_full else "Não",
                "catalogo": "Sim" if is_catalog else "Não",
                "nota": round(nota, 2),
                "url_produto": url_prod,
            }
        )

    return items, detected_name


def _scrape_generic_storefront(
    html: str, url_loja: str, max_items: int = 50
) -> Tuple[List[Dict[str, Any]], str]:
    """Extrator público genérico de vitrine de loja (Shopee, Magalu e afins) via JSON-LD/HTML."""
    soup = BeautifulSoup(html, "lxml")
    detected_name = extract_store_name_from_url_or_html(url_loja, soup)
    embedded_jsons = _extract_embedded_state_jsons(soup, html)

    items: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()

    # Tenta extrair lista de produtos do JSON embutido (__NEXT_DATA__ / __INITIAL_STATE__)
    for blob in embedded_jsons:
        def _walk_products(node: Any) -> None:
            if len(items) >= max_items:
                return
            if isinstance(node, list):
                for entry in node:
                    _walk_products(entry)
            elif isinstance(node, dict):
                title = node.get("title") or node.get("name")
                price = node.get("price") or node.get("salePrice") or node.get("bestPrice")
                pid = node.get("id") or node.get("itemid") or node.get("sku")
                if title and price is not None and pid is not None:
                    id_str = str(pid).strip()
                    if id_str and id_str not in seen_ids:
                        seen_ids.add(id_str)
                        raw_url = str(node.get("permalink") or node.get("url") or url_loja)
                        items.append(
                            {
                                "id_anuncio": id_str,
                                "titulo": str(title).strip(),
                                "preco": round(parse_number(price, 0.0), 2),
                                "estoque": max(0, parse_int(node.get("stock") or node.get("available_quantity"), 0)),
                                "sold_quantity": max(0, parse_int(node.get("sold") or node.get("historical_sold"), 0)),
                                "full": "Sim" if node.get("is_full") or node.get("fulfillment") else "Não",
                                "catalogo": "Sim" if node.get("catalog_listing") else "Não",
                                "nota": round(parse_number(node.get("rating") or node.get("rating_average"), 0.0), 2),
                                "url_produto": raw_url,
                            }
                        )
                for val in node.values():
                    if isinstance(val, (dict, list)):
                        _walk_products(val)

        _walk_products(blob)

    # Fallback via JSON-LD ItemList
    if not items:
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads((script.string or "").strip())
            except Exception:
                continue
            nodes = data if isinstance(data, list) else [data]
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                for elem in node.get("itemListElement", []) if isinstance(node.get("itemListElement"), list) else []:
                    prod = elem.get("item", elem) if isinstance(elem, dict) else {}
                    if not isinstance(prod, dict):
                        continue
                    title = str(prod.get("name", "")).strip()
                    prod_url = str(prod.get("url", url_loja)).strip()
                    if not title:
                        continue
                    id_str = str(prod.get("sku") or f"ITEM-{abs(hash(prod_url + title)) % 10**9}")
                    if id_str in seen_ids:
                        continue
                    seen_ids.add(id_str)
                    offers = prod.get("offers") if isinstance(prod.get("offers"), dict) else {}
                    items.append(
                        {
                            "id_anuncio": id_str,
                            "titulo": title,
                            "preco": round(parse_number(offers.get("price"), 0.0), 2),
                            "estoque": 0,
                            "sold_quantity": 0,
                            "full": "Não",
                            "catalogo": "Não",
                            "nota": round(parse_number((prod.get("aggregateRating") or {}).get("ratingValue"), 0.0), 2),
                            "url_produto": prod_url,
                        }
                    )

    return items[:max_items], detected_name


def scrape_store_catalog_publicly(
    session: requests.Session,
    url_loja: str,
    declared_marketplace: str = "",
    declared_name: str = "",
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Varre todos os anúncios ativos de uma URL_Loja e extrai Nome_Loja automaticamente
    quando não informado. Protegido integralmente contra falhas de rede.
    """
    try:
        mkt = _detect_marketplace(url_loja, declared_marketplace)
        html, final_url = fetch_html_resilient(session, url_loja)
        html_str = html or ""

        if mkt == "mercadolivre":
            seller_id = _extract_ml_seller_id(final_url, html_str)
            if seller_id:
                api_items, api_seller_name = _fetch_ml_seller_api_items(session, seller_id)
                if api_items:
                    resolved_name = (
                        declared_name.strip()
                        or api_seller_name
                        or extract_store_name_from_url_or_html(final_url)
                    )
                    return api_items, resolved_name

            if html_str:
                html_items, html_name = _scrape_ml_storefront_html(html_str, final_url)
                return html_items, (declared_name.strip() or html_name)

        if html_str:
            gen_items, gen_name = _scrape_generic_storefront(html_str, final_url)
            return gen_items, (declared_name.strip() or gen_name)

        return [], (declared_name.strip() or extract_store_name_from_url_or_html(url_loja))
    except Exception as exc:
        logger.error("Erro ao varrer loja '%s': %s", url_loja, exc)
        return [], (declared_name.strip() or extract_store_name_from_url_or_html(url_loja))


def compute_store_item_trend_and_scalability(
    previous_sales_history: List[int], current_vendas: int
) -> Tuple[str, str]:
    """
    Calcula:
    - Tendencia: 'Em Alta', 'Estável' ou 'Em Baixa' comparando o ritmo recente com a média anterior.
    - Escalabilidade: 'Muito Escalável', 'Média' ou 'Não Escalável'.
    """
    if not previous_sales_history:
        tendencia = "Em Alta" if current_vendas >= 3 else "Estável"
        if current_vendas >= 5:
            escalabilidade = "Muito Escalável"
        elif current_vendas >= 1:
            escalabilidade = "Média"
        else:
            escalabilidade = "Não Escalável"
        return tendencia, escalabilidade

    prev_avg = sum(previous_sales_history) / len(previous_sales_history)
    recent_window = previous_sales_history[-2:] + [current_vendas]
    recent_avg = sum(recent_window) / len(recent_window)

    if prev_avg == 0:
        tendencia = "Em Alta" if current_vendas > 0 else "Estável"
    elif recent_avg >= prev_avg * 1.15 and current_vendas > 0:
        tendencia = "Em Alta"
    elif recent_avg <= prev_avg * 0.80 or (current_vendas == 0 and prev_avg >= 1.5):
        tendencia = "Em Baixa"
    else:
        tendencia = "Estável"

    total_recent = sum(recent_window)
    active_periods = sum(1 for v in recent_window if v > 0)

    if (
        (tendencia == "Em Alta" and recent_avg >= 3.0)
        or (total_recent >= 10 and active_periods >= 2 and tendencia != "Em Baixa")
        or (current_vendas >= 5 and tendencia != "Em Baixa")
    ):
        escalabilidade = "Muito Escalável"
    elif tendencia != "Em Baixa" and (total_recent >= 2 or current_vendas >= 1):
        escalabilidade = "Média"
    else:
        escalabilidade = "Não Escalável"

    return tendencia, escalabilidade


def build_store_catalog_history_index(
    catalogo_records: List[Dict[str, Any]],
) -> Dict[Tuple[str, str, str], List[Dict[str, Any]]]:
    """Agrupa leituras históricas de Catalogo_Lojas em ordem cronológica por (Usuario, Nome_Loja, ID_Anuncio)."""
    sorted_rows = sorted(
        catalogo_records, key=lambda r: str(r.get("Data_Hora", ""))
    )
    index: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
    for row in sorted_rows:
        key = (
            normalize_text(row.get("Usuario")),
            normalize_text(row.get("Nome_Loja")),
            str(row.get("ID_Anuncio", "")).strip().upper(),
        )
        if not key[0] or not key[2]:
            continue
        index.setdefault(key, []).append(row)
    return index


def _is_flag_sim(value: Any) -> bool:
    """Retorna True se o valor textual representar 'Sim' (case-insensitive)."""
    return normalize_text(value) == "sim"


def _resolve_telegram_bot_token() -> str:
    """Obtém TELEGRAM_BOT_TOKEN da variável de ambiente ou de st.secrets com segurança."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if token:
        return token
    try:
        import streamlit as st

        if "TELEGRAM_BOT_TOKEN" in st.secrets:
            return str(st.secrets["TELEGRAM_BOT_TOKEN"]).strip()
    except Exception:
        pass
    return ""


def send_telegram_notification(
    chat_id: str, bot_token: str, message_html: str, timeout: int = 12
) -> bool:
    """Envia alerta formatado via API oficial do Telegram com proteção try/except."""
    clean_chat = str(chat_id or "").strip()
    clean_token = str(bot_token or "").strip()
    if not clean_chat or not clean_token:
        return False

    endpoint = f"https://api.telegram.org/bot{clean_token}/sendMessage"
    payload = {
        "chat_id": clean_chat,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(endpoint, json=payload, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get("ok"):
                return True
        logger.warning(
            "Falha no envio Telegram (HTTP %s): %s",
            resp.status_code,
            resp.text[:250] if resp.text else "",
        )
        return False
    except Exception as exc:
        logger.error("Erro de rede ao enviar mensagem Telegram: %s", exc)
        return False


def build_notification_config_index(
    config_notif_records: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Indexa preferências da aba Config_Notificacoes por Usuario normalizado."""
    index: Dict[str, Dict[str, Any]] = {}
    for row in config_notif_records:
        user_key = normalize_text(row.get("Usuario"))
        if user_key:
            index[user_key] = row
    return index


def evaluate_competitor_alerts(
    user_notif_cfg: Optional[Dict[str, Any]],
    competitor_name: str,
    product_title: str,
    current_price: float,
    current_stock: int,
    vendas_na_hora: int,
    current_full: str,
    current_catalog: str,
    previous_reading: Optional[Dict[str, Any]],
    prev_stock_key: str = "Estoque_Atual",
) -> List[Dict[str, str]]:
    """
    Compara leitura atual do concorrente com a imediatamente anterior e retorna
    a lista de alertas habilitados para o usuário conforme Config_Notificacoes:
    1) Estoque Baixo / Zerado
    2) Promoção / Alteração de Preço
    3) Venda Expressiva / Pico
    4) Catálogo / Full
    """
    if not user_notif_cfg or not _is_flag_sim(user_notif_cfg.get("Ativo_Geral")):
        return []

    alerts: List[Dict[str, str]] = []
    comp_label = (competitor_name or "").strip() or "Concorrente"
    prod_label = (product_title or "").strip() or "Produto monitorado"

    # 1. Estoque Baixo / Zerado
    if _is_flag_sim(user_notif_cfg.get("Alerta_Estoque_Baixo")) and previous_reading is not None:
        est_ant = parse_int(previous_reading.get(prev_stock_key), -1)
        est_atual = max(0, parse_int(current_stock, 0))
        limite_est = max(0, parse_int(user_notif_cfg.get("Limite_Estoque"), 5))

        if est_ant > 0 and est_atual == 0:
            alerts.append(
                {
                    "tipo_alerta": "Estoque Zerado",
                    "concorrente": comp_label,
                    "produto": prod_label,
                    "mensagem": (
                        f"Estoque ZERADO! Caiu de {est_ant} un. para 0 un. — "
                        "oportunidade imediata de capturar demanda ou otimizar margem."
                    ),
                }
            )
        elif est_ant > limite_est and 0 < est_atual <= limite_est:
            alerts.append(
                {
                    "tipo_alerta": "Estoque Baixo",
                    "concorrente": comp_label,
                    "produto": prod_label,
                    "mensagem": (
                        f"Estoque baixo detectado: caiu de {est_ant} un. para {est_atual} un. "
                        f"(limite configurado: {limite_est} un.)."
                    ),
                }
            )

    # 2. Promoção / Alteração de Preço
    if _is_flag_sim(user_notif_cfg.get("Alerta_Promocao")) and previous_reading is not None:
        preco_ant = round(parse_number(previous_reading.get("Preco"), 0.0), 2)
        preco_atual = round(parse_number(current_price, 0.0), 2)
        if preco_ant > 0 and preco_atual > 0 and abs(preco_atual - preco_ant) >= 0.01:
            var_pct = ((preco_atual - preco_ant) / preco_ant) * 100.0
            if preco_atual < preco_ant:
                alerts.append(
                    {
                        "tipo_alerta": "Promoção / Queda de Preço",
                        "concorrente": comp_label,
                        "produto": prod_label,
                        "mensagem": (
                            f"Promoção do concorrente! Preço caiu de R$ {preco_ant:.2f} "
                            f"para R$ {preco_atual:.2f} ({var_pct:+.2f}%)."
                        ),
                    }
                )
            else:
                alerts.append(
                    {
                        "tipo_alerta": "Alteração de Preço",
                        "concorrente": comp_label,
                        "produto": prod_label,
                        "mensagem": (
                            f"Aumento de preço do concorrente: subiu de R$ {preco_ant:.2f} "
                            f"para R$ {preco_atual:.2f} ({var_pct:+.2f}%)."
                        ),
                    }
                )

    # 3. Venda Expressiva / Pico
    if _is_flag_sim(user_notif_cfg.get("Alerta_Venda_Pico")):
        limite_vendas = max(1, parse_int(user_notif_cfg.get("Limite_Venda_Hora"), 5))
        vendas_int = max(0, parse_int(vendas_na_hora, 0))
        if vendas_int >= limite_vendas:
            alerts.append(
                {
                    "tipo_alerta": "Pico de Vendas",
                    "concorrente": comp_label,
                    "produto": prod_label,
                    "mensagem": (
                        f"Venda expressiva detectada: {vendas_int} un. vendidas na última leitura "
                        f"(limite: {limite_vendas} un./h) a R$ {parse_number(current_price, 0.0):.2f}."
                    ),
                }
            )

    # 4. Catálogo / Full
    if _is_flag_sim(user_notif_cfg.get("Alerta_Catalogo_Full")) and previous_reading is not None:
        prev_full = "Sim" if _is_flag_sim(previous_reading.get("Full")) else "Não"
        curr_full = "Sim" if _is_flag_sim(current_full) else "Não"
        prev_cat = "Sim" if _is_flag_sim(previous_reading.get("Catalogo")) else "Não"
        curr_cat = "Sim" if _is_flag_sim(current_catalog) else "Não"

        changes: List[str] = []
        if prev_full != curr_full:
            changes.append(f"FULL: {prev_full} → {curr_full}")
        if prev_cat != curr_cat:
            changes.append(f"Catálogo (Buy Box): {prev_cat} → {curr_cat}")

        if changes:
            alerts.append(
                {
                    "tipo_alerta": "Catálogo / Full",
                    "concorrente": comp_label,
                    "produto": prod_label,
                    "mensagem": f"Mudança competitiva detectada: {' | '.join(changes)}.",
                }
            )

    return alerts


def dispatch_alerts_to_telegram_and_rows(
    usuario: str,
    data_hora_br: str,
    alerts: List[Dict[str, str]],
    user_notif_cfg: Optional[Dict[str, Any]],
    telegram_bot_token: str,
) -> List[List[Any]]:
    """Formata, dispara no Telegram (quando configurado) e gera linhas para Historico_Notificacoes."""
    if not alerts:
        return []

    chat_id = str((user_notif_cfg or {}).get("Telegram_Chat_ID", "")).strip()
    icon_map = {
        "Estoque Zerado": "🟢",
        "Estoque Baixo": "🟡",
        "Promoção / Queda de Preço": "🔴",
        "Alteração de Preço": "🟠",
        "Pico de Vendas": "🔵",
        "Catálogo / Full": "🟣",
    }

    rows: List[List[Any]] = []
    for alert in alerts:
        tipo_alerta = alert["tipo_alerta"]
        concorrente = alert["concorrente"]
        produto = alert["produto"]
        mensagem = alert["mensagem"]

        rows.append(
            [
                usuario,
                data_hora_br,
                tipo_alerta,
                concorrente,
                produto,
                mensagem,
                "Nao",
            ]
        )

        if chat_id and telegram_bot_token:
            icon = icon_map.get(tipo_alerta, "🔔")
            tg_msg = (
                f"{icon} <b>PetPulse BI · {html_lib.escape(tipo_alerta)}</b>\n"
                f"<b>Concorrente:</b> {html_lib.escape(concorrente)}\n"
                f"<b>Produto:</b> {html_lib.escape(produto[:140])}\n"
                f"<b>Detalhe:</b> {html_lib.escape(mensagem)}\n"
                f"<i>Horário (BRT): {html_lib.escape(data_hora_br)}</i>"
            )
            send_telegram_notification(chat_id, telegram_bot_token, tg_msg)

    return rows


def run_store_xray_monitor(
    spreadsheet: gspread.Spreadsheet,
    session: requests.Session,
    notif_config_index: Optional[Dict[str, Dict[str, Any]]] = None,
    telegram_bot_token: str = "",
    notification_rows_out: Optional[List[List[Any]]] = None,
) -> int:
    """Executa varredura recorrente das lojas cadastradas em Lojas_Monitoradas e grava em Catalogo_Lojas."""
    ws_lojas = get_or_create_worksheet(
        spreadsheet, TAB_LOJAS_MONITORADAS, HEADERS_LOJAS_MONITORADAS
    )
    ws_catalogo = get_or_create_worksheet(
        spreadsheet, TAB_CATALOGO_LOJAS, HEADERS_CATALOGO_LOJAS
    )
    if ws_lojas is None or ws_catalogo is None:
        logger.error("Não foi possível acessar Lojas_Monitoradas ou Catalogo_Lojas.")
        return 1

    lojas_records = read_sheet_records(ws_lojas)
    if not lojas_records:
        logger.info("Nenhuma loja cadastrada em Lojas_Monitoradas.")
        return 0

    lojas_row_lookup: Dict[Tuple[str, str], int] = {}
    try:
        raw_lojas_vals = ws_lojas.get_all_values()
        if len(raw_lojas_vals) >= 2:
            hdrs = [h.strip() for h in raw_lojas_vals[0]]
            u_idx = hdrs.index("Usuario") if "Usuario" in hdrs else 0
            url_idx = hdrs.index("URL_Loja") if "URL_Loja" in hdrs else 4
            for r_num, r_vals in enumerate(raw_lojas_vals[1:], start=2):
                r_user = normalize_text(r_vals[u_idx] if u_idx < len(r_vals) else "")
                r_url = str(r_vals[url_idx] if url_idx < len(r_vals) else "").strip()
                if r_user and r_url:
                    lojas_row_lookup[(r_user, r_url)] = r_num
    except Exception:
        pass

    catalogo_records = read_sheet_records(ws_catalogo)
    history_index = build_store_catalog_history_index(catalogo_records)

    rows_to_append: List[List[Any]] = []
    for idx, loja in enumerate(lojas_records, start=1):
        usuario = str(loja.get("Usuario", "")).strip()
        tipo = str(loja.get("Tipo", "")).strip() or "Concorrente"
        nome_loja_cfg = str(loja.get("Nome_Loja", "")).strip()
        marketplace = str(loja.get("Marketplace", "")).strip()
        url_loja = str(loja.get("URL_Loja", "")).strip()

        if not usuario or not url_loja:
            continue

        logger.info(
            "[Raio-X %d/%d] Varrendo loja (%s | %s): %s",
            idx,
            len(lojas_records),
            usuario,
            tipo,
            url_loja,
        )

        items, resolved_store_name = scrape_store_catalog_publicly(
            session, url_loja, marketplace, nome_loja_cfg
        )

        # Atualiza Nome_Loja na planilha se o usuário deixou vazio
        if not nome_loja_cfg and resolved_store_name:
            try:
                target_row = lojas_row_lookup.get((normalize_text(usuario), url_loja))
                if target_row:
                    ws_lojas.update_cell(target_row, 3, resolved_store_name)
            except Exception:
                pass

        if not items:
            logger.warning("Nenhum anúncio extraído para a loja '%s'.", resolved_store_name)
            continue

        user_notif_cfg = (notif_config_index or {}).get(normalize_text(usuario))
        data_hora_br, _ = format_timestamps_brasilia()
        for item in items:
            id_anuncio = str(item["id_anuncio"]).strip().upper()
            hist_key = (
                normalize_text(usuario),
                normalize_text(resolved_store_name),
                id_anuncio,
            )
            past_rows = history_index.get(hist_key, [])
            last_row = past_rows[-1] if past_rows else None

            vendas_periodo = 0
            if last_row is not None:
                est_ant = parse_int(last_row.get("Estoque"), -1)
                est_atual = parse_int(item.get("estoque"), 0)
                if est_ant > est_atual >= 0:
                    vendas_periodo = est_ant - est_atual
            elif parse_int(item.get("sold_quantity"), 0) > 0:
                # Primeira leitura quando a API expõe histórico acumulado: usa giro inicial conservador
                vendas_periodo = min(5, max(1, parse_int(item.get("sold_quantity"), 0) // 20))

            prev_sales_series = [
                parse_int(r.get("Vendas_Periodo"), 0) for r in past_rows
            ]
            tendencia, escalabilidade = compute_store_item_trend_and_scalability(
                prev_sales_series, vendas_periodo
            )

            rows_to_append.append(
                [
                    usuario,
                    data_hora_br,
                    tipo,
                    resolved_store_name,
                    id_anuncio,
                    item["titulo"],
                    item["preco"],
                    item["estoque"],
                    vendas_periodo,
                    item["full"],
                    item["catalogo"],
                    item["nota"],
                    tendencia,
                    escalabilidade,
                    item["url_produto"],
                ]
            )

            # Detecção de notificações inteligentes para lojas concorrentes
            if (
                notification_rows_out is not None
                and normalize_text(tipo) == "concorrente"
                and user_notif_cfg is not None
            ):
                alerts = evaluate_competitor_alerts(
                    user_notif_cfg=user_notif_cfg,
                    competitor_name=resolved_store_name,
                    product_title=item["titulo"],
                    current_price=item["preco"],
                    current_stock=item["estoque"],
                    vendas_na_hora=vendas_periodo,
                    current_full=item["full"],
                    current_catalog=item["catalogo"],
                    previous_reading=last_row,
                    prev_stock_key="Estoque",
                )
                if alerts:
                    notification_rows_out.extend(
                        dispatch_alerts_to_telegram_and_rows(
                            usuario=usuario,
                            data_hora_br=data_hora_br,
                            alerts=alerts,
                            user_notif_cfg=user_notif_cfg,
                            telegram_bot_token=telegram_bot_token,
                        )
                    )

        time.sleep(random.uniform(1.0, 2.0))

    if rows_to_append:
        try:
            ws_catalogo.append_rows(rows_to_append, value_input_option="RAW")
            logger.info(
                "Raio-X gravou %d linhas em '%s'.",
                len(rows_to_append),
                TAB_CATALOGO_LOJAS,
            )
        except Exception as exc:
            logger.error("Erro ao gravar em '%s': %s", TAB_CATALOGO_LOJAS, exc)
            return 1
    return 0


# ==============================================================================
# PIPELINE PRINCIPAL
# ==============================================================================


def run_monitor() -> int:
    """Executa o ciclo completo de coleta horária, alertas inteligentes e Raio-X de lojas."""
    logger.info("Iniciando monitoramento horário (horário de Brasília)...")
    spreadsheet = connect_google_sheets()
    if spreadsheet is None:
        logger.error("Encerrando execução por falha de conexão com Google Sheets.")
        return 1

    ws_config = get_or_create_worksheet(
        spreadsheet, TAB_CONFIGURACAO, HEADERS_CONFIGURACAO
    )
    ws_historico = get_or_create_worksheet(
        spreadsheet, TAB_HISTORICO_HORA, HEADERS_HISTORICO_HORA
    )
    ws_notif_cfg = get_or_create_worksheet(
        spreadsheet, TAB_CONFIG_NOTIFICACOES, HEADERS_CONFIG_NOTIFICACOES
    )
    ws_notif_hist = get_or_create_worksheet(
        spreadsheet, TAB_HISTORICO_NOTIFICACOES, HEADERS_HISTORICO_NOTIFICACOES
    )

    if ws_config is None or ws_historico is None:
        logger.error("Não foi possível acessar as abas necessárias na planilha.")
        return 1

    notif_config_records = read_sheet_records(ws_notif_cfg)
    notif_config_index = build_notification_config_index(notif_config_records)
    telegram_bot_token = _resolve_telegram_bot_token()
    notification_rows_to_append: List[List[Any]] = []

    session = create_http_session()
    config_records = read_sheet_records(ws_config)
    if not config_records:
        logger.info("Nenhum anúncio cadastrado na aba Configuracao.")
    else:
        historico_records = read_sheet_records(ws_historico)
        exact_index, group_index, group_counts = build_previous_readings_index(
            historico_records, config_records
        )

        rows_to_append: List[List[Any]] = []
        processed_urls_per_user: set[Tuple[str, str]] = set()

        for idx, cfg in enumerate(config_records, start=1):
            usuario = str(cfg.get("Usuario", "")).strip()
            tipo = str(cfg.get("Tipo", "")).strip()
            grupo_produto = str(cfg.get("Grupo_Produto", "")).strip()
            marketplace = str(cfg.get("Marketplace", "")).strip()
            url = str(cfg.get("URL", "")).strip()

            if not usuario or not url:
                logger.warning(
                    "Linha %d de Configuracao ignorada (Usuario ou URL ausente).", idx + 1
                )
                continue

            dedup_key = (normalize_text(usuario), url)
            if dedup_key in processed_urls_per_user:
                logger.info("URL duplicada ignorada para usuário '%s': %s", usuario, url)
                continue
            processed_urls_per_user.add(dedup_key)

            logger.info(
                "[%d/%d] Coletando (%s | %s | %s): %s",
                idx,
                len(config_records),
                usuario,
                tipo,
                marketplace,
                url,
            )

            scraped = scrape_listing_publicly(session, url, marketplace)
            if scraped is None:
                logger.warning(
                    "Coleta falhou para '%s' (%s). Pulando para o próximo anúncio.",
                    url,
                    usuario,
                )
                continue

            previous_reading = find_previous_reading(
                cfg,
                scraped["titulo"],
                exact_index,
                group_index,
                group_counts,
            )

            vendas_na_hora, faturamento_hora, lucro_liquido_hora = calculate_hourly_metrics(
                cfg=cfg,
                preco_atual=scraped["preco"],
                estoque_atual=scraped["estoque_atual"],
                previous_reading=previous_reading,
            )

            data_hora_br, hora_cheia_br = format_timestamps_brasilia()

            row = [
                usuario,
                data_hora_br,
                hora_cheia_br,
                tipo,
                grupo_produto,
                marketplace,
                scraped["titulo"],
                scraped["preco"],
                scraped["estoque_atual"],
                vendas_na_hora,
                faturamento_hora,
                lucro_liquido_hora,
                scraped["full"],
                scraped["catalogo"],
                scraped["nota"],
            ]
            rows_to_append.append(row)

            # Detecção de alertas inteligentes para anúncios de concorrentes
            if normalize_text(tipo) == "concorrente":
                user_notif_cfg = notif_config_index.get(normalize_text(usuario))
                competitor_label = f"{marketplace} ({grupo_produto})" if grupo_produto else marketplace
                alerts = evaluate_competitor_alerts(
                    user_notif_cfg=user_notif_cfg,
                    competitor_name=competitor_label,
                    product_title=scraped["titulo"],
                    current_price=scraped["preco"],
                    current_stock=scraped["estoque_atual"],
                    vendas_na_hora=vendas_na_hora,
                    current_full=scraped["full"],
                    current_catalog=scraped["catalogo"],
                    previous_reading=previous_reading,
                    prev_stock_key="Estoque_Atual",
                )
                if alerts:
                    notification_rows_to_append.extend(
                        dispatch_alerts_to_telegram_and_rows(
                            usuario=usuario,
                            data_hora_br=data_hora_br,
                            alerts=alerts,
                            user_notif_cfg=user_notif_cfg,
                            telegram_bot_token=telegram_bot_token,
                        )
                    )

            logger.info(
                "OK -> Título: '%s' | Preço: R$ %.2f | Estoque: %d | Vendas/h: %d | "
                "Fat/h: R$ %.2f | Lucro/h: R$ %.2f | Full: %s | Catálogo: %s | Nota: %.2f",
                scraped["titulo"][:50],
                scraped["preco"],
                scraped["estoque_atual"],
                vendas_na_hora,
                faturamento_hora,
                lucro_liquido_hora,
                scraped["full"],
                scraped["catalogo"],
                scraped["nota"],
            )

            if idx < len(config_records):
                time.sleep(random.uniform(1.0, 2.2))

        if rows_to_append:
            try:
                ws_historico.append_rows(rows_to_append, value_input_option="RAW")
                logger.info(
                    "Gravadas %d novas linhas em '%s' com sucesso.",
                    len(rows_to_append),
                    TAB_HISTORICO_HORA,
                )
            except Exception as exc:
                logger.error(
                    "Erro ao gravar linhas em '%s': %s", TAB_HISTORICO_HORA, exc
                )
                return 1
        else:
            logger.warning("Nenhuma leitura válida coletada nesta execução.")

    # Executa varredura recorrente do Raio-X de Lojas
    xray_status = run_store_xray_monitor(
        spreadsheet=spreadsheet,
        session=session,
        notif_config_index=notif_config_index,
        telegram_bot_token=telegram_bot_token,
        notification_rows_out=notification_rows_to_append,
    )

    if notification_rows_to_append and ws_notif_hist is not None:
        try:
            ws_notif_hist.append_rows(
                notification_rows_to_append, value_input_option="RAW"
            )
            logger.info(
                "Gravadas %d notificações em '%s'.",
                len(notification_rows_to_append),
                TAB_HISTORICO_NOTIFICACOES,
            )
        except Exception as exc:
            logger.error(
                "Erro ao gravar notificações em '%s': %s",
                TAB_HISTORICO_NOTIFICACOES,
                exc,
            )

    return xray_status


if __name__ == "__main__":
    raise SystemExit(run_monitor())

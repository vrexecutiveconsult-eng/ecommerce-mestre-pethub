import base64
import html as html_lib
import json
import os
import re
import time
import unicodedata
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse

import gspread
import pandas as pd
import plotly.graph_objects as go
import pytz
import requests
import streamlit as st
from bs4 import BeautifulSoup
from fpdf import FPDF
from google import genai
from google.genai import types
from google.oauth2.service_account import Credentials

# ==============================================================================
# CONFIGURAÇÕES GLOBAIS E CONSTANTES
# ==============================================================================

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

HEADERS_USUARIOS = ["Usuario", "Senha", "Nome_Exibicao"]
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
HEADERS_ANUNCIOS_SALVOS = [
    "Usuario",
    "Data",
    "Produto",
    "Titulo_Escolhido",
    "Descricao_Pronta",
    "Nota_Comparacao",
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

PLATAFORMAS_2026 = [
    "Mercado Livre Clássico (12%)",
    "Mercado Livre Premium (17%)",
    "Shopee CNPJ",
    "Shopee CPF",
    "Magalu",
]


# ==============================================================================
# ESTILO EXECUTIVO DARK MODE PREMIUM (GLASSMORPHISM)
# ==============================================================================


def inject_executive_css() -> None:
    """Injeta CSS Dark Mode Premium com Glassmorphism e tipografia limpa."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #E2E8F0;
        }

        .stApp {
            background: radial-gradient(circle at 12% 10%, rgba(56, 189, 248, 0.08) 0%, transparent 38%),
                        radial-gradient(circle at 88% 18%, rgba(16, 185, 129, 0.07) 0%, transparent 35%),
                        #0B0F19;
            background-color: #0B0F19;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0F172A 0%, #0B0F19 100%);
            border-right: 1px solid #1E293B;
        }

        header[data-testid="stHeader"] {
            background-color: rgba(11, 15, 25, 0.75);
            backdrop-filter: blur(10px);
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        /* Cartões Glassmorphism */
        .glass-card {
            background: rgba(30, 41, 59, 0.50);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 1.25rem 1.4rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.05);
            transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
        }

        .glass-card:hover {
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.55);
            box-shadow: 0 14px 36px rgba(14, 165, 233, 0.14), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }

        .kpi-label {
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #94A3B8;
            margin-bottom: 0.4rem;
        }

        .kpi-value {
            font-size: 1.85rem;
            font-weight: 800;
            color: #F8FAFC;
            line-height: 1.15;
            margin-bottom: 0.35rem;
        }

        .kpi-sub {
            font-size: 0.82rem;
            color: #CBD5E1;
        }

        .hero-header {
            background: rgba(30, 41, 59, 0.50);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid #334155;
            border-radius: 18px;
            padding: 1.35rem 1.65rem;
            margin-bottom: 1.4rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        }

        .hero-title {
            font-size: 1.55rem;
            font-weight: 800;
            color: #F8FAFC;
            margin: 0;
            letter-spacing: -0.02em;
        }

        .hero-subtitle {
            font-size: 0.92rem;
            color: #94A3B8;
            margin-top: 0.35rem;
            margin-bottom: 0;
        }

        /* Badges de Alerta e Status */
        .badge {
            display: inline-block;
            padding: 0.24rem 0.62rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.01em;
            border: 1px solid transparent;
            white-space: nowrap;
        }

        .badge-success {
            background: rgba(16, 185, 129, 0.16);
            color: #34D399;
            border-color: rgba(16, 185, 129, 0.35);
        }

        .badge-warning {
            background: rgba(245, 158, 11, 0.16);
            color: #FBBF24;
            border-color: rgba(245, 158, 11, 0.35);
        }

        .badge-danger {
            background: rgba(239, 68, 68, 0.16);
            color: #F87171;
            border-color: rgba(239, 68, 68, 0.35);
        }

        .badge-info {
            background: rgba(56, 189, 248, 0.16);
            color: #38BDF8;
            border-color: rgba(56, 189, 248, 0.35);
        }

        .badge-neutral {
            background: rgba(148, 163, 184, 0.14);
            color: #CBD5E1;
            border-color: rgba(148, 163, 184, 0.25);
        }

        /* Tabela Comparativa Estilizada */
        .exec-table-wrap {
            background: rgba(30, 41, 59, 0.50);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 0.5rem;
            overflow-x: auto;
        }

        table.exec-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.87rem;
        }

        table.exec-table th {
            text-align: left;
            padding: 0.85rem 0.9rem;
            color: #94A3B8;
            font-weight: 700;
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid #334155;
        }

        table.exec-table td {
            padding: 0.88rem 0.9rem;
            border-bottom: 1px solid rgba(51, 65, 85, 0.55);
            color: #E2E8F0;
            vertical-align: middle;
        }

        table.exec-table tr:last-child td {
            border-bottom: none;
        }

        table.exec-table tr:hover td {
            background: rgba(51, 65, 85, 0.28);
        }

        /* Tela de Login */
        .login-box {
            background: rgba(30, 41, 59, 0.55);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid #334155;
            border-radius: 20px;
            padding: 2rem 2.2rem 1.6rem 2.2rem;
            box-shadow: 0 24px 55px rgba(0, 0, 0, 0.45);
        }

        /* Inputs e Botões */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > div {
            background-color: rgba(15, 23, 42, 0.85) !important;
            border: 1px solid #334155 !important;
            color: #F8FAFC !important;
            border-radius: 10px !important;
        }

        div[data-testid="stExpander"] {
            background: rgba(30, 41, 59, 0.42);
            border: 1px solid #334155;
            border-radius: 14px;
        }

        .stButton > button, .stDownloadButton > button {
            border-radius: 10px;
            font-weight: 600;
            border: 1px solid #334155;
            transition: all 0.2s ease;
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%);
            border: none;
            color: #FFFFFF;
        }

        .stButton > button[kind="primary"]:hover {
            box-shadow: 0 6px 20px rgba(14, 165, 233, 0.35);
            transform: translateY(-1px);
        }

        /* Aba 8: Ranking Geral & Batalha */
        .ranking-card {
            background: rgba(30, 41, 59, 0.50);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.45rem;
            box-shadow: 0 10px 26px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.05);
            transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
        }

        .ranking-card:hover {
            border-color: rgba(56, 189, 248, 0.55);
            box-shadow: 0 14px 32px rgba(14, 165, 233, 0.14);
        }

        .rank-medal {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 44px;
            height: 44px;
            border-radius: 12px;
            font-weight: 800;
            font-size: 1rem;
            letter-spacing: -0.02em;
            border: 1px solid rgba(255, 255, 255, 0.12);
        }

        .rank-medal-1 {
            background: linear-gradient(135deg, rgba(250, 204, 21, 0.28), rgba(234, 179, 8, 0.12));
            color: #FDE047;
            border-color: rgba(250, 204, 21, 0.55);
        }

        .rank-medal-2 {
            background: linear-gradient(135deg, rgba(226, 232, 240, 0.24), rgba(148, 163, 184, 0.10));
            color: #F1F5F9;
            border-color: rgba(203, 213, 225, 0.50);
        }

        .rank-medal-3 {
            background: linear-gradient(135deg, rgba(251, 146, 60, 0.26), rgba(234, 88, 12, 0.12));
            color: #FDBA74;
            border-color: rgba(251, 146, 60, 0.50);
        }

        .rank-medal-n {
            background: rgba(56, 189, 248, 0.12);
            color: #38BDF8;
            border-color: rgba(56, 189, 248, 0.30);
        }

        /* Caixa Interativa de Similaridade com destaque :hover para ⚔️ Comparar */
        .match-compare-box {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.65rem;
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(56, 189, 248, 0.38);
            border-radius: 12px;
            padding: 0.55rem 0.85rem;
            margin-bottom: 0.45rem;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.26s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .match-compare-box .match-score-pill {
            color: #E2E8F0;
            font-size: 0.80rem;
            font-weight: 600;
            transition: opacity 0.22s ease, transform 0.22s ease;
        }

        .match-compare-box .match-score-pill strong {
            color: #38BDF8;
            font-weight: 800;
        }

        .match-compare-box .match-hover-cta {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            padding: 0.22rem 0.62rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 700;
            color: #94A3B8;
            background: rgba(51, 65, 85, 0.45);
            border: 1px solid rgba(148, 163, 184, 0.28);
            transition: all 0.26s cubic-bezier(0.4, 0, 0.2, 1);
            white-space: nowrap;
        }

        .match-compare-box:hover {
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.24), rgba(37, 99, 235, 0.24));
            border-color: #38BDF8;
            transform: translateY(-1px);
            box-shadow: 0 8px 22px rgba(14, 165, 233, 0.26);
        }

        .match-compare-box:hover .match-hover-cta {
            color: #FFFFFF;
            background: linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%);
            border-color: rgba(255, 255, 255, 0.45);
            transform: scale(1.06);
            box-shadow: 0 4px 14px rgba(14, 165, 233, 0.45);
        }

        /* Aba 9: Sistema de Notificações Inteligentes */
        .notif-unread-banner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.75rem;
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.14), rgba(30, 41, 59, 0.72));
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(56, 189, 248, 0.45);
            border-radius: 14px;
            padding: 0.7rem 1.15rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 24px rgba(14, 165, 233, 0.12);
        }

        .notif-card {
            background: rgba(30, 41, 59, 0.56);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid #334155;
            border-left-width: 4px;
            border-radius: 14px;
            padding: 1rem 1.15rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }

        .notif-card:hover {
            transform: translateY(-1px);
        }

        .notif-card-promo {
            border-left-color: #EF4444;
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.11), rgba(30, 41, 59, 0.62));
        }

        .notif-card-stock {
            border-left-color: #10B981;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.11), rgba(30, 41, 59, 0.62));
        }

        .notif-card-peak {
            border-left-color: #38BDF8;
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.11), rgba(30, 41, 59, 0.62));
        }

        .notif-card-logistics {
            border-left-color: #F59E0B;
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.10), rgba(30, 41, 59, 0.62));
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# UTILITÁRIOS DE FORMATAÇÃO E PARSING
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
    """Converte strings numéricas BR/US para float com segurança."""
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)

    raw = str(value).strip()
    if not raw:
        return default

    cleaned = re.sub(r"[R$\s%]", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"[^\d.,\-]", "", cleaned)
    if not cleaned or cleaned in {"-", ".", ","}:
        return default

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
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
    """Converte valor arbitrário para inteiro."""
    if value is None or isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))

    raw = str(value).strip()
    if not raw:
        return default
    match = re.search(r"-?\d+", raw.replace(".", ""))
    if not match:
        return default
    try:
        return int(match.group(0))
    except ValueError:
        return default


def format_brl(value: float) -> str:
    """Formata número float no padrão monetário brasileiro R$ 1.234,56."""
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def get_brasilia_now() -> datetime:
    """Retorna datetime atual no fuso de Brasília."""
    return datetime.now(BRASILIA_TZ)


def safe_latin1(text: Any) -> str:
    """Sanitiza texto para geração de PDF com fonte padrão fpdf2 sem erros de encoding."""
    if text is None:
        return ""
    return str(text).encode("latin-1", "replace").decode("latin-1")


# ==============================================================================
# CONEXÃO E OPERAÇÕES GOOGLE SHEETS (COM CACHE E TRY/EXCEPT)
# ==============================================================================


def _load_service_account_info() -> Dict[str, Any]:
    """Carrega credenciais via st.secrets['gcp_service_account'] ou GCP_SERVICE_ACCOUNT_JSON."""
    try:
        if "gcp_service_account" in st.secrets:
            secret_data = st.secrets["gcp_service_account"]
            if isinstance(secret_data, str):
                return json.loads(secret_data)
            return dict(secret_data)
    except Exception:
        pass

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
            raise ValueError(f"Erro ao ler GCP_SERVICE_ACCOUNT_JSON: {exc}") from exc

    raise RuntimeError(
        "Credenciais não encontradas em st.secrets['gcp_service_account'] "
        "nem em GCP_SERVICE_ACCOUNT_JSON."
    )


def _resolve_sheet_name() -> str:
    """Obtém o nome ou URL da planilha via st.secrets ou variável de ambiente."""
    try:
        if "SHEET_NAME" in st.secrets:
            val = str(st.secrets["SHEET_NAME"]).strip()
            if val:
                return val
    except Exception:
        pass

    env_name = os.environ.get("SHEET_NAME", "").strip()
    if env_name:
        return env_name

    raise RuntimeError("SHEET_NAME não configurado em st.secrets ou variável de ambiente.")


def get_gspread_spreadsheet() -> Optional[gspread.Spreadsheet]:
    """Abre conexão com a planilha Google Sheets com proteção contra exceções."""
    try:
        sa_info = _load_service_account_info()
        sheet_id = _resolve_sheet_name()
        credentials = Credentials.from_service_account_info(
            sa_info, scopes=GOOGLE_SHEETS_SCOPES
        )
        client = gspread.authorize(credentials)
        if sheet_id.startswith("https://"):
            return client.open_by_url(sheet_id)
        return client.open(sheet_id)
    except Exception as exc:
        st.error(f"Não foi possível conectar ao Google Sheets: {exc}")
        return None


def _get_or_create_tab(
    spreadsheet: gspread.Spreadsheet,
    tab_name: str,
    headers: List[str],
) -> Optional[gspread.Worksheet]:
    """Obtém aba existente ou cria com o cabeçalho oficial."""
    try:
        try:
            ws = spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(
                title=tab_name, rows=1000, cols=max(len(headers), 15)
            )
            ws.append_row(headers, value_input_option="RAW")
            return ws

        first_row = ws.row_values(1)
        if not first_row:
            ws.append_row(headers, value_input_option="RAW")
        return ws
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def load_sheet_tab_cached(tab_name: str) -> List[Dict[str, Any]]:
    """Lê uma aba do Google Sheets com cache de 5 minutos (@st.cache_data(ttl=300))."""
    headers_map = {
        TAB_USUARIOS: HEADERS_USUARIOS,
        TAB_CONFIGURACAO: HEADERS_CONFIGURACAO,
        TAB_HISTORICO_HORA: HEADERS_HISTORICO_HORA,
        TAB_ANUNCIOS_SALVOS: HEADERS_ANUNCIOS_SALVOS,
        TAB_LOJAS_MONITORADAS: HEADERS_LOJAS_MONITORADAS,
        TAB_CATALOGO_LOJAS: HEADERS_CATALOGO_LOJAS,
        TAB_CONFIG_NOTIFICACOES: HEADERS_CONFIG_NOTIFICACOES,
        TAB_HISTORICO_NOTIFICACOES: HEADERS_HISTORICO_NOTIFICACOES,
    }
    try:
        spreadsheet = get_gspread_spreadsheet()
        if spreadsheet is None:
            return []
        ws = _get_or_create_tab(
            spreadsheet, tab_name, headers_map.get(tab_name, [])
        )
        if ws is None:
            return []

        values = ws.get_all_values()
        if not values or len(values) < 2:
            return []

        headers = [str(h).strip() for h in values[0]]
        records: List[Dict[str, Any]] = []
        for row in values[1:]:
            if not any(str(cell).strip() for cell in row):
                continue
            item: Dict[str, Any] = {}
            for idx, header in enumerate(headers):
                if not header:
                    continue
                item[header] = str(row[idx]).strip() if idx < len(row) else ""
            records.append(item)
        return records
    except Exception:
        return []


def append_config_row_to_sheets(row_data: List[Any]) -> Tuple[bool, str]:
    """Adiciona uma nova linha na aba Configuracao e limpa o cache."""
    try:
        spreadsheet = get_gspread_spreadsheet()
        if spreadsheet is None:
            return False, "Falha ao conectar ao Google Sheets."

        ws = _get_or_create_tab(spreadsheet, TAB_CONFIGURACAO, HEADERS_CONFIGURACAO)
        if ws is None:
            return False, "Não foi possível abrir a aba Configuracao."

        ws.append_row(row_data, value_input_option="RAW")
        st.cache_data.clear()
        return True, "Anúncio salvo com sucesso na aba Configuracao!"
    except Exception as exc:
        return False, f"Erro ao salvar na planilha: {exc}"


def append_saved_ad_to_sheets(row_data: List[Any]) -> Tuple[bool, str]:
    """Grava anúncio campeão na aba Anuncios_Salvos do Google Sheets."""
    try:
        spreadsheet = get_gspread_spreadsheet()
        if spreadsheet is None:
            return False, "Falha ao conectar ao Google Sheets."

        ws = _get_or_create_tab(spreadsheet, TAB_ANUNCIOS_SALVOS, HEADERS_ANUNCIOS_SALVOS)
        if ws is None:
            return False, "Não foi possível abrir a aba Anuncios_Salvos."

        ws.append_row(row_data, value_input_option="RAW")
        st.cache_data.clear()
        return True, "Anúncio salvo com sucesso na aba Anuncios_Salvos!"
    except Exception as exc:
        return False, f"Erro ao salvar em Anuncios_Salvos: {exc}"


def append_monitored_store_to_sheets(row_data: List[Any]) -> Tuple[bool, str]:
    """Salva uma loja inteira na aba Lojas_Monitoradas e limpa o cache."""
    try:
        spreadsheet = get_gspread_spreadsheet()
        if spreadsheet is None:
            return False, "Falha ao conectar ao Google Sheets."

        ws = _get_or_create_tab(
            spreadsheet, TAB_LOJAS_MONITORADAS, HEADERS_LOJAS_MONITORADAS
        )
        if ws is None:
            return False, "Não foi possível abrir a aba Lojas_Monitoradas."

        ws.append_row(row_data, value_input_option="RAW")
        st.cache_data.clear()
        return True, "Loja adicionada com sucesso à aba Lojas_Monitoradas!"
    except Exception as exc:
        return False, f"Erro ao salvar loja na planilha: {exc}"


def _resolve_telegram_bot_token() -> str:
    """Obtém TELEGRAM_BOT_TOKEN via st.secrets ou variável de ambiente com segurança."""
    try:
        if "TELEGRAM_BOT_TOKEN" in st.secrets:
            val = str(st.secrets["TELEGRAM_BOT_TOKEN"]).strip()
            if val:
                return val
    except Exception:
        pass
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def send_telegram_test_message(
    chat_id: str, usuario: str, nome_exibicao: str
) -> Tuple[bool, str]:
    """Dispara mensagem de teste via API oficial do Telegram."""
    clean_chat = (chat_id or "").strip()
    if not clean_chat:
        return False, "Informe o Telegram Chat ID antes de enviar o teste."

    token = _resolve_telegram_bot_token()
    if not token:
        return (
            False,
            "Token TELEGRAM_BOT_TOKEN não configurado em st.secrets ou variáveis de ambiente.",
        )

    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    now_str = get_brasilia_now().strftime("%d/%m/%Y %H:%M:%S")
    msg_html = (
        f"🔔 <b>Radar Pet Pro · Teste de Conexão</b>\n"
        f"Olá, <b>{html_lib.escape(nome_exibicao)}</b> (<code>@{html_lib.escape(usuario)}</code>)!\n"
        f"Seu canal de alertas inteligentes do monitoramento horário está ativo e validado.\n"
        f"<i>Enviado em {html_lib.escape(now_str)} (BRT)</i>"
    )
    try:
        resp = requests.post(
            endpoint,
            json={
                "chat_id": clean_chat,
                "text": msg_html,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=12,
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get("ok"):
                return True, "Mensagem de teste enviada com sucesso para o Telegram!"
        return False, f"Erro retornado pelo Telegram (HTTP {resp.status_code}): {resp.text[:180]}"
    except Exception as exc:
        return False, f"Falha de comunicação com o Telegram: {exc}"


def save_notification_config_to_sheets(
    usuario: str,
    ativo_geral: bool,
    telegram_chat_id: str,
    alerta_estoque_baixo: bool,
    limite_estoque: int,
    alerta_promocao: bool,
    alerta_venda_pico: bool,
    limite_venda_hora: int,
    alerta_catalogo_full: bool,
) -> Tuple[bool, str]:
    """Cria ou atualiza a linha de preferências do usuário em Config_Notificacoes."""
    row_values = [
        usuario,
        "Sim" if ativo_geral else "Nao",
        telegram_chat_id.strip(),
        "Sim" if alerta_estoque_baixo else "Nao",
        max(0, int(limite_estoque)),
        "Sim" if alerta_promocao else "Nao",
        "Sim" if alerta_venda_pico else "Nao",
        max(1, int(limite_venda_hora)),
        "Sim" if alerta_catalogo_full else "Nao",
    ]
    try:
        spreadsheet = get_gspread_spreadsheet()
        if spreadsheet is None:
            return False, "Falha ao conectar ao Google Sheets."

        ws = _get_or_create_tab(
            spreadsheet, TAB_CONFIG_NOTIFICACOES, HEADERS_CONFIG_NOTIFICACOES
        )
        if ws is None:
            return False, "Não foi possível abrir a aba Config_Notificacoes."

        all_vals = ws.get_all_values()
        target_row_idx: Optional[int] = None
        if len(all_vals) >= 2:
            headers = [str(h).strip() for h in all_vals[0]]
            user_col = headers.index("Usuario") if "Usuario" in headers else 0
            for idx, r_vals in enumerate(all_vals[1:], start=2):
                cell_user = str(r_vals[user_col]).strip() if user_col < len(r_vals) else ""
                if cell_user.lower() == usuario.strip().lower():
                    target_row_idx = idx
                    break

        if target_row_idx is not None:
            cells = [
                gspread.Cell(row=target_row_idx, col=col_i, value=val)
                for col_i, val in enumerate(row_values, start=1)
            ]
            ws.update_cells(cells, value_input_option="RAW")
        else:
            ws.append_row(row_values, value_input_option="RAW")

        st.cache_data.clear()
        return True, "Preferências de notificação salvas em Config_Notificacoes!"
    except Exception as exc:
        return False, f"Erro ao salvar preferências: {exc}"


def mark_all_notifications_read_in_sheets(usuario: str) -> Tuple[bool, str]:
    """Marca todas as notificações de Historico_Notificacoes do usuário como Lida = 'Sim'."""
    try:
        spreadsheet = get_gspread_spreadsheet()
        if spreadsheet is None:
            return False, "Falha ao conectar ao Google Sheets."

        ws = _get_or_create_tab(
            spreadsheet, TAB_HISTORICO_NOTIFICACOES, HEADERS_HISTORICO_NOTIFICACOES
        )
        if ws is None:
            return False, "Não foi possível abrir a aba Historico_Notificacoes."

        all_vals = ws.get_all_values()
        if len(all_vals) < 2:
            return True, "Nenhuma notificação pendente."

        headers = [str(h).strip() for h in all_vals[0]]
        user_col = headers.index("Usuario") if "Usuario" in headers else 0
        lida_col = headers.index("Lida") if "Lida" in headers else 6

        cells_to_update: List[gspread.Cell] = []
        for r_idx, r_vals in enumerate(all_vals[1:], start=2):
            row_user = str(r_vals[user_col]).strip() if user_col < len(r_vals) else ""
            row_lida = str(r_vals[lida_col]).strip() if lida_col < len(r_vals) else ""
            if (
                row_user.lower() == usuario.strip().lower()
                and normalize_text(row_lida) != "sim"
            ):
                cells_to_update.append(
                    gspread.Cell(row=r_idx, col=lida_col + 1, value="Sim")
                )

        if not cells_to_update:
            return True, "Todas as notificações já estavam marcadas como lidas."

        ws.update_cells(cells_to_update, value_input_option="RAW")
        st.cache_data.clear()
        return True, f"{len(cells_to_update)} notificação(ões) marcada(s) como lida(s)."
    except Exception as exc:
        return False, f"Erro ao atualizar notificações na planilha: {exc}"


def get_gemini_client() -> genai.Client:
    """Inicializa o cliente oficial google-genai usando GEMINI_API_KEY do ambiente ou st.secrets."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        try:
            if "GEMINI_API_KEY" in st.secrets:
                api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
                if api_key:
                    os.environ["GEMINI_API_KEY"] = api_key
        except Exception:
            pass

    if api_key:
        return genai.Client(api_key=api_key)
    return genai.Client()


def parse_gemini_json(raw_text: str) -> Dict[str, Any]:
    """Extrai e interpreta JSON retornado pelo Gemini com tolerância a blocos markdown."""
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("Resposta vazia do modelo Gemini.")

    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    elif not text.startswith("{"):
        brace_match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        if brace_match:
            text = brace_match.group(1).strip()

    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Formato JSON inesperado retornado pelo Gemini.")
    return data


def extract_real_seo_keywords(titles: List[str], top_n: int = 18) -> List[Tuple[str, int]]:
    """Extrai termos reais mais frequentes nos títulos dos líderes de busca (sem inventar palavras)."""
    stopwords = {
        "de", "da", "do", "das", "dos", "para", "com", "sem", "em", "na", "no",
        "nas", "nos", "e", "ou", "a", "o", "as", "os", "um", "uma", "por", "ate",
        "kit", "unidade", "unidades", "un", "c/", "p/",
    }
    counter: Counter[str] = Counter()
    for title in titles:
        tokens = re.findall(r"[A-Za-zÀ-ÿ0-9]+", str(title))
        seen_in_title = set()
        for tok in tokens:
            norm = normalize_text(tok)
            if len(norm) <= 1 or norm in stopwords:
                continue
            if norm not in seen_in_title:
                counter[tok.strip()] += 1
                seen_in_title.add(norm)
    return counter.most_common(top_n)


def scrape_competitor_listing_for_ai(url: str) -> Optional[Dict[str, Any]]:
    """Coleta publicamente título, preço e descrição do anúncio concorrente para comparação."""
    clean_url = (url or "").strip()
    if not clean_url.startswith(("http://", "https://")):
        return None

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }
    try:
        resp = requests.get(clean_url, headers=headers, timeout=18, allow_redirects=True)
        if resp.status_code != 200 or not resp.text:
            return None

        soup = BeautifulSoup(resp.text, "lxml")

        # Título
        titulo = ""
        h1 = soup.select_one("h1.ui-pdp-title, #productTitle, h1")
        if h1:
            titulo = h1.get_text(" ", strip=True)
        if not titulo:
            og_title = soup.find("meta", attrs={"property": "og:title"})
            if og_title and og_title.get("content"):
                titulo = str(og_title["content"]).strip()

        # Preço
        preco = 0.0
        meta_price = soup.find("meta", attrs={"itemprop": "price"})
        if meta_price and meta_price.get("content"):
            preco = parse_number(meta_price["content"], 0.0)
        if preco <= 0:
            price_el = soup.select_one(
                ".ui-pdp-price__second-line .andes-money-amount, .a-price .a-offscreen"
            )
            if price_el:
                frac = price_el.select_one(".andes-money-amount__fraction")
                cents = price_el.select_one(".andes-money-amount__cents")
                if frac:
                    c_txt = cents.get_text(strip=True) if cents else "00"
                    preco = parse_number(f"{frac.get_text(strip=True)},{c_txt}", 0.0)
                else:
                    preco = parse_number(price_el.get_text(strip=True), 0.0)

        # Descrição
        desc_el = soup.select_one(
            ".ui-pdp-description__content, #productDescription, #feature-bullets"
        )
        descricao = desc_el.get_text("\n", strip=True) if desc_el else ""
        if not descricao:
            og_desc = soup.find("meta", attrs={"name": "description"}) or soup.find(
                "meta", attrs={"property": "og:description"}
            )
            if og_desc and og_desc.get("content"):
                descricao = str(og_desc["content"]).strip()

        return {
            "url": clean_url,
            "titulo": titulo or "Título não identificado",
            "preco": round(preco, 2),
            "descricao": descricao[:2500] if descricao else "Descrição pública indisponível.",
        }
    except Exception:
        return None


# ==============================================================================
# AUTENTICAÇÃO MULTI-USUÁRIO E ISOLAMENTO DE DADOS
# ==============================================================================


def validate_user_credentials(
    username: str, password: str
) -> Optional[Dict[str, str]]:
    """Valida Usuario e Senha na aba Usuarios do Google Sheets."""
    user_input = username.strip()
    pass_input = password.strip()
    if not user_input or not pass_input:
        return None

    try:
        users = load_sheet_tab_cached(TAB_USUARIOS)
        for row in users:
            sheet_user = str(row.get("Usuario", "")).strip()
            sheet_pass = str(row.get("Senha", "")).strip()
            if sheet_user.lower() == user_input.lower() and sheet_pass == pass_input:
                return {
                    "usuario": sheet_user,
                    "nome_exibicao": str(
                        row.get("Nome_Exibicao", "") or sheet_user
                    ).strip(),
                }
        return None
    except Exception:
        return None


def filter_user_dataframe(records: List[Dict[str, Any]], usuario: str) -> pd.DataFrame:
    """Isola 100% dos registros pelo Usuario autenticado em st.session_state."""
    if not records or not usuario:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    if "Usuario" not in df.columns:
        return pd.DataFrame()
    mask = df["Usuario"].astype(str).str.strip().str.lower() == usuario.strip().lower()
    return df.loc[mask].copy()


def prepare_history_dataframe(
    records: List[Dict[str, Any]], usuario: str
) -> pd.DataFrame:
    """Prepara DataFrame tipado do Historico_Hora isolado por usuário."""
    df = filter_user_dataframe(records, usuario)
    if df.empty:
        return df

    for col in ["Preco", "Faturamento_Hora", "Lucro_Liquido_Hora", "Nota"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: parse_number(x, 0.0))
        else:
            df[col] = 0.0

    for col in ["Estoque_Atual", "Vendas_na_Hora"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: parse_int(x, 0))
        else:
            df[col] = 0

    df["Data_Hora_dt"] = pd.to_datetime(
        df.get("Data_Hora", ""), errors="coerce"
    )
    df["Data_Dia"] = df["Data_Hora_dt"].dt.strftime("%Y-%m-%d").fillna("")
    df["Hora_Int"] = df["Data_Hora_dt"].dt.hour.fillna(0).astype(int)
    df["Tipo_Norm"] = df.get("Tipo", "").apply(normalize_text)
    return df


def render_login_screen() -> None:
    """Renderiza tela de login executiva com Glassmorphism."""
    col_l, col_c, col_r = st.columns([1.15, 1.3, 1.15])
    with col_c:
        st.markdown("<div style='height: 3.5rem;'></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="login-box">
                <div style="display:flex; align-items:center; gap:0.65rem; margin-bottom:0.6rem;">
                    <span style="font-size:1.7rem;">🐾</span>
                    <div>
                        <div style="font-size:1.35rem; font-weight:800; color:#F8FAFC; line-height:1.15;">
                            Radar Pet Pro
                        </div>
                        <div style="font-size:0.82rem; color:#38BDF8; font-weight:600;">
                            Inteligência Executiva para E-commerce Pet
                        </div>
                    </div>
                </div>
                <p style="font-size:0.88rem; color:#94A3B8; margin-bottom:1.25rem;">
                    Acesse sua conta para monitorar vendas horárias, margem líquida e movimentação de concorrentes.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            usuario = st.text_input("Usuário", placeholder="ex: loja_pet_prime")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            submitted = st.form_submit_button(
                "Entrar no Painel Executivo", type="primary", use_container_width=True
            )

            if submitted:
                if not usuario.strip() or not senha.strip():
                    st.warning("Informe usuário e senha para continuar.")
                else:
                    with st.spinner("Validando credenciais no Google Sheets..."):
                        auth_user = validate_user_credentials(usuario, senha)
                    if auth_user:
                        st.session_state["usuario"] = auth_user["usuario"]
                        st.session_state["nome_exibicao"] = auth_user["nome_exibicao"]
                        st.rerun()
                    else:
                        st.error("Usuário ou senha inválidos na aba Usuarios.")


# ==============================================================================
# ABA 1: BATALHA DE HORÁRIO DE PICO + PDF + CADASTRO NA CONFIGURACAO
# ==============================================================================


def generate_executive_pdf(
    nome_exibicao: str,
    data_ref: str,
    faturamento: float,
    lucro: float,
    ticket_medio: float,
    total_vendas: int,
    df_resumo: pd.DataFrame,
) -> bytes:
    """Gera relatório executivo em PDF usando fpdf2."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Cabeçalho
    pdf.set_fill_color(11, 15, 25)
    pdf.rect(0, 0, 210, 34, "F")
    pdf.set_text_color(248, 250, 252)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(12, 10)
    pdf.cell(0, 8, safe_latin1("Radar Pet Pro - Relatorio Executivo de Performance"), ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(12)
    now_str = get_brasilia_now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(
        0,
        6,
        safe_latin1(
            f"Conta: {nome_exibicao} | Periodo: {data_ref} | Gerado em: {now_str} (BRT)"
        ),
        ln=True,
    )

    # KPIs
    pdf.set_text_color(15, 23, 42)
    pdf.ln(14)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, safe_latin1("Indicadores Principais (Meus Anuncios)"), ln=True)
    pdf.ln(2)

    kpis = [
        ("Faturamento no Periodo", format_brl(faturamento)),
        ("Lucro Liquido Estimado", format_brl(lucro)),
        ("Ticket Medio", format_brl(ticket_medio)),
        ("Total de Vendas", f"{total_vendas} un."),
    ]
    pdf.set_font("Helvetica", "", 10)
    for label, val in kpis:
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(90, 8, safe_latin1(f"  {label}"), border=1, fill=True)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(95, 8, safe_latin1(f"  {val}"), border=1, ln=True)
        pdf.set_font("Helvetica", "", 10)

    # Tabela por Grupo de Produto
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, safe_latin1("Desempenho por Grupo de Produto"), ln=True)
    pdf.ln(2)

    if df_resumo.empty:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 8, safe_latin1("Sem registros para o periodo selecionado."), ln=True)
    else:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(30, 41, 59)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(55, 8, safe_latin1("Grupo Produto"), border=1, fill=True)
        pdf.cell(32, 8, safe_latin1("Tipo"), border=1, fill=True)
        pdf.cell(23, 8, safe_latin1("Vendas"), border=1, fill=True, align="R")
        pdf.cell(38, 8, safe_latin1("Faturamento"), border=1, fill=True, align="R")
        pdf.cell(37, 8, safe_latin1("Lucro Liq."), border=1, fill=True, align="R", ln=True)

        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(15, 23, 42)
        for _, row in df_resumo.head(30).iterrows():
            pdf.cell(55, 7, safe_latin1(str(row["Grupo_Produto"])[:28]), border=1)
            pdf.cell(32, 7, safe_latin1(str(row["Tipo"])[:16]), border=1)
            pdf.cell(23, 7, safe_latin1(str(int(row["Vendas"]))), border=1, align="R")
            pdf.cell(38, 7, safe_latin1(format_brl(float(row["Faturamento"]))), border=1, align="R")
            pdf.cell(37, 7, safe_latin1(format_brl(float(row["Lucro"]))), border=1, align="R", ln=True)

    output = pdf.output(dest="S")
    if isinstance(output, str):
        return output.encode("latin-1")
    return bytes(output)


def render_add_config_expander(usuario: str) -> None:
    """Formulário expansível para cadastrar novos links/produtos direto na aba Configuracao."""
    with st.expander("➕ Adicionar Novo Link / Produto à Planilha (Configuracao)", expanded=False):
        with st.form("add_config_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1, 1.4, 1.1])
            tipo = c1.selectbox("Tipo de Anúncio", ["Meu Anuncio", "Concorrente"])
            grupo = c2.text_input(
                "Grupo do Produto",
                placeholder="ex: Tapete Higiênico 30un",
                help="Use o mesmo nome de grupo para comparar seu anúncio com seus concorrentes.",
            )
            marketplace = c3.selectbox(
                "Marketplace",
                ["Mercado Livre", "Amazon", "Shopee", "Magalu", "Petz", "Cobasi", "Outro"],
            )

            url = st.text_input(
                "URL Pública do Anúncio",
                placeholder="https://produto.mercadolivre.com.br/MLB-...",
            )

            f1, f2, f3, f4, f5 = st.columns(5)
            meu_custo = f1.number_input("Meu Custo (R$)", min_value=0.0, value=0.0, step=1.0)
            imposto_pct = f2.number_input("Imposto (%)", min_value=0.0, max_value=100.0, value=6.0, step=0.5)
            comissao_pct = f3.number_input("Comissão (%)", min_value=0.0, max_value=100.0, value=12.0, step=0.5)
            taxa_fixa = f4.number_input("Taxa Fixa (R$)", min_value=0.0, value=0.0, step=0.5)
            frete_est = f5.number_input("Frete Est. (R$)", min_value=0.0, value=0.0, step=1.0)

            submitted = st.form_submit_button(
                "Salvar na aba Configuracao", type="primary", use_container_width=True
            )
            if submitted:
                if not grupo.strip():
                    st.warning("Informe o Grupo do Produto.")
                elif not url.strip().startswith(("http://", "https://")):
                    st.warning("Informe uma URL válida começando com http:// ou https://.")
                else:
                    row_to_save = [
                        usuario,
                        tipo,
                        grupo.strip(),
                        marketplace,
                        url.strip(),
                        round(float(meu_custo), 2),
                        round(float(imposto_pct), 2),
                        round(float(comissao_pct), 2),
                        round(float(taxa_fixa), 2),
                        round(float(frete_est), 2),
                    ]
                    with st.spinner("Salvando configuração no Google Sheets..."):
                        ok, msg = append_config_row_to_sheets(row_to_save)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


def render_batalha_horario_pico(
    usuario: str, nome_exibicao: str, df_hist: pd.DataFrame, df_cfg: pd.DataFrame
) -> None:
    """Aba 1: Batalha de Horário de Pico, KPIs, Área Sobreposta Plotly, PDF e Cadastro."""
    st.markdown(
        """
        <div class="hero-header">
            <h1 class="hero-title">⚡ Batalha de Horário de Pico</h1>
            <p class="hero-subtitle">
                Acompanhe faturamento, lucro líquido e o ritmo de vendas hora a hora (00h–23h) frente à concorrência.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_add_config_expander(usuario)

    hoje_str = get_brasilia_now().strftime("%Y-%m-%d")

    if df_hist.empty:
        st.info(
            "Ainda não existem coletas em Historico_Hora para o seu usuário. "
            "Cadastre anúncios acima e execute o monitor horário para visualizar os gráficos."
        )
        return

    # Filtros de período e grupo
    f_col1, f_col2, f_col3 = st.columns([1.1, 1.3, 1.0])
    available_days = sorted(
        [d for d in df_hist["Data_Dia"].unique().tolist() if d], reverse=True
    )
    periodo_opcoes = ["Hoje (" + hoje_str + ")", "Últimos 7 dias", "Todo o histórico"]
    if available_days and hoje_str not in available_days:
        periodo_opcoes.insert(1, f"Último dia com dados ({available_days[0]})")

    sel_periodo = f_col1.selectbox("Período de Análise", periodo_opcoes)
    grupos_disp = ["Todos"] + sorted(
        [g for g in df_hist["Grupo_Produto"].dropna().unique().tolist() if str(g).strip()]
    )
    sel_grupo = f_col2.selectbox("Filtrar por Grupo de Produto", grupos_disp)

    df_view = df_hist.copy()
    if sel_grupo != "Todos":
        df_view = df_view[df_view["Grupo_Produto"] == sel_grupo]

    if sel_periodo.startswith("Hoje"):
        df_kpi = df_view[df_view["Data_Dia"] == hoje_str]
        label_periodo = f"Hoje ({hoje_str})"
    elif sel_periodo.startswith("Último dia com dados"):
        last_day = available_days[0]
        df_kpi = df_view[df_view["Data_Dia"] == last_day]
        label_periodo = last_day
    elif sel_periodo == "Últimos 7 dias":
        cutoff = (get_brasilia_now() - pd.Timedelta(days=6)).strftime("%Y-%m-%d")
        df_kpi = df_view[df_view["Data_Dia"] >= cutoff]
        label_periodo = "Últimos 7 dias"
    else:
        df_kpi = df_view
        label_periodo = "Histórico Completo"

    df_meus = df_kpi[df_kpi["Tipo_Norm"] == "meu anuncio"]
    df_conc = df_kpi[df_kpi["Tipo_Norm"] != "meu anuncio"]

    faturamento_hoje = float(df_meus["Faturamento_Hora"].sum()) if not df_meus.empty else 0.0
    lucro_hoje = float(df_meus["Lucro_Liquido_Hora"].sum()) if not df_meus.empty else 0.0
    total_vendas = int(df_meus["Vendas_na_Hora"].sum()) if not df_meus.empty else 0
    ticket_medio = (faturamento_hoje / total_vendas) if total_vendas > 0 else 0.0
    margem_pct = (lucro_hoje / faturamento_hoje * 100.0) if faturamento_hoje > 0 else 0.0
    vendas_conc = int(df_conc["Vendas_na_Hora"].sum()) if not df_conc.empty else 0

    # Resumo para PDF
    df_resumo_pdf = (
        df_kpi.groupby(["Grupo_Produto", "Tipo"], as_index=False)
        .agg(
            Vendas=("Vendas_na_Hora", "sum"),
            Faturamento=("Faturamento_Hora", "sum"),
            Lucro=("Lucro_Liquido_Hora", "sum"),
        )
        .sort_values("Faturamento", ascending=False)
    )

    with f_col3:
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        pdf_bytes = generate_executive_pdf(
            nome_exibicao=nome_exibicao,
            data_ref=label_periodo,
            faturamento=faturamento_hoje,
            lucro=lucro_hoje,
            ticket_medio=ticket_medio,
            total_vendas=total_vendas,
            df_resumo=df_resumo_pdf,
        )
        st.download_button(
            label="📄 Exportar Relatório PDF",
            data=pdf_bytes,
            file_name=f"relatorio_pet_bi_{hoje_str}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # 4 KPIs Executivos
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Faturamento Hoje</div>
                <div class="kpi-value">{format_brl(faturamento_hoje)}</div>
                <div class="kpi-sub">Período: <strong style="color:#38BDF8;">{label_periodo}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        cor_lucro = "#34D399" if lucro_hoje >= 0 else "#F87171"
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Lucro Líquido</div>
                <div class="kpi-value" style="color:{cor_lucro};">{format_brl(lucro_hoje)}</div>
                <div class="kpi-sub">Margem líquida: <strong>{margem_pct:.1f}%</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Ticket Médio</div>
                <div class="kpi-value">{format_brl(ticket_medio)}</div>
                <div class="kpi-sub">Por pedido convertido</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Total Vendas</div>
                <div class="kpi-value">{total_vendas} un.</div>
                <div class="kpi-sub">Concorrentes: <strong>{vendas_conc} un.</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

    # Gráfico de Área Curva Sobreposta (00h - 23h)
    horas_idx = list(range(24))
    horas_labels = [f"{h:02d}h" for h in horas_idx]

    meus_por_hora = (
        df_meus.groupby("Hora_Int")["Vendas_na_Hora"].sum().reindex(horas_idx, fill_value=0)
        if not df_meus.empty
        else pd.Series(0, index=horas_idx)
    )
    conc_por_hora = (
        df_conc.groupby("Hora_Int")["Vendas_na_Hora"].sum().reindex(horas_idx, fill_value=0)
        if not df_conc.empty
        else pd.Series(0, index=horas_idx)
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=horas_labels,
            y=meus_por_hora.values,
            name="Meu Anúncio",
            mode="lines+markers",
            line=dict(color="#38BDF8", width=3, shape="spline", smoothing=0.85),
            marker=dict(size=6, color="#38BDF8"),
            fill="tozeroy",
            fillcolor="rgba(56, 189, 248, 0.20)",
            hovertemplate="<b>Meu Anúncio</b><br>Hora: %{x}<br>Vendas: %{y} un.<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=horas_labels,
            y=conc_por_hora.values,
            name="Concorrente",
            mode="lines+markers",
            line=dict(color="#F59E0B", width=3, shape="spline", smoothing=0.85),
            marker=dict(size=6, color="#F59E0B"),
            fill="tozeroy",
            fillcolor="rgba(245, 158, 11, 0.16)",
            hovertemplate="<b>Concorrente</b><br>Hora: %{x}<br>Vendas: %{y} un.<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="Batalha de Horário de Pico — Volume de Vendas por Hora (00h–23h)",
            font=dict(size=16, color="#F8FAFC", family="Inter"),
            x=0.01,
        ),
        paper_bgcolor="rgba(15, 23, 42, 0.45)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        font=dict(color="#CBD5E1", family="Inter"),
        xaxis=dict(
            title="Horário (Brasília)",
            gridcolor="rgba(51, 65, 85, 0.45)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Vendas Estimadas (un.)",
            gridcolor="rgba(51, 65, 85, 0.45)",
            zeroline=False,
            rangemode="tozero",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
        margin=dict(l=30, r=20, t=60, b=35),
        height=410,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Resumo operacional
    if not df_kpi.empty:
        pico_meu = horas_labels[int(meus_por_hora.idxmax())] if meus_por_hora.max() > 0 else "—"
        pico_conc = horas_labels[int(conc_por_hora.idxmax())] if conc_por_hora.max() > 0 else "—"
        st.markdown(
            f"""
            <div class="glass-card" style="margin-top:0.5rem;">
                <div style="display:flex; flex-wrap:wrap; justify-content:space-between; gap:1rem; align-items:center;">
                    <div>
                        <span class="badge badge-info">Horário de Pico (Meu Anúncio): {pico_meu}</span>
                        &nbsp;
                        <span class="badge badge-warning">Horário de Pico (Concorrente): {pico_conc}</span>
                    </div>
                    <div style="font-size:0.85rem; color:#94A3B8;">
                        Links ativos configurados: <strong style="color:#F8FAFC;">{len(df_cfg)}</strong>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# ABA 2: COMPARATIVO DIRETO & ALERTAS
# ==============================================================================


def build_comparative_rows(df_hist: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Consolida por Grupo_Produto os dados lado a lado (Meu Anúncio vs Concorrente),
    vendas hoje, horário de pico, status Full/Catálogo e alertas inteligentes.
    """
    if df_hist.empty:
        return []

    hoje_str = get_brasilia_now().strftime("%Y-%m-%d")
    df_sorted = df_hist.sort_values("Data_Hora")

    grupos = sorted(
        [g for g in df_sorted["Grupo_Produto"].dropna().unique().tolist() if str(g).strip()]
    )

    rows: List[Dict[str, Any]] = []
    for grupo in grupos:
        df_g = df_sorted[df_sorted["Grupo_Produto"] == grupo]
        df_meu = df_g[df_g["Tipo_Norm"] == "meu anuncio"]
        df_conc = df_g[df_g["Tipo_Norm"] != "meu anuncio"]

        # Última leitura
        last_meu = df_meu.iloc[-1] if not df_meu.empty else None
        # Para concorrente, pega a última leitura de cada concorrente distinto (por título) ou o principal
        if not df_conc.empty:
            latest_concs = df_conc.groupby("Titulo", as_index=False).tail(1)
            # Seleciona concorrente com menor preço ativo ou o mais recente
            active_concs = latest_concs[latest_concs["Preco"] > 0]
            ref_conc = (
                active_concs.sort_values("Preco").iloc[0]
                if not active_concs.empty
                else latest_concs.iloc[-1]
            )
            conc_estoque_total = int(latest_concs["Estoque_Atual"].sum())
            conc_any_zero = bool((latest_concs["Estoque_Atual"] == 0).any())
        else:
            ref_conc = None
            conc_estoque_total = 0
            conc_any_zero = False

        meu_preco = float(last_meu["Preco"]) if last_meu is not None else 0.0
        conc_preco = float(ref_conc["Preco"]) if ref_conc is not None else 0.0
        meu_estoque = int(last_meu["Estoque_Atual"]) if last_meu is not None else 0

        # Vendas hoje
        df_g_hoje = df_g[df_g["Data_Dia"] == hoje_str]
        if df_g_hoje.empty and not df_g.empty:
            ultimo_dia = df_g["Data_Dia"].max()
            df_g_hoje = df_g[df_g["Data_Dia"] == ultimo_dia]

        vendas_meu = int(
            df_g_hoje[df_g_hoje["Tipo_Norm"] == "meu anuncio"]["Vendas_na_Hora"].sum()
        )
        vendas_conc = int(
            df_g_hoje[df_g_hoje["Tipo_Norm"] != "meu anuncio"]["Vendas_na_Hora"].sum()
        )

        # Horário de pico (geral do grupo ou do meu anúncio)
        pico_series = df_g.groupby("Hora_Int")["Vendas_na_Hora"].sum()
        if not pico_series.empty and pico_series.max() > 0:
            horario_pico = f"{int(pico_series.idxmax()):02d}h"
        else:
            horario_pico = "—"

        meu_full = str(last_meu["Full"]) if last_meu is not None else "—"
        conc_full = str(ref_conc["Full"]) if ref_conc is not None else "—"
        meu_cat = str(last_meu["Catalogo"]) if last_meu is not None else "—"
        conc_cat = str(ref_conc["Catalogo"]) if ref_conc is not None else "—"

        # Alertas inteligentes
        alerts: List[Tuple[str, str]] = []
        if ref_conc is not None and (conc_estoque_total == 0 or conc_any_zero):
            alerts.append(
                ("Concorrente zerou estoque - oportunidade de subir preço", "success")
            )
        if last_meu is not None and meu_estoque == 0:
            alerts.append(("Seu estoque zerou - reposição urgente", "danger"))
        elif last_meu is not None and 0 < meu_estoque <= 5:
            alerts.append((f"Estoque baixo ({meu_estoque} un.)", "warning"))

        if meu_preco > 0 and conc_preco > 0:
            diff_pct = (meu_preco - conc_preco) / conc_preco * 100.0
            if diff_pct > 5.0:
                alerts.append((f"Seu preço +{diff_pct:.1f}% acima do concorrente", "warning"))
            elif diff_pct < -5.0:
                alerts.append((f"Vantagem de preço ({diff_pct:.1f}%)", "info"))

        if normalize_text(conc_full) == "sim" and normalize_text(meu_full) != "sim":
            alerts.append(("Concorrente no FULL e você fora do FULL", "danger"))

        if normalize_text(meu_cat) == "sim" or normalize_text(conc_cat) == "sim":
            alerts.append(("Anúncio em Catálogo", "info"))

        if not alerts:
            alerts.append(("Equilíbrio competitivo", "neutral"))

        rows.append(
            {
                "grupo": grupo,
                "marketplace": str(last_meu["Marketplace"]) if last_meu is not None else (str(ref_conc["Marketplace"]) if ref_conc is not None else "—"),
                "meu_preco": meu_preco,
                "conc_preco": conc_preco,
                "meu_estoque": meu_estoque,
                "conc_estoque": conc_estoque_total,
                "vendas_meu": vendas_meu,
                "vendas_conc": vendas_conc,
                "horario_pico": horario_pico,
                "meu_full": meu_full,
                "conc_full": conc_full,
                "meu_cat": meu_cat,
                "conc_cat": conc_cat,
                "alerts": alerts,
            }
        )

    return rows


def render_comparativo_alertas(df_hist: pd.DataFrame) -> None:
    """Aba 2: Comparativo Direto & Alertas por Grupo_Produto."""
    st.markdown(
        """
        <div class="hero-header">
            <h1 class="hero-title">🎯 Comparativo Direto & Alertas</h1>
            <p class="hero-subtitle">
                Visão lado a lado por Grupo de Produto entre seus anúncios e concorrentes, com alertas automáticos de estoque e preço.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_hist.empty:
        st.info("Sem histórico disponível para comparar. Aguarde a primeira coleta do monitor.")
        return

    comp_rows = build_comparative_rows(df_hist)
    if not comp_rows:
        st.info("Nenhum Grupo_Produto encontrado no histórico do usuário.")
        return

    # Resumo de alertas críticos no topo
    oportunidades = sum(
        1 for r in comp_rows for msg, sev in r["alerts"] if sev == "success"
    )
    criticos = sum(
        1 for r in comp_rows for msg, sev in r["alerts"] if sev == "danger"
    )
    atencao = sum(
        1 for r in comp_rows for msg, sev in r["alerts"] if sev == "warning"
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Oportunidades de Margem</div>
                <div class="kpi-value" style="color:#34D399;">{oportunidades}</div>
                <div class="kpi-sub">Concorrentes sem estoque</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Alertas de Atenção</div>
                <div class="kpi-value" style="color:#FBBF24;">{atencao}</div>
                <div class="kpi-sub">Desvio de preço ou estoque baixo</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Alertas Críticos</div>
                <div class="kpi-value" style="color:#F87171;">{criticos}</div>
                <div class="kpi-sub">Ruptura de estoque ou desvantagem FULL</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.1rem;'></div>", unsafe_allow_html=True)

    # Tabela HTML Glassmorphism
    html_rows: List[str] = []
    for r in comp_rows:
        meu_p_txt = format_brl(r["meu_preco"]) if r["meu_preco"] > 0 else "—"
        conc_p_txt = format_brl(r["conc_preco"]) if r["conc_preco"] > 0 else "—"

        full_meu_badge = (
            '<span class="badge badge-success">Meu: FULL</span>'
            if normalize_text(r["meu_full"]) == "sim"
            else '<span class="badge badge-neutral">Meu: Normal</span>'
        )
        full_conc_badge = (
            '<span class="badge badge-info">Conc: FULL</span>'
            if normalize_text(r["conc_full"]) == "sim"
            else '<span class="badge badge-neutral">Conc: Normal</span>'
        )

        cat_meu_badge = (
            '<span class="badge badge-info">Meu: Catálogo</span>'
            if normalize_text(r["meu_cat"]) == "sim"
            else '<span class="badge badge-neutral">Meu: Clássico</span>'
        )
        cat_conc_badge = (
            '<span class="badge badge-warning">Conc: Catálogo</span>'
            if normalize_text(r["conc_cat"]) == "sim"
            else '<span class="badge badge-neutral">Conc: Clássico</span>'
        )

        alerts_html = "<br/>".join(
            f'<span class="badge badge-{sev}" style="margin:2px 0;">{msg}</span>'
            for msg, sev in r["alerts"]
        )

        html_rows.append(
            f"""
            <tr>
                <td>
                    <strong style="color:#F8FAFC;">{r['grupo']}</strong><br/>
                    <span style="font-size:0.78rem; color:#94A3B8;">{r['marketplace']}</span>
                </td>
                <td>
                    <strong style="color:#38BDF8;">{meu_p_txt}</strong><br/>
                    <span style="font-size:0.77rem; color:#94A3B8;">Est: {r['meu_estoque']} un.</span>
                </td>
                <td>
                    <strong style="color:#F59E0B;">{conc_p_txt}</strong><br/>
                    <span style="font-size:0.77rem; color:#94A3B8;">Est: {r['conc_estoque']} un.</span>
                </td>
                <td>
                    <strong style="color:#34D399;">{r['vendas_meu']} un.</strong>
                    <span style="color:#64748B;">vs</span>
                    <strong style="color:#FBBF24;">{r['vendas_conc']} un.</strong>
                </td>
                <td><span class="badge badge-info">{r['horario_pico']}</span></td>
                <td>{full_meu_badge}<br/><div style="height:4px;"></div>{full_conc_badge}</td>
                <td>{cat_meu_badge}<br/><div style="height:4px;"></div>{cat_conc_badge}</td>
                <td>{alerts_html}</td>
            </tr>
            """
        )

    table_html = f"""
    <div class="exec-table-wrap">
        <table class="exec-table">
            <thead>
                <tr>
                    <th>Grupo do Produto</th>
                    <th>Meu Preço</th>
                    <th>Concorrente</th>
                    <th>Vendas Hoje (Meu vs Conc)</th>
                    <th>Horário Pico</th>
                    <th>Status FULL</th>
                    <th>Catálogo</th>
                    <th>Alertas Inteligentes</th>
                </tr>
            </thead>
            <tbody>
                {"".join(html_rows)}
            </tbody>
        </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


# ==============================================================================
# ABA 3: RADAR NICHO PET (MINERADOR PÚBLICO MERCADO LIVRE)
# ==============================================================================


@st.cache_data(ttl=300, show_spinner=False)
def search_mercadolivre_public(keyword: str, limit: int = 20) -> Tuple[List[Dict[str, Any]], str]:
    """
    Consulta publicamente https://api.mercadolibre.com/sites/MLB/search (sem token)
    com fallback automático para raspagem pública de https://lista.mercadolivre.com.br/.
    """
    query = keyword.strip()
    if not query:
        return [], "Informe uma palavra-chave."

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }

    # Tentativa 1: Endpoint público oficial https://api.mercadolibre.com/sites/MLB/search (sem token)
    try:
        api_url = f"https://api.mercadolibre.com/sites/MLB/search?q={quote_plus(query)}&limit={limit}"
        resp = requests.get(api_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            payload = resp.json()
            results = payload.get("results", [])[:limit]
            if results:
                items: List[Dict[str, Any]] = []
                for idx, item in enumerate(results, start=1):
                    shipping = item.get("shipping") or {}
                    is_full = shipping.get("logistic_type") == "fulfillment"
                    is_catalog = bool(item.get("catalog_listing") or item.get("catalog_product_id"))
                    items.append(
                        {
                            "Posicao": idx,
                            "Titulo": str(item.get("title", "")).strip(),
                            "Preco": round(parse_number(item.get("price"), 0.0), 2),
                            "Full": "Sim" if is_full else "Não",
                            "Catalogo": "Sim" if is_catalog else "Não",
                            "Vendedor": str((item.get("seller") or {}).get("nickname", "—")),
                            "Link": str(item.get("permalink", "")),
                        }
                    )
                return items, "Fonte pública: MercadoLibre Search API"
    except Exception:
        pass

    # Tentativa 2: Raspagem pública da página de resultados lista.mercadolivre.com.br
    try:
        slug = re.sub(r"\s+", "-", query.lower())
        web_url = f"https://lista.mercadolivre.com.br/{quote_plus(slug).replace('%2B', '-')}"
        resp = requests.get(web_url, headers=headers, timeout=18)
        if resp.status_code == 200 and resp.text:
            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select("li.ui-search-layout__item, div.ui-search-result__wrapper")
            items = []
            for card in cards:
                if len(items) >= limit:
                    break
                title_el = card.select_one(
                    "a.poly-component__title, h2.ui-search-item__title, a.ui-search-link"
                )
                title = title_el.get_text(" ", strip=True) if title_el else ""
                link = str(title_el.get("href", "")) if title_el else ""
                if not title:
                    continue

                price_box = card.select_one(".poly-price__current .andes-money-amount") or card.select_one(
                    ".ui-search-price__second-line .andes-money-amount"
                )
                price = 0.0
                if price_box:
                    frac = price_box.select_one(".andes-money-amount__fraction")
                    cents = price_box.select_one(".andes-money-amount__cents")
                    f_txt = frac.get_text(strip=True) if frac else ""
                    c_txt = cents.get_text(strip=True) if cents else "00"
                    if f_txt:
                        price = parse_number(f"{f_txt},{c_txt}", 0.0)

                card_html = str(card).lower()
                is_full = "fulfillment" in card_html or "poly-component__shipped-from" in card_html or "full" in normalize_text(card.get_text(" ", strip=True))
                is_catalog = "/p/mlb" in link.lower()

                items.append(
                    {
                        "Posicao": len(items) + 1,
                        "Titulo": title,
                        "Preco": round(price, 2),
                        "Full": "Sim" if is_full else "Não",
                        "Catalogo": "Sim" if is_catalog else "Não",
                        "Vendedor": "Público ML",
                        "Link": link,
                    }
                )
            if items:
                return items, "Fonte pública: lista.mercadolivre.com.br"
    except Exception as exc:
        return [], f"Falha na consulta pública: {exc}"

    return [], "Não foi possível obter resultados públicos no momento. Tente outra palavra-chave."


def render_radar_nicho_pet() -> None:
    """Aba 3: Radar Nicho Pet (Minerador) com busca pública e dispersão Plotly."""
    st.markdown(
        """
        <div class="hero-header">
            <h1 class="hero-title">🔎 Radar Nicho Pet (Minerador)</h1>
            <p class="hero-subtitle">
                Pesquise palavras-chave do nicho Pet publicamente no Mercado Livre para mapear ticket médio, penetração FULL e Catálogo nos Top 20 anúncios.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("radar_search_form"):
        s1, s2 = st.columns([3.5, 1.0])
        keyword = s1.text_input(
            "Palavra-chave do Produto Pet",
            value=st.session_state.get("radar_last_kw", "tapete higienico cachorro"),
            placeholder="ex: racao golden gato castrado 10kg",
        )
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        buscar = s2.form_submit_button("🔍 Minerar Top 20", type="primary", use_container_width=True)

    if buscar and keyword.strip():
        st.session_state["radar_last_kw"] = keyword.strip()

    active_kw = st.session_state.get("radar_last_kw", "")
    if not active_kw:
        st.info("Digite uma palavra-chave acima e clique em Minerar Top 20.")
        return

    with st.spinner(f"Minerando publicamente '{active_kw}'..."):
        items, source_msg = search_mercadolivre_public(active_kw, limit=20)

    if not items:
        st.warning(source_msg)
        return

    df_radar = pd.DataFrame(items)
    valid_prices = df_radar[df_radar["Preco"] > 0]["Preco"]
    ticket_medio = float(valid_prices.mean()) if not valid_prices.empty else 0.0
    pct_full = float((df_radar["Full"] == "Sim").mean() * 100.0)
    pct_cat = float((df_radar["Catalogo"] == "Sim").mean() * 100.0)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Ticket Médio (Top 20)</div>
                <div class="kpi-value">{format_brl(ticket_medio)}</div>
                <div class="kpi-sub">Faixa: {format_brl(float(valid_prices.min()) if not valid_prices.empty else 0)} – {format_brl(float(valid_prices.max()) if not valid_prices.empty else 0)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">% Anúncios FULL</div>
                <div class="kpi-value" style="color:#34D399;">{pct_full:.1f}%</div>
                <div class="kpi-sub">Logística Fulfillment</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">% em Catálogo</div>
                <div class="kpi-value" style="color:#38BDF8;">{pct_cat:.1f}%</div>
                <div class="kpi-sub">Competição por Buybox</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Anúncios Coletados</div>
                <div class="kpi-value">{len(df_radar)}</div>
                <div class="kpi-sub">{source_msg}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Gráfico de Dispersão Plotly (Posição no Ranking x Preço)
    fig_scatter = go.Figure()
    for full_status, color in [("Sim", "#34D399"), ("Não", "#38BDF8")]:
        sub = df_radar[df_radar["Full"] == full_status]
        if sub.empty:
            continue
        symbols = ["diamond" if c == "Sim" else "circle" for c in sub["Catalogo"]]
        fig_scatter.add_trace(
            go.Scatter(
                x=sub["Posicao"],
                y=sub["Preco"],
                mode="markers",
                name=f"FULL: {full_status}",
                marker=dict(
                    size=13,
                    color=color,
                    symbol=symbols,
                    line=dict(width=1.5, color="#0B0F19"),
                ),
                text=sub["Titulo"],
                customdata=sub["Catalogo"],
                hovertemplate=(
                    "<b>#%{x} — %{text}</b><br>"
                    "Preço: R$ %{y:.2f}<br>"
                    f"FULL: {full_status} | Catálogo: %{{customdata}}<extra></extra>"
                ),
            )
        )

    fig_scatter.add_hline(
        y=ticket_medio,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text=f"Ticket Médio: {format_brl(ticket_medio)}",
        annotation_font_color="#FBBF24",
    )

    fig_scatter.update_layout(
        title=dict(
            text="Dispersão de Preços vs. Posição no Ranking Orgânico (Diamante = Catálogo)",
            font=dict(size=15, color="#F8FAFC", family="Inter"),
        ),
        paper_bgcolor="rgba(15, 23, 42, 0.45)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        font=dict(color="#CBD5E1", family="Inter"),
        xaxis=dict(
            title="Posição no Ranking (Top 20)",
            dtick=1,
            gridcolor="rgba(51, 65, 85, 0.45)",
        ),
        yaxis=dict(
            title="Preço (R$)",
            gridcolor="rgba(51, 65, 85, 0.45)",
        ),
        legend=dict(orientation="h", y=1.06, x=1, xanchor="right"),
        height=390,
        margin=dict(l=30, r=20, t=65, b=35),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.subheader("Top 20 Anúncios Minerados")
    st.dataframe(
        df_radar,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Posicao": st.column_config.NumberColumn("#", width="small"),
            "Preco": st.column_config.NumberColumn("Preço (R$)", format="R$ %.2f"),
            "Link": st.column_config.LinkColumn("Abrir Anúncio", display_text="Ver anúncio"),
        },
    )


# ==============================================================================
# ABA 4: CALCULADORA DE PRECIFICAÇÃO 2026 (PRÉ-SELECIONADA E EDITÁVEL)
# ==============================================================================


def compute_platform_defaults_2026(
    plataforma: str, preco_venda: float
) -> Tuple[float, float, str]:
    """
    Retorna (comissao_pct, taxa_fixa, marketplace_normalizado) para 2026:
    - Mercado Livre Clássico (12%)
    - Mercado Livre Premium (17%)
    - Shopee CNPJ: 20% até R$79,99 + R$4,50; 14% >= R$80 + R$16 / R$20 / R$26
    - Shopee CPF: mesma regra CNPJ + R$3,00 na taxa fixa
    - Magalu: 18% + R$5,00
    """
    if plataforma == "Mercado Livre Clássico (12%)":
        taxa_fixa = 6.00 if 0 < preco_venda < 79.00 else 0.00
        return 12.0, taxa_fixa, "Mercado Livre"

    if plataforma == "Mercado Livre Premium (17%)":
        taxa_fixa = 6.00 if 0 < preco_venda < 79.00 else 0.00
        return 17.0, taxa_fixa, "Mercado Livre"

    if plataforma in ("Shopee CNPJ", "Shopee CPF"):
        extra_cpf = 3.00 if plataforma == "Shopee CPF" else 0.00
        if preco_venda <= 79.99:
            return 20.0, round(4.50 + extra_cpf, 2), "Shopee"
        # Faixas >= R$ 80,00: R$16 (80-99,99), R$20 (100-199,99), R$26 (>=200)
        if preco_venda < 100.00:
            base_fixa = 16.00
        elif preco_venda < 200.00:
            base_fixa = 20.00
        else:
            base_fixa = 26.00
        return 14.0, round(base_fixa + extra_cpf, 2), "Shopee"

    if plataforma == "Magalu":
        return 18.0, 5.00, "Magalu"

    return 12.0, 0.00, "Outro"


def _shopee_tier_key(preco: float) -> str:
    """Identifica a faixa de preço da Shopee para atualizar padrões apenas quando mudar de faixa."""
    if preco <= 79.99:
        return "tier_le_79"
    if preco < 100.00:
        return "tier_80_99"
    if preco < 200.00:
        return "tier_100_199"
    return "tier_ge_200"


def calculate_pricing_breakdown(
    preco_venda: float,
    meu_custo: float,
    imposto_pct: float,
    comissao_pct: float,
    taxa_fixa: float,
    frete_estimado: float,
) -> Dict[str, float]:
    """Calcula detalhamento financeiro completo de precificação."""
    comissao_rs = preco_venda * (comissao_pct / 100.0)
    imposto_rs = preco_venda * (imposto_pct / 100.0)
    descontos_totais = meu_custo + imposto_rs + comissao_rs + taxa_fixa + frete_estimado
    lucro_liquido = preco_venda - descontos_totais
    margem_pct = (lucro_liquido / preco_venda * 100.0) if preco_venda > 0 else 0.0
    roi_pct = (lucro_liquido / meu_custo * 100.0) if meu_custo > 0 else 0.0

    denom = 1.0 - (imposto_pct + comissao_pct) / 100.0
    if denom > 0:
        preco_equilibrio = (meu_custo + taxa_fixa + frete_estimado) / denom
    else:
        preco_equilibrio = 0.0

    return {
        "comissao_rs": round(comissao_rs, 2),
        "imposto_rs": round(imposto_rs, 2),
        "lucro_liquido": round(lucro_liquido, 2),
        "margem_pct": round(margem_pct, 2),
        "roi_pct": round(roi_pct, 2),
        "preco_equilibrio": round(preco_equilibrio, 2),
    }


def render_calculadora_precificacao(usuario: str) -> None:
    """Aba 4: Calculadora de Precificação 2026 com Gauge Chart Plotly e salvamento."""
    st.markdown(
        """
        <div class="hero-header">
            <h1 class="hero-title">🧮 Calculadora de Precificação 2026</h1>
            <p class="hero-subtitle">
                Taxas pré-preenchidas por plataforma e faixa de preço (100% editáveis), velocímetro de margem líquida e gravação direta em Configuracao.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_inputs, col_gauge = st.columns([1.25, 1.0], gap="large")

    with col_inputs:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        p1, p2 = st.columns([1.3, 1.0])
        plataforma = p1.selectbox(
            "Plataforma / Modalidade 2026",
            PLATAFORMAS_2026,
            key="calc_plataforma",
        )
        preco_venda = p2.number_input(
            "Preço de Venda (R$)",
            min_value=0.0,
            value=89.90,
            step=1.0,
            key="calc_preco_venda",
        )

        # Sincronização inteligente: pré-preenche automaticamente quando plataforma ou faixa muda, mantendo editável
        tier_sig = (
            f"{plataforma}|{_shopee_tier_key(preco_venda)}|{preco_venda < 79.0}"
        )
        if st.session_state.get("calc_last_sig") != tier_sig:
            def_com, def_taxa, _ = compute_platform_defaults_2026(
                plataforma, preco_venda
            )
            st.session_state["calc_comissao_pct"] = def_com
            st.session_state["calc_taxa_fixa"] = def_taxa
            st.session_state["calc_last_sig"] = tier_sig

        c1, c2, c3 = st.columns(3)
        meu_custo = c1.number_input(
            "Meu Custo (R$)",
            min_value=0.0,
            value=32.00,
            step=1.0,
            key="calc_meu_custo",
        )
        imposto_pct = c2.number_input(
            "Imposto (%)",
            min_value=0.0,
            max_value=100.0,
            value=6.0,
            step=0.5,
            key="calc_imposto_pct",
        )
        frete_estimado = c3.number_input(
            "Frete Estimado (R$)",
            min_value=0.0,
            value=14.90,
            step=0.5,
            key="calc_frete_estimado",
        )

        e1, e2, e3 = st.columns([1.0, 1.0, 0.9])
        comissao_pct = e1.number_input(
            "Comissão (%) — Editável",
            min_value=0.0,
            max_value=100.0,
            step=0.5,
            key="calc_comissao_pct",
        )
        taxa_fixa = e2.number_input(
            "Taxa Fixa (R$) — Editável",
            min_value=0.0,
            step=0.5,
            key="calc_taxa_fixa",
        )
        with e3:
            st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
            if st.button("↺ Restaurar Padrão", use_container_width=True):
                def_com, def_taxa, _ = compute_platform_defaults_2026(
                    plataforma, preco_venda
                )
                st.session_state["calc_comissao_pct"] = def_com
                st.session_state["calc_taxa_fixa"] = def_taxa
                st.rerun()

        if plataforma == "Shopee CNPJ":
            st.caption(
                "Regra Shopee CNPJ 2026 aplicada: 20% + R$ 4,50 até R$ 79,99 | "
                "14% + R$ 16,00 (R$80–99,99), R$ 20,00 (R$100–199,99) ou R$ 26,00 (>= R$200)."
            )
        elif plataforma == "Shopee CPF":
            st.caption(
                "Regra Shopee CPF 2026 aplicada: mesmas faixas do CNPJ acrescidas de +R$ 3,00 na taxa fixa."
            )
        elif plataforma == "Magalu":
            st.caption("Regra Magalu 2026 aplicada: 18% de comissão + R$ 5,00 de taxa fixa.")
        else:
            st.caption(
                "Regra Mercado Livre aplicada: comissão pré-selecionada e taxa fixa editável."
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # Formulário para salvar direto na aba Configuracao
        st.markdown("<div style='height: 0.9rem;'></div>", unsafe_allow_html=True)
        with st.form("save_calc_config_form"):
            st.markdown("#### 💾 Enviar Precificação para Monitoramento (`Configuracao`)")
            s1, s2 = st.columns([1.1, 1.6])
            grupo_calc = s1.text_input(
                "Grupo do Produto",
                placeholder="ex: Ração Golden Gatos 10kg",
            )
            url_calc = s2.text_input(
                "URL do Meu Anúncio",
                placeholder="https://produto.mercadolivre.com.br/MLB-...",
            )
            save_btn = st.form_submit_button(
                "Salvar na aba Configuracao", type="primary", use_container_width=True
            )

            if save_btn:
                if not grupo_calc.strip():
                    st.warning("Informe o Grupo do Produto para salvar.")
                elif not url_calc.strip().startswith(("http://", "https://")):
                    st.warning("Informe uma URL válida começando com http:// ou https://.")
                else:
                    _, _, mkt_name = compute_platform_defaults_2026(
                        plataforma, preco_venda
                    )
                    row_to_save = [
                        usuario,
                        "Meu Anuncio",
                        grupo_calc.strip(),
                        mkt_name,
                        url_calc.strip(),
                        round(float(meu_custo), 2),
                        round(float(imposto_pct), 2),
                        round(float(comissao_pct), 2),
                        round(float(taxa_fixa), 2),
                        round(float(frete_estimado), 2),
                    ]
                    with st.spinner("Gravando em Configuracao..."):
                        ok, msg = append_config_row_to_sheets(row_to_save)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    res = calculate_pricing_breakdown(
        preco_venda=preco_venda,
        meu_custo=meu_custo,
        imposto_pct=imposto_pct,
        comissao_pct=comissao_pct,
        taxa_fixa=taxa_fixa,
        frete_estimado=frete_estimado,
    )

    with col_gauge:
        margem = res["margem_pct"]
        lucro = res["lucro_liquido"]
        gauge_color = (
            "#34D399" if margem >= 20 else ("#FBBF24" if margem >= 10 else "#F87171")
        )

        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=margem,
                number={"suffix": "%", "font": {"size": 38, "color": "#F8FAFC"}},
                delta={"reference": 15.0, "suffix": "% meta", "font": {"size": 14}},
                title={
                    "text": "Margem Líquida Estimada",
                    "font": {"size": 16, "color": "#CBD5E1"},
                },
                gauge={
                    "axis": {"range": [-20, 50], "tickcolor": "#94A3B8"},
                    "bar": {"color": gauge_color, "thickness": 0.32},
                    "bgcolor": "rgba(15, 23, 42, 0.8)",
                    "borderwidth": 1,
                    "bordercolor": "#334155",
                    "steps": [
                        {"range": [-20, 10], "color": "rgba(239, 68, 68, 0.22)"},
                        {"range": [10, 20], "color": "rgba(245, 158, 11, 0.22)"},
                        {"range": [20, 50], "color": "rgba(16, 185, 129, 0.22)"},
                    ],
                    "threshold": {
                        "line": {"color": "#38BDF8", "width": 3},
                        "thickness": 0.78,
                        "value": 15,
                    },
                },
            )
        )
        fig_gauge.update_layout(
            paper_bgcolor="rgba(30, 41, 59, 0.50)",
            font={"color": "#E2E8F0", "family": "Inter"},
            height=305,
            margin=dict(l=24, r=24, t=55, b=16),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        cor_lucro_card = "#34D399" if lucro >= 0 else "#F87171"
        st.markdown(
            f"""
            <div class="glass-card">
                <div style="display:flex; justify-content:space-between; margin-bottom:0.65rem;">
                    <span style="color:#94A3B8;">Lucro Líquido por Unidade</span>
                    <strong style="color:{cor_lucro_card}; font-size:1.25rem;">{format_brl(lucro)}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:0.45rem; font-size:0.88rem;">
                    <span style="color:#94A3B8;">Comissão ({comissao_pct:.1f}%)</span>
                    <span>-{format_brl(res['comissao_rs'])}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:0.45rem; font-size:0.88rem;">
                    <span style="color:#94A3B8;">Taxa Fixa</span>
                    <span>-{format_brl(taxa_fixa)}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:0.45rem; font-size:0.88rem;">
                    <span style="color:#94A3B8;">Imposto ({imposto_pct:.1f}%)</span>
                    <span>-{format_brl(res['imposto_rs'])}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:0.45rem; font-size:0.88rem;">
                    <span style="color:#94A3B8;">Custo + Frete</span>
                    <span>-{format_brl(meu_custo + frete_estimado)}</span>
                </div>
                <hr style="border-color:#334155; margin:0.65rem 0;"/>
                <div style="display:flex; justify-content:space-between; font-size:0.88rem;">
                    <span style="color:#94A3B8;">ROI sobre Custo / Break-even</span>
                    <strong style="color:#38BDF8;">{res['roi_pct']:.1f}% | {format_brl(res['preco_equilibrio'])}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# ABAS 5 E 6: FÁBRICA DE ANÚNCIOS (IA) E RESGATE DE ANÚNCIO (IA)
# ==============================================================================


def _truncate_seo_title(title: str, max_len: int = 60) -> str:
    """Garante limite estrito de até 60 caracteres sem cortar palavra ao meio quando possível."""
    clean = re.sub(r"\s+", " ", str(title)).strip()
    if len(clean) <= max_len:
        return clean
    clipped = clean[:max_len].rstrip()
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0].rstrip()
    return clipped[:max_len]


def render_fabrica_anuncios() -> None:
    """Aba 5: Fábrica de Anúncios (Metodologia 6 Passos com SEO Real e Gemini 2.5 Flash)."""
    st.markdown(
        """
        <div class="hero-header">
            <h1 class="hero-title">🏭 Fábrica de Anúncios — Metodologia 6 Passos (SEO Real)</h1>
            <p class="hero-subtitle">
                Extração real de palavras-chave dos líderes no Mercado Livre + inteligência Gemini 2.5 Flash para criar anúncios campeões prontos para copiar e colar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    usuario = str(st.session_state.get("usuario", ""))

    with st.form("fabrica_anuncios_form"):
        r1c1, r1c2, r1c3 = st.columns([1.6, 1.0, 1.0])
        produto = r1c1.text_input(
            "Produto *",
            placeholder="ex: Tapete Higiênico Super Absorvente 30 Unidades",
        )
        marca = r1c2.text_input("Marca", placeholder="ex: PetPrime")
        faixa_preco = r1c3.text_input("Faixa de Preço", placeholder="ex: R$ 74,90 a R$ 89,90")

        r2c1, r2c2, r2c3, r2c4 = st.columns([0.8, 1.2, 0.9, 1.3])
        custo = r2c1.number_input("Custo (R$)", min_value=0.0, value=32.0, step=1.0)
        publico_alvo = r2c2.text_input(
            "Público-Alvo",
            placeholder="ex: Tutores de cães de porte pequeno/médio em apartamento",
        )
        tom = r2c3.selectbox("Tom de Comunicação", ["Casual", "Profissional"])
        garantias_brindes = r2c4.text_input(
            "Garantias / Brindes",
            placeholder="ex: Garantia 30 dias + Envio Imediato + Nota Fiscal",
        )

        ficha_tecnica = st.text_area(
            "Ficha Técnica *",
            height=110,
            placeholder=(
                "Ex: Medidas 80x60cm, 6 camadas com gel absorvente, fita adesiva nas 4 pontas, "
                "atrativo canino, barreira antivazamento, pacote com 30 unidades..."
            ),
        )

        link_concorrente = st.text_input(
            "Link do Anúncio Concorrente (Opcional — para Placar de Batalha 0 a 10)",
            placeholder="https://produto.mercadolivre.com.br/MLB-...",
        )

        gerar_btn = st.form_submit_button(
            "🚀 Gerar Anúncio Campeão", type="primary", use_container_width=True
        )

    if gerar_btn:
        if not produto.strip() or not ficha_tecnica.strip():
            st.warning("Preencha pelo menos os campos Produto e Ficha Técnica.")
        else:
            dynamic_messages = [
                "Aprimorando seu anúncio...",
                "Buscando palavras-chave reais pesquisadas pelos compradores...",
                "Quebrando objeções do cliente desconfiado...",
                "Vamos fazer esse anúncio acabar com a concorrência!",
            ]
            progress_bar = st.progress(0)
            status_box = st.empty()

            # Etapa 1 (2s): Mensagem inicial + consulta SEO real no Mercado Livre
            status_box.info(f"⏳ {dynamic_messages[0]}")
            progress_bar.progress(15)
            time.sleep(2)

            status_box.info(f"🔎 {dynamic_messages[1]}")
            progress_bar.progress(38)
            radar_items, radar_source = search_mercadolivre_public(produto.strip(), limit=20)
            leader_titles = [item["Titulo"] for item in radar_items if item.get("Titulo")]
            real_keywords = extract_real_seo_keywords(leader_titles, top_n=20)
            time.sleep(2)

            # Etapa 3 (2s): Raspagem opcional do concorrente + preparação de quebra de objeções
            status_box.info(f"🛡️ {dynamic_messages[2]}")
            progress_bar.progress(62)
            competitor_data = (
                scrape_competitor_listing_for_ai(link_concorrente.strip())
                if link_concorrente.strip()
                else None
            )
            time.sleep(2)

            # Etapa 4 (2s): Chamada ao Gemini 2.5 Flash
            status_box.info(f"🔥 {dynamic_messages[3]}")
            progress_bar.progress(82)
            time.sleep(2)

            keywords_summary = (
                ", ".join(f"{kw} ({freq}x)" for kw, freq in real_keywords)
                if real_keywords
                else "Sem resultados públicos capturados; use apenas os termos literais do produto informado."
            )
            titles_sample_txt = (
                "\n".join(f"- {t}" for t in leader_titles[:15])
                if leader_titles
                else "Nenhum título coletado."
            )

            competitor_block = (
                json.dumps(competitor_data, ensure_ascii=False, indent=2)
                if competitor_data
                else "Nenhum link de concorrente informado."
            )

            prompt = f"""
Você é um copywriter sênior e estrategista de SEO especialista em marketplaces brasileiros no nicho Pet.
Gere uma estratégia COMPLETA seguindo exatamente a Metodologia de 6 Passos abaixo.

DADOS DO PRODUTO DO CLIENTE:
- Produto: {produto.strip()}
- Marca: {marca.strip() or 'Não informada'}
- Faixa de Preço: {faixa_preco.strip() or 'Não informada'}
- Custo Unitário: R$ {custo:.2f}
- Público-Alvo: {publico_alvo.strip() or 'Tutores de pets em geral'}
- Tom de Comunicação: {tom}
- Garantias / Brindes: {garantias_brindes.strip() or 'Garantia padrão de plataforma'}
- Ficha Técnica: {ficha_tecnica.strip()}

PALAVRAS-CHAVE REAIS EXTRAÍDAS DOS TÍTULOS LÍDERES NO MERCADO LIVRE (PROIBIDO INVENTAR PALAVRAS-CHAVE FORA DESSES TERMOS REAIS E DA FICHA TÉCNICA):
{keywords_summary}

AMOSTRA DE TÍTULOS REAIS DOS LÍDERES DE BUSCA:
{titles_sample_txt}

ANÚNCIO CONCORRENTE COLETADO (se houver):
{competitor_block}

REGRAS OBRIGATÓRIAS DE SAÍDA (RESPONDA ESTRITAMENTE EM JSON VÁLIDO):
1. "objecoes_15": lista com EXATAMENTE 15 objetos {{"pergunta": "...", "resposta_conversao": "..."}} representando as 15 dúvidas/objeções reais que travam a compra.
2. "top_5_objecoes": lista com EXATAMENTE 5 strings indicando as 5 objeções que mais aumentam conversão ao serem quebradas.
3. "beneficios_tabela": lista com 6 a 8 objetos {{"caracteristica": "...", "beneficio_real": "..."}} respondendo "e daí, o que ganho com isso?".
4. "beneficios_3_frases": lista com EXATAMENTE 3 strings com frases prontas de alto impacto.
5. "beneficio_destaque": string única com o destaque principal do produto.
6. "titulos_seo": lista com EXATAMENTE 10 objetos {{"opcao": 1..10, "titulo": "...", "caracteres": int}} onde TODOS os títulos têm NO MÁXIMO 60 caracteres e COMEÇAM pela palavra-chave de maior busca real identificada nos títulos líderes.
7. "top_3_titulos_explicados": lista com EXATAMENTE 3 objetos {{"titulo": "...", "por_que_funciona": "..."}}.
8. "descricao_pronta": string única pronta para copiar e colar no marketplace contendo obrigatoriamente:
   - Abertura de 2 linhas que prende a atenção;
   - Benefícios escaneáveis (sem negrito excessivo e sem emojis exagerados, usando hífens ou listas limpas);
   - Quebra das 3 principais objeções;
   - Chamada clara para compra;
   - FAQ respondendo as 5 perguntas principais.
9. "comparativo_honesto": lista com 5 a 6 objetos {{"criterio": "...", "meu_produto": "...", "outras_opcoes": "..."}} (PROIBIDO citar nomes de concorrentes).
10. "comparativo_frase_fechamento": string com a frase de fechamento do comparativo.
11. "plano_teste_ab": lista com EXATAMENTE 4 objetos {{"ordem": 1..4, "variacao_isolada": "Título"|"Abertura"|"Foto Principal"|"Ângulo de Venda", "o_que_testar": "...", "metrica_observar": "...", "dias_teste": int}}.
12. "placar_batalha": objeto {{"nota_novo_anuncio": float (0 a 10), "nota_concorrente": float (0 a 10), "veredito": "...", "vantagens_novo": ["...", "...", "..."]}} (preencha mesmo se não houver concorrente, atribuindo 0.0 à nota do concorrente nesse caso).
"""

            try:
                client = get_gemini_client()
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        system_instruction=(
                            "Retorne apenas JSON válido em português do Brasil, completo e fiel às regras de SEO real."
                        ),
                    ),
                )
                parsed = parse_gemini_json(response.text or "")

                # Garante estritamente <= 60 caracteres e recalcula contagem real em Python
                raw_titles = parsed.get("titulos_seo", [])
                clean_titles = []
                for idx, item in enumerate(raw_titles[:10], start=1):
                    t_str = _truncate_seo_title(
                        item.get("titulo", "") if isinstance(item, dict) else str(item), 60
                    )
                    clean_titles.append(
                        {
                            "Nº": idx,
                            "Título SEO": t_str,
                            "Caracteres": len(t_str),
                        }
                    )
                parsed["titulos_seo_limpos"] = clean_titles

                st.session_state["fabrica_result"] = {
                    "produto": produto.strip(),
                    "data": parsed,
                    "real_keywords": real_keywords,
                    "radar_source": radar_source,
                    "competitor_data": competitor_data,
                    "has_competitor": bool(link_concorrente.strip()),
                }
                progress_bar.progress(100)
                status_box.success("✅ Anúncio campeão gerado com sucesso!")
            except Exception as exc:
                progress_bar.empty()
                status_box.error(f"Erro ao gerar anúncio com Gemini 2.5 Flash: {exc}")

    # Renderização persistida dos resultados
    result_state = st.session_state.get("fabrica_result")
    if not result_state:
        return

    data = result_state["data"]
    real_keywords = result_state.get("real_keywords", [])
    competitor_data = result_state.get("competitor_data")
    has_competitor = result_state.get("has_competitor", False)

    if real_keywords:
        with st.expander("🔑 Termos Reais Extraídos dos Líderes no Mercado Livre", expanded=False):
            badges_kw = " ".join(
                f'<span class="badge badge-info" style="margin:3px;">{kw} ({freq}x)</span>'
                for kw, freq in real_keywords
            )
            st.markdown(badges_kw, unsafe_allow_html=True)

    # Placar de Batalha quando houve link de concorrente
    if has_competitor:
        placar = data.get("placar_batalha", {})
        nota_novo = parse_number(placar.get("nota_novo_anuncio"), 9.2)
        nota_conc = parse_number(placar.get("nota_concorrente"), 6.8)
        veredito = str(placar.get("veredito", "Novo anúncio superior em SEO e quebra de objeções."))
        vantagens = placar.get("vantagens_novo", [])
        vantagens_html = "".join(
            f"<li style='margin-bottom:4px;'>{v}</li>" for v in vantagens[:4]
        )
        conc_title_ref = (
            competitor_data.get("titulo", "Concorrente analisado")
            if competitor_data
            else "Link concorrente informado"
        )
        conc_price_ref = (
            format_brl(float(competitor_data.get("preco", 0.0)))
            if competitor_data and competitor_data.get("preco", 0) > 0
            else "—"
        )

        st.markdown(
            f"""
            <div class="glass-card" style="margin: 1rem 0; border-color: rgba(56, 189, 248, 0.55);">
                <div style="display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:1rem;">
                    <div>
                        <div class="kpi-label">⚔️ Placar de Batalha (0 a 10)</div>
                        <div style="font-size:1.05rem; font-weight:700; color:#F8FAFC;">
                            Seu Novo Anúncio vs. Concorrente ({conc_price_ref})
                        </div>
                        <div style="font-size:0.82rem; color:#94A3B8; margin-top:0.2rem;">
                            Ref. Concorrente: {conc_title_ref[:90]}
                        </div>
                    </div>
                    <div style="display:flex; gap:1.2rem; align-items:center;">
                        <div style="text-align:center;">
                            <div style="font-size:0.72rem; color:#94A3B8; text-transform:uppercase;">Novo Anúncio</div>
                            <div style="font-size:2rem; font-weight:800; color:#34D399;">{nota_novo:.1f}/10</div>
                        </div>
                        <div style="font-size:1.2rem; color:#64748B; font-weight:700;">VS</div>
                        <div style="text-align:center;">
                            <div style="font-size:0.72rem; color:#94A3B8; text-transform:uppercase;">Concorrente</div>
                            <div style="font-size:2rem; font-weight:800; color:#F59E0B;">{nota_conc:.1f}/10</div>
                        </div>
                    </div>
                </div>
                <p style="margin:0.8rem 0 0.4rem 0; color:#E2E8F0; font-size:0.9rem;">{veredito}</p>
                <ul style="margin:0.3rem 0 0 1.1rem; color:#CBD5E1; font-size:0.86rem;">{vantagens_html}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Abas internas dos 6 passos
    t1, t2, t3, t4, t5, t6 = st.tabs(
        [
            "1️⃣ Objeções",
            "2️⃣ Benefícios Reais",
            "3️⃣ Títulos SEO (≤60)",
            "4️⃣ Descrição Pronta",
            "5️⃣ Comparativo Honesto",
            "6️⃣ Teste A/B",
        ]
    )

    with t1:
        obj_list = data.get("objecoes_15", [])
        if obj_list:
            df_obj = pd.DataFrame(obj_list)
            st.dataframe(df_obj, use_container_width=True, hide_index=True)
        top5 = data.get("top_5_objecoes", [])
        if top5:
            st.markdown("**Top 5 Objeções que Mais Aumentam Conversão:**")
            top5_text = "\n".join(f"{i}. {q}" for i, q in enumerate(top5, start=1))
            st.code(top5_text, language="text")

    with t2:
        ben_list = data.get("beneficios_tabela", [])
        if ben_list:
            st.dataframe(pd.DataFrame(ben_list), use_container_width=True, hide_index=True)
        destaque = str(data.get("beneficio_destaque", ""))
        frases_3 = data.get("beneficios_3_frases", [])
        bloco_ben = f"DESTAQUE PRINCIPAL:\n{destaque}\n\n3 FRASES PRONTAS:\n" + "\n".join(
            f"- {f}" for f in frases_3
        )
        st.code(bloco_ben, language="text")

    with t3:
        titles_clean = data.get("titulos_seo_limpos", [])
        if titles_clean:
            st.dataframe(pd.DataFrame(titles_clean), use_container_width=True, hide_index=True)
            titles_copy = "\n".join(
                f"{row['Nº']}. {row['Título SEO']} ({row['Caracteres']} chars)"
                for row in titles_clean
            )
            st.code(titles_copy, language="text")
        top3_exp = data.get("top_3_titulos_explicados", [])
        if top3_exp:
            st.markdown("**Top 3 Títulos Explicados:**")
            for idx, item in enumerate(top3_exp[:3], start=1):
                st.markdown(
                    f"- **{idx}. {_truncate_seo_title(item.get('titulo', ''), 60)}** — {item.get('por_que_funciona', '')}"
                )

    with t4:
        desc_pronta = str(data.get("descricao_pronta", ""))
        st.markdown("Copie e cole a descrição estruturada abaixo diretamente no seu anúncio:")
        st.code(desc_pronta, language="text")

    with t5:
        comp_list = data.get("comparativo_honesto", [])
        if comp_list:
            st.dataframe(pd.DataFrame(comp_list), use_container_width=True, hide_index=True)
        fechamento = str(data.get("comparativo_frase_fechamento", ""))
        comp_copy_lines = [
            f"{r.get('criterio', '')} | Meu Produto: {r.get('meu_produto', '')} | Outras Opções: {r.get('outras_opcoes', '')}"
            for r in comp_list
        ]
        comp_copy_lines.append(f"\nFechamento: {fechamento}")
        st.code("\n".join(comp_copy_lines), language="text")

    with t6:
        ab_list = data.get("plano_teste_ab", [])
        if ab_list:
            st.dataframe(pd.DataFrame(ab_list), use_container_width=True, hide_index=True)
            ab_copy = "\n".join(
                f"Ordem {r.get('ordem', i)} | {r.get('variacao_isolada', '')} ({r.get('dias_teste', 7)} dias): "
                f"{r.get('o_que_testar', '')} -> Métrica: {r.get('metrica_observar', '')}"
                for i, r in enumerate(ab_list, start=1)
            )
            st.code(ab_copy, language="text")

    # Salvar na aba Anuncios_Salvos do Google Sheets
    st.markdown("<div style='height: 0.9rem;'></div>", unsafe_allow_html=True)
    titles_options = [row["Título SEO"] for row in data.get("titulos_seo_limpos", [])] or [
        result_state["produto"]
    ]
    placar_obj = data.get("placar_batalha", {})
    nota_comp_str = (
        f"Novo {parse_number(placar_obj.get('nota_novo_anuncio'), 0.0):.1f}/10 vs "
        f"Conc {parse_number(placar_obj.get('nota_concorrente'), 0.0):.1f}/10"
        if has_competitor
        else f"Autoavaliação {parse_number(placar_obj.get('nota_novo_anuncio'), 9.0):.1f}/10"
    )

    with st.container():
        sc1, sc2 = st.columns([2.2, 1.0])
        titulo_escolhido = sc1.selectbox(
            "Escolha o Título para Salvar na Planilha (Anuncios_Salvos)",
            titles_options,
            key="fabrica_titulo_escolhido",
        )
        sc2.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        if sc2.button(
            "💾 Salvar em Anuncios_Salvos", type="primary", use_container_width=True
        ):
            data_br = get_brasilia_now().strftime("%Y-%m-%d %H:%M:%S")
            row_save = [
                usuario,
                data_br,
                result_state["produto"],
                titulo_escolhido,
                str(data.get("descricao_pronta", "")),
                nota_comp_str,
            ]
            with st.spinner("Gravando na aba Anuncios_Salvos..."):
                ok, msg = append_saved_ad_to_sheets(row_save)
            if ok:
                st.success(msg)
            else:
                st.error(msg)


def render_resgate_anuncio() -> None:
    """Aba 6: Resgate de Anúncio (Passo 7 - Consertar Anúncio com Poucas Vendas)."""
    st.markdown(
        """
        <div class="hero-header">
            <h1 class="hero-title">🚑 Resgate de Anúncio — Diagnóstico e Reconstrução</h1>
            <p class="hero-subtitle">
                Auditoria com Gemini 2.5 Flash para identificar se o gargalo está em Tráfego ou Conversão e entregar um anúncio novo pronto para publicar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("resgate_anuncio_form"):
        titulo_atual = st.text_input(
            "Título Atual *",
            placeholder="ex: Tapete para cachorro barato 30un promocao",
        )

        c1, c2, c3, c4 = st.columns(4)
        preco_atual = c1.number_input("Preço (R$)", min_value=0.0, value=79.90, step=1.0)
        num_fotos = c2.number_input("Nº de Fotos", min_value=0, max_value=30, value=4, step=1)
        visitas_30d = c3.number_input("Visitas (30 dias)", min_value=0, value=420, step=10)
        vendas_30d = c4.number_input("Vendas (30 dias)", min_value=0, value=3, step=1)

        descricao_atual = st.text_area(
            "Descrição Atual *",
            height=130,
            placeholder="Cole aqui a descrição atual do anúncio com baixa performance...",
        )
        suspeita = st.text_input(
            "Suspeita do Vendedor",
            placeholder="ex: Acho que meu preço está bom, mas recebo cliques e quase ninguém compra.",
        )

        resgatar_btn = st.form_submit_button(
            "🩺 Diagnosticar e Resgatar Anúncio", type="primary", use_container_width=True
        )

    if resgatar_btn:
        if not titulo_atual.strip() or not descricao_atual.strip():
            st.warning("Informe o Título Atual e a Descrição Atual para o diagnóstico.")
        else:
            taxa_conv = (vendas_30d / visitas_30d * 100.0) if visitas_30d > 0 else 0.0
            prompt_resgate = f"""
Você é um consultor especialista em recuperação de anúncios de e-commerce Pet no Brasil.
Analise o anúncio abaixo que está vendendo pouco e faça o resgate completo.

DADOS DO ANÚNCIO ATUAL:
- Título Atual: {titulo_atual.strip()}
- Descrição Atual: {descricao_atual.strip()}
- Preço: R$ {preco_atual:.2f}
- Número de Fotos: {int(num_fotos)}
- Visitas (30 dias): {int(visitas_30d)}
- Vendas (30 dias): {int(vendas_30d)}
- Taxa de Conversão Calculada: {taxa_conv:.2f}%
- Suspeita do Vendedor: {suspeita.strip() or 'Não informada'}

REGRAS OBRIGATÓRIAS DE SAÍDA (RESPONDA ESTRITAMENTE EM JSON VÁLIDO):
1. "diagnostico_2_linhas": string com EXATAMENTE 2 linhas claras classificando o gargalo principal entre TRÁFEGO vs. CONVERSÃO e o motivo direto.
2. "novo_titulo_seo": string com o novo título otimizado (MÁXIMO 60 caracteres).
3. "nova_descricao": string com a nova descrição completa, persuasiva, escaneável e com quebra de objeções + FAQ curto, pronta para copiar e colar.
4. "bullets_mudancas": lista com EXATAMENTE 3 strings explicando objetivamente o que mudou e por quê (foco em impacto na taxa de clique e conversão).
"""
            with st.spinner("Diagnosticando gargalos e reescrevendo anúncio com Gemini 2.5 Flash..."):
                try:
                    client = get_gemini_client()
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt_resgate,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            system_instruction=(
                                "Responda apenas em JSON válido, direto, técnico e acionável em português do Brasil."
                            ),
                        ),
                    )
                    parsed_resgate = parse_gemini_json(response.text or "")
                    parsed_resgate["novo_titulo_seo"] = _truncate_seo_title(
                        parsed_resgate.get("novo_titulo_seo", ""), 60
                    )
                    parsed_resgate["taxa_conv"] = round(taxa_conv, 2)
                    st.session_state["resgate_result"] = parsed_resgate
                except Exception as exc:
                    st.error(f"Erro ao executar resgate com Gemini 2.5 Flash: {exc}")

    resgate = st.session_state.get("resgate_result")
    if not resgate:
        return

    diag = str(resgate.get("diagnostico_2_linhas", ""))
    novo_titulo = str(resgate.get("novo_titulo_seo", ""))
    nova_desc = str(resgate.get("nova_descricao", ""))
    bullets = resgate.get("bullets_mudancas", [])
    taxa_conv_val = float(resgate.get("taxa_conv", 0.0))

    st.markdown(
        f"""
        <div class="glass-card" style="margin: 1rem 0; border-color: rgba(245, 158, 11, 0.55);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                <div class="kpi-label" style="margin:0;">🩺 Diagnóstico (Tráfego vs. Conversão)</div>
                <span class="badge badge-info">Conversão atual: {taxa_conv_val:.2f}%</span>
            </div>
            <div style="color:#F8FAFC; font-size:0.96rem; line-height:1.55; white-space:pre-line;">{diag}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### ✨ Anúncio Novo Completo (Pronto para Copiar e Colar)")
    anuncio_novo_bloco = (
        f"TÍTULO SEO ({len(novo_titulo)} caracteres):\n"
        f"{novo_titulo}\n\n"
        f"DESCRIÇÃO:\n"
        f"{nova_desc}"
    )
    st.code(anuncio_novo_bloco, language="text")

    st.markdown("### 📌 O que Mudou e Por Quê")
    for bullet in bullets[:3]:
        st.markdown(f"- {bullet}")


# ==============================================================================
# ABA 7: RAIO-X DE LOJAS (MINHA LOJA VS. CONCORRENTES)
# ==============================================================================


def infer_marketplace_and_store_name(url_loja: str, apelido: str = "") -> Tuple[str, str]:
    """Infere Marketplace e Nome_Loja amigável a partir da URL caso apelido esteja vazio."""
    host = urlparse(url_loja).netloc.lower()
    if "mercadolivre" in host or "mercadolibre" in host:
        mkt = "Mercado Livre"
    elif "shopee" in host:
        mkt = "Shopee"
    elif "magazineluiza" in host or "magalu" in host:
        mkt = "Magalu"
    elif "amazon" in host:
        mkt = "Amazon"
    else:
        mkt = "Outro"

    if apelido.strip():
        return mkt, apelido.strip()

    cust_match = re.search(r"_CustId_(\d+)", url_loja, flags=re.IGNORECASE)
    if cust_match:
        return mkt, f"Loja ML {cust_match.group(1)}"

    parts = [p for p in urlparse(url_loja).path.split("/") if p and not p.startswith("_")]
    if parts:
        clean_slug = re.sub(r"[-_]+", " ", parts[-1]).strip().title()
        if clean_slug:
            return mkt, clean_slug[:60]

    return mkt, f"Loja {mkt}"


def prepare_store_catalog_dataframe(
    records: List[Dict[str, Any]], usuario: str
) -> pd.DataFrame:
    """Prepara DataFrame tipado do Catalogo_Lojas isolado por Usuario."""
    df = filter_user_dataframe(records, usuario)
    if df.empty:
        return df

    for col in ["Preco", "Nota"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: parse_number(x, 0.0))
        else:
            df[col] = 0.0

    for col in ["Estoque", "Vendas_Periodo"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: parse_int(x, 0))
        else:
            df[col] = 0

    df["Data_Hora_dt"] = pd.to_datetime(df.get("Data_Hora", ""), errors="coerce")
    df["Tipo_Norm"] = df.get("Tipo", "").apply(normalize_text)
    df["Titulo_Norm"] = df.get("Titulo", "").apply(normalize_text)
    return df


def _title_tokens(text: str) -> set[str]:
    """Extrai conjunto de tokens relevantes de um título para cruzamento entre lojas."""
    stopwords = {
        "de", "da", "do", "das", "dos", "para", "com", "sem", "em", "na", "no",
        "e", "ou", "a", "o", "as", "os", "um", "uma", "por", "kit",
    }
    return {
        tok
        for tok in re.findall(r"[a-z0-9]+", normalize_text(text))
        if len(tok) > 1 and tok not in stopwords
    }


def _find_matching_my_product(
    comp_row: Dict[str, Any], my_latest_rows: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Encontra produto equivalente em Minha Loja por ID_Anuncio ou similaridade de título."""
    comp_id = str(comp_row.get("ID_Anuncio", "")).strip().upper()
    comp_tokens = _title_tokens(str(comp_row.get("Titulo", "")))

    best_match: Optional[Dict[str, Any]] = None
    best_score = 0.0

    for my_row in my_latest_rows:
        my_id = str(my_row.get("ID_Anuncio", "")).strip().upper()
        if comp_id and my_id and comp_id == my_id:
            return my_row

        my_tokens = _title_tokens(str(my_row.get("Titulo", "")))
        if not comp_tokens or not my_tokens:
            continue
        inter = len(comp_tokens & my_tokens)
        union = len(comp_tokens | my_tokens)
        jaccard = inter / union if union > 0 else 0.0
        if jaccard >= 0.55 and jaccard > best_score:
            best_score = jaccard
            best_match = my_row

    return best_match


def compute_store_cross_analysis(
    df_latest_all: pd.DataFrame,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Cruza os catálogos mais recentes de Concorrentes contra Minha Loja:
    1) oportunidades_ouro: produtos 'Muito Escalável' dos concorrentes que Minha Loja ainda não possui.
    2) concorrente_vendendo_mais: produtos equivalentes onde o concorrente vende mais que Minha Loja.
    """
    if df_latest_all.empty:
        return [], []

    df_meu = df_latest_all[df_latest_all["Tipo_Norm"] == "minha loja"]
    df_conc = df_latest_all[df_latest_all["Tipo_Norm"] != "minha loja"]

    my_rows = df_meu.to_dict("records")
    comp_rows = df_conc.to_dict("records")

    oportunidades_ouro: List[Dict[str, Any]] = []
    concorrente_vendendo_mais: List[Dict[str, Any]] = []

    for c_row in comp_rows:
        matched_my = _find_matching_my_product(c_row, my_rows)
        escala_norm = normalize_text(c_row.get("Escalabilidade", ""))

        if matched_my is None:
            if escala_norm == "muito escalavel":
                oportunidades_ouro.append(c_row)
        else:
            vendas_conc = parse_int(c_row.get("Vendas_Periodo"), 0)
            vendas_meu = parse_int(matched_my.get("Vendas_Periodo"), 0)
            if vendas_conc > vendas_meu:
                concorrente_vendendo_mais.append(
                    {
                        "Produto": str(matched_my.get("Titulo", "")),
                        "Concorrente": str(c_row.get("Nome_Loja", "")),
                        "Meu_Preco": float(matched_my.get("Preco", 0.0)),
                        "Conc_Preco": float(c_row.get("Preco", 0.0)),
                        "Minhas_Vendas": vendas_meu,
                        "Conc_Vendas": vendas_conc,
                        "Meu_Full": str(matched_my.get("Full", "Não")),
                        "Conc_Full": str(c_row.get("Full", "Não")),
                        "Meu_Catalogo": str(matched_my.get("Catalogo", "Não")),
                        "Conc_Catalogo": str(c_row.get("Catalogo", "Não")),
                        "URL_Concorrente": str(c_row.get("URL_Produto", "")),
                    }
                )

    oportunidades_ouro.sort(
        key=lambda r: parse_int(r.get("Vendas_Periodo"), 0), reverse=True
    )
    concorrente_vendendo_mais.sort(
        key=lambda r: r["Conc_Vendas"] - r["Minhas_Vendas"], reverse=True
    )
    return oportunidades_ouro, concorrente_vendendo_mais


def _trend_badge_html(tendencia: str) -> str:
    norm = normalize_text(tendencia)
    if norm == "em alta":
        return '<span class="badge badge-success">▲ Em Alta</span>'
    if norm == "em baixa":
        return '<span class="badge badge-danger">▼ Em Baixa</span>'
    return '<span class="badge badge-info">● Estável</span>'


def _scalability_badge_html(escalabilidade: str) -> str:
    norm = normalize_text(escalabilidade)
    if norm == "muito escalavel":
        return '<span class="badge badge-success">★ Muito Escalável</span>'
    if norm == "media":
        return '<span class="badge badge-warning">◆ Média</span>'
    return '<span class="badge badge-danger">✕ Não Escalável</span>'


def _render_single_store_xray(
    df_store_history: pd.DataFrame, store_label: str
) -> None:
    """Renderiza KPIs, tabela com badges e gráfico Plotly de Validação de Compra para uma loja."""
    if df_store_history.empty:
        st.info(
            f"Ainda não há varreduras gravadas em Catalogo_Lojas para '{store_label}'. "
            "Após o próximo ciclo do monitor.py, todo o catálogo aparecerá aqui."
        )
        return

    df_sorted = df_store_history.sort_values("Data_Hora")
    df_latest = df_sorted.groupby("ID_Anuncio", as_index=False).tail(1).copy()
    df_latest = df_latest.sort_values(
        ["Vendas_Periodo", "Preco"], ascending=[False, False]
    )

    total_anuncios = len(df_latest)
    valid_prices = df_latest[df_latest["Preco"] > 0]["Preco"]
    ticket_medio = float(valid_prices.mean()) if not valid_prices.empty else 0.0
    pct_full = float(
        (df_latest["Full"].apply(normalize_text) == "sim").mean() * 100.0
    )
    pct_catalogo = float(
        (df_latest["Catalogo"].apply(normalize_text) == "sim").mean() * 100.0
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Anúncios Ativos</div>
                <div class="kpi-value">{total_anuncios}</div>
                <div class="kpi-sub">Loja: <strong>{store_label}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Ticket Médio da Loja</div>
                <div class="kpi-value">{format_brl(ticket_medio)}</div>
                <div class="kpi-sub">Média dos itens ativos</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">% no Full</div>
                <div class="kpi-value" style="color:#34D399;">{pct_full:.1f}%</div>
                <div class="kpi-sub">Operação Fulfillment</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">% em Catálogo</div>
                <div class="kpi-value" style="color:#38BDF8;">{pct_catalogo:.1f}%</div>
                <div class="kpi-sub">Disputa em Buybox</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Tabela estilizada com badges coloridas de Tendência e Escalabilidade
    html_rows: List[str] = []
    for _, row in df_latest.iterrows():
        prod_url = str(row.get("URL_Produto", "")).strip()
        titulo_txt = str(row.get("Titulo", ""))
        titulo_cell = (
            f'<a href="{prod_url}" target="_blank" style="color:#F8FAFC; text-decoration:none; font-weight:600;">{titulo_txt[:68]}</a>'
            if prod_url.startswith("http")
            else f'<strong style="color:#F8FAFC;">{titulo_txt[:68]}</strong>'
        )
        full_badge = (
            '<span class="badge badge-success">FULL</span>'
            if normalize_text(row.get("Full")) == "sim"
            else '<span class="badge badge-neutral">Normal</span>'
        )
        cat_badge = (
            '<span class="badge badge-info">Catálogo</span>'
            if normalize_text(row.get("Catalogo")) == "sim"
            else '<span class="badge badge-neutral">Clássico</span>'
        )

        html_rows.append(
            f"""
            <tr>
                <td>
                    {titulo_cell}<br/>
                    <span style="font-size:0.75rem; color:#94A3B8;">ID: {row.get('ID_Anuncio', '')}</span>
                </td>
                <td style="font-weight:700; color:#38BDF8;">{format_brl(float(row.get('Preco', 0.0)))}</td>
                <td>{int(row.get('Estoque', 0))} un.</td>
                <td style="font-weight:700; color:#34D399;">{int(row.get('Vendas_Periodo', 0))} un.</td>
                <td>{full_badge} {cat_badge}</td>
                <td>{float(row.get('Nota', 0.0)):.1f}</td>
                <td>{_trend_badge_html(str(row.get('Tendencia', 'Estável')))}</td>
                <td>{_scalability_badge_html(str(row.get('Escalabilidade', 'Média')))}</td>
            </tr>
            """
        )

    st.markdown(
        f"""
        <div class="exec-table-wrap">
            <table class="exec-table">
                <thead>
                    <tr>
                        <th>Produto</th>
                        <th>Preço</th>
                        <th>Estoque</th>
                        <th>Vendas Período</th>
                        <th>Modalidade</th>
                        <th>Nota</th>
                        <th>Tendência</th>
                        <th>Escalabilidade</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(html_rows)}
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Gráfico Interativo de Validação de Compra (Evolução de Vendas e Estoque)
    st.markdown("<div style='height: 1.1rem;'></div>", unsafe_allow_html=True)
    product_options = [
        f"{r['ID_Anuncio']} — {str(r['Titulo'])[:70]}"
        for _, r in df_latest.iterrows()
    ]
    selected_opt = st.selectbox(
        f"📈 Selecione um produto de '{store_label}' para Validação de Compra (Curva Histórica)",
        product_options,
        key=f"xray_select_{normalize_text(store_label)}",
    )

    if selected_opt:
        selected_id = selected_opt.split(" — ")[0].strip()
        df_item_hist = df_sorted[df_sorted["ID_Anuncio"] == selected_id]

        fig_val = go.Figure()
        fig_val.add_trace(
            go.Scatter(
                x=df_item_hist["Data_Hora"],
                y=df_item_hist["Vendas_Periodo"],
                name="Vendas no Período",
                mode="lines+markers",
                line=dict(color="#34D399", width=3, shape="spline", smoothing=0.75),
                marker=dict(size=7, color="#34D399"),
                fill="tozeroy",
                fillcolor="rgba(52, 211, 153, 0.18)",
                yaxis="y1",
            )
        )
        fig_val.add_trace(
            go.Scatter(
                x=df_item_hist["Data_Hora"],
                y=df_item_hist["Estoque"],
                name="Estoque Restante",
                mode="lines+markers",
                line=dict(color="#38BDF8", width=2, dash="dot"),
                marker=dict(size=6, color="#38BDF8"),
                yaxis="y2",
            )
        )
        fig_val.update_layout(
            title=dict(
                text=f"Validação de Compra — {selected_opt}",
                font=dict(size=15, color="#F8FAFC", family="Inter"),
            ),
            paper_bgcolor="rgba(15, 23, 42, 0.45)",
            plot_bgcolor="rgba(0, 0, 0, 0)",
            font=dict(color="#CBD5E1", family="Inter"),
            xaxis=dict(title="Leituras Recorrentes", gridcolor="rgba(51, 65, 85, 0.45)"),
            yaxis=dict(
                title="Vendas no Período (un.)",
                gridcolor="rgba(51, 65, 85, 0.45)",
                rangemode="tozero",
            ),
            yaxis2=dict(
                title="Estoque (un.)",
                overlaying="y",
                side="right",
                showgrid=False,
                rangemode="tozero",
            ),
            legend=dict(orientation="h", y=1.06, x=1, xanchor="right"),
            hovermode="x unified",
            height=360,
            margin=dict(l=30, r=40, t=65, b=35),
        )
        st.plotly_chart(fig_val, use_container_width=True)


def render_raiox_lojas(
    usuario: str, df_lojas: pd.DataFrame, df_catalogo: pd.DataFrame
) -> None:
    """Aba 7: Raio-X de Lojas (Minha Loja vs. Concorrentes)."""
    st.markdown(
        """
        <div class="hero-header">
            <h1 class="hero-title">🏪 Raio-X de Lojas (Minha Loja vs. Concorrentes)</h1>
            <p class="hero-subtitle">
                Monitoramento completo de vitrines inteiras para descobrir produtos muito escaláveis e gargalos competitivos frente à concorrência.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Formulário no topo para cadastrar loja inteira em Lojas_Monitoradas
    with st.form("add_store_xray_form", clear_on_submit=True):
        st.markdown("#### ➕ Cadastrar Loja para Raio-X Recorrente (`Lojas_Monitoradas`)")
        c1, c2, c3, c4 = st.columns([2.2, 1.0, 1.2, 0.9])
        url_loja = c1.text_input(
            "URL da página de 'Todos os Anúncios' *",
            placeholder="https://lista.mercadolivre.com.br/_CustId_123456789",
        )
        tipo_loja = c2.selectbox("Tipo", ["Minha Loja", "Concorrente"])
        apelido_loja = c3.text_input(
            "Apelido da Loja (opcional)",
            placeholder="ex: PetShop Líder SP",
        )
        st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
        salvar_loja = c4.form_submit_button(
            "Salvar Loja", type="primary", use_container_width=True
        )

        if salvar_loja:
            if not url_loja.strip().startswith(("http://", "https://")):
                st.warning("Informe uma URL válida começando com http:// ou https://.")
            else:
                mkt_detectado, nome_resolvido = infer_marketplace_and_store_name(
                    url_loja.strip(), apelido_loja
                )
                row_store = [
                    usuario,
                    tipo_loja,
                    nome_resolvido,
                    mkt_detectado,
                    url_loja.strip(),
                ]
                with st.spinner("Salvando loja na aba Lojas_Monitoradas..."):
                    ok, msg = append_monitored_store_to_sheets(row_store)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # Descobre todas as lojas concorrentes únicas cadastradas ou já coletadas
    concorrentes_nomes: List[str] = []
    if not df_lojas.empty and "Tipo" in df_lojas.columns:
        df_l_conc = df_lojas[df_lojas["Tipo"].apply(normalize_text) != "minha loja"]
        for nome in df_l_conc.get("Nome_Loja", pd.Series(dtype=str)).tolist():
            n_clean = str(nome).strip()
            if n_clean and n_clean not in concorrentes_nomes:
                concorrentes_nomes.append(n_clean)

    if not df_catalogo.empty:
        df_c_conc = df_catalogo[df_catalogo["Tipo_Norm"] != "minha loja"]
        for nome in df_c_conc.get("Nome_Loja", pd.Series(dtype=str)).tolist():
            n_clean = str(nome).strip()
            if n_clean and n_clean not in concorrentes_nomes:
                concorrentes_nomes.append(n_clean)

    tab_labels = ["Minha Loja"] + concorrentes_nomes + ["Cruzamento Geral (Eu vs. Todos)"]
    dynamic_tabs = st.tabs(tab_labels)

    # 1ª sub-aba: Minha Loja
    with dynamic_tabs[0]:
        df_minha = (
            df_catalogo[df_catalogo["Tipo_Norm"] == "minha loja"]
            if not df_catalogo.empty
            else pd.DataFrame()
        )
        _render_single_store_xray(df_minha, "Minha Loja")

    # Sub-abas individuais por Concorrente
    for idx, conc_name in enumerate(concorrentes_nomes, start=1):
        with dynamic_tabs[idx]:
            df_conc = (
                df_catalogo[
                    (df_catalogo["Tipo_Norm"] != "minha loja")
                    & (df_catalogo["Nome_Loja"].astype(str).str.strip() == conc_name)
                ]
                if not df_catalogo.empty
                else pd.DataFrame()
            )
            _render_single_store_xray(df_conc, conc_name)

    # Última sub-aba: Cruzamento Geral (Eu vs. Todos)
    with dynamic_tabs[-1]:
        if df_catalogo.empty:
            st.info(
                "Sem dados suficientes em Catalogo_Lojas para cruzar Minha Loja vs. Concorrentes."
            )
            return

        df_latest_all = (
            df_catalogo.sort_values("Data_Hora")
            .groupby(["Tipo_Norm", "Nome_Loja", "ID_Anuncio"], as_index=False)
            .tail(1)
        )
        oportunidades_ouro, perdendo_para_conc = compute_store_cross_analysis(df_latest_all)

        st.markdown("### 🏆 Oportunidades de Ouro (Muito Escalável nos Concorrentes e Ausente na Minha Loja)")
        if not oportunidades_ouro:
            st.info("Nenhuma oportunidade nova com selo 'Muito Escalável' detectada até o momento.")
        else:
            ouro_rows_html = []
            for item in oportunidades_ouro[:25]:
                url_p = str(item.get("URL_Produto", "")).strip()
                titulo_p = str(item.get("Titulo", ""))
                titulo_link = (
                    f'<a href="{url_p}" target="_blank" style="color:#34D399; font-weight:700; text-decoration:none;">{titulo_p[:65]}</a>'
                    if url_p.startswith("http")
                    else f'<strong style="color:#34D399;">{titulo_p[:65]}</strong>'
                )
                ouro_rows_html.append(
                    f"""
                    <tr>
                        <td><span class="badge badge-warning">{item.get('Nome_Loja', '')}</span></td>
                        <td>{titulo_link}</td>
                        <td style="font-weight:700;">{format_brl(float(item.get('Preco', 0.0)))}</td>
                        <td style="font-weight:700; color:#34D399;">{int(item.get('Vendas_Periodo', 0))} un.</td>
                        <td>{item.get('Full', 'Não')} · {item.get('Catalogo', 'Não')}</td>
                        <td>{_scalability_badge_html(str(item.get('Escalabilidade', 'Muito Escalável')))}</td>
                    </tr>
                    """
                )
            st.markdown(
                f"""
                <div class="exec-table-wrap">
                    <table class="exec-table">
                        <thead>
                            <tr>
                                <th>Concorrente</th>
                                <th>Produto Oportunidade</th>
                                <th>Preço</th>
                                <th>Vendas Período</th>
                                <th>Full · Catálogo</th>
                                <th>Selo</th>
                            </tr>
                        </thead>
                        <tbody>{"".join(ouro_rows_html)}</tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 1.4rem;'></div>", unsafe_allow_html=True)
        st.markdown("### ⚔️ Produtos Iguais Onde o Concorrente Vende Mais Que Você")
        if not perdendo_para_conc:
            st.success("Nenhum produto equivalente em desvantagem de volume frente aos concorrentes monitorados.")
        else:
            comp_rows_html = []
            for item in perdendo_para_conc[:25]:
                comp_rows_html.append(
                    f"""
                    <tr>
                        <td>
                            <strong style="color:#F8FAFC;">{item['Produto'][:60]}</strong><br/>
                            <span style="font-size:0.76rem; color:#94A3B8;">vs. {item['Concorrente']}</span>
                        </td>
                        <td>
                            <span style="color:#38BDF8; font-weight:700;">{format_brl(item['Meu_Preco'])}</span>
                            <span style="color:#64748B;">vs</span>
                            <span style="color:#F59E0B; font-weight:700;">{format_brl(item['Conc_Preco'])}</span>
                        </td>
                        <td>
                            <span style="color:#F87171; font-weight:700;">{item['Minhas_Vendas']} un.</span>
                            <span style="color:#64748B;">vs</span>
                            <span style="color:#34D399; font-weight:700;">{item['Conc_Vendas']} un.</span>
                        </td>
                        <td>Eu: {item['Meu_Full']} · Conc: {item['Conc_Full']}</td>
                        <td>Eu: {item['Meu_Catalogo']} · Conc: {item['Conc_Catalogo']}</td>
                    </tr>
                    """
                )
            st.markdown(
                f"""
                <div class="exec-table-wrap">
                    <table class="exec-table">
                        <thead>
                            <tr>
                                <th>Produto Equivalente</th>
                                <th>Meu Preço vs. Concorrente</th>
                                <th>Minhas Vendas vs. Concorrente</th>
                                <th>Status FULL</th>
                                <th>Catálogo</th>
                            </tr>
                        </thead>
                        <tbody>{"".join(comp_rows_html)}</tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ==============================================================================
# ABA 8: RANKING GERAL & BATALHA (SPARKLINES + DETECTOR DE SIMILARIDADE + MODAL)
# ==============================================================================


def compute_title_similarity(title_a: str, title_b: str) -> float:
    """
    Calcula similaridade entre dois títulos de anúncio combinando SequenceMatcher
    e sobreposição de tokens relevantes (retorna valor entre 0.0 e 1.0).
    """
    norm_a = normalize_text(title_a)
    norm_b = normalize_text(title_b)
    if not norm_a or not norm_b:
        return 0.0

    seq_ratio = SequenceMatcher(None, norm_a, norm_b).ratio()
    toks_a = _title_tokens(norm_a)
    toks_b = _title_tokens(norm_b)
    if toks_a and toks_b:
        inter = len(toks_a & toks_b)
        union = len(toks_a | toks_b)
        jaccard = inter / union if union > 0 else 0.0
        overlap_min = inter / min(len(toks_a), len(toks_b))
    else:
        jaccard = 0.0
        overlap_min = 0.0

    blended = (0.45 * jaccard) + (0.35 * overlap_min) + (0.20 * seq_ratio)
    return round(max(seq_ratio, jaccard, blended), 4)


def calculate_battle_score_0_to_10(
    my_ad: Dict[str, Any], comp_ad: Dict[str, Any]
) -> float:
    """
    Calcula Nota de Comparação de 0.0 a 10.0 para o nosso anúncio frente ao concorrente:
    - Preço competitivo (até 2.5 pts)
    - Presença no Full (até 2.0 pts)
    - Presença no Catálogo (até 1.5 pts)
    - Nota do anúncio (até 2.0 pts)
    - Volume de vendas (até 2.0 pts)
    """
    my_price = parse_number(my_ad.get("preco"), 0.0)
    comp_price = parse_number(comp_ad.get("preco"), 0.0)
    if my_price > 0 and comp_price > 0:
        if my_price <= comp_price:
            price_pts = 2.5
        else:
            ratio_diff = (my_price - comp_price) / comp_price
            price_pts = max(0.3, 2.5 * (1.0 - min(1.0, ratio_diff * 2.0)))
    elif my_price > 0:
        price_pts = 1.5
    else:
        price_pts = 1.0

    my_full = normalize_text(my_ad.get("full", "")) == "sim"
    comp_full = normalize_text(comp_ad.get("full", "")) == "sim"
    if my_full and not comp_full:
        full_pts = 2.0
    elif my_full and comp_full:
        full_pts = 1.6
    elif not my_full and not comp_full:
        full_pts = 1.0
    else:
        full_pts = 0.2

    my_cat = normalize_text(my_ad.get("catalogo", "")) == "sim"
    comp_cat = normalize_text(comp_ad.get("catalogo", "")) == "sim"
    if my_cat and not comp_cat:
        cat_pts = 1.5
    elif my_cat and comp_cat:
        cat_pts = 1.2
    elif not my_cat and not comp_cat:
        cat_pts = 0.8
    else:
        cat_pts = 0.2

    my_nota = min(5.0, max(0.0, parse_number(my_ad.get("nota"), 0.0)))
    comp_nota = min(5.0, max(0.0, parse_number(comp_ad.get("nota"), 0.0)))
    if my_nota > 0:
        nota_pts = (my_nota / 5.0) * 1.6
        if my_nota >= comp_nota:
            nota_pts += 0.4
    else:
        nota_pts = 0.8 if comp_nota == 0 else 0.5

    my_vendas = max(0, parse_int(my_ad.get("vendas_estimadas"), 0))
    comp_vendas = max(0, parse_int(comp_ad.get("vendas_estimadas"), 0))
    if my_vendas + comp_vendas > 0:
        share = my_vendas / (my_vendas + comp_vendas)
        vendas_pts = min(2.0, share * 2.6)
    else:
        vendas_pts = 1.0

    total = price_pts + full_pts + cat_pts + nota_pts + vendas_pts
    return round(min(10.0, max(0.0, total)), 1)


def _infer_trend_from_series(series: List[int]) -> str:
    """Infere tendência ('Em Alta', 'Estável' ou 'Em Baixa') a partir de uma série numérica."""
    if len(series) < 2:
        return "Em Alta" if series and series[-1] >= 3 else "Estável"
    prev = series[:-1]
    prev_avg = sum(prev) / len(prev)
    last_val = series[-1]
    if prev_avg == 0:
        return "Em Alta" if last_val > 0 else "Estável"
    if last_val >= prev_avg * 1.15 and last_val > 0:
        return "Em Alta"
    if last_val <= prev_avg * 0.80 or (last_val == 0 and prev_avg >= 1.5):
        return "Em Baixa"
    return "Estável"


def _infer_scalability_from_metrics(vendas_total: int, tendencia: str) -> str:
    """Classifica escalabilidade quando vinda apenas de Historico_Hora."""
    if (tendencia == "Em Alta" and vendas_total >= 5) or (
        vendas_total >= 12 and tendencia != "Em Baixa"
    ):
        return "Muito Escalável"
    if tendencia != "Em Baixa" and vendas_total >= 2:
        return "Média"
    return "Não Escalável"


def build_general_ranking_dataset(
    df_catalogo: pd.DataFrame, df_hist: pd.DataFrame
) -> List[Dict[str, Any]]:
    """
    Consolida todos os anúncios concorrentes de Catalogo_Lojas e Historico_Hora
    (já isolados pelo Usuario), ordena por Vendas Estimadas e Faturamento Bruto,
    gera a série de vendas para Sparklines e detecta anúncios parecidos (>= 45%)
    com a Minha Loja / Meu Anuncio calculando Nota de 0 a 10.
    """
    my_ads: List[Dict[str, Any]] = []
    competitor_items: List[Dict[str, Any]] = []
    seen_comp_keys: set[Tuple[str, str]] = set()

    # 1) Coleta Minha Loja + Concorrentes de Catalogo_Lojas
    if not df_catalogo.empty:
        rows_cat = df_catalogo.to_dict("records")
        grouped_cat: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
        for r in rows_cat:
            t_norm = normalize_text(r.get("Tipo_Norm") or r.get("Tipo", ""))
            loja = str(r.get("Nome_Loja", "")).strip() or "Loja Monitorada"
            aid = str(r.get("ID_Anuncio", "")).strip().upper() or normalize_text(
                r.get("Titulo", "")
            )
            grouped_cat.setdefault((t_norm, loja, aid), []).append(r)

        for (t_norm, loja, aid), grp in grouped_cat.items():
            grp_sorted = sorted(grp, key=lambda x: str(x.get("Data_Hora", "")))
            latest = grp_sorted[-1]
            series = [max(0, parse_int(x.get("Vendas_Periodo"), 0)) for x in grp_sorted[-12:]]
            vendas_est = max(
                parse_int(latest.get("Vendas_Periodo"), 0),
                sum(series[-3:]) if len(series) > 1 else (series[0] if series else 0),
            )
            preco = round(parse_number(latest.get("Preco"), 0.0), 2)
            fat_est = round(vendas_est * preco, 2)
            titulo = str(latest.get("Titulo", "")).strip() or aid

            entry = {
                "rank_key": f"cat_{normalize_text(loja)}_{aid}",
                "origem": "Catalogo_Lojas",
                "loja_concorrente": loja,
                "id_anuncio": aid,
                "titulo": titulo,
                "preco": preco,
                "estoque_atual": max(0, parse_int(latest.get("Estoque"), 0)),
                "vendas_estimadas": vendas_est,
                "faturamento_estimado": fat_est,
                "full": str(latest.get("Full", "Não")).strip() or "Não",
                "catalogo": str(latest.get("Catalogo", "Não")).strip() or "Não",
                "nota": round(parse_number(latest.get("Nota"), 0.0), 2),
                "tendencia": str(latest.get("Tendencia", "")).strip()
                or _infer_trend_from_series(series),
                "escalabilidade": str(latest.get("Escalabilidade", "")).strip()
                or _infer_scalability_from_metrics(vendas_est, _infer_trend_from_series(series)),
                "sales_series": series or [0],
                "url_produto": str(latest.get("URL_Produto", "")).strip(),
            }
            if t_norm == "minha loja":
                my_ads.append(entry)
            else:
                dedup_k = (normalize_text(loja), normalize_text(titulo))
                seen_comp_keys.add(dedup_k)
                competitor_items.append(entry)

    # 2) Complementa com Meu Anuncio + Concorrentes de Historico_Hora
    if not df_hist.empty:
        rows_hist = df_hist.to_dict("records")
        grouped_hist: Dict[Tuple[str, str, str, str], List[Dict[str, Any]]] = {}
        for r in rows_hist:
            t_norm = normalize_text(r.get("Tipo_Norm") or r.get("Tipo", ""))
            grupo = str(r.get("Grupo_Produto", "")).strip() or "Monitorado"
            mkt = str(r.get("Marketplace", "")).strip() or "Marketplace"
            titulo = str(r.get("Titulo", "")).strip() or grupo
            grouped_hist.setdefault((t_norm, grupo, mkt, titulo), []).append(r)

        for (t_norm, grupo, mkt, titulo), grp in grouped_hist.items():
            grp_sorted = sorted(grp, key=lambda x: str(x.get("Data_Hora", "")))
            latest = grp_sorted[-1]
            series = [max(0, parse_int(x.get("Vendas_na_Hora"), 0)) for x in grp_sorted[-12:]]
            vendas_sum = sum(max(0, parse_int(x.get("Vendas_na_Hora"), 0)) for x in grp_sorted)
            fat_sum = round(
                sum(parse_number(x.get("Faturamento_Hora"), 0.0) for x in grp_sorted), 2
            )
            preco = round(parse_number(latest.get("Preco"), 0.0), 2)
            if fat_sum <= 0 and vendas_sum > 0 and preco > 0:
                fat_sum = round(vendas_sum * preco, 2)

            tend = _infer_trend_from_series(series)
            loja_label = f"{mkt} · {grupo}"
            entry = {
                "rank_key": f"hist_{normalize_text(mkt)}_{normalize_text(titulo)[:28]}",
                "origem": "Historico_Hora",
                "loja_concorrente": loja_label,
                "id_anuncio": grupo[:24].upper(),
                "titulo": titulo,
                "preco": preco,
                "estoque_atual": max(0, parse_int(latest.get("Estoque_Atual"), 0)),
                "vendas_estimadas": vendas_sum,
                "faturamento_estimado": fat_sum,
                "full": str(latest.get("Full", "Não")).strip() or "Não",
                "catalogo": str(latest.get("Catalogo", "Não")).strip() or "Não",
                "nota": round(parse_number(latest.get("Nota"), 0.0), 2),
                "tendencia": tend,
                "escalabilidade": _infer_scalability_from_metrics(vendas_sum, tend),
                "sales_series": series or [0],
                "url_produto": "",
            }

            if t_norm == "meu anuncio":
                my_ads.append(entry)
            else:
                dedup_k = (normalize_text(loja_label), normalize_text(titulo))
                title_already_in_cat = any(
                    normalize_text(c["titulo"]) == normalize_text(titulo)
                    for c in competitor_items
                )
                if dedup_k not in seen_comp_keys and not title_already_in_cat:
                    seen_comp_keys.add(dedup_k)
                    competitor_items.append(entry)

    # 3) Ordenação executiva por Vendas Estimadas e Faturamento Bruto Estimado
    competitor_items.sort(
        key=lambda x: (
            x["vendas_estimadas"],
            x["faturamento_estimado"],
            x["preco"],
        ),
        reverse=True,
    )

    # 4) Detector automático de 'Anúncio Parecido com o Seu' (>= 45%) + Nota 0 a 10
    for idx, comp in enumerate(competitor_items, start=1):
        comp["posicao"] = idx
        best_my: Optional[Dict[str, Any]] = None
        best_sim = 0.0

        for my_item in my_ads:
            sim = compute_title_similarity(comp["titulo"], my_item["titulo"])
            if sim >= 0.45 and sim > best_sim:
                best_sim = sim
                best_my = my_item

        if best_my is not None:
            comp["matched_my_ad"] = best_my
            comp["similarity_pct"] = round(best_sim * 100.0, 1)
            comp["battle_score"] = calculate_battle_score_0_to_10(best_my, comp)
        else:
            comp["matched_my_ad"] = None
            comp["similarity_pct"] = 0.0
            comp["battle_score"] = None

    return competitor_items


def build_sparkline_figure(sales_series: List[int], tendencia: str) -> go.Figure:
    """
    Cria mini-gráfico de linha (Sparkline ~60px) colorido dinamicamente pela tendência:
    Verde (#00E676) em alta | Amarelo (#FFD600) estável | Vermelho (#FF5252) em queda.
    """
    norm_t = normalize_text(tendencia)
    if norm_t == "em alta":
        line_color = "#00E676"
        fill_color = "rgba(0, 230, 118, 0.16)"
    elif norm_t in ("em baixa", "em queda"):
        line_color = "#FF5252"
        fill_color = "rgba(255, 82, 82, 0.16)"
    else:
        line_color = "#FFD600"
        fill_color = "rgba(255, 214, 0, 0.14)"

    y_vals = list(sales_series) if sales_series else [0, 0]
    if len(y_vals) == 1:
        y_vals = [y_vals[0], y_vals[0]]
    x_vals = list(range(1, len(y_vals) + 1))

    fig = go.Figure(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines",
            line=dict(color=line_color, width=2.4, shape="spline", smoothing=0.8),
            fill="tozeroy",
            fillcolor=fill_color,
            hovertemplate="Leitura %{x}: <b>%{y}</b> un.<extra></extra>",
        )
    )
    fig.update_layout(
        height=62,
        margin=dict(l=2, r=2, t=4, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False, rangemode="tozero"),
    )
    return fig


def _generate_battle_improvement_plan(
    my_ad: Dict[str, Any], comp_ad: Dict[str, Any]
) -> Dict[str, Any]:
    """Envia ambos os anúncios para gemini-2.5-flash via google-genai para gerar plano tático."""
    prompt = f"""
Você é um estrategista sênior de marketplaces brasileiros no nicho Pet.
Compare o NOSSO ANÚNCIO com o ANÚNCIO CONCORRENTE e gere um plano prático e objetivo para colocarmos o nosso anúncio acima do concorrente em conversão e vendas.

NOSSO ANÚNCIO:
- Título: {my_ad.get('titulo', '')}
- Preço: R$ {parse_number(my_ad.get('preco'), 0.0):.2f}
- Estoque Atual: {parse_int(my_ad.get('estoque_atual'), 0)}
- Vendas Estimadas no Período: {parse_int(my_ad.get('vendas_estimadas'), 0)}
- FULL: {my_ad.get('full', 'Não')}
- Catálogo: {my_ad.get('catalogo', 'Não')}
- Nota: {parse_number(my_ad.get('nota'), 0.0):.1f}

ANÚNCIO CONCORRENTE ({comp_ad.get('loja_concorrente', '')}):
- Título: {comp_ad.get('titulo', '')}
- Preço: R$ {parse_number(comp_ad.get('preco'), 0.0):.2f}
- Estoque Atual: {parse_int(comp_ad.get('estoque_atual'), 0)}
- Vendas Estimadas no Período: {parse_int(comp_ad.get('vendas_estimadas'), 0)}
- FULL: {comp_ad.get('full', 'Não')}
- Catálogo: {comp_ad.get('catalogo', 'Não')}
- Nota: {parse_number(comp_ad.get('nota'), 0.0):.1f}

RETORNE ESTRITAMENTE EM JSON VÁLIDO com as seguintes chaves:
{{
  "resumo_executivo": "Diagnóstico direto em 2 linhas de por que o concorrente performa como está e onde está nossa alavanca.",
  "titulo_seo": {{
    "novo_titulo_sugerido": "Título otimizado <= 60 caracteres focado em busca real",
    "acoes": ["ação 1", "ação 2"]
  }},
  "preco_oferta": {{
    "estrategia": "Sugestão de preço, kit, cupom ou ancoragem",
    "acoes": ["ação 1", "ação 2"]
  }},
  "logistica": {{
    "diagnostico_full_envio": "Recomendação sobre FULL, prazo e catálogo",
    "acoes": ["ação 1", "ação 2"]
  }},
  "quebra_objecoes": {{
    "pontos_criticos": ["objeção/argumento 1", "objeção/argumento 2", "objeção/argumento 3"]
  }}
}}
"""
    client = get_gemini_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction=(
                "Responda apenas JSON válido em português do Brasil, direto ao ponto e acionável."
            ),
        ),
    )
    return parse_gemini_json(response.text or "")


@st.dialog("Auditoria de Batalha: Você vs. Concorrente", width="large")
def open_battle_audit_dialog(comp_item: Dict[str, Any]) -> None:
    """Modal de Comparação Profunda lado a lado + Plano de Melhoria com Gemini 2.5 Flash."""
    my_ad = comp_item.get("matched_my_ad") or {}
    battle_score = parse_number(comp_item.get("battle_score"), 0.0)
    sim_pct = parse_number(comp_item.get("similarity_pct"), 0.0)

    my_title_esc = html_lib.escape(str(my_ad.get("titulo", "Meu Anúncio")))
    comp_title_esc = html_lib.escape(str(comp_item.get("titulo", "Concorrente")))
    comp_loja_esc = html_lib.escape(str(comp_item.get("loja_concorrente", "")))

    st.markdown(
        f"""
        <div class="glass-card" style="margin-bottom: 1rem; border-color: rgba(56, 189, 248, 0.50);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.8rem;">
                <div>
                    <div class="kpi-label" style="margin-bottom:0.2rem;">Similaridade Detectada: {sim_pct:.1f}%</div>
                    <div style="font-size:0.95rem; font-weight:700; color:#F8FAFC;">
                        Seu Anúncio vs. #{comp_item.get('posicao', '-')} ({comp_loja_esc})
                    </div>
                </div>
                <div style="text-align:right;">
                    <span class="badge badge-info" style="font-size:0.92rem; padding:0.35rem 0.85rem;">
                        Nota da Batalha: {battle_score:.1f} / 10
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Tabela comparativa lado a lado
    my_preco = parse_number(my_ad.get("preco"), 0.0)
    comp_preco = parse_number(comp_item.get("preco"), 0.0)
    my_est = parse_int(my_ad.get("estoque_atual"), 0)
    comp_est = parse_int(comp_item.get("estoque_atual"), 0)
    my_vendas = parse_int(my_ad.get("vendas_estimadas"), 0)
    comp_vendas = parse_int(comp_item.get("vendas_estimadas"), 0)
    my_nota = parse_number(my_ad.get("nota"), 0.0)
    comp_nota = parse_number(comp_item.get("nota"), 0.0)

    st.markdown(
        f"""
        <div class="exec-table-wrap" style="margin-bottom: 1rem;">
            <table class="exec-table">
                <thead>
                    <tr>
                        <th>Critério</th>
                        <th>Seu Anúncio ({my_title_esc[:42]})</th>
                        <th>Concorrente ({comp_title_esc[:42]})</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Preço</strong></td>
                        <td style="color:{'#34D399' if my_preco <= comp_preco and my_preco > 0 else '#F8FAFC'}; font-weight:700;">{format_brl(my_preco)}</td>
                        <td style="color:#38BDF8; font-weight:700;">{format_brl(comp_preco)}</td>
                    </tr>
                    <tr>
                        <td><strong>Estoque</strong></td>
                        <td>{my_est} un.</td>
                        <td>{comp_est} un.</td>
                    </tr>
                    <tr>
                        <td><strong>Vendas Estimadas</strong></td>
                        <td style="color:{'#34D399' if my_vendas >= comp_vendas else '#F87171'}; font-weight:700;">{my_vendas} un.</td>
                        <td style="color:#34D399; font-weight:700;">{comp_vendas} un.</td>
                    </tr>
                    <tr>
                        <td><strong>FULL</strong></td>
                        <td>{html_lib.escape(str(my_ad.get('full', 'Não')))}</td>
                        <td>{html_lib.escape(str(comp_item.get('full', 'Não')))}</td>
                    </tr>
                    <tr>
                        <td><strong>Catálogo</strong></td>
                        <td>{html_lib.escape(str(my_ad.get('catalogo', 'Não')))}</td>
                        <td>{html_lib.escape(str(comp_item.get('catalogo', 'Não')))}</td>
                    </tr>
                    <tr>
                        <td><strong>Nota</strong></td>
                        <td>{my_nota:.1f} ⭐</td>
                        <td>{comp_nota:.1f} ⭐</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "ranking_ai_plans" not in st.session_state:
        st.session_state["ranking_ai_plans"] = {}

    plan_key = f"{comp_item.get('rank_key', '')}::{my_ad.get('id_anuncio', '')}"
    if st.button(
        "🚀 Gerar Plano de Melhoria com IA",
        type="primary",
        use_container_width=True,
        key=f"ai_plan_btn_{plan_key}",
    ):
        with st.spinner("Consultando Gemini 2.5 Flash para montar seu plano de ultrapassagem..."):
            try:
                ai_plan = _generate_battle_improvement_plan(my_ad, comp_item)
                st.session_state["ranking_ai_plans"][plan_key] = ai_plan
            except Exception as exc:
                st.error(f"Erro ao gerar plano com Gemini 2.5 Flash: {exc}")

    saved_plan = st.session_state["ranking_ai_plans"].get(plan_key)
    if saved_plan:
        st.markdown(
            f"""
            <div class="glass-card" style="margin-top:0.8rem; border-color: rgba(52, 211, 153, 0.45);">
                <div class="kpi-label">Diagnóstico Estratégico</div>
                <p style="margin:0; color:#F8FAFC; font-size:0.92rem;">
                    {html_lib.escape(str(saved_plan.get('resumo_executivo', '')))}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        p1, p2 = st.columns(2)
        with p1:
            t_seo = saved_plan.get("titulo_seo", {})
            st.markdown("#### 🏷️ Título SEO")
            if t_seo.get("novo_titulo_sugerido"):
                st.code(
                    _truncate_seo_title(str(t_seo.get("novo_titulo_sugerido", "")), 60),
                    language="text",
                )
            for act in t_seo.get("acoes", []):
                st.markdown(f"- {act}")

            st.markdown("#### 🚚 Logística")
            log_obj = saved_plan.get("logistica", {})
            if log_obj.get("diagnostico_full_envio"):
                st.caption(str(log_obj.get("diagnostico_full_envio")))
            for act in log_obj.get("acoes", []):
                st.markdown(f"- {act}")

        with p2:
            pr_obj = saved_plan.get("preco_oferta", {})
            st.markdown("#### 💰 Preço / Oferta")
            if pr_obj.get("estrategia"):
                st.caption(str(pr_obj.get("estrategia")))
            for act in pr_obj.get("acoes", []):
                st.markdown(f"- {act}")

            st.markdown("#### 🛡️ Quebra de Objeções")
            q_obj = saved_plan.get("quebra_objecoes", {})
            for pt in q_obj.get("pontos_criticos", []):
                st.markdown(f"- {pt}")


def render_ranking_geral(
    usuario: str, df_hist: pd.DataFrame, df_catalogo: pd.DataFrame
) -> None:
    """Aba 8: Ranking Geral & Batalha consolidando todos os concorrentes monitorados."""
    st.markdown(
        """
        <div class="hero-header">
            <h1 class="hero-title">🏆 Ranking Geral & Batalha</h1>
            <p class="hero-subtitle">
                Visão executiva consolidada dos anúncios concorrentes ordenados por vendas e faturamento estimado, com micro-gráficos de tendência e auditoria automática frente ao seu catálogo.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ranking_items = build_general_ranking_dataset(df_catalogo, df_hist)
    if not ranking_items:
        st.info(
            f"Nenhum anúncio concorrente encontrado para @{usuario} em Catalogo_Lojas ou Historico_Hora. "
            "Cadastre concorrentes nas abas anteriores e aguarde a coleta do monitor.py."
        )
        return

    # Filtros executivos rápidos no topo
    f1, f2, f3 = st.columns([1.8, 1.0, 1.0])
    busca_txt = f1.text_input(
        "Filtrar por título ou loja concorrente",
        placeholder="ex: tapete, golden, petprime...",
        key="ranking_filter_txt",
    )
    filtro_escala = f2.selectbox(
        "Escalabilidade",
        ["Todas", "Muito Escalável", "Média", "Não Escalável"],
        key="ranking_filter_escala",
    )
    apenas_parecidos = f3.checkbox(
        "Apenas parecidos c/ os meus (≥45%)",
        value=False,
        key="ranking_filter_similar",
    )

    filtered_items = ranking_items
    if busca_txt.strip():
        q_norm = normalize_text(busca_txt)
        filtered_items = [
            it
            for it in filtered_items
            if q_norm in normalize_text(it["titulo"])
            or q_norm in normalize_text(it["loja_concorrente"])
        ]
    if filtro_escala != "Todas":
        escala_target = normalize_text(filtro_escala)
        filtered_items = [
            it
            for it in filtered_items
            if normalize_text(it["escalabilidade"]) == escala_target
        ]
    if apenas_parecidos:
        filtered_items = [
            it for it in filtered_items if it.get("matched_my_ad") is not None
        ]

    # KPIs Consolidados do Ranking Filtrado
    total_conc = len(filtered_items)
    total_vendas_rank = sum(it["vendas_estimadas"] for it in filtered_items)
    total_fat_rank = sum(it["faturamento_estimado"] for it in filtered_items)
    total_matches = sum(1 for it in filtered_items if it.get("matched_my_ad") is not None)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Concorrentes no Ranking</div>
                <div class="kpi-value">{total_conc}</div>
                <div class="kpi-sub">Consolidado Catalogo + Historico</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Vendas Estimadas</div>
                <div class="kpi-value" style="color:#34D399;">{total_vendas_rank} un.</div>
                <div class="kpi-sub">Soma do ranking filtrado</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Faturamento Bruto Est.</div>
                <div class="kpi-value">{format_brl(total_fat_rank)}</div>
                <div class="kpi-sub">Volume financeiro estimado</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="kpi-label">Confrontos Diretos (≥45%)</div>
                <div class="kpi-value" style="color:#38BDF8;">{total_matches}</div>
                <div class="kpi-sub">Itens parecidos c/ Minha Loja</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 1.1rem;'></div>", unsafe_allow_html=True)

    if not filtered_items:
        st.warning("Nenhum anúncio corresponde aos filtros selecionados.")
        return

    # Renderização das linhas/cards do Ranking (Top 1, 2, 3...)
    for item in filtered_items[:50]:
        pos = item["posicao"]
        medal_icon = "🥇" if pos == 1 else ("🥈" if pos == 2 else ("🥉" if pos == 3 else ""))
        medal_cls = (
            "rank-medal-1"
            if pos == 1
            else ("rank-medal-2" if pos == 2 else ("rank-medal-3" if pos == 3 else "rank-medal-n"))
        )

        loja_esc = html_lib.escape(str(item["loja_concorrente"]))
        titulo_esc = html_lib.escape(str(item["titulo"]))
        url_prod = str(item.get("url_produto", "")).strip()
        titulo_html = (
            f'<a href="{html_lib.escape(url_prod)}" target="_blank" style="color:#F8FAFC; text-decoration:none; font-weight:700;">{titulo_esc[:78]}</a>'
            if url_prod.startswith("http")
            else f'<strong style="color:#F8FAFC;">{titulo_esc[:78]}</strong>'
        )
        escala_badge = _scalability_badge_html(item["escalabilidade"])

        c_info, c_spark, c_match = st.columns([3.0, 1.35, 1.45], vertical_alignment="center")

        with c_info:
            st.markdown(
                f"""
                <div class="ranking-card">
                    <div style="display:flex; align-items:flex-start; gap:0.9rem;">
                        <div class="rank-medal {medal_cls}">{medal_icon} #{pos}</div>
                        <div style="flex:1; min-width:0;">
                            <div style="display:flex; align-items:center; flex-wrap:wrap; gap:0.45rem; margin-bottom:0.28rem;">
                                <span class="badge badge-info">{loja_esc}</span>
                                {escala_badge}
                                <span class="badge badge-neutral">{html_lib.escape(item['origem'])}</span>
                            </div>
                            <div style="font-size:0.96rem; line-height:1.35; margin-bottom:0.45rem;">
                                {titulo_html}
                            </div>
                            <div style="display:flex; flex-wrap:wrap; gap:1.1rem; font-size:0.82rem; color:#CBD5E1;">
                                <span>Preço: <strong style="color:#38BDF8;">{format_brl(item['preco'])}</strong></span>
                                <span>Estoque: <strong>{item['estoque_atual']} un.</strong></span>
                                <span>Vendas Est.: <strong style="color:#34D399;">{item['vendas_estimadas']} un.</strong></span>
                                <span>Fat. Bruto Est.: <strong style="color:#F8FAFC;">{format_brl(item['faturamento_estimado'])}</strong></span>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_spark:
            st.plotly_chart(
                build_sparkline_figure(item["sales_series"], item["tendencia"]),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"spark_{pos}_{item['rank_key']}",
            )
            st.markdown(
                f"<div style='text-align:center; margin-top:-0.55rem;'>{_trend_badge_html(item['tendencia'])}</div>",
                unsafe_allow_html=True,
            )

        with c_match:
            if item.get("matched_my_ad") is not None:
                score_val = parse_number(item.get("battle_score"), 0.0)
                st.markdown(
                    f"""
                    <div class="match-compare-box" title="Similaridade: {item['similarity_pct']:.0f}% — Clique em Comparar abaixo">
                        <span class="match-score-pill">
                            Anúncio parecido com o seu | Nota: <strong>{score_val:.1f}/10</strong>
                        </span>
                        <span class="match-hover-cta">⚔️ Comparar</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    "⚔️ Comparar",
                    key=f"cmp_btn_{pos}_{item['rank_key']}",
                    use_container_width=True,
                ):
                    open_battle_audit_dialog(item)
            else:
                st.markdown(
                    """
                    <div class="glass-card" style="padding:0.62rem 0.85rem; text-align:center;">
                        <span style="font-size:0.78rem; color:#94A3B8;">
                            Sem item equivalente ≥45% em Minha Loja
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ==============================================================================
# ABA 9: NOTIFICAÇÕES & ALERTAS INTELIGENTES (MULTI-USUÁRIO + TELEGRAM)
# ==============================================================================


def _count_unread_notifications(df_notif_hist: pd.DataFrame) -> int:
    """Conta notificações com Lida != 'Sim' para o usuário logado."""
    if df_notif_hist.empty or "Lida" not in df_notif_hist.columns:
        return 0
    unread_mask = df_notif_hist["Lida"].apply(lambda x: normalize_text(x) != "sim")
    return int(unread_mask.sum())


def render_top_notifications_banner(
    df_notif_hist: pd.DataFrame, active_tab: str
) -> None:
    """Exibe banner/contador sutil no topo de qualquer aba quando houver alertas não lidos."""
    unread_count = _count_unread_notifications(df_notif_hist)
    if unread_count <= 0:
        return

    plural = "alerta não lido" if unread_count == 1 else "alertas não lidos"
    col_b, col_btn = st.columns([4.6, 1.2], vertical_alignment="center")
    with col_b:
        st.markdown(
            f"""
            <div class="notif-unread-banner">
                <div style="display:flex; align-items:center; gap:0.65rem; flex-wrap:wrap;">
                    <span class="badge badge-info">🔔 {unread_count} {plural}</span>
                    <span style="font-size:0.86rem; color:#E2E8F0;">
                        Novos movimentos de concorrentes detectados no monitoramento horário.
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_btn:
        if active_tab != "🔔 Notificações & Alertas":
            if st.button(
                "🔔 Abrir Alertas",
                key="top_banner_open_notif_btn",
                use_container_width=True,
            ):
                st.session_state["jump_to_notif"] = True
                st.rerun()


def _resolve_alert_card_style(tipo_alerta: str) -> Tuple[str, str, str]:
    """Retorna (css_class, badge_class, emoji) conforme o tipo do alerta."""
    norm = normalize_text(tipo_alerta)
    if "promocao" in norm or "queda" in norm or "preco" in norm:
        return "notif-card-promo", "badge-danger", "🔴"
    if "estoque" in norm:
        return "notif-card-stock", "badge-success", "🟢"
    if "pico" in norm or "venda" in norm:
        return "notif-card-peak", "badge-info", "🔵"
    return "notif-card-logistics", "badge-warning", "🟣"


def render_notificacoes(
    usuario: str,
    nome_exibicao: str,
    df_notif_cfg: pd.DataFrame,
    df_notif_hist: pd.DataFrame,
) -> None:
    """Aba 9: Painel de Controle de Notificações (Telegram + Regras) e Feed de Alertas Recebidos."""
    st.markdown(
        """
        <div class="hero-header">
            <h1 class="hero-title">🔔 Notificações & Alertas</h1>
            <p class="hero-subtitle">
                Configure gatilhos inteligentes por usuário, valide seu canal no Telegram e acompanhe em tempo real todas as movimentações dos concorrentes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Carrega preferências atuais do usuário ou padrões iniciais
    current_cfg: Dict[str, Any] = {}
    if not df_notif_cfg.empty:
        current_cfg = df_notif_cfg.iloc[-1].to_dict()

    has_saved_cfg = bool(current_cfg)
    default_ativo = (
        normalize_text(current_cfg.get("Ativo_Geral", "Sim")) == "sim"
        if has_saved_cfg
        else True
    )
    default_chat_id = str(current_cfg.get("Telegram_Chat_ID", "")).strip()
    default_est_ativo = (
        normalize_text(current_cfg.get("Alerta_Estoque_Baixo", "Sim")) == "sim"
        if has_saved_cfg
        else True
    )
    default_lim_est = max(0, parse_int(current_cfg.get("Limite_Estoque"), 5))
    default_promo = (
        normalize_text(current_cfg.get("Alerta_Promocao", "Sim")) == "sim"
        if has_saved_cfg
        else True
    )
    default_pico = (
        normalize_text(current_cfg.get("Alerta_Venda_Pico", "Sim")) == "sim"
        if has_saved_cfg
        else True
    )
    default_lim_venda = max(1, parse_int(current_cfg.get("Limite_Venda_Hora"), 5))
    default_cat_full = (
        normalize_text(current_cfg.get("Alerta_Catalogo_Full", "Sim")) == "sim"
        if has_saved_cfg
        else True
    )

    col_ctrl, col_feed = st.columns([1.05, 1.35], gap="large")

    # ==========================================================================
    # COLUNA 1: PAINEL DE CONTROLE CLICÁVEL (st.toggle)
    # ==========================================================================
    with col_ctrl:
        st.markdown(
            """
            <div class="glass-card" style="margin-bottom: 1rem;">
                <div class="kpi-label">Painel de Controle Clicável</div>
                <div style="font-size:1.05rem; font-weight:700; color:#F8FAFC;">
                    Preferências de Disparo Automático
                </div>
                <div style="font-size:0.82rem; color:#94A3B8; margin-top:0.2rem;">
                    Aplicado automaticamente na coleta horária do monitor.py e no histórico do painel.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        ativo_geral = st.toggle(
            "Toggle Mestre: Ativar Notificações Gerais",
            value=default_ativo,
            key=f"notif_master_{usuario}",
            help="Quando desativado, nenhum alerta será gravado ou enviado ao Telegram.",
        )

        st.markdown("##### 📱 Integração Telegram")
        tg_col1, tg_col2 = st.columns([1.4, 1.0], vertical_alignment="bottom")
        with tg_col1:
            telegram_chat_id = st.text_input(
                "Telegram Chat ID",
                value=default_chat_id,
                placeholder="ex: 123456789 ou -100123456789",
                key=f"notif_chat_id_{usuario}",
            )
        with tg_col2:
            if st.button(
                "Enviar Mensagem de Teste",
                key=f"notif_test_tg_{usuario}",
                use_container_width=True,
            ):
                with st.spinner("Enviando mensagem de teste ao Telegram..."):
                    ok_tg, msg_tg = send_telegram_test_message(
                        telegram_chat_id, usuario, nome_exibicao
                    )
                if ok_tg:
                    st.success(msg_tg)
                else:
                    st.error(msg_tg)

        st.markdown("##### ⚙️ Regras Individuais de Alerta")

        alerta_estoque_baixo = st.toggle(
            "Aviso de estoque baixo / zerado do concorrente",
            value=default_est_ativo,
            key=f"notif_tog_stock_{usuario}",
        )
        limite_estoque = st.number_input(
            "Limite de unidades para estoque baixo",
            min_value=0,
            max_value=9999,
            value=int(default_lim_est),
            step=1,
            key=f"notif_lim_stock_{usuario}",
            disabled=not alerta_estoque_baixo,
        )

        alerta_promocao = st.toggle(
            "Aviso de promoção / alteração de preço do concorrente",
            value=default_promo,
            key=f"notif_tog_promo_{usuario}",
        )

        alerta_venda_pico = st.toggle(
            "Aviso de venda expressiva dos concorrentes",
            value=default_pico,
            key=f"notif_tog_peak_{usuario}",
        )
        limite_venda_hora = st.number_input(
            "Quantas vendas/hora disparam o alerta de pico",
            min_value=1,
            max_value=9999,
            value=int(default_lim_venda),
            step=1,
            key=f"notif_lim_peak_{usuario}",
            disabled=not alerta_venda_pico,
        )

        alerta_catalogo_full = st.toggle(
            "Aviso de mudança de Full ou Catálogo (Buy Box)",
            value=default_cat_full,
            key=f"notif_tog_cat_{usuario}",
        )

        st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)
        if st.button(
            "💾 Salvar Preferências",
            type="primary",
            use_container_width=True,
            key=f"notif_save_prefs_{usuario}",
        ):
            with st.spinner("Gravando preferências na aba Config_Notificacoes..."):
                ok_save, msg_save = save_notification_config_to_sheets(
                    usuario=usuario,
                    ativo_geral=ativo_geral,
                    telegram_chat_id=telegram_chat_id,
                    alerta_estoque_baixo=alerta_estoque_baixo,
                    limite_estoque=int(limite_estoque),
                    alerta_promocao=alerta_promocao,
                    alerta_venda_pico=alerta_venda_pico,
                    limite_venda_hora=int(limite_venda_hora),
                    alerta_catalogo_full=alerta_catalogo_full,
                )
            if ok_save:
                st.success(msg_save)
                st.rerun()
            else:
                st.error(msg_save)

    # ==========================================================================
    # COLUNA 2: FEED DE ALERTAS RECEBIDOS
    # ==========================================================================
    with col_feed:
        unread_total = _count_unread_notifications(df_notif_hist)
        total_alerts = len(df_notif_hist)

        f_head1, f_head2 = st.columns([1.45, 1.0], vertical_alignment="center")
        with f_head1:
            st.markdown(
                f"""
                <div class="glass-card" style="padding: 0.9rem 1.1rem; margin-bottom: 0.8rem;">
                    <div class="kpi-label" style="margin-bottom:0.2rem;">Feed de Alertas Recebidos</div>
                    <div style="font-size:1rem; font-weight:700; color:#F8FAFC;">
                        {total_alerts} registrado(s) · <span style="color:#38BDF8;">{unread_total} não lido(s)</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with f_head2:
            if st.button(
                "✔️ Marcar todas como lidas",
                use_container_width=True,
                disabled=(unread_total == 0),
                key=f"notif_mark_all_read_{usuario}",
            ):
                with st.spinner("Atualizando Historico_Notificacoes..."):
                    ok_mark, msg_mark = mark_all_notifications_read_in_sheets(usuario)
                if ok_mark:
                    st.success(msg_mark)
                    st.rerun()
                else:
                    st.error(msg_mark)

        if df_notif_hist.empty:
            st.info(
                "Nenhum alerta registrado em Historico_Notificacoes para a sua conta ainda. "
                "Salve suas preferências ao lado e aguarde o próximo ciclo do monitor.py."
            )
            return

        filtro_feed = st.selectbox(
            "Filtrar Feed de Alertas",
            [
                "Todos os alertas",
                "Apenas não lidos",
                "Promoção / Preço",
                "Estoque Baixo / Zerado",
                "Pico de Vendas",
                "Catálogo / Full",
            ],
            key=f"notif_feed_filter_{usuario}",
        )

        df_feed = df_notif_hist.copy()
        df_feed["Data_Hora_Sort"] = pd.to_datetime(
            df_feed.get("Data_Hora", ""), errors="coerce"
        )
        df_feed = df_feed.sort_values(
            ["Data_Hora_Sort", "Data_Hora"], ascending=[False, False]
        )

        if filtro_feed == "Apenas não lidos":
            df_feed = df_feed[df_feed["Lida"].apply(lambda x: normalize_text(x) != "sim")]
        elif filtro_feed == "Promoção / Preço":
            df_feed = df_feed[
                df_feed["Tipo_Alerta"].apply(
                    lambda x: "promocao" in normalize_text(x) or "preco" in normalize_text(x)
                )
            ]
        elif filtro_feed == "Estoque Baixo / Zerado":
            df_feed = df_feed[
                df_feed["Tipo_Alerta"].apply(lambda x: "estoque" in normalize_text(x))
            ]
        elif filtro_feed == "Pico de Vendas":
            df_feed = df_feed[
                df_feed["Tipo_Alerta"].apply(
                    lambda x: "pico" in normalize_text(x) or "venda" in normalize_text(x)
                )
            ]
        elif filtro_feed == "Catálogo / Full":
            df_feed = df_feed[
                df_feed["Tipo_Alerta"].apply(
                    lambda x: "catalogo" in normalize_text(x) or "full" in normalize_text(x)
                )
            ]

        if df_feed.empty:
            st.info("Nenhum alerta corresponde ao filtro selecionado.")
            return

        for _, row in df_feed.head(60).iterrows():
            tipo_alerta = str(row.get("Tipo_Alerta", "Alerta")).strip()
            concorrente = str(row.get("Concorrente", "Concorrente")).strip()
            produto = str(row.get("Produto", "")).strip()
            mensagem = str(row.get("Mensagem", "")).strip()
            data_hora = str(row.get("Data_Hora", "")).strip()
            is_lida = normalize_text(row.get("Lida", "")) == "sim"

            card_cls, badge_cls, icon = _resolve_alert_card_style(tipo_alerta)
            status_badge = (
                '<span class="badge badge-neutral">Lida</span>'
                if is_lida
                else '<span class="badge badge-info">● Não lida</span>'
            )

            st.markdown(
                f"""
                <div class="notif-card {card_cls}">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.45rem;">
                        <div style="display:flex; align-items:center; gap:0.45rem; flex-wrap:wrap;">
                            <span class="badge {badge_cls}">{icon} {html_lib.escape(tipo_alerta)}</span>
                            <span style="font-size:0.80rem; font-weight:700; color:#E2E8F0;">{html_lib.escape(concorrente)}</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:0.45rem;">
                            {status_badge}
                            <span style="font-size:0.75rem; color:#94A3B8;">{html_lib.escape(data_hora)}</span>
                        </div>
                    </div>
                    <div style="font-size:0.92rem; font-weight:700; color:#F8FAFC; margin-bottom:0.32rem;">
                        {html_lib.escape(produto[:120])}
                    </div>
                    <div style="font-size:0.85rem; color:#CBD5E1; line-height:1.45;">
                        {html_lib.escape(mensagem)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ==============================================================================
# ORQUESTRADOR PRINCIPAL
# ==============================================================================


def main() -> None:
    st.set_page_config(
        page_title="Radar Pet Pro — E-commerce Pet",
        page_icon="🐾",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_executive_css()

    if "usuario" not in st.session_state or not st.session_state["usuario"]:
        render_login_screen()
        return

    usuario = str(st.session_state["usuario"])
    nome_exibicao = str(st.session_state.get("nome_exibicao") or usuario)

    if st.session_state.pop("jump_to_notif", False):
        st.session_state["sidebar_nav_tab"] = "🔔 Notificações & Alertas"

    # Carregamento com cache de 5 minutos e isolamento estrito por usuário
    raw_config = load_sheet_tab_cached(TAB_CONFIGURACAO)
    raw_history = load_sheet_tab_cached(TAB_HISTORICO_HORA)
    raw_lojas = load_sheet_tab_cached(TAB_LOJAS_MONITORADAS)
    raw_catalogo_lojas = load_sheet_tab_cached(TAB_CATALOGO_LOJAS)
    raw_notif_cfg = load_sheet_tab_cached(TAB_CONFIG_NOTIFICACOES)
    raw_notif_hist = load_sheet_tab_cached(TAB_HISTORICO_NOTIFICACOES)

    df_cfg = filter_user_dataframe(raw_config, usuario)
    df_hist = prepare_history_dataframe(raw_history, usuario)
    df_lojas = filter_user_dataframe(raw_lojas, usuario)
    df_catalogo_lojas = prepare_store_catalog_dataframe(raw_catalogo_lojas, usuario)
    df_notif_cfg = filter_user_dataframe(raw_notif_cfg, usuario)
    df_notif_hist = filter_user_dataframe(raw_notif_hist, usuario)

    unread_notif_count = _count_unread_notifications(df_notif_hist)
    unread_sidebar_html = (
        f'<div style="margin-top:0.45rem;"><span class="badge badge-info">🔔 {unread_notif_count} alerta(s) não lido(s)</span></div>'
        if unread_notif_count > 0
        else '<div style="margin-top:0.45rem; font-size:0.75rem; color:#64748B;">🔔 Sem alertas pendentes</div>'
    )

    with st.sidebar:
        st.markdown(
            f"""
            <div class="glass-card" style="padding: 1rem 1.1rem; margin-bottom: 1rem;">
                <div style="font-size:1.15rem; font-weight:800; color:#F8FAFC;">🕵️ Radar Pet Pro</div>
                <div style="font-size:0.8rem; color:#38BDF8; margin-top:0.15rem;">Sessão Isolada</div>
                <div style="font-size:0.9rem; color:#E2E8F0; font-weight:600; margin-top:0.55rem;">
                    👤 {html_lib.escape(nome_exibicao)}
                </div>
                <div style="font-size:0.75rem; color:#94A3B8;">@{html_lib.escape(usuario)}</div>
                {unread_sidebar_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

        aba_selecionada = st.radio(
            "Navegação Executiva",
            [
                "⚡ Batalha de Horário de Pico",
                "🎯 Comparativo Direto & Alertas",
                "🔎 Radar Nicho Pet (Minerador)",
                "🧮 Calculadora de Precificação 2026",
                "🏭 Fábrica de Anúncios",
                "🚑 Resgate de Anúncio",
                "🏪 Raio-X de Lojas (Minha Loja vs. Concorrentes)",
                "🏆 Ranking Geral & Batalha",
                "🔔 Notificações & Alertas",
            ],
            key="sidebar_nav_tab",
            label_visibility="collapsed",
        )

        st.markdown("---")
        c_ref, c_out = st.columns(2)
        if c_ref.button("🔄 Atualizar", use_container_width=True, help="Limpa cache e relê a planilha"):
            st.cache_data.clear()
            st.rerun()
        if c_out.button("🚪 Sair", use_container_width=True):
            for key in ["usuario", "nome_exibicao", "sidebar_nav_tab"]:
                st.session_state.pop(key, None)
            st.rerun()

    # Banner sutil no topo de qualquer aba quando houver alertas com Lida == 'Nao'
    render_top_notifications_banner(df_notif_hist, aba_selecionada)

    if aba_selecionada == "⚡ Batalha de Horário de Pico":
        render_batalha_horario_pico(usuario, nome_exibicao, df_hist, df_cfg)
    elif aba_selecionada == "🎯 Comparativo Direto & Alertas":
        render_comparativo_alertas(df_hist)
    elif aba_selecionada == "🔎 Radar Nicho Pet (Minerador)":
        render_radar_nicho_pet()
    elif aba_selecionada == "🧮 Calculadora de Precificação 2026":
        render_calculadora_precificacao(usuario)
    elif aba_selecionada == "🏭 Fábrica de Anúncios":
        render_fabrica_anuncios()
    elif aba_selecionada == "🚑 Resgate de Anúncio":
        render_resgate_anuncio()
    elif aba_selecionada == "🏪 Raio-X de Lojas (Minha Loja vs. Concorrentes)":
        render_raiox_lojas(usuario, df_lojas, df_catalogo_lojas)
    elif aba_selecionada == "🏆 Ranking Geral & Batalha":
        render_ranking_geral(usuario, df_hist, df_catalogo_lojas)
    elif aba_selecionada == "🔔 Notificações & Alertas":
        render_notificacoes(usuario, nome_exibicao, df_notif_cfg, df_notif_hist)


if __name__ == "__main__":
    main()

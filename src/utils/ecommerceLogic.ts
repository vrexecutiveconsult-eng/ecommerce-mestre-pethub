export type ModuleId =
  | 'batalha'
  | 'comparativo'
  | 'radar'
  | 'calculadora'
  | 'fabrica'
  | 'resgate'
  | 'ranking';

export type TrendDirection = 'up' | 'stable' | 'down';

export type ScalabilityLevel = 'Muito Escalável' | 'Média' | 'Não Escalável';

export interface RankingSeedCompetitor {
  id: string;
  lojaConcorrente: string;
  marketplace: MarketplaceName;
  titulo: string;
  url: string;
  preco: number;
  estoqueAtual: number;
  vendasPeriodo: number;
  full: boolean;
  catalogo: boolean;
  nota: number;
  sparklineSeries: number[];
}

export interface RankingEntry {
  id: string;
  posicao: number;
  lojaConcorrente: string;
  marketplace: MarketplaceName;
  titulo: string;
  url: string;
  preco: number;
  estoqueAtual: number;
  vendasPeriodo: number;
  faturamentoEstimado: number;
  full: boolean;
  catalogo: boolean;
  nota: number;
  tendencia: TrendDirection;
  escalabilidade: ScalabilityLevel;
  sparklineSeries: number[];
  matchedMyListing: MonitoredListing | null;
  similarityPct: number;
  battleScore: number | null;
}

export type MarketplaceName =
  | 'Mercado Livre'
  | 'Amazon'
  | 'Shopee'
  | 'Magalu'
  | 'Petz'
  | 'Cobasi';

export type Platform2026 =
  | 'Mercado Livre Clássico (12%)'
  | 'Mercado Livre Premium (17%)'
  | 'Shopee CNPJ'
  | 'Shopee CPF'
  | 'Magalu';

export interface MonitoredListing {
  id: string;
  tipo: 'Meu Anuncio' | 'Concorrente';
  grupoProduto: string;
  marketplace: MarketplaceName;
  url: string;
  titulo: string;
  preco: number;
  estoqueAtual: number;
  vendasHoje: number;
  horarioPico: string;
  full: boolean;
  catalogo: boolean;
  nota: number;
  meuCusto: number;
  impostoPct: number;
  comissaoPct: number;
  taxaFixa: number;
  freteEstimado: number;
  vendasPorHora: number[]; // 24 posições (00h..23h)
}

export interface PricingDefaults {
  comissaoPct: number;
  taxaFixa: number;
  marketplace: MarketplaceName;
}

export interface PricingBreakdown {
  comissaoRs: number;
  impostoRs: number;
  lucroLiquido: number;
  margemPct: number;
  roiPct: number;
  precoEquilibrio: number;
}

export interface ExecutiveKpis {
  faturamentoHoje: number;
  lucroLiquido: number;
  margemMediaPct: number;
  ticketMedio: number;
  totalVendas: number;
  vendasConcorrentes: number;
}

export interface HourlyPoint {
  hora: string;
  meuAnuncio: number;
  concorrente: number;
}

export interface ComparativeRow {
  grupoProduto: string;
  marketplace: MarketplaceName;
  meuPreco: number;
  concPreco: number;
  meuEstoque: number;
  concEstoque: number;
  vendasMeu: number;
  vendasConc: number;
  horarioPico: string;
  meuFull: boolean;
  concFull: boolean;
  meuCatalogo: boolean;
  concCatalogo: boolean;
  alertaTexto: string;
  alertaNivel: 'oportunidade' | 'atencao' | 'critico' | 'estavel';
}

export function formatBrl(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(Number.isFinite(value) ? value : 0);
}

export function computePlatformDefaults2026(
  plataforma: Platform2026,
  precoVenda: number
): PricingDefaults {
  switch (plataforma) {
    case 'Mercado Livre Clássico (12%)':
      return {
        comissaoPct: 12,
        taxaFixa: precoVenda > 0 && precoVenda < 79 ? 6 : 0,
        marketplace: 'Mercado Livre',
      };
    case 'Mercado Livre Premium (17%)':
      return {
        comissaoPct: 17,
        taxaFixa: precoVenda > 0 && precoVenda < 79 ? 6 : 0,
        marketplace: 'Mercado Livre',
      };
    case 'Shopee CNPJ': {
      if (precoVenda <= 79.99) {
        return { comissaoPct: 20, taxaFixa: 4.5, marketplace: 'Shopee' };
      }
      const taxaBase =
        precoVenda < 100 ? 16 : precoVenda < 200 ? 20 : 26;
      return { comissaoPct: 14, taxaFixa: taxaBase, marketplace: 'Shopee' };
    }
    case 'Shopee CPF': {
      if (precoVenda <= 79.99) {
        return { comissaoPct: 20, taxaFixa: 7.5, marketplace: 'Shopee' };
      }
      const taxaBase =
        precoVenda < 100 ? 16 : precoVenda < 200 ? 20 : 26;
      return {
        comissaoPct: 14,
        taxaFixa: taxaBase + 3,
        marketplace: 'Shopee',
      };
    }
    case 'Magalu':
      return { comissaoPct: 18, taxaFixa: 5, marketplace: 'Magalu' };
  }
}

export function calculatePricingBreakdown(params: {
  precoVenda: number;
  meuCusto: number;
  impostoPct: number;
  comissaoPct: number;
  taxaFixa: number;
  freteEstimado: number;
}): PricingBreakdown {
  const {
    precoVenda,
    meuCusto,
    impostoPct,
    comissaoPct,
    taxaFixa,
    freteEstimado,
  } = params;

  const comissaoRs = precoVenda * (comissaoPct / 100);
  const impostoRs = precoVenda * (impostoPct / 100);
  const lucroLiquido =
    precoVenda - meuCusto - impostoRs - comissaoRs - taxaFixa - freteEstimado;
  const margemPct = precoVenda > 0 ? (lucroLiquido / precoVenda) * 100 : 0;
  const roiPct = meuCusto > 0 ? (lucroLiquido / meuCusto) * 100 : 0;

  const denom = 1 - (impostoPct + comissaoPct) / 100;
  const precoEquilibrio =
    denom > 0 ? (meuCusto + taxaFixa + freteEstimado) / denom : 0;

  return {
    comissaoRs: Number(comissaoRs.toFixed(2)),
    impostoRs: Number(impostoRs.toFixed(2)),
    lucroLiquido: Number(lucroLiquido.toFixed(2)),
    margemPct: Number(margemPct.toFixed(2)),
    roiPct: Number(roiPct.toFixed(2)),
    precoEquilibrio: Number(precoEquilibrio.toFixed(2)),
  };
}

export function calculateKpis(
  listings: MonitoredListing[],
  grupoFiltro: string = 'Todos'
): ExecutiveKpis {
  const filtered =
    grupoFiltro === 'Todos'
      ? listings
      : listings.filter((item) => item.grupoProduto === grupoFiltro);

  const meus = filtered.filter((item) => item.tipo === 'Meu Anuncio');
  const conc = filtered.filter((item) => item.tipo === 'Concorrente');

  let faturamentoHoje = 0;
  let lucroLiquido = 0;
  let totalVendas = 0;

  for (const item of meus) {
    const vendas = item.vendasHoje;
    const fatItem = vendas * item.preco;
    const breakdown = calculatePricingBreakdown({
      precoVenda: item.preco,
      meuCusto: item.meuCusto,
      impostoPct: item.impostoPct,
      comissaoPct: item.comissaoPct,
      taxaFixa: item.taxaFixa,
      freteEstimado: item.freteEstimado,
    });
    faturamentoHoje += fatItem;
    lucroLiquido += vendas * breakdown.lucroLiquido;
    totalVendas += vendas;
  }

  const vendasConcorrentes = conc.reduce(
    (acc, item) => acc + item.vendasHoje,
    0
  );
  const ticketMedio = totalVendas > 0 ? faturamentoHoje / totalVendas : 0;
  const margemMediaPct =
    faturamentoHoje > 0 ? (lucroLiquido / faturamentoHoje) * 100 : 0;

  return {
    faturamentoHoje: Number(faturamentoHoje.toFixed(2)),
    lucroLiquido: Number(lucroLiquido.toFixed(2)),
    margemMediaPct: Number(margemMediaPct.toFixed(1)),
    ticketMedio: Number(ticketMedio.toFixed(2)),
    totalVendas,
    vendasConcorrentes,
  };
}

export function buildHourlyBattleSeries(
  listings: MonitoredListing[],
  grupoFiltro: string = 'Todos'
): HourlyPoint[] {
  const filtered =
    grupoFiltro === 'Todos'
      ? listings
      : listings.filter((item) => item.grupoProduto === grupoFiltro);

  return Array.from({ length: 24 }, (_, hour) => {
    let meuAnuncio = 0;
    let concorrente = 0;
    for (const item of filtered) {
      const qty = item.vendasPorHora[hour] ?? 0;
      if (item.tipo === 'Meu Anuncio') {
        meuAnuncio += qty;
      } else {
        concorrente += qty;
      }
    }
    return {
      hora: `${String(hour).padStart(2, '0')}h`,
      meuAnuncio,
      concorrente,
    };
  });
}

export function buildComparativeRows(
  listings: MonitoredListing[]
): ComparativeRow[] {
  const grupos = Array.from(
    new Set(listings.map((item) => item.grupoProduto))
  ).sort();

  return grupos.map((grupo) => {
    const groupItems = listings.filter((i) => i.grupoProduto === grupo);
    const meu = groupItems.find((i) => i.tipo === 'Meu Anuncio');
    const concList = groupItems.filter((i) => i.tipo === 'Concorrente');
    const conc =
      concList.sort((a, b) => a.preco - b.preco)[0] ?? concList[0];

    const meuPreco = meu?.preco ?? 0;
    const concPreco = conc?.preco ?? 0;
    const meuEstoque = meu?.estoqueAtual ?? 0;
    const concEstoque = concList.reduce((acc, i) => acc + i.estoqueAtual, 0);
    const vendasMeu = meu?.vendasHoje ?? 0;
    const vendasConc = concList.reduce((acc, i) => acc + i.vendasHoje, 0);

    let alertaTexto = 'Equilíbrio competitivo';
    let alertaNivel: ComparativeRow['alertaNivel'] = 'estavel';

    if (conc && concEstoque === 0) {
      alertaTexto = 'Concorrente zerou estoque — oportunidade de subir preço';
      alertaNivel = 'oportunidade';
    } else if (meu && meuEstoque === 0) {
      alertaTexto = 'Seu estoque zerou — reposição urgente';
      alertaNivel = 'critico';
    } else if (conc && conc.full && meu && !meu.full) {
      alertaTexto = 'Concorrente no FULL e você fora do FULL';
      alertaNivel = 'critico';
    } else if (meu && meuEstoque > 0 && meuEstoque <= 5) {
      alertaTexto = `Estoque baixo (${meuEstoque} un.)`;
      alertaNivel = 'atencao';
    } else if (meuPreco > 0 && concPreco > 0) {
      const diffPct = ((meuPreco - concPreco) / concPreco) * 100;
      if (diffPct > 5) {
        alertaTexto = `Seu preço ${diffPct.toFixed(1)}% acima do concorrente`;
        alertaNivel = 'atencao';
      } else if (diffPct < -5) {
        alertaTexto = `Vantagem de preço (${diffPct.toFixed(1)}%)`;
        alertaNivel = 'oportunidade';
      }
    }

    return {
      grupoProduto: grupo,
      marketplace: meu?.marketplace ?? conc?.marketplace ?? 'Mercado Livre',
      meuPreco,
      concPreco,
      meuEstoque,
      concEstoque,
      vendasMeu,
      vendasConc,
      horarioPico: meu?.horarioPico ?? conc?.horarioPico ?? '—',
      meuFull: meu?.full ?? false,
      concFull: conc?.full ?? false,
      meuCatalogo: meu?.catalogo ?? false,
      concCatalogo: conc?.catalogo ?? false,
      alertaTexto,
      alertaNivel,
    };
  });
}

export function generateSeoTitles(
  produto: string,
  marca: string,
  beneficioChave: string
): string[] {
  const base = produto.trim() || 'Produto Pet';
  const brand = marca.trim();
  const benefit = beneficioChave.trim() || 'Alta Absorção';

  const candidates = [
    `${base} ${brand} ${benefit}`.trim(),
    `${base} Original ${brand} Envio Imediato`.trim(),
    `${base} ${benefit} Para Cães e Gatos`.trim(),
    `${base} ${brand} Uso Diário Nota Fiscal`.trim(),
    `${base} Premium ${benefit} Qualidade Pet`.trim(),
  ];

  return candidates.map((title) => {
    const clean = title.replace(/\s+/g, ' ').trim();
    if (clean.length <= 60) return clean;
    const sliced = clean.slice(0, 60);
    const lastSpace = sliced.lastIndexOf(' ');
    return (lastSpace > 30 ? sliced.slice(0, lastSpace) : sliced).trim();
  });
}

export function analyzeListingDiagnostic(params: {
  titulo: string;
  preco: number;
  fotos: number;
  visitas30d: number;
  vendas30d: number;
}): {
  taxaConversao: number;
  gargalo: 'Tráfego' | 'Conversão' | 'Equilibrado';
  resumo: string;
  acoes: string[];
} {
  const { titulo, fotos, visitas30d, vendas30d } = params;
  const taxaConversao =
    visitas30d > 0 ? Number(((vendas30d / visitas30d) * 100).toFixed(2)) : 0;

  let gargalo: 'Tráfego' | 'Conversão' | 'Equilibrado' = 'Equilibrado';
  let resumo =
    'Desempenho dentro da média do nicho Pet; otimizações finas podem escalar margem.';

  if (visitas30d < 200) {
    gargalo = 'Tráfego';
    resumo =
      'Baixo volume de visitas nos últimos 30 dias indica falha de indexação SEO no título ou ausência de envio FULL.';
  } else if (taxaConversao < 1.8) {
    gargalo = 'Conversão';
    resumo =
      'O anúncio atrai cliques, mas converte abaixo de 1,8% por falta de prova visual, quebra de objeções ou preço fora da faixa.';
  }

  const acoes: string[] = [];
  if (titulo.trim().length < 40) {
    acoes.push(
      'Expandir o título para 52–60 caracteres iniciando pela palavra-chave principal de busca.'
    );
  } else {
    acoes.push(
      'Reordenar as primeiras 3 palavras do título para priorizar termos de busca exata dos compradores.'
    );
  }

  if (fotos < 6) {
    acoes.push(
      `Aumentar de ${fotos} para pelo menos 7 fotos incluindo infográfico de medidas e selo de garantia.`
    );
  } else {
    acoes.push(
      'Substituir a foto principal por fundo branco puro com ângulo de embalagem + produto em destaque.'
    );
  }

  acoes.push(
    'Inserir FAQ de 5 perguntas na descrição respondendo tamanho, rendimento e envio imediato.'
  );

  return { taxaConversao, gargalo, resumo, acoes };
}

function normalizeRankingText(value: string): string {
  return value
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

const RANKING_STOPWORDS = new Set([
  'de',
  'da',
  'do',
  'das',
  'dos',
  'para',
  'com',
  'sem',
  'em',
  'na',
  'no',
  'e',
  'ou',
  'a',
  'o',
  'as',
  'os',
  'um',
  'uma',
  'por',
  'kit',
]);

function extractRankingTokens(text: string): Set<string> {
  const matches = normalizeRankingText(text).match(/[a-z0-9]+/g) ?? [];
  const tokens = new Set<string>();
  for (const tok of matches) {
    if (tok.length > 1 && !RANKING_STOPWORDS.has(tok)) {
      tokens.add(tok);
    }
  }
  return tokens;
}

export function getSparklineColor(trend: TrendDirection): string {
  if (trend === 'up') return '#00E676';
  if (trend === 'down') return '#FF5252';
  return '#FFD600';
}

export function inferListingTrend(series: number[]): TrendDirection {
  if (series.length < 2) {
    return series.length === 1 && series[0] >= 3 ? 'up' : 'stable';
  }
  const prev = series.slice(0, -1);
  const prevAvg = prev.reduce((acc, n) => acc + n, 0) / prev.length;
  const last = series[series.length - 1];

  if (prevAvg === 0) {
    return last > 0 ? 'up' : 'stable';
  }
  if (last >= prevAvg * 1.15 && last > 0) {
    return 'up';
  }
  if (last <= prevAvg * 0.8 || (last === 0 && prevAvg >= 1.5)) {
    return 'down';
  }
  return 'stable';
}

export function inferListingScalability(
  vendasPeriodo: number,
  trend: TrendDirection
): ScalabilityLevel {
  if (
    (trend === 'up' && vendasPeriodo >= 10) ||
    (vendasPeriodo >= 20 && trend !== 'down')
  ) {
    return 'Muito Escalável';
  }
  if (trend !== 'down' && vendasPeriodo >= 5) {
    return 'Média';
  }
  return 'Não Escalável';
}

export function computeListingTitleSimilarity(
  titleA: string,
  titleB: string
): number {
  const normA = normalizeRankingText(titleA);
  const normB = normalizeRankingText(titleB);
  if (!normA || !normB) return 0;

  const toksA = extractRankingTokens(normA);
  const toksB = extractRankingTokens(normB);

  let jaccard = 0;
  let overlapMin = 0;
  if (toksA.size > 0 && toksB.size > 0) {
    let inter = 0;
    for (const tok of toksA) {
      if (toksB.has(tok)) inter += 1;
    }
    const union = toksA.size + toksB.size - inter;
    jaccard = union > 0 ? inter / union : 0;
    overlapMin = inter / Math.min(toksA.size, toksB.size);
  }

  // Similaridade de bigramas (Dice) para captar radicais próximos
  const bigrams = (s: string): string[] => {
    const out: string[] = [];
    for (let i = 0; i < s.length - 1; i++) {
      out.push(s.slice(i, i + 2));
    }
    return out;
  };
  const bgA = bigrams(normA);
  const bgB = bigrams(normB);
  let dice = 0;
  if (bgA.length > 0 && bgB.length > 0) {
    const counts = new Map<string, number>();
    for (const b of bgA) counts.set(b, (counts.get(b) ?? 0) + 1);
    let matches = 0;
    for (const b of bgB) {
      const c = counts.get(b) ?? 0;
      if (c > 0) {
        matches += 1;
        counts.set(b, c - 1);
      }
    }
    dice = (2 * matches) / (bgA.length + bgB.length);
  }

  const blended = 0.45 * jaccard + 0.35 * overlapMin + 0.2 * dice;
  return Number(Math.max(jaccard, dice, blended).toFixed(4));
}

export function calculateBattleComparisonScore(
  myAd: MonitoredListing,
  compAd: {
    preco: number;
    full: boolean;
    catalogo: boolean;
    nota: number;
    vendasPeriodo: number;
  }
): number {
  let pricePts = 1.0;
  if (myAd.preco > 0 && compAd.preco > 0) {
    if (myAd.preco <= compAd.preco) {
      pricePts = 2.5;
    } else {
      const diffRatio = (myAd.preco - compAd.preco) / compAd.preco;
      pricePts = Math.max(0.3, 2.5 * (1 - Math.min(1, diffRatio * 2)));
    }
  }

  let fullPts = 1.0;
  if (myAd.full && !compAd.full) fullPts = 2.0;
  else if (myAd.full && compAd.full) fullPts = 1.6;
  else if (!myAd.full && compAd.full) fullPts = 0.2;

  let catPts = 0.8;
  if (myAd.catalogo && !compAd.catalogo) catPts = 1.5;
  else if (myAd.catalogo && compAd.catalogo) catPts = 1.2;
  else if (!myAd.catalogo && compAd.catalogo) catPts = 0.2;

  const myNota = Math.min(5, Math.max(0, myAd.nota));
  const notaPts =
    myNota > 0
      ? (myNota / 5) * 1.6 + (myNota >= compAd.nota ? 0.4 : 0)
      : 0.7;

  const denomVendas = myAd.vendasHoje + compAd.vendasPeriodo;
  const vendasPts =
    denomVendas > 0
      ? Math.min(2.0, (myAd.vendasHoje / denomVendas) * 2.6)
      : 1.0;

  const total = pricePts + fullPts + catPts + notaPts + vendasPts;
  return Number(Math.min(10, Math.max(0, total)).toFixed(1));
}

function buildRecentSparklineFromHourly(vendasPorHora: number[]): number[] {
  // Agrupa blocos de 4h das 00h às 23h em 6 pontos recentes para o sparkline
  const buckets: number[] = [];
  for (let i = 0; i < 24; i += 4) {
    const sum = vendasPorHora
      .slice(i, i + 4)
      .reduce((acc, v) => acc + (v ?? 0), 0);
    buckets.push(sum);
  }
  return buckets;
}

export function buildGeneralRankingRows(
  listings: MonitoredListing[],
  storeCompetitors: RankingSeedCompetitor[] = []
): RankingEntry[] {
  const myListings = listings.filter((item) => item.tipo === 'Meu Anuncio');
  const compListings = listings.filter((item) => item.tipo === 'Concorrente');

  const rawEntries: Omit<
    RankingEntry,
    'posicao' | 'matchedMyListing' | 'similarityPct' | 'battleScore'
  >[] = [];
  const seenTitles = new Set<string>();

  for (const seed of storeCompetitors) {
    const normT = normalizeRankingText(seed.titulo);
    seenTitles.add(normT);
    const trend = inferListingTrend(seed.sparklineSeries);
    rawEntries.push({
      id: seed.id,
      lojaConcorrente: seed.lojaConcorrente,
      marketplace: seed.marketplace,
      titulo: seed.titulo,
      url: seed.url,
      preco: seed.preco,
      estoqueAtual: seed.estoqueAtual,
      vendasPeriodo: seed.vendasPeriodo,
      faturamentoEstimado: Number((seed.vendasPeriodo * seed.preco).toFixed(2)),
      full: seed.full,
      catalogo: seed.catalogo,
      nota: seed.nota,
      tendencia: trend,
      escalabilidade: inferListingScalability(seed.vendasPeriodo, trend),
      sparklineSeries: seed.sparklineSeries,
    });
  }

  for (const item of compListings) {
    const normT = normalizeRankingText(item.titulo);
    if (seenTitles.has(normT)) continue;
    seenTitles.add(normT);

    const spark = buildRecentSparklineFromHourly(item.vendasPorHora);
    const trend = inferListingTrend(spark);
    rawEntries.push({
      id: item.id,
      lojaConcorrente: `Vitrine ${item.grupoProduto}`,
      marketplace: item.marketplace,
      titulo: item.titulo,
      url: item.url,
      preco: item.preco,
      estoqueAtual: item.estoqueAtual,
      vendasPeriodo: item.vendasHoje,
      faturamentoEstimado: Number((item.vendasHoje * item.preco).toFixed(2)),
      full: item.full,
      catalogo: item.catalogo,
      nota: item.nota,
      tendencia: trend,
      escalabilidade: inferListingScalability(item.vendasHoje, trend),
      sparklineSeries: spark,
    });
  }

  rawEntries.sort(
    (a, b) =>
      b.vendasPeriodo - a.vendasPeriodo ||
      b.faturamentoEstimado - a.faturamentoEstimado ||
      b.preco - a.preco
  );

  return rawEntries.map((entry, idx) => {
    let bestMy: MonitoredListing | null = null;
    let bestSim = 0;

    for (const mine of myListings) {
      const sim = computeListingTitleSimilarity(entry.titulo, mine.titulo);
      if (sim >= 0.45 && sim > bestSim) {
        bestSim = sim;
        bestMy = mine;
      }
    }

    return {
      ...entry,
      posicao: idx + 1,
      matchedMyListing: bestMy,
      similarityPct: bestMy ? Number((bestSim * 100).toFixed(1)) : 0,
      battleScore: bestMy
        ? calculateBattleComparisonScore(bestMy, entry)
        : null,
    };
  });
}


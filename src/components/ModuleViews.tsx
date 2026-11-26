import { useState } from 'react';
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Copy,
  Download,
  Search,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import {
  analyzeListingDiagnostic,
  buildComparativeRows,
  buildHourlyBattleSeries,
  calculateKpis,
  calculatePricingBreakdown,
  computePlatformDefaults2026,
  formatBrl,
  generateSeoTitles,
  MarketplaceName,
  MonitoredListing,
  Platform2026,
} from '../utils/ecommerceLogic';
import { PET_RADAR_SEED } from '../data/petSeedData';
import { HourlyBattleChart } from './HourlyBattleChart';
import { MarginGauge } from './MarginGauge';

const PLATFORMS: Platform2026[] = [
  'Mercado Livre Clássico (12%)',
  'Mercado Livre Premium (17%)',
  'Shopee CNPJ',
  'Shopee CPF',
  'Magalu',
];

interface PeakBattleViewProps {
  listings: MonitoredListing[];
  onOpenAddModal: () => void;
}

export function PeakBattleView({
  listings,
  onOpenAddModal,
}: PeakBattleViewProps) {
  const [selectedGroup, setSelectedGroup] = useState<string>('Todos');

  const groups = [
    'Todos',
    ...Array.from(new Set(listings.map((item) => item.grupoProduto))).sort(),
  ];

  const kpis = calculateKpis(listings, selectedGroup);
  const hourlySeries = buildHourlyBattleSeries(listings, selectedGroup);

  const handleExportCsv = () => {
    const headers = [
      'Tipo',
      'Grupo_Produto',
      'Marketplace',
      'Titulo',
      'Preco',
      'Estoque_Atual',
      'Vendas_Hoje',
    ];
    const rows = listings
      .filter((l) => selectedGroup === 'Todos' || l.grupoProduto === selectedGroup)
      .map((l) => [
        l.tipo,
        l.grupoProduto,
        l.marketplace,
        `"${l.titulo.replace(/"/g, '""')}"`,
        l.preco.toFixed(2),
        String(l.estoqueAtual),
        String(l.vendasHoje),
      ]);
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'relatorio-ecommerce-mestre.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  if (listings.length === 0) {
    return (
      <div className="glass-card rounded-2xl p-10 text-center">
        <h2 className="font-display text-xl font-bold text-slate-100">
          Nenhum anúncio monitorado ainda
        </h2>
        <p className="mx-auto mt-2 max-w-md text-sm text-slate-400">
          Cadastre o link do seu anúncio ou concorrente para acompanhar vendas
          horárias, estoque e lucro líquido.
        </p>
        <button
          type="button"
          onClick={onOpenAddModal}
          className="mt-5 inline-flex min-h-[42px] items-center gap-2 rounded-xl bg-sky-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 whitespace-nowrap"
        >
          Adicionar Primeiro Anúncio
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <label
            htmlFor="grupo-filter"
            className="text-sm font-medium text-slate-300"
          >
            Grupo de Produto
          </label>
          <select
            id="grupo-filter"
            value={selectedGroup}
            onChange={(e) => setSelectedGroup(e.target.value)}
            className="min-h-[40px] rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 py-2 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
          >
            {groups.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          onClick={handleExportCsv}
          className="inline-flex min-h-[40px] items-center gap-2 rounded-xl border border-[#334155] bg-slate-900/70 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-sky-400/60 hover:text-white whitespace-nowrap shrink-0"
        >
          <Download className="h-4 w-4 text-sky-400" />
          Exportar Relatório
        </button>
      </div>

      {/* 4 KPIs Glassmorphism */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="glass-card glass-card-interactive rounded-2xl p-6">
          <div className="text-xs font-medium text-slate-400">
            Faturamento Hoje
          </div>
          <div className="font-tabular mt-2 text-2xl font-bold text-slate-50">
            {formatBrl(kpis.faturamentoHoje)}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Meus anúncios ativos · Hoje
          </div>
        </div>

        <div className="glass-card glass-card-interactive rounded-2xl p-6">
          <div className="text-xs font-medium text-slate-400">
            Lucro Líquido
          </div>
          <div
            className={`font-tabular mt-2 text-2xl font-bold ${
              kpis.lucroLiquido >= 0 ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {formatBrl(kpis.lucroLiquido)}
          </div>
          <div className="mt-2 font-tabular text-xs text-slate-300">
            Margem líquida: {kpis.margemMediaPct.toFixed(1)}%
          </div>
        </div>

        <div className="glass-card glass-card-interactive rounded-2xl p-6">
          <div className="text-xs font-medium text-slate-400">
            Ticket Médio
          </div>
          <div className="font-tabular mt-2 text-2xl font-bold text-slate-50">
            {formatBrl(kpis.ticketMedio)}
          </div>
          <div className="mt-2 text-xs text-slate-400">
            Receita média por pedido
          </div>
        </div>

        <div className="glass-card glass-card-interactive rounded-2xl p-6">
          <div className="text-xs font-medium text-slate-400">
            Total Vendas
          </div>
          <div className="font-tabular mt-2 text-2xl font-bold text-slate-50">
            {kpis.totalVendas} un.
          </div>
          <div className="mt-2 font-tabular text-xs text-slate-400">
            Concorrentes: {kpis.vendasConcorrentes} un.
          </div>
        </div>
      </div>

      <HourlyBattleChart data={hourlySeries} />
    </div>
  );
}

export function ComparativeAlertsView({
  listings,
}: {
  listings: MonitoredListing[];
}) {
  const [search, setSearch] = useState('');
  const [filterAlert, setFilterAlert] = useState<'todos' | 'alertas'>('todos');

  const rows = buildComparativeRows(listings).filter((row) => {
    const matchesSearch = row.grupoProduto
      .toLowerCase()
      .includes(search.trim().toLowerCase());
    const matchesFilter =
      filterAlert === 'todos' || row.alertaNivel !== 'estavel';
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6">
      <div className="glass-card flex flex-wrap items-center justify-between gap-4 rounded-2xl p-5">
        <div className="relative min-w-[240px] flex-1">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filtrar por grupo de produto..."
            aria-label="Filtrar por grupo de produto"
            className="min-h-[40px] w-full rounded-xl border border-[#334155] bg-slate-900/75 pl-10 pr-4 text-sm text-slate-100 placeholder:text-slate-500 focus:border-sky-400 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-1 rounded-xl border border-[#334155] bg-slate-900/70 p-1">
          <button
            type="button"
            onClick={() => setFilterAlert('todos')}
            className={`min-h-[34px] rounded-lg px-3.5 py-1.5 text-xs font-semibold transition whitespace-nowrap ${
              filterAlert === 'todos'
                ? 'bg-sky-500 text-slate-950'
                : 'text-slate-300 hover:text-white'
            }`}
          >
            Todos os Grupos
          </button>
          <button
            type="button"
            onClick={() => setFilterAlert('alertas')}
            className={`min-h-[34px] rounded-lg px-3.5 py-1.5 text-xs font-semibold transition whitespace-nowrap ${
              filterAlert === 'alertas'
                ? 'bg-sky-500 text-slate-950'
                : 'text-slate-300 hover:text-white'
            }`}
          >
            Apenas Alertas Ativos
          </button>
        </div>
      </div>

      <div className="glass-card overflow-x-auto rounded-2xl p-2">
        <table className="w-full min-w-[820px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-[#334155] text-xs font-semibold text-slate-400">
              <th className="px-4 py-3.5">Grupo de Produto</th>
              <th className="px-4 py-3.5 text-right">Meu Preço</th>
              <th className="px-4 py-3.5 text-right">Concorrente</th>
              <th className="px-4 py-3.5 text-right">Vendas (Meu / Conc)</th>
              <th className="px-4 py-3.5">Pico</th>
              <th className="px-4 py-3.5">Full · Catálogo</th>
              <th className="px-4 py-3.5">Alerta Operacional</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#334155]/60">
            {rows.map((row) => (
              <tr
                key={row.grupoProduto}
                className="transition-colors hover:bg-slate-800/35"
              >
                <td className="px-4 py-3.5">
                  <div className="font-semibold text-slate-100">
                    {row.grupoProduto}
                  </div>
                  <div className="text-xs text-slate-400">
                    {row.marketplace} · Estoque: {row.meuEstoque} un.
                  </div>
                </td>
                <td className="font-tabular px-4 py-3.5 text-right font-semibold text-sky-300">
                  {row.meuPreco > 0 ? formatBrl(row.meuPreco) : '—'}
                </td>
                <td className="font-tabular px-4 py-3.5 text-right font-semibold text-amber-300">
                  {row.concPreco > 0 ? formatBrl(row.concPreco) : '—'}
                </td>
                <td className="font-tabular px-4 py-3.5 text-right text-slate-200">
                  {row.vendasMeu} / {row.vendasConc} un.
                </td>
                <td className="font-tabular px-4 py-3.5 text-slate-300">
                  {row.horarioPico}
                </td>
                <td className="px-4 py-3.5 text-xs text-slate-300">
                  {row.meuFull ? 'Full' : 'Normal'} ·{' '}
                  {row.meuCatalogo ? 'Catálogo' : 'Clássico'}
                </td>
                <td className="px-4 py-3.5 text-xs font-medium">
                  {row.alertaNivel === 'oportunidade' && (
                    <span className="inline-flex items-center gap-1.5 text-emerald-400">
                      <TrendingUp className="h-3.5 w-3.5 shrink-0" />
                      {row.alertaTexto}
                    </span>
                  )}
                  {row.alertaNivel === 'critico' && (
                    <span className="inline-flex items-center gap-1.5 text-rose-400">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                      {row.alertaTexto}
                    </span>
                  )}
                  {row.alertaNivel === 'atencao' && (
                    <span className="inline-flex items-center gap-1.5 text-amber-400">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                      {row.alertaTexto}
                    </span>
                  )}
                  {row.alertaNivel === 'estavel' && (
                    <span className="inline-flex items-center gap-1.5 text-slate-400">
                      <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                      {row.alertaTexto}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function PetRadarView() {
  const [query, setQuery] = useState('');

  const filtered = PET_RADAR_SEED.filter(
    (item) =>
      !query.trim() ||
      item.titulo.toLowerCase().includes(query.trim().toLowerCase()) ||
      item.keywordGroup.toLowerCase().includes(query.trim().toLowerCase())
  );

  const ticketMedio =
    filtered.length > 0
      ? filtered.reduce((acc, i) => acc + i.preco, 0) / filtered.length
      : 0;
  const pctFull =
    filtered.length > 0
      ? (filtered.filter((i) => i.full).length / filtered.length) * 100
      : 0;
  const pctCatalogo =
    filtered.length > 0
      ? (filtered.filter((i) => i.catalogo).length / filtered.length) * 100
      : 0;

  return (
    <div className="space-y-6">
      <div className="glass-card rounded-2xl p-5">
        <label
          htmlFor="radar-query"
          className="mb-2 block text-xs font-medium text-slate-400"
        >
          Buscar palavra-chave no nicho Pet
        </label>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            id="radar-query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ex: tapete higienico, racao golden, areia silica..."
            className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/75 pl-10 pr-4 text-sm text-slate-100 placeholder:text-slate-500 focus:border-sky-400 focus:outline-none"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="glass-card glass-card-interactive rounded-2xl p-6">
          <div className="text-xs font-medium text-slate-400">
            Ticket Médio Minerado
          </div>
          <div className="font-tabular mt-2 text-2xl font-bold text-slate-50">
            {formatBrl(ticketMedio)}
          </div>
          <div className="mt-1 text-xs text-slate-400">
            {filtered.length} anúncios na amostra
          </div>
        </div>
        <div className="glass-card glass-card-interactive rounded-2xl p-6">
          <div className="text-xs font-medium text-slate-400">
            Penetração FULL
          </div>
          <div className="font-tabular mt-2 text-2xl font-bold text-emerald-400">
            {pctFull.toFixed(0)}%
          </div>
          <div className="mt-1 text-xs text-slate-400">
            Logística fulfillment ativa
          </div>
        </div>
        <div className="glass-card glass-card-interactive rounded-2xl p-6">
          <div className="text-xs font-medium text-slate-400">
            Presença em Catálogo
          </div>
          <div className="font-tabular mt-2 text-2xl font-bold text-sky-400">
            {pctCatalogo.toFixed(0)}%
          </div>
          <div className="mt-1 text-xs text-slate-400">
            Disputa direta de Buybox
          </div>
        </div>
      </div>

      <div className="glass-card overflow-x-auto rounded-2xl p-2">
        <table className="w-full min-w-[700px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-[#334155] text-xs font-semibold text-slate-400">
              <th className="px-4 py-3">#</th>
              <th className="px-4 py-3">Título do Líder</th>
              <th className="px-4 py-3 text-right">Preço</th>
              <th className="px-4 py-3">Modalidade</th>
              <th className="px-4 py-3 text-right">Nota</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#334155]/60">
            {filtered.map((item) => (
              <tr key={item.posicao} className="hover:bg-slate-800/35">
                <td className="font-tabular px-4 py-3 text-slate-400">
                  {item.posicao}
                </td>
                <td className="px-4 py-3">
                  <div className="font-medium text-slate-100">
                    {item.titulo}
                  </div>
                  <div className="text-xs text-slate-400">{item.vendedor}</div>
                </td>
                <td className="font-tabular px-4 py-3 text-right font-semibold text-slate-100">
                  {formatBrl(item.preco)}
                </td>
                <td className="px-4 py-3 text-xs text-slate-300">
                  {item.full ? 'Full' : 'Normal'} ·{' '}
                  {item.catalogo ? 'Catálogo' : 'Individual'}
                </td>
                <td className="font-tabular px-4 py-3 text-right text-amber-300">
                  {item.nota.toFixed(1)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

interface PricingCalculatorViewProps {
  onSaveListing: (listing: MonitoredListing) => void;
}

export function PricingCalculatorView({
  onSaveListing,
}: PricingCalculatorViewProps) {
  const [plataforma, setPlataforma] = useState<Platform2026>(
    'Mercado Livre Clássico (12%)'
  );
  const [precoVenda, setPrecoVenda] = useState<number>(89.9);
  const [meuCusto, setMeuCusto] = useState<number>(32.0);
  const [impostoPct, setImpostoPct] = useState<number>(6.0);
  const [freteEstimado, setFreteEstimado] = useState<number>(14.9);

  const initialDefaults = computePlatformDefaults2026(
    'Mercado Livre Clássico (12%)',
    89.9
  );
  const [comissaoPct, setComissaoPct] = useState<number>(
    initialDefaults.comissaoPct
  );
  const [taxaFixa, setTaxaFixa] = useState<number>(initialDefaults.taxaFixa);

  const [grupoProduto, setGrupoProduto] = useState<string>('');
  const [urlAnuncio, setUrlAnuncio] = useState<string>('');
  const [savedFeedback, setSavedFeedback] = useState<string>('');

  const handlePlatformChange = (nextPlatform: Platform2026) => {
    setPlataforma(nextPlatform);
    const defs = computePlatformDefaults2026(nextPlatform, precoVenda);
    setComissaoPct(defs.comissaoPct);
    setTaxaFixa(defs.taxaFixa);
  };

  const handlePriceChange = (nextPrice: number) => {
    const safePrice = Number.isFinite(nextPrice) ? Math.max(0, nextPrice) : 0;
    setPrecoVenda(safePrice);
    const defs = computePlatformDefaults2026(plataforma, safePrice);
    setComissaoPct(defs.comissaoPct);
    setTaxaFixa(defs.taxaFixa);
  };

  const breakdown = calculatePricingBreakdown({
    precoVenda,
    meuCusto,
    impostoPct,
    comissaoPct,
    taxaFixa,
    freteEstimado,
  });

  const handleSaveToConfig = (e: React.FormEvent) => {
    e.preventDefault();
    if (!grupoProduto.trim()) {
      setSavedFeedback('Informe o Grupo de Produto antes de salvar.');
      return;
    }
    const mkt: MarketplaceName = computePlatformDefaults2026(
      plataforma,
      precoVenda
    ).marketplace;

    onSaveListing({
      id: `calc-${Date.now()}`,
      tipo: 'Meu Anuncio',
      grupoProduto: grupoProduto.trim(),
      marketplace: mkt,
      url: urlAnuncio.trim() || 'https://produto.mercadolivre.com.br',
      titulo: `${grupoProduto.trim()} (${mkt})`,
      preco: precoVenda,
      estoqueAtual: 25,
      vendasHoje: 0,
      horarioPico: '—',
      full: mkt === 'Mercado Livre',
      catalogo: false,
      nota: 5.0,
      meuCusto,
      impostoPct,
      comissaoPct,
      taxaFixa,
      freteEstimado,
      vendasPorHora: Array(24).fill(0),
    });

    setGrupoProduto('');
    setUrlAnuncio('');
    setSavedFeedback('Precificação salva no painel de monitoramento.');
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
      <div className="space-y-6 lg:col-span-7">
        <div className="glass-card rounded-2xl p-6">
          <h2 className="font-display mb-4 text-lg font-semibold text-slate-100">
            Regras de Marketplace 2026 (Editável)
          </h2>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="calc-plat"
                className="mb-1.5 block text-xs font-medium text-slate-400"
              >
                Plataforma
              </label>
              <select
                id="calc-plat"
                value={plataforma}
                onChange={(e) =>
                  handlePlatformChange(e.target.value as Platform2026)
                }
                className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
              >
                {PLATFORMS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                htmlFor="calc-preco"
                className="mb-1.5 block text-xs font-medium text-slate-400"
              >
                Preço de Venda (R$)
              </label>
              <input
                id="calc-preco"
                type="number"
                min="0"
                step="0.5"
                value={precoVenda}
                onChange={(e) => handlePriceChange(Number(e.target.value))}
                className="font-tabular min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
              />
            </div>

            <div>
              <label
                htmlFor="calc-custo"
                className="mb-1.5 block text-xs font-medium text-slate-400"
              >
                Meu Custo (R$)
              </label>
              <input
                id="calc-custo"
                type="number"
                min="0"
                step="0.5"
                value={meuCusto}
                onChange={(e) => setMeuCusto(Number(e.target.value))}
                className="font-tabular min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
              />
            </div>

            <div>
              <label
                htmlFor="calc-imposto"
                className="mb-1.5 block text-xs font-medium text-slate-400"
              >
                Imposto (%)
              </label>
              <input
                id="calc-imposto"
                type="number"
                min="0"
                max="100"
                step="0.5"
                value={impostoPct}
                onChange={(e) => setImpostoPct(Number(e.target.value))}
                className="font-tabular min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
              />
            </div>

            <div>
              <label
                htmlFor="calc-comissao"
                className="mb-1.5 block text-xs font-medium text-slate-400"
              >
                Comissão (%) — Editável
              </label>
              <input
                id="calc-comissao"
                type="number"
                min="0"
                max="100"
                step="0.5"
                value={comissaoPct}
                onChange={(e) => setComissaoPct(Number(e.target.value))}
                className="font-tabular min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
              />
            </div>

            <div>
              <label
                htmlFor="calc-taxa-fixa"
                className="mb-1.5 block text-xs font-medium text-slate-400"
              >
                Taxa Fixa (R$) — Editável
              </label>
              <input
                id="calc-taxa-fixa"
                type="number"
                min="0"
                step="0.5"
                value={taxaFixa}
                onChange={(e) => setTaxaFixa(Number(e.target.value))}
                className="font-tabular min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
              />
            </div>

            <div className="sm:col-span-2">
              <label
                htmlFor="calc-frete"
                className="mb-1.5 block text-xs font-medium text-slate-400"
              >
                Frete Estimado (R$)
              </label>
              <input
                id="calc-frete"
                type="number"
                min="0"
                step="0.5"
                value={freteEstimado}
                onChange={(e) => setFreteEstimado(Number(e.target.value))}
                className="font-tabular min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
              />
            </div>
          </div>
        </div>

        <form
          onSubmit={handleSaveToConfig}
          className="glass-card space-y-4 rounded-2xl p-6"
        >
          <h3 className="font-display text-base font-semibold text-slate-100">
            Salvar Direto na Configuração
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="calc-grupo"
                className="mb-1.5 block text-xs font-medium text-slate-400"
              >
                Grupo de Produto
              </label>
              <input
                id="calc-grupo"
                type="text"
                value={grupoProduto}
                onChange={(e) => setGrupoProduto(e.target.value)}
                placeholder="Ex: Ração Golden 15kg"
                className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
              />
            </div>
            <div>
              <label
                htmlFor="calc-url"
                className="mb-1.5 block text-xs font-medium text-slate-400"
              >
                URL do Anúncio (opcional)
              </label>
              <input
                id="calc-url"
                type="url"
                value={urlAnuncio}
                onChange={(e) => setUrlAnuncio(e.target.value)}
                placeholder="https://produto.mercadolivre.com.br/..."
                className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <button
              type="submit"
              className="min-h-[42px] rounded-xl bg-sky-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 whitespace-nowrap"
            >
              Salvar na Configuração
            </button>
            {savedFeedback && (
              <span className="text-xs font-medium text-emerald-300">
                {savedFeedback}
              </span>
            )}
          </div>
        </form>
      </div>

      <div className="space-y-6 lg:col-span-5">
        <MarginGauge marginPct={breakdown.margemPct} />

        <div className="glass-card space-y-3 rounded-2xl p-6 text-sm">
          <div className="flex items-center justify-between border-b border-[#334155] pb-3">
            <span className="text-slate-400">Lucro Líquido Unitário</span>
            <span
              className={`font-tabular text-xl font-bold ${
                breakdown.lucroLiquido >= 0
                  ? 'text-emerald-400'
                  : 'text-rose-400'
              }`}
            >
              {formatBrl(breakdown.lucroLiquido)}
            </span>
          </div>
          <div className="flex justify-between text-slate-300">
            <span className="text-slate-400">Comissão ({comissaoPct}%)</span>
            <span className="font-tabular">-{formatBrl(breakdown.comissaoRs)}</span>
          </div>
          <div className="flex justify-between text-slate-300">
            <span className="text-slate-400">Taxa Fixa</span>
            <span className="font-tabular">-{formatBrl(taxaFixa)}</span>
          </div>
          <div className="flex justify-between text-slate-300">
            <span className="text-slate-400">Imposto ({impostoPct}%)</span>
            <span className="font-tabular">-{formatBrl(breakdown.impostoRs)}</span>
          </div>
          <div className="flex justify-between text-slate-300">
            <span className="text-slate-400">Custo + Frete</span>
            <span className="font-tabular">
              -{formatBrl(meuCusto + freteEstimado)}
            </span>
          </div>
          <div className="flex justify-between border-t border-[#334155] pt-3">
            <span className="text-slate-400">ROI / Preço Break-even</span>
            <span className="font-tabular font-semibold text-sky-300">
              {breakdown.roiPct.toFixed(1)}% · {formatBrl(breakdown.precoEquilibrio)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function AdFactoryView() {
  const [produto, setProduto] = useState(
    'Tapete Higiênico Super Absorvente 30 Unidades'
  );
  const [marca, setMarca] = useState('PetPrime');
  const [beneficio, setBeneficio] = useState('6 Camadas Gel Antivazamento');
  const [tom, setTom] = useState<'Casual' | 'Profissional'>('Profissional');
  const [titulos, setTitulos] = useState<string[]>(() =>
    generateSeoTitles(
      'Tapete Higiênico Super Absorvente 30 Unidades',
      'PetPrime',
      '6 Camadas Gel Antivazamento'
    )
  );
  const [copied, setCopied] = useState(false);

  const handleGenerate = (e: React.FormEvent) => {
    e.preventDefault();
    setTitulos(generateSeoTitles(produto, marca, beneficio));
    setCopied(false);
  };

  const descriptionText = `${produto} da linha ${marca} com ${beneficio}.\n\nDesenvolvido para máxima absorção e praticidade no dia a dia (${tom}).\n- Barreira antivazamento reforçada\n- Adesivo de fixação nas bordas\n- Pronta entrega com nota fiscal`;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(
        `${titulos[0] ?? produto}\n\n${descriptionText}`
      );
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
      <form
        onSubmit={handleGenerate}
        className="glass-card space-y-4 rounded-2xl p-6 lg:col-span-5"
      >
        <h2 className="font-display text-lg font-semibold text-slate-100">
          Fábrica de Anúncios SEO
        </h2>
        <div>
          <label
            htmlFor="fab-prod"
            className="mb-1.5 block text-xs font-medium text-slate-400"
          >
            Produto
          </label>
          <input
            id="fab-prod"
            type="text"
            value={produto}
            onChange={(e) => setProduto(e.target.value)}
            className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label
              htmlFor="fab-marca"
              className="mb-1.5 block text-xs font-medium text-slate-400"
            >
              Marca
            </label>
            <input
              id="fab-marca"
              type="text"
              value={marca}
              onChange={(e) => setMarca(e.target.value)}
              className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
            />
          </div>
          <div>
            <label
              htmlFor="fab-tom"
              className="mb-1.5 block text-xs font-medium text-slate-400"
            >
              Tom
            </label>
            <select
              id="fab-tom"
              value={tom}
              onChange={(e) =>
                setTom(e.target.value as 'Casual' | 'Profissional')
              }
              className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
            >
              <option value="Profissional">Profissional</option>
              <option value="Casual">Casual</option>
            </select>
          </div>
        </div>
        <div>
          <label
            htmlFor="fab-ben"
            className="mb-1.5 block text-xs font-medium text-slate-400"
          >
            Benefício Principal
          </label>
          <input
            id="fab-ben"
            type="text"
            value={beneficio}
            onChange={(e) => setBeneficio(e.target.value)}
            className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
          />
        </div>
        <button
          type="submit"
          className="inline-flex min-h-[42px] w-full items-center justify-center gap-2 rounded-xl bg-sky-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 whitespace-nowrap"
        >
          <Sparkles className="h-4 w-4" />
          Gerar Variações SEO
        </button>
      </form>

      <div className="space-y-6 lg:col-span-7">
        <div className="glass-card rounded-2xl p-6">
          <div className="mb-3 flex items-center justify-between gap-2">
            <h3 className="font-display text-base font-semibold text-slate-100">
              Títulos SEO (máximo 60 caracteres)
            </h3>
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex min-h-[36px] items-center gap-1.5 rounded-lg border border-[#334155] bg-slate-900/70 px-3 py-1.5 text-xs font-medium text-slate-200 transition hover:border-sky-400 whitespace-nowrap"
            >
              {copied ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-400" />
                  Copiado
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5 text-sky-400" />
                  Copiar Anúncio
                </>
              )}
            </button>
          </div>

          <ul className="space-y-2.5 text-sm">
            {titulos.map((titulo, idx) => (
              <li
                key={`${titulo}-${idx}`}
                className="flex items-center justify-between gap-4 border-b border-[#334155]/60 pb-2.5 last:border-none last:pb-0"
              >
                <span className="text-slate-100">
                  {idx + 1}. {titulo}
                </span>
                <span className="font-tabular shrink-0 text-xs text-slate-400">
                  {titulo.length}/60
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <h3 className="font-display mb-2 text-base font-semibold text-slate-100">
            Prévia Estruturada para Publicação
          </h3>
          <pre className="overflow-x-auto whitespace-pre-wrap rounded-xl border border-[#334155] bg-slate-950/70 p-4 font-sans text-sm leading-relaxed text-slate-300">
            {descriptionText}
          </pre>
        </div>
      </div>
    </div>
  );
}

export function AdRescueView() {
  const [tituloAtual, setTituloAtual] = useState(
    'Tapete cachorro barato 30 unidades'
  );
  const [preco, setPreco] = useState(79.9);
  const [fotos, setFotos] = useState(4);
  const [visitas, setVisitas] = useState(420);
  const [vendas, setVendas] = useState(3);

  const diag = analyzeListingDiagnostic({
    titulo: tituloAtual,
    preco,
    fotos,
    visitas30d: visitas,
    vendas30d: vendas,
  });

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
      <div className="glass-card space-y-4 rounded-2xl p-6 lg:col-span-5">
        <h2 className="font-display text-lg font-semibold text-slate-100">
          Diagnóstico de Anúncio com Baixa Venda
        </h2>
        <div>
          <label
            htmlFor="resg-titulo"
            className="mb-1.5 block text-xs font-medium text-slate-400"
          >
            Título Atual
          </label>
          <input
            id="resg-titulo"
            type="text"
            value={tituloAtual}
            onChange={(e) => setTituloAtual(e.target.value)}
            className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label
              htmlFor="resg-preco"
              className="mb-1.5 block text-xs font-medium text-slate-400"
            >
              Preço (R$)
            </label>
            <input
              id="resg-preco"
              type="number"
              min="0"
              step="0.5"
              value={preco}
              onChange={(e) => setPreco(Number(e.target.value))}
              className="font-tabular min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
            />
          </div>
          <div>
            <label
              htmlFor="resg-fotos"
              className="mb-1.5 block text-xs font-medium text-slate-400"
            >
              Nº de Fotos
            </label>
            <input
              id="resg-fotos"
              type="number"
              min="0"
              max="30"
              value={fotos}
              onChange={(e) => setFotos(Number(e.target.value))}
              className="font-tabular min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
            />
          </div>
          <div>
            <label
              htmlFor="resg-visitas"
              className="mb-1.5 block text-xs font-medium text-slate-400"
            >
              Visitas (30 dias)
            </label>
            <input
              id="resg-visitas"
              type="number"
              min="0"
              value={visitas}
              onChange={(e) => setVisitas(Number(e.target.value))}
              className="font-tabular min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
            />
          </div>
          <div>
            <label
              htmlFor="resg-vendas"
              className="mb-1.5 block text-xs font-medium text-slate-400"
            >
              Vendas (30 dias)
            </label>
            <input
              id="resg-vendas"
              type="number"
              min="0"
              value={vendas}
              onChange={(e) => setVendas(Number(e.target.value))}
              className="font-tabular min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/80 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
            />
          </div>
        </div>
      </div>

      <div className="space-y-6 lg:col-span-7">
        <div className="glass-card rounded-2xl p-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-display text-base font-semibold text-slate-100">
              Gargalo Detectado: {diag.gargalo}
            </h3>
            <span className="font-tabular text-sm font-semibold text-sky-300">
              Conversão: {diag.taxaConversao.toFixed(2)}%
            </span>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-slate-300">
            {diag.resumo}
          </p>
        </div>

        <div className="glass-card rounded-2xl p-6">
          <h3 className="font-display mb-3 text-base font-semibold text-slate-100">
            3 Ações Prioritárias de Resgate
          </h3>
          <ul className="space-y-3 text-sm text-slate-300">
            {diag.acoes.map((acao, idx) => (
              <li
                key={idx}
                className="flex gap-3 border-b border-[#334155]/60 pb-3 last:border-none last:pb-0"
              >
                <span className="font-tabular font-semibold text-sky-400">
                  0{idx + 1}.
                </span>
                <span>{acao}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

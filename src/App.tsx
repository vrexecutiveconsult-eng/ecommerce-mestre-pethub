import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Calculator,
  Compass,
  GitCompareArrows,
  LifeBuoy,
  Menu,
  Plus,
  Search,
  Sparkles,
  Trophy,
  X,
} from 'lucide-react';
import {
  buildGeneralRankingRows,
  formatBrl,
  MarketplaceName,
  ModuleId,
  MonitoredListing,
  RankingEntry,
  ScalabilityLevel,
} from './utils/ecommerceLogic';
import { INITIAL_LISTINGS, RANKING_STORE_SEED } from './data/petSeedData';
import {
  AdFactoryView,
  AdRescueView,
  ComparativeAlertsView,
  PeakBattleView,
  PetRadarView,
  PricingCalculatorView,
} from './components/ModuleViews';
import { SparklineChart } from './components/SparklineChart';

const STORAGE_KEY = 'ecommerce_mestre_listings_v1';

interface NavItem {
  id: ModuleId;
  label: string;
  subtitle: string;
  icon: typeof Activity;
}

const NAV_ITEMS: NavItem[] = [
  {
    id: 'batalha',
    label: 'Batalha de Horário',
    subtitle: 'Vendas horárias e lucro líquido por anúncio',
    icon: Activity,
  },
  {
    id: 'comparativo',
    label: 'Comparativo & Alertas',
    subtitle: 'Monitoramento lado a lado contra concorrentes',
    icon: GitCompareArrows,
  },
  {
    id: 'radar',
    label: 'Radar Nicho Pet',
    subtitle: 'Mapeamento de ticket médio, Full e Catálogo',
    icon: Compass,
  },
  {
    id: 'calculadora',
    label: 'Precificação 2026',
    subtitle: 'Taxas editáveis por plataforma e margem líquida',
    icon: Calculator,
  },
  {
    id: 'fabrica',
    label: 'Fábrica de Anúncios',
    subtitle: 'Geração de títulos SEO e estrutura de copy',
    icon: Sparkles,
  },
  {
    id: 'resgate',
    label: 'Resgate de Anúncio',
    subtitle: 'Diagnóstico de tráfego e recuperação de conversão',
    icon: LifeBuoy,
  },
  {
    id: 'ranking',
    label: 'Ranking Geral',
    subtitle: 'Concorrentes ordenados por vendas com tendência e confronto direto',
    icon: Trophy,
  },
];

function getTrendLabel(trend: RankingEntry['tendencia']): string {
  if (trend === 'up') return 'Em alta';
  if (trend === 'down') return 'Em queda';
  return 'Estável';
}

function getScalabilityTextClass(level: ScalabilityLevel): string {
  if (level === 'Muito Escalável') return 'text-emerald-400';
  if (level === 'Média') return 'text-amber-300';
  return 'text-rose-400';
}

export default function App() {
  const [activeModule, setActiveModule] = useState<ModuleId>('batalha');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [addModalOpen, setAddModalOpen] = useState(false);

  // Estados da aba Ranking Geral
  const [rankingSearch, setRankingSearch] = useState('');
  const [rankingScaleFilter, setRankingScaleFilter] = useState<
    'Todas' | ScalabilityLevel
  >('Todas');
  const [onlyMatchedSimilar, setOnlyMatchedSimilar] = useState(false);
  const [selectedBattleEntry, setSelectedBattleEntry] =
    useState<RankingEntry | null>(null);

  const [listings, setListings] = useState<MonitoredListing[]>(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch {
      // Fallback silencioso para dados iniciais
    }
    return INITIAL_LISTINGS;
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(listings));
    } catch {
      // Ignora erro de quota de armazenamento
    }
  }, [listings]);

  // Estado do formulário do modal de novo anúncio
  const [newTipo, setNewTipo] = useState<'Meu Anuncio' | 'Concorrente'>(
    'Meu Anuncio'
  );
  const [newGrupo, setNewGrupo] = useState('');
  const [newMarketplace, setNewMarketplace] =
    useState<MarketplaceName>('Mercado Livre');
  const [newUrl, setNewUrl] = useState('');
  const [newPreco, setNewPreco] = useState(89.9);
  const [newCusto, setNewCusto] = useState(34.0);
  const [formError, setFormError] = useState('');

  const rankingRows = useMemo(
    () => buildGeneralRankingRows(listings, RANKING_STORE_SEED),
    [listings]
  );

  const filteredRankingRows = useMemo(() => {
    const query = rankingSearch.trim().toLowerCase();
    return rankingRows.filter((row) => {
      const matchesQuery =
        !query ||
        row.titulo.toLowerCase().includes(query) ||
        row.lojaConcorrente.toLowerCase().includes(query);
      const matchesScale =
        rankingScaleFilter === 'Todas' ||
        row.escalabilidade === rankingScaleFilter;
      const matchesSimilar =
        !onlyMatchedSimilar || row.matchedMyListing !== null;
      return matchesQuery && matchesScale && matchesSimilar;
    });
  }, [rankingRows, rankingSearch, rankingScaleFilter, onlyMatchedSimilar]);

  const rankingSummary = useMemo(() => {
    const vendas = filteredRankingRows.reduce(
      (acc, r) => acc + r.vendasPeriodo,
      0
    );
    const faturamento = filteredRankingRows.reduce(
      (acc, r) => acc + r.faturamentoEstimado,
      0
    );
    const confrontos = filteredRankingRows.filter(
      (r) => r.matchedMyListing !== null
    ).length;
    return {
      total: filteredRankingRows.length,
      vendas,
      faturamento,
      confrontos,
    };
  }, [filteredRankingRows]);

  const currentNav =
    NAV_ITEMS.find((item) => item.id === activeModule) ?? NAV_ITEMS[0];

  const handleSelectModule = (id: ModuleId) => {
    setActiveModule(id);
    setMobileMenuOpen(false);
  };

  const handleSaveListing = (listing: MonitoredListing) => {
    setListings((prev) => [listing, ...prev]);
  };

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGrupo.trim()) {
      setFormError('Informe o Grupo do Produto.');
      return;
    }
    if (!newUrl.trim().startsWith('http')) {
      setFormError('Informe uma URL válida começando com http:// ou https://.');
      return;
    }

    handleSaveListing({
      id: `item-${Date.now()}`,
      tipo: newTipo,
      grupoProduto: newGrupo.trim(),
      marketplace: newMarketplace,
      url: newUrl.trim(),
      titulo: `${newGrupo.trim()} — ${newMarketplace}`,
      preco: newPreco,
      estoqueAtual: 20,
      vendasHoje: 0,
      horarioPico: '—',
      full: newMarketplace === 'Mercado Livre',
      catalogo: false,
      nota: 5.0,
      meuCusto: newTipo === 'Meu Anuncio' ? newCusto : 0,
      impostoPct: 6,
      comissaoPct: 12,
      taxaFixa: 0,
      freteEstimado: 15,
      vendasPorHora: Array(24).fill(0),
    });

    setNewGrupo('');
    setNewUrl('');
    setFormError('');
    setAddModalOpen(false);
  };

  const sidebarContent = (
    <div className="flex h-full flex-col justify-between p-4">
      <div>
        <div className="mb-6 flex items-center justify-between px-2 pt-1">
          <span className="font-display text-lg font-extrabold tracking-tight text-slate-50 whitespace-nowrap">
            E-Commerce Mestre
          </span>
          <button
            type="button"
            onClick={() => setMobileMenuOpen(false)}
            aria-label="Fechar menu lateral"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white md:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav aria-label="Navegação principal" className="space-y-1.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = item.id === activeModule;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => handleSelectModule(item.id)}
                aria-current={isActive ? 'page' : undefined}
                className={`flex min-h-[42px] w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-left text-sm font-medium transition whitespace-nowrap ${
                  isActive
                    ? 'border border-[#334155] bg-slate-800/80 text-sky-300 shadow-sm'
                    : 'border border-transparent text-slate-300 hover:bg-slate-800/45 hover:text-slate-100'
                }`}
              >
                <Icon
                  className={`h-4 w-4 shrink-0 ${
                    isActive ? 'text-sky-400' : 'text-slate-400'
                  }`}
                />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="glass-card rounded-xl p-4">
        <div className="text-xs font-medium text-slate-400">
          Conta Ativa · Nicho Pet
        </div>
        <div className="mt-1 text-sm font-semibold text-slate-100">
          PetPrime Oficial
        </div>
        <div className="font-tabular mt-1 text-xs text-slate-400">
          {listings.length} anúncios monitorados
        </div>
      </div>
    </div>
  );

  return (
    <div className="app-canvas min-h-screen bg-[#0B0F19] text-slate-200">
      <div className="flex min-h-screen">
        {/* Sidebar Desktop Fixa */}
        <aside className="glass-sidebar hidden w-[264px] shrink-0 md:sticky md:top-0 md:block md:h-screen">
          {sidebarContent}
        </aside>

        {/* Drawer Mobile */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-40 flex md:hidden">
            <div
              className="fixed inset-0 bg-black/65"
              onClick={() => setMobileMenuOpen(false)}
              aria-hidden="true"
            />
            <aside className="glass-sidebar relative z-50 h-full w-[264px]">
              {sidebarContent}
            </aside>
          </div>
        )}

        {/* Área Principal */}
        <div className="flex min-w-0 flex-1 flex-col">
          {/* Top Bar */}
          <header className="glass-topbar sticky top-0 z-30 flex items-center justify-between gap-4 px-5 py-3.5 lg:px-8">
            <div className="flex min-w-0 items-center gap-3">
              <button
                type="button"
                onClick={() => setMobileMenuOpen(true)}
                aria-label="Abrir menu lateral"
                className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[#334155] bg-slate-900/80 text-slate-200 hover:border-sky-400 md:hidden"
              >
                <Menu className="h-5 w-5" />
              </button>

              <div className="flex min-w-0 items-center gap-2 text-sm">
                <span className="hidden text-slate-400 sm:inline whitespace-nowrap">
                  E-Commerce Mestre
                </span>
                <span
                  className="hidden text-slate-600 sm:inline"
                  aria-hidden="true"
                >
                  /
                </span>
                <span className="truncate font-semibold text-slate-100">
                  {currentNav.label}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setAddModalOpen(true)}
              className="inline-flex min-h-[40px] shrink-0 items-center gap-2 rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 whitespace-nowrap"
            >
              <Plus className="h-4 w-4" />
              Adicionar Anúncio
            </button>
          </header>

          {/* Conteúdo do Módulo */}
          <main className="mx-auto w-full max-w-[1200px] flex-1 px-5 py-6 lg:px-8">
            <div className="mb-5">
              <h1 className="font-display text-2xl font-bold tracking-tight text-slate-50 text-balance">
                {currentNav.label}
              </h1>
              <p className="mt-1 text-sm text-slate-400">
                {currentNav.subtitle}
              </p>
            </div>

            {activeModule === 'batalha' && (
              <PeakBattleView
                listings={listings}
                onOpenAddModal={() => setAddModalOpen(true)}
              />
            )}
            {activeModule === 'comparativo' && (
              <ComparativeAlertsView listings={listings} />
            )}
            {activeModule === 'radar' && <PetRadarView />}
            {activeModule === 'calculadora' && (
              <PricingCalculatorView onSaveListing={handleSaveListing} />
            )}
            {activeModule === 'fabrica' && <AdFactoryView />}
            {activeModule === 'resgate' && <AdRescueView />}
            {activeModule === 'ranking' && (
              <section aria-label="Ranking Geral de Concorrentes" className="space-y-6">
                {/* KPIs Consolidados */}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  <div className="glass-card glass-card-interactive rounded-2xl p-5">
                    <div className="text-xs font-medium text-slate-400">
                      Concorrentes Rankeados
                    </div>
                    <div className="font-tabular mt-2 text-2xl font-bold text-slate-50">
                      {rankingSummary.total}
                    </div>
                    <div className="mt-1.5 text-xs text-slate-400">
                      Lojas e anúncios consolidados
                    </div>
                  </div>

                  <div className="glass-card glass-card-interactive rounded-2xl p-5">
                    <div className="text-xs font-medium text-slate-400">
                      Vendas Estimadas
                    </div>
                    <div className="font-tabular mt-2 text-2xl font-bold text-emerald-400">
                      {rankingSummary.vendas} un.
                    </div>
                    <div className="mt-1.5 text-xs text-slate-400">
                      Volume total do recorte atual
                    </div>
                  </div>

                  <div className="glass-card glass-card-interactive rounded-2xl p-5">
                    <div className="text-xs font-medium text-slate-400">
                      Faturamento Bruto Est.
                    </div>
                    <div className="font-tabular mt-2 text-2xl font-bold text-slate-50">
                      {formatBrl(rankingSummary.faturamento)}
                    </div>
                    <div className="mt-1.5 text-xs text-slate-400">
                      Receita estimada concorrente
                    </div>
                  </div>

                  <div className="glass-card glass-card-interactive rounded-2xl p-5">
                    <div className="text-xs font-medium text-slate-400">
                      Confrontos Diretos
                    </div>
                    <div className="font-tabular mt-2 text-2xl font-bold text-sky-400">
                      {rankingSummary.confrontos}
                    </div>
                    <div className="mt-1.5 text-xs text-slate-400">
                      Similaridade ≥ 45% com seus itens
                    </div>
                  </div>
                </div>

                {/* Barra de Filtros */}
                <div className="glass-card flex flex-wrap items-center justify-between gap-3 rounded-2xl p-4">
                  <div className="relative min-w-[230px] flex-1">
                    <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      value={rankingSearch}
                      onChange={(e) => setRankingSearch(e.target.value)}
                      placeholder="Buscar concorrente ou título do anúncio..."
                      aria-label="Buscar concorrente ou título do anúncio"
                      className="min-h-[40px] w-full rounded-xl border border-[#334155] bg-slate-900/75 pl-10 pr-4 text-sm text-slate-100 placeholder:text-slate-500 focus:border-sky-400 focus:outline-none"
                    />
                  </div>

                  <div className="flex w-full flex-wrap items-center gap-2 lg:w-auto">
                    <div className="flex max-w-full flex-wrap items-center gap-1 rounded-xl border border-[#334155] bg-slate-900/70 p-1">
                      {(
                        [
                          'Todas',
                          'Muito Escalável',
                          'Média',
                          'Não Escalável',
                        ] as const
                      ).map((level) => (
                        <button
                          key={level}
                          type="button"
                          onClick={() => setRankingScaleFilter(level)}
                          className={`min-h-[34px] rounded-lg px-2.5 sm:px-3 py-1.5 text-xs font-semibold transition whitespace-nowrap shrink-0 ${
                            rankingScaleFilter === level
                              ? 'bg-sky-500 text-slate-950'
                              : 'text-slate-300 hover:text-white'
                          }`}
                        >
                          {level}
                        </button>
                      ))}
                    </div>

                    <button
                      type="button"
                      onClick={() => setOnlyMatchedSimilar((v) => !v)}
                      aria-pressed={onlyMatchedSimilar}
                      className={`min-h-[40px] rounded-xl border px-3.5 py-2 text-xs font-semibold transition whitespace-nowrap shrink-0 ${
                        onlyMatchedSimilar
                          ? 'border-sky-400 bg-sky-500/20 text-sky-300'
                          : 'border-[#334155] bg-slate-900/70 text-slate-300 hover:border-slate-500 hover:text-white'
                      }`}
                    >
                      Parecidos ≥ 45%
                    </button>
                  </div>
                </div>

                {/* Lista do Ranking Geral */}
                {filteredRankingRows.length === 0 ? (
                  <div className="glass-card rounded-2xl p-10 text-center">
                    <h2 className="font-display text-lg font-semibold text-slate-100">
                      Nenhum concorrente encontrado neste filtro
                    </h2>
                    <p className="mt-1.5 text-sm text-slate-400">
                      Ajuste o termo de busca ou limpe o filtro de escalabilidade para visualizar todo o ranking.
                    </p>
                    <button
                      type="button"
                      onClick={() => {
                        setRankingSearch('');
                        setRankingScaleFilter('Todas');
                        setOnlyMatchedSimilar(false);
                      }}
                      className="mt-4 inline-flex min-h-[40px] items-center rounded-xl bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400"
                    >
                      Limpar Filtros
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredRankingRows.map((row) => {
                      const medalModifier =
                        row.posicao === 1
                          ? 'ranking-medal-1'
                          : row.posicao === 2
                          ? 'ranking-medal-2'
                          : row.posicao === 3
                          ? 'ranking-medal-3'
                          : '';
                      const medalPrefix =
                        row.posicao === 1
                          ? '🥇 '
                          : row.posicao === 2
                          ? '🥈 '
                          : row.posicao === 3
                          ? '🥉 '
                          : '';

                      return (
                        <article
                          key={row.id}
                          className="ranking-glass-row rounded-2xl p-4 lg:px-5 lg:py-4"
                        >
                          <div className="grid grid-cols-1 items-center gap-3.5 lg:grid-cols-[minmax(0,1fr)_156px_292px]">
                            {/* Posição + Loja + Título + Métricas Tabulares */}
                            <div className="flex min-w-0 items-start gap-3.5">
                              <div
                                className={`ranking-medal font-tabular flex h-11 min-w-[52px] shrink-0 items-center justify-center rounded-xl px-2 text-sm font-bold ${medalModifier}`}
                              >
                                {medalPrefix}#{row.posicao}
                              </div>

                              <div className="min-w-0 flex-1">
                                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
                                  <span className="font-semibold text-sky-300">
                                    {row.lojaConcorrente}
                                  </span>
                                  <span aria-hidden="true">·</span>
                                  <span>{row.marketplace}</span>
                                  <span aria-hidden="true">·</span>
                                  <span
                                    className={`font-semibold ${getScalabilityTextClass(
                                      row.escalabilidade
                                    )}`}
                                  >
                                    {row.escalabilidade}
                                  </span>
                                </div>

                                <h2 className="mt-1 truncate text-base font-semibold text-slate-50">
                                  {row.titulo}
                                </h2>

                                <div className="font-tabular mt-2 flex flex-wrap items-center gap-x-3.5 gap-y-1 text-xs text-slate-300">
                                  <span className="whitespace-nowrap">
                                    Preço:{' '}
                                    <strong className="text-sky-300">
                                      {formatBrl(row.preco)}
                                    </strong>
                                  </span>
                                  <span className="whitespace-nowrap">
                                    Estoque:{' '}
                                    <strong
                                      className={
                                        row.estoqueAtual === 0
                                          ? 'text-rose-400'
                                          : 'text-slate-100'
                                      }
                                    >
                                      {row.estoqueAtual} un.
                                    </strong>
                                  </span>
                                  <span className="whitespace-nowrap">
                                    Vendas:{' '}
                                    <strong className="text-emerald-400">
                                      {row.vendasPeriodo} un.
                                    </strong>
                                  </span>
                                  <span className="whitespace-nowrap">
                                    Fat. Bruto:{' '}
                                    <strong className="text-slate-100">
                                      {formatBrl(row.faturamentoEstimado)}
                                    </strong>
                                  </span>
                                </div>
                              </div>
                            </div>

                            {/* Sparkline Condicional */}
                            <div className="flex justify-start lg:justify-center">
                              <SparklineChart
                                series={row.sparklineSeries}
                                trend={row.tendencia}
                                trendLabel={getTrendLabel(row.tendencia)}
                              />
                            </div>

                            {/* Detector de Similaridade + Botão Hover '⚔️ Comparar' */}
                            <div className="flex justify-end">
                              {row.matchedMyListing &&
                              row.battleScore !== null ? (
                                <button
                                  type="button"
                                  onClick={() => setSelectedBattleEntry(row)}
                                  className="compare-hover-box flex min-h-[48px] w-full items-center justify-between gap-2.5 rounded-xl px-3 py-2.5 text-left"
                                >
                                  <span className="min-w-0 text-xs text-slate-200">
                                    <span className="block whitespace-nowrap font-medium text-slate-300">
                                      Anúncio parecido com o seu
                                    </span>
                                    <span className="font-tabular mt-0.5 block font-bold text-sky-300">
                                      Nota: {row.battleScore.toFixed(1)}/10
                                    </span>
                                  </span>
                                  <span className="compare-hover-cta inline-flex shrink-0 items-center rounded-lg px-2.5 py-1.5 text-xs font-bold whitespace-nowrap">
                                    ⚔️ Comparar
                                  </span>
                                </button>
                              ) : (
                                <div className="flex min-h-[48px] w-full items-center justify-center rounded-xl border border-dashed border-[#334155] px-3 py-2 text-center text-xs text-slate-500">
                                  Sem equivalente ≥ 45% no seu catálogo
                                </div>
                              )}
                            </div>
                          </div>
                        </article>
                      );
                    })}
                  </div>
                )}
              </section>
            )}
          </main>
        </div>
      </div>

      {/* Modal Auditoria de Batalha (Você vs. Concorrente) */}
      {selectedBattleEntry && selectedBattleEntry.matchedMyListing && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="battle-modal-title"
        >
          <div className="glass-card w-full max-w-2xl rounded-2xl p-6">
            <div className="flex items-start justify-between gap-4 border-b border-[#334155] pb-4">
              <div>
                <div className="text-xs font-medium text-sky-300">
                  Similaridade {selectedBattleEntry.similarityPct.toFixed(0)}% ·{' '}
                  <span className="font-tabular">
                    Nota {selectedBattleEntry.battleScore?.toFixed(1)}/10
                  </span>
                </div>
                <h2
                  id="battle-modal-title"
                  className="font-display mt-1 text-lg font-bold text-slate-50"
                >
                  Auditoria de Batalha: Você vs. {selectedBattleEntry.lojaConcorrente}
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setSelectedBattleEntry(null)}
                aria-label="Fechar auditoria de batalha"
                className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-[#334155] text-xs text-slate-400">
                    <th className="py-2.5 pr-3 font-semibold">Critério</th>
                    <th className="px-3 py-2.5 font-semibold text-sky-300">
                      Seu Anúncio
                    </th>
                    <th className="pl-3 py-2.5 font-semibold text-amber-300">
                      Concorrente (#{selectedBattleEntry.posicao})
                    </th>
                  </tr>
                </thead>
                <tbody className="font-tabular divide-y divide-[#334155]/60 text-slate-200">
                  <tr>
                    <td className="py-2.5 pr-3 font-sans text-xs text-slate-400">
                      Título
                    </td>
                    <td className="px-3 py-2.5 font-sans text-xs">
                      {selectedBattleEntry.matchedMyListing.titulo}
                    </td>
                    <td className="pl-3 py-2.5 font-sans text-xs">
                      {selectedBattleEntry.titulo}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-3 font-sans text-xs text-slate-400">
                      Preço
                    </td>
                    <td className="px-3 py-2.5 font-semibold text-slate-100">
                      {formatBrl(selectedBattleEntry.matchedMyListing.preco)}
                    </td>
                    <td className="pl-3 py-2.5 font-semibold text-slate-100">
                      {formatBrl(selectedBattleEntry.preco)}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-3 font-sans text-xs text-slate-400">
                      Estoque Atual
                    </td>
                    <td className="px-3 py-2.5">
                      {selectedBattleEntry.matchedMyListing.estoqueAtual} un.
                    </td>
                    <td className="pl-3 py-2.5">
                      {selectedBattleEntry.estoqueAtual} un.
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-3 font-sans text-xs text-slate-400">
                      Vendas no Período
                    </td>
                    <td className="px-3 py-2.5 font-semibold text-emerald-400">
                      {selectedBattleEntry.matchedMyListing.vendasHoje} un.
                    </td>
                    <td className="pl-3 py-2.5 font-semibold text-emerald-400">
                      {selectedBattleEntry.vendasPeriodo} un.
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-3 font-sans text-xs text-slate-400">
                      FULL / Catálogo
                    </td>
                    <td className="px-3 py-2.5 font-sans text-xs">
                      {selectedBattleEntry.matchedMyListing.full ? 'FULL' : 'Padrão'}{' '}
                      ·{' '}
                      {selectedBattleEntry.matchedMyListing.catalogo
                        ? 'Catálogo'
                        : 'Clássico'}
                    </td>
                    <td className="pl-3 py-2.5 font-sans text-xs">
                      {selectedBattleEntry.full ? 'FULL' : 'Padrão'} ·{' '}
                      {selectedBattleEntry.catalogo ? 'Catálogo' : 'Clássico'}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-3 font-sans text-xs text-slate-400">
                      Avaliação
                    </td>
                    <td className="px-3 py-2.5">
                      {selectedBattleEntry.matchedMyListing.nota.toFixed(1)}
                    </td>
                    <td className="pl-3 py-2.5">
                      {selectedBattleEntry.nota.toFixed(1)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="mt-5 border-t border-[#334155] pt-4">
              <div className="text-xs font-semibold text-slate-300">
                Ações Recomendadas para Ultrapassagem
              </div>
              <ul className="mt-2 space-y-1.5 text-xs text-slate-300">
                <li>
                  •{' '}
                  {selectedBattleEntry.matchedMyListing.preco >
                  selectedBattleEntry.preco
                    ? `Ajustar preço em ${formatBrl(
                        selectedBattleEntry.matchedMyListing.preco -
                          selectedBattleEntry.preco
                      )} ou ativar cupom equivalente para igualar a oferta de ${formatBrl(
                        selectedBattleEntry.preco
                      )}.`
                    : 'Seu preço já é competitivo; destaque frete rápido e garantia na primeira linha da descrição.'}
                </li>
                <li>
                  •{' '}
                  {!selectedBattleEntry.matchedMyListing.catalogo &&
                  selectedBattleEntry.catalogo
                    ? 'Vincular SKU ao catálogo do marketplace para disputar a Buybox principal.'
                    : !selectedBattleEntry.matchedMyListing.full &&
                      selectedBattleEntry.full
                    ? 'Migrar estoque prioritário para logística FULL para eliminar desvantagem no prazo de entrega.'
                    : 'Manter estoque acima de 15 dias de cobertura para sustentar relevância orgânica.'}
                </li>
              </ul>
            </div>

            <div className="mt-5 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedBattleEntry(null)}
                className="min-h-[40px] rounded-xl bg-sky-500 px-5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400"
              >
                Fechar Auditoria
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Adicionar Anúncio */}
      {addModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-add-title"
        >
          <div className="glass-card w-full max-w-lg rounded-2xl p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2
                id="modal-add-title"
                className="font-display text-lg font-bold text-slate-100"
              >
                Adicionar Anúncio Monitorado
              </h2>
              <button
                type="button"
                onClick={() => setAddModalOpen(false)}
                aria-label="Fechar modal"
                className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label
                    htmlFor="add-tipo"
                    className="mb-1.5 block text-xs font-medium text-slate-400"
                  >
                    Tipo
                  </label>
                  <select
                    id="add-tipo"
                    value={newTipo}
                    onChange={(e) =>
                      setNewTipo(
                        e.target.value as 'Meu Anuncio' | 'Concorrente'
                      )
                    }
                    className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/85 px-3 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
                  >
                    <option value="Meu Anuncio">Meu Anuncio</option>
                    <option value="Concorrente">Concorrente</option>
                  </select>
                </div>

                <div>
                  <label
                    htmlFor="add-mkt"
                    className="mb-1.5 block text-xs font-medium text-slate-400"
                  >
                    Marketplace
                  </label>
                  <select
                    id="add-mkt"
                    value={newMarketplace}
                    onChange={(e) =>
                      setNewMarketplace(e.target.value as MarketplaceName)
                    }
                    className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/85 px-3 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
                  >
                    <option value="Mercado Livre">Mercado Livre</option>
                    <option value="Amazon">Amazon</option>
                    <option value="Shopee">Shopee</option>
                    <option value="Magalu">Magalu</option>
                    <option value="Petz">Petz</option>
                    <option value="Cobasi">Cobasi</option>
                  </select>
                </div>
              </div>

              <div>
                <label
                  htmlFor="add-grupo"
                  className="mb-1.5 block text-xs font-medium text-slate-400"
                >
                  Grupo de Produto
                </label>
                <input
                  id="add-grupo"
                  type="text"
                  value={newGrupo}
                  onChange={(e) => setNewGrupo(e.target.value)}
                  placeholder="Ex: Tapete Higiênico 30un"
                  className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/85 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
                />
              </div>

              <div>
                <label
                  htmlFor="add-url"
                  className="mb-1.5 block text-xs font-medium text-slate-400"
                >
                  URL do Anúncio
                </label>
                <input
                  id="add-url"
                  type="url"
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  placeholder="https://produto.mercadolivre.com.br/MLB-..."
                  className="min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/85 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label
                    htmlFor="add-preco"
                    className="mb-1.5 block text-xs font-medium text-slate-400"
                  >
                    Preço (R$)
                  </label>
                  <input
                    id="add-preco"
                    type="number"
                    min="0"
                    step="0.5"
                    value={newPreco}
                    onChange={(e) => setNewPreco(Number(e.target.value))}
                    className="font-tabular min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/85 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
                  />
                </div>
                <div>
                  <label
                    htmlFor="add-custo"
                    className="mb-1.5 block text-xs font-medium text-slate-400"
                  >
                    Meu Custo (R$)
                  </label>
                  <input
                    id="add-custo"
                    type="number"
                    min="0"
                    step="0.5"
                    value={newCusto}
                    onChange={(e) => setNewCusto(Number(e.target.value))}
                    className="font-tabular min-h-[42px] w-full rounded-xl border border-[#334155] bg-slate-900/85 px-3.5 text-sm text-slate-100 focus:border-sky-400 focus:outline-none"
                  />
                </div>
              </div>

              {formError && (
                <p className="text-xs font-medium text-rose-400">{formError}</p>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setAddModalOpen(false)}
                  className="min-h-[40px] rounded-xl border border-[#334155] px-4 py-2 text-sm font-medium text-slate-300 hover:text-white"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="min-h-[40px] rounded-xl bg-sky-500 px-5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-sky-400"
                >
                  Salvar Anúncio
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

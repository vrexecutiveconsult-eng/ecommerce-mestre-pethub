import test from 'node:test';
import assert from 'node:assert/strict';
import {
  analyzeListingDiagnostic,
  buildComparativeRows,
  buildHourlyBattleSeries,
  calculateKpis,
  calculatePricingBreakdown,
  computePlatformDefaults2026,
  generateSeoTitles,
} from './ecommerceLogic';
import { INITIAL_LISTINGS } from '../data/petSeedData';

test('computePlatformDefaults2026 applies Mercado Livre, Shopee CNPJ/CPF and Magalu 2026 tiers', () => {
  assert.deepEqual(
    computePlatformDefaults2026('Mercado Livre Clássico (12%)', 100),
    { comissaoPct: 12, taxaFixa: 0, marketplace: 'Mercado Livre' }
  );
  assert.deepEqual(
    computePlatformDefaults2026('Mercado Livre Premium (17%)', 60),
    { comissaoPct: 17, taxaFixa: 6, marketplace: 'Mercado Livre' }
  );
  assert.deepEqual(computePlatformDefaults2026('Shopee CNPJ', 79.99), {
    comissaoPct: 20,
    taxaFixa: 4.5,
    marketplace: 'Shopee',
  });
  assert.deepEqual(computePlatformDefaults2026('Shopee CNPJ', 120), {
    comissaoPct: 14,
    taxaFixa: 20,
    marketplace: 'Shopee',
  });
  assert.deepEqual(computePlatformDefaults2026('Shopee CPF', 220), {
    comissaoPct: 14,
    taxaFixa: 29,
    marketplace: 'Shopee',
  });
  assert.deepEqual(computePlatformDefaults2026('Magalu', 89.9), {
    comissaoPct: 18,
    taxaFixa: 5,
    marketplace: 'Magalu',
  });
});

test('calculatePricingBreakdown computes net profit, margin and break-even accurately', () => {
  const res = calculatePricingBreakdown({
    precoVenda: 100,
    meuCusto: 40,
    impostoPct: 10,
    comissaoPct: 12,
    taxaFixa: 0,
    freteEstimado: 15,
  });
  assert.equal(res.comissaoRs, 12);
  assert.equal(res.impostoRs, 10);
  assert.equal(res.lucroLiquido, 23);
  assert.equal(res.margemPct, 23);
  assert.equal(res.roiPct, 57.5);
});

test('calculateKpis and buildHourlyBattleSeries aggregate listings deterministically', () => {
  const kpis = calculateKpis(INITIAL_LISTINGS);
  assert.ok(kpis.faturamentoHoje > 0);
  assert.ok(kpis.totalVendas > 0);
  assert.equal(
    Number((kpis.faturamentoHoje / kpis.totalVendas).toFixed(2)),
    kpis.ticketMedio
  );

  const series = buildHourlyBattleSeries(INITIAL_LISTINGS);
  assert.equal(series.length, 24);
  assert.equal(series[0].hora, '00h');
  assert.equal(series[23].hora, '23h');
});

test('buildComparativeRows detects zero-stock competitor opportunity alert', () => {
  const rows = buildComparativeRows(INITIAL_LISTINGS);
  const oport = rows.find((r) => r.alertaNivel === 'oportunidade');
  assert.ok(oport, 'Expected at least one opportunity alert from seed data');
});

test('generateSeoTitles enforces 60 character cap and analyzeListingDiagnostic flags bottlenecks', () => {
  const titles = generateSeoTitles(
    'Tapete Higiênico Super Absorvente 30 Unidades',
    'PetPrime',
    'Antivazamento'
  );
  assert.equal(titles.length, 5);
  for (const t of titles) {
    assert.ok(t.length <= 60, `Title exceeded 60 chars: ${t.length}`);
  }

  const diag = analyzeListingDiagnostic({
    titulo: 'Tapete cachorro',
    preco: 79.9,
    fotos: 3,
    visitas30d: 400,
    vendas30d: 2,
  });
  assert.equal(diag.gargalo, 'Conversão');
  assert.equal(diag.taxaConversao, 0.5);
  assert.equal(diag.acoes.length, 3);
});

import {
  buildGeneralRankingRows,
  calculateBattleComparisonScore,
  computeListingTitleSimilarity,
  getSparklineColor,
  inferListingScalability,
  inferListingTrend,
} from './ecommerceLogic';
import { RANKING_STORE_SEED } from '../data/petSeedData';

test('Ranking Geral computes conditional sparkline colors, similarity >= 45%, battle score, and sorted ranking', () => {
  assert.equal(getSparklineColor('up'), '#00E676');
  assert.equal(getSparklineColor('stable'), '#FFD600');
  assert.equal(getSparklineColor('down'), '#FF5252');

  assert.equal(inferListingTrend([4, 5, 6, 9, 12]), 'up');
  assert.equal(inferListingTrend([3, 3, 2, 3, 3]), 'stable');
  assert.equal(inferListingTrend([5, 4, 3, 1, 0]), 'down');

  assert.equal(inferListingScalability(38, 'up'), 'Muito Escalável');
  assert.equal(inferListingScalability(9, 'stable'), 'Média');
  assert.equal(inferListingScalability(4, 'down'), 'Não Escalável');

  const simMatch = computeListingTitleSimilarity(
    'Tapete Higiênico PetPrime Super Seco 80x60cm 30 Unidades',
    'Tapete Higiênico Super Seco Cães 80x60cm 30 Unidades Gel'
  );
  const simUnrelated = computeListingTitleSimilarity(
    'Tapete Higiênico PetPrime Super Seco 80x60cm 30 Unidades',
    'Arranhador Torre Pelúcia Sisal Gatos Adultos Grande'
  );
  assert.ok(simMatch >= 0.45, `Expected >= 0.45 similarity, got ${simMatch}`);
  assert.ok(simUnrelated < 0.45, `Expected < 0.45 similarity, got ${simUnrelated}`);

  const rows = buildGeneralRankingRows(INITIAL_LISTINGS, RANKING_STORE_SEED);
  assert.ok(rows.length >= 5);
  assert.equal(rows[0].posicao, 1);
  assert.ok(rows[0].vendasPeriodo >= rows[1].vendasPeriodo);

  const matched = rows.filter((r) => r.matchedMyListing !== null);
  assert.ok(matched.length >= 2);
  for (const item of matched) {
    assert.ok(item.battleScore !== null && item.battleScore >= 0 && item.battleScore <= 10);
  }

  const scoreCheck = calculateBattleComparisonScore(INITIAL_LISTINGS[0], {
    preco: 84.9,
    full: false,
    catalogo: false,
    nota: 4.5,
    vendasPeriodo: 10,
  });
  assert.ok(scoreCheck >= 8 && scoreCheck <= 10, `Expected high score, got ${scoreCheck}`);
});


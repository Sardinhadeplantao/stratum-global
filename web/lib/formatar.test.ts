import assert from "node:assert/strict";
import { test } from "node:test";
import { classeAgendador, classeCopia, continente, controleFonte, dataHora, datasDocumento, diaHora, faixas, hora, plural, situacao, tipoFonte } from "./formatar.ts";

test("datas em horário de Brasília", () => {
  assert.equal(dataHora("2026-10-16T10:30:00Z"), "16/10/2026, 07:30");
  assert.equal(diaHora("2026-10-16T10:30:00Z"), "16/10, 07:30");
  assert.equal(hora("2026-10-16T10:30:00Z"), "07:30");
  assert.equal(dataHora(null), "—");
  assert.equal(hora("não é data"), "—");
});

test("notícia mostra as duas datas; sem data da fonte, diz isso", () => {
  assert.equal(datasDocumento("2026-10-16T10:30:00Z", "2026-10-16T10:52:00Z"), "publicado 16/10, 07:30 · coletado 16/10, 07:52");
  assert.equal(datasDocumento(null, "2026-10-16T10:52:00Z"), "sem data da fonte · coletado 16/10, 07:52");
});

test("cor do agendador só para estado medido; sem dado é cinza", () => {
  assert.equal(classeAgendador("ok"), "sit-ok");
  assert.equal(classeAgendador("vence_logo"), "sit-parcial");
  assert.equal(classeAgendador("token_invalido"), "sit-falhou");
  assert.equal(classeAgendador(null), "sem-dado");
  assert.equal(classeAgendador("sem_banco"), "sem-dado");
  assert.equal(classeAgendador("aguardando"), "sem-dado");
});

test("cor da cópia do banco: só verde em dia; não conferida é cinza", () => {
  assert.equal(classeCopia("ok"), "sit-ok");
  assert.equal(classeCopia("atrasada"), "sit-falhou");
  assert.equal(classeCopia("nenhuma"), "sit-falhou");
  assert.equal(classeCopia("sem_dado"), "sem-dado");
  assert.equal(classeCopia(undefined), "sem-dado");
});

test("controle da fonte", () => {
  assert.equal(controleFonte("estatal"), "Estatal");
  assert.equal(controleFonte("publico"), "Público");
  assert.equal(controleFonte(null), "—");
});

test("situação desconhecida aparece como sem dado (cinza)", () => {
  assert.deepEqual(situacao("ok"), { texto: "Funcionando", classe: "sit-ok" });
  assert.deepEqual(situacao(undefined), { texto: "Sem dado", classe: "sem-dado" });
  assert.deepEqual(situacao("xyz"), { texto: "Sem dado", classe: "sem-dado" });
});

test("nomes em português", () => {
  assert.equal(continente("South America"), "América do Sul");
  assert.equal(continente("Atlântida"), "Atlântida");
  assert.equal(tipoFonte("social"), "Rede social (pista)");
  assert.equal(tipoFonte(null), "—");
});

test("faixas da legenda vêm dos limites do robô", () => {
  assert.deepEqual(faixas([1, 3, 10, 30]), ["1–2", "3–9", "10–29", "30+"]);
  assert.deepEqual(faixas([1, 2, 5]), ["1", "2–4", "5+"]);
});

test("plural", () => {
  assert.equal(plural(1, "notícia", "notícias"), "1 notícia");
  assert.equal(plural(1200, "notícia", "notícias"), "1.200 notícias");
});

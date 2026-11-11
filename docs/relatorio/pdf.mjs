// Gera os PDFs das Partes 1 e 2 no padrão de relatório de sistematização (CEUB).
// Uso: node pdf.mjs   (lê parte1.html e parte2.html desta pasta; escreve os PDFs em ./saida)
import { createRequire } from "node:module";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
const require = createRequire(import.meta.url);
const puppeteer = require(process.env.PUPPETEER_PATH || "puppeteer");
const dir = path.dirname(fileURLToPath(import.meta.url));
const saida = path.join(dir, "saida");
fs.mkdirSync(saida, { recursive: true });
const partes = [
  ["parte1.html", "EDI-B-CV-VIR-Sistematizacao-Parte1-DIEGO-NUNES-DE-MORAIS.pdf", "Parte 1"],
  ["parte2.render.html", "EDI-B-CV-VIR-Sistematizacao-Parte2-DIEGO-NUNES-DE-MORAIS.pdf", "Parte 2"],
];
const browser = await puppeteer.launch({ executablePath: process.env.CHROME || "/usr/bin/google-chrome", args: ["--no-sandbox"] });
for (const [html, pdf, rotulo] of partes) {
  const page = await browser.newPage();
  await page.goto("file://" + path.join(dir, html), { waitUntil: "networkidle0" });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({
    path: path.join(saida, pdf), format: "A4", printBackground: true, displayHeaderFooter: true,
    margin: { top: "18mm", bottom: "18mm", left: "17mm", right: "17mm" },
    headerTemplate: "<div></div>",
    footerTemplate: `<div style="font-family:'IBM Plex Sans',sans-serif;font-size:7.5pt;color:#64748b;width:100%;padding:0 17mm;display:flex;justify-content:space-between"><span>Mapa Vivo de Risco — Sistematização de Ecossistemas Digitais Inteligentes, ${rotulo} · Diego Nunes de Morais</span><span class="pageNumber"></span></div>`,
  });
  console.log(pdf);
  await page.close();
}
await browser.close();

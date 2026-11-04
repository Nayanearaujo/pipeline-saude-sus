const { chromium } = require("playwright");
const fs = require("node:fs/promises");
const url = "https://pipeline-saude-sus.streamlit.app/";

async function verificar(page, prazoMs = 180000) {
  const fim = Date.now() + prazoMs;
  while (Date.now() < fim) {
    for (const frame of page.frames()) {
      const cards = frame.locator(".sus-card");
      if (await cards.count() === 5 && await cards.nth(4).isVisible()) {
        if (await frame.locator("[data-testid=stException]").count()) {
          throw new Error("O painel apresentou uma excecao.");
        }
        console.log("Dashboard verificado: cinco cartoes renderizados.");
        return;
      }
      const botao = frame.getByRole("button", { name: /Yes, get this app back up/i });
      if (await botao.isVisible().catch(() => false)) {
        console.log("Solicitando inicializacao do aplicativo.");
        await botao.click({ timeout: 10000 });
      }
    }
    await page.waitForTimeout(2000);
  }
  throw new Error("O painel nao apresentou os cinco cartoes dentro do prazo.");
}

async function main() {
  await fs.mkdir("diagnostico-keepalive", { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage();
  try {
    for (let tentativa = 1; tentativa <= 2; tentativa++) {
      try {
        console.log("Tentativa", tentativa);
        const resposta = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
        console.log("HTTP", resposta?.status(), "URL", page.url());
        await verificar(page);
        return;
      } catch (erro) {
        console.error(erro.message);
        await page.screenshot({ path: `diagnostico-keepalive/tentativa-${tentativa}.png`, fullPage: true }).catch(() => {});
        await fs.writeFile(`diagnostico-keepalive/tentativa-${tentativa}.json`, JSON.stringify({
          url: page.url(), frames: page.frames().map(f => f.url()), erro: erro.message
        }, null, 2));
        if (tentativa === 2) throw erro;
      }
    }
  } finally {
    await browser.close();
  }
}
main().catch(erro => { console.error(erro); process.exitCode = 1; });

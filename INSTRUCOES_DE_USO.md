# Guia de Teste Local - LeadScraper

**Ótima notícia:** Você **NÃO** precisa pagar nada para testar e usar sua extensão locally (no seu próprio computador). A taxa de $5 do Google é apenas para quem quer publicar a extensão na "Chrome Web Store" para o público geral. Para uso próprio e desenvolvimento, é **grátis**.

Siga este passo a passo para ver o sistema funcionando agora mesmo:

## Passo 1: Iniciar o "Cérebro" (Backend)

O navegador precisa se comunicar com o seu Python. Abra o terminal na pasta do projeto e rode:

```bash
uvicorn src.api:app --reload
```

*Você deve ver uma mensagem dizendo que o servidor está rodando em `http://127.0.0.1:8000`.*
*Mantenha esse terminal aberto!*

## Passo 2: Instalar a Extensão no Chrome

1.  Abra o Google Chrome.
2.  Na barra de endereço, digite: `chrome://extensions` e aperte Enter.
3.  No canto superior direito, **ative** a opção **"Modo do desenvolvedor"** (Developer mode).
4.  Vai aparecer um botão novo chamado **"Carregar sem compactação"** (Load unpacked). Clique nele.
5.  Uma janela vai abrir. Navegue até a pasta do nosso projeto.
    
    > **Caminho da pasta:** `c:\Users\Barreto\.gemini\antigravity\scratch\Rastre.IA\extension`
    > (Copie e cole esse endereço na barra superior da janela que abriu)

6.  Pronto! O ícone do **LeadScraper** vai aparecer na sua barra do navegador.

## Passo 3: O Teste Real

Agora vem a mágica:

1.  Abra uma nova aba e entre em um site corporativo, por exemplo: [https://openai.com](https://openai.com) ou [https://zoom.us](https://zoom.us).
2.  Clique no ícone do **LeadScraper** (quebra-cabeça/ícone da extensão).
3.  Você verá o botão azul **"Scan Current Domain"**. Clique nele.
4.  Aguarde... (O Python vai rodar o scraper, fazer a busca no Google e verificar os e-mails).
5.  **Resultado:** Os e-mails encontrados aparecerão na janelinha da extensão.

---

### Dicas
- Se der "Erro", verifique se o terminal do Passo 1 ainda está rodando.
- Para ver mais detalhes do que está acontecendo, olhe para o terminal do Passo 1 enquanto a extensão roda. Você verá os logs do backend funcionando.

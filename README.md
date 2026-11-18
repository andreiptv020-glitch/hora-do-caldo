# HORA DO CALDO – sistema de pedidos

- `pc/` → **HORA DO CALDO PC** (cadastro, impressão, contas)
- `mobile/` → **HR DO CALDO APP** (cardápio + mesa + enviar pedido)
- `.github/workflows/` → geram o `.exe` e o `.apk` automaticamente

## Gerar EXE e APK no GitHub
1. Crie conta em github.com → **New repository** (ex: `hora-do-caldo`) → Create.
2. Clique em **uploading an existing file**, arraste TODO o conteúdo desta pasta (incluindo a pasta oculta `.github`) e clique **Commit changes**.
3. Aba **Actions** → aguarde as 2 execuções ficarem verdes (✔), ~3 a 8 min.
4. Clique em cada execução → role até **Artifacts** → baixe `HORA_DO_CALDO_PC` (.exe) e `HR_DO_CALDO_APP` (.apk).
   (Para rodar de novo: Actions → escolha o workflow → **Run workflow**.)

## Instalar e conectar
1. PC e celular no **mesmo Wi-Fi**.
2. Abra `HORA_DO_CALDO_PC.exe` (Windows pede permissão de rede: marque **Redes privadas** → Permitir). O painel abre no navegador e mostra o **endereço** (ex: 192.168.0.10:5000).
3. No PC: cadastre produtos, mesas e configure a impressora (aba Impressora → Imprimir teste).
4. Celular: instale o APK (permita "fontes desconhecidas"), abra, toque em ⚙️ e digite o endereço do PC.
5. Dica: fixe o IP do PC no roteador para o endereço não mudar.

## Impressoras
- **USB**: instale o driver, escolha "USB / Windows" e selecione a impressora.
- **Rede**: escolha "Rede (IP)", informe IP e porta (normalmente 9100).
- **Papel**: 58 mm, 76 mm, 80 mm ou colunas personalizadas.
- Acentos errados? Troque a *página de código* (cp860 / cp850 / cp858).

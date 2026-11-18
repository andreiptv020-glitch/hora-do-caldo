# HR DO CALDO APP (garçom)

Aplicativo Android que o garçom usa para anotar pedidos e enviar para o site.

## Antes de subir para o GitHub
Abra `app/www/config.js` e troque `https://SEU-SITE.COM.BR` pelo endereço do seu site.

## Gerar o APK
1. Crie um repositório no github.com (ex: `hora-do-caldo-app`).
2. Envie TODO o conteúdo desta pasta (incluindo a pasta `.github`): *Add file → Upload files* → arraste tudo → *Commit changes*.
3. Aba **Actions** → aguarde o workflow **Gerar APK** ficar verde (3 a 8 min).
4. Clique na execução → no final da página, em **Artifacts**, baixe `HR_DO_CALDO_APP` (dentro vem o `app-debug.apk`).
5. Instale no celular (permita "fontes desconhecidas") e entre com o usuário/senha de garçom criado no painel do site.

Para gerar de novo depois de mudar algo: Actions → *Gerar APK* → **Run workflow**.

## Observações
- Mudou o endereço do site? Edite `config.js` e envie de novo. Também dá para trocar no próprio app (link "Alterar endereço do site" na tela de login).
- Produtos, categorias e mesas vêm do site: o que você cadastrar lá aparece no app (botão ⟳ atualiza).

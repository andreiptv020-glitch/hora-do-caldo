# HR ENTREGADOR (app de confirmação de entrega)

O entregador abre o app, a câmera lê o QR Code do ticket da entrega, aparecem o cliente e os itens, e o botão **ENTREGA FEITA** atualiza o pedido no site.

## Antes de subir
Confira `app/www/config.js`: o endereço do site já está como `https://loja.harpiabanner.shop` — troque se for outro.

## Gerar o APK
1. Crie um repositório no GitHub (ex: `hora-do-caldo-entregador`).
2. Envie TODO o conteúdo desta pasta (inclusive a pasta `.github`): *Add file → Upload files* → arraste tudo → *Commit changes*.
3. Aba **Actions** → aguarde o workflow **Gerar APK** ficar verde.
4. Na execução, em **Artifacts**, baixe `HR_ENTREGADOR` (contém o `app-debug.apk`) e instale no celular.
5. Entre com um usuário do tipo **Entregador** (criado no painel do site, aba Equipe).

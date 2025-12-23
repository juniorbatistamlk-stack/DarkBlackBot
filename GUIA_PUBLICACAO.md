# 📘 Guia de Publicação de Atualizações

## Sistema de Repositórios Duplos

### Estrutura:
- **Repositório PRIVADO** (`Antigravity/`): Código-fonte completo + geradores
- **Repositório PÚBLICO** (`updates-bot`): Apenas pacotes ZIP + version.json

---

## 🚀 Como Publicar uma Nova Versão

### Passo 1: Criar o Repositório Público (APENAS UMA VEZ)

1. Acesse: https://github.com/new
2. **Repository name**: `updates-bot`
3. **Description**: "Dark Black Bot - Public Updates Distribution"
4. Marque: **Public** ✅
5. **NÃO** marque "Add a README"
6. Clique em **Create repository**

### Passo 2: Preparar a Atualização

1. **Teste seu código** - certifique-se que está tudo funcionando
2. Execute no terminal:
   ```
   python publicar_atualizacao.py
   ```
3. Escolha o tipo de versão:
   - `1` = PATCH (correções de bugs) - 1.0.0 → 1.0.1
   - `2` = MINOR (novas funcionalidades) - 1.0.0 → 1.1.0
   - `3` = MAJOR (mudanças grandes) - 1.0.0 → 2.0.0

4. Digite o CHANGELOG (o que mudou):
   ```
   Exemplo:
   - Corrigido bug na estratégia 6
   - Adicionado suporte para EUR/USD
   - Melhorias de performance
   ```

5. O script vai criar na pasta `updates/`:
   - `darkblack-bot-client-v1.0.1.zip`
   - `version.json`
   - `README.md`

### Passo 3: Publicar no GitHub

1. Dê dois cliques em:
   ```
   PUBLICAR_UPDATES.bat
   ```

2. Se for a **primeira vez**, vai pedir login do GitHub
   - Faça login normalmente

3. Aguarde aparecer "PUBLICADO COM SUCESSO!"

### Passo 4: Verificar

1. Abra: https://github.com/juniorbatistamlk-stack/updates-bot
2. Confirme que apareceu:
   - O arquivo ZIP
   - `version.json`
   - `README.md`

---

## 🔄 Atualização Automática para Clientes

Os clientes vão receber automaticamente porque o `updater.py` verifica:
```
https://raw.githubusercontent.com/juniorbatistamlk-stack/updates-bot/main/version.json
```

Quando o cliente abrir o bot:
1. O bot verifica se há nova versão
2. Pergunta se quer atualizar
3. Baixa o ZIP automaticamente
4. Instala e pede para reiniciar

**Pronto!** 🎉

---

## ⚠️ Importante

### ❌ NÃO envie para o repo público:
- Geradores de licença (`key_gen.py`, etc.)
- Arquivos de licença (`licenses.json`)
- Código-fonte solto (`.py` individuais)

### ✅ APENAS envie:
- Pacote ZIP completo
- `version.json`
- `README.md`

---

## 🆘 Problemas Comuns

### "fatal: remote origin already exists"
- Normal na segunda vez que rodar
- Ignore, o script continua funcionando

### "Push failed"
- Verifique se criou o repositório no GitHub
- Confirme que o nome está correto: `updates-bot`
- Tente fazer login novamente

### Clientes não recebem atualização
- Verifique se `version.json` está no GitHub
- Teste abrindo: https://raw.githubusercontent.com/juniorbatistamlk-stack/updates-bot/main/version.json
- Deve mostrar o JSON com a versão

---

**Dúvidas?** Releia este guia! 📖

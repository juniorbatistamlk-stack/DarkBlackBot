# 📤 GUIA RÁPIDO: Como Enviar Arquivos para o GitHub

## 🎯 Existem 2 Situações Diferentes:

---

## 1️⃣ ATUALIZAR O CÓDIGO-FONTE (Repositório Privado)

**Quando usar:** Sempre que você mexer no código do bot (adicionar features, corrigir bugs, etc.)

### Passo a Passo:

1. **Faça suas alterações** no código (edite arquivos Python, estratégias, etc.)

2. **Abra o arquivo:**
   ```
   ATUALIZAR_GITHUB.bat
   ```
   (Dê dois cliques nele)

3. **Digite o que mudou** quando pedir
   - Exemplo: "Corrigido bug na estratégia 6"
   - Exemplo: "Adicionado novo indicador"

4. **Pronto!** O código vai para o repositório PRIVADO (`dev-workspace`)

---

## 2️⃣ PUBLICAR NOVA VERSÃO PARA CLIENTES (Repositório Público)

**Quando usar:** Quando você terminar uma versão e quiser que os clientes baixem

### Passo a Passo:

#### Etapa 1: Criar o Pacote

1. **Abra o terminal** (PowerShell ou CMD) na pasta do projeto

2. **Execute:**
   ```bash
   python publicar_atualizacao.py
   ```

3. **Escolha o tipo de versão:**
   - Digite `1` para PATCH (correções pequenas) - Ex: 1.0.0 → 1.0.1
   - Digite `2` para MINOR (novas funcionalidades) - Ex: 1.0.0 → 1.1.0
   - Digite `3` para MAJOR (mudanças grandes) - Ex: 1.0.0 → 2.0.0

4. **Digite o CHANGELOG** (o que mudou):
   ```
   Exemplo:
   - Corrigido bug na conexão
   - Melhorada estratégia 6
   - Adicionado suporte para novos ativos
   ```
   (Pressione ENTER duas vezes para finalizar)

5. **Aguarde** - O script vai criar:
   - `darkblack-bot-client-vX.X.X.zip`
   - `version.json` atualizado

#### Etapa 2: Enviar para o GitHub

1. **Abra o arquivo:**
   ```
   PUBLICAR_UPDATES.bat
   ```
   (Dê dois cliques nele)

2. **Aguarde** a mensagem "PUBLICADO COM SUCESSO!"

3. **Pronto!** Os clientes vão receber a atualização automaticamente!

---

## 📋 Resumo Visual

```
┌─────────────────────────────────────────┐
│  Mexeu no código?                       │
│  ↓                                      │
│  ATUALIZAR_GITHUB.bat                   │
│  ↓                                      │
│  Código vai para dev-workspace (PRIVADO)│
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Versão pronta para clientes?           │
│  ↓                                      │
│  python publicar_atualizacao.py         │
│  ↓                                      │
│  PUBLICAR_UPDATES.bat                   │
│  ↓                                      │
│  Clientes recebem atualização!          │
└─────────────────────────────────────────┘
```

---

## ⚠️ Dicas Importantes

### ✅ FAÇA:
- Sempre teste o código antes de publicar para clientes
- Use mensagens claras no changelog
- Incremente a versão corretamente (PATCH para bugs, MINOR para features)

### ❌ NÃO FAÇA:
- Não envie código quebrado para clientes
- Não esqueça de rodar `ATUALIZAR_GITHUB.bat` depois de mexer no código
- Não pule versões (ex: 1.0.1 → 1.0.5)

---

## 🆘 Problemas Comuns

### "Git não reconhecido"
**Solução:** Use os arquivos `.bat` em vez de comandos diretos

### "Push failed"
**Solução:** 
1. Verifique sua conexão com internet
2. Tente rodar novamente
3. Se pedir login, faça login no GitHub

### "Arquivo não encontrado"
**Solução:** Certifique-se de estar na pasta `Antigravity` quando executar os comandos

---

## 📞 Fluxo Completo de Trabalho

**Dia a dia:**
1. Mexe no código
2. Testa localmente
3. Roda `ATUALIZAR_GITHUB.bat`
4. Repete

**Quando tiver versão pronta:**
1. Testa tudo
2. `python publicar_atualizacao.py`
3. `PUBLICAR_UPDATES.bat`
4. Clientes recebem!

---

**Simples assim!** 🚀

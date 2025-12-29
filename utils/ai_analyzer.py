# utils/ai_analyzer.py
"""
Sistema de Analise com IA via OpenRouter para validar sinais de trading
Com integração de memória para aprendizado contínuo
"""
import os
import time
from openai import OpenAI

class AIAnalyzer:
    def __init__(self, api_key, provider="openrouter", memory=None):
        """
        Inicializa o cliente IA com suporte a múltiplos provedores
        Providers: 'openrouter', 'groq', 'gemini'
        """
        self.provider = provider.lower()
        # Permite override de modelo por env sem alterar UX
        # - AI_MODEL: fallback geral
        # - <PROVIDER>_MODEL: específico do provedor
        def _env_model(provider_name: str) -> str | None:
            return (
                os.getenv(f"{provider_name.upper()}_MODEL")
                or os.getenv("AI_MODEL")
                or None
            )
        
        if self.provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
            self.model = _env_model("groq") or "llama-3.3-70b-versatile"
            print(f"[AI] Conectando via GROQ ({self.model})")
        elif self.provider == "gemini":
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
            self.model = _env_model("gemini") or "gemini-2.0-flash"
            print(f"[AI] Conectando via GEMINI ({self.model})")
        else:
            # Default: OpenRouter
            base_url = "https://openrouter.ai/api/v1"
            self.model = _env_model("openrouter") or "meta-llama/llama-3.3-70b-instruct:free"
            print(f"[AI] Conectando via OPENROUTER ({self.model})")

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=30.0,
        )
        self.memory = memory
        self.last_analysis_time = 0
        self.min_interval = 2.0
        self._logger = None
        self.enabled = True
        self.disabled_reason = None
        if memory:
            print(f"[AI] Memoria integrada: {memory.stats['total_trades']} trades carregados")

    def set_logger(self, log_func):
        """Define logger opcional (ex: painel do sistema)."""
        self._logger = log_func

    def _log(self, msg):
        if self._logger:
            self._logger(msg)
        else:
            # manter prints como fallback (quando não há UI)
            print(msg)

    def is_enabled(self):
        return bool(self.enabled)
    
    def check_connection(self):
        """Testa se a API Key está válida fazendo uma requisição mínima"""
        try:
            # Teste rápido: pedir para dizer "OLÁ"
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "HI"}],
                max_tokens=5,
            )
            return True, "Conexão OK"
        except Exception as e:
            msg = str(e)

            # Tenta extrair status code de exceções do SDK (openai>=1.x)
            status_code = getattr(e, "status_code", None)
            if status_code is None:
                resp = getattr(e, "response", None)
                status_code = getattr(resp, "status_code", None)

            # 429 normalmente significa quota/rate-limit (chave pode estar correta)
            if status_code == 429 or "429" in msg or "rate" in msg.lower() or "quota" in msg.lower() or "RESOURCE_EXHAUSTED" in msg:
                return True, "Chave OK, mas limite/QUOTA atingido (429) — tente novamente em alguns minutos ou ajuste quota/faturamento"

            # Erros típicos de autenticação/permissão
            if status_code in (401, 403) or "401" in msg or "403" in msg or "unauthorized" in msg.lower() or "permission" in msg.lower() or "api key" in msg.lower():
                return False, "Chave inválida/sem permissão (401/403)"

            if status_code == 404 or "404" in msg:
                return False, "Modelo não encontrado (404)"

            if status_code == 400 or "400" in msg or "bad request" in msg.lower():
                return False, "Requisição inválida (400) — verifique modelo/provedor"

            # Fallback: não classificar como inválida sem evidência
            short = msg.replace("\n", " ").strip()
            if len(short) > 180:
                short = short[:180] + "..."
            return False, f"Erro ao validar: {short}"
            
    def set_memory(self, memory):
        """Define a memoria para aprendizado"""
        self.memory = memory
        print(f"[AI] Memoria conectada: {memory.stats['total_trades']} trades")
    
    def calculate_trade_score(self, signal, trend, sr_zones, candles, desc):
        """
        Sistema de Score Objetivo para Opções Binárias
        Retorna: (score 0-100, breakdown dict)
        
        Mínimo para executar: 50 pontos
        """
        score = 40  # Base
        breakdown = {}
        
        # 1. TENDÊNCIA (+15 a favor, -15 contra)
        trend_upper = str(trend).upper()
        if signal == "CALL" and "UP" in trend_upper:
            score += 15
            breakdown["trend"] = "+15 (a favor)"
        elif signal == "PUT" and "DOWN" in trend_upper:
            score += 15
            breakdown["trend"] = "+15 (a favor)"
        elif "LATERAL" in trend_upper:
            score -= 5
            breakdown["trend"] = "-5 (lateral)"
        else:
            score -= 15
            breakdown["trend"] = "-15 (contra)"
        
        # 2. ZONA S/R (+10 se perto, -10 se longe)
        has_sr = False
        if isinstance(sr_zones, dict):
            has_sr = len(sr_zones.get('support', [])) > 0 or len(sr_zones.get('resistance', [])) > 0
        elif isinstance(sr_zones, list):
            has_sr = len(sr_zones) > 0
        
        if has_sr:
            score += 10
            breakdown["sr"] = "+10 (zona S/R)"
        else:
            score -= 10
            breakdown["sr"] = "-10 (sem zona)"
        
        # 3. PADRÃO DE VELA (+10 se forte)
        desc_upper = str(desc).upper()
        strong_patterns = ["MARUBOZU", "ENGOLFO", "HAMMER", "SHOOTING", "PIN_BAR", "SOLDIERS", "CROWS", "MORNING", "EVENING"]
        if any(p in desc_upper for p in strong_patterns):
            score += 10
            breakdown["pattern"] = "+10 (padrão forte)"
        elif "FLUXO" in desc_upper or "IMPULSO" in desc_upper:
            score += 8
            breakdown["pattern"] = "+8 (fluxo/impulso)"
        else:
            breakdown["pattern"] = "+0 (padrão comum)"
        
        # 4. HISTÓRICO (+15 se bom, -10 se ruim)
        if self.memory:
            try:
                pattern = desc.split("|")[0].strip() if "|" in desc else desc
                stats = getattr(self.memory, 'stats', {})
                patterns = stats.get("patterns", {})
                if pattern in patterns:
                    p = patterns[pattern]
                    wins = int(p.get("wins") or 0)
                    total = int(p.get("total") or 0)
                    if total >= 5:
                        win_rate = (wins / total) * 100
                        if win_rate >= 60:
                            score += 15
                            breakdown["history"] = f"+15 (WR:{win_rate:.0f}%)"
                        elif win_rate < 45:
                            score -= 10
                            breakdown["history"] = f"-10 (WR:{win_rate:.0f}%)"
                        else:
                            breakdown["history"] = f"+0 (WR:{win_rate:.0f}%)"
                    else:
                        breakdown["history"] = "+0 (poucos trades)"
                else:
                    breakdown["history"] = "+0 (padrão novo)"
            except:
                breakdown["history"] = "+0 (erro)"
        else:
            breakdown["history"] = "+0 (sem memória)"
        
        # 5. ÚLTIMA VELA (penaliza contradição)
        if candles and len(candles) >= 1:
            last = candles[-1]
            last_direction = "CALL" if last.get('close', 0) > last.get('open', 0) else "PUT"
            if last_direction != signal:
                score -= 5
                breakdown["last_candle"] = "-5 (contradição)"
            else:
                score += 5
                breakdown["last_candle"] = "+5 (confirmação)"
        
        score = max(0, min(100, score))
        return score, breakdown

    
    def analyze_signal(self, signal, desc, candles, sr_zones, trend, pair, ai_context=None, strategy_logic=None):
        """
        Analisa um sinal usando OpenRouter COM CONTEXTO DA MEMÓRIA
        ai_context: dicionário opcional com 'trend', 'setup', 'pattern', 'sr', 'sr_strength'
        strategy_logic: regras específicas da estratégia (string)
        """
        # Rate limiting
        elapsed = time.time() - self.last_analysis_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        try:
            # Formatar dados
            candles_data = self._format_candles(candles[-10:]) if len(candles) >= 10 else "Dados insuficientes"
            
            # Obter contexto da memória
            memory_context = self._get_memory_context(desc)
            
            # Criar prompt COM MEMÓRIA E LÓGICA
            prompt = self._create_prompt_with_memory(
                signal, desc, candles_data, sr_zones, trend, pair, memory_context, strategy_logic
            )
            
            # Chamar OpenRouter
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Voce e um TRADER PROFISSIONAL DE OPCOES BINARIAS com 10+ anos de experiencia. Sua missao e PRESERVAR O CAPITAL e so entrar em trades de ALTA PROBABILIDADE. Em duvida? NAO OPERE. Qualidade > Quantidade."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4, # Mais criativo/agressivo
                max_tokens=150,
            )
            
            self.last_analysis_time = time.time()
            
            confirm, confidence, reason = self._parse_response(response.choices[0].message.content)
            
            # Ajustar confiança baseado no win rate histórico (mas SEM BLOQUEAR AUTOMATICAMENTE)
            confidence = self._adjust_confidence_by_winrate(confidence, desc)

            # NÃO BLOQUEAR MAIS POR STATS - Deixar a IA decidir no prompt
            # O cérebro (IA) tem a palavra final, não a tabela de excel.
            # if self._should_block_by_winrate(desc): ... -> REMOVIDO
            
            return confirm, confidence, reason
            
        except TimeoutError:
            self._log("[AI] ⏱️ TIMEOUT - usando fallback")
            return True, 70, "IA timeout (fallback)"
        except Exception as e:
            error_msg = str(e)
            
            if "rate" in error_msg.lower() or "429" in error_msg or "quota" in error_msg.lower():
                self._log("[AI] ⚠️ RATE LIMIT - usando fallback")
                return True, 100, "IA limite (fallback)"
            
            # Mute specific noisy errors (like 401 User not found / Invalid Key)
            if "401" in error_msg or "User not found" in error_msg:
                # Desabilita IA para não ficar 'confirmando' sem realmente analisar
                self.enabled = False
                self.disabled_reason = "Chave inválida/401"
                self._log("[AI] ❌ Chave inválida (401). IA desabilitada nesta sessão.")
                return True, 100, "IA desabilitada (chave inválida)"

            self._log(f"[AI] ❌ Erro: {error_msg}")
            return True, 70, "AI indisponivel"
    
    # ... (métodos auxiliares mantidos) ...

    def _should_block_by_winrate(self, pattern_desc):
        """
        [DESATIVADO] A IA agora decide tudo. Não bloqueamos mais por estatística fria.
        Mantido apenas para compatibilidade de interface se necessário.
        """
        return False
    
    def _get_memory_context(self, desc):
        """Obtém contexto COMPLETO da memória para o prompt (todas as estratégias)"""
        if not self.memory:
            return "Sem historico disponivel."
        
        try:
            pattern = desc.split("|")[0].strip() if "|" in desc else desc
            
            # Estatísticas gerais - verificar se existe
            stats = getattr(self.memory, 'stats', {})
            if not isinstance(stats, dict):
                stats = {}
            
            total_trades = stats.get('total_trades', 0)
            win_rate = stats.get('win_rate', 0)
            context = f"=== HISTORICO GLOBAL (TODAS ESTRATEGIAS) ===\n"
            context += f"Total: {total_trades} trades | Win Rate Global: {win_rate:.1f}%\n"
            
            # Últimos 5 trades (qualquer estratégia)
            history = getattr(self.memory, 'history', [])
            if history and len(history) > 0:
                last_5 = history[-5:][::-1]  # Últimos 5, do mais recente
                context += f"\nULTIMOS 5 TRADES:\n"
                for t in last_5:
                    result = t.get('result', '?')
                    pair = t.get('pair', '?')
                    pat = t.get('pattern', '?')[:25]
                    emoji = "✅" if result == "WIN" else "❌" if result == "LOSS" else "🔄"
                    context += f"  {emoji} {pair} | {pat}\n"
            
            # Performance por par (se disponível)
            patterns = stats.get("patterns", {})
            pair_stats = {}
            for h in history[-50:]:  # Analisar últimos 50 trades
                p = h.get('pair', 'UNKNOWN')
                if p not in pair_stats:
                    pair_stats[p] = {'wins': 0, 'losses': 0}
                if h.get('result') == 'WIN':
                    pair_stats[p]['wins'] += 1
                elif h.get('result') == 'LOSS':
                    pair_stats[p]['losses'] += 1
            
            if pair_stats:
                context += f"\nPERFORMANCE POR ATIVO (ultimos 50):\n"
                for pair, ps in sorted(pair_stats.items(), key=lambda x: x[1]['wins'] - x[1]['losses'], reverse=True)[:5]:
                    total = ps['wins'] + ps['losses']
                    wr = (ps['wins'] / max(total, 1)) * 100
                    emoji = "🔥" if wr >= 60 else "⚠️" if wr < 45 else "📊"
                    context += f"  {emoji} {pair}: {wr:.0f}% ({total} trades)\n"
            
            # Estatísticas do padrão específico
            if pattern in patterns:
                p = patterns[pattern]
                wins = int(p.get("wins") or 0)
                total = int(p.get("total") or 0)
                pattern_rate = (wins / max(total, 1) * 100)
                if pattern_rate >= 60:
                    context += f"\n✅ PADRAO ATUAL ({pattern[:30]}): Win Rate {pattern_rate:.0f}% - BOM HISTORICO!\n"
                elif pattern_rate < 40 and total >= 5:
                    context += f"\n⚠️ PADRAO ATUAL ({pattern[:30]}): Win Rate {pattern_rate:.0f}% - CUIDADO!\n"
                else:
                    context += f"\n📊 PADRAO ATUAL ({pattern[:30]}): Win Rate {pattern_rate:.0f}%\n"
            else:
                context += f"\n🆕 PADRAO ATUAL: Novo padrao, sem historico.\n"
            
            # Padrões a EVITAR (win rate < 40% com 5+ trades)
            avoid_patterns = []
            prefer_patterns = []
            for pname, pdata in patterns.items():
                total = int(pdata.get("total") or 0)
                wins = int(pdata.get("wins") or 0)
                if total >= 5:
                    wr = (wins / total) * 100
                    if wr < 40:
                        avoid_patterns.append((pname[:20], wr, total))
                    elif wr >= 60:
                        prefer_patterns.append((pname[:20], wr, total))
            
            if avoid_patterns:
                context += f"\n🚫 PADROES A EVITAR:\n"
                for ap in avoid_patterns[:3]:
                    context += f"   ❌ {ap[0]} ({ap[1]:.0f}% em {ap[2]} trades)\n"
            
            if prefer_patterns:
                context += f"\n🎯 PADROES QUE MAIS FUNCIONAM:\n"
                for pp in sorted(prefer_patterns, key=lambda x: x[1], reverse=True)[:3]:
                    context += f"   ✅ {pp[0]} ({pp[1]:.0f}% em {pp[2]} trades)\n"
            
            return context
        except Exception as e:
            return f"Contexto indisponivel: {e}"
    
    def _format_candles(self, candles):
        """Formata velas para o prompt"""
        formatted = []
        for c in candles[-10:]:
            direction = "VERDE" if c['close'] > c['open'] else "VERMELHA"
            body = abs(c['close'] - c['open'])
            range_total = c['high'] - c['low']
            body_pct = (body / range_total * 100) if range_total > 0 else 0
            # Mini “leitura de gráfico”: corpo% e presença de pavios
            upper_wick = c['high'] - max(c['open'], c['close'])
            lower_wick = min(c['open'], c['close']) - c['low']
            wick_tag = ""
            if range_total > 0:
                if upper_wick / range_total > 0.35:
                    wick_tag += "↑"
                if lower_wick / range_total > 0.35:
                    wick_tag += "↓"
            formatted.append(f"{direction}({body_pct:.0f}%){wick_tag}")
        return " | ".join(formatted)
    
    def _create_prompt_with_memory(self, signal, desc, candles_data, zones, trend, pair, memory_context, strategy_logic=None):
        """Cria prompt com contexto da memória"""
        # Resumo S/R compacto
        zones_summary = "0"
        try:
            if isinstance(zones, dict):
                sup = zones.get('support') or []
                res = zones.get('resistance') or []
                zones_summary = f"S:{len(sup)} R:{len(res)}"
            elif isinstance(zones, list):
                zones_summary = str(len(zones))
        except Exception:
            zones_summary = "?"

        return f"""ANALISE DE TRADING - OPCOES BINARIAS (PROFISSIONAL)

{memory_context}
{chr(10) + "REGRAS DA ESTRATEGIA:" + chr(10) + strategy_logic if strategy_logic else ""}

SINAL PROPOSTO:
- Par: {pair}
- Sinal: {signal}
- Padrao: {desc}
- Tendencia: {trend}
- Zonas S/R: {zones_summary}
- Ultimas 10 velas: {candles_data}

=== VOCE E UM TRADER PROFISSIONAL DE OPCOES BINARIAS ===

REGRAS DE OURO (SEGUIR RIGOROSAMENTE):
1. EM DUVIDA? NAO OPERE. Preservar capital e prioridade #1.
2. CONFLUENCIA OBRIGATORIA: So confirme com 2+ fatores alinhados:
   - Tendencia + S/R + Padrao de vela = ENTRADA FORTE
   - Apenas 1 fator = REJEITAR
3. CONTRA-TENDENCIA: So opere se houver EXAUSTAO CLARA (pavio longo + volume).
4. HISTORICO: Se padrao tem <45% win rate no historico, REJEITE.
5. TIMING: Entrada no "meio do nada" (longe de S/R) = REJEITAR.
6. VELA ATUAL: Se a ultima vela contradiz o sinal, REJEITE.
7. LATERALIZACAO: Muitos pavios sem direcao clara = REJEITE.

CHECKLIST ANTES DE CONFIRMAR:
[ ] Tendencia clara? (EMA alinhadas ou estrutura HH/HL ou LH/LL)
[ ] Proximo de S/R? (Nao operar no "vacuo")
[ ] Padrao de vela valido? (Corpo expressivo, pavio coerente)
[ ] Sem contradicao na ultima vela?
[ ] Historico OK? (Padrao nao esta na lista de evitar)

SE 4+ ITENS = SIM → CONFIRMAR
SE 3 OU MENOS = REJEITAR

RESPONDA APENAS SEGUINDO ESTE MODELO (EM PORTUGUES):
DECISAO: CONFIRMAR ou REJEITAR
CONFIANCA: 0-100
MOTIVO: [Explicacao tecnica curta - max 50 caracteres]"""
    
    def _adjust_confidence_by_winrate(self, confidence, pattern_desc):
        """
        Ajusta confiança baseado no win rate histórico do padrão
        
        Win rate >70%  → +25 (padrão MUITO comprovado)
        Win rate 60-70% → +15 (padrão BOM)
        Win rate 50-60% → ±0 (padrão NEUTRO)
        Win rate <50%  → -5 (padrão NOVO)
        """
        if not self.memory:
            return confidence
        
        try:
            pattern = pattern_desc.split("|")[0].strip() if "|" in pattern_desc else pattern_desc
            stats = getattr(self.memory, 'stats', {})
            
            if not isinstance(stats, dict):
                return confidence
            
            patterns = stats.get("patterns", {})
            if pattern not in patterns:
                # Padrão novo: não penaliza; garante piso 60 para operar e aprender
                return max(confidence, 60)
            
            p = patterns[pattern]
            wins = int(p.get("wins") or 0)
            total = int(p.get("total") or 0)
            
            if total == 0:
                return confidence
            
            win_rate = (wins / total) * 100
            
            if win_rate > 70:
                return min(100, confidence + 25)
            elif win_rate >= 60:  # 60-70%
                return min(100, confidence + 15)
            elif win_rate >= 50:  # 50-60%
                return max(confidence, 65)  # piso leve para confirmar e aprender
            else:  # <50%
                return max(confidence, 60)  # não penaliza: deixa entrar para ganhar histórico
        
        except Exception:
            return confidence

    def _should_block_by_winrate(self, pattern_desc):
        """
        [DESATIVADO] A IA agora decide tudo. Não bloqueamos mais por estatística fria.
        Mantido apenas para compatibilidade de interface se necessário.
        """
        return False
    
    def _parse_response(self, response_text):
        """Parseia resposta da IA"""
        text = response_text.upper()
        
        confirm = "CONFIRMAR" in text
        
        confidence = 70
        import re
        conf_match = re.search(r'CONFIANCA[:\s]*(\d+)', text)
        if conf_match:
            confidence = min(100, max(0, int(conf_match.group(1))))
        
        reason = "Analise com memoria"
        lines = response_text.split('\n')
        for line in lines:
            if 'MOTIVO' in line.upper():
                reason = line.split(':', 1)[-1].strip()[:50]
                break
        
        if not confirm:
            confidence = min(confidence, 45)
        
        return confirm, confidence, reason

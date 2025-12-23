# utils/ai_analyzer.py
"""
Sistema de Analise com IA via OpenRouter para validar sinais de trading
Com integração de memória para aprendizado contínuo
"""
import time
from openai import OpenAI

class AIAnalyzer:
    def __init__(self, api_key, memory=None):
        """Inicializa o cliente OpenRouter com memória"""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.model = "meta-llama/llama-3.3-70b-instruct:free"
        self.memory = memory
        self.last_analysis_time = 0
        self.min_interval = 2.0
        print(f"[AI] OpenRouter inicializado com modelo: {self.model}")
        if memory:
            print(f"[AI] Memoria integrada: {memory.stats['total_trades']} trades carregados")
    
    def set_memory(self, memory):
        """Define a memoria para aprendizado"""
        self.memory = memory
        print(f"[AI] Memoria conectada: {memory.stats['total_trades']} trades")
    
    def analyze_signal(self, signal, desc, candles, sr_zones, trend, pair):
        """
        Analisa um sinal usando OpenRouter COM CONTEXTO DA MEMÓRIA
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
            
            # Criar prompt COM MEMÓRIA
            prompt = self._create_prompt_with_memory(
                signal, desc, candles_data, sr_zones, trend, pair, memory_context
            )
            
            # Chamar OpenRouter
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Voce e um trader profissional de opcoes binarias. Use o historico de trades para tomar decisoes mais inteligentes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150,
                timeout=5
            )
            
            self.last_analysis_time = time.time()
            
            return self._parse_response(response.choices[0].message.content)
            
        except Exception as e:
            error_msg = str(e)
            
            if "rate" in error_msg.lower() or "429" in error_msg or "quota" in error_msg.lower():
                print("[AI] RATE LIMIT - OpenRouter excedeu limite")
                return True, 100, "IA limite (fallback)"
            
            # Mute specific noisy errors (like 401 User not found / Invalid Key)
            if "401" in error_msg or "User not found" in error_msg:
                # Silently fail for invalid key
                return True, 70, "AI indisponivel (Key)"

            print(f"[AI ERROR] {error_msg}")
            return True, 70, "AI indisponivel"
    
    def _get_memory_context(self, desc):
        """Obtém contexto da memória para o prompt"""
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
            context = f"HISTORICO GERAL: {total_trades} trades | Win Rate: {win_rate:.1f}%\n"
            
            # Estatísticas do padrão específico (opcional)
            patterns = stats.get("patterns", {})
            if pattern in patterns:
                p = patterns[pattern]
                wins = int(p.get("wins") or 0)
                total = int(p.get("total") or 0)
                pattern_rate = (wins / max(total, 1) * 100)
                context += f"PADRAO ATUAL ({pattern}): Win Rate {pattern_rate:.0f}%\n"
            else:
                context += f"PADRAO ATUAL: Novo padrao, sem historico.\n"
            
            # Melhores padrões (se método existir)
            if hasattr(self.memory, 'get_best_patterns'):
                best = self.memory.get_best_patterns(min_trades=5)[:3]
                if best:
                    context += "MELHORES PADROES: "
                    context += ", ".join([f"{p.get('name', 'N/A')[:20]}({p.get('win_rate', 0):.0f}%)" for p in best])
                    context += "\n"
            
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
            formatted.append(f"{direction}({body_pct:.0f}%)")
        return " | ".join(formatted)
    
    def _create_prompt_with_memory(self, signal, desc, candles_data, zones, trend, pair, memory_context):
        """Cria prompt com contexto da memória"""
        return f"""ANALISE DE TRADING COM APRENDIZADO

{memory_context}

SINAL PROPOSTO:
- Par: {pair}
- Sinal: {signal}
- Padrao: {desc}
- Tendencia: {trend}
- Zonas S/R: {len(zones)} detectadas
- Ultimas 10 velas: {candles_data}

INSTRUCOES:
1. Use o HISTORICO para decidir - se o padrao tem win rate alto, confirme
2. Se o padrao tem win rate baixo (<50%), rejeite
3. Considere os ultimos resultados (sequencias de WIN/LOSS)
4. Novos padroes: seja cauteloso (confianca media)

RESPONDA APENAS:
DECISAO: CONFIRMAR ou REJEITAR
CONFIANCA: 0-100
MOTIVO: maximo 15 palavras baseado no historico"""
    
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

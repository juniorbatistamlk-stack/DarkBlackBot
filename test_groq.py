"""
Teste rápido da API Groq para diagnosticar problema
"""
import sys
import os

# Testar importação
try:
    from groq import Groq
    print("[OK] Groq importado com sucesso")
except ImportError as e:
    print(f"[ERRO] Erro ao importar Groq: {e}")
    sys.exit(1)

# Testar conexão
api_key = os.environ.get("GROQ_API_KEY", "SUA_KEY_AQUI")

try:
    client = Groq(api_key=api_key)
    print("[OK] Cliente Groq criado")
    
    # Testar chamada simples
    print("\nTestando chamada a API...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": "Responda apenas: OK"
            }
        ],
        temperature=0.3,
        max_tokens=50
    )
    
    result = response.choices[0].message.content
    print(f"[OK] Resposta da IA: {result}")
    print("\n[SUCESSO] GROQ FUNCIONANDO PERFEITAMENTE!")
    
except Exception as e:
    print(f"\n[ERRO] ERRO NA API GROQ:")
    print(f"Tipo: {type(e).__name__}")
    print(f"Mensagem: {str(e)}")
    
    if "api_key" in str(e).lower():
        print("\n[SOLUCAO] API Key invalida ou expirada")
    elif "model" in str(e).lower():
        print("\n[SOLUCAO] Modelo nao existe ou foi renomeado")
    elif "rate" in str(e).lower():
        print("\n[SOLUCAO] Limite de requisicoes excedido")
    else:
        print("\n[SOLUCAO] Verifique sua conexao com internet")

"""Teste rapido da API Gemini"""
import google.generativeai as genai

import os
api_key = os.environ.get("GEMINI_API_KEY", "SUA_KEY_AQUI")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    print("[OK] Gemini configurado")
    
    response = model.generate_content("Responda apenas: OK")
    print(f"[OK] Resposta: {response.text}")
    print("\n[SUCESSO] Gemini funcionando!")
    
except Exception as e:
    print(f"\n[ERRO] {type(e).__name__}")
    print(f"Mensagem: {str(e)}")

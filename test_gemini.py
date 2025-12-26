"""Teste rapido da API Gemini"""
import google.generativeai as genai

import os
api_key = os.environ.get("GEMINI_API_KEY", "SUA_KEY_AQUI")
model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
do_list = os.environ.get("GEMINI_LIST_MODELS", "0") in ("1", "true", "TRUE", "yes", "YES")

try:
    genai.configure(api_key=api_key)
    if do_list:
        print("[INFO] Listando modelos disponíveis...")
        for m in genai.list_models():
            # m.name costuma vir como 'models/<nome>'
            print(m.name)
        raise SystemExit(0)

    model = genai.GenerativeModel(model_name)
    print(f"[OK] Gemini configurado (modelo: {model_name})")
    
    response = model.generate_content("Responda apenas: OK")
    print(f"[OK] Resposta: {response.text}")
    print("\n[SUCESSO] Gemini funcionando!")
    
except Exception as e:
    print(f"\n[ERRO] {type(e).__name__}")
    print(f"Mensagem: {str(e)}")

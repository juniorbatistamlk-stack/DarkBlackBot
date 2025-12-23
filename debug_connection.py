
import socket
import ssl
import sys
import time
from urllib.request import urlopen
from urllib.error import URLError

def log(msg, status="INFO"):
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "ERROR": "\033[91m",
        "WARNING": "\033[93m",
        "RESET": "\033[0m"
    }
    print(f"{colors.get(status, '')}[{status}] {msg}{colors['RESET']}")

def check_dns(hostname):
    log(f"Resolvendo DNS para {hostname}...", "INFO")
    try:
        ip = socket.gethostbyname(hostname)
        log(f"DNS Resolvido: {hostname} -> {ip}", "SUCCESS")
        return ip
    except socket.gaierror as e:
        log(f"Falha no DNS: {e}", "ERROR")
        return None

def check_tcp(ip, port):
    log(f"Testando conexão TCP com {ip}:{port}...", "INFO")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        start = time.time()
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            elapsed = (time.time() - start) * 1000
            log(f"Porta {port} aberta via TCP ({elapsed:.2f}ms)", "SUCCESS")
            return True
        else:
            log(f"Porta {port} fechada ou bloqueada (Erro: {result})", "ERROR")
            return False
    except Exception as e:
        log(f"Erro no teste TCP: {e}", "ERROR")
        return False

def check_https(url):
    log(f"Testando requisição HTTPS para {url}...", "INFO")
    try:
        start = time.time()
        # Set timeout to 15 seconds
        response = urlopen(url, timeout=15)
        elapsed = (time.time() - start) * 1000
        code = response.getcode()
        log(f"HTTPS Sucesso! Código: {code} ({elapsed:.2f}ms)", "SUCCESS")
        return True
    except URLError as e:
        log(f"Falha HTTPS: {e.reason}", "ERROR")
        return False
    except Exception as e:
        log(f"Erro HTTPS: {e}", "ERROR")
        return False

def main():
    print("="*60)
    print("DIAGNÓSTICO DE REDE - IQ OPTION")
    print("="*60)
    
    target_host = "iqoption.com"
    target_url = "https://iqoption.com"
    
    # 1. Check DNS
    ip = check_dns(target_host)
    
    if not ip:
        print("\nDIAGNÓSTICO: ERRO CRÍTICO")
        print("Seu computador não consegue encontrar o endereço de IP da IQ Option.")
        print("Solução: Tente mudar seu DNS para Google (8.8.8.8) ou Cloudflare (1.1.1.1).")
        return

    print("-" * 30)
    
    # 2. Check TCP 443
    tcp_ok = check_tcp(ip, 443)
    
    print("-" * 30)
    
    # 3. Check HTTPS Download
    http_ok = check_https(target_url)
    
    print("-" * 30)
    
    # 4. Check WebSocket Domain (iqoption.com/echo/websocket)
    ws_host = "ws.iqoption.com" # Exemplo, o real usa wss://iqoption.com/echo/websocket
    # Mas vamos testar o dominio principal que geralmente é o endpoint
    
    print("\n" + "="*60)
    if tcp_ok and http_ok:
        log("✅ CONEXÃO ESTÁVEL", "SUCCESS")
        print("Seu computador consegue acessar a IQ Option normalmente.")
        print("Se o bot não conecta, verifique:")
        print("1. Se login/senha estão corretos")
        print("2. Se a IQ Option bloqueou temporariamente sua API")
    else:
        log("❌ BLOQUEIO DETECTADO", "ERROR")
        print("O sistema não consegue conectar com a IQ Option.")
        print("Possíveis causas:")
        print("1. Bloqueio do seu Provedor de Internet (ISP)")
        print("2. Bloqueio de Firewall/Antivírus")
        print("Soluções:")
        print("- Use uma VPN")
        print("- Teste rotear internet 4G do celular")

if __name__ == "__main__":
    main()

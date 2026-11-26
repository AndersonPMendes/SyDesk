"""Aplica a marca SyDesk (SynogConnect) no codigo do RustDesk antes de compilar.

Roda na raiz do codigo do RustDesk (o workflow sydesk-windows.yml chama sozinho):
    python sydesk/aplicar-marca.py
Variaveis opcionais (ficam embutidas no programa):
    SYDESK_SERVIDOR  endereco do servidor (ex.: srv2199784.hstgr.cloud)
    SYDESK_KEY       Key publica do servidor (conteudo de id_ed25519.pub)
So usa a biblioteca padrao do Python. Para se algo nao for encontrado (o RustDesk mudou),
para nao gerar um programa com a marca pela metade.
"""
import os
import re
import shutil
import sys
from pathlib import Path

NOME = "SyDesk"
DESCRICAO = "SyDesk - Acesso remoto SynogConnect"
RAIZ = Path.cwd()
MARCA = Path(__file__).resolve().parent
ICONES = MARCA / "icones"


def trocar(caminho: str, regras: list[tuple[str, str]], regex: bool = False):
    f = RAIZ / caminho
    with open(f, encoding="utf-8", newline="") as arq:  # mantem as quebras de linha originais
        texto = arq.read()
    for velho, novo in regras:
        if regex:
            texto, n = re.subn(velho, novo, texto, flags=re.MULTILINE)
        else:
            n = texto.count(velho)
            texto = texto.replace(velho, novo)
        if n == 0:
            sys.exit(f"ERRO: nao achei {velho!r} em {caminho}. O RustDesk mudou; ajuste aplicar-marca.py.")
    with open(f, "w", encoding="utf-8", newline="") as arq:
        arq.write(texto)
    print(f"  ok  {caminho}")


def copiar(origem: str, destino: str):
    d = RAIZ / destino
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ICONES / origem, d)
    print(f"  ok  {destino}")


def main():
    if not (RAIZ / "libs/hbb_common/src/config.rs").exists():
        sys.exit("ERRO: rode na raiz do codigo do RustDesk (com os submodulos baixados).")
    print("Aplicando a marca SyDesk...")

    # 1. Nome do programa: muda pasta de instalacao, servico, janelas e os textos da interface
    regras = [(r'APP_NAME: RwLock<String> = RwLock::new\("RustDesk"\.to_owned\(\)\)',
               f'APP_NAME: RwLock<String> = RwLock::new("{NOME}".to_owned())')]
    servidor = os.environ.get("SYDESK_SERVIDOR", "").strip()
    key = os.environ.get("SYDESK_KEY", "").strip()
    if servidor:
        if not re.fullmatch(r"[A-Za-z0-9.\-:]+", servidor):
            sys.exit("ERRO: SYDESK_SERVIDOR invalido.")
        regras.append((r'pub const RENDEZVOUS_SERVERS: &\[&str\] = &\[[^\]]*\];',
                       f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{servidor}"];'))
    if key:
        if not re.fullmatch(r"[A-Za-z0-9+/=]{40,60}", key):
            sys.exit("ERRO: SYDESK_KEY invalida (cole so o conteudo de id_ed25519.pub).")
        regras.append((r'pub const RS_PUB_KEY: &str = "[^"]*";', f'pub const RS_PUB_KEY: &str = "{key}";'))
    trocar("libs/hbb_common/src/config.rs", regras, regex=True)

    # 2. Informacoes do .exe (Propriedades > Detalhes). O copyright original fica (licenca AGPL).
    trocar("Cargo.toml", [('ProductName = "RustDesk"', f'ProductName = "{NOME}"'),
                          ('FileDescription = "RustDesk Remote Desktop"', f'FileDescription = "{DESCRICAO}"')])
    trocar("flutter/windows/runner/Runner.rc",
           [('VALUE "FileDescription", "RustDesk Remote Desktop"', f'VALUE "FileDescription", "{DESCRICAO}"'),
            ('VALUE "ProductName", "RustDesk"', f'VALUE "ProductName", "{NOME}"')])
    trocar("flutter/windows/runner/main.cpp", [('std::wstring app_name = L"RustDesk";', f'std::wstring app_name = L"{NOME}";')])
    trocar("flutter/lib/desktop/widgets/tabbar_widget.dart", [(r'"RustDesk",(\r?\n)', f'"{NOME}",\\1')], regex=True)

    # 3. Icones
    copiar("icon.ico", "res/icon.ico")
    copiar("tray-icon.ico", "res/tray-icon.ico")
    copiar("icon.ico", "flutter/windows/runner/resources/app_icon.ico")
    copiar("icon-1024.png", "res/icon.png")
    copiar("icon-1024.png", "res/mac-icon.png")
    copiar("icon-32.png", "res/32x32.png")
    copiar("icon-64.png", "res/64x64.png")
    copiar("icon-128.png", "res/128x128.png")
    copiar("icon-256.png", "res/128x128@2x.png")
    copiar("icon.svg", "flutter/assets/icon.svg")
    copiar("icon-256.png", "flutter/assets/icon.png")
    copiar("icon-512.png", "flutter/assets/logo.png")
    print("Marca SyDesk aplicada.")


if __name__ == "__main__":
    main()

#!/bin/sh
  # start.sh – entrypoint para o Render

  echo "=== Iniciando Servidor de Túnel TCP Simples ==="
  echo "Servidor Reiniciado"

  # Muda para o diretório onde o repositório foi baixado pelo Render
  cd /opt/render/project/src

  # Verifica se o Python está disponível
  if ! command -v python3 >/dev/null 2>&1; then
      echo "Erro: python3 não encontrado"
      exit 1
  fi

  echo "Ambiente:"
  echo "  Python: $(python3 --version 2>/dev/null || echo 'Não
  encontrado')"
  echo "  Diretório de trabalho: $(pwd)"
  echo "  Porta do Render: ${PORT:-não definida (usará 4444)}"
  echo ""

  echo "Iniciando servidor de túnel..."
  echo "----------------------------------------"
  exec python3 tunnel_server.py

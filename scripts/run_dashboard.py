"""
Script para iniciar o dashboard
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Inicia o dashboard Streamlit"""
    
    # Caminho do dashboard
    dashboard_path = Path(__file__).parent.parent / "src" / "dashboard" / "app.py"
    
    print("\n" + "="*60)
    print("🚀 Iniciando Dashboard do Bot de Divulgação")
    print("="*60 + "\n")
    
    print("📊 Dashboard será aberto em: http://localhost:8501")
    print("⏹️  Pressione Ctrl+C para parar\n")
    
    # Executar streamlit
    try:
        subprocess.run([
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(dashboard_path),
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ])
    except KeyboardInterrupt:
        print("\n\n⏹️  Dashboard encerrado")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar dashboard: {str(e)}")
        print("\nTente instalar streamlit:")
        print("pip install streamlit plotly")
        sys.exit(1)


if __name__ == "__main__":
    main()
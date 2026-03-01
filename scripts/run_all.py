"""
Script para iniciar todos os componentes do bot
(API, Scheduler e Dashboard)

Correções:
- Streamlit SEM stdout/stderr PIPE (evita freeze)
- Execução via módulos (-m)
"""
import subprocess
import sys
import time
import signal

processes = []


def signal_handler(sig, frame):
    print("\n\n⏹️  Encerrando todos os serviços...")

    for proc in processes:
        try:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=5)
        except Exception:
            proc.kill()

    print("✅ Todos os serviços foram encerrados")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def start_api():
    print("🚀 Iniciando API...")

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    processes.append(proc)
    time.sleep(5)
    print("✅ API iniciada em http://localhost:8000")
    return proc


def start_scheduler():
    print("⏰ Iniciando Scheduler...")

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "src.scheduler.jobs",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    processes.append(proc)
    time.sleep(3)
    print("✅ Scheduler iniciado")
    return proc


def start_dashboard():
    print("📊 Iniciando Dashboard...")

    # ❗️ CRÍTICO: NÃO usar PIPE com Streamlit
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "src/dashboard/app.py",
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false",
        ],
        stdout=None,   # ← herda do terminal
        stderr=None,   # ← herda do terminal
    )

    processes.append(proc)
    time.sleep(4)
    print("✅ Dashboard iniciado em http://localhost:8501")
    return proc


def monitor_processes():
    print("\n" + "=" * 60)
    print("✅ Todos os serviços estão rodando!")
    print("=" * 60)
    print("\n📍 URLs de Acesso:")
    print("   • API: http://localhost:8000")
    print("   • API Docs: http://localhost:8000/docs")
    print("   • Dashboard: http://localhost:8501")
    print("\n⏹️  Pressione Ctrl+C para parar todos os serviços")
    print("=" * 60 + "\n")

    names = ["API", "Scheduler", "Dashboard"]

    try:
        while True:
            for i, proc in enumerate(processes):
                if proc.poll() is not None:
                    print(f"\n⚠️  {names[i]} parou inesperadamente!")

                    if proc.stderr:
                        stderr = proc.stderr.read()
                        if stderr:
                            print("\n🔴 STDERR:")
                            print(stderr[:1000])

                    return False

            time.sleep(2)

    except KeyboardInterrupt:
        return True


def main():
    print("\n" + "=" * 60)
    print("🤖 Bot de Divulgação - Inicialização Completa")
    print("=" * 60 + "\n")

    try:
        print("🔍 Verificando ambiente...")

        import streamlit  # noqa
        print("✅ Streamlit instalado")

        print("\n" + "=" * 60)
        print("🚀 Iniciando Serviços")
        print("=" * 60 + "\n")

        start_api()
        start_scheduler()
        start_dashboard()

        if not monitor_processes():
            print("\n⚠️  Um dos serviços falhou.")
            return 1

        return 0

    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return 1

    finally:
        signal_handler(None, None)


if __name__ == "__main__":
    sys.exit(main())

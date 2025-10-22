import nextcord
from nextcord.ext import commands
import subprocess
from asyncio import Semaphore

CONCURRENT_RUNS = 5
run_semaphore = Semaphore(CONCURRENT_RUNS)

class RunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def run_in_docker(self, language, code):
        async with run_semaphore:
            common_base = [
                "docker", "run", "--rm", "-i",
                "--network", "none",
                "--memory", "512m", "--memory-swap", "512m",
                "--cpus", "1", "--pids-limit", "50",
                "--read-only", "--tmpfs", "/tmp:rw,size=64m",
                "--tmpfs", "/code:rw,size=64m",
                "--user", "1000:1000",
                "--cap-drop=ALL", "--security-opt", "no-new-privileges",
            ]

            if language == "python":
                image = "python:3.12-slim"
                run_cmd = "cat > /code/script.py && python /code/script.py"

            elif language == "bash":
                image = "bash:5"
                run_cmd = "cat > /code/script.sh && bash /code/script.sh"
            else:
                return "Nieobsługiwany język!"

            cmd = common_base + [image, "bash", "-lc", run_cmd]

            try:
                result = subprocess.run(
                    cmd,
                    input=code,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                output = (result.stdout or "") + (result.stderr or "")
                if not output:
                    output = "Brak outputu (proces nic nie wypisał)."
                if len(output) > 1900:
                    output = output[:1900] + "\n\n... (wynik przycięty)"
                return f"```\n{output}\n```"
            except subprocess.TimeoutExpired:
                return "Kod przekroczył limit czasu!"
            except subprocess.SubprocessError as e:
                return f"Błąd uruchamiania kontenera: {e}"

    async def extract_code(self, content: str):
        """Parsuje blok kodu z wiadomości."""
        if "```" not in content:
            return None, None
        try:
            block = content.split("```")[1]
            language, code = block.split("\n", 1)
            return language.strip().lower(), code.strip()
        except Exception:
            return None, None

    async def execute_and_edit(self, user_message, bot_message):
        language, code = await self.extract_code(user_message.content)
        if not language or not code:
            await bot_message.edit(content="Nie znaleziono bloku kodu!")
            return

        await bot_message.edit(content="Uruchamiam kod...")
        output = await self.run_in_docker(language, code)
        await bot_message.edit(content=output)

    @commands.command()
    async def run(self, ctx):
        if ctx.author.id not in [1071887648718848051, 1284776252582137906, 886227892269367338]:
            return

        msg = await ctx.send("Uruchamiam kod...")
        await self.execute_and_edit(ctx.message, msg)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Ponowne uruchomienie kodu po edycji wiadomości z ?run"""
        if after.author.bot:
            return
        if after.content.strip().startswith("?run"):
            async for msg in after.channel.history(limit=10):
                if msg.author.bot and msg.reference and msg.reference.message_id == after.id:
                    # Znaleziono powiązaną wiadomość bota
                    await self.execute_and_edit(after, msg)
                    return
            msg = await after.channel.send("Uruchamiam kod...")
            await self.execute_and_edit(after, msg)

def setup(bot):
    print("POBIERANIE OBRAZÓW: PYTHON, BASH, RUST, C++")
    # subprocess.run(["docker", "pull", "python:3.12-slim"])
    # subprocess.run(["docker", "pull", "bash:5"])
    # subprocess.run(["docker", "pull", "rust:1.81"])
    # subprocess.run(["docker", "pull", "gcc:13"])
    print("POBRANO WSZYSTKIE OBRAZY")

    bot.add_cog(RunCog(bot))
